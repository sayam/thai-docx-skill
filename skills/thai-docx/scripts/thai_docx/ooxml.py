# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""What the checker and the builder both know about WordprocessingML.

The data lives once, in `assets/ooxml.json`, and the JavaScript implementation
embeds the same file (ADR 0008). Element orders are the schema's sequences
(ECMA-376 Part 1, CT_RPr / CT_PPr / CT_Settings): Word ignores a property that
stands in the wrong place without any error, so order is checked, not assumed.
"""

from __future__ import annotations

import json
import pathlib

_DATA = json.loads(
    (pathlib.Path(__file__).resolve().parent.parent.parent / "assets" / "ooxml.json").read_text(encoding="utf-8")
)

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

RPR_ORDER: list[str] = _DATA["rpr_order"]
PPR_ORDER: list[str] = _DATA["ppr_order"]
SETTINGS_ORDER: list[str] = _DATA["settings_order"]
# Invisible characters the builder never adds and the checker always reports, by name; and
# every other format character (Unicode category Cf) with them — the soft hyphen, the marks and
# overrides of direction, the tag characters — from one list both implementations read, so
# neither asks its own runtime's Unicode tables, which differ in version (ADR 0008).
INVISIBLE: dict[str, str] = _DATA["invisible"]
FORMAT = frozenset(chr(cp) for first, last in _DATA["format"] for cp in range(first, last + 1))


def noncharacter(cp: int) -> bool:
    """U+FDD0 to U+FDEF, and the last two code points of every plane."""
    return 0xFDD0 <= cp <= 0xFDEF or cp & 0xFFFE == 0xFFFE


def unseen(ch: str) -> str | None:
    """How a character a reader cannot see is named in a message, or None."""
    if ch in INVISIBLE:
        return INVISIBLE[ch]
    if ch in FORMAT:
        return "U+%04X, a format character" % ord(ch)
    if noncharacter(ord(ch)):
        return "U+%04X, a noncharacter" % ord(ch)
    return None


# Fonts known to carry Thai glyphs, lower-cased. A font outside this list is a
# warning, never a failure (ADR 0029): the list is what the maintainer knows.
THAI_FONTS = frozenset(_DATA["thai_fonts"])


def w(tag: str) -> str:
    return "{%s}%s" % (W, tag)


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def is_thai(ch: str) -> bool:
    return "฀" <= ch <= "๿"
