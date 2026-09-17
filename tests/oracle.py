# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Independent readings of the same Markdown, to hold the parser to its references.

Two reference implementations judge it, each on the dialect it defines:

- commonmark.js 0.31.2, the CommonMark reference implementation, on documents
  with nothing but CommonMark in them (tests/js/cm_canon.cjs, run under Node.js);
- cmark-gfm, GitHub's renderer, on documents with GFM tables, strikethrough,
  task items, autolinks and footnotes (its HTML read back by _GfmHtml).

Our tree and each reference's output are reduced to one canonical sequence —
block structure, text, and each run's formatting — and compared. Where the two
references read CommonMark differently this parser follows commonmark.js, and
known_divergence() names each such case. Test-only: nothing here ships.

What the reduction deliberately normalizes, each tied to a decision:
- a soft break between two Thai characters is nothing, any other is a space (ADR 0005 §1)
- a task marker is its own item and the one space after it is consumed (ADR 0005 §2)
- link destinations are compared after markdown-it's own normalization on both sides,
  and a link with an empty destination is plain text: a Word hyperlink needs a target
- image alt text is not compared (ADR 0005 §4: it is not body text)
- a code line of only spaces and tabs compares as empty: inside a list item the
  references disagree on keeping the spaces, and neither reading is visible
"""

from __future__ import annotations

import json
import pathlib
import random
import re
import subprocess

from markdown_it import MarkdownIt

from thai_docx.ooxml import is_thai

MDIT = MarkdownIt("commonmark")  # only for its link normalization, applied to every side alike


def norm_link(url: str) -> str:
    return MDIT.normalizeLinkText(MDIT.normalizeLink(url))


def _blank_code_lines(code: str) -> str:
    return "\n".join("" if not ln.strip(" \t") else ln for ln in code.split("\n"))


def _resolve(items: list[tuple]) -> tuple:
    """Soft breaks to text by the Thai rule, then merge equal neighbours."""
    out: list[tuple] = []
    items = [it for it in items if not (it[0] == "t" and not it[1])]
    for i, it in enumerate(items):
        if it[0] == "soft":
            prev = items[i - 1] if i else None
            nxt = items[i + 1] if i + 1 < len(items) else None
            if prev is None or nxt is None or prev[0] == "task":
                it = ("t", "", it[2], it[3])  # nothing rendered before or after it in the paragraph
            else:
                p = prev[1][-1] if prev[0] == "t" and prev[1] else ""
                n = nxt[1][0] if nxt[0] == "t" and nxt[1] else ""
                it = ("t", "" if p and n and is_thai(p) and is_thai(n) else " ", it[2], it[3])
        if it[0] == "t" and not it[1]:
            continue
        if it[0] == "t" and out and out[-1][0] == "t" and out[-1][2:] == it[2:]:
            out[-1] = ("t", out[-1][1] + it[1], it[2], it[3])
        else:
            out.append(it)
    return tuple(out)


# --- our tree -------------------------------------------------------------------


def _ours_inline(inlines: list[dict], core: bool) -> tuple:
    items: list[tuple] = []
    for n in inlines:
        t = n["t"]
        if t == "text":
            f = frozenset(k for k in ("b", "i", "strike", "code", "u", "sup", "sub") if n[k])
            link = n["link"] if n["link"] and not (core and n["autolink"]) else None
            items.append(("t", n["s"], f, norm_link(link) if link else None))
        elif t == "hardbreak":
            items.append(("br",))
        elif t == "image":
            items.append(("img", norm_link(n["src"])))
        elif t == "footnote_ref":
            items.append(("fn", n["id"]))
        elif t == "task":
            items.append(("task", None if gfm_task_presence_only[0] else n["checked"]))
    return _resolve(items)


gfm_task_presence_only = [False]


def _ours_blocks(blocks: list[dict], out: list[tuple], core: bool = False) -> None:
    for b in blocks:
        t = b["t"]
        if t == "heading":
            out.append(("h", b["level"], _ours_inline(b["inlines"], core)))
        elif t == "paragraph":
            out.append(("p", _ours_inline(b["inlines"], core)))
        elif t == "code":
            out.append(("code", _blank_code_lines("\n".join(b["lines"]))))
        elif t == "break":
            out.append(("hr",))
        elif t == "quote":
            out.append(("bq",))
            _ours_blocks(b["blocks"], out, core)
            out.append(("/bq",))
        elif t == "list":
            out.append(("ol", b["start"]) if b["ordered"] else ("ul",))
            for item in b["items"]:
                out.append(("li",))
                _ours_blocks(item, out, core)
                out.append(("/li",))
            out.append(("/ol",) if b["ordered"] else ("/ul",))
        elif t == "table":
            out.append(("table", tuple(b["aligns"])))
            for row in b["rows"]:
                out.append(("tr",))
                for cell in row:
                    out.append(("cell", _ours_inline(cell, core)))
            out.append(("/table",))


def ours_canon(doc, core: bool = False) -> list[tuple]:
    """`core`: compare as CommonMark sees it — GFM extended autolinks are text."""
    out: list[tuple] = []
    _ours_blocks(doc.blocks, out, core)
    for n, label in enumerate(doc.footnote_order, 1):
        out.append(("fn", n))
        _ours_blocks(doc.footnotes[label], out, core)
        out.append(("/fn",))
    return out


# --- a generator of Markdown that stays inside the compared dialect -------------

# No astral characters (emoji): both reference implementations classify a
# delimiter's neighbour by UTF-16 code unit, so they read an emoji as neither
# space nor punctuation, against CommonMark 0.31 (Unicode P or S). Emoji flanking
# is held by unit tests instead.
WORDS = ["สวัสดี", "ภาษาไทย", "ก", "ข้อความ", "ทดสอบ", "ครับ", "foo", "bar", "a", "b", "Word", "๑๒๓", "©", "→"]
PUNCT = ["*", "**", "***", "_", "__", "~~", "`", "``", "[", "]", "(", ")", "![", "](/u)", "](/ข้อ)", "<", ">",
         "&amp;", "&copy;", "&#169;", "&#x0E01;", "&bogus;", "\\*", "\\_", "\\[", "\\", "!", ":", ".", ",", "-", "#",
         "|", "\\|", "\"", "'", "<https://x.example/p>", "<me@x.example>", "<u>", "</u>", "<sup>", "</sup>",
         "<kbd>", "</kbd>", "<br>", "<!-- c -->", "[^1]", "[^n]", "[ref]", "[ref][]", "[x][ref]", "1.", "+", "=",
         "\t", "  "]


def _inline(rng: random.Random) -> str:
    parts = []
    for _ in range(rng.randint(1, 9)):
        r = rng.random()
        if r < 0.45:
            parts.append(rng.choice(WORDS))
        elif r < 0.6:
            parts.append(" ")
        else:
            parts.append(rng.choice(PUNCT))
    return "".join(parts)


GFM_KINDS = ["p", "p", "p", "h", "setext", "list", "olist", "quote", "code", "fence", "hr", "table", "task", "lazy"]
CORE_KINDS = ["p", "p", "p", "h", "setext", "list", "olist", "quote", "code", "fence", "hr", "lazy"]


def _block(rng: random.Random, depth: int = 0, kinds: list = GFM_KINDS, tame: bool = False) -> list[str]:
    """`tame` keeps to exact continuation indents, `> ` quotes and no lazy lines:
    the structure CommonMark leaves to laziness is judged by the reference
    implementation in the core corpus, so the GFM corpus judges GFM alone."""
    kind = rng.choice(kinds)
    if tame and kind in ("lazy", "code"):
        kind = "p"
    if tame and kind == "p":
        # no raw tag opens a line: a lone tag on a lazy line is an HTML block to
        # cmark-gfm and paragraph text to commonmark.js (see known_divergence)
        lines = [_inline(rng).lstrip(" \t") or "x" for _ in range(rng.randint(1, 3))]
        return ["x" + ln if ln.startswith("<") else ln for ln in lines]
    if depth > 2 and kind in ("list", "olist", "quote", "task"):
        kind = "p"
    if kind == "p":
        return [_inline(rng) for _ in range(rng.randint(1, 3))]
    if kind == "h":
        return ["#" * rng.randint(1, 7) + rng.choice([" ", "", "  "]) + _inline(rng) + rng.choice(["", " #", " ##"])]
    if kind == "setext":
        if tame:
            first = _inline(rng).lstrip(" \t") or "x"
            return ["x" + first if first.startswith("<") else first, rng.choice(["===", "---"])]
        return [_inline(rng), rng.choice(["===", "---", "  --", "= ="])]
    if kind in ("list", "olist", "task"):
        lines = []
        for _ in range(rng.randint(1, 3)):
            marker = rng.choice(["-", "*", "+"]) if kind != "olist" else rng.choice(["1.", "2.", "3)", "10."])
            pad = " " if tame else rng.choice([" ", "  ", "   ", "     "])
            head = marker + pad + (rng.choice(["[ ] ", "[x] ", "[X] ", "[ ]", "[y] "]) if kind == "task" else "")
            body = _block(rng, depth + 1, kinds, tame)
            indent = " " * (len(marker) + len(pad))
            lines.append(head + body[0])
            for extra in body[1:]:
                lines.append((indent if tame else rng.choice([indent, "", " "])) + extra)
            if rng.random() < 0.3:
                lines.append("")
        return lines
    if kind == "quote":
        return [(("> " if tame else rng.choice(["> ", ">", " > "])) + ln) for ln in _block(rng, depth + 1, kinds, tame)]
    if kind == "code":
        return ["    " + _inline(rng) for _ in range(rng.randint(1, 2))]
    if kind == "fence":
        f = rng.choice(["```", "~~~", "````"])
        return [f + rng.choice(["", "py", " ภาษา"])] + [_inline(rng) for _ in range(rng.randint(0, 2))] + ([f] if rng.random() < 0.9 else [])
    if kind == "hr":
        return [rng.choice(["---", "***", "_ _ _", " - - -"])]
    if kind == "table":
        n = rng.randint(1, 3)
        head = "| " + " | ".join(_inline(rng).replace("\\|", "").replace("|", "") or "h" for _ in range(n)) + " |"
        delim = "|" + "|".join(rng.choice(["---", ":--", "--:", ":-:"]) for _ in range(n)) + "|"
        rows = ["| " + " | ".join(_inline(rng).replace("\\|", "").replace("|", "") for _ in range(rng.randint(1, n))) + " |"
                for _ in range(rng.randint(0, 2))]
        return [head, delim] + rows
    return [_inline(rng), rng.choice(["", "  "]) + _inline(rng)]


GFM_WORDS = [w for w in WORDS if w not in ("©", "→")]
GFM_PUNCT = [p for p in PUNCT if p not in ("\t", "<!-- c -->", "\\")]
EMPTY_ITEM = re.compile(r"^[ \t>]*(?:[-*+]|[0-9]{1,9}[.)])(?:[ \t]+(?:[-*+]|[0-9]{1,9}[.)]))*[ \t]*$")
LONE_TAG = re.compile(r"^[ \t>*+0-9.)-]*</?[A-Za-z][A-Za-z0-9-]*[ \t]*/?>[ \t]*$")


def generate_gfm(seed: int) -> str:
    """The GFM corpus, judged by cmark-gfm. Tame structure, no tabs, no symbol
    characters: where cmark-gfm and commonmark.js read CommonMark differently —
    laziness, trailing tabs, S-category punctuation (cmark-gfm still reads only
    the P categories) — this parser follows commonmark.js and CommonMark 0.31.2,
    and the core corpus judges it there. This corpus judges the GFM additions."""
    rng = random.Random(seed)
    saved_w, saved_p = WORDS[:], PUNCT[:]
    WORDS[:], PUNCT[:] = GFM_WORDS, GFM_PUNCT
    try:
        text = _generate(rng, True)
    finally:
        WORDS[:], PUNCT[:] = saved_w, saved_p
    # a tag alone on a line: cmark-gfm may open an HTML block where commonmark.js
    # continues a paragraph lazily; the core corpus covers such lines
    # and no empty list item: an item that opens with a blank line and is followed
    # by one is closed in commonmark.js and kept open in cmark-gfm
    return "\n".join(ln + "x" if LONE_TAG.match(ln) or EMPTY_ITEM.match(ln) else ln for ln in text.split("\n"))


def _generate(rng: random.Random, tame: bool) -> str:
    lines: list[str] = []
    for _ in range(rng.randint(1, 6)):
        lines.extend(_block(rng, 0, GFM_KINDS, tame))
        if rng.random() < 0.7:
            lines.append("")
    if rng.random() < 0.4:
        lines += ["", "[ref]: /url \"title\""]
    if rng.random() < 0.4:
        lines += ["", "see[^1]", "", "[^1]: note " + _inline(rng)]
    if rng.random() < 0.2:
        lines += ["", "and[^n]", "", "[^n]: another", "    continued " + _inline(rng)]
    return "\n".join(lines) + rng.choice(["", "\n"])


# --- the reference implementation, for the core dialect --------------------------

CM_CANON = pathlib.Path(__file__).resolve().parent / "js" / "cm_canon.cjs"


def cm_canon_many(texts: list[str]) -> list:
    """commonmark.js's reading of each text, as canonical sequences. Needs Node.js
    and `npm ci` in tests/js."""
    done = subprocess.run(["node", str(CM_CANON)], input=json.dumps(texts), capture_output=True, text=True, check=True)
    results = []
    for raw in json.loads(done.stdout):
        if isinstance(raw, dict):
            results.append(raw)
            continue
        seq = []
        for entry in raw:
            if entry[0] == "html_block" and not re.sub(r"<!--[\s\S]*?-->", "", entry[1]).strip(" \t\n"):
                continue  # a comment block renders nothing; the build drops it too
            if entry[0] in ("h", "p", "cell"):
                items = entry[-1]
                conv = []
                for it in items:
                    if it[0] in ("t", "soft"):
                        conv.append((it[0], it[1], frozenset(it[2]), norm_link(it[3]) if it[3] else None))
                    elif it[0] == "img":
                        conv.append(("img", norm_link(it[1])))
                    else:
                        conv.append(tuple(it))
                seq.append(tuple(entry[:-1]) + (_resolve(conv),))
            elif entry[0] == "code":
                seq.append(("code", _blank_code_lines(entry[1])))
            else:
                seq.append(tuple(entry))
        results.append(seq)
    return results


CORE_PUNCT = [p for p in PUNCT if p not in ("~~", "[^1]", "[^n]", "|", "\\|")]


def generate_core(seed: int) -> str:
    """Markdown with nothing but CommonMark in it: no tables, strikethrough,
    footnotes or task items, so the reference implementation can judge it."""
    rng = random.Random(seed)
    saved = PUNCT[:]
    PUNCT[:] = CORE_PUNCT
    try:
        lines: list[str] = []
        for _ in range(rng.randint(1, 6)):
            lines.extend(_block(rng, 0, CORE_KINDS))
            if rng.random() < 0.7:
                lines.append("")
        if rng.random() < 0.4:
            lines += ["", "[ref]: /url \"title\""]
        return "\n".join(lines) + rng.choice(["", "\n"])
    finally:
        PUNCT[:] = saved


# --- cmark-gfm, GitHub's own renderer, for the GFM dialect --------------------

import html.parser  # noqa: E402

import cmarkgfm  # noqa: E402
from cmarkgfm.cmark import Options  # noqa: E402

_BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "hr", "blockquote", "ul", "ol", "li", "table",
               "thead", "tbody", "tr", "th", "td", "section"}


class _GfmHtml(html.parser.HTMLParser):
    """cmark-gfm's HTML back to the canonical sequence. Inline content that sits
    directly in <li> or <td>/<th> (tight lists, table cells) is an implicit
    paragraph or cell."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[tuple] = []
        self.footnotes: list[tuple] = []
        self.target = self.out
        self.inline: list[tuple] | None = None  # items of the open paragraph-like block
        self.inline_kind: tuple | None = None
        self.flags = {"b": 0, "i": 0, "strike": 0, "code": 0}
        self.tags = {"sup": 0, "sub": 0, "u": 0, "kbd": 0}
        self.links: list = []
        self.in_pre = False
        self.pre_text: list[str] = []
        self.skip = 0  # inside a footnote back-reference or reference number
        self.fnref_text: list[str] | None = None
        self.strip_space = False
        self.in_footnotes = False
        self.fn_count = 0
        self.table_aligns: list | None = None
        self.stack: list[str] = []

    def _fl(self) -> frozenset:
        f = {k for k in ("b", "i", "strike", "code") if self.flags[k]}
        if self.tags["kbd"]:
            f.add("code")
        if self.tags["u"]:
            f.add("u")
        if self.tags["sup"]:
            f.add("sup")
        elif self.tags["sub"]:
            f.add("sub")
        return frozenset(f)

    def _open_inline(self, kind: tuple) -> None:
        self.inline = []
        self.inline_kind = kind

    def _close_inline(self) -> None:
        if self.inline is None:
            return
        items = self.inline
        # a newline before or after a nested block is layout, not a soft break
        while items and items[-1][0] == "soft":
            items.pop()
        while items and items[0][0] == "soft":
            items.pop(0)
        kind = self.inline_kind
        # raw inline tags and emphasis never outlive their block in Markdown,
        # whatever an HTML tree would make of an unclosed <u>
        self.flags = {k: 0 for k in self.flags}
        self.tags = {k: 0 for k in self.tags}
        self.links = []
        if kind == ("implicit",):
            if items:
                self.target.append(("p", _resolve(items)))
        else:
            self.target.append(kind + (_resolve(items),))
        self.inline = None
        self.inline_kind = None

    def _ensure_inline(self) -> None:
        if self.inline is None:
            self._open_inline(("implicit",))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.skip:
            self.skip += 1 if tag in ("a", "sup") else 0
            return
        if tag == "sup" and a.get("class") == "footnote-ref":
            self._ensure_inline()
            self.fnref_text = []
            self.skip = 1
            return
        if tag == "a" and "data-footnote-backref" in a:
            # the space cmark-gfm writes before a back-reference is not content
            if self.inline and self.inline[-1][0] == "t" and self.inline[-1][1].endswith(" "):
                last = self.inline[-1]
                self.inline[-1] = ("t", last[1][:-1]) + last[2:]
            self.skip = 1
            return
        if tag in _BLOCK_TAGS:
            carried = []
            if tag == "p" and self.inline_kind == ("implicit",) and self.inline and all(it[0] in ("task", "soft") for it in self.inline):
                carried = [it for it in self.inline if it[0] == "task"]  # a loose task item: <li><input/> <p>
                self.inline = None
                self.inline_kind = None
            if tag not in ("li", "td", "th", "tr", "thead", "tbody"):
                self._close_inline()
            self.stack.append(tag)
            if tag == "p" or tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                self._close_inline()
                self._open_inline(("p",) if tag == "p" else ("h", int(tag[1])))
                self.inline.extend(carried)
            elif tag == "pre":
                self.in_pre = True
                self.pre_text = []
            elif tag == "hr":
                self.target.append(("hr",))
                self.stack.pop()
            elif tag == "blockquote":
                self.target.append(("bq",))
            elif tag == "ul":
                self._close_inline()
                self.target.append(("ul",))
            elif tag == "ol":
                self._close_inline()
                if self.in_footnotes:
                    return
                self.target.append(("ol", int(a.get("start", 1))))
            elif tag == "li":
                self._close_inline()
                if self.in_footnotes:
                    self.fn_count += 1
                    self.target = self.footnotes
                    self.target.append(("fn", self.fn_count))
                else:
                    self.target.append(("li",))
            elif tag == "table":
                self.table_aligns = []
                self.target.append(("table", None))  # aligns filled at </thead>
                self._table_index = len(self.target) - 1
            elif tag == "tr":
                self.target.append(("tr",))
            elif tag in ("th", "td"):
                if tag == "th":
                    self.table_aligns.append(a.get("align"))
                self._open_inline(("cell",))
            elif tag == "section":
                self.in_footnotes = True
            return
        if tag == "code" and self.in_pre:
            return
        if tag == "input" and a.get("type") == "checkbox":
            self._ensure_inline()
            self.inline.append(("task", None))  # checked state not trusted: cmark-gfm marks "- [ ] a [x]" checked
            self.strip_space = True
            return
        self._ensure_inline()
        if tag == "br":
            self.inline.append(("br",))
        elif tag in ("em",):
            self.flags["i"] += 1
        elif tag == "strong":
            self.flags["b"] += 1
        elif tag == "del":
            self.flags["strike"] += 1
        elif tag == "code" and not self.in_pre:
            self.flags["code"] += 1
        elif tag == "a":
            self.links.append(norm_link(a.get("href", "")) or None)
        elif tag == "img":
            self.inline.append(("img", norm_link(a.get("src", ""))))
        elif tag in self.tags:
            self.tags[tag] += 1
        elif tag != "code":
            self.inline.append(("html", tag))

    def handle_startendtag(self, tag, attrs):
        if tag == "br" and not self.skip:
            self._ensure_inline()
            self.inline.append(("br",))
            self.after_hardbreak = True  # cmark-gfm writes a hard break as "<br />\n"
            return
        self.handle_starttag(tag, attrs)
        if tag in self.tags or tag in ("em", "strong", "del", "a"):
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.skip:
            if tag in ("a", "sup"):
                self.skip -= 1
                if self.skip == 0 and self.fnref_text is not None:
                    self.inline.append(("fn", int("".join(self.fnref_text))))
                    self.fnref_text = None
            return
        if tag in _BLOCK_TAGS:
            if self.stack and self.stack[-1] == tag:
                self.stack.pop()
            if tag in ("p", "h1", "h2", "h3", "h4", "h5", "h6", "th", "td"):
                self._close_inline()
            elif tag == "pre":
                self.in_pre = False
                code = "".join(self.pre_text)
                self.target.append(("code", _blank_code_lines(code[:-1] if code.endswith("\n") else code)))
            elif tag == "blockquote":
                self._close_inline()
                self.target.append(("/bq",))
            elif tag == "ul":
                self._close_inline()
                self.target.append(("/ul",))
            elif tag == "ol":
                self._close_inline()
                if not self.in_footnotes:
                    self.target.append(("/ol",))
            elif tag == "li":
                self._close_inline()
                if self.in_footnotes:
                    self.target.append(("/fn",))
                    self.target = self.out
                else:
                    self.target.append(("/li",))
            elif tag == "thead":
                i = self._table_index
                self.target[i] = ("table", tuple(self.table_aligns))
            elif tag == "table":
                self.target.append(("/table",))
            elif tag == "section":
                self.in_footnotes = False
            return
        if tag == "em":
            self.flags["i"] -= 1
        elif tag == "strong":
            self.flags["b"] -= 1
        elif tag == "del":
            self.flags["strike"] -= 1
        elif tag == "code" and not self.in_pre:
            self.flags["code"] -= 1
        elif tag == "a":
            if self.links:
                self.links.pop()
        elif tag in self.tags:
            self.tags[tag] = max(0, self.tags[tag] - 1)
        elif tag == "br":
            self._ensure_inline()
            self.inline.append(("br",))

    def handle_data(self, data):
        if self.skip:
            if self.fnref_text is not None:
                self.fnref_text.append(data)
            return
        if self.in_pre:
            self.pre_text.append(data)
            return
        if self.inline is None:
            if not data.strip("\n"):
                return
            self._ensure_inline()
        if self.strip_space:
            if data[:1] in (" ", "\t"):
                data = data[1:]
            self.strip_space = False
        if getattr(self, "after_hardbreak", False):
            self.after_hardbreak = False
            if data.startswith("\n"):
                data = data[1:]  # the newline after "<br />" is layout
                if not data:
                    return
        link = self.links[-1] if self.links else None
        parts = data.split("\n")
        for k, part in enumerate(parts):
            if k:
                self.inline.append(("soft", " ", self._fl(), link))
            if part:
                self.inline.append(("t", part, self._fl(), link))

    def handle_comment(self, data):
        pass


def gfm_canon(text: str) -> list[tuple]:
    rendered = cmarkgfm.github_flavored_markdown_to_html(text, options=Options.CMARK_OPT_UNSAFE | Options.CMARK_OPT_FOOTNOTES)
    parser = _GfmHtml()
    parser.feed(rendered)
    parser.close()
    parser._close_inline()
    return parser.out + parser.footnotes



# --- where cmark-gfm and commonmark.js read CommonMark differently --------------
#
# The GFM corpus is judged by cmark-gfm; a mismatch is accepted only when it falls
# in one of these named categories, and in each the core corpus holds this parser
# to commonmark.js on the same construct.


def _code_ws(seq: list[tuple]) -> list[tuple]:
    """Whitespace runs inside code spans collapsed: cmark-gfm keeps a continuation
    line's indentation inside a code span, commonmark.js removes it."""
    out = []
    for entry in seq:
        if entry[0] in ("p", "h", "cell"):
            items = tuple(
                (it[0], re.sub(" +", " ", it[1])) + it[2:] if it[0] == "t" and "code" in it[2] else it
                for it in entry[-1]
            )
            out.append(tuple(entry[:-1]) + (_resolve(list(items)),))
        else:
            out.append(entry)
    return out


def _flags_only(seq: list[tuple]) -> list[tuple]:
    """Text with formatting, links and emphasis delimiters dropped, block structure kept."""
    out = []
    for entry in seq:
        if entry[0] in ("p", "h", "cell"):
            text = "".join(it[1] for it in entry[-1] if it[0] == "t").replace("*", "").replace("_", "")
            others = tuple(it for it in entry[-1] if it[0] != "t")
            out.append(tuple(entry[:-1]) + (text, others))
        else:
            out.append(entry)
    return out


def _link_syntax_free(seq: list[tuple]) -> list[tuple]:
    """Text with link destinations, brackets and links dropped."""
    out = []
    for entry in seq:
        if entry[0] in ("p", "h", "cell"):
            text = "".join(it[1] for it in entry[-1] if it[0] == "t")
            text = re.sub(r"\]\([^)]*\)", "", text).replace("[", "").replace("]", "")
            out.append(tuple(entry[:-1]) + (text, tuple(it for it in entry[-1] if it[0] not in ("t",))))
        else:
            out.append(entry)
    return out


def _renumber_footnotes(seq: list[tuple]) -> list[tuple]:
    order: dict[int, int] = {}

    def num(n):
        return order.setdefault(n, len(order) + 1)

    body = []
    for entry in seq:
        if entry[0] in ("p", "h", "cell"):
            items = tuple(("fn", num(it[1])) if it[0] == "fn" else it for it in entry[-1])
            body.append(tuple(entry[:-1]) + (items,))
        else:
            body.append(entry)
    # footnote bodies, re-sorted by their new numbers
    out, notes, current = [], {}, None
    for entry in body:
        if entry[0] == "fn" and len(entry) == 2 and current is None:
            current = [("fn", num(entry[1]))]
        elif entry[0] == "/fn":
            current.append(entry)
            notes[current[0][1]] = current
            current = None
        elif current is not None:
            current.append(entry)
        else:
            out.append(entry)
    for n in sorted(notes):
        out.extend(notes[n])
    return out


def _no_code_syntax(seq: list[tuple]) -> list[tuple]:
    out = []
    for entry in seq:
        if entry[0] in ("p", "h", "cell"):
            text = "".join(it[1] for it in entry[-1] if it[0] == "t").replace("`", "").replace("\\", "")
            out.append(tuple(entry[:-1]) + (re.sub(" +", " ", text), tuple(it for it in entry[-1] if it[0] != "t")))
        else:
            out.append(entry)
    return out


def known_divergence(text: str, ours: list[tuple], gfm: list[tuple]) -> str | None:
    """The category a mismatch falls in, or None when it is unexplained."""
    if "`" in text and _no_code_syntax(ours) == _no_code_syntax(gfm):
        return "code span after an unmatched shorter backtick run (cmark-gfm misses it)"
    if "![" in text and _renumber_footnotes(ours) == _renumber_footnotes(gfm):
        return "footnote reference inside image alt text numbered by cmark-gfm"
    if [e for e in ours if e != ("p", ())] == [e for e in gfm if e != ("p", ())]:
        return "paragraph of raw tags only, which HTML shows as nothing"
    if "[^" in text and _link_syntax_free(ours) == _link_syntax_free(gfm):
        return "link inside a link around a footnote-style bracket (cmark-gfm; commonmark.js refuses it)"
    if re.search(r"^[ >*+0-9.)-]*\[[^\]]+\]:.*\n[ >]*-+[ \t]*$", text, re.M):
        # commonmark.js: an emptied paragraph, then a thematic break;
        # cmark-gfm: the dashes as that paragraph's text
        a = []
        k = 0
        while k < len(ours):
            if ours[k] == ("p", ()) and k + 1 < len(ours) and ours[k + 1] == ("hr",):
                a.append(("dashes",))
                k += 2
                continue
            a.append(ours[k])
            k += 1
        b = [("dashes",) if e[0] == "p" and len(e[1]) == 1 and e[1][0][0] == "t" and re.fullmatch("-+", e[1][0][1]) else e for e in gfm]
        if a == b:
            return "setext-like underline under a paragraph of link definitions only"
    if _code_ws(ours) == _code_ws(gfm):
        return "code-span continuation indentation"
    if re.search(r"[*_]~|~[*_]", text) and _flags_only(ours) == _flags_only(gfm):
        return "emphasis beside unpaired strikethrough tildes"
    return None


# --- a wide corpus for comparing the two implementations with each other -------
# No reference judges this one: it exists to find where Python and JavaScript
# strings disagree — astral characters beside delimiters, Unicode spaces,
# combining marks, line separators, CRLF, entities past the BMP, and characters
# the build refuses (whose line numbers must agree too).

WIDE_EXTRA = ["😀", "a😀", "😀*", "*😀", "_😀_", "𝒜", "\u00a0", "\u3000", "\u2028", "\u2029", "e\u0301", "กำ", "\u0e33",
              "&#x1F600;", "&#128512;", "&#9;", "&#x0;", "&#xD800;", "&#x110000;", "[😀]", "[😀]: /😀", "<😀>", "\r\n", "\r",
              "\t", "www.😀.example", "a@😀.example", "https://x.example/😀)", "$😀$", "\ufb01", "\u216b", "ก่ำ"]
WIDE_REFUSED = ["\u200b", "\x07", "\ufeff", "&#10;", "&#x7F;", "\ufffe"]


def generate_wide(seed: int) -> str:
    rng = random.Random(seed)
    saved_w, saved_p = WORDS[:], PUNCT[:]
    WORDS[:] = saved_w + WIDE_EXTRA
    PUNCT[:] = saved_p + WIDE_EXTRA
    try:
        text = _generate(rng, False)
    finally:
        WORDS[:], PUNCT[:] = saved_w, saved_p
    if rng.random() < 0.08:
        lines = text.split("\n")
        k = rng.randrange(len(lines))
        lines[k] += rng.choice(WIDE_REFUSED)
        text = "\n".join(lines)
    return ("\ufeff" if rng.random() < 0.05 else "") + text
