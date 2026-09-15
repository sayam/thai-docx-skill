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
# Invisible characters the builder never adds and the checker always reports.
INVISIBLE: dict[str, str] = _DATA["invisible"]
# Fonts known to carry Thai glyphs, lower-cased. A font outside this list is a
# warning, never a failure (ADR 0009): the list is what the maintainer knows.
THAI_FONTS = frozenset(_DATA["thai_fonts"])


def w(tag: str) -> str:
    return "{%s}%s" % (W, tag)


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def is_thai(ch: str) -> bool:
    return "฀" <= ch <= "๿"
