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
from . import package
from .fidelity import docx_text

USAGE = "usage: thai_docx repair IN.docx OUT.docx"

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


def repair_parts(parts: dict[str, bytes], findings: list[dict]) -> tuple[dict[str, bytes], dict[str, int]]:
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
    return replace, repaired


def repair(in_path: str, out_path: str) -> dict:
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
    replace, repaired = repair_parts(parts, before.findings)
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
    result.update(ok=True, repaired=repaired, remaining=after.findings, warnings=after.warnings,
                  sha256=hashlib.sha256(out).hexdigest(), bytes=len(out))
    return result


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(json.dumps({"ok": False, "error": USAGE}))
        return 2
    result = repair(argv[0], argv[1])
    print(json.dumps(result, ensure_ascii=False))
    if "error" in result:
        return 2
    return 1 if result["remaining"] else 0
