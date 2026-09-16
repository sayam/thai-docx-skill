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
import os
import pathlib
import re
import stat
import struct
import unicodedata
from xml.etree import ElementTree as ET

from . import check as check_mod
from . import markdown as md
from . import package
from .ooxml import W, w
from .settings import (  # noqa: F401  the build's settings, and the names callers know them by
    APPENDIX_NUMBERS, DEFAULTS, FRONT_NUMBERS, MIN_TEXT_TWIPS, NUMBER, PAGE_NUMBERS, PAPER, USAGE,
    BuildError, half_up, page_size, parse_args, settings_json,
)

CODE_FONT = "Consolas"
SYMBOL_FONT = "Segoe UI Symbol"
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
_OS_ERRORS = {
    errno.ENOENT: "No such file or directory",
    errno.EACCES: "Permission denied",
    errno.EISDIR: "Is a directory",
    errno.ENOTDIR: "Not a directory",
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def attr(s: str) -> str:
    """An attribute value with its double quotes."""
    return '"' + esc(s).replace('"', "&quot;").replace("\t", "&#9;").replace("\n", "&#10;").replace("\r", "&#13;") + '"'


def os_error(exc: OSError) -> str:
    return _OS_ERRORS.get(exc.errno, "cannot be read")


# --- heading styles from front matter (ADR 0020) ------------------------------------

HEADING_KEY = re.compile(r"heading-([1-6])")  # fullmatch
NEAR_HEADING_KEY = re.compile(r"(?:h|heading)[-_ ]?[0-9]+", re.I)  # fullmatch: a slip worth a warning
_LENGTH = re.compile(r"(-?)([0-9]+(?:\.[0-9]+)?)(in|cm|pt)")  # fullmatch
_POINTS = re.compile(r"([0-9]+(?:\.[0-9]+)?)pt")  # fullmatch
_COLOR = re.compile(r"#[0-9A-Fa-f]{6}")  # fullmatch
MAX_LENGTH_TWIPS = 14400  # 10 in
ALIGN = {"left": "left", "center": "center", "right": "right", "justify": "both", "thai-distribute": "thaiDistribute"}
UNDERLINE = {"solid": "single", "double": "double", "dotted": "dotted", "dashed": "dash", "wavy": "wave", "thick": "thick"}  # thick: Word's, not CSS
HEADING_PROPERTIES = (
    "font-family", "font-size", "color", "font-weight", "font-style", "text-decoration", "text-align",
    "margin-left", "text-indent", "margin-top", "margin-bottom", "line-height", "page-break-before",
)


def _declarations(value: str, line: int, key: str) -> list[tuple[str, str]]:
    """`name: value; name: value` — `;` inside double quotes belongs to the value."""
    pieces, current, quoted = [], "", False
    for ch in value:
        if ch == '"':
            quoted = not quoted
        if ch == ";" and not quoted:
            pieces.append(current)
            current = ""
        else:
            current += ch
    if quoted:
        raise md.Unsupported(line, key + ": a double quote is not closed")
    pieces.append(current)
    out = []
    for piece in pieces:
        piece = piece.strip(" \t")
        if not piece:
            continue
        if ":" not in piece:
            raise md.Unsupported(line, key + ": '" + piece + "' is not a property: value pair")
        name, _, val = piece.partition(":")
        out.append((name.strip(" \t"), val.strip(" \t")))
    return out


def _length(val: str, line: int, where: str, negative: bool) -> int:
    m = _LENGTH.fullmatch(val)
    if val == "0":
        return 0
    if m is None or (m.group(1) and not negative):
        raise md.Unsupported(line, where + " takes a length in in, cm or pt" + ("" if negative else " that is not negative") + ", e.g. 0.5in")
    x = float(m.group(2))
    twips = half_up(x * 1440) if m.group(3) == "in" else half_up(x * 1440 / 2.54) if m.group(3) == "cm" else half_up(x * 20)
    if twips > MAX_LENGTH_TWIPS:
        raise md.Unsupported(line, where + " is at most 10in")
    return -twips if m.group(1) else twips


def heading_styles(doc: md.Document) -> tuple[dict[int, dict], list[str]]:
    """`heading-1` … `heading-6` in the front matter → {level: properties}, and warnings
    for keys that look meant as one. A property or value outside ADR 0020 stops the build."""
    styles: dict[int, dict] = {}
    warnings: list[str] = []
    for key, value in doc.front_matter.items():
        line = doc.front_matter_lines[key]
        m = HEADING_KEY.fullmatch(key)
        if m is None:
            if NEAR_HEADING_KEY.fullmatch(key):
                warnings.append("line " + str(line) + ": front matter key '" + key + "' is not used; heading styles are heading-1 to heading-6")
            continue
        props: dict = {}
        for name, val in _declarations(value, line, key):
            where = key + ": " + name
            if name == "font-family":
                if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                    val = val[1:-1]
                if not val or len(val) > 64 or any(md.forbidden_char(c) for c in val) or '"' in val:
                    raise md.Unsupported(line, where + " takes a font name of 1 to 64 characters")
                props["font"] = val
            elif name == "font-size":
                pm = _POINTS.fullmatch(val)
                if pm is None or not 1 <= float(pm.group(1)) <= 400:
                    raise md.Unsupported(line, where + " takes points from 1pt to 400pt, e.g. 20pt")
                props["size"] = float(pm.group(1))
            elif name == "color":
                if not _COLOR.fullmatch(val):
                    raise md.Unsupported(line, where + " takes #RRGGBB, e.g. #1F4E79")
                props["color"] = val[1:].upper()
            elif name == "font-weight":
                if val not in ("bold", "normal"):
                    raise md.Unsupported(line, where + " takes bold or normal")
                props["bold"] = val == "bold"
            elif name == "font-style":
                if val not in ("italic", "normal"):
                    raise md.Unsupported(line, where + " takes italic or normal")
                props["italic"] = val == "italic"
            elif name == "text-decoration":
                # CSS's `line || style`, in any order; the style is the underline's (Word has no styled strike)
                words = [x for x in re.split(r"[ \t]+", val) if x]
                under, strike, style = False, False, None
                bad = not words
                for word in words if words != ["none"] else []:
                    if word == "underline" and not under:
                        under = True
                    elif word == "line-through" and not strike:
                        strike = True
                    elif word in UNDERLINE and style is None:
                        style = UNDERLINE[word]
                    else:
                        bad = True
                if bad or (style and not under):
                    raise md.Unsupported(line, where + " takes none, or underline and line-through, the underline solid, double, dotted, dashed, wavy or thick")
                props["underline"], props["strike"] = (style or "single") if under else None, strike
            elif name == "text-align":
                if val not in ALIGN:
                    raise md.Unsupported(line, where + " takes left, center, right, justify or thai-distribute")
                props["jc"] = ALIGN[val]
            elif name == "margin-left":
                props["left"] = _length(val, line, where, False)
            elif name == "text-indent":
                props["first"] = _length(val, line, where, True)
            elif name == "margin-top":
                props["before"] = _length(val, line, where, False)
            elif name == "margin-bottom":
                props["after"] = _length(val, line, where, False)
            elif name == "line-height":
                if not NUMBER.fullmatch(val) or not 1 <= float(val) <= 3:
                    raise md.Unsupported(line, where + " takes a multiple of single spacing from 1 to 3")
                props["line"] = half_up(float(val) * 240)
            elif name == "page-break-before":
                if val not in ("always", "auto"):
                    raise md.Unsupported(line, where + " takes always or auto")
                props["break"] = val == "always"
            else:
                raise md.Unsupported(line, key + ": unknown property '" + name + "'; the heading properties are " + ", ".join(HEADING_PROPERTIES))
        styles[int(m.group(1))] = props
    return styles, warnings


# --- regions, sections and captions (ADR 0021) ---------------------------------------

REGIONS = ("front", "chapters", "back", "appendices")
ORDER = "front, chapters, back, appendices, back"  # a second back only after the appendices
def has_thai(text: str) -> bool:
    return any("\u0e00" <= ch <= "\u0e7f" for ch in text)


THAI_LETTERS = "กขคงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ"  # as appendices are lettered: no ฃ or ฅ
ROMAN = ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))
SECTION_MARK = "\x00"  # between sections in the body; the input can hold no control character
LIST_FIELDS = {"toc": 'TOC \\o "1-3" \\h \\z \\u', "list-of-tables": 'TOC \\h \\z \\c "Table"', "list-of-figures": 'TOC \\h \\z \\c "Figure"'}
THAI_DIGITS = str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙")
CAPTION_PREFIX = {"table": "Table:", "figure": "Figure:"}
PLAIN_KEYS = ("link", "code", "b", "i", "strike", "u", "sup", "sub")


def number_text(n: int, fmt: str, thai_digits: bool) -> str:
    """n in a chapter or appendix number format, as the caption's field result shows it."""
    if fmt == "thai-letters":
        return THAI_LETTERS[(n - 1) % len(THAI_LETTERS)] * ((n - 1) // len(THAI_LETTERS) + 1)
    if fmt == "upper-letters":
        return chr(65 + (n - 1) % 26) * ((n - 1) // 26 + 1)
    if fmt == "upper-roman":
        out = ""
        for value, letters in ROMAN:
            while n >= value:
                out, n = out + letters, n - value
        return out
    return str(n).translate(THAI_DIGITS) if thai_digits else str(n)


def _caption_kind(b: dict) -> str | None:
    """"table" or "figure" for a paragraph that opens with plain `Table:` or `Figure:`."""
    if b["t"] != "paragraph" or not b["inlines"]:
        return None
    first = b["inlines"][0]
    if first["t"] != "text" or any(first.get(k) for k in PLAIN_KEYS):
        return None
    for kind, prefix in CAPTION_PREFIX.items():
        s = first["s"]
        if s.startswith(prefix) and (len(s) == len(prefix) or s[len(prefix)] in " \t"):
            return kind
    return None


def _caption_rest(b: dict, kind: str) -> list[dict]:
    first = b["inlines"][0]
    s = first["s"][len(CAPTION_PREFIX[kind]):].lstrip(" \t")
    return ([dict(first, s=s)] if s else []) + b["inlines"][1:]


def _figure_in_image_paragraph(b: dict) -> bool:
    """`Figure:` on the line under an image, with no blank line: one paragraph, no caption."""
    if b["t"] != "paragraph":
        return False
    seen_image = False
    for n in b["inlines"]:
        if n["t"] == "image":
            seen_image = True
        elif n["t"] == "hardbreak" or (n["t"] == "text" and not n["s"].strip(" \t")):
            continue
        elif n["t"] == "text" and seen_image and not any(n.get(k) for k in PLAIN_KEYS):
            s = n["s"].lstrip(" \t")
            return s.startswith("Figure:") and (len(s) == 7 or s[7] in " \t")
        else:
            return False
    return False


def _table_ends_in_caption(b: dict) -> bool:
    """`Table:` on the line under a table, with no blank line: the table's last row."""
    if b["t"] != "table" or len(b["rows"]) < 2:
        return False
    first, rest = b["rows"][-1][0], b["rows"][-1][1:]
    return bool(first) and _caption_kind({"t": "paragraph", "inlines": first}) == "table" and not any(rest)


def _image_only(b: dict) -> bool:
    return b["t"] == "paragraph" and any(n["t"] == "image" for n in b["inlines"]) and all(
        n["t"] == "image" or (n["t"] == "text" and not n["s"].strip(" \t")) for n in b["inlines"])


def layout(doc: md.Document, opts: dict) -> tuple[list[dict], list[str], list[str]]:
    """The top-level blocks as ADR 0021 arranges them → (items, the region of each section,
    warnings). No region comment: no sections, and captions numbered through the document."""
    seen: list[str] = []
    ranks: list[int] = []
    for b in doc.blocks:
        if b["t"] == "directive" and b["name"] in REGIONS:
            rank = 4 if b["name"] == "back" and "appendices" in seen else REGIONS.index(b["name"])
            if rank in ranks:
                again = "; a second <!-- back --> comes only after <!-- appendices -->" if b["name"] == "back" else "; each region comment comes once"
                raise md.Unsupported(b["line"], "<!-- " + b["name"] + " --> is given twice" + again)
            if ranks and rank < ranks[-1]:
                raise md.Unsupported(b["line"], "<!-- " + b["name"] + " --> comes after <!-- " + seen[-1] + " -->; the regions go " + ORDER)
            seen.append(b["name"])
            ranks.append(rank)
    sectioned = bool(seen)
    items: list[dict] = []
    regions = ["cover"] if sectioned else []
    warnings: list[str] = []
    region, pending, has_content, chapter, appendix = "cover", None, False, 0, 0
    counters = {"table": 0, "figure": 0}
    blocks = doc.blocks
    for i, b in enumerate(blocks):
        if b["t"] == "directive" and b["name"] in REGIONS:
            pending = b["name"]
            continue
        heading1 = b["t"] == "heading" and b["level"] == 1
        item: dict = {"block": b, "region": region if pending is None else pending}
        if sectioned and has_content and (pending is not None or heading1):
            item["new_section"] = True
            regions.append(item["region"])
        elif sectioned and pending is not None:
            regions[-1] = pending
        region, pending, has_content = item["region"], None, True
        if sectioned and heading1:
            counters = {"table": 0, "figure": 0}
            if region == "chapters":
                chapter += 1
                item["number"] = opts["chapter_label"] + " " + number_text(chapter, "decimal", opts["thai_digits"])
            elif region == "appendices":
                appendix += 1
                item["number"] = opts["appendix_label"] + " " + number_text(appendix, opts["appendix_numbers"], opts["thai_digits"])
        kind = _caption_kind(b)
        if kind == "table" and not (i + 1 < len(blocks) and blocks[i + 1]["t"] == "table"):
            warnings.append("line " + str(b["line"]) + ": 'Table:' makes a caption only in the paragraph just before a table; kept as text")
            kind = None
        if kind == "figure" and not (i > 0 and _image_only(blocks[i - 1])):
            warnings.append("line " + str(b["line"]) + ": 'Figure:' makes a caption only in the paragraph just after an image on its own; kept as text")
            kind = None
        if _figure_in_image_paragraph(b):
            warnings.append("line " + str(b["line"]) + ": 'Figure:' shares a paragraph with the image above it; leave a blank line between them to make a caption")
        if _table_ends_in_caption(b):
            warnings.append("line " + str(b["line"]) + ": the table's last row starts with 'Table:'; a caption goes before the table, on its own line")
        if kind is not None:
            counters[kind] += 1
            chap = ""
            if region == "chapters" and chapter:
                chap = number_text(chapter, "decimal", opts["thai_digits"])
            elif region == "appendices" and appendix:
                chap = number_text(appendix, opts["appendix_numbers"], opts["thai_digits"])
            seq = number_text(counters[kind], "decimal", opts["thai_digits"])
            item["caption"] = {"kind": kind, "label": opts[kind + "_label"], "chapter": chap, "seq": seq,
                               "reset": sectioned, "inlines": _caption_rest(b, kind)}
            if kind == "table":
                item["keep_next"] = True
            else:
                items[-1]["keep_next"] = True
        items.append(item)
    return items, regions, warnings


def _end_section(xml: str, sect: str) -> str:
    """Close a section in the properties of its last top-level paragraph — a table's is the
    empty paragraph after it — so no empty paragraph can spill onto a page of its own."""
    at = xml.rindex("<w:p>")
    if xml.startswith("<w:p><w:pPr/>", at):
        return xml[:at] + "<w:p><w:pPr>" + sect + "</w:pPr>" + xml[at + len("<w:p><w:pPr/>"):]
    end = xml.index("</w:pPr>", at)
    return xml[:end] + sect + xml[end:]


LIST_KINDS = {"list-of-tables": "table", "list-of-figures": "figure"}


def list_entries(items: list[dict], name: str) -> list[tuple[int, str]]:
    """What a table of contents, tables or figures holds, as (heading level, text).
    Written into the field so an application that never updates fields still shows it;
    Word, which does update, replaces it with its own — with the page numbers only a
    layout knows (ADR 0027)."""
    out: list[tuple[int, str]] = []
    for item in items:
        b = item["block"]
        if name == "toc":
            if "caption" not in item and b["t"] == "heading" and b["level"] <= 3:
                number = item["number"] + " " if "number" in item else ""
                out.append((b["level"], _one_line(number + md.inline_text(b["inlines"]))))
        elif "caption" in item and item["caption"]["kind"] == LIST_KINDS[name]:
            out.append((1, _one_line(caption_text(item["caption"]))))
    return out


def _one_line(text: str) -> str:
    """An entry is one line: a heading broken over two lines reads as one in the list."""
    return " ".join(text.split("\n"))


def caption_text(c: dict) -> str:
    """What a caption paragraph reads as: its label and number, then the Markdown's text."""
    number = (c["chapter"] + "-" if c["chapter"] else "") + c["seq"]
    return c["label"] + " " + number + (" " + md.inline_text(c["inlines"]) if c["inlines"] else "")


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
    def __init__(self, doc: md.Document, opts: dict, read_image):
        """`read_image(src)` returns (resolved path, bytes), or raises BuildError."""
        self.doc, self.opts = doc, opts
        self.read_image = read_image
        self.rels: list[tuple[str, str, str, bool]] = []  # id, type, target, external
        self.media: list[tuple[str, bytes]] = []  # part name, bytes
        self.image_rel: dict[str, tuple[str, int, int]] = {}
        self.nums: list[tuple[int, int, int]] = []  # numId, start, level
        self.doc_pr = 0
        self.heading_props, self.style_warnings = heading_styles(doc)
        self.items, self.regions, self.layout_warnings = layout(doc, opts)
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

    def paragraph(self, inlines: list[dict], style: str | None = None, ppr: str = "", bold: bool = False, lead: str = "") -> str:
        head = ('<w:pStyle w:val="' + style + '"/>' if style else "") + ppr
        self.counts["paragraphs"] += 1
        return "<w:p><w:pPr>" + head + self.latin_jc(head, md.inline_text(inlines)) + "</w:pPr>" + lead + self.inlines(inlines, bold) + "</w:p>"

    def latin_jc(self, head: str, text: str) -> str:
        """Thai distributed fills a line by spreading what is on it, which is how Thai is set
        — it has no spaces between words — and not how English is: a paragraph with no Thai in
        it keeps the ordinary left alignment, so "(2024a)" does not come out as "( 2 0 2 4 a)"
        and a title does not stretch across the page. Alignment only — ADR 0023 stands."""
        if self.opts["align"] != "thai" or "<w:jc " in head or not text or has_thai(text):
            return ""
        return '<w:jc w:val="left"/>'

    def title_break(self, item: dict) -> str:
        """--chapter-title-on-new-line: the number Word writes keeps the first line and the
        heading's own text starts the next one. OOXML gives a level no such suffix — nothing,
        a space or a tab — so the break belongs to the heading (ADR 0027)."""
        if not self.opts["chapter_title_on_new_line"] or "number" not in item:
            return ""
        return "<w:r><w:rPr>" + LANG + "</w:rPr><w:br/></w:r>"

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
            elif b["t"] == "heading" and self.regions and item["region"] != "chapters" and b["level"] in self.numbered_levels():
                # appendices take their own list ("ภาคผนวก ก"); headings in any other region, none
                self.counts["headings"] += 1
                if item["region"] == "appendices":
                    num = '<w:numPr><w:ilvl w:val="' + str(b["level"] - 1) + '"/><w:numId w:val="' + str(self.heading_num_id() + 1) + '"/></w:numPr>'
                else:
                    num = '<w:numPr><w:numId w:val="0"/></w:numPr>'
                out.append(self.paragraph(b["inlines"], "Heading" + str(b["level"]), num, lead=self.title_break(item)))
            elif b["t"] == "heading" and self.title_break(item):
                self.counts["headings"] += 1
                out.append(self.paragraph(b["inlines"], "Heading" + str(b["level"]), lead=self.title_break(item)))
            else:
                out.append(self.blocks([b], body=True, keep_next=item.get("keep_next", False)))
        return "".join(out)

    def caption(self, c: dict, keep_next: bool) -> str:
        """Label, chapter number and SEQ number, bold, with their results written in — an
        application that never updates fields still shows them — then the caption text."""
        self.counts["paragraphs"] += 1
        bold = "<w:b/><w:bCs/>"

        def run(text: str, rpr: str) -> str:
            return "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:t xml:space="preserve">' + esc(text) + "</w:t></w:r>"

        ppr = '<w:pStyle w:val="Caption"/>' + ("<w:keepNext/>" if keep_next else "") + ('<w:jc w:val="center"/>' if c["kind"] == "figure" else "")
        ppr += self.latin_jc(ppr, caption_text(c))
        out = "<w:p><w:pPr>" + ppr + "</w:pPr>" + run(c["label"] + " ", bold)
        if c["chapter"]:
            out += self.field_runs("STYLEREF 1 \\s", c["chapter"], bold) + run("-", bold)
        seq = "SEQ " + c["kind"].capitalize() + " \\* " + ("ThaiArabic" if self.opts["thai_digits"] else "ARABIC") + (" \\s 1" if c["reset"] else "")
        out += self.field_runs(seq, c["seq"], bold)
        rest = c["inlines"]
        if rest and rest[0]["t"] == "text":
            # the space joins the first text run: a run of its own would sit beside one formatted alike (cause 4)
            out += self.inlines([dict(rest[0], s=" " + rest[0]["s"])] + rest[1:])
        elif rest:
            out += run(" ", "") + self.inlines(rest)
        return out + "</w:p>"

    def field_runs(self, instr: str, result: str, rpr: str) -> str:
        return (
            "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
            "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:instrText xml:space="preserve"> ' + instr + " </w:instrText></w:r>"
            "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:fldChar w:fldCharType="separate"/></w:r>'
            "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:t xml:space="preserve">' + result + "</w:t></w:r>"
            "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:fldChar w:fldCharType="end"/></w:r>'
        )

    def numbered_levels(self) -> set[int]:
        """Heading levels Word numbers: the chapter level whenever there are chapters, the rest with --heading-numbers."""
        rest = set(range(2, 7)) if self.opts["heading_numbers"] else set()
        return ({1} | rest) if self.has_chapters else ({1} | rest if self.opts["heading_numbers"] else set())

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
                ppr = ('<w:pStyle w:val="TableText"/>' if self.opts["table_size"] is not None else "") + '<w:spacing w:after="0"/>' + ('<w:jc w:val="' + jc + '"/>' if jc in ("center", "right") else "")
                cells.append('<w:tc><w:tcPr><w:tcW w:w="' + str(widths[ci]) + '" w:type="dxa"/></w:tcPr>' + self.paragraph(cell, None, ppr, ri == 0) + "</w:tc>")
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
        char = lambda kind: "<w:r><w:rPr>" + LANG + '</w:rPr><w:fldChar w:fldCharType="' + kind + '"/></w:r>'
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

    def document_xml(self, body: str) -> str:
        pw, ph, top, right, bottom, left = self.page
        rids = []  # (kind, numbered part, plain part)
        for kind in self.page_parts():
            numbered = self.rel(REL + kind, kind + "1.xml")
            rids.append((kind, numbered, self.rel(REL + kind, kind + "2.xml") if self.plain_page_part() else None))
        toc = self.field('TOC \\o "1-3" \\h \\z \\u', entries=list_entries(self.items, "toc")) + "<w:p><w:pPr/></w:p>" if self.opts["toc"] else ""
        numbers = "thaiNumbers" if self.opts["thai_digits"] else "decimal"

        def sect(region: str | None, start: bool) -> str:
            """A cover shows the plain parts; front pages count ก ข ค from ก, the rest from 1."""
            refs = ""
            for kind, numbered, plain in rids:
                if region == "cover":
                    refs += '<w:' + kind + 'Reference w:type="default" r:id="' + plain + '"/>'
                    continue
                refs += '<w:' + kind + 'Reference w:type="default" r:id="' + numbered + '"/>'
                if self.title_page():
                    refs += '<w:' + kind + 'Reference w:type="first" r:id="' + plain + '"/>'
            if region is None:
                pg = '<w:pgNumType w:fmt="thaiNumbers"/>' if self.opts["thai_digits"] else ""
            elif region == "cover":
                pg = ""
            else:
                front = FRONT_NUMBERS[self.opts["front_page_numbers"]]
                front = "thaiNumbers" if front == "decimal" and self.opts["thai_digits"] else front
                pg = '<w:pgNumType w:fmt="' + (front if region == "front" else numbers) + '"' + (' w:start="1"' if start else "") + "/>"
            return (
                "<w:sectPr>" + refs + self.footnote_format() + '<w:pgSz w:w="' + str(pw) + '" w:h="' + str(ph) + '"' + (' w:orient="landscape"' if self.opts["landscape"] else "") + "/>"
                '<w:pgMar w:top="' + str(top) + '" w:right="' + str(right) + '" w:bottom="' + str(bottom) + '" w:left="' + str(left)
                + '" w:header="720" w:footer="720" w:gutter="0"/>' + pg
                + ("<w:titlePg/>" if self.title_page() and region != "cover" else "") + "</w:sectPr>"
            )

        if not self.regions:
            body += sect(None, False)
        else:
            pieces, started = body.split(SECTION_MARK), set()
            for k, region in enumerate(self.regions):
                group = "front" if region == "front" else "cover" if region == "cover" else "numbered"
                xml = sect(region, group not in started)
                started.add(group)
                pieces[k] = pieces[k] + xml if k == len(self.regions) - 1 else _end_section(pieces[k], xml)
            body = "".join(pieces)
        return (
            XML + '<w:document xmlns:w="' + W + '" xmlns:r="' + NS_R + '" '
            'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            "<w:body>" + toc + body + "</w:body></w:document>"
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
            """The built-in look, with what the front matter's heading-n changes (ADR 0020)."""
            p = self.heading_props.get(n, {})
            face = attr(p["font"]) if "font" in p else ""
            pt = p.get("size", pt)
            rpr = (
                ("<w:rFonts w:ascii=" + face + " w:hAnsi=" + face + " w:cs=" + face + " w:eastAsia=" + face + "/>" if face else "")
                + ("<w:b/><w:bCs/>" if p.get("bold", bold) else "") + ("<w:i/><w:iCs/>" if p.get("italic", italic) else "")
                + ("<w:strike/>" if p.get("strike") else "")
                + ('<w:color w:val="' + p["color"] + '"/>' if "color" in p else "")
                + '<w:sz w:val="' + hp(pt) + '"/><w:szCs w:val="' + hp(pt) + '"/>'
                + ('<w:u w:val="' + p["underline"] + '"/>' if p.get("underline") else "")
            )
            num = '<w:numPr><w:ilvl w:val="' + str(n - 1) + '"/><w:numId w:val="' + str(self.heading_num_id()) + '"/></w:numPr>' if n in self.numbered_levels() else ""
            spacing = '<w:spacing w:before="' + str(p.get("before", 240 if n == 1 else 200)) + '" w:after="' + str(p.get("after", 80)) + '"'
            spacing += (' w:line="' + str(p["line"]) + '" w:lineRule="auto"/>') if "line" in p else "/>"
            ind = ""
            if "left" in p or "first" in p:
                ind = "<w:ind" + (' w:left="' + str(p["left"]) + '"' if "left" in p else "")
                if "first" in p:
                    ind += (' w:hanging="' + str(-p["first"]) + '"') if p["first"] < 0 else (' w:firstLine="' + str(p["first"]) + '"')
                ind += "/>"
            return (
                '<w:style w:type="paragraph" w:styleId="Heading' + str(n) + '"><w:name w:val="heading ' + str(n) + '"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
                "<w:pPr><w:keepNext/><w:keepLines/>" + ("<w:pageBreakBefore/>" if p.get("break") else "") + num + spacing + ind
                + '<w:jc w:val="' + p.get("jc", "left") + '"/><w:outlineLvl w:val="' + str(n - 1) + '"/></w:pPr>'
                "<w:rPr>" + rpr + "</w:rPr></w:style>"
            )

        def own(style_id: str, name: str, ppr: str = "") -> str:
            """A style Word applies itself (a TOC entry, a header): missing from the file, Word
            takes its own template's definition — another font and size — so it is written out."""
            return (
                '<w:style w:type="paragraph" w:styleId="' + style_id + '"><w:name w:val="' + name + '"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/>'
                + ("<w:pPr>" + ppr + "</w:pPr>" if ppr else "")
                + "<w:rPr><w:rFonts w:ascii=" + font + " w:hAnsi=" + font + " w:cs=" + font + " w:eastAsia=" + font + "/>"
                '<w:sz w:val="' + hp(size) + '"/><w:szCs w:val="' + hp(size) + '"/></w:rPr></w:style>'
            )

        applied = ""
        if self.opts["toc"]:
            applied += own("TOC1", "toc 1") + own("TOC2", "toc 2", '<w:ind w:left="240"/>') + own("TOC3", "toc 3", '<w:ind w:left="480"/>')
        for kind in self.page_parts():
            applied += own(kind.capitalize(), kind)
        if any("caption" in item for item in self.items):
            applied += own("Caption", "caption", '<w:spacing w:before="120" w:after="120"/>')
        if any(item["block"]["t"] == "directive" and item["block"]["name"] != "toc" for item in self.items):
            applied += own("TableofFigures", "table of figures")
        if any(item["block"]["t"] == "directive" and item["block"]["name"] == "toc" for item in self.items) and not self.opts["toc"]:
            applied += own("TOC1", "toc 1") + own("TOC2", "toc 2", '<w:ind w:left="240"/>') + own("TOC3", "toc 3", '<w:ind w:left="480"/>')
        if self.opts["table_size"] is not None:
            pt = hp(self.opts["table_size"])
            applied += ('<w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/><w:basedOn w:val="Normal"/><w:qFormat/>'
                        '<w:rPr><w:sz w:val="' + pt + '"/><w:szCs w:val="' + pt + '"/></w:rPr></w:style>')

        return (
            XML + '<w:styles xmlns:w="' + W + '">'
            "<w:docDefaults><w:rPrDefault><w:rPr>"
            "<w:rFonts w:ascii=" + font + " w:hAnsi=" + font + " w:cs=" + font + " w:eastAsia=" + font + "/>"
            '<w:sz w:val="' + hp(size) + '"/><w:szCs w:val="' + hp(size) + '"/><w:cs/><w:lang w:val="en-US" w:eastAsia="en-US" w:bidi="th-TH"/>'
            "</w:rPr></w:rPrDefault><w:pPrDefault><w:pPr>"
            '<w:spacing w:after="120" w:line="' + str(half_up(self.opts["line_spacing"] * 240)) + '" w:lineRule="auto"/>' + jc
            + "</w:pPr></w:pPrDefault></w:docDefaults>"
            # Normal repeats what the defaults above already say: an application that reads
            # styles but not w:docDefaults (WPS numbers one) then still has the font and size
            '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:rPr>'
            "<w:rFonts w:ascii=" + font + " w:hAnsi=" + font + " w:cs=" + font + " w:eastAsia=" + font + "/>"
            '<w:sz w:val="' + hp(size) + '"/><w:szCs w:val="' + hp(size) + '"/>' + LANG + "</w:rPr></w:style>"
            + heading(1, size + 4, True, False) + heading(2, size + 2, True, False) + heading(3, size, True, False)
            + heading(4, size, True, True) + heading(5, size, True, False) + heading(6, size, False, True)
            + '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:ind w:left="720"/><w:contextualSpacing/></w:pPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:ind w:left="720" w:right="720"/></w:pPr><w:rPr><w:i/><w:iCs/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="CodeBlock"><w:name w:val="Code Block"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr><w:rPr><w:rFonts w:ascii="'
            + CODE_FONT + '" w:hAnsi="' + CODE_FONT + '" w:cs=' + font + '/><w:sz w:val="' + hp(small) + '"/><w:szCs w:val="' + hp(small) + '"/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="FootnoteText"><w:name w:val="footnote text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:left="360" w:hanging="360"/></w:pPr><w:rPr><w:sz w:val="'
            + hp(small) + '"/><w:szCs w:val="' + hp(small) + '"/></w:rPr></w:style>'
            '<w:style w:type="character" w:styleId="FootnoteReference"><w:name w:val="footnote reference"/><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>'
            '<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:rPr><w:rFonts w:ascii=' + font + " w:hAnsi=" + font + " w:cs=" + font + '/><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr></w:style>'
            + applied +
            "</w:styles>"
        )

    def heading_num_id(self) -> int:
        """After every ordered list's numId, which the body has handed out by the time styles are written."""
        return len(self.nums) + 2

    def numbering_xml(self) -> str:
        font, size = attr(self.opts["font"]), self.opts["size"]
        fmt = "thaiNumbers" if self.opts["thai_digits"] else "decimal"
        # a level with no font of its own is drawn in the application's default, which need
        # not carry Thai: WPS showed "บทที่ ๑" as Latin letters until every level named one
        half = str(half_up(size * 2))
        level_font = ("<w:rPr><w:rFonts w:ascii=" + font + " w:hAnsi=" + font + " w:cs=" + font + "/>"
                      '<w:sz w:val="' + half + '"/><w:szCs w:val="' + half + '"/>' + LANG + "</w:rPr>")
        bullet = "".join(
            '<w:lvl w:ilvl="' + str(l) + '"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>'
            '<w:pPr><w:ind w:left="' + str(720 * (l + 1)) + '" w:hanging="360"/></w:pPr>' + level_font + "</w:lvl>"
            for l in range(9)
        )
        decimal = "".join(
            '<w:lvl w:ilvl="' + str(l) + '"><w:start w:val="1"/><w:numFmt w:val="' + fmt + '"/><w:lvlText w:val="%' + str(l + 1) + '."/><w:lvlJc w:val="left"/>'
            '<w:pPr><w:ind w:left="' + str(720 * (l + 1)) + '" w:hanging="360"/></w:pPr>' + level_font + "</w:lvl>"
            for l in range(9)
        )
        nums = '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>' + "".join(
            '<w:num w:numId="' + str(nid) + '"><w:abstractNumId w:val="1"/><w:lvlOverride w:ilvl="' + str(min(level, 8))
            + '"><w:startOverride w:val="' + str(start) + '"/></w:lvlOverride></w:num>'
            for nid, start, level in self.nums
        )
        headings = ""
        levels_on = self.numbered_levels()
        if levels_on:
            # "1." for a # heading — "บทที่ 1" with chapters — then "1.1", "1.1.1" ... followed by a space, no hanging indent
            def lvl_text(l: int) -> str:
                if l == 0:
                    return self.opts["chapter_label"] + " %1" if self.has_chapters else "%1."
                return ".".join("%" + str(k + 1) for k in range(l + 1))

            levels = "".join(
                '<w:lvl w:ilvl="' + str(l) + '"><w:start w:val="1"/><w:numFmt w:val="' + fmt + '"/>'
                + ('<w:pStyle w:val="Heading' + str(l + 1) + '"/>' if l + 1 in levels_on else "")
                + '<w:suff w:val="space"/><w:lvlText w:val=' + attr(lvl_text(l)) + '/><w:lvlJc w:val="left"/>' + level_font + "</w:lvl>"
                for l in range(9)
            )
            headings = '<w:abstractNum w:abstractNumId="2"><w:multiLevelType w:val="multilevel"/>' + levels + "</w:abstractNum>"
            nums += '<w:num w:numId="' + str(self.heading_num_id()) + '"><w:abstractNumId w:val="2"/></w:num>'
        if "appendices" in self.regions:
            # "ภาคผนวก ก", then "ก.1", "ก.1.1" with --heading-numbers; set on each heading, linked to no style
            first = APPENDIX_NUMBERS[self.opts["appendix_numbers"]]
            first = "thaiNumbers" if first == "decimal" and self.opts["thai_digits"] else first
            headings += '<w:abstractNum w:abstractNumId="3"><w:multiLevelType w:val="multilevel"/>' + "".join(
                '<w:lvl w:ilvl="' + str(l) + '"><w:start w:val="1"/><w:numFmt w:val="' + (first if l == 0 else fmt) + '"/>'
                + '<w:suff w:val="space"/><w:lvlText w:val=' + attr(self.opts["appendix_label"] + " %1" if l == 0 else ".".join("%" + str(k + 1) for k in range(l + 1)))
                + '/><w:lvlJc w:val="left"/>' + level_font + "</w:lvl>"
                for l in range(9)
            ) + "</w:abstractNum>"
            nums += '<w:num w:numId="' + str(self.heading_num_id() + 1) + '"><w:abstractNumId w:val="3"/></w:num>'
        return (
            XML + '<w:numbering xmlns:w="' + W + '">'
            '<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="hybridMultilevel"/>' + bullet + "</w:abstractNum>"
            '<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="hybridMultilevel"/>' + decimal + "</w:abstractNum>"
            + headings + nums + "</w:numbering>"
        )

    def settings_xml(self) -> str:
        parts = []
        if self.opts["hide_spelling_errors"]:
            parts.append("<w:hideSpellingErrors/><w:hideGrammaticalErrors/>")
        parts.append('<w:defaultTabStop w:val="720"/><w:characterSpacingControl w:val="doNotCompress"/>')
        if self.opts["toc"] or any(item["block"]["t"] == "directive" for item in self.items):
            parts.append('<w:updateFields w:val="true"/>')
        if self.doc.footnote_order:
            fmt = '<w:numFmt w:val="thaiNumbers"/>' if self.opts["thai_digits"] else ""
            parts.append("<w:footnotePr>" + fmt + '<w:footnote w:id="-1"/><w:footnote w:id="0"/></w:footnotePr>')
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

    def footnote_format(self) -> str:
        """Thai-digit footnote marks, for the section; settings.xml says the same for the document."""
        return '<w:footnotePr><w:numFmt w:val="thaiNumbers"/></w:footnotePr>' if self.opts["thai_digits"] and self.doc.footnote_order else ""

    def page_number_part(self) -> str:
        """Where the page number goes; only when there is one."""
        return "footer" if self.opts["page_numbers"].startswith("bottom-") else "header"

    def page_parts(self) -> list[str]:
        """"header", "footer", both or neither: where --header, --footer and --page-numbers put something."""
        where = self.opts["page_numbers"]
        return [kind for kind in ("header", "footer")
                if self.opts[kind] is not None or (where and self.page_number_part() == kind)]

    def plain_page_part(self) -> bool:
        """A header or footer without the page number: for a first page without it, and a cover."""
        return self.title_page() or (bool(self.regions) and self.regions[0] == "cover")

    def title_page(self) -> bool:
        return bool(self.opts["page_numbers"]) and not self.opts["page_number_on_first"]

    def page_part_xml(self, kind: str, first: bool) -> str:
        """The text of --header or --footer, centred, then the page number when it goes
        here — except on a first page that goes without it. A part with neither is written
        out empty, so no application falls back to the numbered one."""
        style = '<w:pStyle w:val="' + kind.capitalize() + '"/>'
        body = ""
        if self.opts[kind] is not None:
            body += ("<w:p><w:pPr>" + style + '<w:jc w:val="center"/></w:pPr><w:r><w:rPr>' + LANG + '</w:rPr><w:t xml:space="preserve">'
                     + esc(self.opts[kind]) + "</w:t></w:r></w:p>")
        if self.opts["page_numbers"] and self.page_number_part() == kind and not first:
            body += self.field("PAGE", style + '<w:jc w:val="' + self.opts["page_numbers"].split("-")[1] + '"/>')
        tag = "hdr" if kind == "header" else "ftr"
        return XML + "<w:" + tag + ' xmlns:w="' + W + '">' + (body or "<w:p><w:pPr>" + style + "</w:pPr></w:p>") + "</w:" + tag + ">"

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
        body = self.body()
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
        footnotes = None
        if self.doc.footnote_order:
            self.rel(REL + "footnotes", "footnotes.xml")
            overrides.append(("/word/footnotes.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"))
            footnotes = self.footnotes_xml()
        page_parts = []  # (part name, xml)
        for kind in self.page_parts():
            for n, first in (("1", False), ("2", True)) if self.plain_page_part() else (("1", False),):
                overrides.append(("/word/" + kind + n + ".xml", "application/vnd.openxmlformats-officedocument.wordprocessingml." + kind + "+xml"))
                page_parts.append(("word/" + kind + n + ".xml", self.page_part_xml(kind, first)))
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
        parts.extend(page_parts)
        parts.append(("word/_rels/document.xml.rels", XML + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                      + "".join('<Relationship Id="' + rid + '" Type="' + kind + '" Target=' + attr(target) + (' TargetMode="External"/>' if ext else "/>")
                                for rid, kind, target, ext in self.rels)
                      + "</Relationships>"))
        parts.extend(self.media)
        return [(name, data.encode("utf-8") if isinstance(data, str) else data) for name, data in parts]


pack = package.pack  # stored entries, fixed metadata (ADR 0017)


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


def by_line(messages: list[str]) -> list[str]:
    """`line N: …` messages in line order; messages on one line keep theirs."""
    return sorted(messages, key=lambda m: int(m.split(":")[0].split()[1]))


def expected_text(doc: md.Document, opts: dict | None = None) -> list[str]:
    opts = opts or DEFAULTS
    out = []
    items = layout(doc, opts)[0]
    if opts["toc"]:
        out.extend(text for _, text in list_entries(items, "toc"))  # the entries the field carries
    for item in items:
        if "caption" in item:
            out.append(caption_text(item["caption"]))
        elif item["block"]["t"] == "directive" and item["block"]["name"] in LIST_FIELDS:
            out.extend(text for _, text in list_entries(items, item["block"]["name"]))
        elif opts["chapter_title_on_new_line"] and "number" in item and item["block"]["t"] == "heading":
            out.extend("\n" + line for line in md.plain_text([item["block"]]))
        else:
            out.extend(md.plain_text([item["block"]]))
    for label in doc.footnote_order:
        blocks = doc.footnotes[label]
        if not blocks or blocks[0]["t"] != "paragraph":
            out.append("")
        out.extend(md.plain_text(blocks))
    return [unicodedata.normalize("NFC", s) for s in out]


# --- entry ---------------------------------------------------------------------


def build_text(text: str, opts: dict, read_image) -> tuple[dict, bytes | None]:
    """The whole build except reading the Markdown and writing the file: the part
    both implementations must agree on byte for byte."""
    result: dict = {}
    try:
        doc = md.parse(text)
        writer = Writer(doc, opts, read_image)
        parts = writer.package()
    except md.Unsupported as exc:
        return {"error": exc.what, "line": exc.line}, None
    except BuildError as exc:
        return {"error": exc.what}, None
    data = pack(parts)
    report = check_mod.check(io.BytesIO(data))
    findings = list(report.findings)
    if not findings:
        expected, actual = expected_text(doc, opts), docx_text(dict(parts), len(doc.footnote_order))
        if expected != actual:
            # the runs may differ in length; the first difference, or where the shorter ends
            idx = next((i for i, (a, b) in enumerate(zip(expected, actual)) if a != b), min(len(expected), len(actual)))  # noqa: B905
            findings.append({"code": "fidelity", "part": "word/document.xml",
                             "message": "paragraph " + str(idx + 1) + " does not match the Markdown (" + str(len(expected))
                             + " paragraphs expected, " + str(len(actual)) + " written)"})
    # a flag that changed nothing is said out loud, never dropped in silence
    settings_warnings = []
    if opts["chapter_title_on_new_line"] and not any("number" in item for item in writer.items):
        settings_warnings.append("--chapter-title-on-new-line changed nothing: the document has no"
                                 " <!-- chapters --> or <!-- appendices --> comment, so no heading carries a number")
    result.update(
        counts={**writer.counts, "runs": report.counts.get("runs", 0)},
        warnings=[{"code": "markdown", "message": m} for m in by_line(writer.style_warnings + writer.layout_warnings + doc.warnings)]
        + [{"code": "settings", "message": m} for m in settings_warnings] + report.warnings,
        findings=findings,
        sha256=hashlib.sha256(data).hexdigest(),
        bytes=len(data),
    )
    return result, (None if findings else data)


MAX_LINKS = 40


def _split_root(path: str) -> tuple[str, list[str]]:
    drive, rest = os.path.splitdrive(path)
    parts = re.split(r"[\\/]", rest) if os.sep == "\\" else rest.split("/")
    return drive + os.sep, [part for part in parts if part not in ("", ".")]


def _parent(path: str, root: str) -> str:
    cut = path.rstrip(os.sep).rfind(os.sep)
    return root if cut < len(root) else path[:cut]


def real_path(path: str) -> str:
    """The path as the file system walks it: each component's symbolic link
    followed, `..` taken from what is already resolved. A component that does not
    exist, or a link past the fortieth, stays as written. js/90-entry.js walks it
    the same way, so both implementations judge ADR 0011 §4 on the same file."""
    if not os.path.isabs(path):
        path = os.getcwd() + os.sep + path
    root, pending = _split_root(path)
    pending.reverse()
    resolved, links = root, 0
    while pending:
        part = pending.pop()
        if part == "..":
            resolved = _parent(resolved, root)
            continue
        candidate = resolved + part if resolved.endswith(os.sep) else resolved + os.sep + part
        try:
            is_link = stat.S_ISLNK(os.lstat(candidate).st_mode)
        except (OSError, ValueError):
            is_link = False
        if not is_link or links >= MAX_LINKS:
            resolved = candidate
            continue
        links += 1
        try:
            target = os.readlink(candidate)
        except (OSError, ValueError):
            resolved = candidate
            continue
        if os.path.isabs(target):
            root, parts = _split_root(target)
            resolved = root
        else:
            _, parts = _split_root(os.sep + target)
        pending.extend(reversed(parts))
    return resolved


def _inside(path: str, directory: str) -> bool:
    return path == directory or path.startswith(directory if directory.endswith(os.sep) else directory + os.sep)


def image_reader(md_dir: str, allow_dirs: list[str]):
    roots = [md_dir] + allow_dirs

    def read(src: str) -> tuple[str, bytes]:
        path = real_path(src if os.path.isabs(src) else md_dir + os.sep + src)
        if not any(_inside(path, root) for root in roots):
            raise BuildError("image '" + src + "' lies outside the Markdown file's directory; pass --allow-dir for its directory (ADR 0011 §4)")
        try:
            with open(path, "rb") as f:
                return path, f.read()
        except OSError as exc:
            raise BuildError("image '" + src + "': " + os_error(exc)) from None
        except ValueError:  # a path the OS cannot name, e.g. with a NUL
            raise BuildError("image '" + src + "': cannot be read") from None

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
    resolved = real_path(md_path)
    reader = image_reader(_parent(resolved, _split_root(resolved)[0]), [real_path(str(d)) for d in allow_dirs])
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


def main(argv: list[str]) -> int:
    from . import profiles  # here: profiles reads this module's defaults and flags

    try:
        argv, used = profiles.expand(argv)
        opts, (md_path, out_path), allow = parse_args(argv)
    except (BuildError, profiles.ProfileError) as exc:
        print(json.dumps({"ok": False, "error": exc.what}, ensure_ascii=False))
        return 2
    result = build(md_path, out_path, opts, allow)
    if used is not None:
        result["profile"] = used
    print(json.dumps(result, ensure_ascii=False))
    if result["ok"]:
        return 0
    return 2 if "error" in result else 1
