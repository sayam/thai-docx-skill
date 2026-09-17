# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""The settings of a build, in one registry (ADR 0028).

Every setting is one entry: its flag, its kind, its default, the layer it belongs to, how
a value is read and what the refusal says, what it needs, and the name the build reports
it under. The defaults, the usage line, the parser, the reported settings and the flags a
profile may hold are all derived from the entries; `js/45-settings.js` holds the same
entries, and a test holds the two equal.

Kinds: `value` takes a value; `option` takes one or is left out (None, or False for the
page numbers); `list` takes numbers separated by commas; `switch` turns a setting on;
`off` turns a setting that is on by default off.
"""

from __future__ import annotations

import math
import re

from . import markdown as md

PAPER = {"a4": (11906, 16838), "letter": (12240, 15840), "f14": (12240, 18720)}  # f14: 8.5 x 13 in, folio
PAGE_NUMBERS = ("top-right", "top-center", "bottom-center")  # the first is --page-numbers with no position
# page numbers before the chapters, and appendix numbers: flag value → Word's number format
FRONT_NUMBERS = {"thai-letters": "thaiLetters", "lower-roman": "lowerRoman", "upper-roman": "upperRoman", "decimal": "decimal"}
APPENDIX_NUMBERS = {"thai-letters": "thaiLetters", "upper-letters": "upperLetter", "decimal": "decimal", "upper-roman": "upperRoman"}
MIN_TEXT_TWIPS = 1440
# layers (ADR 0028): 1 page and type, 2 page furniture, 3 tables, 4 headings, 5 thesis structure
LAYERS = {1: "page and type", 2: "page furniture", 3: "tables", 4: "headings", 5: "thesis structure"}
# what a document may hold that a setting needs (ADR 0028): the name a registry entry says in
# `needs` or `clashes` → (the thing, as the settings reference names it; why the flag did nothing)
STRUCTURES = {
    "tables": ("a table", "the document has no table"),
    "table captions": ("a `Table:` caption", "the document has no 'Table:' caption"),
    "figure captions": ("a `Figure:` caption", "the document has no 'Figure:' caption"),
    "chapters or appendices": ("a `<!-- chapters -->` or `<!-- appendices -->` comment",
                               "the document has no <!-- chapters --> or <!-- appendices --> comment"),
    "numbered headings": ("a `#` heading under `<!-- chapters -->` or `<!-- appendices -->`",
                          "no heading carries a chapter or appendix number; a # heading under <!-- chapters --> or <!-- appendices --> does"),
    "appendices": ("an `<!-- appendices -->` comment", "the document has no <!-- appendices --> comment"),
    "front": ("a `<!-- front -->` comment", "the document has no <!-- front --> comment"),
}
# (what the document places, as the reference names it; what the flag then does; the warning)
CLASHES = {
    "toc comment": ("a `<!-- toc -->` comment", "makes a second table of contents",
                    "the document places a table of contents with <!-- toc --> as well, so it now has two"),
}

# read: ("text", most characters, characters refused besides the forbidden ones)
#       ("points", least, most) — a whole number stays an integer
#       ("number", least or None, most or None) — always a float
#       ("numbers", how many) — floats, comma-separated
#       ("choice", values) and ("position", values) — the second may be left out
# report: (the name in the build's "settings", "value" | "float" | "sides")
# needs: a setting that must be on too (refused without it), or a structure in STRUCTURES (the
#        build warns that the flag changed nothing when the document lacks it)
# clashes: a structure in CLASHES the setting duplicates (the build warns)
# doc: (the setting, its default, the flag with an example) — the row of references/settings.md
SETTINGS: tuple[dict, ...] = (
    {"key": "font", "flag": "--font", "kind": "value", "default": "TH Sarabun New", "layer": 1,
     "read": ("text", 64, ""), "takes": "a font name of 1 to 64 characters", "usage": "NAME",
     "report": ("font", "value"),
     "doc": ("font", "TH Sarabun New", '`--font "Sarabun"`')},
    {"key": "size", "flag": "--size", "kind": "value", "default": 16, "layer": 1,
     "read": ("points", 1, 400), "takes": "a number of points from 1 to 400", "usage": "PT",
     "report": ("size_pt", "value"),
     "doc": ("size", "16 pt", "`--size 14` (1–400)")},
    {"key": "paper", "flag": "--paper", "kind": "value", "default": "a4", "layer": 1,
     "read": ("choice", tuple(PAPER)), "takes": "a4, letter or f14",
     "report": ("paper", "value"),
     "doc": ("paper", "A4", "`--paper letter` or `--paper f14` (8.5 × 13 in)")},
    {"key": "landscape", "flag": "--landscape", "kind": "switch", "default": False, "layer": 1,
     "report": ("landscape", "value"),
     "doc": ("orientation", "portrait", "`--landscape` (margins stay top, right, bottom, left)")},
    {"key": "margins", "flag": "--margins", "kind": "list", "default": (1.0, 1.0, 1.0, 1.5), "layer": 1,  # top, right, bottom, left — inches
     "read": ("numbers", 4), "takes": "four non-negative numbers: top,right,bottom,left", "usage": "T,R,B,L",
     "report": ("margins_in", "sides"),
     "doc": ("margins, inches", "1, 1, 1, 1.5 (top, right, bottom, left)", "`--margins 1,1,1,1`")},
    {"key": "indent", "flag": "--indent", "kind": "value", "default": 0.0, "layer": 1,  # first line of body paragraphs — inches
     "read": ("number", None, None), "takes": "a non-negative number of inches", "usage": "IN",
     "report": ("first_line_indent_in", "float"),
     "doc": ("first-line indent, inches", "none", "`--indent 0.5` (body paragraphs only)")},
    {"key": "line_spacing", "flag": "--line-spacing", "kind": "value", "default": 1.0, "layer": 1,  # code and footnotes stay single
     "read": ("number", 1, 3), "takes": "a multiple of single spacing from 1 to 3", "usage": "N",
     "report": ("line_spacing", "float"),
     "doc": ("line spacing", "1", "`--line-spacing 1.5` (1–3; code and footnotes stay single)")},
    {"key": "align", "flag": "--align", "kind": "value", "default": "left", "layer": 1,
     "read": ("choice", ("left", "thai")), "takes": "left or thai",
     "report": ("align", "value"),
     "doc": ("alignment", "left", "`--align thai` (Thai distributed; a paragraph with no Thai stays left)")},
    {"key": "toc", "flag": "--toc", "kind": "switch", "default": False, "layer": 4,
     "clashes": "toc comment",
     "report": ("toc", "value"),
     "doc": ("table of contents", "none", "`--toc` (at the top of the document)")},
    {"key": "heading_numbers", "flag": "--heading-numbers", "kind": "switch", "default": False, "layer": 4,  # 1. / 1.1 / 1.1.1, numbered by Word
     "report": ("heading_numbers", "value"),
     "doc": ("heading numbers", "none", "`--heading-numbers` (1. for `#`, 1.1 for `##`, 1.1.1 …)")},
    {"key": "page_numbers", "flag": "--page-numbers", "kind": "option", "default": False, "layer": 2,  # or one of PAGE_NUMBERS
     "read": ("position", PAGE_NUMBERS), "takes": "top-right, top-center or bottom-center",
     "report": ("page_numbers", "value"),
     "doc": ("page numbers", "none", "`--page-numbers` (top right), `--page-numbers top-center` or `--page-numbers bottom-center`")},
    {"key": "page_number_on_first", "flag": "--no-page-number-first", "kind": "off", "default": True, "layer": 2,
     "needs": "page_numbers",
     "report": ("page_number_on_first", "value"),
     "doc": ("page number on the first page of each section", "shown", "`--no-page-number-first` (with `--page-numbers`)")},
    {"key": "header", "flag": "--header", "kind": "option", "default": None, "layer": 2,  # centred at the top of every page
     "read": ("text", 200, "\t\n"), "takes": "text of 1 to 200 characters on one line", "usage": "TEXT",
     "report": ("header", "value"),
     "doc": ("header text", "none", '`--header "ลับ"` (centred, above a page number there)')},
    {"key": "footer", "flag": "--footer", "kind": "option", "default": None, "layer": 2,  # centred at the bottom of every page
     "read": ("text", 200, "\t\n"), "takes": "text of 1 to 200 characters on one line", "usage": "TEXT",
     "report": ("footer", "value"),
     "doc": ("footer text", "none", '`--footer "TEXT"` (centred, above a page number there)')},
    {"key": "thai_digits", "flag": "--thai-digits", "kind": "switch", "default": False, "layer": 2,  # numbers Word generates; never the text
     "report": ("thai_digits", "value"),
     "doc": ("page, list and footnote numbers", "1 2 3", "`--thai-digits` (๑ ๒ ๓; the text itself is never changed)")},
    {"key": "hide_spelling_errors", "flag": "--hide-spelling-errors", "kind": "switch", "default": False, "layer": 1,
     "report": ("hide_spelling_errors", "value"),
     "doc": ("spelling squiggles", "shown", "`--hide-spelling-errors`")},
    {"key": "repeat_table_header", "flag": "--no-repeat-table-header", "kind": "off", "default": True, "layer": 3,
     "needs": "tables",
     "report": ("repeat_table_header", "value"),
     "doc": ("table header row", "repeats on every page", "`--no-repeat-table-header`")},
    {"key": "table_widths", "flag": "--table-widths", "kind": "value", "default": "equal", "layer": 3,  # or by the longest text
     "read": ("choice", ("equal", "auto")), "takes": "equal or auto",
     "needs": "tables",
     "report": ("table_widths", "value"),
     "doc": ("table column widths", "equal", "`--table-widths auto` (wider for longer text)")},
    {"key": "table_size", "flag": "--table-size", "kind": "option", "default": None, "layer": 3,  # None: the body size
     "read": ("points", 1, 400), "takes": "a number of points from 1 to 400", "usage": "PT",
     "report": ("table_size_pt", "value"),
     "doc": ("table text size", "as the body", "`--table-size 14` (1–400)")},
    {"key": "chapter_label", "flag": "--chapter-label", "kind": "value", "default": "บทที่", "layer": 5,
     "read": ("text", 40, "\t\n%"), "takes": "text of 1 to 40 characters on one line, without %", "usage": "TEXT",
     "needs": "chapters or appendices",
     "report": ("chapter_label", "value"),
     "doc": ("chapter label", "บทที่", '`--chapter-label "บท"`')},
    {"key": "table_label", "flag": "--table-label", "kind": "value", "default": "ตารางที่", "layer": 5,
     "read": ("text", 40, "\t\n%"), "takes": "text of 1 to 40 characters on one line, without %", "usage": "TEXT",
     "needs": "table captions",
     "report": ("table_label", "value"),
     "doc": ("table caption label", "ตารางที่", '`--table-label "ตาราง"`')},
    {"key": "figure_label", "flag": "--figure-label", "kind": "value", "default": "รูปที่", "layer": 5,
     "read": ("text", 40, "\t\n%"), "takes": "text of 1 to 40 characters on one line, without %", "usage": "TEXT",
     "needs": "figure captions",
     "report": ("figure_label", "value"),
     "doc": ("figure caption label", "รูปที่", '`--figure-label "ภาพที่"`')},
    {"key": "front_page_numbers", "flag": "--front-page-numbers", "kind": "value", "default": "thai-letters", "layer": 5,
     "read": ("choice", tuple(FRONT_NUMBERS)), "takes": ", ".join(FRONT_NUMBERS),
     "needs": "front",
     "report": ("front_page_numbers", "value"),
     "doc": ("page numbers before the chapters", "ก ข ค", "`--front-page-numbers lower-roman` (or `upper-roman`, `decimal`)")},
    {"key": "appendix_label", "flag": "--appendix-label", "kind": "value", "default": "ภาคผนวก", "layer": 5,
     "read": ("text", 40, "\t\n%"), "takes": "text of 1 to 40 characters on one line, without %", "usage": "TEXT",
     "needs": "appendices",
     "report": ("appendix_label", "value"),
     "doc": ("appendix label", "ภาคผนวก", '`--appendix-label "Appendix"`')},
    {"key": "appendix_numbers", "flag": "--appendix-numbers", "kind": "value", "default": "thai-letters", "layer": 5,
     "read": ("choice", tuple(APPENDIX_NUMBERS)), "takes": ", ".join(APPENDIX_NUMBERS),
     "needs": "appendices",
     "report": ("appendix_numbers", "value"),
     "doc": ("appendix numbers", "ก ข ค", "`--appendix-numbers upper-letters` (or `decimal`, `upper-roman`)")},
    {"key": "chapter_title_on_new_line", "flag": "--chapter-title-on-new-line", "kind": "switch", "default": False, "layer": 5,
     "needs": "numbered headings",
     "report": ("chapter_title_on_new_line", "value"),
     "doc": ("chapter title", "beside its number", "`--chapter-title-on-new-line` (บทที่ 1 on one line, the title under it)")},
)

DEFAULTS = {s["key"]: s["default"] for s in SETTINGS}
BY_FLAG = {s["flag"]: s for s in SETTINGS}
BY_KEY = {s["key"]: s for s in SETTINGS}
USAGE = "usage: thai_docx build IN.md OUT.docx " + " ".join(
    "[" + s["flag"]
    + ("" if s["kind"] in ("switch", "off")
       else " [" + "|".join(s["read"][1]) + "]" if s["read"][0] == "position"
       else " " + "|".join(s["read"][1]) if s["read"][0] == "choice"
       else " " + s["usage"])
    + "]"
    for s in SETTINGS
) + " [--profile NAME|PATH [--default SETTING[,SETTING]]] [--allow-dir DIR]"
NUMBER = re.compile(r"[0-9]+(?:\.[0-9]+)?")  # used with fullmatch: no "$" before a newline


class BuildError(Exception):
    def __init__(self, what: str):
        super().__init__(what)
        self.what = what


def half_up(x: float) -> int:
    return int(math.floor(x + 0.5))


def page_size(opts: dict) -> tuple[int, int]:
    """Width and height in twips; landscape turns the paper, the margins stay top, right, bottom, left."""
    pw, ph = PAPER[opts["paper"]]
    return (ph, pw) if opts["landscape"] else (pw, ph)


def _read(s: dict, value: str):
    """A value as the entry reads it, or BuildError with the entry's own words."""
    how = s["read"]
    refused = BuildError(s["flag"] + " takes " + s["takes"])
    if how[0] == "text":
        if not value or len(value) > how[1] or any(c in how[2] or md.forbidden_char(c) for c in value):
            raise refused
        return value
    if how[0] in ("choice", "position"):
        if value not in how[1]:
            raise refused
        return value
    if how[0] == "numbers":
        vals = value.split(",")
        if len(vals) != how[1] or not all(NUMBER.fullmatch(v) for v in vals):
            raise refused
        return tuple(float(v) for v in vals)
    if not NUMBER.fullmatch(value) or (how[1] is not None and not how[1] <= float(value) <= how[2]):
        raise refused
    x = float(value)
    return int(x) if how[0] == "points" and x == int(x) else x


def parse_args(argv: list[str]) -> tuple[dict, list[str], list[str]]:
    """Flags → (opts, positionals, allow_dirs). Raises BuildError with a message
    both implementations share; no abbreviations, `--flag value` or `--flag=value`."""
    opts = dict(DEFAULTS)
    positional: list[str] = []
    allow: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if not arg.startswith("--"):
            positional.append(arg)
            i += 1
            continue
        name, eq, value = arg.partition("=")
        s = BY_FLAG.get(name)
        if s is not None and s["kind"] == "option" and s["read"][0] == "position":
            # the position is optional: taken only when it names one
            if not eq and i + 1 < len(argv) and argv[i + 1] in s["read"][1]:
                eq, value = "=", argv[i + 1]
                i += 1
            opts[s["key"]] = _read(s, value) if eq else s["read"][1][0]
            i += 1
            continue
        if s is not None and s["kind"] in ("switch", "off"):
            if eq:
                raise BuildError(name + " takes no value")
            opts[s["key"]] = s["kind"] == "switch"
            i += 1
            continue
        if s is None and name != "--allow-dir":
            raise BuildError("unknown option " + name)
        if not eq:
            if i + 1 >= len(argv):
                raise BuildError(name + " needs a value")
            value = argv[i + 1]
            i += 1
        i += 1
        if s is None:
            allow.append(value)
        else:
            opts[s["key"]] = _read(s, value)
    if len(positional) != 2:
        raise BuildError(USAGE)
    for s in SETTINGS:
        needed = s.get("needs")
        if needed in DEFAULTS and opts[s["key"]] != s["default"] and opts[needed] == DEFAULTS[needed]:
            raise BuildError(s["flag"] + " needs " + BY_KEY[needed]["flag"])
    pw, ph = page_size(opts)
    top, right, bottom, left = (half_up(m * 1440) for m in opts["margins"])
    if pw - left - right < MIN_TEXT_TWIPS or ph - top - bottom < MIN_TEXT_TWIPS:
        raise BuildError("--margins leave less than one inch for text")
    if pw - left - right - half_up(opts["indent"] * 1440) < MIN_TEXT_TWIPS:
        raise BuildError("--indent leaves less than one inch for text")
    return opts, positional, allow


def settings_json(opts: dict) -> dict:
    """The settings as the build reports them, in registry order."""
    out = {}
    for s in SETTINGS:
        name, form = s["report"]
        value = opts[s["key"]]
        if form == "float":
            value = float(value)
        elif form == "sides":
            value = dict(zip(("top", "right", "bottom", "left"), (float(v) for v in value), strict=True))
        out[name] = value
    return out


def _and(flags: list[str]) -> str:
    return flags[0] if len(flags) == 1 else ", ".join(flags[:-1]) + " and " + flags[-1]


def settings_warnings(opts: dict, present: set[str]) -> list[str]:
    """A flag that changed nothing is said out loud, never dropped in silence: one warning
    for each structure the document lacks, naming every flag given that needed it; then
    one for each flag that duplicates what the document already places."""
    missing: dict[str, list[str]] = {}
    for s in SETTINGS:
        need = s.get("needs")
        if need in STRUCTURES and need not in present and opts[s["key"]] != s["default"]:
            missing.setdefault(need, []).append(s["flag"])
    out = [_and(flags) + " changed nothing: " + STRUCTURES[need][1] for need, flags in missing.items()]
    for s in SETTINGS:
        clash = s.get("clashes")
        if clash in present and opts[s["key"]] != s["default"]:
            out.append(s["flag"] + ": " + CLASHES[clash][2])
    return out


# --- the interview (ADR 0029) ----------------------------------------------------------------

# The nine questions of grill mode, in order. A choice sets settings (`set`), or takes a value
# the user types (`other`: the setting and the placeholder its flag shows), or says where the
# answers are kept (`save`). Labels are (Thai, English).
QUESTIONS: tuple[dict, ...] = (
    {"key": "font", "text": ("ฟอนต์", "Font"), "choices": (
        {"set": {"font": "TH Sarabun New"}, "label": ("TH Sarabun New", "TH Sarabun New")},
        {"set": {"font": "TH SarabunPSK"}, "label": ("TH SarabunPSK", "TH SarabunPSK")},
        {"set": {"font": "Sarabun"}, "label": ("Sarabun", "Sarabun")},
        {"other": {"font": "NAME"}, "label": ("อื่น ๆ: พิมพ์ชื่อฟอนต์", "Other: the font name")})},
    {"key": "size", "text": ("ขนาดตัวอักษร", "Font size"), "choices": (
        {"set": {"size": 16}, "label": ("16 pt", "16 pt")},
        {"set": {"size": 14}, "label": ("14 pt", "14 pt")},
        {"set": {"size": 15}, "label": ("15 pt", "15 pt")},
        {"other": {"size": "N"}, "label": ("อื่น ๆ: พิมพ์ขนาด", "Other: the size")})},
    {"key": "paper", "text": ("กระดาษและขอบ", "Paper and margins"), "choices": (
        {"set": {"paper": "a4", "margins": (1.0, 1.0, 1.0, 1.5)},
         "label": ("A4 ขอบซ้าย 1.5 นิ้ว ด้านอื่น 1 นิ้ว", "A4, left 1.5 in, others 1 in")},
        {"set": {"paper": "a4", "margins": (1.0, 1.0, 1.0, 1.0)}, "label": ("A4 ขอบ 1 นิ้วทุกด้าน", "A4, 1 in all round")},
        {"set": {"paper": "letter", "margins": (1.0, 1.0, 1.0, 1.5)},
         "label": ("Letter ขอบซ้าย 1.5 นิ้ว ด้านอื่น 1 นิ้ว", "Letter, left 1.5 in, others 1 in")},
        {"other": {"paper": "PAPER", "margins": "T,R,B,L"},
         "label": ("อื่น ๆ: กระดาษ และขอบ บน ขวา ล่าง ซ้าย เป็นนิ้ว", "Other: paper, and margins top, right, bottom, left in inches")})},
    {"key": "align", "text": ("การจัดย่อหน้า", "Paragraph alignment"), "choices": (
        {"set": {"align": "left"}, "label": ("ชิดซ้าย", "Left")},
        {"set": {"align": "thai"}, "label": ("กระจายแบบไทย", "Thai distributed")})},
    {"key": "indent", "text": ("ย่อหน้าบรรทัดแรกของเนื้อความ", "First-line indent of body paragraphs"), "choices": (
        {"set": {"indent": 0.0}, "label": ("ไม่ย่อ", "None")},
        {"set": {"indent": 0.5}, "label": ("0.5 นิ้ว", "0.5 in")},
        {"set": {"indent": 1.0}, "label": ("1 นิ้ว", "1 in")},
        {"other": {"indent": "N"}, "label": ("อื่น ๆ: พิมพ์เป็นนิ้ว", "Other: inches")})},
    {"key": "toc", "text": ("สารบัญ", "Table of contents"), "choices": (
        {"set": {"toc": False}, "label": ("ไม่ใส่", "No")},
        {"set": {"toc": True}, "label": ("ใส่", "Yes")})},
    {"key": "page-numbers", "text": ("เลขหน้า", "Page numbers"), "choices": (
        {"set": {"page_numbers": False}, "label": ("ไม่ใส่", "No")},
        {"set": {"page_numbers": "top-right"}, "label": ("ใส่", "Yes")})},
    {"key": "squiggles", "text": ("เส้นหยักตรวจคำสะกด", "Spelling squiggles"), "choices": (
        {"set": {"hide_spelling_errors": False}, "label": ("แสดง", "Show")},
        {"set": {"hide_spelling_errors": True}, "label": ("ซ่อน (ซ่อนคำที่สะกดผิดจริงด้วย)", "Hide (hides real typos too)")})},
    {"key": "save", "text": ("บันทึกการตั้งค่านี้ไว้ใช้ครั้งต่อไป", "Keep these settings for next time"), "choices": (
        {"save": None, "label": ("ไม่บันทึก", "No")},
        {"save": "home", "label": ("บันทึกเป็นของฉัน: พิมพ์ชื่อ", "Yes, as mine: the name")},
        {"save": "project", "label": ("บันทึกไว้ในโปรเจกต์นี้: พิมพ์ชื่อ", "Yes, in this project: the name")})},
)
