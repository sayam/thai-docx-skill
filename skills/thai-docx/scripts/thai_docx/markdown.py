"""Markdown → a small block/inline tree, for the dialect ADR 0010 accepts.

CommonMark blocks and inlines, GFM tables / strikethrough / autolinks / task
items, GitHub footnotes. Anything outside that set raises `Unsupported` with the
line it was found on: the build stops rather than guess (ADR 0005, 0010).

The tree is plain dicts, so the JavaScript port can produce the same one:

  block  {"t": "heading", "level": n, "inlines": [...]}
         {"t": "paragraph", "inlines": [...]}
         {"t": "code", "lines": [...], "info": str, "math": bool}
         {"t": "quote", "blocks": [...]}
         {"t": "list", "ordered": bool, "start": int, "items": [[block, ...], ...]}
         {"t": "table", "aligns": [...], "rows": [[[inline, ...], ...], ...]}
         {"t": "break"}
         {"t": "footnote", "label": str, "blocks": [...]}    (collected, not in body)
  inline {"t": "text", "s": str, "b","i","strike","code","u","sup","sub": bool,
          "link": url|None}
         {"t": "hardbreak"}   {"t": "image", "src": str, "alt": str}
         {"t": "footnote_ref", "label": str}   {"t": "task", "checked": bool}
"""

from __future__ import annotations

import html
import re
import unicodedata

from .ooxml import INVISIBLE, is_thai


class Unsupported(Exception):
    def __init__(self, line: int, what: str):
        super().__init__(f"line {line}: {what}")
        self.line = line
        self.what = what


FLAGS = ("b", "i", "strike", "code", "u", "sup", "sub")
ALLOWED_TAGS = {"br", "sup", "sub", "u", "kbd"}

_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*(.*)$")
_ATX = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
_HR = re.compile(r"^ {0,3}((\*[ \t]*){3,}|(-[ \t]*){3,}|(_[ \t]*){3,})$")
_SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
_QUOTE = re.compile(r"^ {0,3}>(.*)$")
_ITEM = re.compile(r"^( {0,3})([-*+]|\d{1,9}[.)])( {1,4}(?=\S)|(?=\s*$))")
_TABLE_DELIM = re.compile(r"^ {0,3}\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
_FOOTNOTE_DEF = re.compile(r"^ {0,3}\[\^([^\]\s]+)\]:[ \t]?(.*)$")
_LINK_DEF = re.compile(r"""^ {0,3}\[([^\]]+)\]:[ \t]*(\S+)(?:[ \t]+("[^"]*"|'[^']*'|\([^)]*\)))?[ \t]*$""")
_HTML_BLOCK = re.compile(r"^ {0,3}<(/?)([A-Za-z][A-Za-z0-9-]*)")
_MATH_FENCE = re.compile(r"^ {0,3}\$\$\s*(.*)$")
_TASK = re.compile(r"^\[( |x|X)\][ \t]+")


class Document:
    def __init__(self):
        self.blocks: list[dict] = []
        self.footnotes: dict[str, list[dict]] = {}
        self.footnote_order: list[str] = []
        self.link_defs: dict[str, str] = {}
        self.front_matter: dict[str, str] = {}
        self.warnings: list[str] = []


def parse(text: str) -> Document:
    doc = Document()
    text = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    lines = text.lstrip("\ufeff").split("\n")
    for no, line in enumerate(lines, 1):
        for ch, label in INVISIBLE.items():
            if ch in line:
                raise Unsupported(no, f"text contains {label}; the build never adds or keeps invisible characters (ADR 0005)")
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() in ("---", "..."):
                for raw in lines[1:i]:
                    if ":" in raw and not raw.startswith((" ", "#")):
                        k, v = raw.split(":", 1)
                        doc.front_matter[k.strip()] = v.strip().strip("\"'")
                start = i + 1
                break
    numbered = [(i + 1, line.expandtabs(4)) for i, line in enumerate(lines)][start:]
    # Definitions are resolved before inline parsing, as CommonMark requires.
    doc.blocks = _parse_blocks(numbered, doc, top=True)
    _resolve_inlines(doc.blocks, doc)
    for label in doc.footnote_order:
        _resolve_inlines(doc.footnotes[label], doc)
    doc.warnings.sort(key=lambda m: int(m.split(":")[0].split()[1]))
    return doc


# --- blocks ------------------------------------------------------------------


def _parse_blocks(lines: list[tuple[int, str]], doc: Document, top: bool = False) -> list[dict]:
    blocks: list[dict] = []
    para: list[tuple[int, str]] = []
    i = 0

    def flush():
        if para:
            blocks.append({"t": "paragraph", "raw": list(para)})
            para.clear()

    while i < len(lines):
        no, line = lines[i]
        if not line.strip():
            flush()
            i += 1
            continue

        m = _FENCE.match(line)
        if m:
            flush()
            fence, info = m.group(1), m.group(2).strip()
            if fence[0] == "`" and "`" in info:
                raise Unsupported(no, "a backtick fence's info string may not contain backticks")
            body = []
            i += 1
            while i < len(lines):
                closing = _FENCE.match(lines[i][1])
                if closing and closing.group(1)[0] == fence[0] and len(closing.group(1)) >= len(fence) and not closing.group(2):
                    break
                body.append(lines[i][1])
                i += 1
            else:
                raise Unsupported(no, "code fence is never closed")
            i += 1
            blocks.append({"t": "code", "lines": body, "info": info, "math": False})
            continue

        m = _MATH_FENCE.match(line)
        if m:
            flush()
            body = [m.group(1)] if m.group(1) else []
            i += 1
            while i < len(lines) and lines[i][1].strip() != "$$":
                body.append(lines[i][1])
                i += 1
            if i >= len(lines):
                raise Unsupported(no, "display math ($$) is never closed")
            i += 1
            doc.warnings.append(f"line {no}: display math kept as literal LaTeX; typeset math is not supported in v0.1")
            blocks.append({"t": "code", "lines": body, "info": "math", "math": True})
            continue

        if _HR.match(line) and not (para and line.lstrip().startswith("-") and _SETEXT.match(line)):
            flush()
            blocks.append({"t": "break"})
            i += 1
            continue

        m = _ATX.match(line)
        if m:
            flush()
            blocks.append({"t": "heading", "level": len(m.group(1)), "raw": [(no, (m.group(2) or "").strip())]})
            i += 1
            continue

        if para and _SETEXT.match(line):
            level = 1 if line.strip()[0] == "=" else 2
            blocks.append({"t": "heading", "level": level, "raw": list(para)})
            para.clear()
            i += 1
            continue

        m = _HTML_BLOCK.match(line)
        if line.lstrip().startswith("<!--"):
            flush()
            while i < len(lines) and "-->" not in lines[i][1]:
                i += 1
            if i >= len(lines):
                raise Unsupported(no, "HTML comment is never closed")
            i += 1
            continue
        if m and m.group(2).lower() not in ALLOWED_TAGS and not _AUTOLINK.match(line.lstrip()):
            raise Unsupported(no, f"HTML <{m.group(2)}> is not supported; only <br>, <sup>, <sub>, <u>, <kbd> and comments are")

        m = _FOOTNOTE_DEF.match(line)
        if m and top:
            flush()
            label, first = m.group(1), m.group(2)
            body = [(no, first)]
            i += 1
            while i < len(lines):
                n2, l2 = lines[i]
                if l2.startswith("    "):
                    body.append((n2, l2[4:]))
                elif l2.strip() and not _starts_block(l2) and body[-1][1].strip():
                    body.append((n2, l2))  # lazy continuation of the paragraph
                elif not l2.strip():
                    body.append((n2, ""))
                    if i + 1 < len(lines) and not lines[i + 1][1].startswith("    "):
                        break
                else:
                    break
                i += 1
            if label in doc.footnotes:
                raise Unsupported(no, f"footnote [^{label}] is defined twice")
            doc.footnotes[label] = _parse_blocks(body, doc)
            doc.footnote_order.append(label)
            continue

        m = _LINK_DEF.match(line)
        if m and not para:
            doc.link_defs.setdefault(m.group(1).strip().casefold(), m.group(2).strip("<>"))
            i += 1
            continue

        m = _QUOTE.match(line)
        if m:
            flush()
            body = []
            while i < len(lines):
                n2, l2 = lines[i]
                q = _QUOTE.match(l2)
                if q:
                    inner = q.group(1)
                    body.append((n2, inner[1:] if inner.startswith(" ") else inner))
                elif l2.strip() and body and body[-1][1].strip() and not _starts_block(l2):
                    body.append((n2, l2))  # lazy continuation
                else:
                    break
                i += 1
            blocks.append({"t": "quote", "blocks": _parse_blocks(body, doc)})
            continue

        m = _ITEM.match(line)
        if m:
            flush()
            ordered = m.group(2)[0].isdigit()
            marker_char = m.group(2)[-1] if ordered else m.group(2)
            start = int(m.group(2)[:-1]) if ordered else 1
            items = []
            while i < len(lines):
                n2, l2 = lines[i]
                im = _ITEM.match(l2)
                if not im:
                    break
                o2 = im.group(2)[0].isdigit()
                if o2 != ordered or (o2 and im.group(2)[-1] != marker_char) or (not o2 and im.group(2) != marker_char):
                    break
                indent = len(im.group(1)) + len(im.group(2)) + max(len(im.group(3)), 1)
                first = l2[im.end():]
                body = [(n2, first)]
                i += 1
                while i < len(lines):
                    n3, l3 = lines[i]
                    if not l3.strip():
                        body.append((n3, ""))
                    elif len(l3) - len(l3.lstrip(" ")) >= indent:
                        body.append((n3, l3[indent:]))
                    elif body[-1][1].strip() and not _starts_block(l3) and not _ITEM.match(l3):
                        body.append((n3, l3.lstrip(" ")))  # lazy continuation
                    else:
                        break
                    i += 1
                while body and not body[-1][1].strip():
                    body.pop()
                item_blocks = _parse_blocks(body, doc)
                if not ordered and item_blocks and item_blocks[0]["t"] == "paragraph":
                    raw0 = item_blocks[0]["raw"]
                    tm = _TASK.match(raw0[0][1])
                    if tm:
                        raw0[0] = (raw0[0][0], raw0[0][1][tm.end():])
                        item_blocks[0]["task"] = tm.group(1) != " "
                items.append(item_blocks)
                # a blank line between items is allowed; two blank lines end the list
                if i < len(lines) and not lines[i][1].strip():
                    j = i
                    while j < len(lines) and not lines[j][1].strip():
                        j += 1
                    if j < len(lines) and _ITEM.match(lines[j][1]) and j - i == 1:
                        i = j
            blocks.append({"t": "list", "ordered": ordered, "start": start, "items": items})
            continue

        if "|" in line and i + 1 < len(lines) and _TABLE_DELIM.match(lines[i + 1][1]) and not para:
            header = _split_row(line)
            aligns = []
            for cell in _split_row(lines[i + 1][1]):
                c = cell.strip()
                aligns.append("center" if c.startswith(":") and c.endswith(":") else "right" if c.endswith(":") else "left" if c.startswith(":") else None)
            if len(aligns) != len(header):
                raise Unsupported(no + 1, f"table delimiter row has {len(aligns)} cells; header has {len(header)}")
            rows = [[(no, c) for c in header]]
            i += 2
            while i < len(lines) and lines[i][1].strip() and "|" in lines[i][1] and not _starts_block(lines[i][1]):
                cells = _split_row(lines[i][1])
                if len(cells) > len(header):
                    raise Unsupported(lines[i][0], f"table row has {len(cells)} cells; header has {len(header)} — nothing may be dropped")
                cells += [""] * (len(header) - len(cells))
                rows.append([(lines[i][0], c) for c in cells])
                i += 1
            blocks.append({"t": "table", "aligns": aligns, "raw_rows": rows})
            continue

        if line.startswith("    ") and not para:
            flush()
            body = []
            while i < len(lines) and (lines[i][1].startswith("    ") or not lines[i][1].strip()):
                body.append(lines[i][1][4:])
                i += 1
            while body and not body[-1].strip():
                body.pop()
            blocks.append({"t": "code", "lines": body, "info": "", "math": False})
            continue

        para.append((no, line))
        i += 1

    flush()
    return blocks


def _starts_block(line: str) -> bool:
    return bool(_FENCE.match(line) or _ATX.match(line) or _HR.match(line) or _QUOTE.match(line)
                or _FOOTNOTE_DEF.match(line) or _MATH_FENCE.match(line) or line.lstrip().startswith("<!--"))


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells, cur, i = [], [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur.append("|")
            i += 2
        elif s[i] == "|":
            cells.append("".join(cur).strip())
            cur = []
            i += 1
        else:
            cur.append(s[i])
            i += 1
    cells.append("".join(cur).strip())
    return cells


# --- inlines -----------------------------------------------------------------


def _resolve_inlines(blocks: list[dict], doc: Document) -> None:
    for b in blocks:
        if b["t"] in ("paragraph", "heading"):
            b["inlines"] = parse_inlines(b.pop("raw"), doc)
            if b.get("task") is not None:
                b["inlines"].insert(0, {"t": "task", "checked": b.pop("task")})
        elif b["t"] == "quote":
            _resolve_inlines(b["blocks"], doc)
        elif b["t"] == "list":
            for item in b["items"]:
                _resolve_inlines(item, doc)
        elif b["t"] == "table":
            b["rows"] = [[parse_inlines([cell], doc) for cell in row] for row in b.pop("raw_rows")]


def _joined(raw: list[tuple[int, str]]) -> tuple[str, list[int]]:
    """Lines of one paragraph as one string; a line map for error messages.

    A soft line break between two Thai characters becomes nothing — Thai has no
    word-separating space, so the author's line wrap must not add one (ADR 0005
    transformation 1). Any other soft break is one space, as CommonMark renders
    it. A hard break (two trailing spaces or a backslash) is kept as a marker.
    """
    out, linemap = [], []
    for k, (no, line) in enumerate(raw):
        s = line.strip() if k else line.lstrip().rstrip()
        if k < len(raw) - 1:
            if s.endswith("\\") and not s.endswith("\\\\"):
                s = s[:-1] + "\x00"
            elif line.endswith("  "):
                s = s + "\x00"
        if out and not out[-1].endswith("\x00"):
            prev, nxt = out[-1][-1:] if out[-1] else "", s[:1]
            if not (prev and nxt and is_thai(prev) and is_thai(nxt)):
                out.append(" ")
                linemap.append(no)
        out.append(s)
        linemap.append(no)
    return "".join(out), linemap


_CODE_SPAN = re.compile(r"(`+)")
_AUTOLINK = re.compile(r"<((?:[A-Za-z][A-Za-z0-9+.-]{1,31}:[^<>\s]*)|(?:[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+))>")
_HTML_TAG = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9-]*)(?:\s[^<>]*?)?/?>")
_ENTITY = re.compile(r"&(?:#[0-9]{1,7}|#[xX][0-9A-Fa-f]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});")
_BARE_URL = re.compile(r"(?:https?://|www\.)[^\s<]+")
_FOOTNOTE_REF = re.compile(r"\[\^([^\]\s]+)\]")
_PUNCT = set("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")


def _is_punct(ch: str) -> bool:
    return ch in _PUNCT or unicodedata.category(ch).startswith("P")


def _is_space(ch: str) -> bool:
    return ch == "" or ch.isspace()


def parse_inlines(raw: list[tuple[int, str]], doc: Document) -> list[dict]:
    text, linemap = _joined(raw)
    first_line = raw[0][0] if raw else 0

    def line_at(pos: int) -> int:
        return linemap[min(pos, len(linemap) - 1)] if linemap else first_line

    nodes: list = []  # text pieces, delimiter runs, and finished inline nodes
    i, n = 0, len(text)
    buf: list[str] = []

    def emit_text():
        if buf:
            nodes.append({"t": "text", "s": "".join(buf)})
            buf.clear()

    while i < n:
        ch = text[i]
        if ch == "\\" and i + 1 < n and text[i + 1] in _PUNCT:
            buf.append(text[i + 1])
            i += 2
            continue
        if ch == "\x00":
            emit_text()
            nodes.append({"t": "hardbreak"})
            i += 1
            continue
        if ch == "`":
            m = _CODE_SPAN.match(text, i)
            ticks = m.group(1)
            end = text.find(ticks, i + len(ticks))
            while end != -1 and end + len(ticks) < n and text[end + len(ticks)] == "`":
                end = text.find(ticks, end + len(ticks) + 1)
            if end == -1:
                buf.append(ticks)
                i += len(ticks)
                continue
            code = text[i + len(ticks):end].replace("\x00", " ")
            if len(code) > 2 and code[0] == " " and code[-1] == " " and code.strip():
                code = code[1:-1]
            emit_text()
            nodes.append({"t": "text", "s": code, "code": True})
            i = end + len(ticks)
            continue
        if ch == "$":
            if text.startswith("$$", i):
                end = text.find("$$", i + 2)
            else:
                end = -1
                if i + 1 < n and not text[i + 1].isspace():
                    j = text.find("$", i + 1)
                    while j != -1 and (text[j - 1].isspace() or (j + 1 < n and text[j + 1].isdigit())):
                        j = text.find("$", j + 1)
                    end = j
            if end != -1 and end > i + 1:
                emit_text()
                width = 2 if text.startswith("$$", i) else 1
                nodes.append({"t": "text", "s": text[i + width:end], "code": True})
                doc.warnings.append(f"line {line_at(i)}: inline math kept as literal LaTeX; typeset math is not supported in v0.1")
                i = end + width
                continue
            buf.append("$")
            i += 1
            continue
        if ch == "<":
            if text.startswith("<!--", i):
                end = text.find("-->", i + 4)
                if end == -1:
                    raise Unsupported(line_at(i), "HTML comment is never closed")
                emit_text()
                i = end + 3
                continue
            m = _AUTOLINK.match(text, i)
            if m:
                emit_text()
                target = m.group(1)
                url = target if ":" in target.split("@")[0] else "mailto:" + target
                nodes.append({"t": "text", "s": target, "link": url})
                i = m.end()
                continue
            m = _HTML_TAG.match(text, i)
            if m:
                tag = m.group(2).lower()
                if tag not in ALLOWED_TAGS:
                    raise Unsupported(line_at(i), f"HTML <{m.group(2)}> is not supported; only <br>, <sup>, <sub>, <u>, <kbd> and comments are")
                emit_text()
                if tag == "br":
                    nodes.append({"t": "hardbreak"})
                else:
                    nodes.append({"t": "tag", "name": tag, "close": bool(m.group(1))})
                i = m.end()
                continue
            buf.append("<")
            i += 1
            continue
        if ch == "&":
            m = _ENTITY.match(text, i)
            if m:
                decoded = html.unescape(m.group(0))
                if decoded != m.group(0):
                    buf.append(decoded)
                    i = m.end()
                    continue
            buf.append("&")
            i += 1
            continue
        if ch == "!" and text.startswith("![", i):
            end = _link_end(text, i + 1, doc)
            if end:
                label_end, target, _title = end
                alt = _plain(parse_inlines([(line_at(i), text[i + 2:label_end])], doc))
                emit_text()
                nodes.append({"t": "image", "src": target, "alt": alt})
                i = _link_end_pos
                continue
        if ch == "[":
            m = _FOOTNOTE_REF.match(text, i)
            if m:
                if m.group(1) not in doc.footnotes:
                    raise Unsupported(line_at(i), f"footnote [^{m.group(1)}] is referenced but never defined")
                emit_text()
                nodes.append({"t": "footnote_ref", "label": m.group(1)})
                i = m.end()
                continue
            end = _link_end(text, i, doc)
            if end:
                label_end, target, _title = end
                emit_text()
                inner = parse_inlines([(line_at(i), text[i + 1:label_end])], doc)
                for node in inner:
                    if node["t"] == "text":
                        node["link"] = target
                nodes.extend(inner)
                i = _link_end_pos
                continue
        if ch in "*_~":
            j = i
            while j < n and text[j] == ch:
                j += 1
            run = text[i:j]
            before = text[i - 1] if i else ""
            after = text[j] if j < n else ""
            left = not _is_space(after) and (not _is_punct(after) or _is_space(before) or _is_punct(before))
            right = not _is_space(before) and (not _is_punct(before) or _is_space(after) or _is_punct(after))
            if ch == "_":
                can_open = left and (not right or _is_punct(before))
                can_close = right and (not left or _is_punct(after))
            else:
                can_open, can_close = left, right
            if ch == "~" and len(run) > 2:
                can_open = can_close = False
            emit_text()
            nodes.append({"t": "delim", "ch": ch, "n": len(run), "open": can_open, "close": can_close, "orig": len(run)})
            i = j
            continue
        m = _BARE_URL.match(text, i) if ch in "hw" and (i == 0 or not text[i - 1].isalnum()) else None
        if m:
            url = m.group(0).rstrip("?!.,:*_~")
            while url.endswith(")") and url.count("(") < url.count(")"):
                url = url[:-1]
            emit_text()
            nodes.append({"t": "text", "s": url, "link": url if url.startswith("http") else "http://" + url})
            i += len(url)
            continue
        buf.append(ch)
        i += 1
    emit_text()
    return _process_emphasis(nodes)


_link_end_pos = 0


def _link_end(text: str, start: int, doc: Document | None = None):
    """From `[` at `start`: (label_end, target, title) and the end position, or None."""
    global _link_end_pos
    depth, j, n = 0, start, len(text)
    while j < n:
        c = text[j]
        if c == "\\":
            j += 2
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                break
        j += 1
    if j >= n:
        return None
    label_end = j
    label = text[start + 1:label_end]
    k = j + 1
    if k < n and text[k] == "(":
        m = re.compile(r"""\(\s*(<[^<>\n]*>|[^\s()]*(?:\([^\s()]*\)[^\s()]*)*)(?:\s+("[^"]*"|'[^']*'|\([^)]*\)))?\s*\)""").match(text, k)
        if m:
            _link_end_pos = m.end()
            return label_end, m.group(1).strip("<>"), m.group(2)
    if doc is not None:
        ref = None
        if k < n and text[k] == "[":
            close = text.find("]", k)
            if close != -1:
                ref = text[k + 1:close] or label
                end_pos = close + 1
        if ref is None:
            ref, end_pos = label, label_end + 1
        target = doc.link_defs.get(ref.strip().casefold())
        if target is not None:
            _link_end_pos = end_pos
            return label_end, target, None
    return None


def _process_emphasis(nodes: list[dict]) -> list[dict]:
    """CommonMark's process-emphasis algorithm over the delimiter runs, then
    flatten to text nodes carrying flags. Unmatched delimiters become text."""
    out: list[dict] = []
    stack: list[int] = []  # indexes into `out` of open delimiters
    for node in nodes:
        if node["t"] != "delim":
            out.append(node)
            continue
        if node["close"]:
            while node["n"] > 0 and stack:
                # find the nearest opener of the same character
                oi = next((s for s in reversed(stack) if out[s]["ch"] == node["ch"] and out[s]["open"]), None)
                if oi is None:
                    break
                opener = out[oi]
                if node["ch"] != "~" and (opener["open"] and opener["close"] or node["open"]) and (opener["orig"] + node["orig"]) % 3 == 0 and not (opener["orig"] % 3 == 0 and node["orig"] % 3 == 0):
                    stack.remove(oi)
                    continue
                use = 2 if opener["n"] >= 2 and node["n"] >= 2 else 1
                if node["ch"] == "~":
                    if opener["n"] != node["n"]:
                        stack.remove(oi)
                        continue
                    use = node["n"]
                flag = "strike" if node["ch"] == "~" else ("b" if use == 2 else "i")
                for k in range(oi + 1, len(out)):
                    if out[k]["t"] == "text":
                        out[k][flag] = True
                    elif out[k]["t"] == "delim":
                        out[k]["t"] = "text"
                        out[k]["s"] = out[k]["ch"] * out[k]["n"]
                        out[k][flag] = True
                        if k in stack:
                            stack.remove(k)
                opener["n"] -= use
                node["n"] -= use
                if opener["n"] == 0:
                    out.pop(oi)
                    stack.remove(oi)
            if node["n"] > 0:
                out.append(node)
                if node["open"]:
                    stack.append(len(out) - 1)
        else:
            out.append(node)
            if node["open"]:
                stack.append(len(out) - 1)
    result = []
    for node in out:
        if node["t"] == "delim":
            node = {"t": "text", "s": node["ch"] * node["n"]}
        if node["t"] == "text":
            node = {"t": "text", "s": node["s"], **{f: bool(node.get(f)) for f in FLAGS}, "link": node.get("link")}
        result.append(node)
    return _apply_tags(_merge(result))


def _apply_tags(nodes: list[dict]) -> list[dict]:
    state = {"sup": False, "sub": False, "u": False, "kbd": False}
    out = []
    for node in nodes:
        if node["t"] == "tag":
            state[node["name"]] = not node["close"]
            continue
        if node["t"] == "text":
            node = dict(node)
            node["sup"] = node["sup"] or state["sup"]
            node["sub"] = node["sub"] or state["sub"]
            node["u"] = node["u"] or state["u"]
            node["code"] = node["code"] or state["kbd"]
        out.append(node)
    return _merge(out)


def _merge(nodes: list[dict]) -> list[dict]:
    """Adjacent text with the same formatting is one node — cause 4 (ADR 0004)."""
    out: list[dict] = []
    for node in nodes:
        if node["t"] == "text" and not node["s"]:
            continue
        prev = out[-1] if out else None
        if (
            node["t"] == "text" and prev is not None and prev["t"] == "text"
            and all(prev.get(f) == node.get(f) for f in FLAGS) and prev.get("link") == node.get("link")
        ):
            prev["s"] += node["s"]
        else:
            out.append(dict(node))
    return out


def _plain(inlines: list[dict]) -> str:
    return "".join(n["s"] for n in inlines if n["t"] == "text")


def plain_text(blocks: list[dict]) -> list[str]:
    """Every paragraph's text, in document order — what the .docx must carry
    character for character (ADR 0005). Hard breaks are newlines; task markers
    are ☐/☑; images and footnote marks contribute nothing."""
    out: list[str] = []
    for b in blocks:
        t = b["t"]
        if t in ("paragraph", "heading"):
            out.append(_inline_text(b["inlines"]))
        elif t == "code":
            out.extend(b["lines"])
        elif t == "quote":
            out.extend(plain_text(b["blocks"]))
        elif t == "list":
            for item in b["items"]:
                out.extend(plain_text(item))
        elif t == "table":
            for row in b["rows"]:
                for cell in row:
                    out.append(_inline_text(cell))
    return out


def _inline_text(inlines: list[dict]) -> str:
    parts = []
    for n in inlines:
        if n["t"] == "text":
            parts.append(n["s"])
        elif n["t"] == "hardbreak":
            parts.append("\n")
        elif n["t"] == "task":
            parts.append("☑ " if n["checked"] else "☐ ")
    return "".join(parts)
