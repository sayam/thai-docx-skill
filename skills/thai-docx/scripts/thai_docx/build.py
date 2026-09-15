"""`thai_docx build IN.md OUT.docx [flags]` — Markdown to a .docx that passes
`thai_docx check`, with the content unchanged (ADR 0005) and the same bytes on
every run and in both implementations (ADR 0008).

The output is written only when the package passes the checker and the fidelity
check; otherwise nothing is written and the JSON line says why. Standard library
only; reads the Markdown file and the images it names, writes one file (ADR 0011).

Byte stability: zip entries are *stored*, not deflated — deflate output differs
between zlib builds. No clock, host name or user name enters any part. Escaping,
rounding and messages are spelled out here rather than borrowed from the
standard library, so the JavaScript port can say exactly the same (ADR 0015).
"""

from __future__ import annotations

import errno
import hashlib
import io
import json
import math
import pathlib
import re
import struct
import unicodedata
import zipfile
from xml.etree import ElementTree as ET

from . import check as check_mod
from . import markdown as md
from .ooxml import W, w

PAPER = {"a4": (11906, 16838), "letter": (12240, 15840)}
DEFAULTS = {
    "font": "TH Sarabun New",
    "size": 16,
    "paper": "a4",
    "margins": (1.0, 1.0, 1.0, 1.5),  # top, right, bottom, left — inches
    "align": "left",
    "toc": False,
    "page_numbers": False,
    "hide_spelling_errors": False,
}
CODE_FONT = "Consolas"
SYMBOL_FONT = "Segoe UI Symbol"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
EMU_PER_PX = 9525  # at 96 dpi
EMU_PER_TWIP = 635
LANG = '<w:cs/><w:lang w:val="en-US" w:bidi="th-TH"/>'
MIN_TEXT_TWIPS = 1440
USAGE = "usage: thai_docx build IN.md OUT.docx [--font NAME] [--size PT] [--paper a4|letter] [--margins T,R,B,L] [--align left|thai] [--toc] [--page-numbers] [--hide-spelling-errors] [--allow-dir DIR]"
_NUMBER = re.compile(r"^[0-9]+(?:\.[0-9]+)?$")
_OS_ERRORS = {
    errno.ENOENT: "No such file or directory",
    errno.EACCES: "Permission denied",
    errno.EISDIR: "Is a directory",
    errno.ENOTDIR: "Not a directory",
}


class BuildError(Exception):
    def __init__(self, what: str):
        super().__init__(what)
        self.what = what


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def attr(s: str) -> str:
    """An attribute value with its double quotes."""
    return '"' + esc(s).replace('"', "&quot;").replace("\t", "&#9;").replace("\n", "&#10;").replace("\r", "&#13;") + '"'


def half_up(x: float) -> int:
    return int(math.floor(x + 0.5))


def os_error(exc: OSError) -> str:
    return _OS_ERRORS.get(exc.errno, "cannot be read")


# --- images --------------------------------------------------------------------


def _image_size(data: bytes) -> tuple[str, int, int]:
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        wpx, hpx = struct.unpack(">II", data[16:24])
        if wpx and hpx:
            return "png", wpx, hpx
        raise BuildError("image has no width or height")
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
                if wpx and hpx:
                    return "jpeg", wpx, hpx
                raise BuildError("image has no width or height")
            if length < 2:
                break
            i += 2 + length
    raise BuildError("image is not a PNG or JPEG file (by its bytes, not its name)")


# --- the writer ----------------------------------------------------------------


class Writer:
    def __init__(self, doc: md.Document, opts: dict, md_dir: str, allow_dirs: list[str], read_image):
        """`read_image(src)` returns (resolved path, bytes), or raises BuildError."""
        self.doc, self.opts = doc, opts
        self.md_dir, self.allow_dirs, self.read_image = md_dir, allow_dirs, read_image
        self.rels: list[tuple[str, str, str, bool]] = []  # id, type, target, external
        self.media: list[tuple[str, bytes]] = []  # part name, bytes
        self.image_rel: dict[str, tuple[str, int, int]] = {}
        self.nums: list[tuple[int, int, int]] = []  # numId, start, level
        self.doc_pr = 0
        self.counts = {"headings": 0, "paragraphs": 0, "list_items": 0, "tables": 0, "table_rows": 0,
                       "code_blocks": 0, "images": 0, "footnotes": 0, "links": 0}
        pw, ph = PAPER[opts["paper"]]
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
                mark = "☑ " if n["checked"] else "☐ "
                out.append('<w:r><w:rPr><w:rFonts w:ascii="' + SYMBOL_FONT + '" w:hAnsi="' + SYMBOL_FONT + '" w:cs="' + SYMBOL_FONT + '"/>'
                           + LANG + '</w:rPr><w:t xml:space="preserve">' + mark + "</w:t></w:r>")
            elif t == "footnote_ref":
                out.append('<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/>' + LANG + '</w:rPr><w:footnoteReference w:id="' + str(n["id"]) + '"/></w:r>')
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
            '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="' + str(cx) + '" cy="' + str(cy) + '"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            "</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>"
        )

    # -- blocks --

    def paragraph(self, inlines: list[dict], style: str | None = None, ppr: str = "", bold: bool = False) -> str:
        head = ('<w:pStyle w:val="' + style + '"/>' if style else "") + ppr
        self.counts["paragraphs"] += 1
        return "<w:p><w:pPr>" + head + "</w:pPr>" + self.inlines(inlines, bold) + "</w:p>"

    def blocks(self, blocks: list[dict], level: int = 0, quote: bool = False) -> str:
        out = []
        for b in blocks:
            t = b["t"]
            ind = '<w:ind w:left="' + str(720 * level) + '"/>' if level else ""
            if t == "heading":
                self.counts["headings"] += 1
                out.append(self.paragraph(b["inlines"], "Heading" + str(b["level"])))
            elif t == "paragraph":
                out.append(self.paragraph(b["inlines"], "Quote" if quote else ("ListParagraph" if level else None), ind))
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
        if b["ordered"]:
            num_id = len(self.nums) + 2
            self.nums.append((num_id, b["start"], level))
        else:
            num_id = 1
        out = []
        for item in b["items"]:
            self.counts["list_items"] += 1
            if item and item[0]["t"] == "paragraph":
                first, rest = item[0]["inlines"], item[1:]
            else:
                first, rest = [], item  # the marker still shows on an item that opens with no paragraph
            if first and first[0]["t"] == "task":
                ppr = '<w:ind w:left="' + str(720 * (level + 1)) + '"/>'
            else:
                ppr = '<w:numPr><w:ilvl w:val="' + str(min(level, 8)) + '"/><w:numId w:val="' + str(num_id) + '"/></w:numPr>'
            out.append(self.paragraph(first, "ListParagraph", ppr))
            out.append(self.blocks(rest, level + 1, quote))
        return "".join(out)

    def table(self, b: dict) -> str:
        self.counts["tables"] += 1
        ncols = len(b["aligns"])
        col = self.text_width_twips // ncols
        grid = "".join('<w:gridCol w:w="' + str(col) + '"/>' for _ in range(ncols))
        borders = "".join('<w:' + s + ' w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
                          for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
        rows = []
        for ri, row in enumerate(b["rows"]):
            self.counts["table_rows"] += 1
            cells = []
            for ci, cell in enumerate(row):
                jc = b["aligns"][ci]
                ppr = '<w:jc w:val="' + jc + '"/>' if jc in ("center", "right") else ""
                cells.append('<w:tc><w:tcPr><w:tcW w:w="' + str(col) + '" w:type="dxa"/></w:tcPr>' + self.paragraph(cell, None, ppr, ri == 0) + "</w:tc>")
            trpr = "<w:trPr><w:tblHeader/></w:trPr>" if ri == 0 else ""
            rows.append("<w:tr>" + trpr + "".join(cells) + "</w:tr>")
        return (
            '<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders>' + borders + "</w:tblBorders>"
            '<w:tblLayout w:type="autofit"/></w:tblPr><w:tblGrid>' + grid + "</w:tblGrid>" + "".join(rows) + "</w:tbl>"
            "<w:p><w:pPr/></w:p>"
        )

    # -- parts --

    def field(self, instr: str, ppr: str = "") -> str:
        return (
            "<w:p><w:pPr>" + ppr + "</w:pPr>"
            "<w:r><w:rPr>" + LANG + '</w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
            "<w:r><w:rPr>" + LANG + '</w:rPr><w:instrText xml:space="preserve"> ' + instr + " </w:instrText></w:r>"
            "<w:r><w:rPr>" + LANG + '</w:rPr><w:fldChar w:fldCharType="separate"/></w:r>'
            "<w:r><w:rPr>" + LANG + '</w:rPr><w:fldChar w:fldCharType="end"/></w:r></w:p>'
        )

    def document_xml(self, body: str) -> str:
        pw, ph, top, right, bottom, left = self.page
        header = ""
        if self.opts["page_numbers"]:
            header = '<w:headerReference w:type="default" r:id="' + self.rel(REL + "header", "header1.xml") + '"/>'
        toc = self.field('TOC \\o "1-3" \\h \\z \\u') + "<w:p><w:pPr/></w:p>" if self.opts["toc"] else ""
        sect = (
            "<w:sectPr>" + header + '<w:pgSz w:w="' + str(pw) + '" w:h="' + str(ph) + '"/>'
            '<w:pgMar w:top="' + str(top) + '" w:right="' + str(right) + '" w:bottom="' + str(bottom) + '" w:left="' + str(left)
            + '" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>'
        )
        return (
            XML + '<w:document xmlns:w="' + W + '" xmlns:r="' + NS_R + '" '
            'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            "<w:body>" + toc + body + sect + "</w:body></w:document>"
        )

    def footnotes_xml(self) -> str:
        parts = [
            '<w:footnote w:type="separator" w:id="-1"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:separator/></w:r></w:p></w:footnote>',
            '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>',
        ]
        mark = ('<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/>' + LANG + "</w:rPr><w:footnoteRef/></w:r>"
                "<w:r><w:rPr>" + LANG + "</w:rPr><w:tab/></w:r>")
        for fid, label in enumerate(self.doc.footnote_order, 1):
            self.counts["footnotes"] += 1
            blocks = self.doc.footnotes[label]
            if blocks and blocks[0]["t"] == "paragraph":
                first, rest = blocks[0]["inlines"], blocks[1:]
            else:
                first, rest = [], blocks
            self.counts["paragraphs"] += 1
            body = '<w:p><w:pPr><w:pStyle w:val="FootnoteText"/></w:pPr>' + mark + self.inlines(first) + "</w:p>" + self.blocks(rest)
            parts.append('<w:footnote w:id="' + str(fid) + '">' + body + "</w:footnote>")
        return XML + '<w:footnotes xmlns:w="' + W + '" xmlns:r="' + NS_R + '">' + "".join(parts) + "</w:footnotes>"

    def styles_xml(self) -> str:
        font = attr(self.opts["font"])
        size = self.opts["size"]
        small = max(size - 3, 1)

        def hp(pt: float) -> str:
            return str(half_up(pt * 2))

        jc = '<w:jc w:val="thaiDistribute"/>' if self.opts["align"] == "thai" else ""

        def heading(n: int, pt: float, bold: bool, italic: bool) -> str:
            rpr = ("<w:b/><w:bCs/>" if bold else "") + ("<w:i/><w:iCs/>" if italic else "") + '<w:sz w:val="' + hp(pt) + '"/><w:szCs w:val="' + hp(pt) + '"/>'
            return (
                '<w:style w:type="paragraph" w:styleId="Heading' + str(n) + '"><w:name w:val="heading ' + str(n) + '"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
                '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="' + ("240" if n == 1 else "200") + '" w:after="80"/><w:jc w:val="left"/><w:outlineLvl w:val="' + str(n - 1) + '"/></w:pPr>'
                "<w:rPr>" + rpr + "</w:rPr></w:style>"
            )

        return (
            XML + '<w:styles xmlns:w="' + W + '">'
            "<w:docDefaults><w:rPrDefault><w:rPr>"
            "<w:rFonts w:ascii=" + font + " w:hAnsi=" + font + " w:cs=" + font + " w:eastAsia=" + font + "/>"
            '<w:sz w:val="' + hp(size) + '"/><w:szCs w:val="' + hp(size) + '"/><w:cs/><w:lang w:val="en-US" w:eastAsia="en-US" w:bidi="th-TH"/>'
            "</w:rPr></w:rPrDefault><w:pPrDefault><w:pPr>"
            '<w:spacing w:after="120" w:line="264" w:lineRule="auto"/>' + jc
            + "</w:pPr></w:pPrDefault></w:docDefaults>"
            '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
            + heading(1, size + 4, True, False) + heading(2, size + 2, True, False) + heading(3, size, True, False)
            + heading(4, size, True, True) + heading(5, size, True, False) + heading(6, size, False, True)
            + '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:ind w:left="720"/><w:contextualSpacing/></w:pPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:ind w:left="720" w:right="720"/></w:pPr><w:rPr><w:i/><w:iCs/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="CodeBlock"><w:name w:val="Code Block"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr><w:rPr><w:rFonts w:ascii="'
            + CODE_FONT + '" w:hAnsi="' + CODE_FONT + '" w:cs=' + font + '/><w:sz w:val="' + hp(small) + '"/><w:szCs w:val="' + hp(small) + '"/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="FootnoteText"><w:name w:val="footnote text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:left="360" w:hanging="360"/></w:pPr><w:rPr><w:sz w:val="'
            + hp(small) + '"/><w:szCs w:val="' + hp(small) + '"/></w:rPr></w:style>'
            '<w:style w:type="character" w:styleId="FootnoteReference"><w:name w:val="footnote reference"/><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>'
            '<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr></w:style>'
            "</w:styles>"
        )

    def numbering_xml(self) -> str:
        font = attr(self.opts["font"])
        bullet = "".join(
            '<w:lvl w:ilvl="' + str(l) + '"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>'
            '<w:pPr><w:ind w:left="' + str(720 * (l + 1)) + '" w:hanging="360"/></w:pPr><w:rPr><w:rFonts w:ascii=' + font + " w:hAnsi=" + font + " w:cs=" + font + "/></w:rPr></w:lvl>"
            for l in range(9)
        )
        decimal = "".join(
            '<w:lvl w:ilvl="' + str(l) + '"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%' + str(l + 1) + '."/><w:lvlJc w:val="left"/>'
            '<w:pPr><w:ind w:left="' + str(720 * (l + 1)) + '" w:hanging="360"/></w:pPr></w:lvl>'
            for l in range(9)
        )
        nums = '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>' + "".join(
            '<w:num w:numId="' + str(nid) + '"><w:abstractNumId w:val="1"/><w:lvlOverride w:ilvl="' + str(min(level, 8))
            + '"><w:startOverride w:val="' + str(start) + '"/></w:lvlOverride></w:num>'
            for nid, start, level in self.nums
        )
        return (
            XML + '<w:numbering xmlns:w="' + W + '">'
            '<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="hybridMultilevel"/>' + bullet + "</w:abstractNum>"
            '<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="hybridMultilevel"/>' + decimal + "</w:abstractNum>"
            + nums + "</w:numbering>"
        )

    def settings_xml(self) -> str:
        parts = []
        if self.opts["hide_spelling_errors"]:
            parts.append("<w:hideSpellingErrors/><w:hideGrammaticalErrors/>")
        parts.append('<w:defaultTabStop w:val="720"/><w:characterSpacingControl w:val="doNotCompress"/>')
        if self.opts["toc"]:
            parts.append('<w:updateFields w:val="true"/>')
        if self.doc.footnote_order:
            parts.append('<w:footnotePr><w:footnote w:id="-1"/><w:footnote w:id="0"/></w:footnotePr>')
        uri = ' w:uri="http://schemas.microsoft.com/office/word" '
        parts.append(
            "<w:compat>"
            '<w:compatSetting w:name="compatibilityMode"' + uri + 'w:val="15"/>'
            '<w:compatSetting w:name="overrideTableStyleFontSizeAndJustification"' + uri + 'w:val="1"/>'
            '<w:compatSetting w:name="enableOpenTypeFeatures"' + uri + 'w:val="1"/>'
            '<w:compatSetting w:name="doNotFlipMirrorIndents"' + uri + 'w:val="1"/>'
            '<w:compatSetting w:name="differentiateMultirowTableHeaders"' + uri + 'w:val="1"/>'
            "</w:compat>"
            '<w:themeFontLang w:val="en-US" w:bidi="th-TH"/>'
        )
        return XML + '<w:settings xmlns:w="' + W + '">' + "".join(parts) + "</w:settings>"

    def header_xml(self) -> str:
        return XML + '<w:hdr xmlns:w="' + W + '">' + self.field("PAGE", '<w:jc w:val="right"/>') + "</w:hdr>"

    def core_xml(self) -> str:
        fm = self.doc.front_matter
        inner = ""
        if fm.get("title"):
            inner += "<dc:title>" + esc(fm["title"]) + "</dc:title>"
        if fm.get("author"):
            inner += "<dc:creator>" + esc(fm["author"]) + "</dc:creator>"
        return (
            XML + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/">' + inner + "</cp:coreProperties>"
        )

    def package(self) -> list[tuple[str, bytes]]:
        body = self.blocks(self.doc.blocks)
        document = self.document_xml(body)
        overrides = [
            ("/word/document.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"),
            ("/word/styles.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"),
            ("/word/settings.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"),
            ("/word/numbering.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"),
            ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
        ]
        self.rel(REL + "styles", "styles.xml")
        self.rel(REL + "settings", "settings.xml")
        self.rel(REL + "numbering", "numbering.xml")
        footnotes = header = None
        if self.doc.footnote_order:
            self.rel(REL + "footnotes", "footnotes.xml")
            overrides.append(("/word/footnotes.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"))
            footnotes = self.footnotes_xml()
        if self.opts["page_numbers"]:
            overrides.append(("/word/header1.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"))
            header = self.header_xml()
        defaults = '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
        for ext in sorted({name.rsplit(".", 1)[1] for name, _ in self.media}):
            defaults += '<Default Extension="' + ext + '" ContentType="image/' + ext + '"/>'
        parts: list[tuple[str, str | bytes]] = [
            ("[Content_Types].xml", XML + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' + defaults
             + "".join('<Override PartName="' + p + '" ContentType="' + ct + '"/>' for p, ct in overrides) + "</Types>"),
            ("_rels/.rels", XML + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Id="rId1" Type="' + REL + 'officeDocument" Target="word/document.xml"/>'
             '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
             "</Relationships>"),
            ("docProps/core.xml", self.core_xml()),
            ("word/document.xml", document),
            ("word/styles.xml", self.styles_xml()),
            ("word/settings.xml", self.settings_xml()),
            ("word/numbering.xml", self.numbering_xml()),
        ]
        if footnotes is not None:
            parts.append(("word/footnotes.xml", footnotes))
        if header is not None:
            parts.append(("word/header1.xml", header))
        parts.append(("word/_rels/document.xml.rels", XML + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                      + "".join('<Relationship Id="' + rid + '" Type="' + kind + '" Target=' + attr(target) + (' TargetMode="External"/>' if ext else "/>")
                                for rid, kind, target, ext in self.rels)
                      + "</Relationships>"))
        parts.extend(self.media)
        return [(name, data.encode("utf-8") if isinstance(data, str) else data) for name, data in parts]


def pack(parts: list[tuple[str, bytes]]) -> bytes:
    """Stored entries, fixed timestamp, no OS-specific attributes — bytes the
    JavaScript port reproduces. Part order is the order given."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        for name, data in parts:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 0
            info.external_attr = 0o600 << 16
            zf.writestr(info, data)
    return buf.getvalue()


# --- fidelity (ADR 0005) -------------------------------------------------------


def docx_text(parts: dict[str, bytes], footnote_count: int) -> list[str]:
    """Every paragraph's text from the package, in the order plain_text() gives it.
    A tab is text, except the one that separates a footnote's mark from its body."""
    out = []

    def paragraphs(root):
        for p in root.iter(w("p")):
            pieces, seen, after_mark = [], False, False
            for el in p.iter():
                tag = el.tag
                if tag == w("footnoteRef"):
                    after_mark = True
                    seen = True
                elif tag == w("t"):
                    pieces.append(el.text or "")
                    seen = True
                    after_mark = False
                elif tag == w("tab"):
                    if not after_mark:
                        pieces.append("\t")
                    after_mark = False
                    seen = True
                elif tag == w("br"):
                    pieces.append("\n")
                    seen = True
                elif tag == w("drawing"):
                    seen = True
            if seen:
                out.append("".join(pieces))

    paragraphs(ET.fromstring(parts["word/document.xml"]))
    if footnote_count:
        root = ET.fromstring(parts["word/footnotes.xml"])
        for note in root.iter(w("footnote")):
            if note.get(w("type")) is None:
                paragraphs(note)
    return out


def expected_text(doc: md.Document) -> list[str]:
    out = md.plain_text(doc.blocks)
    for label in doc.footnote_order:
        blocks = doc.footnotes[label]
        if not blocks or blocks[0]["t"] != "paragraph":
            out.append("")
        out.extend(md.plain_text(blocks))
    return [unicodedata.normalize("NFC", s) for s in out]


# --- entry ---------------------------------------------------------------------


def settings_json(opts: dict) -> dict:
    top, right, bottom, left = opts["margins"]
    return {
        "font": opts["font"], "size_pt": opts["size"], "paper": opts["paper"],
        "margins_in": {"top": float(top), "right": float(right), "bottom": float(bottom), "left": float(left)},
        "align": opts["align"], "toc": opts["toc"], "page_numbers": opts["page_numbers"],
        "hide_spelling_errors": opts["hide_spelling_errors"],
    }


def build_text(text: str, opts: dict, read_image) -> tuple[dict, bytes | None]:
    """The whole build except reading the Markdown and writing the file: the part
    both implementations must agree on byte for byte."""
    result: dict = {}
    try:
        doc = md.parse(text)
        writer = Writer(doc, opts, "", [], read_image)
        parts = writer.package()
    except md.Unsupported as exc:
        return {"error": exc.what, "line": exc.line}, None
    except BuildError as exc:
        return {"error": exc.what}, None
    data = pack(parts)
    report = check_mod.check(io.BytesIO(data))
    findings = list(report.findings)
    if not findings:
        expected, actual = expected_text(doc), docx_text(dict(parts), len(doc.footnote_order))
        if expected != actual:
            idx = next((i for i, (a, b) in enumerate(zip(expected, actual)) if a != b), min(len(expected), len(actual)))
            findings.append({"code": "fidelity", "part": "word/document.xml",
                             "message": "paragraph " + str(idx + 1) + " does not match the Markdown (" + str(len(expected))
                             + " paragraphs expected, " + str(len(actual)) + " written)"})
    result.update(
        counts={**writer.counts, "runs": report.counts.get("runs", 0)},
        warnings=[{"code": "markdown", "message": m} for m in doc.warnings] + report.warnings,
        findings=findings,
        sha256=hashlib.sha256(data).hexdigest(),
        bytes=len(data),
    )
    return result, (None if findings else data)


def image_reader(md_dir: pathlib.Path, allow_dirs: list[pathlib.Path]):
    roots = [md_dir] + allow_dirs

    def read(src: str) -> tuple[str, bytes]:
        path = (md_dir / src).resolve()
        if not any(path == root or root in path.parents for root in roots):
            raise BuildError("image '" + src + "' lies outside the Markdown file's directory; pass --allow-dir for its directory (ADR 0011 §4)")
        try:
            return str(path), path.read_bytes()
        except OSError as exc:
            raise BuildError("image '" + src + "': " + os_error(exc))

    return read


def build(md_path, out_path, opts: dict, allow_dirs: list) -> dict:
    md_path, out_path = str(md_path), str(out_path)
    result: dict = {"ok": False, "file": out_path, "settings": settings_json(opts)}
    src = pathlib.Path(md_path)
    try:
        raw = src.read_bytes()
    except OSError as exc:
        result["error"] = "cannot read " + md_path + ": " + os_error(exc)
        return result
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        result["error"] = "cannot read " + md_path + ": not UTF-8 text"
        return result
    reader = image_reader(src.resolve().parent, [pathlib.Path(str(d)).resolve() for d in allow_dirs])
    outcome, data = build_text(text, opts, reader)
    result.update(outcome)
    if data is None:
        return result
    try:
        pathlib.Path(out_path).write_bytes(data)
    except OSError as exc:
        result["error"] = "cannot write " + out_path + ": " + os_error(exc)
        return result
    result["ok"] = True
    return result


def parse_args(argv: list[str]) -> tuple[dict, list[str], list[str]]:
    """Flags → (opts, positionals, allow_dirs). Raises BuildError with a message
    both implementations share; no abbreviations, `--flag value` or `--flag=value`."""
    opts = dict(DEFAULTS)
    positional: list[str] = []
    allow: list[str] = []
    valued = ("--font", "--size", "--paper", "--margins", "--align", "--allow-dir")
    switches = {"--toc": "toc", "--page-numbers": "page_numbers", "--hide-spelling-errors": "hide_spelling_errors"}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--"):
            name, eq, value = arg.partition("=")
            if name in switches:
                if eq:
                    raise BuildError(name + " takes no value")
                opts[switches[name]] = True
                i += 1
                continue
            if name not in valued:
                raise BuildError("unknown option " + name)
            if not eq:
                if i + 1 >= len(argv):
                    raise BuildError(name + " needs a value")
                value = argv[i + 1]
                i += 1
            i += 1
            if name == "--font":
                if not value or len(value) > 64 or any(md.forbidden_char(c) for c in value):
                    raise BuildError("--font takes a font name of 1 to 64 characters")
                opts["font"] = value
            elif name == "--size":
                if not _NUMBER.match(value) or not 1 <= float(value) <= 400:
                    raise BuildError("--size takes a number of points from 1 to 400")
                size = float(value)
                opts["size"] = int(size) if size == int(size) else size
            elif name == "--paper":
                if value not in PAPER:
                    raise BuildError("--paper takes a4 or letter")
                opts["paper"] = value
            elif name == "--margins":
                vals = value.split(",")
                if len(vals) != 4 or not all(_NUMBER.match(v) for v in vals):
                    raise BuildError("--margins takes four non-negative numbers: top,right,bottom,left")
                opts["margins"] = tuple(float(v) for v in vals)
            elif name == "--align":
                if value not in ("left", "thai"):
                    raise BuildError("--align takes left or thai")
                opts["align"] = value
            elif name == "--allow-dir":
                allow.append(value)
            continue
        positional.append(arg)
        i += 1
    if len(positional) != 2:
        raise BuildError(USAGE)
    pw, ph = PAPER[opts["paper"]]
    top, right, bottom, left = (half_up(m * 1440) for m in opts["margins"])
    if pw - left - right < MIN_TEXT_TWIPS or ph - top - bottom < MIN_TEXT_TWIPS:
        raise BuildError("--margins leave less than one inch for text")
    return opts, positional, allow


def main(argv: list[str]) -> int:
    try:
        opts, (md_path, out_path), allow = parse_args(argv)
    except BuildError as exc:
        print(json.dumps({"ok": False, "error": exc.what}, ensure_ascii=False))
        return 2
    result = build(md_path, out_path, opts, allow)
    print(json.dumps(result, ensure_ascii=False))
    if result["ok"]:
        return 0
    return 2 if "error" in result else 1
