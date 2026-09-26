# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""The fidelity reference (ADR 0023): the text every paragraph of the package must hold,
built from the Markdown, and the text the package does hold, read back from its XML.
"""

from __future__ import annotations

import unicodedata
from xml.etree import ElementTree as ET

from . import markdown as md
from .layout import LIST_FIELDS, caption_text, layout, list_entries
from .ooxml import w
from .settings import DEFAULTS


SPACE = "{http://www.w3.org/XML/1998/namespace}space"


def paragraphs(root, out: list[str]) -> None:
    """Each paragraph's text under `root`, appended to `out`. A tab is text, except the one that
    separates a footnote's mark from its body. A w:t that does not say xml:space="preserve"
    loses the space at its ends, as an application reading it may drop it and Word does — so a
    space a writer left there without the attribute is not counted as text it kept."""
    for p in root.iter(w("p")):
        pieces, seen, after_mark = [], False, False
        for el in p.iter():
            tag = el.tag
            if tag == w("footnoteRef"):
                after_mark = True
                seen = True
            elif tag == w("t"):
                text = el.text or ""
                pieces.append(text if el.get(SPACE) == "preserve" else text.strip(" \t\n\r"))
                seen = True
                after_mark = False
            elif tag == w("tab"):
                if not after_mark:
                    pieces.append("\t")
                after_mark = False
                seen = True
            elif tag == w("br"):
                pieces.append("\n")
                seen = True
            elif tag == w("drawing"):
                seen = True
        if seen:
            out.append("".join(pieces))


def docx_text(parts: dict[str, bytes], footnote_count: int) -> list[str]:
    """Every paragraph's text from the package, in the order plain_text() gives it."""
    out: list[str] = []
    paragraphs(ET.fromstring(parts["word/document.xml"]), out)
    if footnote_count:
        root = ET.fromstring(parts["word/footnotes.xml"])
        for note in root.iter(w("footnote")):
            if note.get(w("type")) is None:
                paragraphs(note, out)
    return out


def expected_text(doc: md.Document, opts: dict | None = None) -> list[str]:
    opts = opts or DEFAULTS
    out = []
    items = layout(doc, opts)[0]
    # one answer for the whole document, as the writer takes it (ADR 0036)
    numbers_are_text = not opts["auto_numbering"]
    if opts["toc"]:
        out.extend(text for _, text in list_entries(items, "toc"))  # the entries the field carries
    for item in items:
        if "caption" in item:
            out.append(caption_text(item["caption"]))
        elif item["block"]["t"] == "directive" and item["block"]["name"] in LIST_FIELDS:
            out.extend(text for _, text in list_entries(items, item["block"]["name"]))
        elif item["block"]["t"] == "heading" and "number" in item and numbers_are_text:
            # the number is text in the heading's own paragraph, not one an application draws (ADR 0036)
            join = "\n" if opts["chapter_title_on_new_line"] else " "
            out.extend(item["number"] + join + line for line in md.plain_text([item["block"]], True, opts["thai_digits"]))
        elif (item["block"]["t"] == "heading" and "number" in item and opts["chapter_title_on_new_line"]):
            # the application draws the number; the break after it is still the build's
            out.extend("\n" + line for line in md.plain_text([item["block"]]))
        else:
            out.extend(md.plain_text([item["block"]], numbers_are_text, opts["thai_digits"]))
    for label in doc.footnote_order:
        blocks = doc.footnotes[label]
        if not blocks or blocks[0]["t"] != "paragraph":
            out.append("")
        out.extend(md.plain_text(blocks, numbers_are_text, opts["thai_digits"]))
    return [unicodedata.normalize("NFC", s) for s in out]
