# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""tools/oracle_set.py: the documents a release is opened in (ADR 0012) — one per
application, the same bytes as the goldens, and a checklist that names them all."""

from __future__ import annotations

import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import oracle_set  # noqa: E402


def test_every_variant_for_every_application_is_its_golden(tmp_path):
    results = oracle_set.write(tmp_path)
    # the five applications open the documents the skill hands over ready to use; the variant
    # built with --auto-numbering is made for Word and is opened there alone (ADR 0036)
    assert sum(len(v[-1]) for v in oracle_set.VARIANTS.values()) == len(results) == 4 * 5 + 1
    assert oracle_set.VARIANTS["sample-auto"][-1] == oracle_set.WORD == ("word365_windows",)
    names = sorted(p.name for p in tmp_path.glob("*.docx"))
    assert names == sorted(f"{v}-{a}.docx" for v, spec in oracle_set.VARIANTS.items() for a in spec[-1])
    checklist = (tmp_path / "CHECKLIST.md").read_text(encoding="utf-8")
    for variant, (_source, _flags, golden, _about, applications) in oracle_set.VARIANTS.items():
        golden_bytes = (ROOT / "tests" / "golden" / f"{golden}.docx").read_bytes()
        for application in applications:
            assert (tmp_path / f"{variant}-{application}.docx").read_bytes() == golden_bytes, (variant, application)
        assert f"## {variant}" in checklist and hashlib.sha256(golden_bytes).hexdigest() in checklist
    for r in results:
        assert r["ok"] and r["findings"] == []
        # the sample's literal LaTeX warns; sample-layout's --toc beside the thesis's own
        # <!-- toc --> writes a second table of contents, and says so (ADR 0028)
        said = [w["message"] for w in r["warnings"]]
        if r["variant"] == "sample-basic":
            # the fixture goes from level 2 to level 5 on purpose, to exercise both in one file;
            # the build says so, and the bytes are the goldens', so the fixture stays as it is
            assert said and all("LaTeX" in m or "a heading of level 5 follows one of level 2" in m for m in said)
            assert sum("heading of level" in m for m in said) == 1
        elif r["variant"] == "sample-layout":
            assert said == ["--toc: the document places a table of contents with <!-- toc --> as well, so it now has two"]
        else:
            assert said == []
    assert all(a in checklist for a in oracle_set.APPLICATIONS)


def test_a_question_is_answered_with_the_usage_and_nothing_is_made(tmp_path, monkeypatch, capsys):
    """`--help` once made a directory named `--help` and stopped with a trace inside it."""
    monkeypatch.chdir(tmp_path)
    for argv in (["--help"], ["-h"], []):
        assert oracle_set.main(argv) == 2
        assert "python3 tools/oracle_set.py OUT_DIR" in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []


def test_the_checklist_asks_whether_two_headings_match():
    """A level-1 heading holding no Thai was placed by its paragraph, not its style, so
    บทคัดย่อ sat centred and Abstract beside it did not; no item of ADR 0012 asked it."""
    assert any("บทคัดย่อ and Abstract" in item for item in oracle_set.SHOWS["sample-options"])


def test_every_item_says_whether_the_page_shows_it(tmp_path):
    """A reading takes long, and an item left for later is an item missed. Every item says whether
    the page as drawn shows it (a PDF the application exports, a screenshot) or only the
    application open does: typing, editing, updating fields, proofing marks, the status bar."""
    oracle_set.write(tmp_path)
    rows = [line for line in (tmp_path / "CHECKLIST.md").read_text(encoding="utf-8").splitlines()
            if line.startswith("| ") and not line.startswith(("| item", "|---"))]
    assert rows and all(line.split(" | ")[1] in ("page", "open") for line in rows)
    assert oracle_set.how_read("Bold and italic render on Thai") == "page"
    assert oracle_set.how_read("Captions read ตารางที่ 1-1, รูปที่ 2-1, ตารางที่ ก-1 — before and after updating fields") == "open"
    for item in (*oracle_set.WORD_ONLY, *oracle_set.SHOWS["sample-auto"][1:]):
        assert oracle_set.how_read(item) == "open" or item.startswith("(Word only)"), item


def test_libreoffice_renders_with_a_profile_that_reads_thai(tmp_path, monkeypatch, capsys):
    """tools/render_libreoffice.py exports what LibreOffice draws, for the items a page shows.
    LibreOffice is found on the PATH, as a flatpak, or where THAI_DOCX_SOFFICE says, and runs
    with a profile of its own whose complex text is Thai — an English installation's is Hindi,
    which underlines every Thai word."""
    import render_libreoffice as rl
    assert rl.soffice({"THAI_DOCX_SOFFICE": "flatpak run org.libreoffice.LibreOffice"}) == [
        "flatpak", "run", "org.libreoffice.LibreOffice"]
    home = rl.profile(tmp_path)
    assert "<value>th-TH</value>" in (home / "user" / "registrymodifications.xcu").read_text(encoding="utf-8")
    assert "DefaultLocale_CTL" in (home / "user" / "registrymodifications.xcu").read_text(encoding="utf-8")
    ran = []
    monkeypatch.setattr(rl, "soffice", lambda env=None: ["soffice"])
    monkeypatch.setattr(rl.shutil, "which", lambda name: None)  # no pdftoppm: the PDFs alone
    monkeypatch.setattr(rl.subprocess, "run", lambda args, **kw: ran.append(args))
    (tmp_path / "a-libreoffice_writer.docx").write_bytes(b"x")
    (tmp_path / "a-wps_writer.docx").write_bytes(b"x")
    assert rl.main([str(tmp_path), "--match", "*-libreoffice_writer.docx"]) == 0
    assert len(ran) == 1 and ran[0][0] == "soffice" and "--headless" in ran[0]
    assert ran[0][1].startswith("-env:UserInstallation=file://") and ran[0][-1].endswith("a-libreoffice_writer.docx")
    assert not any(a.endswith("a-wps_writer.docx") for a in ran[0])
    capsys.readouterr()
    assert rl.main(["--help"]) == 2 and "render_libreoffice.py DIR" in capsys.readouterr().out
