# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""The checker's limits hold at the values it states, in both implementations (ADR 0017, 0030).

A limit held only by reading the code is not held: the review of 0.2.0 raised the per-part and
total caps tenfold, and the hops through symbolic links a hundredfold, and every test stayed
green — the one test of the total cap patched the constant it claimed to hold. So each limit is
met here at its value, from the input side, through both command lines, and each constant is
read from both sources beside it.

And a part is judged UTF-8 on its bytes. A part in UTF-16 with no byte-order mark decodes as
UTF-8 — a NUL is valid there — so it reached a parser that read it as UTF-16, past the DOCTYPE
refusal that reads bytes as ASCII, and expanded the entities it declared.
"""

from __future__ import annotations

import os
import re

import pytest

import parity
from docx_fixture import good, pack, replaced
from test_what_a_command_takes import JS, _node, both  # noqa: F401  the fixture runs here too
from thai_docx import build, check, package, profiles
from thai_docx import markdown as md

MiB = 1024 * 1024
BUNDLE = JS[1]


def test_each_limit_is_the_value_both_implementations_state():
    python = {"MAX_PART": check.MAX_PART, "MAX_TOTAL": check.MAX_TOTAL, "MAX_FILE": package.MAX_FILE,
              "MAX_LINKS": build.MAX_LINKS, "MAX_MARKDOWN": build.MAX_MARKDOWN, "MAX_IMAGE": build.MAX_IMAGE,
              "MAX_DEPTH": md.MAX_DEPTH, "PROFILE_MAX_BYTES": profiles.MAX_BYTES}
    assert python == {"MAX_PART": 32 * MiB, "MAX_TOTAL": 64 * MiB, "MAX_FILE": 64 * MiB, "MAX_LINKS": 40,
                      "MAX_MARKDOWN": 16 * MiB, "MAX_IMAGE": 32 * MiB, "MAX_DEPTH": 100, "PROFILE_MAX_BYTES": 64 * 1024}
    source = open(BUNDLE, encoding="utf-8").read()
    for name, value in python.items():
        m = re.search(r"\bconst " + name + r" = ([0-9 *]+);", source)
        assert m is not None and eval(m.group(1)) == value, name  # noqa: S307  digits and * only


def declared(sizes: list[int]) -> bytes:
    """A package whose directory declares these sizes and holds none of the bytes: a cap on
    declared sizes is met without writing them."""
    return parity.write_zip([{"name": ("word/document.xml" if i == 0 else f"word/p{i}.xml").encode(), "data": b"",
                              "crc": 0, "size": size, "method": 0, "flags": 0} for i, size in enumerate(sizes)])


@pytest.mark.parametrize(("sizes", "refused"), [
    ([30 * MiB, 30 * MiB, 30 * MiB], True),   # every part under the part cap, the whole over the total
    ([22 * MiB, 21 * MiB, 21 * MiB], False),  # 64 MiB, to the byte
    ([32 * MiB + 1], True),
    ([32 * MiB], False),
])
def test_the_size_caps_hold_at_their_values(tmp_path, sizes, refused):
    (tmp_path / "p.docx").write_bytes(declared(sizes))
    code, result = both(["check", "p.docx"], tmp_path)
    assert code == 2 and (("size" in {f["code"] for f in result["findings"]}) == refused), result


@pytest.mark.skipif(os.name != "posix", reason="symbolic links as POSIX makes them")
def test_forty_links_are_followed_and_the_forty_first_is_not(tmp_path):
    """A chain whose end lies outside the Markdown's directory. Followed to its end, it is refused
    as outside. One link longer, the walk once stopped at the fortieth — inside the directory —
    and the OS then followed the last link out of it: the picture was read. It is refused."""
    outside = tmp_path / "outside.png"
    outside.write_bytes(parity.PNG)
    doc = tmp_path / "doc"
    doc.mkdir()
    for hops, said in ((40, "lies outside"), (41, "more than 40 symbolic links")):
        chain = doc / f"c{hops}"
        chain.mkdir()
        (chain / "l0").symlink_to(outside)
        for i in range(1, hops):
            (chain / f"l{i}").symlink_to(chain / f"l{i - 1}")
        (doc / f"in{hops}.md").write_text(f"ก ![x](c{hops}/l{hops - 1})\n", encoding="utf-8")
        code, result = both(["build", f"doc/in{hops}.md", "out.docx"], tmp_path)
        assert code == 2 and said in result["error"], (hops, result)


@pytest.mark.parametrize("encoding", ["utf-16-le", "utf-16-be"])
def test_a_utf16_part_is_refused_not_parsed(tmp_path, encoding):
    parts = good()
    doc = parts["word/document.xml"].replace(
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n',
        '<?xml version="1.0"?>\n<!DOCTYPE w:document [<!ENTITY thai "กขค">]>\n', 1)
    parts["word/document.xml"] = doc.replace("<w:t", "&thai;<w:t", 1).encode(encoding)
    (tmp_path / "u16.docx").write_bytes(pack(parts))
    code, result = both(["check", "u16.docx"], tmp_path)
    assert code == 2 and result["findings"] == [
        {"code": "package", "part": "word/document.xml", "message": "XML part is not UTF-8"}], result
    code, result = both(["repair", "u16.docx", "out.docx"], tmp_path)
    assert code == 2 and not (tmp_path / "out.docx").exists(), result


def test_a_run_nested_past_any_stack_is_read_not_a_trace(tmp_path):
    """Comparing two runs' formatting once recursed as deep as the input went: 500 levels
    stopped Python, and JavaScript at a depth of its own. Both now give a verdict."""
    deep = "<w:x>" * 5000 + "</w:x>" * 5000
    parts = replaced(good(), "word/document.xml", "<w:rPr><w:cs/>", "<w:rPr>" + deep + "<w:cs/>")
    (tmp_path / "deep.docx").write_bytes(pack(parts))
    code, result = both(["check", "deep.docx"], tmp_path)
    assert code == 0 and result["ok"] and result["counts"]["runs"] > 0, result
