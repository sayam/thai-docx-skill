# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-FileCopyrightText: 2014 John MacFarlane
# SPDX-License-Identifier: MIT AND BSD-2-Clause
"""Markdown → a small block/inline tree, for the dialect ADR 0022 accepts.

The block and inline parsers are a port of commonmark.js 0.31.2, the CommonMark
reference implementation (BSD-2-Clause, Copyright (c) 2014 John MacFarlane; its
licence is reproduced in LICENSES/commonmark.js.txt beside this skill). Extended
here with GFM tables, strikethrough, extended autolinks and task list items, and
GitHub footnotes. Anything outside the
dialect raises `Unsupported` with the line it was found on (ADR 0022, 0023).

It is written to be ported line for line to JavaScript (ADR 0008), so it never
leans on what only Python means: whitespace, digits and punctuation are named
explicitly (ADR 0015), and every position is a code point.

The tree handed to the writer is plain dicts:

  block  {"t": "heading", "level": n, "inlines": [...], "line": n}
         {"t": "paragraph", "inlines": [...]}
         {"t": "code", "lines": [...], "info": str, "math": bool}
         {"t": "quote", "blocks": [...]}
         {"t": "list", "ordered": bool, "start": int, "items": [[block, ...], ...]}
         {"t": "table", "aligns": [...], "rows": [[[inline, ...], ...], ...]}
         {"t": "break"}
  inline {"t": "text", "s": str, "b","i","strike","code","u","sup","sub": bool, "link": url|None, "autolink": bool}
         {"t": "hardbreak"}   {"t": "image", "src": str, "alt": str}
         {"t": "footnote_ref", "label": str, "id": n}   {"t": "task", "checked": bool}
  ("autolink" on a text node: its link is a GFM extended autolink, not CommonMark)
"""

from __future__ import annotations

import json
import pathlib
import re
import unicodedata

from .ooxml import INVISIBLE, is_thai

ENTITIES: dict[str, str] = json.loads(
    (pathlib.Path(__file__).resolve().parent.parent.parent / "assets" / "entities.json").read_text(encoding="utf-8")
)

FLAGS = ("b", "i", "strike", "code", "u", "sup", "sub")
ALLOWED_TAGS = ("br", "sup", "sub", "u", "kbd")
CODE_INDENT = 4


# Deepest nesting of blocks, and of inline formatting within a block, that is read.
# Past it every later step recurses; a limit both implementations share turns a
# stack overflow — at a depth that differs by runtime — into the same refusal.
MAX_DEPTH = 100


class Unsupported(Exception):
    def __init__(self, line: int, what: str):
        super().__init__(f"line {line}: {what}")
        self.line = line
        self.what = what


# --- the character model (ADR 0015) -------------------------------------------

ASCII_PUNCT = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
_WS = " \t\n\x0b\x0c\r"
# ำ has a compatibility decomposition into these two, and no composition back (ADR 0034)
NIKHAHIT, SARA_AA, SARA_AM = "\u0e4d", "\u0e32", "\u0e33"


def is_space_or_tab(ch: str) -> bool:
    return ch == " " or ch == "\t"


def is_unicode_whitespace(ch: str) -> bool:
    """CommonMark: Zs, tab, line feed, form feed, carriage return. The start and
    end of the subject count as whitespace."""
    return ch == "" or ch in "\t\n\x0c\r" or unicodedata.category(ch) == "Zs"


def is_unicode_punctuation(ch: str) -> bool:
    """CommonMark 0.31: a character in the Unicode P or S general categories."""
    return ch != "" and unicodedata.category(ch)[0] in "PS"


def strip_ws(s: str) -> str:
    return s.strip(_WS)


def normalize_label(label: str) -> str:
    """Link labels match case-insensitively with inner whitespace collapsed."""
    return re.sub(r"[ \t\r\n]+", " ", strip_ws(label)).lower().upper()


def forbidden_char(ch: str) -> str | None:
    """A character this skill refuses in its input: controls, noncharacters and the
    invisible characters of ADR 0023. Returns a label, or None."""
    cp = ord(ch)
    if ch in INVISIBLE:
        return INVISIBLE[ch]
    if (cp < 0x20 and ch not in "\t\n") or 0x7F <= cp <= 0x9F:
        return "U+%04X, a control character" % cp
    if cp in (0xFFFE, 0xFFFF):
        return "U+%04X, a noncharacter" % cp
    return None


# --- shared regular expressions (ASCII classes only) --------------------------

ESCAPABLE = "[!\"#$%&'()*+,./:;<=>?@\\[\\\\\\]^_`{|}~-]"
ENTITY = "&(?:#[xX][A-Fa-f0-9]{1,6}|#[0-9]{1,7}|[A-Za-z][A-Za-z0-9]{1,31});"
TAGNAME = "[A-Za-z][A-Za-z0-9-]*"
ATTRNAME = "[A-Za-z_:][A-Za-z0-9:._-]*"
S = "[ \\t\\n\\x0b\\x0c\\r]"
ATTRVALUE = "(?:[^\"'=<>`\\x00-\\x20]+|'[^']*'|\"[^\"]*\")"
OPENTAG = "<" + TAGNAME + "(?:" + S + "+" + ATTRNAME + "(?:" + S + "*=" + S + "*" + ATTRVALUE + ")?)*" + S + "*/?>"
CLOSETAG = "</" + TAGNAME + S + "*>"
HTMLCOMMENT = "<!-->|<!--->|<!--[\\s\\S]*?-->"
PI = "<\\?[\\s\\S]*?\\?>"
DECLARATION = "<![A-Za-z]+[^>]*>"
CDATA = "<!\\[CDATA\\[[\\s\\S]*?\\]\\]>"

re_escapable = re.compile(ESCAPABLE)
re_entity_or_escaped = re.compile("\\\\" + ESCAPABLE + "|" + ENTITY)
re_entity_here = re.compile(ENTITY)
re_html_tag = re.compile("(?:(" + OPENTAG + ")|(" + CLOSETAG + ")|(" + HTMLCOMMENT + ")|" + PI + "|" + DECLARATION + "|" + CDATA + ")")
re_tag_name = re.compile("</?(" + TAGNAME + ")")
re_link_title = re.compile(
    "(?:\"(?:\\\\" + ESCAPABLE + "|\\\\[^\\\\]|[^\\\\\"\\x00])*\""
    + "|'(?:\\\\" + ESCAPABLE + "|\\\\[^\\\\]|[^\\\\'\\x00])*'"
    + "|\\((?:\\\\" + ESCAPABLE + "|\\\\[^\\\\]|[^\\\\()\\x00])*\\))"
)
re_link_destination_braces = re.compile("<(?:[^<>\\n\\\\\\x00]|\\\\[^\\n])*>")
re_link_label = re.compile("\\[(?:[^\\\\\\[\\]]|\\\\[\\s\\S]){0,1000}\\]")
re_email_autolink = re.compile(
    "<([a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)>"
)
re_autolink = re.compile("<[A-Za-z][A-Za-z0-9.+-]{1,31}:[^<>\\x00-\\x20]*>")
re_spnl = re.compile(" *(?:\\n *)?")
re_whitespace_char = re.compile("[ \\t\\n\\x0b\\x0c\\r]")
re_final_space = re.compile(" *$")
re_initial_space = re.compile(" *")
re_space_at_end_of_line = re.compile(" *(?:\\n|$)")
re_ticks = re.compile("`+")
re_ticks_here = re.compile("`+")
re_main = re.compile("[^\\n`\\[\\]\\\\!<&*_~$]+")

re_html_block_open = [
    None,
    re.compile("^<(?:script|pre|textarea|style)(?:" + S + "|>|$)", re.I),
    re.compile("^<!--"),
    re.compile("^<[?]"),
    re.compile("^<![A-Za-z]"),
    re.compile("^<!\\[CDATA\\["),
    re.compile(
        "^<[/]?(?:address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|"
        "dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[123456]|head|header|hr|html|"
        "iframe|legend|li|link|main|menu|menuitem|nav|noframes|ol|optgroup|option|p|param|search|section|summary|"
        "table|tbody|td|tfoot|th|thead|title|tr|track|ul)(?:" + S + "|[/]?[>]|$)",
        re.I,
    ),
    re.compile("^(?:" + OPENTAG + "|" + CLOSETAG + ")" + S + "*$", re.I),
]
re_html_block_close = [
    None,
    re.compile("</(?:script|pre|textarea|style)>", re.I),
    re.compile("-->"),
    re.compile("\\?>"),
    re.compile(">"),
    re.compile("\\]\\]>"),
]
re_thematic_break = re.compile("^(?:\\*[ \\t]*){3,}$|^(?:_[ \\t]*){3,}$|^(?:-[ \\t]*){3,}$")
re_maybe_special = re.compile("^[#`~*+_=<>0-9$\\[|:-]")
re_non_space = re.compile("[^ \\t\\f\\v\\r\\n]")
re_bullet_list_marker = re.compile("^[*+-]")
re_ordered_list_marker = re.compile("^([0-9]{1,9})([.)])")
re_atx_heading_marker = re.compile("^#{1,6}(?:[ \\t]+|$)")
re_code_fence = re.compile("^`{3,}(?![\\s\\S]*`)|^~{3,}")
re_closing_code_fence = re.compile("^(?:`{3,}|~{3,})(?=[ \\t]*$)")
re_math_fence = re.compile("^\\$\\$")
re_closing_math_fence = re.compile("^\\$\\$[ \\t]*$")
re_setext_heading_line = re.compile("^(?:=+|-+)[ \\t]*$")
re_footnote_def = re.compile("^\\[\\^([^\\] ]+)\\]:")
re_task = re.compile("^\\[([ xX])\\][ \\t]+")
re_table_delim_cell = re.compile("^:?-+:?$")


def _decode_entity(ref: str, line: int) -> str:
    if ref[1] == "#":
        cp = int(ref[3:-1], 16) if ref[2] in "xX" else int(ref[2:-1])
        if cp == 0 or 0xD800 <= cp <= 0xDFFF or cp > 0x10FFFF:
            return "\uFFFD"
        ch = chr(cp)
        label = "a line break" if ch == "\n" else forbidden_char(ch)
        if label is not None:
            raise Unsupported(line, "character reference " + ref + " is " + label + "; the build refuses it (ADR 0015)")
        return ch
    return ENTITIES.get(ref[1:-1], ref)


def unescape_string(s: str, line: int = 0) -> str:
    if "\\" not in s and "&" not in s:
        return s
    return re_entity_or_escaped.sub(lambda m: m.group(0)[1] if m.group(0)[0] == "\\" else _decode_entity(m.group(0), line), s)


# --- nodes ---------------------------------------------------------------------


class Node:
    __slots__ = ("type", "parent", "first_child", "last_child", "prev", "next", "open", "line", "string_content",
                 "literal", "info", "level", "list_data", "fence_char", "fence_length", "fence_offset", "is_fenced",
                 "html_type", "destination", "title", "label", "aligns", "rows", "task", "math", "task_ok", "extended", "table_failed",
                 "lines")

    def __init__(self, type_: str, line: int = 0):
        self.type = type_
        self.parent = self.first_child = self.last_child = self.prev = self.next = None
        self.open = True
        self.line = line
        self.string_content = ""
        self.literal = None
        self.info = None
        self.level = 0
        self.list_data = None
        self.fence_char = None
        self.fence_length = 0
        self.fence_offset = 0
        self.is_fenced = False
        self.html_type = 0
        self.destination = None
        self.title = None
        self.label = None
        self.aligns = None
        self.rows = None
        self.task = None
        self.math = False
        self.task_ok = False
        self.extended = False  # a GFM extended autolink, not CommonMark
        self.table_failed = False  # a delimiter row under this paragraph did not fit its header
        self.lines = None  # paragraph: [(line number, text, indented)]

    def append_child(self, child: "Node") -> None:
        child.unlink()
        child.parent = self
        if self.last_child is not None:
            self.last_child.next = child
            child.prev = self.last_child
            self.last_child = child
        else:
            self.first_child = self.last_child = child

    def insert_after(self, sibling: "Node") -> None:
        sibling.unlink()
        sibling.next = self.next
        if sibling.next is not None:
            sibling.next.prev = sibling
        sibling.prev = self
        self.next = sibling
        sibling.parent = self.parent
        if sibling.next is None:
            sibling.parent.last_child = sibling

    def unlink(self) -> None:
        if self.prev is not None:
            self.prev.next = self.next
        elif self.parent is not None:
            self.parent.first_child = self.next
        if self.next is not None:
            self.next.prev = self.prev
        elif self.parent is not None:
            self.parent.last_child = self.prev
        self.parent = self.next = self.prev = None

    def children(self):
        c = self.first_child
        while c is not None:
            nxt = c.next
            yield c
            c = nxt


def _text(s: str) -> Node:
    n = Node("text")
    n.literal = s
    return n


# --- blocks --------------------------------------------------------------------


def _peek(s: str, pos: int) -> str:
    return s[pos] if pos < len(s) else ""


class BlockParser:
    def __init__(self):
        self.doc = Node("document", 1)
        self.tip = self.doc
        self.oldtip = self.doc
        self.line = ""
        self.line_number = 0
        self.offset = 0
        self.column = 0
        self.next_nonspace = 0
        self.next_nonspace_column = 0
        self.indent = 0
        self.indented = False
        self.blank = False
        self.partially_consumed_tab = False
        self.all_closed = True
        self.last_matched_container = self.doc
        self.refmap: dict[str, tuple[str, str]] = {}
        self.ref_lines: dict[str, tuple[int, str]] = {}  # label → its line and the label as written
        self.refs_used: set[str] = set()      # labels some link or image actually referred to
        self.footnote_defs: dict[str, Node] = {}
        self.last_line_length = 0
        self.warnings: list[str] = []

    # -- line state --

    def find_next_nonspace(self) -> None:
        line = self.line
        i = self.offset
        cols = self.column
        while i < len(line):
            c = line[i]
            if c == " ":
                i += 1
                cols += 1
            elif c == "\t":
                i += 1
                cols += 4 - (cols % 4)
            else:
                break
        self.blank = i >= len(line) or line[i] in "\n\r"
        self.next_nonspace = i
        self.next_nonspace_column = cols
        self.indent = self.next_nonspace_column - self.column
        self.indented = self.indent >= CODE_INDENT

    def advance_next_nonspace(self) -> None:
        self.offset = self.next_nonspace
        self.column = self.next_nonspace_column
        self.partially_consumed_tab = False

    def advance_offset(self, count: int, columns: bool) -> None:
        line = self.line
        while count > 0 and self.offset < len(line):
            c = line[self.offset]
            if c == "\t":
                chars_to_tab = 4 - (self.column % 4)
                if columns:
                    self.partially_consumed_tab = chars_to_tab > count
                    chars_to_advance = min(chars_to_tab, count)
                    self.column += chars_to_advance
                    if not self.partially_consumed_tab:
                        self.offset += 1
                    count -= chars_to_advance
                else:
                    self.partially_consumed_tab = False
                    self.column += chars_to_tab
                    self.offset += 1
                    count -= 1
            else:
                self.partially_consumed_tab = False
                self.offset += 1
                self.column += 1
                count -= 1

    # -- tree --

    def add_line(self) -> None:
        if self.partially_consumed_tab:
            self.offset += 1
            chars_to_tab = 4 - (self.column % 4)
            self.tip.string_content += " " * chars_to_tab
        text = self.line[self.offset:]
        if self.tip.type == "table":
            if not re_non_space.search(text):
                return  # the delimiter row itself, consumed by the table start
            cells = _table_cells(text)
            width = len(self.tip.aligns)
            if len(cells) > width:
                raise Unsupported(self.line_number, f"table row has {len(cells)} cells; the header has {width} — nothing may be dropped")
            self.tip.rows.append((self.line_number, cells + [""] * (width - len(cells))))
            return
        if self.tip.type == "paragraph":
            self.tip.lines.append((self.line_number, text, self.indented))
        self.tip.string_content += text + "\n"

    def add_child(self, tag: str) -> Node:
        while not _can_contain(self.tip.type, tag):
            self.finalize(self.tip, self.line_number - 1)
        depth, above = 1, self.tip
        while above.parent is not None:
            depth, above = depth + 1, above.parent
        if depth > MAX_DEPTH:
            raise Unsupported(self.line_number, f"blocks nested more than {MAX_DEPTH} deep are not supported")
        child = Node(tag, self.line_number)
        if tag == "paragraph":
            child.lines = []
        self.tip.append_child(child)
        self.tip = child
        return child

    def close_unmatched_blocks(self) -> None:
        if not self.all_closed:
            while self.oldtip is not self.last_matched_container:
                parent = self.oldtip.parent
                self.finalize(self.oldtip, self.line_number - 1)
                self.oldtip = parent
            self.all_closed = True

    def finalize(self, block: Node, line_number: int) -> None:
        above = block.parent
        block.open = False
        _FINALIZE[block.type](self, block)
        self.tip = above

    # -- the main loop (spec appendix, "phase 1") --

    def incorporate_line(self, ln: str) -> None:
        container = self.doc
        self.oldtip = self.tip
        self.offset = 0
        self.column = 0
        self.blank = False
        self.partially_consumed_tab = False
        self.line_number += 1
        self.line = ln

        while True:
            last_child = container.last_child
            if last_child is None or not last_child.open:
                break
            container = last_child
            self.find_next_nonspace()
            res = _CONTINUE[container.type](self, container)
            if res == 0:
                continue
            if res == 1:
                container = container.parent
                break
            self.last_line_length = len(ln)
            return

        self.all_closed = container is self.oldtip
        self.last_matched_container = container

        matched_leaf = container.type not in ("paragraph", "table") and _ACCEPTS_LINES[container.type]
        while not matched_leaf:
            self.find_next_nonspace()
            if not self.indented and not re_maybe_special.match(ln[self.next_nonspace:]):
                self.advance_next_nonspace()
                break
            for start in _BLOCK_STARTS:
                res = start(self, container)
                if res == 1:
                    container = self.tip
                    break
                if res == 2:
                    container = self.tip
                    matched_leaf = True
                    break
            else:
                self.advance_next_nonspace()
                break

        if not self.all_closed and not self.blank and self.tip.type == "paragraph":
            self.add_line()
        else:
            self.close_unmatched_blocks()
            t = container.type
            if _ACCEPTS_LINES[t]:
                self.add_line()
                if t == "html_block" and 1 <= container.html_type <= 5 and re_html_block_close[container.html_type].search(ln[self.offset:]):
                    self.last_line_length = len(ln)
                    self.finalize(container, self.line_number)
            elif self.offset < len(ln) and not self.blank:
                para = self.add_child("paragraph")
                self.advance_next_nonspace()
                item = para.parent
                if item.type == "item" and item.task_ok and item.line == self.line_number and para.prev is None:
                    # a GFM task marker, taken off while blocks are parsed — as
                    # GitHub does — so what follows it can still head a table
                    m = re_task.match(ln[self.offset:])
                    if m:
                        para.task = m.group(1) != " "
                        self.advance_offset(len(m.group(0)), False)
                self.add_line()
        self.last_line_length = len(ln)

    def parse(self, text: str) -> Node:
        lines = text.split("\n")
        if text.endswith("\n"):
            lines.pop()
        for ln in lines:
            self.incorporate_line(ln)
        while self.tip is not None:
            self.finalize(self.tip, len(lines))
        return self.doc


def _can_contain(parent: str, child: str) -> bool:
    if parent in ("document", "block_quote", "footnote_def"):
        return child not in ("item",) and not (parent == "footnote_def" and child == "footnote_def")
    if parent == "item":
        return child != "item"
    if parent == "list":
        return child == "item"
    return False


_ACCEPTS_LINES = {
    "document": False, "list": False, "item": False, "block_quote": False, "footnote_def": False,
    "heading": False, "thematic_break": False, "code_block": True, "html_block": True,
    "paragraph": True, "table": True,
}


def _continue_document(p, c):
    return 0


def _continue_list(p, c):
    return 0


def _continue_block_quote(p, c):
    ln = p.line
    if not p.indented and _peek(ln, p.next_nonspace) == ">":
        p.advance_next_nonspace()
        p.advance_offset(1, False)
        if is_space_or_tab(_peek(ln, p.offset)):
            p.advance_offset(1, True)
        return 0
    return 1


def _continue_item(p, c):
    if p.blank:
        if c.first_child is None:
            return 1
        p.advance_next_nonspace()
    elif p.indent >= c.list_data["marker_offset"] + c.list_data["padding"]:
        p.advance_offset(c.list_data["marker_offset"] + c.list_data["padding"], True)
    else:
        return 1
    return 0


def _continue_footnote_def(p, c):
    if p.blank:
        p.advance_next_nonspace()
        return 0
    if p.indent >= CODE_INDENT:
        p.advance_offset(CODE_INDENT, True)
        return 0
    return 1


def _continue_heading(p, c):
    return 1


def _continue_thematic_break(p, c):
    return 1


def _continue_code_block(p, c):
    ln = p.line
    indent = p.indent
    if c.is_fenced:
        closing = None
        if indent <= 3:
            rest = ln[p.next_nonspace:]
            if c.math:
                closing = re_closing_math_fence.match(rest)
                length_ok = closing is not None
            else:
                closing = re_closing_code_fence.match(rest) if _peek(ln, p.next_nonspace) == c.fence_char else None
                length_ok = closing is not None and len(closing.group(0)) >= c.fence_length
            if closing is not None and length_ok:
                p.last_line_length = p.offset + indent + len(closing.group(0))
                p.finalize(c, p.line_number)
                return 2
        i = c.fence_offset
        while i > 0 and is_space_or_tab(_peek(ln, p.offset)):
            p.advance_offset(1, True)
            i -= 1
    else:
        if indent >= CODE_INDENT:
            p.advance_offset(CODE_INDENT, True)
        elif p.blank:
            p.advance_next_nonspace()
        else:
            return 1
    return 0


def _continue_html_block(p, c):
    return 1 if p.blank and c.html_type in (6, 7) else 0


def _continue_paragraph(p, c):
    return 1 if p.blank else 0


def _continue_table(p, c):
    if p.blank:
        return 1
    rest = p.line[p.next_nonspace:]
    return 1 if not _table_cells(rest) else 0  # a row of nothing but pipes ends the table


_CONTINUE = {
    "document": _continue_document, "list": _continue_list, "block_quote": _continue_block_quote,
    "item": _continue_item, "footnote_def": _continue_footnote_def, "heading": _continue_heading,
    "thematic_break": _continue_thematic_break, "code_block": _continue_code_block,
    "html_block": _continue_html_block, "paragraph": _continue_paragraph, "table": _continue_table,
}


def _finalize_noop(p, b):
    pass


def _finalize_document(p, doc):
    """commonmark.js removeLinkReferenceDefinitions: every paragraph, in document
    order, gives up the definitions it starts with."""
    empty = []

    def walk(node):
        for child in node.children():
            if child.type == "paragraph":
                if _take_references(p, child):
                    empty.append(child)
            elif child.type != "table":
                walk(child)

    walk(doc)
    for node in empty:
        node.unlink()


def _take_references(p, b) -> bool:
    """Strip leading link reference definitions; True when nothing else is left."""
    content = b.string_content
    has_defs = False
    while _peek(content, 0) == "[":
        pos = InlineParser(p, b.line).parse_reference(content, p.refmap)
        if not pos:
            break
        consumed = content[:pos]
        content = content[pos:]
        has_defs = True
        drop = consumed.count("\n")
        b.lines = b.lines[drop:]
    b.string_content = content
    return has_defs and not re_non_space.search(content)


def _finalize_code_block(p, b):
    if b.is_fenced:
        content = b.string_content
        nl = content.find("\n")
        first_line, rest = content[:nl], content[nl + 1:]
        if b.math:
            b.info = "math"
            b.literal = (strip_ws(first_line) + "\n" if strip_ws(first_line) else "") + rest
        else:
            b.info = unescape_string(strip_ws(first_line), b.line)
            b.literal = rest
    else:
        lines = b.string_content.split("\n")
        while re.match("^[ \\t]*$", lines[-1]):
            lines.pop()
        b.literal = "\n".join(lines) + "\n"
    b.string_content = ""


def _finalize_html_block(p, b):
    if b.html_type == 2:
        if not re_html_block_close[2].search(b.string_content):
            raise Unsupported(b.line, "HTML comment is never closed")
        rest = re.sub(HTMLCOMMENT, "", b.string_content)
        if re_non_space.search(rest):
            raise Unsupported(b.line, "an HTML comment block also holds text; put the text outside the comment")
        # the node stays in the tree while blocks are parsed — a list item holding
        # only a comment is not empty — and renders nothing
        return
    raise Unsupported(b.line, "HTML blocks are not supported; only <br>, <sup>, <sub>, <u>, <kbd> inside text, and comments")


_FINALIZE = {
    "document": _finalize_document, "list": _finalize_noop, "block_quote": _finalize_noop, "item": _finalize_noop,
    "footnote_def": _finalize_noop, "heading": _finalize_noop, "thematic_break": _finalize_noop,
    "code_block": _finalize_code_block, "html_block": _finalize_html_block, "paragraph": _finalize_noop,
    "table": _finalize_noop,
}


# -- block starts, in the order commonmark.js tries them; tables and footnotes and
#    display math are inserted where they cannot shadow a CommonMark block.


def _start_block_quote(p, container):
    if not p.indented and _peek(p.line, p.next_nonspace) == ">":
        p.advance_next_nonspace()
        p.advance_offset(1, False)
        if is_space_or_tab(_peek(p.line, p.offset)):
            p.advance_offset(1, True)
        p.close_unmatched_blocks()
        p.add_child("block_quote")
        return 1
    return 0


def _start_atx_heading(p, container):
    if not p.indented:
        m = re_atx_heading_marker.match(p.line[p.next_nonspace:])
        if m:
            p.advance_next_nonspace()
            p.advance_offset(len(m.group(0)), False)
            p.close_unmatched_blocks()
            h = p.add_child("heading")
            h.level = len(m.group(0).strip(" \t"))
            content = p.line[p.offset:]
            content = re.sub("^[ \\t]*#+[ \\t]*$", "", content)
            content = re.sub("[ \\t]+#+[ \\t]*$", "", content)
            h.string_content = content
            p.advance_offset(len(p.line) - p.offset, False)
            return 2
    return 0


def _start_fenced_code(p, container):
    if not p.indented:
        m = re_code_fence.match(p.line[p.next_nonspace:])
        if m:
            fence_length = len(m.group(0))
            p.close_unmatched_blocks()
            c = p.add_child("code_block")
            c.is_fenced = True
            c.fence_length = fence_length
            c.fence_char = m.group(0)[0]
            c.fence_offset = p.indent
            p.advance_next_nonspace()
            p.advance_offset(fence_length, False)
            return 2
    return 0


def _start_math_fence(p, container):
    if not p.indented and re_math_fence.match(p.line[p.next_nonspace:]):
        rest = p.line[p.next_nonspace + 2:]
        p.close_unmatched_blocks()
        c = p.add_child("code_block")
        c.is_fenced = True
        c.math = True
        c.fence_offset = p.indent
        p.warnings.append(f"line {p.line_number}: display math kept as literal LaTeX; typeset math is not supported in v0.1")
        p.advance_next_nonspace()
        p.advance_offset(2, False)
        stripped = rest.rstrip(" \t")
        if stripped.endswith("$$") and len(strip_ws(stripped)) > 2:
            # $$ ... $$ on one line
            c.string_content = strip_ws(stripped[:-2]) + "\n"
            p.advance_offset(len(p.line) - p.offset, False)
            p.finalize(c, p.line_number)
            return 2
        return 2
    return 0


def _start_html_block(p, container):
    if not p.indented and _peek(p.line, p.next_nonspace) == "<":
        s = p.line[p.next_nonspace:]
        for block_type in range(1, 8):
            if re_html_block_open[block_type].search(s) and (
                block_type < 7 or (container.type != "paragraph" and not (not p.all_closed and not p.blank and p.tip.type == "paragraph"))
            ):
                p.close_unmatched_blocks()
                b = p.add_child("html_block")
                b.html_type = block_type
                return 2
    return 0


def _split_row(line: str) -> list[str]:
    """GFM table row → cells, as markdown-it splits them: a pipe right after a
    backslash is escaped, and that backslash is removed."""
    result, current, last, escaped = [], "", 0, False
    for pos, ch in enumerate(line):
        if ch == "|":
            if not escaped:
                result.append(current + line[last:pos])
                current = ""
                last = pos + 1
            else:
                current += line[last:pos - 1]
                last = pos
        escaped = ch == "\\"
    result.append(current + line[last:])
    return result


def _table_delimiter(row: str) -> list | None:
    """A GFM delimiter row. CommonMark's block starts are tried first (see
    _BLOCK_STARTS), so a row that is also a setext underline never gets here."""
    if not row or row[0] not in "|-:":
        return None
    if len(row) < 2 or row[1] not in "|-: \t":
        return None
    if row[0] == "-" and is_space_or_tab(row[1]):
        return None
    if any(ch not in "|-: \t" for ch in row):
        return None
    cols = row.split("|")
    aligns = []
    for i, col in enumerate(cols):
        t = strip_ws(col)
        if not t:
            if i == 0 or i == len(cols) - 1:
                continue
            return None
        if not re_table_delim_cell.match(t):
            return None
        if t[-1] == ":":
            aligns.append("center" if t[0] == ":" else "right")
        else:
            aligns.append("left" if t[0] == ":" else None)
    return aligns


def _table_cells(row: str) -> list[str]:
    cells = _split_row(strip_ws(row))
    if cells and cells[0] == "":
        cells.pop(0)
    if cells and cells[-1] == "":
        cells.pop()
    return cells


def _start_table(p, container):
    if p.indented or container.type != "paragraph" or not container.lines or container.table_failed:
        return 0
    aligns = _table_delimiter(p.line[p.next_nonspace:])
    if aligns is None:
        return 0
    header_no, header, header_indented = container.lines[-1]
    cells = _table_cells(header)
    if header_indented or not cells or len(cells) != len(aligns):
        # as cmark-gfm: once a delimiter row fails its header, this paragraph
        # starts no table at all
        container.table_failed = True
        return 0
    p.close_unmatched_blocks()
    # the header is the paragraph's last line; what came before stays a paragraph
    para = container
    table = Node("table", header_no)
    table.aligns = aligns
    table.rows = [(header_no, cells)]
    lines_before = para.lines[:-1]
    para.insert_after(table)
    if not lines_before and para.task is not None:
        # a task item whose text heads a table keeps its checkbox before it
        para.lines = []
        para.string_content = ""
        p.finalize(para, p.line_number - 1)
    elif lines_before:
        para.lines = lines_before
        para.string_content = "".join(t + "\n" for _, t, _ in lines_before)
        p.finalize(para, p.line_number - 1)
    else:
        para.unlink()
    p.tip = table
    p.advance_offset(len(p.line) - p.offset, False)
    return 2


def _start_setext_heading(p, container):
    if not p.indented and container.type == "paragraph":
        m = re_setext_heading_line.match(p.line[p.next_nonspace:])
        if m:
            p.close_unmatched_blocks()
            content = container.string_content
            while _peek(content, 0) == "[":
                pos = InlineParser(p, container.line).parse_reference(content, p.refmap)
                if not pos:
                    break
                container.lines = container.lines[content[:pos].count("\n"):]
                content = content[pos:]
            if re_non_space.search(content):
                heading = Node("heading", container.line)
                heading.level = 1 if m.group(0)[0] == "=" else 2
                heading.string_content = content
                heading.lines = container.lines
                container.insert_after(heading)
                if container.task is not None:
                    # a task item whose text becomes a heading keeps its checkbox before it
                    container.string_content = ""
                    container.lines = []
                    container.open = False
                else:
                    container.unlink()
                p.tip = heading
                p.advance_offset(len(p.line) - p.offset, False)
                return 2
            container.string_content = content
            return 0
    return 0


def _start_thematic_break(p, container):
    if not p.indented and re_thematic_break.match(p.line[p.next_nonspace:]):
        p.close_unmatched_blocks()
        p.add_child("thematic_break")
        p.advance_offset(len(p.line) - p.offset, False)
        return 2
    return 0


def _parse_list_marker(p, container):
    rest = p.line[p.next_nonspace:]
    data = {"type": None, "tight": True, "bullet_char": None, "start": None, "delimiter": None, "padding": None,
            "marker_offset": p.indent}
    if p.indent >= 4:
        return None
    m = re_bullet_list_marker.match(rest)
    if m:
        data["type"] = "bullet"
        data["bullet_char"] = m.group(0)[0]
    else:
        m = re_ordered_list_marker.match(rest)
        if m and (container.type != "paragraph" or m.group(1) == "1"):
            data["type"] = "ordered"
            data["start"] = int(m.group(1))
            data["delimiter"] = m.group(2)
        else:
            return None
    nextc = _peek(p.line, p.next_nonspace + len(m.group(0)))
    if not (nextc == "" or nextc == "\t" or nextc == " "):
        return None
    if container.type == "paragraph" and not re_non_space.search(p.line[p.next_nonspace + len(m.group(0)):]):
        return None
    p.advance_next_nonspace()
    p.advance_offset(len(m.group(0)), True)
    spaces_start_col = p.column
    spaces_start_offset = p.offset
    while True:
        p.advance_offset(1, True)
        nextc = _peek(p.line, p.offset)
        if not (p.column - spaces_start_col < 5 and is_space_or_tab(nextc)):
            break
    blank_item = _peek(p.line, p.offset) == ""
    spaces_after_marker = p.column - spaces_start_col
    if spaces_after_marker >= 5 or spaces_after_marker < 1 or blank_item:
        data["padding"] = len(m.group(0)) + 1
        p.column = spaces_start_col
        p.offset = spaces_start_offset
        if is_space_or_tab(_peek(p.line, p.offset)):
            p.advance_offset(1, True)
    else:
        data["padding"] = len(m.group(0)) + spaces_after_marker
    return data


def _lists_match(a, b):
    return a["type"] == b["type"] and a["delimiter"] == b["delimiter"] and a["bullet_char"] == b["bullet_char"]


def _start_list_item(p, container):
    if not p.indented or container.type == "list":
        # GitHub reads a task marker only on an item whose own marker is the first
        # thing on its line — not after "> " or another list marker
        first_on_line = not p.line[:p.next_nonspace].strip(" \t")
        data = _parse_list_marker(p, container)
        if data is not None:
            p.close_unmatched_blocks()
            if p.tip.type != "list" or not _lists_match(container.list_data, data):
                lst = p.add_child("list")
                lst.list_data = data
            item = p.add_child("item")
            item.list_data = data
            item.task_ok = first_on_line
            return 1
    return 0


def _start_indented_code(p, container):
    if p.indented and p.tip.type != "paragraph" and not p.blank:
        p.advance_offset(CODE_INDENT, True)
        p.close_unmatched_blocks()
        p.add_child("code_block")
        return 2
    return 0


def _start_footnote_def(p, container):
    if p.indented:
        return 0
    m = re_footnote_def.match(p.line[p.next_nonspace:])
    if not m:
        return 0
    p.advance_next_nonspace()
    p.advance_offset(len(m.group(0)), False)
    while is_space_or_tab(_peek(p.line, p.offset)):
        p.advance_offset(1, False)
    p.close_unmatched_blocks()
    fn = p.add_child("footnote_def")
    fn.label = m.group(1)
    if fn.label in p.footnote_defs:
        raise Unsupported(p.line_number, f"footnote [^{fn.label}] is defined twice")
    p.footnote_defs[fn.label] = fn
    return 1


_BLOCK_STARTS = [
    _start_block_quote,
    _start_atx_heading,
    _start_fenced_code,
    _start_math_fence,
    _start_html_block,
    _start_footnote_def,
    _start_setext_heading,
    _start_thematic_break,
    _start_list_item,
    _start_indented_code,
    # GFM table: tried after CommonMark's own starts, as cmark-gfm tries its
    # extensions — so `---` under a line is a setext heading and `- x` a list item,
    # while `-:` or `|---|` is a delimiter row
    _start_table,
]


# --- inlines -------------------------------------------------------------------


_UNDEFINED = object()  # commonmark.js's `undefined`, which compares unequal to null


class Delimiter:
    __slots__ = ("cc", "numdelims", "origdelims", "node", "previous", "next", "can_open", "can_close")


class Bracket:
    __slots__ = ("node", "previous", "previous_delimiter", "index", "image", "active", "bracket_after")


class InlineParser:
    def __init__(self, bp: BlockParser, line: int):
        self.bp = bp
        self.subject = ""
        self.pos = 0
        self.delimiters: Delimiter | None = None
        self.brackets: Bracket | None = None
        self.refmap = bp.refmap
        self.base_line = line
        self.line_starts: list[int] = [0]

    def line_at(self, pos: int) -> int:
        n = 0
        for i, start in enumerate(self.line_starts):
            if start <= pos:
                n = i
        return self.base_line + n

    def match(self, regex) -> str | None:
        """Match `regex` exactly at the current position and move past it."""
        m = regex.match(self.subject, self.pos)
        if m is None:
            return None
        self.pos = m.end()
        return m.group(0)

    def search(self, regex) -> str | None:
        """Find `regex` at or after the current position and move past it."""
        m = regex.search(self.subject, self.pos)
        if m is None:
            return None
        self.pos = m.end()
        return m.group(0)

    def peek(self) -> str:
        return self.subject[self.pos] if self.pos < len(self.subject) else ""

    def spnl(self) -> bool:
        self.match(re_spnl)
        return True

    # -- entry --

    def parse(self, block: Node) -> None:
        self.subject = strip_ws(block.string_content)
        self.line_starts = [0] + [i + 1 for i, ch in enumerate(self.subject) if ch == "\n"]
        self.pos = 0
        self.delimiters = None
        self.brackets = None
        while self.parse_inline(block):
            pass
        block.string_content = ""
        self.process_emphasis(None)

    def parse_inline(self, block: Node) -> bool:
        c = self.peek()
        if c == "":
            return False
        if c == "\n":
            res = self.parse_newline(block)
        elif c == "\\":
            res = self.parse_backslash(block)
        elif c == "`":
            res = self.parse_backticks(block)
        elif c in "*_~":
            res = self.handle_delim(c, block)
        elif c == "[":
            res = self.parse_open_bracket(block)
        elif c == "!":
            res = self.parse_bang(block)
        elif c == "]":
            res = self.parse_close_bracket(block)
        elif c == "<":
            res = self.parse_autolink(block) or self.parse_html_tag(block)
        elif c == "&":
            res = self.parse_entity(block)
        elif c == "$":
            res = self.parse_math(block)
        else:
            res = self.parse_string(block)
        if not res:
            self.pos += 1
            block.append_child(_text(c))
        return True

    def parse_newline(self, block: Node) -> bool:
        self.pos += 1
        lastc = block.last_child
        if lastc is not None and lastc.type == "text" and lastc.literal.endswith(" "):
            hardbreak = len(lastc.literal) >= 2 and lastc.literal[-2] == " "
            lastc.literal = re_final_space.sub("", lastc.literal, count=1)
            block.append_child(Node("linebreak" if hardbreak else "softbreak"))
        else:
            block.append_child(Node("softbreak"))
        self.match(re_initial_space)
        return True

    def parse_backslash(self, block: Node) -> bool:
        subj = self.subject
        self.pos += 1
        if self.peek() == "\n":
            self.pos += 1
            block.append_child(Node("linebreak"))
        elif self.pos < len(subj) and re_escapable.fullmatch(subj[self.pos]):
            block.append_child(_text(subj[self.pos]))
            self.pos += 1
        else:
            block.append_child(_text("\\"))
        return True

    def parse_backticks(self, block: Node) -> bool:
        ticks = self.match(re_ticks_here)
        if ticks is None:
            return False
        after_open_ticks = self.pos
        while True:
            matched = self.search(re_ticks)
            if matched is None:
                break
            if matched == ticks:
                node = Node("code")
                contents = self.subject[after_open_ticks:self.pos - len(ticks)].replace("\n", " ")
                if contents and re.search("[^ ]", contents) and contents[0] == " " and contents[-1] == " ":
                    node.literal = contents[1:-1]
                else:
                    node.literal = contents
                block.append_child(node)
                return True
        self.pos = after_open_ticks
        block.append_child(_text(ticks))
        return True

    def scan_delims(self, cc: str):
        numdelims = 0
        startpos = self.pos
        while self.peek() == cc:
            numdelims += 1
            self.pos += 1
        if numdelims == 0:
            return None
        char_before = "\n" if startpos == 0 else self.subject[startpos - 1]
        char_after = self.peek() or "\n"
        after_ws = is_unicode_whitespace(char_after)
        after_punct = is_unicode_punctuation(char_after)
        before_ws = is_unicode_whitespace(char_before)
        before_punct = is_unicode_punctuation(char_before)
        left = not after_ws and (not after_punct or before_ws or before_punct)
        right = not before_ws and (not before_punct or after_ws or after_punct)
        if cc == "_":
            can_open = left and (not right or before_punct)
            can_close = right and (not left or after_punct)
        else:
            can_open, can_close = left, right
        if cc == "~" and numdelims > 2:
            can_open = can_close = False
        self.pos = startpos
        return numdelims, can_open, can_close

    def handle_delim(self, cc: str, block: Node) -> bool:
        res = self.scan_delims(cc)
        if res is None:
            return False
        numdelims, can_open, can_close = res
        startpos = self.pos
        self.pos += numdelims
        node = _text(self.subject[startpos:self.pos])
        block.append_child(node)
        if can_open or can_close:
            d = Delimiter()
            d.cc, d.numdelims, d.origdelims, d.node = cc, numdelims, numdelims, node
            d.previous, d.next, d.can_open, d.can_close = self.delimiters, None, can_open, can_close
            if d.previous is not None:
                d.previous.next = d
            self.delimiters = d
        return True

    def remove_delimiter(self, delim: Delimiter) -> None:
        if delim.previous is not None:
            delim.previous.next = delim.next
        if delim.next is None:
            self.delimiters = delim.previous
        else:
            delim.next.previous = delim.previous

    @staticmethod
    def remove_delimiters_between(bottom: Delimiter, top: Delimiter) -> None:
        if bottom.next is not top:
            bottom.next = top
            top.previous = bottom

    def process_emphasis(self, stack_bottom: Delimiter | None) -> None:
        openers_bottom = [stack_bottom] * 15
        closer = self.delimiters
        while closer is not None and closer.previous is not stack_bottom:
            closer = closer.previous
        while closer is not None:
            closercc = closer.cc
            if not closer.can_close:
                closer = closer.next
                continue
            opener = closer.previous
            opener_found = False
            if closercc == "_":
                idx = 2 + (3 if closer.can_open else 0) + closer.origdelims % 3
            elif closercc == "*":
                idx = 8 + (3 if closer.can_open else 0) + closer.origdelims % 3
            else:
                idx = 14
            while opener is not None and opener is not stack_bottom and opener is not openers_bottom[idx]:
                if closercc == "~":
                    if opener.cc == "~" and opener.can_open and opener.numdelims == closer.numdelims:
                        opener_found = True
                        break
                else:
                    odd_match = ((closer.can_open or opener.can_close) and closer.origdelims % 3 != 0
                                 and (opener.origdelims + closer.origdelims) % 3 == 0)
                    if opener.cc == closer.cc and opener.can_open and not odd_match:
                        opener_found = True
                        break
                opener = opener.previous
            old_closer = closer
            if not opener_found:
                closer = closer.next
            else:
                if closercc == "~":
                    use_delims = closer.numdelims
                else:
                    use_delims = 2 if closer.numdelims >= 2 and opener.numdelims >= 2 else 1
                opener_inl, closer_inl = opener.node, closer.node
                opener.numdelims -= use_delims
                closer.numdelims -= use_delims
                opener_inl.literal = opener_inl.literal[:len(opener_inl.literal) - use_delims]
                closer_inl.literal = closer_inl.literal[:len(closer_inl.literal) - use_delims]
                emph = Node("strikethrough" if closercc == "~" else ("emph" if use_delims == 1 else "strong"))
                tmp = opener_inl.next
                while tmp is not None and tmp is not closer_inl:
                    nxt = tmp.next
                    tmp.unlink()
                    emph.append_child(tmp)
                    tmp = nxt
                opener_inl.insert_after(emph)
                self.remove_delimiters_between(opener, closer)
                if opener.numdelims == 0:
                    opener_inl.unlink()
                    self.remove_delimiter(opener)
                if closer.numdelims == 0:
                    closer_inl.unlink()
                    tempstack = closer.next
                    self.remove_delimiter(closer)
                    closer = tempstack
            if not opener_found:
                openers_bottom[idx] = old_closer.previous
                if not old_closer.can_open:
                    self.remove_delimiter(old_closer)
        while self.delimiters is not None and self.delimiters is not stack_bottom:
            self.remove_delimiter(self.delimiters)

    def add_bracket(self, node: Node, index: int, image: bool) -> None:
        if self.brackets is not None:
            self.brackets.bracket_after = True
        b = Bracket()
        b.node, b.previous, b.previous_delimiter, b.index, b.image, b.active, b.bracket_after = (
            node, self.brackets, self.delimiters, index, image, True, False)
        self.brackets = b

    def remove_bracket(self) -> None:
        self.brackets = self.brackets.previous

    def parse_open_bracket(self, block: Node) -> bool:
        startpos = self.pos
        self.pos += 1
        node = _text("[")
        block.append_child(node)
        self.add_bracket(node, startpos, False)
        return True

    def parse_bang(self, block: Node) -> bool:
        startpos = self.pos
        self.pos += 1
        if self.peek() == "[":
            self.pos += 1
            node = _text("![")
            block.append_child(node)
            self.add_bracket(node, startpos + 1, True)
        else:
            block.append_child(_text("!"))
        return True

    def parse_link_label(self) -> int:
        m = self.match(re_link_label)
        if m is None or len(m) > 1001:
            return 0
        return len(m)

    def parse_link_destination(self) -> str | None:
        res = self.match(re_link_destination_braces)
        if res is None:
            if self.peek() == "<":
                return None
            savepos = self.pos
            openparens = 0
            c = ""
            while True:
                c = self.peek()
                if c == "":
                    break
                if c == "\\" and re_escapable.fullmatch(_peek(self.subject, self.pos + 1)):
                    self.pos += 1
                    if self.peek() != "":
                        self.pos += 1
                elif c == "(":
                    self.pos += 1
                    openparens += 1
                elif c == ")":
                    if openparens < 1:
                        break
                    self.pos += 1
                    openparens -= 1
                elif re_whitespace_char.fullmatch(c):
                    break
                else:
                    self.pos += 1
            if self.pos == savepos and c != ")":
                return None
            if openparens != 0:
                return None
            res = self.subject[savepos:self.pos]
            return unescape_string(res, self.line_at(savepos))
        return unescape_string(res[1:-1], self.line_at(self.pos))

    def parse_link_title(self) -> str | None:
        title = self.match(re_link_title)
        if title is None:
            return None
        return unescape_string(title[1:-1], self.line_at(self.pos))

    def parse_close_bracket(self, block: Node) -> bool:
        matched = False
        dest = title = None
        self.pos += 1
        startpos = self.pos
        opener = self.brackets
        if opener is None:
            block.append_child(_text("]"))
            return True
        if not opener.active:
            block.append_child(_text("]"))
            self.remove_bracket()
            return True
        is_image = opener.image
        if is_image and self.subject[opener.index + 1:opener.index + 2] == "^":
            # cmark-gfm with footnotes: "![^x]" is "!" and then "[^x]" — a link when
            # a destination follows, a footnote when the label is defined
            is_image = False
            opener.node.literal = "!"
            bang = opener.node
            opener.node = _text("[")
            bang.insert_after(opener.node)
            opener.image = False
        savepos = self.pos
        if self.peek() == "(":
            self.pos += 1
            self.spnl()
            dest = self.parse_link_destination()
            if dest is not None:
                self.spnl()
                if re_whitespace_char.fullmatch(_peek(self.subject, self.pos - 1)):
                    title = self.parse_link_title()
                self.spnl()
                if self.peek() == ")":
                    self.pos += 1
                    matched = True
            if not matched:
                self.pos = savepos
        if not matched:
            beforelabel = self.pos
            n = self.parse_link_label()
            reflabel = None
            if n > 2:
                reflabel = self.subject[beforelabel:beforelabel + n]
            elif not opener.bracket_after:
                reflabel = self.subject[opener.index:startpos]
            if n == 0:
                self.pos = savepos
            if reflabel:
                label = normalize_label(reflabel[1:-1])
                link = self.refmap.get(label)
                if link is not None:
                    self.bp.refs_used.add(label)
                    dest, title = link
                    matched = True
        if matched:
            node = Node("image" if is_image else "link")
            node.destination = dest
            node.title = title or ""
            tmp = opener.node.next
            while tmp is not None:
                nxt = tmp.next
                tmp.unlink()
                node.append_child(tmp)
                tmp = nxt
            block.append_child(node)
            self.process_emphasis(opener.previous_delimiter)
            self.remove_bracket()
            opener.node.unlink()
            if not is_image:
                o = self.brackets
                while o is not None:
                    if not o.image:
                        o.active = False
                    o = o.previous
            return True
        # GitHub footnote reference, tried as cmark-gfm tries it: only once no link
        # matched, for "[^label]" with a defined label (after "!", the "!" stays text)
        inner = self.subject[opener.index + 1:startpos - 1]
        if inner.startswith("^") and len(inner) > 1 and not re.search("[ \\t\\n]", inner) and inner[1:] in self.bp.footnote_defs:
            node = Node("footnote_ref")
            node.label = inner[1:]
            tmp = opener.node.next
            while tmp is not None:
                nxt = tmp.next
                tmp.unlink()
                tmp = nxt
            block.append_child(node)
            self.process_emphasis(opener.previous_delimiter)
            self.remove_bracket()
            if is_image:
                opener.node.literal = "!"
            else:
                opener.node.unlink()
            self.pos = startpos
            return True
        self.remove_bracket()
        self.pos = startpos
        block.append_child(_text("]"))
        return True

    def parse_autolink(self, block: Node) -> bool:
        m = self.match(re_email_autolink)
        if m is not None:
            dest = m[1:-1]
            node = Node("link")
            node.destination = "mailto:" + dest
            node.title = ""
            node.append_child(_text(dest))
            block.append_child(node)
            return True
        m = self.match(re_autolink)
        if m is not None:
            dest = m[1:-1]
            node = Node("link")
            node.destination = dest
            node.title = ""
            node.append_child(_text(dest))
            block.append_child(node)
            return True
        return False

    def parse_html_tag(self, block: Node) -> bool:
        start = self.pos
        m = re_html_tag.match(self.subject, self.pos)
        if m is None:
            return False
        self.pos = m.end()
        raw = m.group(0)
        line = self.line_at(start)
        if m.group(3) is not None:
            # a comment renders nothing, but it still stands between the text before
            # it and a line break after it (CommonMark keeps those spaces)
            block.append_child(Node("html_comment"))
            return True
        if m.group(1) is not None or m.group(2) is not None:
            name = re_tag_name.match(raw).group(1).lower()
            if name == "br" and m.group(2) is not None:
                block.append_child(Node("linebreak"))  # browsers read </br> as <br>
                return True
            if name in ALLOWED_TAGS:
                if name == "br":
                    block.append_child(Node("linebreak"))
                    return True
                node = Node("html_tag")
                node.label = name
                node.literal = "close" if m.group(2) is not None else "open"
                block.append_child(node)
                return True
            raise Unsupported(line, f"HTML <{name}> is not supported; only <br>, <sup>, <sub>, <u>, <kbd> and comments are")
        raise Unsupported(line, "HTML declarations, processing instructions and CDATA are not supported")

    def parse_entity(self, block: Node) -> bool:
        m = self.match(re_entity_here)
        if m is None:
            return False
        block.append_child(_text(_decode_entity(m, self.line_at(self.pos))))
        return True

    def parse_math(self, block: Node) -> bool:
        subj, i = self.subject, self.pos
        n = len(subj)
        width = 2 if subj.startswith("$$", i) else 1
        if width == 2:
            end = subj.find("$$", i + 2)
        else:
            end = -1
            if i + 1 < n and not is_unicode_whitespace(subj[i + 1]):
                j = subj.find("$", i + 1)
                while j != -1 and (is_unicode_whitespace(subj[j - 1]) or (j + 1 < n and "0" <= subj[j + 1] <= "9")):
                    j = subj.find("$", j + 1)
                end = j
        if end == -1 or end <= i + width - 1 or end == i + width:
            return False
        node = Node("code")
        node.literal = subj[i + width:end].replace("\n", " ")
        node.math = True
        block.append_child(node)
        self.bp.warnings.append(f"line {self.line_at(i)}: inline math kept as literal LaTeX; typeset math is not supported in v0.1")
        self.pos = end + width
        return True

    def parse_string(self, block: Node) -> bool:
        m = self.match(re_main)
        if m is None:
            return False
        block.append_child(_text(m))
        return True

    def parse_reference(self, s: str, refmap: dict) -> int:
        self.subject = s
        self.pos = 0
        startpos = self.pos
        match_chars = self.parse_link_label()
        if match_chars == 0:
            return 0
        rawlabel = self.subject[:match_chars]
        if self.peek() == ":":
            self.pos += 1
        else:
            self.pos = startpos
            return 0
        self.spnl()
        dest = self.parse_link_destination()
        if dest is None:
            self.pos = startpos
            return 0
        beforetitle = self.pos
        self.spnl()
        title = _UNDEFINED
        if self.pos != beforetitle:
            title = self.parse_link_title()
        if title is None:
            self.pos = beforetitle
        at_line_end = True
        if self.match(re_space_at_end_of_line) is None:
            if title is None:
                at_line_end = False
            else:
                title = None
                self.pos = beforetitle
                at_line_end = self.match(re_space_at_end_of_line) is not None
        if not at_line_end:
            self.pos = startpos
            return 0
        normlabel = normalize_label(rawlabel[1:-1])
        if normlabel == "":
            self.pos = startpos
            return 0
        if normlabel not in refmap:
            refmap[normlabel] = (dest, "" if title is None or title is _UNDEFINED else title)
            self.bp.ref_lines[normlabel] = (self.line_at(startpos), rawlabel[1:-1])
        return self.pos - startpos


# --- extended autolinks (GFM 6.9), on text nodes after inline parsing ---------
# Only `www.` and `http(s)://` forms: they change no text, only whether a run of
# it is a hyperlink.

re_www = re.compile("www\\.")
re_url_scheme = re.compile("https?://")
re_domain = re.compile("[A-Za-z0-9_-]+(?:\\.[A-Za-z0-9_-]+)*")
re_entity_tail = re.compile("&[A-Za-z0-9]+;$")


def _autolink_end(s: str, start: int) -> int:
    """End of an extended autolink that starts at `start`, or -1."""
    m = re_url_scheme.match(s, start) or re_www.match(s, start)
    if m is None:
        return -1
    dstart = m.end() if m.group(0).startswith("http") else start
    d = re_domain.match(s, dstart)
    if d is None:
        return -1
    labels = d.group(0).split(".")
    if len(labels) < 2 or "_" in labels[-1] or "_" in labels[-2]:
        return -1
    end = d.end()
    while end < len(s) and not is_unicode_whitespace(s[end]) and s[end] != "<":
        end += 1
    while end > d.end():
        last = s[end - 1]
        if last in "?!.,:*_~'\"":
            end -= 1
        elif last == ")" and s.count(")", start, end) > s.count("(", start, end):
            end -= 1
        elif last == ";" and re_entity_tail.search(s[start:end]):
            end = start + re_entity_tail.search(s[start:end]).start()
        else:
            break
    return end


re_email_local = re.compile("[A-Za-z0-9._+-]")
re_email_domain = re.compile("[A-Za-z0-9_-]+(?:\\.[A-Za-z0-9_-]+)*")


def _split_emails(s: str) -> list[tuple[str, str | None]]:
    """Bare email addresses, as cmark-gfm finds them: from each "@", back over
    the local part and forward over a domain with a dot, whose last character is
    not "-" or "_"."""
    pieces: list[tuple[str, str | None]] = []
    last = 0
    i = 0
    while i < len(s):
        if s[i] == "@":
            start = i
            while start > last and re_email_local.match(s[start - 1]):
                start -= 1
            d = re_email_domain.match(s, i + 1)
            if start < i and d is not None:
                end = d.end()
                if "." in s[i + 1:end] and s[end - 1] not in "-_":
                    if start > last:
                        pieces.append((s[last:start], None))
                    pieces.append((s[start:end], "mailto:" + s[start:end]))
                    last = i = end
                    continue
        i += 1
    if last < len(s):
        pieces.append((s[last:], None))
    return pieces


def _split_autolinks(s: str) -> list[tuple[str, str | None]]:
    pieces: list[tuple[str, str | None]] = []
    for text, url in _split_urls(s):
        if url is None:
            pieces.extend(_split_emails(text))
        else:
            pieces.append((text, url))
    return pieces


def _split_urls(s: str) -> list[tuple[str, str | None]]:
    pieces: list[tuple[str, str | None]] = []
    last = i = 0
    while i < len(s):
        before = s[i - 1] if i else ""
        # cmark-gfm: "www." after a space or one of *_~( ; "http(s)://" after
        # anything that is not a letter or digit
        www_ok = s.startswith("www.", i) and (i == 0 or is_unicode_whitespace(before) or before in "*_~(")
        url_ok = s[i] == "h" and (i == 0 or not re.match("[A-Za-z0-9]", before))
        if www_ok or url_ok:
            end = _autolink_end(s, i)
            if end > i:
                if i > last:
                    pieces.append((s[last:i], None))
                url = s[i:end]
                pieces.append((url, url if url.startswith("http") else "http://" + url))
                i = last = end
                continue
        i += 1
    if last < len(s):
        pieces.append((s[last:], None))
    return pieces


def _link_extended(parent: Node) -> None:
    # adjacent text nodes are one text first, so a link is not cut by how the
    # inline parser happened to split them
    node = parent.first_child
    while node is not None:
        if node.type == "text":
            while node.next is not None and node.next.type == "text":
                node.literal += node.next.literal
                node.next.unlink()
        node = node.next
    node = parent.first_child
    while node is not None:
        nxt = node.next
        if node.type == "text":
            pieces = _split_autolinks(node.literal)
            if any(url is not None for _, url in pieces):
                anchor = node
                for text, url in pieces:
                    if url is None:
                        new = _text(text)
                    else:
                        new = Node("link")
                        new.destination = url
                        new.title = ""
                        new.extended = True
                        new.append_child(_text(text))
                    anchor.insert_after(new)
                    anchor = new
                node.unlink()
        elif node.type in ("emph", "strong", "strikethrough"):
            _link_extended(node)
        node = nxt


# --- to the writer's tree -----------------------------------------------------


class Document:
    def __init__(self):
        self.blocks: list[dict] = []
        self.footnotes: dict[str, list[dict]] = {}
        self.footnote_order: list[str] = []  # by first reference
        self.front_matter: dict[str, str] = {}
        self.front_matter_lines: dict[str, int] = {}  # key -> the line it was last given on
        self.warnings: list[str] = []
        self.pending: dict[str, list[dict]] = {}


def parse(text: str) -> Document:
    doc = Document()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("\ufeff"):
        text = text[1:]
    text = unicodedata.normalize("NFC", text)
    long_sara_am: list[int] = []
    for no, ln in enumerate(text.split("\n"), 1):
        for ch in ln:
            label = forbidden_char(ch)
            if label is not None:
                raise Unsupported(no, f"text contains {label}; the build refuses it (ADR 0023, 0015)")
        # ำ written the long way. No normalisation joins these: NFC leaves them apart and NFKC
        # takes ำ the other way, into these two. So it is named and left alone (ADR 0034).
        if NIKHAHIT + SARA_AA in ln:
            long_sara_am.append(no)
    lines = text.split("\n")
    offset = _front_matter(lines, doc)
    # front matter lines become blank lines, so every line number stays true
    body = "\n".join([""] * offset + lines[offset:])
    bp = BlockParser()
    root = bp.parse(body)
    _resolve_inlines(bp, root)
    doc.blocks = _blocks(bp, root, doc)
    unreferenced = [label for label in bp.footnote_defs if label not in doc.footnotes]
    if unreferenced:
        fn = bp.footnote_defs[unreferenced[0]]
        raise Unsupported(fn.line, f"footnote [^{fn.label}] is defined but never referenced; nothing may be dropped silently (ADR 0023)")
    # a link definition nobody refers to is dropped by CommonMark itself. This project promises
    # that nothing goes silently (references/markdown.md), so it is named — a warning, not a
    # refusal, because unlike a footnote it takes no room in the document either way.
    for label, (line, written) in bp.ref_lines.items():
        if label not in bp.refs_used:
            bp.warnings.append("line " + str(line) + ": the link definition [" + written
                               + "] is never used; it is not written into the document")
    for no in long_sara_am:
        bp.warnings.append("line " + str(no) + ": " + NIKHAHIT + " followed by " + SARA_AA + " looks like "
                           + SARA_AM + " but is two characters; it is written as it stands and a search for "
                           + SARA_AM + " will not find it")
    doc.warnings = sorted(bp.warnings, key=lambda m: int(m.split(":")[0].split()[1]))
    return doc


re_front_matter_line = re.compile("^([A-Za-z_][A-Za-z0-9_-]*):(?:[ \\t]+([^\\n]*))?$")


def _front_matter(lines: list[str], doc: Document) -> int:
    """YAML-style front matter, only in its plainest form: `---` on the first line,
    then nothing but `key: value` lines (or blank ones), then `---` or `...`.
    Anything else is Markdown — a document that opens with a thematic break must
    not lose the text up to the next one. Returns the number of lines consumed."""
    if not lines or lines[0] != "---":
        return 0
    found: dict[str, str] = {}
    at: dict[str, int] = {}
    for i in range(1, len(lines)):
        line = lines[i]
        if line in ("---", "...") and found:
            doc.front_matter.update(found)
            doc.front_matter_lines.update(at)
            return i + 1
        if not line.strip(" \t"):
            continue
        m = re_front_matter_line.match(line)
        if m is None:
            return 0
        v = strip_ws(m.group(2) or "")
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        found[m.group(1)] = v
        at[m.group(1)] = i + 1
    return 0


def _inline_depth_within(block: Node, line: int) -> None:
    """Refuse inline formatting nested past MAX_DEPTH, before any walk recurses into it."""
    stack = [(n, 1) for n in block.children()]
    while stack:
        node, depth = stack.pop()
        if depth > MAX_DEPTH:
            raise Unsupported(line, f"inline formatting nested more than {MAX_DEPTH} deep is not supported")
        stack.extend((n, depth + 1) for n in node.children())


def _resolve_inlines(bp: BlockParser, node: Node) -> None:
    for child in node.children():
        if child.type in ("paragraph", "heading"):
            ip = InlineParser(bp, child.line)
            ip.parse(child)
            _inline_depth_within(child, child.line)
            _link_extended(child)
        elif child.type == "table":
            parsed = []
            for no, cells in child.rows:
                row = []
                for cell in cells:
                    holder = Node("paragraph", no)
                    holder.string_content = cell
                    InlineParser(bp, no).parse(holder)
                    _inline_depth_within(holder, no)
                    _link_extended(holder)
                    row.append(holder)
                parsed.append(row)
            child.rows = parsed
        elif child.first_child is not None:
            _resolve_inlines(bp, child)


def _inlines(bp: BlockParser, block: Node, doc: Document) -> list[dict]:
    out: list[dict] = []
    tags = {"sup": 0, "sub": 0, "u": 0, "kbd": 0}

    def walk(node: Node, flags: dict, link: str | None, extended: bool = False) -> None:
        for n in node.children():
            t = n.type
            if t == "text" or t == "code":
                f = dict(flags)
                if t == "code":
                    f["code"] = True
                out.append(("text", n.literal, f, link, dict(tags), extended))
            elif t == "softbreak":
                out.append(("soft", " ", dict(flags), link, dict(tags), extended))
            elif t == "linebreak":
                out.append(("hard",))
            elif t in ("emph", "strong", "strikethrough"):
                key = {"emph": "i", "strong": "b", "strikethrough": "strike"}[t]
                walk(n, {**flags, key: True}, link)
            elif t == "link":
                walk(n, flags, n.destination, n.extended)
            elif t == "image":
                out.append(("image", n.destination, _plain(n)))
            elif t == "footnote_ref":
                if n.label not in doc.footnotes:
                    doc.footnote_order.append(n.label)
                    doc.footnotes[n.label] = []  # filled after the body, in reference order
                out.append(("fn", n.label, doc.footnote_order.index(n.label) + 1))
            elif t == "html_tag":
                delta = 1 if n.literal == "open" else -1
                tags[n.label] = max(0, tags[n.label] + delta)

    walk(block, {}, None)
    if block.task is not None:
        result: list[dict] = [{"t": "task", "checked": block.task}]
    else:
        result = []
    for i, item in enumerate(out):
        kind = item[0]
        if kind in ("text", "soft"):
            s = item[1]
            if kind == "soft":
                prev = _neighbour(out, i, -1)
                nxt = _neighbour(out, i, 1)  # a neighbouring soft break is not Thai
                if nxt is None or prev is None:
                    s = ""  # nothing is rendered after it (or before it) in this paragraph
                elif prev and nxt and is_thai(prev) and is_thai(nxt):
                    s = ""
                else:
                    s = " "
            flags, link, tags_now = item[2], item[3], item[4]
            node = {"t": "text", "s": s, "b": bool(flags.get("b")), "i": bool(flags.get("i")),
                    "strike": bool(flags.get("strike")), "code": bool(flags.get("code") or tags_now["kbd"]),
                    "u": bool(tags_now["u"]), "sup": bool(tags_now["sup"]), "sub": bool(tags_now["sub"]) and not tags_now["sup"],
                    "link": link, "autolink": bool(item[5] and link)}
            result.append(node)
        elif kind == "hard":
            result.append({"t": "hardbreak"})
        elif kind == "image":
            result.append({"t": "image", "src": item[1], "alt": item[2]})
        elif kind == "fn":
            result.append({"t": "footnote_ref", "label": item[1], "id": item[2]})
    return _merge(result)


def _neighbour(out: list, i: int, step: int) -> str | None:
    """The character next to a soft break in the rendered text. Empty text is
    skipped; anything that is not text (an image, a break) gives ""; running off
    the paragraph gives None."""
    j = i + step
    while 0 <= j < len(out) and out[j][0] == "text" and not out[j][1]:
        j += step
    if not 0 <= j < len(out):
        return None
    if out[j][0] == "text":
        return out[j][1][-1] if step < 0 else out[j][1][0]
    return ""


def _merge(nodes: list[dict]) -> list[dict]:
    """Adjacent text with the same formatting is one node — cause 4 (ADR 0004)."""
    out: list[dict] = []
    for node in nodes:
        if node["t"] == "text" and not node["s"]:
            continue
        prev = out[-1] if out else None
        if (node["t"] == "text" and prev is not None and prev["t"] == "text"
                and all(prev[f] == node[f] for f in FLAGS) and prev["link"] == node["link"] and prev["autolink"] == node["autolink"]):
            prev["s"] += node["s"]
        else:
            out.append(dict(node))
    return out


def _plain(node: Node) -> str:
    parts = []
    for n in node.children():
        if n.type in ("text", "code"):
            parts.append(n.literal)
        elif n.type in ("softbreak", "linebreak"):
            parts.append(" ")
        elif n.first_child is not None:
            parts.append(_plain(n))
    return "".join(parts)


DIRECTIVES = ("front", "chapters", "back", "appendices", "toc", "list-of-tables", "list-of-figures")
re_directive = re.compile("<!--[ \\t]*([a-z-]+)[ \\t]*-->")  # fullmatch


re_near_directive = re.compile("<!--[ \\t]*([A-Za-z][A-Za-z _-]{0,30}?)[ \\t]*-->")  # fullmatch
DIRECTIVE_ALIASES = {"chapter": "chapters", "appendix": "appendices", "list-of-table": "list-of-tables",
                     "list-of-figure": "list-of-figures", "table-of-contents": "toc", "contents": "toc"}


def _edit_distance(a: str, b: str) -> int:
    row = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, row[0] = row[0], i
        for j, cb in enumerate(b, 1):
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + (ca != cb))
    return row[len(b)]


def _meant_directive(body: str) -> str | None:
    """The directive a comment of a word or two looks meant as: the same but for case or
    spacing, a known slip (chapter, appendix), or one or two letters off a long name."""
    m = re_near_directive.fullmatch(body)
    if m is None:
        return None
    word = re.sub("[ _]+", "-", m.group(1).lower())
    if word in DIRECTIVES:
        return word
    if word in DIRECTIVE_ALIASES:
        return DIRECTIVE_ALIASES[word]
    for name in DIRECTIVES:
        if _edit_distance(word, name) <= (2 if len(name) >= 6 else 1):
            return name
    return None


def _blocks(bp: BlockParser, node: Node, doc: Document) -> list[dict]:
    out = []
    for child in node.children():
        t = child.type
        if t == "heading":
            out.append({"t": "heading", "level": child.level, "inlines": _inlines(bp, child, doc), "line": child.line})
        elif t == "paragraph":
            out.append({"t": "paragraph", "inlines": _inlines(bp, child, doc), "line": child.line})
        elif t == "html_block":
            # a comment alone at the top level may be a directive (ADR 0021); any other renders
            # nothing — with a warning when it looks meant as one, so none is lost silently
            body = child.string_content.strip(" \t\n")
            d = re_directive.fullmatch(body)
            if node.type == "document" and d and d.group(1) in DIRECTIVES:
                out.append({"t": "directive", "name": d.group(1), "line": child.line})
            else:
                meant = _meant_directive(body)
                if meant and d and d.group(1) == meant:
                    bp.warnings.append(f"line {child.line}: <!-- {meant} --> works only at the top level, "
                                       "not inside a list, quotation or footnote; read as a comment")
                elif meant:
                    bp.warnings.append(f"line {child.line}: {body} is read as a comment; the comment that works is <!-- {meant} -->")
        elif t == "code_block":
            literal = child.literal or ""
            lines = literal.split("\n")
            if lines and lines[-1] == "":
                lines.pop()
            out.append({"t": "code", "lines": lines, "info": child.info or ("math" if child.math else ""), "math": child.math})
        elif t == "block_quote":
            out.append({"t": "quote", "blocks": _blocks(bp, child, doc)})
        elif t == "list":
            items = [_blocks(bp, item, doc) for item in child.children()]
            data = child.list_data
            out.append({"t": "list", "ordered": data["type"] == "ordered", "start": data["start"] or 1, "items": items})
        elif t == "thematic_break":
            out.append({"t": "break"})
        elif t == "table":
            rows = [[_inlines(bp, cell, doc) for cell in row] for row in child.rows]
            out.append({"t": "table", "aligns": child.aligns, "rows": rows, "line": child.line})
        elif t == "footnote_def":
            # footnote bodies are collected; their references may come later
            doc.pending[child.label] = _blocks(bp, child, doc)
    if node.type == "document":
        for label in doc.footnote_order:
            doc.footnotes[label] = doc.pending[label]
    return out


# --- what the .docx must carry (ADR 0023) -------------------------------------


THAI_DIGITS = str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙")


def plain_text(blocks: list[dict], numbers_are_text: bool = False, thai_digits: bool = False) -> list[str]:
    """Every paragraph's text, in document order. Hard breaks are newlines; task markers are
    □/■ (ADR 0033); images and footnote marks contribute nothing. `numbers_are_text` is the
    document whose numbers the build writes rather than the application (ADR 0036): there an
    ordered list's marker is text, in the document's own digits, and comes with the tab after
    it. Elsewhere
    the numbering part draws it, as it draws a bullet, and it is not text."""
    out: list[str] = []
    for b in blocks:
        t = b["t"]
        if t in ("paragraph", "heading"):
            out.append(inline_text(b["inlines"]))
        elif t == "code":
            out.extend(b["lines"] or [""])
        elif t == "quote":
            out.extend(plain_text(b["blocks"], numbers_are_text, thai_digits))
        elif t == "list":
            for n, item in enumerate(b["items"]):
                marker = ""
                if numbers_are_text and b["ordered"] and not (item and item[0]["t"] == "paragraph"
                                                             and item[0]["inlines"] and item[0]["inlines"][0]["t"] == "task"):
                    number = str(b["start"] + n)
                    marker = (number.translate(THAI_DIGITS) if thai_digits else number) + ".\t"
                if not item or item[0]["t"] != "paragraph":
                    out.append(marker)  # the writer gives such an item a paragraph with the marker alone
                    out.extend(plain_text(item, numbers_are_text, thai_digits))
                    continue
                lines = plain_text(item, numbers_are_text, thai_digits)
                out.extend([marker + lines[0]] + lines[1:] if lines else [marker])
        elif t == "table":
            for row in b["rows"]:
                for cell in row:
                    out.append(inline_text(cell))
    return out


def inline_text(inlines: list[dict]) -> str:
    parts = []
    for n in inlines:
        if n["t"] == "text":
            parts.append(n["s"])
        elif n["t"] == "hardbreak":
            parts.append("\n")
        elif n["t"] == "task":
            parts.append("■ " if n["checked"] else "□ ")
    return "".join(parts)
