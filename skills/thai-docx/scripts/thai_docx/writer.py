# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""The body of word/document.xml: paragraphs, runs, tables, images, captions and fields,
as layout() arranged the document (ADR 0023, 0021, 0027).

`Package` in parts.py adds the package's other parts to this class.
"""

from __future__ import annotations

import re
import struct

from . import markdown as md
from .layout import CAPTION_STYLE, LIST_FIELDS, SECTION_MARK, caption_text, has_thai, heading_styles, layout, list_entries, number_text
from .settings import BuildError, half_up, page_size

def _bold_only(node: dict) -> bool:
    """A text inline whose run properties are the ones a caption's label carries: bold, nothing
    else — so the label, the number and the words after them belong in one run."""
    return bool(node.get("b")) and not (node.get("i") or node.get("strike") or node.get("code")
                                        or node.get("u") or node.get("sup") or node.get("sub") or node.get("link"))


def _formatted(node: dict) -> bool:
    """A text inline that carries any formatting of its own, so a number joined to it would
    take that formatting rather than the heading style's."""
    return bool(node.get("b") or node.get("i") or node.get("strike") or node.get("code")
                or node.get("u") or node.get("sup") or node.get("sub") or node.get("link"))


CODE_FONT = "Consolas"
# Styles whose own definition fixes the alignment — parts.py writes a <w:jc> into each of them.
# A paragraph in one of these takes its style's alignment, so latin_jc must leave it alone; held
# by test_the_styles_that_fix_alignment_are_the_ones_named.
STYLE_FIXES_ALIGNMENT = frozenset({"Heading" + str(n) for n in range(1, 7)} | {"CodeBlock"})
_PSTYLE = re.compile(r'<w:pStyle w:val="([^"]+)"/>')
# The box a task list draws, and the font that has it. Not ☐/☑ in Segoe UI Symbol: those
# characters live only in symbol fonts, and the one Windows has is on no other machine, so the
# box vanished everywhere else (ADR 0033). A white and a black square are in every ordinary
# text font, and Arial is on Windows and macOS and is what fontconfig gives for Arial on Linux.
SYMBOL_FONT = "Arial"
BOX, BOX_CHECKED = "□ ", "■ "
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
EMU_PER_PX = 9525  # at 96 dpi
EMU_PER_TWIP = 635
LANG = '<w:cs/><w:lang w:val="en-US" w:bidi="th-TH"/>'
# Thai marks above and below a consonant take no width of their own when a column is measured
THAI_MARKS = frozenset([0x0E31, *range(0x0E34, 0x0E3B), *range(0x0E47, 0x0E4F)])
# Word's own table default; with no table style it would otherwise be 0 and text touches the borders
CELL_MARGINS = '<w:tblCellMar><w:left w:w="108" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar>'
def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def attr(s: str) -> str:
    """An attribute value with its double quotes."""
    return '"' + esc(s).replace('"', "&quot;").replace("\t", "&#9;").replace("\n", "&#10;").replace("\r", "&#13;") + '"'


# --- images --------------------------------------------------------------------


def _image_size(data: bytes) -> tuple[str, int, int]:
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        wpx, hpx = struct.unpack(">II", data[16:24])
        if not (wpx and hpx):
            raise BuildError("image has no width or height")
        # a signature and an IHDR say how big the picture is, not that its pixels arrived;
        # a copy or a download that stopped has both, and Word draws a blank frame for it
        if data[-8:-4] != b"IEND":
            raise BuildError("image stops partway: a PNG ends with its IEND chunk and this one does not")
        return "png", wpx, hpx
    if data[:3] == b"\xff\xd8\xff":
        i = 2
        while i + 9 <= len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xD8, 0x01, 0xFF) or 0xD0 <= marker <= 0xD7:
                i += 1 if marker == 0xFF else 2
                continue
            length = (data[i + 2] << 8) | data[i + 3]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                hpx = (data[i + 5] << 8) | data[i + 6]
                wpx = (data[i + 7] << 8) | data[i + 8]
                if not (wpx and hpx):
                    raise BuildError("image has no width or height")
                if data[-2:] != b"\xff\xd9":
                    raise BuildError("image stops partway: a JPEG ends with its end-of-image marker and this one does not")
                return "jpeg", wpx, hpx
            if length < 2:
                break
            i += 2 + length
    raise BuildError("image is not a PNG or JPEG file (by its bytes, not its name)")


# --- the writer ----------------------------------------------------------------


class Writer:
    def __init__(self, doc: md.Document, opts: dict, read_image):
        """`read_image(src)` returns (resolved path, bytes), or raises BuildError."""
        self.doc, self.opts = doc, opts
        self.read_image = read_image
        self.rels: list[tuple[str, str, str, bool]] = []  # id, type, target, external
        self.media: list[tuple[str, bytes]] = []  # part name, bytes
        self.image_rel: dict[str, tuple[str, int, int]] = {}
        self.doc_pr = 0
        self.has_ordered_list = False  # whether --auto-numbering has anything to count (ADR 0028)
        self.heading_props, self.style_warnings = heading_styles(doc)
        self.items, self.regions, self.layout_warnings = layout(doc, opts)
        self.nums: list[tuple[int, int, int]] = []  # numId, start, level
        self.has_chapters = "chapters" in self.regions or "appendices" in self.regions  # headings Word numbers by region
        self.counts = {"headings": 0, "paragraphs": 0, "list_items": 0, "tables": 0, "table_rows": 0,
                       "code_blocks": 0, "images": 0, "footnotes": 0, "links": 0}
        pw, ph = page_size(opts)
        top, right, bottom, left = (half_up(m * 1440) for m in opts["margins"])
        self.page = (pw, ph, top, right, bottom, left)
        self.text_width_twips = pw - left - right

    def rel(self, kind: str, target: str, external: bool = False) -> str:
        rid = "rId" + str(len(self.rels) + 1)
        self.rels.append((rid, kind, target, external))
        return rid

    # -- inlines --

    def run_props(self, node: dict, bold: bool = False) -> str:
        p = []
        if node.get("link"):
            p.append('<w:rStyle w:val="Hyperlink"/>')
        if node.get("code"):
            p.append('<w:rFonts w:ascii="' + CODE_FONT + '" w:hAnsi="' + CODE_FONT + '" w:cs=' + attr(self.opts["font"]) + "/>")
        if node.get("b") or bold:
            p.append("<w:b/><w:bCs/>")
        if node.get("i"):
            p.append("<w:i/><w:iCs/>")
        if node.get("strike"):
            p.append("<w:strike/>")
        if node.get("u"):
            p.append('<w:u w:val="single"/>')
        if node.get("sup"):
            p.append('<w:vertAlign w:val="superscript"/>')
        elif node.get("sub"):
            p.append('<w:vertAlign w:val="subscript"/>')
        p.append(LANG)
        return "<w:rPr>" + "".join(p) + "</w:rPr>"

    def text_run(self, node: dict, bold: bool = False) -> str:
        pieces = node["s"].split("\t")
        body = "<w:tab/>".join('<w:t xml:space="preserve">' + esc(piece) + "</w:t>" for piece in pieces)
        return "<w:r>" + self.run_props(node, bold) + body + "</w:r>"

    def inlines(self, nodes: list[dict], bold: bool = False) -> str:
        out = []
        i = 0
        while i < len(nodes):
            n = nodes[i]
            if n["t"] == "text" and n.get("link"):
                j = i
                while j < len(nodes) and nodes[j]["t"] == "text" and nodes[j].get("link") == n["link"]:
                    j += 1
                rid = self.rel(REL + "hyperlink", n["link"], external=True)
                self.counts["links"] += 1
                runs = "".join(self.text_run(x, bold) for x in nodes[i:j])
                out.append('<w:hyperlink r:id="' + rid + '" w:history="1">' + runs + "</w:hyperlink>")
                i = j
                continue
            t = n["t"]
            if t == "text":
                out.append(self.text_run(n, bold))
            elif t == "hardbreak":
                out.append("<w:r><w:rPr>" + LANG + "</w:rPr><w:br/></w:r>")
            elif t == "task":
                mark = BOX_CHECKED if n["checked"] else BOX
                out.append('<w:r><w:rPr><w:rFonts w:ascii="' + SYMBOL_FONT + '" w:hAnsi="' + SYMBOL_FONT + '" w:cs="' + SYMBOL_FONT + '"/>'
                           + LANG + '</w:rPr><w:t xml:space="preserve">' + mark + "</w:t></w:r>")
            elif t == "footnote_ref":
                out.append('<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/>' + LANG + '</w:rPr><w:footnoteReference w:id="' + str(n["id"])
                           + '"/></w:r>')
            elif t == "image":
                out.append(self.image(n))
            i += 1
        if not out:  # an empty paragraph still carries a run, so fidelity reads it
            out.append("<w:r><w:rPr>" + LANG + '</w:rPr><w:t xml:space="preserve"></w:t></w:r>')
        return "".join(out)

    def image(self, node: dict) -> str:
        src = node["src"]
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", src):
            raise BuildError("image '" + src + "': remote images are not supported; only local PNG or JPEG files")
        path, data = self.read_image(src)
        if path not in self.image_rel:
            kind, wpx, hpx = _image_size(data)
            n = len(self.media) + 1
            self.media.append(("word/media/image" + str(n) + "." + kind, data))
            rid = self.rel(REL + "image", "media/image" + str(n) + "." + kind)
            self.image_rel[path] = (rid, wpx, hpx)
            self.counts["images"] += 1
        rid, wpx, hpx = self.image_rel[path]
        cx, cy = wpx * EMU_PER_PX, hpx * EMU_PER_PX
        max_cx = self.text_width_twips * EMU_PER_TWIP
        if cx > max_cx:
            cy = cy * max_cx // cx
            cx = max_cx
        self.doc_pr += 1
        k = str(self.doc_pr)
        return (
            "<w:r><w:rPr>" + LANG + "</w:rPr><w:drawing>"
            '<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="' + str(cx) + '" cy="' + str(cy) + '"/>'
            '<wp:docPr id="' + k + '" name="Picture ' + k + '" descr=' + attr(node["alt"]) + "/>"
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="Picture ' + k + '"/><pic:cNvPicPr/></pic:nvPicPr>'
            '<pic:blipFill><a:blip r:embed="' + rid + '"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="' + str(cx) + '" cy="' + str(cy)
            + '"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            "</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>"
        )

    # -- blocks --

    def paragraph(self, inlines: list[dict], style: str | None = None, ppr: str = "", bold: bool = False, lead: str = "") -> str:
        head = ('<w:pStyle w:val="' + style + '"/>' if style else "") + ppr
        self.counts["paragraphs"] += 1
        return "<w:p><w:pPr>" + head + self.latin_jc(head, md.inline_text(inlines)) + "</w:pPr>" + lead + self.inlines(inlines, bold) + "</w:p>"

    def latin_jc(self, head: str, text: str) -> str:
        """Thai distributed fills a line by spreading what is on it, which is how Thai is set
        — it has no spaces between words — and not how English is: a paragraph with no Thai in
        it keeps the ordinary left alignment, so "(2024a)" does not come out as "( 2 0 2 4 a)"
        and a title does not stretch across the page. Alignment only — ADR 0023 stands.

        A paragraph whose style already fixes an alignment is left as it is: an English heading
        under `heading-1: text-align: center` is centred like its Thai twin, and nothing here
        repeats what CodeBlock's own definition says."""
        if self.opts["align"] != "thai" or "<w:jc " in head or not text or has_thai(text):
            return ""
        style = _PSTYLE.search(head)
        if style is not None and style.group(1) in STYLE_FIXES_ALIGNMENT:
            return ""
        return '<w:jc w:val="left"/>'

    def title_break(self, item: dict) -> str:
        """--chapter-title-on-new-line: the number keeps the first line and the heading's own
        text starts the next one."""
        if not self.opts["chapter_title_on_new_line"] or "number" not in item:
            return ""
        return "<w:r><w:rPr>" + LANG + "</w:rPr><w:br/></w:r>"

    def numbers_are_text(self) -> bool:
        """Whether the build writes this document's numbers itself, instead of asking the
        application for them (ADR 0036). It is one answer for the whole document, never a
        number here and a field there: a document that renumbers its headings but not its
        captions goes wrong silently the first time a reader inserts a chapter.

        The build writes them unless `--auto-numbering` asks otherwise, because a written
        number reads the same in all five applications and a counted one does not — both
        measured on 2026-09-19:

        - **Thai digits.** LibreOffice draws `thaiNumbers` as 1, 2, 3, and does not read a
          `custom` format at all.
        - **Regions.** A caption inside chapters takes its number from `STYLEREF 1 \\s`, which
          LibreOffice answers with the chapter's *title*, and from a `SEQ` whose restart at each
          chapter it ignores.

        With `--auto-numbering` the application counts, whole: headings, ordered lists and
        captions renumber themselves as a reader edits, in Word — and `references/numbering.md`
        says what each of the other four draws."""
        return not self.opts["auto_numbering"]

    def field_runs(self, instr: str, result: str, rpr: str) -> str:
        """A field and the result the build already knows, between `separate` and `end`."""
        return (
            "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
            "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:instrText xml:space="preserve"> ' + instr + " </w:instrText></w:r>"
            "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:fldChar w:fldCharType="separate"/></w:r>'
            "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:t xml:space="preserve">' + result + "</w:t></w:r>"
            "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:fldChar w:fldCharType="end"/></w:r>'
        )

    def numbered_levels(self) -> set[int]:
        """Heading levels the numbering part numbers: the chapter level whenever there are
        chapters, the rest with --heading-numbers."""
        rest = set(range(2, 7)) if self.opts["heading_numbers"] else set()
        return ({1} | rest) if self.has_chapters else ({1} | rest if self.opts["heading_numbers"] else set())

    def heading_num_id(self) -> int:
        """After every ordered list's numId, which the body has handed out by the time styles are written."""
        return len(self.nums) + 2

    def numbered_heading(self, item: dict) -> tuple[list[dict], str, str]:
        """A heading's inlines and what goes before them: its number, written into the paragraph
        as text (ADR 0036). The number carries no run properties of its own, so it takes the
        heading style's — the size, weight and colour of the words beside it, which is what ADR
        0027 asked a numbering level to repeat. Where the first word is unformatted the number
        joins its run rather than sitting in one beside it, formatted alike (cause 4)."""
        b, inlines = item["block"], item["block"]["inlines"]
        if not self.numbers_are_text():
            # the numbering part numbers the heading, through its style or its own list
            ppr = ""
            if self.regions and item["region"] != "chapters" and b["level"] in self.numbered_levels():
                # appendices take their own list ("ภาคผนวก ก"); headings in any other region, none
                ppr = ('<w:numPr><w:ilvl w:val="' + str(b["level"] - 1) + '"/><w:numId w:val="' + str(self.heading_num_id() + 1) + '"/></w:numPr>'
                       if item["region"] == "appendices" else '<w:numPr><w:numId w:val="0"/></w:numPr>')
            return inlines, ppr, self.title_break(item)
        if "number" not in item:
            return inlines, "", ""
        brk = self.title_break(item)
        if not brk and inlines and inlines[0]["t"] == "text" and not _formatted(inlines[0]):
            return [dict(inlines[0], s=item["number"] + " " + inlines[0]["s"])] + inlines[1:], "", ""
        text = item["number"] if brk else item["number"] + " "
        return inlines, "", ("<w:r><w:rPr>" + LANG + '</w:rPr><w:t xml:space="preserve">' + esc(text) + "</w:t></w:r>" + brk)

    def body(self) -> str:
        """The document's own top level, as layout() arranged it: sections apart by
        SECTION_MARK, captions, directives, and headings outside the chapters unnumbered."""
        out = []
        for item in self.items:
            b = item["block"]
            if item.get("new_section"):
                out.append(SECTION_MARK)
            if "caption" in item:
                out.append(self.caption(item["caption"], item.get("keep_next", False)))
            elif b["t"] == "directive":
                out.append(self.field(LIST_FIELDS[b["name"]], entries=list_entries(self.items, b["name"])))
            elif b["t"] == "heading":
                self.counts["headings"] += 1
                inlines, ppr, lead = self.numbered_heading(item)
                out.append(self.paragraph(inlines, "Heading" + str(b["level"]), ppr, lead=lead))
            else:
                out.append(self.blocks([b], body=True, keep_next=item.get("keep_next", False)))
        return "".join(out)

    def caption(self, c: dict, keep_next: bool) -> str:
        """Label and number, bold, then the caption text. Where the document's numbers are the
        build's own (ADR 0036) the number is text. With `--auto-numbering` it is the pair of
        fields Word's own Insert Caption writes — the chapter from a STYLEREF, the count from a
        SEQ that starts again at each chapter, in Thai digits when those are asked for — with the
        results written in, so an application that never updates fields still shows them."""
        self.counts["paragraphs"] += 1
        bold = "<w:b/><w:bCs/>"

        def run(text: str, rpr: str) -> str:
            return "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:t xml:space="preserve">' + esc(text) + "</w:t></w:r>"

        ppr = ('<w:pStyle w:val="' + CAPTION_STYLE[c["kind"]] + '"/>' + ("<w:keepNext/>" if keep_next else "")
               + ('<w:jc w:val="center"/>' if c["kind"] == "figure" else ""))
        ppr += self.latin_jc(ppr, caption_text(c))
        rest = c["inlines"]
        if not self.numbers_are_text():
            out = "<w:p><w:pPr>" + ppr + "</w:pPr>" + run(c["label"] + " ", bold)
            if c["chapter"]:
                out += self.field_runs("STYLEREF 1 \\s", c["chapter"], bold) + run("-", bold)
            seq = ("SEQ " + c["kind"].capitalize() + " \\* " + ("ThaiArabic" if self.opts["thai_digits"] else "ARABIC")
                   + (" \\s 1" if c["reset"] else ""))
            out += self.field_runs(seq, c["seq"], bold)
            if rest and rest[0]["t"] == "text":
                out += self.inlines([dict(rest[0], s=" " + rest[0]["s"])] + rest[1:])
            elif rest:
                out += run(" ", "") + self.inlines(rest)
            return out + "</w:p>"
        number = (c["chapter"] + "-" if c["chapter"] else "") + c["seq"]
        head = c["label"] + " " + number
        if rest and rest[0]["t"] == "text" and _bold_only(rest[0]):
            # the caption opens in bold, as the label does: one run, or two formatted alike (cause 4)
            out = "<w:p><w:pPr>" + ppr + "</w:pPr>" + self.inlines([dict(rest[0], s=head + " " + rest[0]["s"])] + rest[1:])
            return out + "</w:p>"
        out = "<w:p><w:pPr>" + ppr + "</w:pPr>" + run(head, bold)
        if rest and rest[0]["t"] == "text":
            # the space joins the first text run: a run of its own would sit beside one formatted alike (cause 4)
            out += self.inlines([dict(rest[0], s=" " + rest[0]["s"])] + rest[1:])
        elif rest:
            out += run(" ", "") + self.inlines(rest)
        return out + "</w:p>"

    def blocks(self, blocks: list[dict], level: int = 0, quote: bool = False, body: bool = False, keep_next: bool = False) -> str:
        """`body` marks the document's own top level: only its paragraphs take the
        first-line indent — not headings, lists, quotes, tables, code or footnotes."""
        out = []
        first_line = half_up(self.opts["indent"] * 1440) if body else 0
        for b in blocks:
            t = b["t"]
            ind = '<w:ind w:left="' + str(720 * level) + '"/>' if level else ""
            if t == "heading":
                self.counts["headings"] += 1
                out.append(self.paragraph(b["inlines"], "Heading" + str(b["level"])))
            elif t == "paragraph":
                ppr = '<w:ind w:firstLine="' + str(first_line) + '"/>' if first_line else ind
                ppr = ("<w:keepNext/>" if keep_next else "") + ppr
                out.append(self.paragraph(b["inlines"], "Quote" if quote else ("ListParagraph" if level else None), ppr))
            elif t == "code":
                self.counts["code_blocks"] += 1
                for line in b["lines"] or [""]:
                    out.append(self.paragraph([{"t": "text", "s": line}], "CodeBlock", ind))
            elif t == "quote":
                out.append(self.blocks(b["blocks"], level, quote=True))
            elif t == "break":
                self.counts["paragraphs"] += 1
                out.append('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="808080"/></w:pBdr></w:pPr></w:p>')
            elif t == "list":
                out.append(self.list(b, level, quote))
            elif t == "table":
                out.append(self.table(b))
        return "".join(out)

    def list(self, b: dict, level: int, quote: bool) -> str:
        """A bullet is drawn by the numbering part, which every application reads the same way.
        An ordered list's number is written as text instead (ADR 0036): its format is one a
        reader may not have — LibreOffice draws thaiNumbers as 1, 2, 3 — and the hanging indent
        and the tab after the marker put it where the numbering put it."""
        ordered, out = b["ordered"], []
        self.has_ordered_list = self.has_ordered_list or ordered
        written = self.numbers_are_text()
        if ordered and not written:
            num_id = len(self.nums) + 2
            self.nums.append((num_id, b["start"], level))
        indent = '<w:ind w:left="' + str(720 * (level + 1)) + '" w:hanging="360"/>'
        for n, item in enumerate(b["items"]):
            self.counts["list_items"] += 1
            if item and item[0]["t"] == "paragraph":
                first, rest = item[0]["inlines"], item[1:]
            else:
                first, rest = [], item  # the marker still shows on an item that opens with no paragraph
            if first and first[0]["t"] == "task":
                ppr, lead = '<w:ind w:left="' + str(720 * (level + 1)) + '"/>', ""
            elif ordered and not written:
                ppr, lead = '<w:numPr><w:ilvl w:val="' + str(min(level, 8)) + '"/><w:numId w:val="' + str(num_id) + '"/></w:numPr>', ""
            elif ordered:
                marker = number_text(b["start"] + n, "decimal", self.opts["thai_digits"]) + "."
                ppr = indent
                lead = ("<w:r><w:rPr>" + LANG + '</w:rPr><w:t xml:space="preserve">' + esc(marker) + "</w:t></w:r>"
                        "<w:r><w:rPr>" + LANG + "</w:rPr><w:tab/></w:r>")
            else:
                ppr, lead = '<w:numPr><w:ilvl w:val="' + str(min(level, 8)) + '"/><w:numId w:val="1"/></w:numPr>', ""
            out.append(self.paragraph(first, "ListParagraph", ppr, lead=lead))
            out.append(self.blocks(rest, level + 1, quote))
        return "".join(out)

    def column_widths(self, b: dict) -> list[int]:
        """Twips per column, filling the text width. `auto`: each column a quarter of an equal
        share, and the rest shared by the longest line of text the column holds."""
        n, width = len(b["aligns"]), self.text_width_twips
        if self.opts["table_widths"] == "equal":
            return [width // n] * n
        need = [1] * n
        for row in b["rows"]:
            for ci, cell in enumerate(row):
                for line in md.inline_text(cell).split("\n"):
                    need[ci] = max(need[ci], sum(1 for c in line if ord(c) not in THAI_MARKS))
        floor = width // (4 * n)
        spare, total = width - floor * n, sum(need)
        widths = [floor + spare * k // total for k in need]
        widths[-1] += width - sum(widths)
        return widths

    def table(self, b: dict) -> str:
        self.counts["tables"] += 1
        widths = self.column_widths(b)
        grid = "".join('<w:gridCol w:w="' + str(col) + '"/>' for col in widths)
        borders = "".join('<w:' + s + ' w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
                          for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
        rows = []
        for ri, row in enumerate(b["rows"]):
            self.counts["table_rows"] += 1
            cells = []
            for ci, cell in enumerate(row):
                jc = b["aligns"][ci]
                # no space after: the body's 6 pt would leave every row taller than its text
                ppr = (('<w:pStyle w:val="TableText"/>' if self.opts["table_size"] is not None else "") + '<w:spacing w:after="0"/>'
                       + ('<w:jc w:val="' + jc + '"/>' if jc in ("center", "right") else ""))
                cells.append('<w:tc><w:tcPr><w:tcW w:w="' + str(widths[ci]) + '" w:type="dxa"/></w:tcPr>' + self.paragraph(cell, None, ppr, ri == 0)
                             + "</w:tc>")
            trpr = "<w:trPr><w:tblHeader/></w:trPr>" if ri == 0 and self.opts["repeat_table_header"] else ""
            rows.append("<w:tr>" + trpr + "".join(cells) + "</w:tr>")
        return (
            '<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders>' + borders + "</w:tblBorders>"
            '<w:tblLayout w:type="autofit"/>' + CELL_MARGINS + "</w:tblPr>"
            '<w:tblGrid>' + grid + "</w:tblGrid>" + "".join(rows) + "</w:tbl>"
            "<w:p><w:pPr/></w:p>"
        )

    # -- parts --

    def field(self, instr: str, ppr: str = "", entries: list[tuple[int, str]] | None = None) -> str:
        """A field paragraph, and — for a list of contents, tables or figures — the entries
        it already holds between `separate` and `end`, one paragraph each (ADR 0027).
        The field opens in the first entry and closes in the last, as Word writes it."""

        def char(kind: str) -> str:
            return "<w:r><w:rPr>" + LANG + '</w:rPr><w:fldChar w:fldCharType="' + kind + '"/></w:r>'

        instruction = "<w:r><w:rPr>" + LANG + '</w:rPr><w:instrText xml:space="preserve"> ' + instr + " </w:instrText></w:r>"
        if not entries:
            return "<w:p><w:pPr>" + ppr + "</w:pPr>" + char("begin") + instruction + char("separate") + char("end") + "</w:p>"
        self.counts["paragraphs"] += len(entries)
        out = []
        for i, (level, text) in enumerate(entries):
            opening = char("begin") + instruction + char("separate") if i == 0 else ""
            closing = char("end") if i == len(entries) - 1 else ""
            entry_ppr = '<w:pStyle w:val="TOC' + str(min(level, 3)) + '"/>'
            out.append(
                "<w:p><w:pPr>" + entry_ppr + self.latin_jc(entry_ppr, text) + "</w:pPr>" + opening
                + "<w:r><w:rPr>" + LANG + '</w:rPr><w:t xml:space="preserve">' + esc(text) + "</w:t></w:r>" + closing + "</w:p>"
            )
        return "".join(out)
