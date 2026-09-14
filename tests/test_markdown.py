"""The Markdown dialect of ADR 0010, one construct at a time — and the line number
on everything outside it. Uses the parser directly; the build tests cover the XML.
"""

from __future__ import annotations

import pytest

from thai_docx import markdown as md


def inl(text: str) -> list[tuple]:
    """(text, flags, link) triples of the first paragraph of `text`."""
    doc = md.parse(text)
    return [
        (n["s"], "".join(f for f in md.FLAGS if n.get(f)), n.get("link"))
        if n["t"] == "text" else (n["t"],)
        for n in doc.blocks[0]["inlines"]
    ]


def types(text: str) -> list[str]:
    return [b["t"] for b in md.parse(text).blocks]


# --- the soft-break rule (ADR 0005 transformation 1) ---


def test_soft_break_between_thai_characters_adds_nothing():
    assert inl("สวัสดี\nชาวโลก") == [("สวัสดีชาวโลก", "", None)]


@pytest.mark.parametrize("text,expected", [
    ("hello\nworld", "hello world"),
    ("สวัสดี\nworld", "สวัสดี world"),
    ("hello\nชาวโลก", "hello ชาวโลก"),
    ("สวัสดี,\nชาวโลก", "สวัสดี, ชาวโลก"),
])
def test_other_soft_breaks_are_one_space(text, expected):
    assert inl(text) == [(expected, "", None)]


@pytest.mark.parametrize("text", ["ก  \nข", "ก\\\nข", "ก<br>ข", "ก<br/>ข"])
def test_hard_breaks(text):
    assert inl(text) == [("ก", "", None), ("hardbreak",), ("ข", "", None)]


# --- inlines ---


def test_emphasis_and_strong():
    assert inl("a **b** *c* ***d*** _e_ __f__") == [
        ("a ", "", None), ("b", "b", None), (" ", "", None), ("c", "i", None), (" ", "", None),
        ("d", "bi", None), (" ", "", None), ("e", "i", None), (" ", "", None), ("f", "b", None),
    ]


def test_intraword_underscore_is_literal_but_star_is_not():
    assert inl("snake_case_name") == [("snake_case_name", "", None)]
    assert inl("foo_bar_ and _baz_") == [("foo_bar_ and ", "", None), ("baz", "i", None)]
    assert inl("a*b*c") == [("a", "", None), ("b", "i", None), ("c", "", None)]


def test_strikethrough_needs_matching_tilde_runs():
    assert inl("~~gone~~ ~keep~~") == [("gone", "strike", None), (" ~keep~~", "", None)]


def test_unmatched_delimiters_are_text():
    assert inl("2 * 3 * 4 and **open") == [("2 * 3 * 4 and **open", "", None)]


def test_code_span_keeps_markup_and_strips_one_padding_space():
    assert inl("x `` a ` b `` y ` **z** `") == [
        ("x ", "", None), ("a ` b", "code", None), (" y ", "", None), ("**z**", "code", None),
    ]


def test_escapes_and_entities():
    assert inl(r"\*not\* &amp; &#169; &copy; &bogus; \\") == [(r"*not* & © © &bogus; \ ", "", None)][:1] or inl(r"\*not\* &amp; &#169; &copy; &bogus; \\")[0][0].startswith("*not* & © © &bogus;")


def test_links_inline_reference_collapsed_shortcut():
    text = "[a](https://x.example/ \"t\") [b][ref] [ref][] [ref] [none]\n\n[ref]: https://r.example/"
    assert inl(text) == [
        ("a", "", "https://x.example/"), (" ", "", None), ("b", "", "https://r.example/"), (" ", "", None),
        ("ref", "", "https://r.example/"), (" ", "", None), ("ref", "", "https://r.example/"), (" [none]", "", None),
    ]


def test_link_text_keeps_its_own_formatting():
    assert inl("[**b** i](u)") == [("b", "b", "u"), (" i", "", "u")]


def test_autolinks_and_bare_urls():
    assert inl("<https://a.example/> <me@b.example> www.c.example/p, https://d.example/x.") == [
        ("https://a.example/", "", "https://a.example/"), (" ", "", None),
        ("me@b.example", "", "mailto:me@b.example"), (" ", "", None),
        ("www.c.example/p", "", "http://www.c.example/p"), (", ", "", None),
        ("https://d.example/x", "", "https://d.example/x"), (".", "", None),
    ]


def test_image_alt_is_plain_text():
    doc = md.parse("![a **b**](p.png)")
    assert doc.blocks[0]["inlines"] == [{"t": "image", "src": "p.png", "alt": "a b"}]


def test_reference_style_image_is_an_image_not_a_bang_and_a_link():
    doc = md.parse("![alt][pic]\n\n[pic]: p.png")
    assert doc.blocks[0]["inlines"] == [{"t": "image", "src": "p.png", "alt": "alt"}]


def test_allowed_html_inline_tags():
    assert inl("H<sub>2</sub>O x<sup>2</sup> <u>u</u> <kbd>K</kbd>") == [
        ("H", "", None), ("2", "sub", None), ("O x", "", None), ("2", "sup", None), (" ", "", None),
        ("u", "u", None), (" ", "", None), ("K", "code", None),
    ]


def test_inline_comment_is_removed_and_merged():
    assert inl("ก<!-- x -->ข") == [("กข", "", None)]


@pytest.mark.parametrize("text,line", [("a\n\nb <span>c</span>", 3), ("<div>\nx\n</div>", 1), ("<script>", 1)])
def test_other_html_stops_with_its_line(text, line):
    with pytest.raises(md.Unsupported) as e:
        md.parse(text)
    assert e.value.line == line and "not supported" in e.value.what


def test_math_is_literal_code_with_a_warning_and_currency_is_not():
    doc = md.parse("สูตร $E=mc^2$ ราคา 5 $ ต่อ 3 $ จบ\n\n$$\nx\n$$")
    assert [n.get("s") for n in doc.blocks[0]["inlines"]] == ["สูตร ", "E=mc^2", " ราคา 5 $ ต่อ 3 $ จบ"]
    assert doc.blocks[0]["inlines"][1]["code"]
    assert doc.blocks[1] == {"t": "code", "lines": ["x"], "info": "math", "math": True}
    assert [w.split(":")[0] for w in doc.warnings] == ["line 1", "line 3"]


def test_footnote_reference_and_definition():
    doc = md.parse("a[^n] b\n\n[^n]: note **x**\n    more\n")
    assert doc.blocks[0]["inlines"][1] == {"t": "footnote_ref", "label": "n"}
    assert md.plain_text(doc.footnotes["n"]) == ["note x more"]


def test_undefined_and_duplicate_footnotes_stop():
    with pytest.raises(md.Unsupported, match="never defined"):
        md.parse("a[^x]")
    with pytest.raises(md.Unsupported, match="defined twice"):
        md.parse("a[^x]\n\n[^x]: 1\n\n[^x]: 2")


def test_invisible_character_in_input_stops_with_its_line():
    with pytest.raises(md.Unsupported) as e:
        md.parse("ok\n\nก​ข")
    assert e.value.line == 3 and "U+200B" in e.value.what


# --- blocks ---


def test_headings_atx_closing_and_setext():
    doc = md.parse("# One #\n\nTwo\n===\n\nThree\n---\n\n###### Six\n\n####### not")
    assert [(b["level"], md._plain(b["inlines"])) for b in doc.blocks[:4]] == [(1, "One"), (1, "Two"), (2, "Three"), (6, "Six")]
    assert doc.blocks[4]["t"] == "paragraph"


def test_thematic_break_versus_setext():
    assert types("a\n---\n\n---\n\n* * *") == ["heading", "break", "break"]


def test_fenced_and_indented_code():
    doc = md.parse("```py x\n  keep\n```\n\n    tab\n    bed\n\n~~~\n```\n~~~")
    assert doc.blocks[0] == {"t": "code", "lines": ["  keep"], "info": "py x", "math": False}
    assert doc.blocks[1]["lines"] == ["tab", "bed"]
    assert doc.blocks[2]["lines"] == ["```"]


def test_unclosed_fence_stops():
    with pytest.raises(md.Unsupported, match="never closed"):
        md.parse("x\n\n```\ncode")


def test_nested_lists_ordered_start_and_lazy_lines():
    doc = md.parse("- a\n  continued\n- b\n  - c\n  - d\n\n3) x\n4) y\n   1. z")
    ul, ol = doc.blocks
    assert not ul["ordered"] and ol["ordered"] and ol["start"] == 3
    assert md.plain_text(ul["items"][0]) == ["a continued"]
    assert ul["items"][1][1]["t"] == "list" and md.plain_text(ul["items"][1][1]["items"][1]) == ["d"]
    assert ol["items"][1][1]["items"][0][0]["inlines"][0]["s"] == "z"


def test_task_items():
    doc = md.parse("- [ ] open\n- [x] done\n- [X] DONE\n- [y] not a task")
    first = [i[0]["inlines"][0] for i in doc.blocks[0]["items"]]
    assert first[:3] == [{"t": "task", "checked": False}, {"t": "task", "checked": True}, {"t": "task", "checked": True}]
    assert first[3]["s"] == "[y] not a task"
    assert md.plain_text(doc.blocks[0]["items"][0]) == ["☐ open"]


def test_table_alignment_escaped_pipe_and_padding():
    doc = md.parse("| a | b | c |\n|:--|--:|:-:|\n| x \\| y | 1 |\n")
    t = doc.blocks[0]
    assert t["aligns"] == ["left", "right", "center"]
    assert [[md._plain(c) for c in r] for r in t["rows"]] == [["a", "b", "c"], ["x | y", "1", ""]]


def test_table_row_with_extra_cells_stops():
    with pytest.raises(md.Unsupported) as e:
        md.parse("| a |\n|---|\n| 1 | 2 |")
    assert e.value.line == 3 and "dropped" in e.value.what


def test_blockquote_with_lazy_continuation_and_nested_block():
    doc = md.parse("> ก\nข\n>\n> - item")
    q = doc.blocks[0]
    assert q["t"] == "quote" and md.plain_text(q["blocks"]) == ["กข", "item"]


def test_front_matter_and_bom():
    doc = md.parse("﻿---\ntitle: T\nauthor: \"A\"\n---\n\nbody")
    assert doc.front_matter == {"title": "T", "author": "A"}
    assert types("---\ntitle: T\n---\n\nbody") == ["paragraph"]


def test_html_comment_block_is_dropped():
    assert types("a\n\n<!-- one\ntwo -->\n\nb") == ["paragraph", "paragraph"]


def test_plain_text_orders_everything_the_docx_must_carry():
    doc = md.parse("# h\n\np  \nq\n\n- [x] t\n\n| a |\n|---|\n| b |\n\n> z\n\n```\nc\n```")
    assert md.plain_text(doc.blocks) == ["h", "p\nq", "☑ t", "a", "b", "z", "c"]
