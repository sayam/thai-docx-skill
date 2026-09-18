# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Repair: the attributes that break Thai, never the text (ADR 0032; gate
`repair-changes-only-what-it-names`). This version repairs findings 1 and 3 and reports
every other one.
"""

from __future__ import annotations

import pathlib
import zipfile

import pytest

from docx_fixture import good, pack, replaced, run
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
    assert result["ok"] and result["repaired"] == {"1": 1} and result["remaining"] == []
    assert check(out).findings == []


def test_a_second_compatibility_mode_is_dropped(tmp_path):
    twice = replaced(good(), "word/settings.xml", "</w:compat>",
                     '<w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="14"/></w:compat>')
    src = written(tmp_path, twice)
    assert codes(check(src).findings) == {"1": 1}
    result = rp.repair(str(src), str(tmp_path / "out.docx"))
    assert result["ok"] and result["repaired"] == {"1": 1}
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
    assert result["repaired"] == {"1": 1, "3": 1} and check(out).findings == []


# --- what it must not do -------------------------------------------------------------


def test_the_text_comes_through_character_for_character(tmp_path):
    src = FIXTURES / "legacy-python-docx-default.docx"
    out = tmp_path / "out.docx"
    result = rp.repair(str(src), str(out))
    assert result["ok"]
    before, after = parts_of(src), parts_of(out)
    assert docx_text(before, 0) == docx_text(after, 0)


def test_every_part_it_did_not_write_keeps_its_bytes(tmp_path):
    """ADR 0032: everything untouched comes through byte for byte, still compressed."""
    src = FIXTURES / "legacy-python-docx-default.docx"
    b = src.read_bytes()
    out = tmp_path / "out.docx"
    assert rp.repair(str(src), str(out))["ok"]
    got = out.read_bytes()
    before = {e.name: e for e in pk.entries(b)}
    for e in pk.entries(got):
        if e.name == "word/settings.xml":
            continue
        assert pk.raw(got, e) == pk.raw(b, before[e.name]), e.name
        assert (e.method, e.crc) == (before[e.name].method, before[e.name].crc), e.name


def test_findings_this_version_does_not_repair_are_reported_and_left(tmp_path):
    """A file whose only fault is one this version does not make: nothing is written."""
    parts = replaced(good(), "word/document.xml", run("ข้อความทดสอบ "), "<w:r><w:rPr/><w:t>ข้อความทดสอบ </w:t></w:r>")
    src = written(tmp_path, parts)
    out = tmp_path / "out.docx"
    result = rp.repair(str(src), str(out))
    assert not result["ok"] and not out.exists()
    assert "nothing here is a repair this version makes" in result["error"]
    assert "2" in codes(result["remaining"])


def test_a_clean_file_is_left_alone(tmp_path):
    src = GOLDEN / "sample-default.docx"
    out = tmp_path / "out.docx"
    result = rp.repair(str(src), str(out))
    assert not result["ok"] and not out.exists() and result["remaining"] == []


def test_repairing_a_repaired_file_changes_nothing(tmp_path):
    """Idempotent, as ADR 0032 requires: the second run has nothing left to do."""
    once = tmp_path / "once.docx"
    assert rp.repair(str(FIXTURES / "legacy-python-docx-default.docx"), str(once))["ok"]
    twice = tmp_path / "twice.docx"
    result = rp.repair(str(once), str(twice))
    assert not result["ok"] and not twice.exists()


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


@pytest.mark.parametrize("argv", [[], ["one.docx"], ["a", "b", "c"]])
def test_the_command_takes_two_paths(argv, capsys):
    assert rp.main(argv) == 2
    assert rp.USAGE in capsys.readouterr().out


def test_exit_codes_say_what_happened(tmp_path, capsys):
    """0: repaired, nothing left. 1: repaired, findings remain. 2: nothing written."""
    clean = replaced(good(), "word/settings.xml", 'w:val="15"', 'w:val="14"')
    assert rp.main([str(written(tmp_path, clean)), str(tmp_path / "a.docx")]) == 0
    capsys.readouterr()
    assert rp.main([str(FIXTURES / "legacy-python-docx-default.docx"), str(tmp_path / "b.docx")]) == 1
    capsys.readouterr()
    assert rp.main([str(GOLDEN / "sample-default.docx"), str(tmp_path / "c.docx")]) == 2


def test_the_file_it_writes_is_a_package_another_reader_opens(tmp_path):
    out = tmp_path / "out.docx"
    assert rp.repair(str(FIXTURES / "legacy-helper-2026-09-14.docx"), str(out))["ok"]
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        assert b'w:val="15"' in z.read("word/settings.xml")
