# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Repair a .docx this skill did not write: the attributes that break Thai, never the text
(ADR 0037).

    thai_docx repair IN.docx OUT.docx

This version repairs two findings, and reports every other one:

    1  compatibilityMode is not exactly one 15 — set it, or drop the ones that are not 15
    3  <w:noProof/> switches Thai proofing, and Thai line breaking, off — remove it

Everything else in the package comes through byte for byte, including the compressed bytes of
every part this did not rewrite (`package.repack`). The text of the output must equal the text
of the input, character for character, or nothing is written.
"""

from __future__ import annotations

import hashlib
import io
import json
import pathlib
import re

from . import check as check_mod
from . import ooxml
from . import package
from . import settings as st
from .ooxml import is_thai
from .fidelity import docx_text
from .writer import script_runs

USAGE = ('usage: thai_docx repair IN.docx OUT.docx [--font "TH Sarabun New"] [--thai-language]'
         " [--force-cs-whole-doc]")

# A part is edited as bytes, not re-serialised from a tree: a tree would rewrite prefixes,
# attribute order and empty-element spelling across the whole part, and ADR 0037 allows only
# the attributes named. Both elements below are empty ones, so the shapes are few.
NO_PROOF = re.compile(rb"<w:noProof(?:\s[^>]*?)?/>|<w:noProof(?:\s[^>]*?)?>\s*</w:noProof>")
COMPAT_SETTING = re.compile(rb"<w:compatSetting\s[^>]*?/>")
ATTR = re.compile(rb'([\w:]+)\s*=\s*"([^"]*)"')
MODE, URI = b"compatibilityMode", check_mod.COMPAT_URI.encode()


def _attrs(tag: bytes) -> dict[bytes, bytes]:
    return dict(ATTR.findall(tag))


def remove_no_proof(xml: bytes) -> tuple[bytes, int]:
    """Every <w:noProof/> gone. Removing it leaves the default, which is proofing on."""
    out, count = NO_PROOF.subn(b"", xml)
    return out, count


def one_compatibility_mode(xml: bytes) -> tuple[bytes, int]:
    """Exactly one compatibilityMode, declared 15: the first is set to 15 and any other is
    dropped. A part that declares none is left alone — writing one means placing an element
    in schema order, which this version does not do."""
    found = [m for m in COMPAT_SETTING.finditer(xml)
             if _attrs(m.group(0)).get(b"w:name") == MODE and _attrs(m.group(0)).get(b"w:uri") == URI]
    if not found:
        return xml, 0
    changed, out, last = 0, bytearray(), 0
    for i, m in enumerate(found):
        out += xml[last:m.start()]
        if i == 0:
            tag = m.group(0)
            if _attrs(tag).get(b"w:val") != b"15":
                tag = re.sub(rb'(w:val\s*=\s*)"[^"]*"', rb'\g<1>"15"', tag)
                if tag == m.group(0):  # no w:val at all: the default is not 15, so say it
                    tag = tag[:-2].rstrip() + b' w:val="15"/>'
                changed += 1
            out += tag
        else:
            changed += 1  # a second declaration is one more thing that was wrong
        last = m.end()
    out += xml[last:]
    return bytes(out), changed


# --- the marks a Thai run needs, and the twins a Latin property needs ------------------

TAG = re.compile(rb"<(/?)(w:[\w.-]+)((?:[^<>\"']|\"[^\"]*\"|'[^']*')*?)(/?)>")
RUN_START = re.compile(rb"<w:r(?:\s[^<>]*?)?>")
# the one run shape a split may touch: properties, if any, then one w:t and nothing else
SIMPLE_INNER = re.compile(rb"\A(<w:rPr(?:\s[^<>]*?)?>.*?</w:rPr>)?(<w:t(?:\s[^<>]*?)?>)(.*)</w:t>\Z", re.S)
LATIN_FONT = (b"w:ascii", b"w:hAnsi", b"w:asciiTheme", b"w:hAnsiTheme")


def _end_of(xml: bytes, after_start: int, name: bytes) -> tuple[int, int]:
    """Where the element that opened just before `after_start` ends: (inner end, element end).
    Depth is counted, because a run can hold a drawing that holds runs of its own."""
    depth = 1
    for m in TAG.finditer(xml, after_start):
        if m.group(2) != name or m.group(4):
            continue
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return m.start(), m.end()
    raise ValueError("<" + name.decode() + "> is never closed")  # the checker parsed it, so this cannot happen


def _children(inner: bytes) -> list[tuple[bytes, bytes]]:
    """An element's own children, in order: (name, the raw bytes of the whole child)."""
    out, pos = [], 0
    while True:
        m = TAG.search(inner, pos)
        if m is None:
            return out
        if m.group(4):  # <w:x/>
            out.append((m.group(2), m.group(0)))
            pos = m.end()
            continue
        inner_end, element_end = _end_of(inner, m.end(), m.group(2))
        out.append((m.group(2), inner[m.start():element_end]))
        pos = element_end


def _insert(children: list[tuple[bytes, bytes]], name: bytes, element: bytes) -> list[tuple[bytes, bytes]]:
    """`element` among `children`, at the place the schema puts it (ADR 0004's order table).
    Nothing already there moves: repairing the order is a different finding."""
    rank = ooxml.RPR_ORDER.index(name.decode()[2:])
    for i, (there, _raw) in enumerate(children):
        local = there.decode()[2:]
        if local in ooxml.RPR_ORDER and ooxml.RPR_ORDER.index(local) > rank:
            return children[:i] + [(name, element)] + children[i:]
    return children + [(name, element)]


def _drop(children: list[tuple[bytes, bytes]], name: bytes) -> list[tuple[bytes, bytes]]:
    """`children` without `name`. Removing the marker is how a run says it is not complex
    script: the element has no "off" spelling that Word writes (ADR 0039)."""
    return [(there, raw) for there, raw in children if there != name]


def _unescape(text: bytes) -> bytes:
    return (text.replace(b"&lt;", b"<").replace(b"&gt;", b">").replace(b"&quot;", b'"')
                .replace(b"&apos;", b"'").replace(b"&amp;", b"&"))


def _escape(text: bytes) -> bytes:
    return text.replace(b"&", b"&amp;").replace(b"<", b"&lt;").replace(b">", b"&gt;")


def fix_rpr(inner: bytes, font: bytes, mark: bool | None,
            thai_language: bool = False) -> tuple[bytes, int, int, int, int]:
    """One w:rPr put right: its new inner XML, then code 2 repairs, code 5 repairs, language
    marks, and markers taken off a run whose text is not complex script.

    `mark` True writes the complex-script marker, False takes it away, None leaves it as it is —
    which is what a style gets when the caller asked for every run to be marked instead.
    """
    children = _children(inner)
    by_name = {name: raw for name, raw in children}
    two = five = marked = unmarked = 0

    for latin, twin in ((b"w:sz", b"w:szCs"), (b"w:b", b"w:bCs"), (b"w:i", b"w:iCs")):
        if latin in by_name and twin not in by_name:
            attrs = re.search(rb'(\sw:val\s*=\s*"[^"]*")', by_name[latin])
            children = _insert(children, twin, b"<" + twin + (attrs.group(1) if attrs else b"") + b"/>")
            by_name[twin] = b""
            five += 1

    fonts = by_name.get(b"w:rFonts")
    if fonts is not None:
        has_latin = any(re.search(a + rb'\s*=\s*"', fonts) for a in LATIN_FONT)
        has_cs = re.search(rb'w:cs(?:theme)?\s*=\s*"', fonts)
        if has_latin and not has_cs:
            new = fonts[:-2].rstrip() + b' w:cs="' + font + b'"/>'
            children = [(n, new if n == b"w:rFonts" else raw) for n, raw in children]
            five += 1

    if mark is False and b"w:cs" in by_name:
        children = _drop(children, b"w:cs")
        unmarked += 1  # not a finding of its own, so it is counted apart from the code 2 repairs
    if mark:
        if b"w:cs" not in by_name:
            children = _insert(children, b"w:cs", b"<w:cs/>")
            two += 1
        if thai_language:
            # the Thai complex-script language, only where the caller asked for it (ADR 0038)
            lang = by_name.get(b"w:lang")
            if lang is None:
                children = _insert(children, b"w:lang", b'<w:lang w:bidi="th-TH"/>')
                marked += 1
            elif not re.search(rb'w:bidi\s*=\s*"th-TH"', lang):
                new = (re.sub(rb'w:bidi\s*=\s*"[^"]*"', b'w:bidi="th-TH"', lang)
                       if re.search(rb'w:bidi\s*=\s*"', lang) else lang[:-2].rstrip() + b' w:bidi="th-TH"/>')
                children = [(n, new if n == b"w:lang" else raw) for n, raw in children]
                marked += 1

    return b"".join(raw for _n, raw in children), two, five, marked, unmarked


def reorder(xml: bytes, element: bytes, order: list[str]) -> tuple[bytes, int]:
    """Every `element` in the part with its children in the order the schema fixes.

    The elements the schema names are put in that order, **in the places they already
    occupy**; anything it does not name keeps its own place, because the checker skips those
    and moving them would change more than the finding asked for. A permutation is the same
    bytes in a different order, so the part's length never changes and the positions of the
    other elements hold while this walks them.
    """
    rank = {name: i for i, name in enumerate(order)}
    start = re.compile(rb"<" + element + rb"(?:\s[^<>]*?)?>")
    count = 0
    for m in reversed(list(start.finditer(xml))):   # inner elements first: they sit further on
        inner_end, _element_end = _end_of(xml, m.end(), element)
        children = _children(xml[m.end():inner_end])
        known = [(i, c) for i, c in enumerate(children) if c[0].decode()[2:] in rank]
        if len(known) < 2:
            continue
        # a stable sort, so two children of one name keep the order they were written in
        ordered = sorted(known, key=lambda pair: rank[pair[1][0].decode()[2:]])
        if [c for _i, c in known] == [c for _i, c in ordered]:
            continue
        put = list(children)
        for (slot, _was), (_at, now) in zip(known, ordered, strict=True):
            put[slot] = now
        xml = xml[:m.end()] + b"".join(raw for _n, raw in put) + xml[inner_end:]
        count += 1
    return xml, count


def _run_text(inner: bytes) -> str:
    """Everything the run's own w:t elements hold, as the text reads."""
    return _unescape(b"".join(re.findall(rb"<w:t(?:\s[^<>]*?)?>(.*?)</w:t>", inner, re.S))).decode("utf-8", "replace")


def _split_run(start: bytes, inner: bytes, font: bytes, counts: dict[str, int],
               thai_language: bool) -> bytes | None:
    """A run whose text holds both scripts, cut where the script changes (ADR 0039) — or None
    when this run is not one to cut.

    Only the plain shape is cut: run properties, if any, then one w:t and nothing else. A run
    carrying a field, a drawing, a tab or a break is left whole, and so is one whose text holds
    a numeric character reference, because re-escaping that would change the text, which repair
    may never do (ADR 0023).
    """
    m = SIMPLE_INNER.match(inner)
    if m is None or b"&#" in m.group(3):
        return None
    rpr_raw, topen, body = m.group(1), m.group(2), m.group(3)
    pieces = script_runs(_unescape(body).decode("utf-8"))
    if len(pieces) < 2:
        return None
    rpr_inner = b"" if rpr_raw is None else rpr_raw[rpr_raw.index(b">") + 1:-len(b"</w:rPr>")]
    out = bytearray()
    for complex_script, piece in pieces:
        new_body, two, five, marked, unmarked = fix_rpr(rpr_inner, font, complex_script, thai_language)
        for key, n in (("2", two), ("5", five), ("thai-language", marked), ("unmarked", unmarked)):
            counts[key] = counts.get(key, 0) + n
        head = b"<w:rPr>" + new_body + b"</w:rPr>" if new_body else b""
        out += start + head + topen + _escape(piece.encode("utf-8")) + b"</w:t></w:r>"
    counts["split"] = counts.get("split", 0) + 1
    return bytes(out)


def _fix_runs(xml: bytes, font: bytes, counts: dict[str, int], thai_language: bool = False,
              cs_all: bool = False) -> bytes:
    """Every run marked where its text is complex script, every rPr's twins filled in — nested
    runs included, and a run that holds both scripts cut where the script changes."""
    out, pos = bytearray(), 0
    for m in RUN_START.finditer(xml):
        if m.start() < pos:
            continue
        inner_end, element_end = _end_of(xml, m.end(), b"w:r")
        inner, start = xml[m.end():inner_end], xml[m.start():m.end()]
        split = None if cs_all else _split_run(start, inner, font, counts, thai_language)
        if split is not None:
            out += xml[pos:m.start()] + split
            pos = element_end
            continue
        out += xml[pos:m.end()] + _fix_run(inner, font, counts, thai_language, cs_all)
        pos = inner_end
    return bytes(out) + xml[pos:]


def _fix_run(inner: bytes, font: bytes, counts: dict[str, int], thai_language: bool = False,
             cs_all: bool = False) -> bytes:
    has_text = re.search(rb"<w:t(?:\s[^<>]*?)?>", inner) is not None
    mark = True if cs_all else (has_text and any(is_thai(ch) for ch in _run_text(inner)))
    rpr = re.match(rb"<w:rPr(?:\s[^<>]*?)?(/?)>", inner)
    rest_from = 0
    head = b""
    if rpr is not None and rpr.group(1):           # <w:rPr/>
        body, rest_from = b"", rpr.end()
    elif rpr is not None:
        body_end, element_end = _end_of(inner, rpr.end(), b"w:rPr")
        body, rest_from = inner[rpr.end():body_end], element_end
    elif mark:
        body, rest_from = b"", 0                    # a run that needs the marker and has no rPr gets one
    else:
        return _fix_runs(inner, font, counts, thai_language, cs_all)  # nothing of ours here; look deeper
    new_body, two, five, marked, unmarked = fix_rpr(body, font, mark if has_text else None, thai_language)
    counts["2"] = counts.get("2", 0) + two
    counts["5"] = counts.get("5", 0) + five
    counts["thai-language"] = counts.get("thai-language", 0) + marked
    counts["unmarked"] = counts.get("unmarked", 0) + unmarked
    if new_body:
        head = b"<w:rPr>" + new_body + b"</w:rPr>"
    elif rpr is not None:
        head = inner[:rest_from]
    return head + _fix_runs(inner[rest_from:], font, counts, thai_language, cs_all)


def fix_text_part(xml: bytes, font: bytes, thai_language: bool = False,
                  cs_all: bool = False) -> tuple[bytes, dict[str, int]]:
    counts: dict[str, int] = {}
    return _fix_runs(xml, font, counts, thai_language, cs_all), {k: v for k, v in counts.items() if v}


def fix_styles(xml: bytes, font: bytes, cs_all: bool = False) -> tuple[bytes, int, int]:
    """A style's w:rPr needs its twins; it formats no text, so no marker is written into one.

    The marker is taken *out*, though, and that is the half without which the rest does nothing:
    `w:cs` inherits down docDefaults and the styles to a run, so a run that leaves it off is
    only saying "whatever the chain says" (ADR 0039). Asked to mark every run instead, the chain
    is left exactly as it was — each run then says it for itself.
    """
    out, pos, five, unmarked = bytearray(), 0, 0, 0
    for m in re.finditer(rb"<w:rPr(?:\s[^<>]*?)?>", xml):
        if m.start() < pos:
            continue
        inner_end, _element_end = _end_of(xml, m.end(), b"w:rPr")
        new_body, _two, n, _marked, off = fix_rpr(xml[m.end():inner_end], font, None if cs_all else False)
        five += n
        unmarked += off
        out += xml[pos:m.end()] + new_body
        pos = inner_end
    return bytes(out) + xml[pos:], five, unmarked


def fix_numbering(xml: bytes, font: bytes) -> tuple[bytes, int]:
    """A bullet level drawn in Symbol has no Thai glyphs; give it the document's font."""
    out, pos, five = bytearray(), 0, 0
    for m in re.finditer(rb"<w:lvl(?:\s[^<>]*?)?>", xml):
        if m.start() < pos:
            continue
        inner_end, _element_end = _end_of(xml, m.end(), b"w:lvl")
        level = xml[m.end():inner_end]
        if re.search(rb'<w:numFmt\s[^<>]*?w:val="bullet"', level):
            fonts = re.search(rb"<w:rFonts(?:\s[^<>]*?)?/>", level)
            if fonts is not None and b'"Symbol"' in fonts.group(0):
                level = level[:fonts.start()] + fonts.group(0).replace(b'"Symbol"', b'"' + font + b'"') + level[fonts.end():]
                five += 1
        out += xml[pos:m.end()] + level
        pos = inner_end
    return bytes(out) + xml[pos:], five


def complex_script_font(parts: dict[str, bytes], asked: str | None) -> tuple[bytes, str]:
    """The font a run that names none is given, and why (ADR 0037): what the user asked for,
    else the complex-script font this document already uses most, else the skill's default."""
    if asked:
        return asked.encode("utf-8"), "the font the command was given"
    counted: dict[bytes, int] = {}
    for name, xml in parts.items():
        # the XML parts only: an image or a font holds no run properties, and reading one as
        # text is how the two implementations came apart (a picture is not valid UTF-8)
        if name.startswith("word/") and name.endswith(".xml"):
            for found in re.findall(rb'w:cs\s*=\s*"([^"]+)"', xml):
                # only a font the checker itself would accept: writing one it warns about
                # would trade a finding for a warning, which is not a repair
                if found.decode("utf-8", "replace").lower() in ooxml.THAI_FONTS:
                    counted[found] = counted.get(found, 0) + 1
    if counted:
        best = max(sorted(counted), key=lambda f: counted[f])
        return best, "the complex-script font this document uses most"
    return st.DEFAULTS["font"].encode("utf-8"), "this skill's default, as the document names none"


def repair_parts(parts: dict[str, bytes], findings: list[dict], font: str | None = None,
                 thai_language: bool = False, cs_all: bool = False) -> tuple[dict[str, bytes], dict[str, int]]:
    """The parts to write anew, and how many of each code were repaired."""
    codes = {f["code"] for f in findings}
    replace: dict[str, bytes] = {}
    repaired: dict[str, int] = {}
    if "1" in codes and "word/settings.xml" in parts:
        settings, n = one_compatibility_mode(parts["word/settings.xml"])
        if n:
            replace["word/settings.xml"] = settings
            repaired["1"] = n
    if "3" in codes:
        for name, xml in parts.items():
            if not name.startswith("word/"):
                continue
            new, n = remove_no_proof(replace.get(name, xml))
            if n:
                replace[name] = new
                repaired["3"] = repaired.get("3", 0) + n
    if "order" in codes:
        # runs first, then paragraphs: a w:pPr holds a w:rPr, and moving a whole child keeps
        # the order already put right inside it
        for name, xml in parts.items():
            if not (check_mod.TEXT_PARTS.fullmatch(name) or name in ("word/styles.xml", "word/numbering.xml", "word/settings.xml")):
                continue
            out, n = replace.get(name, xml), 0
            for element, table in ((b"w:rPr", ooxml.RPR_ORDER), (b"w:pPr", ooxml.PPR_ORDER),
                                   (b"w:settings", ooxml.SETTINGS_ORDER)):
                out, some = reorder(out, element, table)
                n += some
            if n:
                replace[name] = out
                repaired["order"] = repaired.get("order", 0) + n
    chosen = None
    # by default there is always something to look at: a run of Latin that carries the marker
    # is not a finding, so nothing in `codes` would ask for this pass, and taking it off is the
    # repair (ADR 0039). Asked to mark every run instead, this is the work it always was.
    if codes & {"2", "5"} or thai_language or not cs_all:
        cs_font, why = complex_script_font(parts, font)
        for name, xml in parts.items():
            if not check_mod.TEXT_PARTS.fullmatch(name):
                continue
            new, counts = fix_text_part(replace.get(name, xml), cs_font, thai_language, cs_all)
            if counts:
                replace[name] = new
                for code, n in counts.items():
                    repaired[code] = repaired.get(code, 0) + n
        if "word/styles.xml" in parts:
            new, n, off = fix_styles(replace.get("word/styles.xml", parts["word/styles.xml"]), cs_font, cs_all)
            if n or off:
                replace["word/styles.xml"] = new
                if n:
                    repaired["5"] = repaired.get("5", 0) + n
                if off:
                    repaired["unmarked"] = repaired.get("unmarked", 0) + off
        if "word/numbering.xml" in parts:
            new, n = fix_numbering(replace.get("word/numbering.xml", parts["word/numbering.xml"]), cs_font)
            if n:
                replace["word/numbering.xml"] = new
                repaired["5"] = repaired.get("5", 0) + n
        if any(code in repaired for code in ("2", "5")):
            chosen = {"code": "font", "message": "complex-script font written where a run named none: '"
                      + cs_font.decode("utf-8") + "' — " + why}
    return replace, repaired, chosen


def repair(in_path: str, out_path: str, font: str | None = None, thai_language: bool = False,
           cs_all: bool = False) -> dict:
    result: dict = {"ok": False, "file": out_path}
    try:
        with open(in_path, "rb") as f:
            data = f.read(package.MAX_FILE + 1)
    except OSError as exc:
        result["error"] = "cannot read " + in_path + ": " + package.os_error(exc)
        return result

    before = check_mod.check(io.BytesIO(data))
    if before.error is not None:
        result["error"] = before.error
        return result
    refused = [f for f in before.findings if f["code"] in ("package", "doctype", "size")]
    if refused:
        # the same answer `check` gives: a file it cannot read is refused, not repaired
        result["error"] = in_path + ": " + refused[0]["message"]
        return result

    ents = package.entries(data)
    parts = {e.name: package.read(data, e) for e in ents}
    replace, repaired, chosen = repair_parts(parts, before.findings, font, thai_language, cs_all)
    if not replace:
        result["repaired"] = {}
        result["remaining"] = before.findings
        result["error"] = "nothing here is a repair this version makes; the findings say what is wrong"
        return result

    out = package.repack(data, ents, replace)

    # the text is the user's (ADR 0023, 0037): a difference of one character writes nothing
    after = check_mod.check(io.BytesIO(out))
    footnotes = before.counts.get("footnotes", 0)
    was, now = docx_text(parts, footnotes), docx_text({**parts, **replace}, footnotes)
    if was != now:
        result["error"] = "the repair would have changed the document's text; nothing was written"
        return result
    still = {f["code"] for f in after.findings}
    marked = repaired.pop("thai-language", 0)
    for code in repaired:
        if code in still:
            result["error"] = "finding " + code + " is still there after the repair; nothing was written"
            return result

    try:
        pathlib.Path(out_path).write_bytes(out)
    except OSError as exc:
        result["error"] = "cannot write " + out_path + ": " + package.os_error(exc)
        return result
    warnings = ([chosen] if chosen else []) + after.warnings
    if marked:
        warnings = warnings + [{"code": "thai-language", "message":
                                'the Thai complex-script language w:bidi="th-TH" was written into '
                                + str(marked) + " run properties, as --thai-language asked"}]
    result.update(ok=True, repaired=repaired, remaining=after.findings, warnings=warnings,
                  sha256=hashlib.sha256(out).hexdigest(), bytes=len(out))
    return result


def main(argv: list[str]) -> int:
    font, thai_language, cs_all = None, False, False
    if "--thai-language" in argv:
        argv = [a for a in argv if a != "--thai-language"]
        thai_language = True
    if "--force-cs-whole-doc" in argv:
        argv = [a for a in argv if a != "--force-cs-whole-doc"]
        cs_all = True
    if len(argv) == 4 and argv[2] == "--font":
        argv, font = argv[:2], argv[3]
    if len(argv) != 2:
        print(json.dumps({"ok": False, "error": USAGE}))
        return 2
    result = repair(argv[0], argv[1], font, thai_language, cs_all)
    print(json.dumps(result, ensure_ascii=False))
    if "error" in result:
        return 2
    return 1 if result["remaining"] else 0
