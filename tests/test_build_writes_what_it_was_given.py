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
    """Open link destinations were read in quadratic time. Held by how the time grows, not by a
    fixed ceiling: under coverage, on a loaded machine, 8,000 of them came within 3 % of the 10 s
    that ceiling allowed (the review of 0.3.0, F-04). Four times the input may take eight times
    as long, with a second to spare; a quadratic reading takes sixteen."""
    def timed(n: int) -> float:
        (tmp_path / "in.md").write_text("[a](" * n + "\n", encoding="utf-8")
        began = time.monotonic()
        code, result = both(["build", "in.md", "out.docx"], tmp_path)
        assert code == 0, result
        return time.monotonic() - began
    small, large = timed(4000), timed(16000)
    assert large < 8 * small + 1, (small, large)


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


def test_the_thesis_profile_boxes_a_caption_with_its_picture(tmp_path):
    """The thesis profile (read in the five applications as `sample-thesis`, 2026-09-28): a picture alone on its line
    is centred with no indent, and its caption is boxed to the picture — never narrower than 3
    inches, a box centred with the picture, so under a 2-inch one it starts half an inch before
    it — and aligns as the body does: under a picture 3 inches or wider its first character stands
    at the picture's left edge. Under the profile's `--align thai` the boxed caption is justified at the
    spaces between words, not distributed: Thai distributed alignment is for the body alone (the
    maintainer's decision, 2026-09-27). A table fills the text width, and so does its caption. A
    flag or `--default` takes either back."""
    (tmp_path / "small.png").write_bytes(png(192, 40))  # 2 in at 96 dpi
    (tmp_path / "wide.png").write_bytes(png(480, 40))   # 5 in
    (tmp_path / "in.md").write_text("![a](small.png)\n\nFigure: ขั้นตอน\n\n![b](wide.png)\n\nFigure: กว้าง\n\n"
                                    "Table: ตาราง\n\n| ก | ข |\n|---|---|\n| 1 | 2 |\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx", "--profile", "thesis"], tmp_path)
    assert code == 0 and result["settings"]["center_images"] and result["settings"]["caption_matches_object"], result
    document = part(tmp_path / "out.docx", "word/document.xml")
    pictures = re.findall(r"<w:p><w:pPr>((?:(?!</w:pPr>).)*)</w:pPr>(?:(?!</w:p>).)*<w:drawing>", document)
    assert pictures == ['<w:keepNext/><w:jc w:val="center"/>'] * 2, pictures
    captions = re.findall(r'<w:pStyle w:val="(FigureCaption|TableCaption)"/>(.*?)</w:pPr>', document)
    text = 11906 - 2160 - 1440  # A4 less the default margins, in twips
    three, five = (text - 4320) // 2, (text - 7200) // 2
    assert captions == [
        ("FigureCaption", '<w:ind w:left="' + str(three) + '" w:right="' + str(text - 4320 - three) + '"/><w:jc w:val="both"/>'),
        ("FigureCaption", '<w:ind w:left="' + str(five) + '" w:right="' + str(text - 7200 - five) + '"/><w:jc w:val="both"/>'),
        ("TableCaption", "<w:keepNext/>"),
    ], captions
    assert '<w:tblW w:w="5000" w:type="pct"/>' in document
    code, result = both(["build", "in.md", "out.docx", "--profile", "thesis", "--default", "center_images,caption_matches_object"], tmp_path)
    document = part(tmp_path / "out.docx", "word/document.xml")
    assert code == 0 and document.count('<w:pStyle w:val="FigureCaption"/><w:jc w:val="center"/>') == 2, document


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


# --- the review of 0.3.0: what the writer put where -------------------------------------------


def test_only_a_chapter_title_starts_its_own_line(tmp_path):
    """B-01: `--chapter-title-on-new-line` broke the line after the number of every numbered
    heading, so under the thesis profile "๑.๑" stood on a line of its own above its title. Only a
    level-one heading in the chapters or the appendices is broken."""
    (tmp_path / "in.md").write_text("<!-- chapters -->\n\n# บทนำ\n\n## ความเป็นมา\n\nข้อความ\n\n"
                                    "<!-- appendices -->\n\n# แบบสอบถาม\n\n## ส่วนที่ 1\n", encoding="utf-8")
    for flags in ([], ["--auto-numbering"]):
        code, result = both(["build", "in.md", "out.docx", "--profile", "thesis", *flags], tmp_path)
        assert code == 0, result
        document = part(tmp_path / "out.docx", "word/document.xml")
        headings = re.findall(r'<w:pStyle w:val="(Heading\d)"/>((?:(?!</w:p>).)*)</w:p>', document)
        assert [(style, "<w:br/>" in body) for style, body in headings] == [
            ("Heading1", True), ("Heading2", False), ("Heading1", True), ("Heading2", False)], (flags, headings)
    (tmp_path / "plain.md").write_text("# บทนำ\n\n## ความเป็นมา\n", encoding="utf-8")
    code, result = both(["build", "plain.md", "out.docx", "--heading-numbers", "--chapter-title-on-new-line"], tmp_path)
    assert "<w:br/>" not in part(tmp_path / "out.docx", "word/document.xml")
    assert any("--chapter-title-on-new-line changed nothing" in w["message"] for w in result["warnings"]), result


def test_a_footnote_holds_its_own_links_and_pictures(tmp_path):
    """B-02, B-03: a link in a footnote named a relationship of the document part, which OPC
    scopes to its own part; a picture in one made footnotes.xml not well-formed, and the build
    answered exit 1, a defect. The footnotes part has relationships of its own, and declares the
    picture's namespaces."""
    (tmp_path / "p.png").write_bytes(png(96, 40))
    (tmp_path / "in.md").write_text("ข้อความ[^1] และ[ลิงก์](https://example.com/b)\n\n"
                                    "[^1]: ดู [เว็บ](https://example.com/a) และรูป ![รูป](p.png)\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 0 and result["ok"], result
    notes = part(tmp_path / "out.docx", "word/footnotes.xml")
    rels = part(tmp_path / "out.docx", "word/_rels/footnotes.xml.rels")
    for rid in re.findall(r'r:(?:id|embed)="(rId\d+)"', notes):
        assert f'Id="{rid}"' in rels, (rid, rels)
    assert 'Target="https://example.com/a"' in rels and "media/image1.png" in rels, rels
    assert 'Target="https://example.com/a"' not in part(tmp_path / "out.docx", "word/_rels/document.xml.rels")
    assert both(["check", "out.docx"], tmp_path)[0] == 0
    import zipfile
    with zipfile.ZipFile(tmp_path / "out.docx") as z, zipfile.ZipFile(tmp_path / "cut.docx", "w") as cut:
        for info in z.infolist():
            if info.filename != "word/_rels/footnotes.xml.rels":
                cut.writestr(info, z.read(info))
    code, result = both(["check", "cut.docx"], tmp_path)
    assert code == 2 and result["findings"][0]["code"] == "package" and "rId" in result["findings"][0]["message"], result


def test_a_picture_in_a_list_or_a_quotation_keeps_its_place_under_center_images(tmp_path):
    """B-05: `--center-images` wrote a picture in a list or a quotation as a centred paragraph of
    its own, out of the list or the quotation, and still said it changed nothing. It centres a
    picture on a line of its own at the top level, as its warning reads it."""
    (tmp_path / "p.png").write_bytes(png(96, 40))
    (tmp_path / "in.md").write_text("- รายการ\n\n  ![ก](p.png)\n\n> ![ข](p.png)\n>\n> ข้อความ\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx", "--center-images"], tmp_path)
    document = part(tmp_path / "out.docx", "word/document.xml")
    pictures = re.findall(r"<w:p><w:pPr>((?:(?!</w:pPr>).)*)</w:pPr>(?:(?!</w:p>).)*<w:drawing>", document)
    assert pictures == ['<w:pStyle w:val="ListParagraph"/><w:ind w:left="720"/>', '<w:pStyle w:val="Quote"/>'], pictures
    assert any("--center-images changed nothing" in w["message"] for w in result["warnings"]), result


def test_a_picture_in_a_table_fits_its_cell(tmp_path):
    """B-06: a picture in a table cell was fitted to the text width, so a picture 5.77 in wide
    stood in a column of 1.92 in."""
    (tmp_path / "wide.png").write_bytes(png(3000, 100))
    (tmp_path / "in.md").write_text("| ภาพ | ข | ค |\n|---|---|---|\n| ![ก](wide.png) | ข | ค |\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    document = part(tmp_path / "out.docx", "word/document.xml")
    column = int(re.search(r'<w:gridCol w:w="(\d+)"/>', document).group(1))
    cx = int(re.search(r'<wp:extent cx="(\d+)"', document).group(1))
    assert cx <= (column - 216) * 635, (cx // 635, column)


def test_pictures_side_by_side_give_their_caption_the_text_width(tmp_path):
    """B-07: a caption's box was measured from the last picture written, so under two pictures
    side by side it was as wide as the second alone. Under more than one picture a caption takes
    the width of the text, centred."""
    (tmp_path / "wide.png").write_bytes(png(3000, 100))
    (tmp_path / "small.png").write_bytes(png(96, 40))
    (tmp_path / "in.md").write_text("![ก](wide.png) ![ข](small.png)\n\nFigure: สองภาพ\n\n![ค](small.png)\n\nFigure: ภาพเดียว\n",
                                    encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx", "--profile", "thesis"], tmp_path)
    captions = re.findall(r'<w:pStyle w:val="FigureCaption"/>((?:(?!</w:pPr>).)*)</w:pPr>', part(tmp_path / "out.docx", "word/document.xml"))
    assert captions[0] == '<w:jc w:val="center"/>' and captions[1].startswith("<w:ind "), captions


# --- the review of 0.3.0: runs and text --------------------------------------------------------


def _runs(document: str) -> list[tuple[bool, str]]:
    return [("<w:cs/>" in rpr, text) for rpr, text in re.findall(r"<w:r>(<w:rPr>.*?</w:rPr>)?<w:t[^>]*>([^<]*)</w:t></w:r>", document)]


def test_punctuation_after_formatted_thai_is_thai(tmp_path):
    """B-04: a mark with Thai on both sides is Thai (0.3.0), but a mark in a text node of its own
    — after a bold word or a link — had no letter beside it to read, so `.` `)` `”` were Latin."""
    (tmp_path / "in.md").write_text("ดู[เว็บไซต์](https://example.com).\n\nคำว่า “**สำคัญ**”\n\nดูที่ (*ภาคผนวก*)\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    runs = _runs(part(tmp_path / "out.docx", "word/document.xml"))
    assert all(cs for cs, text in runs if text.strip() in (".", "”", ")")), runs


def test_a_run_word_writes_right_to_left_is_marked(tmp_path):
    """B-08: Word writes Arabic and Hebrew with `<w:rtl/>`, which makes the run use its
    complex-script properties (ECMA-376 §17.3.2.30); `check` found it unmarked and `repair` marked
    it again."""
    parts = replaced(good(), "word/document.xml", "<w:body>",
                     '<w:body><w:p><w:pPr><w:bidi/></w:pPr><w:r><w:rPr><w:rtl/><w:lang w:bidi="ar-SA"/></w:rPr>'
                     "<w:t>مرحبا</w:t></w:r></w:p>")
    (tmp_path / "ar.docx").write_bytes(pack(parts))
    code, result = both(["check", "ar.docx"], tmp_path)
    assert code == 0 and result["findings"] == [], result


def test_the_thai_language_is_written_on_thai_only(tmp_path):
    """B-09: `--thai-language` wrote `w:bidi="th-TH"` on every complex-script run, so Lao, Arabic,
    Devanagari and Khmer were told to Word as Thai."""
    (tmp_path / "in.md").write_text("ภาษาลาว ພາສາລາວ ภาษาอาหรับ العربية ภาษาฮินดี हिन्दी\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx", "--thai-language"], tmp_path)
    document = part(tmp_path / "out.docx", "word/document.xml")
    for word in ("ພາສາລາວ", "العربية", "हिन्दी"):
        rpr = re.search(r"<w:r>(<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>)<w:t[^>]*>[^<]*" + word, document).group(1)
        assert "<w:cs/>" in rpr and "th-TH" not in rpr, (word, rpr)
    assert re.search(r'<w:lang w:bidi="th-TH"/></w:rPr><w:t[^>]*>ภาษาลาว', document), document


def test_only_thai_is_put_in_its_normal_form(tmp_path):
    """B-10: the whole text was put in NFC, which changes letters that are not Thai — a
    compatibility ideograph (U+F92C) became its unified twin, U+212B became Å — in silence; the
    Markdown page says the text is never altered but Thai's mark order."""
    (tmp_path / "in.md").write_text("กุ่ 郎 Å é\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    document = part(tmp_path / "out.docx", "word/document.xml")
    assert code == 0 and "郎" in document and "Å" in document and "é" in document, result


def test_a_link_or_picture_title_is_written(tmp_path):
    """B-11: a title given to a link or a picture was read and dropped in silence."""
    (tmp_path / "p.png").write_bytes(png(96, 40))
    (tmp_path / "in.md").write_text('ดู [ลิงก์](https://example.com "คำอธิบายลิงก์") และ ![รูป](p.png "ชื่อรูป")\n', encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    document = part(tmp_path / "out.docx", "word/document.xml")
    assert 'w:tooltip="คำอธิบายลิงก์"' in document and 'title="ชื่อรูป"' in document, document


def test_marks_stacked_on_one_letter_are_named(tmp_path):
    """B-13: only two tone marks were named; two vowels above, two below, a tone mark with the
    thanthakhat, or ำ twice went through in silence."""
    lines = ["กิี", "กุู", "ก่์", "กำำ", "กัิ"]
    (tmp_path / "in.md").write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    named = [w["message"] for w in result["warnings"] if "marks" in w["message"] or "mark" in w["message"]]
    assert len(named) == len(lines), result["warnings"]


def test_signs_between_thai_are_thai(tmp_path):
    """B-14: `°` `×` `±` `§` `·` between Thai were Latin runs cut into the word."""
    (tmp_path / "in.md").write_text("อุณหภูมิ ๓๐°ซ ขนาด ๒×๓ ค่า ๕±๑ มาตรา§๒\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    runs = _runs(part(tmp_path / "out.docx", "word/document.xml"))
    assert all(cs for cs, _ in runs), runs


def test_a_profile_setting_that_changed_nothing_is_not_said(tmp_path):
    """B-15: the thesis profile turns on settings a document may not need, and every build then
    said "--center-images changed nothing" of a flag the user never typed."""
    (tmp_path / "in.md").write_text("<!-- chapters -->\n\n# บทนำ\n\nข้อความ\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx", "--profile", "thesis"], tmp_path)
    assert code == 0 and result["warnings"] == [], result
    code, result = both(["build", "in.md", "out.docx", "--profile", "thesis", "--center-images"], tmp_path)
    assert any("--center-images changed nothing" in w["message"] for w in result["warnings"]), result


# --- the maintainer's decisions on the review of 0.3.0 (DESIGN) ---------------------------------


def test_a_joiner_between_letters_of_another_complex_script_is_kept(tmp_path):
    """B-D1: Persian spells with U+200C and Devanagari shapes a half letter with U+200D, and the
    build refused both. Between two letters of a complex script other than Thai, each is text; in
    Thai, or beside anything else, it is still refused (ADR 0023)."""
    (tmp_path / "in.md").write_text("ภาษาฮินดี नमस्‍ते และเปอร์เซีย من‌می\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    document = part(tmp_path / "out.docx", "word/document.xml")
    assert code == 0 and "नमस्‍ते" in document and "من‌می" in document, result
    assert both(["check", "out.docx"], tmp_path)[0] == 0
    for refused in ("ไทย‍ไทย", "ab‌cd", "मन‍"):
        (tmp_path / "in.md").write_text(refused + "\n", encoding="utf-8")
        assert both(["build", "in.md", "out.docx"], tmp_path)[0] == 2, refused


def test_code_with_no_complex_script_is_not_proofed(tmp_path):
    """B-D2: a code span or a code block of Latin text was proofed as English and underlined in
    every application. Its runs carry `<w:noProof/>` — only where the text holds no complex
    script, as ADR 0004's cause 3 is about Thai line breaking — and `check` takes no finding
    from it."""
    (tmp_path / "in.md").write_text("ใช้ `w:ascii` และ `ภาษาไทย`\n\n```\nw:rFonts ไทย\n```\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    run = r"<w:r>(<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>)?<w:t[^>]*>([^<]*)</w:t>"

    def proofless(name):
        return {text: "<w:noProof/>" in rpr for rpr, text in re.findall(run, part(tmp_path / name, "word/document.xml"))}
    assert proofless("out.docx") == {"ใช้ ": False, "w:ascii": True, " และ ": False, "ภาษาไทย": False,
                                     "w:rFonts ": True, "ไทย": False}, proofless("out.docx")
    assert both(["check", "out.docx"], tmp_path)[1]["findings"] == []
    # repair takes the switch off Thai text and leaves it on the code it belongs to
    with zipfile.ZipFile(tmp_path / "out.docx") as z:
        parts = {n: z.read(n).decode("utf-8") for n in z.namelist() if n.endswith((".xml", ".rels"))}
    thai = re.search(r"<w:cs/>(?:(?!<w:r>).)*>ภาษาไทย<", parts["word/document.xml"]).group(0)
    (tmp_path / "noproof.docx").write_bytes(pack(replaced(parts, "word/document.xml", thai, "<w:noProof/>" + thai)))
    assert [f["code"] for f in both(["check", "noproof.docx"], tmp_path)[1]["findings"]] == ["3"]
    code, result = both(["repair", "noproof.docx", "again.docx"], tmp_path)
    assert code == 0 and result["repaired"] == {"3": 1}, result
    assert proofless("again.docx") == proofless("out.docx")


# --- 0.3.1: four flags that reached nothing in silence -------------------------------------------

HEADINGS_NONE = "--heading-numbers reached no heading: the document has none"
HEADINGS_REGIONS = ("--heading-numbers reached no heading: in a document with region comments it numbers the ## and"
                    " lower headings under <!-- chapters --> or <!-- appendices -->, and there are none")
BODY_NONE = ("--indent changed nothing: the document has no body paragraph; a heading, list, quotation, table,"
             " code, caption or picture alone in its paragraph takes no first-line indent")
TABLE_NONE = "--table-size reached no table: the document has none, and only the Table Text style carries the size"
DIGITS_NONE = ("--thai-digits reached no number: the document has no page, heading, list, caption or footnote number,"
               " and only the page-number format names Thai digits")


def test_each_of_four_flags_that_reaches_nothing_is_named(tmp_path):
    """0.3.1: --heading-numbers, --indent, --table-size and --thai-digits said nothing when the
    document held nothing for them, where every other flag says so (ADR 0028). The two that
    change no byte then "changed nothing"; the two that write a style or a page-number format
    that nothing uses "reached no" — the words --thai-language uses for the same."""
    cases = [
        ("ข้อความ\n", ["--heading-numbers"], [HEADINGS_NONE]),
        ("# หัว\n\nข้อความ\n", ["--heading-numbers"], []),
        ("<!-- chapters -->\n\n# บทนำ\n\nข้อความ\n", ["--heading-numbers"], [HEADINGS_REGIONS]),
        ("<!-- chapters -->\n\n# บทนำ\n\nข้อความ\n", ["--heading-numbers", "--auto-numbering"], [HEADINGS_REGIONS]),
        ("<!-- chapters -->\n\n# บทนำ\n\n## ที่มา\n\nข้อความ\n", ["--heading-numbers"], []),
        ("ปก\n\n<!-- front -->\n\n# บทคัดย่อ\n\n## ย่อย\n", ["--heading-numbers"], [HEADINGS_REGIONS]),
        ("# หัว\n\n- รายการ\n\n> อ้าง\n", ["--indent", "0.5"], [BODY_NONE]),
        ("# หัว\n\nข้อความ\n", ["--indent", "0.5"], []),
        ("ข้อความ\n", ["--table-size", "12"], [TABLE_NONE]),
        ("> | ก | ข |\n> |---|---|\n> | 1 | 2 |\n", ["--table-size", "12"], []),
        ("ข้อความ\n", ["--thai-digits"], [DIGITS_NONE]),
        ("# หัว\n\nข้อความ\n", ["--thai-digits"], [DIGITS_NONE]),
        ("# หัว\n\nข้อความ\n", ["--thai-digits", "--heading-numbers"], []),
        ("ข้อความ\n", ["--thai-digits", "--page-numbers"], []),
        ("ข้อความ[^1]\n\n[^1]: เชิงอรรถ\n", ["--thai-digits"], []),
        ("1. หนึ่ง\n2. สอง\n", ["--thai-digits"], []),
        ("Table: ผล\n\n| ก | ข |\n|---|---|\n| 1 | 2 |\n", ["--thai-digits"], []),
        ("<!-- chapters -->\n\n# บทนำ\n\nข้อความ\n", ["--thai-digits"], []),
        ("# หัว\n\n<!-- toc -->\n", ["--thai-digits"], []),
        ("ข้อความ\n", ["--heading-numbers", "--indent", "1", "--table-size", "12", "--thai-digits"],
         [HEADINGS_NONE, DIGITS_NONE, TABLE_NONE]),
    ]
    for text, flags, expected in cases:
        (tmp_path / "in.md").write_text(text, encoding="utf-8")
        code, result = both(["build", "in.md", "out.docx", *flags], tmp_path)
        said = [w["message"] for w in result["warnings"] if w["code"] == "settings"]
        assert code == 0 and said == expected, (text, flags, said)


def test_a_profile_setting_that_reached_nothing_is_not_said_either(tmp_path):
    """The thesis profile turns on --heading-numbers and --indent; what it set and no flag named
    is not the user's to hear about (B-15). Its page numbers are what its --thai-digits reaches."""
    (tmp_path / "in.md").write_text("<!-- front -->\n\n# บทคัดย่อ\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx", "--profile", "thesis"], tmp_path)
    assert code == 0 and [w for w in result["warnings"] if w["code"] == "settings"] == [], result
    code, result = both(["build", "in.md", "out.docx", "--profile", "thesis", "--indent", "1"], tmp_path)
    assert [w["message"] for w in result["warnings"] if w["code"] == "settings"] == [BODY_NONE]


def test_where_this_reading_and_githubs_differ_the_build_stops_at_the_line(tmp_path):
    """C-13 (the review of 0.2.0): the places where GitHub drops or bends what this reading
    refuses, as references/markdown.md lists them — each stops the build at its line, in both;
    and a non-breaking space at a paragraph's edge is kept, as CommonMark says."""
    stops = [
        ("ก\n\n<!-- ก\n\nข\n", 3, "HTML comment is never closed"),
        ("ก\n\n<!-- ก --> ข\n", 3, "an HTML comment block also holds text"),
        ("| ก |\n|---|\n| 1 | 2 |\n", 3, "table row has 2 cells; the header has 1"),
        ("ก[^1]\n\n[^1]: a\n\n[^1]: b\n", 5, "footnote [^1] is defined twice"),
        ("ก\n\n[^1]: a\n", 3, "footnote [^1] is defined but never referenced"),
        ("<?x?>\n", 1, "HTML blocks are not supported"),
        ("<!DOCTYPE x>\n", 1, "HTML blocks are not supported"),
        ("<![CDATA[x]]>\n", 1, "HTML blocks are not supported"),
    ]
    for text, line, said in stops:
        (tmp_path / "in.md").write_text(text, encoding="utf-8")
        code, result = both(["build", "in.md", "out.docx"], tmp_path)
        assert code == 2 and result["line"] == line and result["error"].startswith(said), (text, result)
    (tmp_path / "in.md").write_text(" ก \n", encoding="utf-8")
    assert both(["build", "in.md", "out.docx"], tmp_path)[0] == 0
    assert "> ก <" in part(tmp_path / "out.docx", "word/document.xml")
