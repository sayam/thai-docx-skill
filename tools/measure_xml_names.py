"""Measure which characters expat — the XML parser behind the Python checker —
accepts in names, and write them to skills/thai-docx/assets/xml-names.json for
the JavaScript XML reader (ADR 0008, 0017).

    python3 tools/measure_xml_names.py           # write the asset
    python3 tools/measure_xml_names.py --check   # exit 1 if the asset differs

Expat classifies name characters by its own tables, which are not the ranges of
XML 1.0 fifth edition (U+0E2F, for one); the reader in js/20-xml.js must agree
with it character for character, so the table is measured, not transcribed.

Role: generator (writes the asset) and decider (`--check`).
"""

from __future__ import annotations

import json
import pathlib
import sys
from xml.etree import ElementTree as ET

ASSET = pathlib.Path(__file__).resolve().parent.parent / "skills" / "thai-docx" / "assets" / "xml-names.json"


def _parses(text: str) -> bool:
    try:
        ET.fromstring(text.encode("utf-8"))
    except ET.ParseError:
        return False
    return True


def _ranges(code_points: list[int]) -> list[list[int]]:
    out: list[list[int]] = []
    for cp in code_points:
        if out and out[-1][1] == cp - 1:
            out[-1][1] = cp
        else:
            out.append([cp, cp])
    return out


def measure() -> dict:
    start, char = [], []
    # expat never takes a character above U+FFFF into a name, so the BMP is the table
    for cp in range(0x10000):
        if 0xD800 <= cp <= 0xDFFF or cp in (0x09, 0x0A, 0x0D, 0x20):  # whitespace ends a name
            continue
        c = chr(cp)
        if _parses("<" + c + "/>"):
            start.append(cp)
        if _parses("<a" + c + "/>"):
            char.append(cp)
    return {"start": _ranges(start), "char": _ranges(char)}


def main(argv: list[str]) -> int:
    text = json.dumps(measure(), separators=(",", ":")) + "\n"
    if argv == ["--check"]:
        if not ASSET.exists() or ASSET.read_text(encoding="utf-8") != text:
            print("skills/thai-docx/assets/xml-names.json differs from this expat: run python3 tools/measure_xml_names.py")
            return 1
        print("xml-names.json matches this expat")
        return 0
    ASSET.write_text(text, encoding="utf-8")
    print("wrote " + str(ASSET.name))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
