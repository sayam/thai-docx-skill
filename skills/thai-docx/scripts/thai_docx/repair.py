# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Repair a .docx this skill did not write: the attributes that break Thai, never the text
(ADR 0032).

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
from .fidelity import docx_text

USAGE = 'usage: thai_docx repair IN.docx OUT.docx [--font "TH Sarabun New"]'

# A part is edited as bytes, not re-serialised from a tree: a tree would rewrite prefixes,
# attribute order and empty-element spelling across the whole part, and ADR 0032 allows only
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


def fix_rpr(inner: bytes, font: bytes, mark_thai: bool) -> tuple[bytes, int, int]:
    """One w:rPr put right: (its new inner XML, code 2 repairs, code 5 repairs)."""
    children = _children(inner)
    by_name = {name: raw for name, raw in children}
    two = five = 0

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

    if mark_thai:
        if b"w:cs" not in by_name:
            children = _insert(children, b"w:cs", b"<w:cs/>")
            two += 1
        lang = by_name.get(b"w:lang")
        if lang is None:
            children = _insert(children, b"w:lang", b'<w:lang w:bidi="th-TH"/>')
            two += 1
        elif not re.search(rb'w:bidi\s*=\s*"th-TH"', lang):
            new = (re.sub(rb'w:bidi\s*=\s*"[^"]*"', b'w:bidi="th-TH"', lang)
                   if re.search(rb'w:bidi\s*=\s*"', lang) else lang[:-2].rstrip() + b' w:bidi="th-TH"/>')
            children = [(n, new if n == b"w:lang" else raw) for n, raw in children]
            two += 1

    return b"".join(raw for _n, raw in children), two, five


def _fix_runs(xml: bytes, font: bytes, counts: dict[str, int]) -> bytes:
    """Every run with text marked, every rPr's twins filled in — nested runs included."""
    out, pos = bytearray(), 0
    for m in RUN_START.finditer(xml):
        if m.start() < pos:
            continue  # inside a run already put right
        inner_end, element_end = _end_of(xml, m.end(), b"w:r")
        inner = xml[m.end():inner_end]
        out += xml[pos:m.end()] + _fix_run(inner, font, counts)
        pos = inner_end
    return bytes(out) + xml[pos:]


def _fix_run(inner: bytes, font: bytes, counts: dict[str, int]) -> bytes:
    has_text = re.search(rb"<w:t(?:\s[^<>]*?)?>", inner) is not None
    rpr = re.match(rb"<w:rPr(?:\s[^<>]*?)?(/?)>", inner)
    rest_from = 0
    head = b""
    if rpr is not None and rpr.group(1):           # <w:rPr/>
        body, rest_from = b"", rpr.end()
    elif rpr is not None:
        body_end, element_end = _end_of(inner, rpr.end(), b"w:rPr")
        body, rest_from = inner[rpr.end():body_end], element_end
    elif has_text:
        body, rest_from = b"", 0                    # a run with text and no rPr gets one
    else:
        return _fix_runs(inner, font, counts)       # nothing of ours here; look deeper
    new_body, two, five = fix_rpr(body, font, has_text)
    counts["2"] = counts.get("2", 0) + two
    counts["5"] = counts.get("5", 0) + five
    if new_body:
        head = b"<w:rPr>" + new_body + b"</w:rPr>"
    elif rpr is not None:
        head = inner[:rest_from]
    return head + _fix_runs(inner[rest_from:], font, counts)


def fix_text_part(xml: bytes, font: bytes) -> tuple[bytes, dict[str, int]]:
    counts: dict[str, int] = {}
    return _fix_runs(xml, font, counts), {k: v for k, v in counts.items() if v}


def fix_styles(xml: bytes, font: bytes) -> tuple[bytes, int]:
    """A style's w:rPr needs its twins; it formats no text, so no Thai marks are added."""
    out, pos, five = bytearray(), 0, 0
    for m in re.finditer(rb"<w:rPr(?:\s[^<>]*?)?>", xml):
        if m.start() < pos:
            continue
        inner_end, _element_end = _end_of(xml, m.end(), b"w:rPr")
        new_body, _two, n = fix_rpr(xml[m.end():inner_end], font, False)
        five += n
        out += xml[pos:m.end()] + new_body
        pos = inner_end
    return bytes(out) + xml[pos:], five


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
    """The font a run that names none is given, and why (ADR 0032): what the user asked for,
    else the complex-script font this document already uses most, else the skill's default."""
    if asked:
        return asked.encode("utf-8"), "the font the command was given"
    counted: dict[bytes, int] = {}
    for name, xml in parts.items():
        if name.startswith("word/"):
            for found in re.findall(rb'w:cs\s*=\s*"([^"]+)"', xml):
                # only a font the checker itself would accept: writing one it warns about
                # would trade a finding for a warning, which is not a repair
                if found.decode("utf-8", "replace").lower() in ooxml.THAI_FONTS:
                    counted[found] = counted.get(found, 0) + 1
    if counted:
        best = max(sorted(counted), key=lambda f: counted[f])
        return best, "the complex-script font this document uses most"
    return st.DEFAULTS["font"].encode("utf-8"), "this skill's default, as the document names none"


def repair_parts(parts: dict[str, bytes], findings: list[dict], font: str | None = None) -> tuple[dict[str, bytes], dict[str, int]]:
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
    chosen = None
    if codes & {"2", "5"}:
        cs_font, why = complex_script_font(parts, font)
        for name, xml in parts.items():
            if not check_mod.TEXT_PARTS.fullmatch(name):
                continue
            new, counts = fix_text_part(replace.get(name, xml), cs_font)
            if counts:
                replace[name] = new
                for code, n in counts.items():
                    repaired[code] = repaired.get(code, 0) + n
        if "word/styles.xml" in parts:
            new, n = fix_styles(replace.get("word/styles.xml", parts["word/styles.xml"]), cs_font)
            if n:
                replace["word/styles.xml"] = new
                repaired["5"] = repaired.get("5", 0) + n
        if "word/numbering.xml" in parts:
            new, n = fix_numbering(replace.get("word/numbering.xml", parts["word/numbering.xml"]), cs_font)
            if n:
                replace["word/numbering.xml"] = new
                repaired["5"] = repaired.get("5", 0) + n
        if any(code in repaired for code in ("2", "5")):
            chosen = {"code": "font", "message": "complex-script font written where a run named none: '"
                      + cs_font.decode("utf-8") + "' — " + why}
    return replace, repaired, chosen


def repair(in_path: str, out_path: str, font: str | None = None) -> dict:
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
    replace, repaired, chosen = repair_parts(parts, before.findings, font)
    if not replace:
        result["repaired"] = {}
        result["remaining"] = before.findings
        result["error"] = "nothing here is a repair this version makes; the findings say what is wrong"
        return result

    out = package.repack(data, ents, replace)

    # the text is the user's (ADR 0023, 0032): a difference of one character writes nothing
    after = check_mod.check(io.BytesIO(out))
    footnotes = before.counts.get("footnotes", 0)
    was, now = docx_text(parts, footnotes), docx_text({**parts, **replace}, footnotes)
    if was != now:
        result["error"] = "the repair would have changed the document's text; nothing was written"
        return result
    still = {f["code"] for f in after.findings}
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
    result.update(ok=True, repaired=repaired, remaining=after.findings, warnings=warnings,
                  sha256=hashlib.sha256(out).hexdigest(), bytes=len(out))
    return result


def main(argv: list[str]) -> int:
    font = None
    if len(argv) == 4 and argv[2] == "--font":
        argv, font = argv[:2], argv[3]
    if len(argv) != 2:
        print(json.dumps({"ok": False, "error": USAGE}))
        return 2
    result = repair(argv[0], argv[1], font)
    print(json.dumps(result, ensure_ascii=False))
    if "error" in result:
        return 2
    return 1 if result["remaining"] else 0
