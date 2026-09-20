# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""The checker, proved in both directions: a clean package passes, and each planted
violation is reported under its own code (ADR 0004, 0023, 0030; gate
`checkers-proven-two-way`).
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from docx_fixture import BOLD_PROPS, RUN_PROPS, good, pack, replaced, run
from thai_docx import check as check_mod
from thai_docx.check import check

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "thai-docx" / "scripts" / "thai_docx"
FIXTURES = ROOT / "tests" / "fixtures"


def codes(report) -> set[str]:
    return {f["code"] for f in report.findings}


def written(tmp_path, parts) -> pathlib.Path:
    path = tmp_path / "doc.docx"
    path.write_bytes(pack(parts))
    return path


def test_clean_package_passes(tmp_path):
    report = check(written(tmp_path, good()))
    assert report.findings == []
    assert report.warnings == []
    assert report.counts == {"runs": 5, "paragraphs": 3, "tables": 0, "thai_language_runs": 5}


def test_cause_1_compat_mode_missing(tmp_path):
    parts = replaced(good(), "word/settings.xml", 'w:val="15"', 'w:val="14"')
    assert codes(check(written(tmp_path, parts))) == {"1"}


def test_cause_1_compat_mode_declared_twice(tmp_path):
    line = '<w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>'
    parts = replaced(good(), "word/settings.xml", line, line.replace("15", "14") + line)
    assert codes(check(written(tmp_path, parts))) == {"1"}


def test_cause_1_no_settings_part(tmp_path):
    parts = good()
    del parts["word/settings.xml"]
    assert codes(check(written(tmp_path, parts))) == {"1"}


def test_cause_2_run_without_cs_element(tmp_path):
    parts = replaced(good(), "word/document.xml", "<w:cs/>", "")
    assert codes(check(written(tmp_path, parts))) == {"2"}


def test_a_language_that_is_not_thai_is_counted_not_a_finding(tmp_path):
    """ADR 0038: the complex-script *language* is `--thai-language`'s to write, so its absence is
    no longer a defect in a file. What the checker does is count the runs that carry it, which is
    what tells a reader whether this document proofs as Thai on a machine that is not set to it."""
    whole = check(written(tmp_path, good())).counts["thai_language_runs"]
    assert whole == 5, "the fixture's runs all carry it"
    for swap in (' w:bidi="ar-SA"', ""):
        parts = replaced(good(), "word/document.xml", ' w:bidi="th-TH"', swap, count=-1)
        report = check(written(tmp_path, parts))
        assert codes(report) == set(), swap
        assert report.counts.get("thai_language_runs", 0) == 0, swap


def test_cause_2_font_attribute_alone_is_not_enough(tmp_path):
    parts = replaced(
        good(), "word/document.xml", "<w:cs/>", '<w:rFonts w:cs="TH Sarabun New"/>'
    )
    report = check(written(tmp_path, parts))
    assert "2" in codes(report)


def test_cause_3_noproof_anywhere(tmp_path):
    parts = replaced(good(), "word/styles.xml", "<w:b/><w:bCs/>", "<w:b/><w:bCs/><w:noProof/>")
    assert codes(check(written(tmp_path, parts))) == {"3"}


def test_cause_4_adjacent_runs_with_same_formatting(tmp_path):
    parts = replaced(good(), "word/document.xml", run("รายการ"), run("ราย") + run("การ"))
    assert codes(check(written(tmp_path, parts))) == {"4"}


def test_cause_4_real_difference_is_not_a_split(tmp_path):
    a = run("ราย", '<w:rFonts w:cs="TH Sarabun New"/>' + RUN_PROPS)
    b = run("การ", RUN_PROPS)
    parts = replaced(good(), "word/document.xml", run("รายการ"), a + b)
    assert "4" not in codes(check(written(tmp_path, parts)))


def test_cause_4_rsid_attributes_do_not_hide_a_split(tmp_path):
    # Word stamps runs with revision ids; two runs that differ only there are
    # the same formatting, and a Thai word split between them is still cause 4.
    a = run("ราย", '<w:rFonts w:cs="TH Sarabun New" w:rsidRPr="00A1"/>' + RUN_PROPS)
    b = run("การ", '<w:rFonts w:cs="TH Sarabun New" w:rsidRPr="00B2"/>' + RUN_PROPS)
    parts = replaced(good(), "word/document.xml", run("รายการ"), a + b)
    assert codes(check(written(tmp_path, parts))) == {"4"}


def test_cause_4_runs_around_a_hyperlink_are_not_adjacent(tmp_path):
    link = '<w:hyperlink r:id="rId9">' + run("ลิงก์") + "</w:hyperlink>"
    parts = replaced(good(), "word/document.xml", run("รายการ"), run("ก่อน ") + link + run(" หลัง"))
    assert "4" not in codes(check(written(tmp_path, parts)))


def test_font_warning_only_where_a_run_holds_thai(tmp_path):
    symbol = '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>' + RUN_PROPS
    parts = replaced(good(), "word/document.xml", run("รายการ"), run("□ ", symbol) + run("รายการ"))
    assert check(written(tmp_path, parts)).warnings == []
    parts = replaced(good(), "word/document.xml", run("รายการ"), run("□ รายการ", symbol))
    assert [x["code"] for x in check(written(tmp_path, parts)).warnings] == ["font"]


def test_cause_5_latin_font_without_cs_font(tmp_path):
    parts = replaced(good(), "word/styles.xml", ' w:cs="TH Sarabun New"', "")
    assert codes(check(written(tmp_path, parts))) == {"5"}


@pytest.mark.parametrize("latin,twin", [("sz", "szCs"), ("b", "bCs"), ("i", "iCs")])
def test_cause_5_twin_missing(tmp_path, latin, twin):
    parts = good()
    if latin == "i":
        parts = replaced(parts, "word/document.xml", BOLD_PROPS, "<w:i/><w:iCs/>" + RUN_PROPS)
    part = "word/document.xml" if latin != "sz" else "word/styles.xml"
    parts = replaced(parts, part, f"<w:{twin}", "<w:vanish", count=1)
    report = check(written(tmp_path, parts))
    assert "5" in codes(report)
    assert any(twin in f["message"] for f in report.findings)


def test_cause_5_symbol_bullet(tmp_path):
    parts = replaced(
        good(), "word/numbering.xml",
        '<w:rFonts w:ascii="TH Sarabun New" w:hAnsi="TH Sarabun New" w:cs="TH Sarabun New"/>',
        '<w:rFonts w:ascii="Symbol" w:hAnsi="Symbol" w:cs="Symbol"/>',
    )
    assert codes(check(written(tmp_path, parts))) == {"5"}


def test_order_in_run_properties(tmp_path):
    parts = replaced(good(), "word/document.xml", "<w:b/><w:bCs/><w:cs/>", "<w:cs/><w:b/><w:bCs/>")
    assert codes(check(written(tmp_path, parts))) == {"order"}


def test_order_in_settings(tmp_path):
    parts = replaced(
        good(), "word/settings.xml", "</w:compat>", "</w:compat><w:hideSpellingErrors/>"
    )
    assert codes(check(written(tmp_path, parts))) == {"order"}


def test_order_in_paragraph_properties(tmp_path):
    parts = replaced(
        good(), "word/styles.xml", "<w:keepNext/><w:outlineLvl w:val=\"0\"/>",
        "<w:outlineLvl w:val=\"0\"/><w:keepNext/>",
    )
    assert codes(check(written(tmp_path, parts))) == {"order"}


@pytest.mark.parametrize("ch", ["​", "‌", "‍", "⁠", "﻿"])
def test_invisible_character_in_text(tmp_path, ch):
    parts = replaced(good(), "word/document.xml", "ข้อความทดสอบ", f"ข้อความ{ch}ทดสอบ")
    assert codes(check(written(tmp_path, parts))) == {"invisible"}


def test_unknown_thai_font_is_a_warning_not_a_finding(tmp_path):
    parts = replaced(good(), "word/styles.xml", 'w:cs="TH Sarabun New"', 'w:cs="Papyrus"')
    report = check(written(tmp_path, parts))
    assert report.ok
    assert [x["code"] for x in report.warnings] == ["font"]


def test_doctype_is_refused_before_parsing(tmp_path):
    parts = replaced(
        good(), "word/settings.xml", "<w:settings",
        '<!DOCTYPE x [<!ENTITY e "e">]><w:settings',
    )
    report = check(written(tmp_path, parts))
    assert codes(report) == {"doctype"}
    assert report.counts == {}, "nothing was parsed after the refusal"


def test_oversized_package_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(check_mod, "MAX_TOTAL", 100)
    assert codes(check(written(tmp_path, good()))) == {"size"}


def test_not_a_docx(tmp_path):
    parts = good()
    del parts["word/document.xml"]
    assert codes(check(written(tmp_path, parts))) == {"package"}
    plain = tmp_path / "x.docx"
    plain.write_bytes(b"not a zip")
    assert codes(check(plain)) == {"package"}


def test_a_path_that_cannot_be_read_is_not_a_damaged_document(tmp_path):
    """A name typed wrong and a Word file that will not open are different problems, and
    only one of them is about the document. `build` has always said which; `check` now does."""
    missing = check(tmp_path / "no-such.docx")
    assert missing.findings == [] and "No such file" in missing.error
    a_directory = check(tmp_path)
    assert a_directory.findings == [] and "Is a directory" in a_directory.error
    # a file that opens and is not a zip is still a finding about the document
    (tmp_path / "x.docx").write_bytes(b"not a zip")
    assert codes(check(tmp_path / "x.docx")) == {"package"}
    assert check(tmp_path / "x.docx").as_dict().get("error") is None


def test_a_comment_is_text_the_reader_sees(tmp_path):
    """Word draws a comment beside the page and its spelling checker reads it, so a Thai run
    in word/comments.xml needs the same marks as one in the body (ADR 0004)."""
    parts = good()
    parts["word/comments.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:comment w:id="1" w:author="a" w:date="2026-01-01T00:00:00Z" w:initials="a">'
        '<w:p><w:r><w:rPr/><w:t>ภาษาไทยในความเห็น</w:t></w:r></w:p></w:comment></w:comments>'
    )
    report = check(written(tmp_path, parts))
    assert codes(report) == {"2"}
    assert [f["part"] for f in report.findings] == ["word/comments.xml"]
    # a comment whose run carries the marks is clean, and its paragraph is counted
    parts["word/comments.xml"] = parts["word/comments.xml"].replace(
        "<w:rPr/>", "<w:rPr>" + RUN_PROPS + "</w:rPr>")
    clean = check(written(tmp_path, parts))
    assert not clean.findings and clean.counts["paragraphs"] == check(written(tmp_path, good())).counts["paragraphs"] + 1


def test_footnotes_are_checked_too(tmp_path):
    parts = good()
    parts["word/footnotes.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>'
        '<w:footnote w:id="1"><w:p><w:r><w:t>เชิงอรรถ</w:t></w:r></w:p></w:footnote></w:footnotes>'
    )
    report = check(written(tmp_path, parts))
    assert codes(report) == {"2"}
    assert report.counts["footnotes"] == 1


# --- red evidence: what generators without this skill produce (ADR 0004, [S2]) ---


def test_legacy_python_docx_default_fails_on_causes_1_2_5():
    report = check(FIXTURES / "legacy-python-docx-default.docx")
    assert codes(report) == {"1", "2", "5"}


def test_legacy_helper_from_handoff_fails_on_1_5_and_order():
    report = check(FIXTURES / "legacy-helper-2026-09-14.docx")
    assert codes(report) == {"1", "5", "order"}
    assert any("declared as 14, 15;" in f["message"] for f in report.findings)


# --- the command as the agent runs it ---


def test_cli_exit_codes_and_json_line(tmp_path):
    path = written(tmp_path, good())
    done = subprocess.run([sys.executable, str(SCRIPT), "check", str(path)], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    out = json.loads(done.stdout)
    assert out["ok"] is True and out["findings"] == []
    assert "ข้อความ" not in done.stdout, "the output never carries document text"

    bad = written(tmp_path, replaced(good(), "word/settings.xml", 'w:val="15"', 'w:val="14"'))
    done = subprocess.run([sys.executable, str(SCRIPT), "check", str(bad)], capture_output=True, text=True)
    assert done.returncode == 1
    assert json.loads(done.stdout)["findings"][0]["code"] == "1"

    done = subprocess.run([sys.executable, str(SCRIPT), "check"], capture_output=True, text=True)
    assert done.returncode == 2
