"""`thai_docx build`: faithful to the Markdown (ADR 0005), the same bytes every
run (ADR 0008), and never a file that fails its own checker (ADR 0007).
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import zipfile

import pytest

from thai_docx import build as b
from thai_docx import markdown as md
from thai_docx.check import check

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "thai-docx" / "scripts" / "thai_docx"
FIXTURES = ROOT / "tests" / "fixtures"
GOLDEN = ROOT / "tests" / "golden"
ALL_FLAGS = ["--toc", "--page-numbers", "--hide-spelling-errors", "--align", "thai", "--paper", "letter", "--size", "15", "--margins", "1,1,1,1"]


def run_cli(*args) -> tuple[int, dict]:
    done = subprocess.run([sys.executable, str(SCRIPT), "build", *map(str, args)], capture_output=True, text=True)
    assert done.stderr == "", done.stderr
    return done.returncode, json.loads(done.stdout)


def build(tmp_path, text: str, **opts) -> tuple[dict, pathlib.Path]:
    src = tmp_path / "in.md"
    src.write_text(text, encoding="utf-8")
    out = tmp_path / "out.docx"
    o = dict(b.DEFAULTS)
    o.update(opts)
    return b.build(src, out, o, []), out


# --- goldens: the same bytes, every run, every machine (ADR 0008) ---


@pytest.mark.parametrize("name,flags", [("sample-default", []), ("sample-all-flags", ALL_FLAGS)])
def test_sample_matches_golden_bytes(tmp_path, name, flags):
    out = tmp_path / f"{name}.docx"
    code, result = run_cli(FIXTURES / "sample.md", out, *flags)
    assert code == 0 and result["ok"], result
    golden = (GOLDEN / f"{name}.docx").read_bytes()
    assert out.read_bytes() == golden, "output differs from the committed golden — a deliberate change regenerates the golden and says so in the commit"
    assert result["sha256"] == hashlib.sha256(golden).hexdigest()


def test_zip_entries_are_stored_with_fixed_metadata():
    with zipfile.ZipFile(GOLDEN / "sample-default.docx") as zf:
        names = [i.filename for i in zf.infolist()]
        assert names[0] == "[Content_Types].xml"
        for info in zf.infolist():
            assert info.compress_type == zipfile.ZIP_STORED
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
            assert info.create_system == 0


def test_docprops_carry_only_front_matter(tmp_path):
    _, out = build(tmp_path, "---\ntitle: ชื่อ\nauthor: ผู้เขียน\n---\n\nก")
    core = zipfile.ZipFile(out).read("docProps/core.xml").decode()
    assert "<dc:title>ชื่อ</dc:title><dc:creator>ผู้เขียน</dc:creator>" in core
    assert "created" not in core and "modified" not in core
    _, out = build(tmp_path, "ก")
    assert zipfile.ZipFile(out).read("docProps/core.xml").decode().endswith("></cp:coreProperties>")


# --- fidelity (ADR 0005) ---


def test_sample_text_round_trips_paragraph_for_paragraph():
    doc = md.parse((FIXTURES / "sample.md").read_text(encoding="utf-8"))
    with zipfile.ZipFile(GOLDEN / "sample-default.docx") as zf:
        parts = {n: zf.read(n) for n in zf.namelist()}
    assert b.docx_text(parts, len(doc.footnote_order)) == b.expected_text(doc)
    assert "☐ งานที่ยังไม่ทำ" in b.docx_text(parts, 1)


def test_a_writer_that_drops_a_character_is_refused(tmp_path, monkeypatch):
    original = b.Writer.text_run

    def lossy(self, node, extra=""):
        node = dict(node, s=node["s"][:-1]) if node["s"].endswith("ข") else node
        return original(self, node, extra)

    monkeypatch.setattr(b.Writer, "text_run", lossy)
    result, out = build(tmp_path, "กข")
    assert not result["ok"] and [f["code"] for f in result["findings"]] == ["fidelity"]
    assert "กข" not in json.dumps(result, ensure_ascii=False), "a finding never quotes the document"
    assert not out.exists(), "nothing is written when the check fails"


def test_a_writer_that_breaks_a_cause_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(b, "LANG", "<w:cs/>")
    result, out = build(tmp_path, "ก")
    assert not result["ok"] and {f["code"] for f in result["findings"]} == {"2"}
    assert not out.exists()


def test_empty_heading_is_still_a_paragraph_with_text(tmp_path):
    result, out = build(tmp_path, "#\n\nก")
    assert result["ok"]
    assert '<w:t xml:space="preserve"></w:t>' in zipfile.ZipFile(out).read("word/document.xml").decode()


def test_special_characters_are_escaped(tmp_path):
    result, out = build(tmp_path, 'a & b < c > "d" [e](https://x.example/?a=1&b=2)')
    assert result["ok"]
    doc = zipfile.ZipFile(out).read("word/document.xml").decode()
    assert "a &amp; b &lt; c &gt; \"d\" " in doc
    assert 'Target="https://x.example/?a=1&amp;b=2"' in zipfile.ZipFile(out).read("word/_rels/document.xml.rels").decode()


# --- images and the script limits (ADR 0010, 0011) ---


def test_image_outside_the_markdown_directory_is_refused_unless_allowed(tmp_path):
    other = tmp_path / "elsewhere"
    other.mkdir()
    shutil.copy(FIXTURES / "pixel.png", other / "p.png")
    src_dir = tmp_path / "doc"
    src_dir.mkdir()
    src = src_dir / "in.md"
    src.write_text("![alt](../elsewhere/p.png)", encoding="utf-8")
    out = tmp_path / "out.docx"
    result = b.build(src, out, dict(b.DEFAULTS), [])
    assert "outside" in result["error"] and not out.exists()
    result = b.build(src, out, dict(b.DEFAULTS), [other])
    assert result["ok"] and result["counts"]["images"] == 1


def test_remote_and_non_image_files_are_refused(tmp_path):
    (tmp_path / "fake.png").write_bytes(b"GIF89a not really")
    assert "remote" in build(tmp_path, "![a](https://x.example/p.png)")[0]["error"]
    assert "not a PNG or JPEG" in build(tmp_path, "![a](fake.png)")[0]["error"]
    assert "No such file" in build(tmp_path, "![a](missing.png)")[0]["error"]


def test_image_is_scaled_to_the_text_width(tmp_path):
    shutil.copy(FIXTURES / "pixel.png", tmp_path / "p.png")
    _, out = build(tmp_path, "![a](p.png)", margins=(1, 3.5, 1, 3.5))
    doc = zipfile.ZipFile(out).read("word/document.xml").decode()
    text_width_emu = (b.PAPER["a4"][0] - 2 * int(3.5 * 1440)) * b.EMU_PER_TWIP  # narrower than 200 px
    cx, cy = text_width_emu, 50 * b.EMU_PER_PX * text_width_emu // (200 * b.EMU_PER_PX)
    assert f'cx="{cx}" cy="{cy}"' in doc


def test_jpeg_dimensions_are_read_from_sof():
    jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\xff\xc0\x00\x11\x08\x00\x20\x00\x40\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01" + b"\xff\xd9"
    assert b._image_size(jpeg) == ("jpeg", 64, 32)


def test_unreferenced_footnote_is_refused(tmp_path):
    result, _ = build(tmp_path, "ก\n\n[^x]: never used")
    assert "never referenced" in result["error"]


# --- settings (ADR 0009) ---


def test_defaults_are_announced_and_flags_change_the_package(tmp_path):
    result, out = build(tmp_path, "ก")
    assert result["settings"] == {
        "font": "TH Sarabun New", "size_pt": 16, "paper": "a4",
        "margins_in": {"top": 1.0, "right": 1.0, "bottom": 1.0, "left": 1.5},
        "align": "left", "toc": False, "page_numbers": False, "hide_spelling_errors": False,
    }
    settings = zipfile.ZipFile(out).read("word/settings.xml").decode()
    assert "hideSpellingErrors" not in settings and "updateFields" not in settings

    result, out = build(tmp_path, "ก", font="Sarabun", size=14, hide_spelling_errors=True, toc=True, page_numbers=True, align="thai")
    assert result["ok"] and result["warnings"] == []
    with zipfile.ZipFile(out) as zf:
        settings, styles, doc = (zf.read(f"word/{n}.xml").decode() for n in ("settings", "styles", "document"))
        assert "<w:hideSpellingErrors/><w:hideGrammaticalErrors/>" in settings and '<w:updateFields w:val="true"/>' in settings
        assert 'w:cs="Sarabun"' in styles and '<w:sz w:val="28"/><w:szCs w:val="28"/>' in styles and 'thaiDistribute' in styles
        assert "TOC \\o" in doc and "headerReference" in doc and " PAGE " in zf.read("word/header1.xml").decode()


def test_unknown_font_is_a_warning_and_still_builds(tmp_path):
    result, out = build(tmp_path, "ก", font="Papyrus")
    assert result["ok"] and [x["code"] for x in result["warnings"]] == ["font"]


# --- the command as the agent runs it (ADR 0007) ---


def test_cli_exit_codes(tmp_path):
    src = tmp_path / "in.md"
    src.write_text("ก <span>x</span>", encoding="utf-8")
    code, result = run_cli(src, tmp_path / "o.docx")
    assert code == 2 and result["line"] == 1 and "not supported" in result["error"]
    code, result = run_cli(src, tmp_path / "o.docx", "--margins", "1,2")
    assert code == 2 and "four" in result["error"]
    src.write_text("ข้อความทดสอบ", encoding="utf-8")
    code, result = run_cli(src, tmp_path / "o.docx")
    assert code == 0 and result["ok"] and (tmp_path / "o.docx").exists()
    assert "ข้อความทดสอบ" not in json.dumps(result, ensure_ascii=False)
    assert check(tmp_path / "o.docx").ok
