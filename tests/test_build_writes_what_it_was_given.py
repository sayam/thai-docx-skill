# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""The build writes what it was given, the same in both implementations (ADR 0008, 0023).

Each case below was found in the review of 0.2.0, in one implementation or both. A value that
reaches a field is escaped there, and a caption label a field would misread is refused. A link
leads only to a web page or an address, and its target is written as a URI. A list numbered
from 0 starts at 0. Every format character and noncharacter is named from one list both read.
A tag name is ASCII in both. An allowed tag alone on its line gets a refusal that says why. A
float is reported as Python writes it. Two thousand open links read in a moment. A picture is
fitted to the page, never to nothing. And grill reads words and languages alike in both, and
says what it did not read. No golden moves.
"""

from __future__ import annotations

import re
import struct
import subprocess
import time
import zipfile
import zlib

from docx_fixture import good, pack, replaced
from test_what_a_command_takes import JS, PY, _node, both  # noqa: F401  the fixture runs here too


def part(path, name: str) -> str:
    with zipfile.ZipFile(path) as z:
        return z.read(name).decode("utf-8")


def texts(path) -> list[str]:
    return re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", part(path, "word/document.xml"))


CAPTIONED = "Table: ผล\n\n| ก | ข |\n|---|---|\n| 1 | 2 |\n"


# --- a value that reaches a field ------------------------------------------------------------------


def test_a_label_is_escaped_in_its_field_and_one_a_field_would_misread_is_refused(tmp_path):
    (tmp_path / "in.md").write_text(CAPTIONED, encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx", "--auto-numbering", "--table-label", "A&B"], tmp_path)
    assert code == 0, result
    assert "SEQ A&amp;B " in part(tmp_path / "out.docx", "word/document.xml")
    for label in ('A"B', "A\\B"):
        code, result = both(["build", "in.md", "out.docx", "--table-label", label], tmp_path)
        assert code == 2 and result["error"].startswith("--table-label takes"), result


def test_a_label_with_a_space_is_refused_only_where_word_counts(tmp_path):
    """Word's SEQ names its counter with one word; a label the build writes as text may hold a
    space as it always could."""
    (tmp_path / "in.md").write_text(CAPTIONED, encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx", "--auto-numbering", "--table-label", "ตาราง ที่"], tmp_path)
    assert code == 2 and result["error"].startswith("--table-label takes no space with --auto-numbering"), result
    assert both(["build", "in.md", "out.docx", "--table-label", "ตาราง ที่"], tmp_path)[0] == 0


# --- links ----------------------------------------------------------------------------------------


def test_a_link_leads_only_to_http_https_or_mailto(tmp_path):
    for text, scheme, line in (("ก [x](javascript:alert(1))\n", "javascript", 1), ("ก\n\n[y](FILE:///etc/passwd)\n", "FILE", 3),
                               ("ก <ftp://example.org/a>\n", "ftp", 1)):
        (tmp_path / "in.md").write_text(text, encoding="utf-8")
        code, result = both(["build", "in.md", "out.docx"], tmp_path)
        assert code == 2 and result["line"] == line and result["error"].endswith("leads to " + scheme + ":"), result
    (tmp_path / "in.md").write_text("[a](https://a.b) [b](HTTP://a.b) [c](#top) [d](other.docx) <mailto:a@b.c>\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 0 and result["counts"]["links"] == 5, result


def test_a_link_target_is_a_uri_and_its_text_is_unchanged(tmp_path):
    (tmp_path / "in.md").write_text("ก [a b](<https://example.com/a b>) [ไทย](https://example.com/ไทย?q=%E0%B8%81)\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 0, result
    rels = part(tmp_path / "out.docx", "word/_rels/document.xml.rels")
    assert 'Target="https://example.com/a%20b"' in rels
    assert 'Target="https://example.com/%E0%B9%84%E0%B8%97%E0%B8%A2?q=%E0%B8%81"' in rels
    assert "a b" in texts(tmp_path / "out.docx") and "ไทย" in texts(tmp_path / "out.docx")


def test_two_thousand_open_links_are_read_in_a_moment(tmp_path):
    (tmp_path / "in.md").write_text("[a](" * 8000 + "\n", encoding="utf-8")
    began = time.monotonic()
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 0 and time.monotonic() - began < 10, result


# --- what the text holds ---------------------------------------------------------------------------


def test_a_list_numbered_from_zero_starts_at_zero(tmp_path):
    (tmp_path / "in.md").write_text("0. ก\n1. ข\n", encoding="utf-8")
    assert both(["build", "in.md", "out.docx"], tmp_path)[0] == 0
    assert texts(tmp_path / "out.docx")[:3] == ["0.", "ก", "1."]
    assert both(["build", "in.md", "out.docx", "--auto-numbering"], tmp_path)[0] == 0
    assert '<w:startOverride w:val="0"/>' in part(tmp_path / "out.docx", "word/numbering.xml")


def test_every_format_character_and_noncharacter_is_refused_by_name(tmp_path):
    for ch, said in (("­", "U+00AD, a format character"), ("‮", "U+202E, a format character"),
                     ("\U000e0067", "U+E0067, a format character"), ("﷐", "U+FDD0, a noncharacter"),
                     ("\U0001fffe", "U+1FFFE, a noncharacter"), ("‍", "U+200D ZERO WIDTH JOINER")):
        (tmp_path / "in.md").write_text("ก" + ch + "ข\n", encoding="utf-8")
        code, result = both(["build", "in.md", "out.docx"], tmp_path)
        assert code == 2 and said in result["error"], (hex(ord(ch)), result)


def test_the_checker_names_a_format_character_in_a_file_it_did_not_write(tmp_path):
    parts = replaced(good(), "word/document.xml", "ตัวหนา", "ตัว‎หนา")
    (tmp_path / "in.docx").write_bytes(pack(parts))
    code, result = both(["check", "in.docx"], tmp_path)
    assert code == 1 and {"code": "invisible", "part": "word/document.xml",
                          "message": "text contains U+200E, a format character"} in result["findings"], result


def test_a_tag_name_is_ascii_in_both(tmp_path):
    for text in ("<ſ>\n", "<ſcript>\nx\n"):
        (tmp_path / "in.md").write_text(text, encoding="utf-8")
        code, result = both(["build", "in.md", "out.docx"], tmp_path)
        assert code == 0, (text, result)


def test_an_allowed_tag_alone_on_its_line_is_refused_with_the_reason(tmp_path):
    (tmp_path / "in.md").write_text("ก\n\n<br>\n\nข\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 2 and result["line"] == 3 and result["error"].startswith("<br> alone on its line is an HTML block"), result


def test_math_is_said_to_be_kept_as_it_was_written_without_a_version(tmp_path):
    (tmp_path / "in.md").write_text("ก $x^2$\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 0 and not any("v0.1" in w["message"] for w in result["warnings"]), result


def test_a_small_float_is_reported_as_python_writes_it(tmp_path):
    """Read as JSON the two spellings are one number, so the line itself is compared."""
    (tmp_path / "in.md").write_text("ก\n", encoding="utf-8")
    lines = [subprocess.run(cli + ["build", "in.md", "out.docx", "--indent", "0.00001"], cwd=tmp_path,
                            capture_output=True, timeout=30).stdout for cli in (PY, JS)]
    assert lines[0] == lines[1] and b'"first_line_indent_in": 1e-05,' in lines[0], lines


# --- pictures ---------------------------------------------------------------------------------------


def png(width: int, height: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)) + chunk(b"IEND", b"")


def test_a_picture_is_fitted_to_the_page_and_never_to_nothing(tmp_path):
    (tmp_path / "tall.png").write_bytes(png(1, 20000))
    (tmp_path / "wide.png").write_bytes(png(20000, 1))
    (tmp_path / "in.md").write_text("ก ![a](tall.png) ![b](wide.png)\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 0, result
    extents = [(int(cx), int(cy)) for cx, cy in re.findall(r'<wp:extent cx="(\d+)" cy="(\d+)"/>', part(tmp_path / "out.docx", "word/document.xml"))]
    page_height = (16838 - 1440 - 1440) * 635  # A4, one-inch margins top and bottom, in EMU
    assert extents[0][1] == page_height and extents[0][0] >= 1 and extents[1][1] >= 1, extents
    (tmp_path / "huge.png").write_bytes(png(1, 2 ** 31))
    (tmp_path / "in.md").write_text("ก ![a](huge.png)\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 2 and "none wider or taller than 20000" in result["error"], result


def test_a_picture_fits_the_line_its_paragraph_leaves_it(tmp_path):
    """RD-01: a picture was fitted to the text width and then indented, so with --indent, in a list
    or in a quotation it ran past the right margin by the indent — in every application read
    (2026-09-26). A picture alone in its paragraph now takes no first-line indent; one that opens
    a paragraph, or sits in a list or a quotation, is drawn no wider than the line it is on."""
    (tmp_path / "wide.png").write_bytes(png(20000, 100))
    (tmp_path / "in.md").write_text("![a](wide.png)\n\n![b](wide.png) ก\n\nก ![c](wide.png)\n\n- ก\n\n  ![d](wide.png)\n\n"
                                    "> ![e](wide.png)\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx", "--indent", "0.5"], tmp_path)
    assert code == 0, result
    document = part(tmp_path / "out.docx", "word/document.xml")
    widths = [int(cx) // 635 for cx in re.findall(r'<wp:extent cx="(\d+)"', document)]
    text = 11906 - 2160 - 1440  # A4 less the default margins, in twips
    assert widths == [text, text - 720, text, text - 720, text - 1440], widths
    alone = re.search(r"<w:p><w:pPr>(.*?)</w:pPr><w:r><w:drawing>", document).group(1)
    assert "w:firstLine" not in alone, alone


# --- grill ------------------------------------------------------------------------------------------


def test_grill_reads_the_same_words_in_both(tmp_path):
    for sep in ("\u001c", "\u0085", "﻿", "　", " "):
        code, result = both(["grill", "--said", "thai-docx grill" + sep + "save to v2"], tmp_path)
        assert code == 0, (hex(ord(sep)), result)
    assert both(["grill", "--said", "thai-docx grill　save to v2"], tmp_path)[1]["save_to"] == "v2"


def test_grill_says_what_it_did_not_read(tmp_path):
    code, result = both(["grill", "--said", "thai-docx grill ทำรายงาน จาก thesis"], tmp_path)
    assert result["start"] is None and result["warnings"][0].startswith("'จาก thesis' was not read"), result


def test_grill_asks_in_the_language_most_of_the_words_are_in(tmp_path):
    assert both(["grill", "--said", "thai-docx grill for a doc titled รายงาน"], tmp_path)[1]["language"] == "en"
    assert both(["grill", "--said", "ขอ thai-docx grill หน่อย"], tmp_path)[1]["language"] == "th"
