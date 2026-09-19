# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""What the parsed document declares, before a byte is written: heading styles from the
front matter (ADR 0020), and the regions, sections, captions and lists of ADR 0021 and 0027.

Pure functions on `markdown.Document`; the writer and the fidelity reference both read
their results, so what a list holds and what a caption says is decided once.
"""

from __future__ import annotations

import re

from . import markdown as md
from .settings import NUMBER, half_up


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
                    raise md.Unsupported(line, where + " takes none, or underline and line-through, "
                                         "the underline solid, double, dotted, dashed, wavy or thick")
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
ROMAN = ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"),
         (1, "I"))
SECTION_MARK = "\x00"  # between sections in the body; the input can hold no control character
LIST_FIELDS = {"toc": 'TOC \\o "1-3" \\h \\z \\u', "list-of-tables": 'TOC \\h \\z \\c "Table"', "list-of-figures": 'TOC \\h \\z \\c "Figure"'}
THAI_DIGITS = md.THAI_DIGITS  # the translation lives beside plain_text, which also writes numbers
CAPTION_PREFIX = {"table": "Table:", "figure": "Figure:"}
# What a Thai writer reaches for instead. These make no caption — the prefix is one word,
# written in English, so one rule holds in both languages — but a paragraph that opens with
# one of them where a caption would go is a mistake worth naming (ADR 0021).
THAI_CAPTION_PREFIX = {"table": ("ตาราง:", "ตารางที่:"), "figure": ("รูป:", "รูปที่:", "ภาพ:", "ภาพที่:")}
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


def _thai_caption_kind(b: dict) -> str | None:
    """"table" or "figure" for a paragraph that opens with the Thai words for them."""
    if b["t"] != "paragraph" or not b["inlines"]:
        return None
    first = b["inlines"][0]
    if first["t"] != "text" or any(first.get(k) for k in PLAIN_KEYS):
        return None
    for kind, prefixes in THAI_CAPTION_PREFIX.items():
        for prefix in prefixes:
            s = first["s"]
            if s.startswith(prefix) and (len(s) == len(prefix) or s[len(prefix)] in " \t"):
                return kind
    return None


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
    sub = [0] * 6  # the counter of each heading level, for the numbers the build writes (ADR 0035)
    last_level = 0  # the heading level before this one: a jump leaves a gap in the outline
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
        if b["t"] == "heading":
            _count_heading(b["level"], sub)
            number = _heading_number(b["level"], sub, region if sectioned else "chapters",
                                     sectioned, chapter, appendix, opts)
            if number is not None:
                item["number"] = number
        for n in b.get("inlines", []):
            if n["t"] == "image" and not n["alt"].strip():
                warnings.append("line " + str(b["line"]) + ": the image '" + n["src"]
                                + "' has no text between the brackets of ![]; a reader who cannot see it is told nothing")
        if b["t"] == "heading":
            if b["level"] > last_level + 1 and last_level:
                warnings.append("line " + str(b["line"]) + ": a heading of level " + str(b["level"])
                                + " follows one of level " + str(last_level)
                                + "; the contents and a screen reader read the levels in order")
            last_level = b["level"]
        kind = _caption_kind(b)
        if kind == "table" and not (i + 1 < len(blocks) and blocks[i + 1]["t"] == "table"):
            warnings.append("line " + str(b["line"]) + ": 'Table:' makes a caption only in the paragraph just before a table; kept as text")
            kind = None
        if kind == "figure" and not (i > 0 and _image_only(blocks[i - 1])):
            warnings.append("line " + str(b["line"])
                            + ": 'Figure:' makes a caption only in the paragraph just after an image on its own; kept as text")
            kind = None
        if _figure_in_image_paragraph(b):
            warnings.append("line " + str(b["line"])
                            + ": 'Figure:' shares a paragraph with the image above it; leave a blank line between them to make a caption")
        if kind is None:
            thai = _thai_caption_kind(b)
            in_place = (thai == "table" and i + 1 < len(blocks) and blocks[i + 1]["t"] == "table") or (
                thai == "figure" and i > 0 and _image_only(blocks[i - 1]))
            if in_place:
                warnings.append("line " + str(b["line"]) + ": a caption is written '" + CAPTION_PREFIX[thai]
                                + "' in English, in every language; this paragraph is kept as text")
        if _table_ends_in_caption(b):
            warnings.append("line " + str(b["line"])
                            + ": the table's last row starts with 'Table:'; a caption goes before the table, on its own line")
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


def _count_heading(level: int, sub: list[int]) -> None:
    """A heading advances its own level's counter and starts the deeper ones again."""
    sub[level - 1] += 1
    for k in range(level, len(sub)):
        sub[k] = 0


def _heading_number(level: int, sub: list[int], region: str, sectioned: bool,
                    chapter: int, appendix: int, opts: dict) -> str | None:
    """The number a heading carries, or None for a heading that carries none. Written into the
    document as text rather than left to the application to compute (ADR 0035), so it reads the
    same in every reader — the shapes are the ones Word's numbering drew before: "บทที่ ๑",
    "ภาคผนวก ก", "๑.๑", "ก.๑.๑", and "1." for a document with no regions."""
    if level > 1 and not opts["heading_numbers"]:
        return None
    if sectioned and region not in ("chapters", "appendices"):
        return None
    thai = opts["thai_digits"]
    if region == "appendices":
        if not appendix:
            return None
        first = number_text(appendix, opts["appendix_numbers"], thai)
        label = opts["appendix_label"]
    elif sectioned:
        if not chapter:
            return None
        first = number_text(chapter, "decimal", thai)
        label = opts["chapter_label"]
    else:
        if not opts["heading_numbers"]:
            return None
        first = number_text(sub[0], "decimal", thai)
        label = None
    if level == 1:
        return (label + " " + first) if label is not None else first + "."
    return ".".join([first] + [number_text(sub[k], "decimal", thai) for k in range(1, level)])


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
