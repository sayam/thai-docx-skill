# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Repair: the attributes that break Thai, never the text (ADR 0037; gate
`repair-changes-only-what-it-names`). This version repairs findings 1 and 3 and reports
every other one.
"""

from __future__ import annotations

import json
import re
import pathlib
import zipfile

import pytest

from docx_fixture import good, pack, replaced, run
from thai_docx import ooxml
from thai_docx import package as pk
from thai_docx import repair as rp
from thai_docx.check import check
from thai_docx.fidelity import docx_text

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
GOLDEN = ROOT / "tests" / "golden"


def written(tmp_path, parts: dict[str, str], name: str = "in.docx") -> pathlib.Path:
    path = tmp_path / name
    path.write_bytes(pack(parts))
    return path


def parts_of(path) -> dict[str, bytes]:
    b = pathlib.Path(path).read_bytes()
    return {e.name: pk.read(b, e) for e in pk.entries(b)}


def codes(findings) -> dict[str, int]:
    out: dict[str, int] = {}
    for f in findings:
        out[f["code"]] = out.get(f["code"], 0) + 1
    return out


# --- what it repairs -----------------------------------------------------------------


def test_a_compatibility_mode_that_is_not_15_is_set_to_15(tmp_path):
    src = written(tmp_path, replaced(good(), "word/settings.xml", 'w:val="15"', 'w:val="14"'))
    out = tmp_path / "out.docx"
    assert codes(check(src).findings) == {"1": 1}
    result = rp.repair(str(src), str(out))
    assert result["ok"] and result["repaired"] == {"1": 1, "unmarked": 1} and result["remaining"] == []
    assert check(out).findings == []


def test_a_second_compatibility_mode_is_dropped(tmp_path):
    twice = replaced(good(), "word/settings.xml", "</w:compat>",
                     '<w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="14"/></w:compat>')
    src = written(tmp_path, twice)
    assert codes(check(src).findings) == {"1": 1}
    result = rp.repair(str(src), str(tmp_path / "out.docx"))
    assert result["ok"] and result["repaired"] == {"1": 1, "unmarked": 1}
    settings = parts_of(tmp_path / "out.docx")["word/settings.xml"]
    assert settings.count(b"compatibilityMode") == 1 and b'w:val="15"' in settings
    assert check(tmp_path / "out.docx").findings == []


def test_no_proof_is_removed_wherever_it_hides(tmp_path):
    """The checker reads it in any part under word/, so the repair does too."""
    parts = replaced(good(), "word/styles.xml", "<w:b/><w:bCs/>", "<w:b/><w:bCs/><w:noProof/>")
    parts = replaced(parts, "word/document.xml", "<w:rPr>", '<w:rPr><w:noProof w:val="true"/>', count=1)
    src = written(tmp_path, parts)
    assert "3" in codes(check(src).findings)
    out = tmp_path / "out.docx"
    result = rp.repair(str(src), str(out))
    assert result["ok"] and result["repaired"]["3"] == 2
    after = parts_of(out)
    assert not any(b"noProof" in xml for xml in after.values())
    assert check(out).findings == []


def test_both_findings_at_once(tmp_path):
    parts = replaced(good(), "word/settings.xml", 'w:val="15"', 'w:val="14"')
    parts = replaced(parts, "word/styles.xml", "<w:b/><w:bCs/>", "<w:b/><w:bCs/><w:noProof/>")
    out = tmp_path / "out.docx"
    result = rp.repair(str(written(tmp_path, parts)), str(out))
    assert result["repaired"] == {"1": 1, "3": 1, "unmarked": 1} and check(out).findings == []


def test_properties_out_of_order_are_put_back_in_it(tmp_path):
    """The schema fixes the order of a run's and a paragraph's properties, and Word ignores
    one that comes in the wrong place. Repairing it moves nothing else."""
    parts = replaced(good(), "word/document.xml", '<w:cs/><w:lang w:val="en-US" w:bidi="th-TH"/>',
                     '<w:lang w:val="en-US" w:bidi="th-TH"/><w:cs/>')
    src = written(tmp_path, parts)
    assert codes(check(src).findings) == {"order": 1}
    out = tmp_path / "out.docx"
    result = rp.repair(str(src), str(out))
    assert result["ok"] and result["repaired"] == {"order": 1, "unmarked": 1}
    assert check(out).findings == []


def test_an_element_the_schema_does_not_name_keeps_its_place():
    """The checker skips an extension element, so moving one would change more than the
    finding asked for. The ordered ones fill the places they already occupied."""
    mixed = b'<w:rPr><w:sz w:val="32"/><w:somethingElse/><w:b/></w:rPr>'
    out, n = rp.reorder(mixed, b"w:rPr", ooxml.RPR_ORDER)
    assert n == 1
    assert out == b'<w:rPr><w:b/><w:somethingElse/><w:sz w:val="32"/></w:rPr>'


def test_two_children_of_one_name_keep_the_order_they_were_written_in():
    twice = b'<w:rPr><w:sz w:val="32"/><w:b w:val="1"/><w:b w:val="0"/></w:rPr>'
    out, _n = rp.reorder(twice, b"w:rPr", ooxml.RPR_ORDER)
    assert out == b'<w:rPr><w:b w:val="1"/><w:b w:val="0"/><w:sz w:val="32"/></w:rPr>'


def test_properties_already_in_order_are_not_touched():
    right = b'<w:rPr><w:b/><w:sz w:val="32"/></w:rPr>'
    assert rp.reorder(right, b"w:rPr", ooxml.RPR_ORDER) == (right, 0)


# --- what it must not do -------------------------------------------------------------


def test_the_text_comes_through_character_for_character(tmp_path):
    src = FIXTURES / "legacy-python-docx-default.docx"
    out = tmp_path / "out.docx"
    result = rp.repair(str(src), str(out))
    assert result["ok"]
    before, after = parts_of(src), parts_of(out)
    assert docx_text(before, 0) == docx_text(after, 0)


def test_every_part_it_did_not_write_keeps_its_bytes(tmp_path):
    """ADR 0037: everything untouched comes through byte for byte, still compressed."""
    src = FIXTURES / "legacy-python-docx-default.docx"
    b = src.read_bytes()
    out = tmp_path / "out.docx"
    assert rp.repair(str(src), str(out))["ok"]
    got = out.read_bytes()
    before = {e.name: e for e in pk.entries(b)}
    rewritten = {"word/document.xml", "word/styles.xml", "word/settings.xml", "word/numbering.xml"}
    kept = 0
    for e in pk.entries(got):
        was = before[e.name]
        if e.name in rewritten:
            assert pk.raw(got, e) != pk.raw(b, was), e.name
            continue
        kept += 1
        assert pk.raw(got, e) == pk.raw(b, was), e.name
        assert (e.method, e.crc, e.mod) == (was.method, was.crc, was.mod), e.name
    assert kept == 13, kept


def test_the_repaired_file_is_about_the_size_it_was(tmp_path):
    """The parts it rewrites are compressed, not stored: a repaired document is not many
    times larger than the one the user handed over."""
    src = FIXTURES / "legacy-python-docx-default.docx"
    out = tmp_path / "out.docx"
    assert rp.repair(str(src), str(out))["ok"]
    assert out.stat().st_size < 1.2 * src.stat().st_size, (out.stat().st_size, src.stat().st_size)


def test_findings_this_version_does_not_repair_are_reported_and_left(tmp_path):
    """A word split across two runs (code 4) waits for v0.3: nothing is written for it.

    The file is repaired once first, because every document written before ADR 0039 carries the
    complex-script marker in its defaults and taking that off is a repair of its own. What is
    left after that is the split word alone, and that is what this holds.
    """
    parts = replaced(good(), "word/document.xml", run("รายการ"), run("ราย") + run("การ"))
    src = written(tmp_path, parts)
    once = tmp_path / "once.docx"
    assert rp.repair(str(src), str(once))["repaired"] == {"unmarked": 1}
    out = tmp_path / "out.docx"
    result = rp.repair(str(once), str(out))
    assert not result["ok"] and not out.exists()
    assert "nothing here is a repair this version makes" in result["error"]
    assert codes(result["remaining"]) == {"4": 1}  # a split word waits for v0.3


def test_a_run_with_no_marks_at_all_is_marked(tmp_path):
    """Code 2, the commonest finding: the run is marked complex script, in schema order. The
    complex-script *language* is not written unless it is asked for (ADR 0038): it is what makes
    WPS Writer misplace ำ, and what a machine without Thai needs."""
    parts = replaced(good(), "word/document.xml", run("ข้อความทดสอบ "), "<w:r><w:t>ข้อความทดสอบ </w:t></w:r>")
    out = tmp_path / "out.docx"
    result = rp.repair(str(written(tmp_path, parts)), str(out))
    assert result["ok"] and result["repaired"] == {"2": 1, "unmarked": 1} and result["remaining"] == []
    document = parts_of(out)["word/document.xml"]
    assert b"<w:rPr><w:cs/></w:rPr><w:t>" in document and b'w:bidi="th-TH"/></w:rPr><w:t>' not in document
    assert check(out).findings == []
    assert [w["code"] for w in result["warnings"] if w["code"] == "thai-language"] == []

    asked = tmp_path / "asked.docx"
    result = rp.repair(str(written(tmp_path, parts)), str(asked), None, True)
    assert result["ok"] and result["repaired"] == {"2": 1, "unmarked": 1}
    assert b'<w:rPr><w:cs/><w:lang w:bidi="th-TH"/></w:rPr><w:t>' in parts_of(asked)["word/document.xml"]
    said = [w["message"] for w in result["warnings"] if w["code"] == "thai-language"]
    assert said == ['the Thai complex-script language w:bidi="th-TH" was written into 1 run properties,'
                    " as --thai-language asked"], result["warnings"]
    assert check(asked).findings == []


def test_a_latin_property_gets_its_complex_script_twin(tmp_path):
    parts = replaced(good(), "word/styles.xml", '<w:sz w:val="40"/><w:szCs w:val="40"/>', '<w:sz w:val="40"/>')
    out = tmp_path / "out.docx"
    result = rp.repair(str(written(tmp_path, parts)), str(out))
    assert result["ok"] and result["repaired"] == {"5": 1, "unmarked": 1}
    assert b'<w:sz w:val="40"/><w:szCs w:val="40"/>' in parts_of(out)["word/styles.xml"]


def test_the_font_for_a_run_that_names_none_is_chosen_and_reported(tmp_path):
    """ADR 0037's order: what the command was given, else the document's own, else ours."""
    parts = replaced(good(), "word/document.xml", "<w:rPr>", '<w:rPr><w:rFonts w:ascii="Calibri"/>', count=1)
    src = written(tmp_path, parts)
    out = tmp_path / "out.docx"

    asked = rp.repair(str(src), str(out), "Noto Sans Thai")
    assert b'w:cs="Noto Sans Thai"' in parts_of(out)["word/document.xml"]
    assert "the font the command was given" in asked["warnings"][0]["message"]
    assert "Noto Sans Thai" in asked["warnings"][0]["message"]

    out.unlink()
    its_own = rp.repair(str(src), str(out))
    # the fixture's docDefaults already name TH Sarabun New as the complex-script font
    assert b'w:cs="TH Sarabun New"' in parts_of(out)["word/document.xml"]
    assert "the complex-script font this document uses most" in its_own["warnings"][0]["message"]


def test_a_symbol_bullet_gets_a_font_with_thai_in_it(tmp_path):
    parts = replaced(good(), "word/numbering.xml", '<w:rFonts w:ascii="TH Sarabun New" w:hAnsi="TH Sarabun New" w:cs="TH Sarabun New"/>',
                     '<w:rFonts w:ascii="Symbol" w:hAnsi="Symbol" w:cs="Symbol"/>')
    out = tmp_path / "out.docx"
    result = rp.repair(str(written(tmp_path, parts)), str(out))
    assert result["ok"] and result["repaired"]["5"] >= 1
    assert b"Symbol" not in parts_of(out)["word/numbering.xml"]


def test_a_clean_file_is_left_alone(tmp_path):
    """Nothing to repair is an answer, not a fault: ok, exit 0, and no file written — an agent
    told `error` here would tell the user the file cannot be repaired, when it needs nothing."""
    src = GOLDEN / "sample-default.docx"
    out = tmp_path / "out.docx"
    result = rp.repair(str(src), str(out))
    assert result["ok"] and not out.exists() and result["remaining"] == [] and "file" not in result
    assert result["warnings"][0]["code"] == "clean" and "error" not in result


def test_repairing_a_repaired_file_changes_nothing(tmp_path):
    """Idempotent, as ADR 0037 requires: the second run has nothing left to do."""
    once = tmp_path / "once.docx"
    assert rp.repair(str(FIXTURES / "legacy-python-docx-default.docx"), str(once))["ok"]
    twice = tmp_path / "twice.docx"
    result = rp.repair(str(once), str(twice))
    assert result["repaired"] == {} and result["warnings"][0]["code"] == "clean" and not twice.exists()


def test_a_file_it_cannot_read_is_refused_not_repaired(tmp_path):
    out = tmp_path / "out.docx"
    assert "No such file" in rp.repair(str(tmp_path / "no-such.docx"), str(out))["error"]
    (tmp_path / "x.docx").write_bytes(b"not a zip")
    assert "not a zip package" in rp.repair(str(tmp_path / "x.docx"), str(out))["error"]
    doctype = good()
    doctype["word/document.xml"] = '<?xml version="1.0"?><!DOCTYPE w:document []>' + doctype["word/document.xml"]
    assert "DOCTYPE" in rp.repair(str(written(tmp_path, doctype, "d.docx")), str(out))["error"]
    assert not out.exists()


# --- the command ---------------------------------------------------------------------


@pytest.mark.parametrize("argv", [[], ["one.docx"], ["a", "b", "c"], ["a", "b", "--font"], ["a", "b", "--size", "14"]])
def test_the_command_takes_two_paths_and_one_flag(argv, capsys):
    assert rp.main(argv) == 2
    assert json.loads(capsys.readouterr().out)["error"] == rp.USAGE


def test_exit_codes_say_what_happened(tmp_path, capsys):
    """0: repaired, nothing left — or nothing to repair. 1: repaired, findings remain. 2: the
    input or the output is at fault, and nothing was written."""
    clean = replaced(good(), "word/settings.xml", 'w:val="15"', 'w:val="14"')
    assert rp.main([str(written(tmp_path, clean)), str(tmp_path / "a.docx")]) == 0
    capsys.readouterr()
    four = replaced(good(), "word/document.xml", run("รายการ"), run("ราย") + run("การ"))
    four = replaced(four, "word/settings.xml", 'w:val="15"', 'w:val="14"')
    assert rp.main([str(written(tmp_path, four, "four.docx")), str(tmp_path / "b.docx")]) == 1
    capsys.readouterr()
    assert rp.main([str(GOLDEN / "sample-default.docx"), str(tmp_path / "c.docx")]) == 0
    assert not (tmp_path / "c.docx").exists()
    capsys.readouterr()
    assert rp.main([str(tmp_path / "missing.docx"), str(tmp_path / "d.docx")]) == 2


def test_the_file_it_writes_is_a_package_another_reader_opens(tmp_path):
    out = tmp_path / "out.docx"
    assert rp.repair(str(FIXTURES / "legacy-helper-2026-09-14.docx"), str(out))["ok"]
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        assert b'w:val="15"' in z.read("word/settings.xml")


# --- ADR 0039: the marker where the text is complex script, and only there ---


def _runs_of(path) -> list[tuple[str, bool]]:
    """Every run of word/document.xml that holds text: (its text, whether it is marked)."""
    doc = parts_of(path)["word/document.xml"].decode("utf-8")
    out = []
    for raw in re.findall(r"<w:r>.*?</w:r>", doc, re.S):
        text = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", raw, re.S))
        if text:
            out.append((text, "<w:cs/>" in raw))
    return out


def test_a_run_of_latin_loses_the_marker(tmp_path):
    """Cause 2 as ADR 0039 restates it: a run whose text is not complex script must not say it
    is, or Word proofs English with a complex-script language and underlines every word."""
    parts = replaced(good(), "word/document.xml", run("รายการ"), run("รายการ") + run("Markdown"))
    out = tmp_path / "out.docx"
    result = rp.repair(str(written(tmp_path, parts)), str(out))
    runs = _runs_of(out)
    assert result["ok"] and check(out).findings == []
    assert ("รายการ", True) in runs and ("Markdown", False) in runs
    # and the rule in general, over every run the fixture holds
    assert [text for text, marked in runs if marked and not any(ooxml.is_thai(ch) for ch in text)] == []


def test_a_run_of_both_scripts_is_cut_where_the_script_changes(tmp_path):
    """The half no attribute could reach: English that shares a run with Thai. The run is cut,
    and the text is the same to the character — repair may not touch it (ADR 0023)."""
    parts = replaced(good(), "word/document.xml", run("รายการ"), run("รายการ Markdown และ XML"))
    src = written(tmp_path, parts)
    out = tmp_path / "out.docx"
    result = rp.repair(str(src), str(out))
    runs = _runs_of(out)
    at = runs.index(("รายการ ", True))
    assert result["ok"] and check(out).findings == []
    assert runs[at:at + 4] == [("รายการ ", True), ("Markdown ", False), ("และ ", True), ("XML", False)]
    assert result["repaired"]["split"] == 1
    assert "".join(text for text, _ in runs[at:at + 4]) == "รายการ Markdown และ XML"


def test_the_marker_comes_off_the_chain_or_leaving_it_off_a_run_means_nothing(tmp_path):
    """w:cs inherits: docDefaults, then the styles, then the run. A run that leaves it off is
    only saying "whatever the chain says", so taking it off the run and leaving it in the
    defaults would repair nothing at all."""
    out = tmp_path / "out.docx"
    assert rp.repair(str(written(tmp_path, good())), str(out))["ok"]
    styles = parts_of(out)["word/styles.xml"].decode("utf-8")
    assert "<w:cs/>" not in styles


def test_asked_for_the_whole_document_the_marker_stays_on_every_run(tmp_path):
    """--force-cs-whole-doc is the shape releases before 0.2.0 wrote: every run marked, the
    chain left as it was, and no run cut. The run starts with no marker at all, which is
    finding 2 either way — what the flag changes is the shape the repair leaves behind."""
    parts = replaced(good(), "word/document.xml", run("รายการ"), run("รายการ Markdown", ""))
    out = tmp_path / "out.docx"
    result = rp.repair(str(written(tmp_path, parts)), str(out), cs_all=True)
    assert result["ok"] and ("รายการ Markdown", True) in _runs_of(out)
    assert all(marked for _text, marked in _runs_of(out))
    assert "split" not in result["repaired"] and "unmarked" not in result["repaired"]
    assert "<w:cs/>" in parts_of(out)["word/styles.xml"].decode("utf-8")


def test_a_run_a_split_may_not_touch_is_left_whole(tmp_path):
    """Only the plain shape is cut. A numeric character reference cannot survive being written
    again, so a run whose text holds one keeps its own run, marker and all."""
    mixed = run("ก&#x20;Word")
    parts = replaced(good(), "word/document.xml", run("รายการ"), mixed)
    out = tmp_path / "out.docx"
    result = rp.repair(str(written(tmp_path, parts)), str(out))
    assert result["ok"] and "split" not in result["repaired"]
    assert ("ก&#x20;Word", True) in _runs_of(out)
