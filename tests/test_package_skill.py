"""What a person who only uses the skill receives (ADR 0018): the skill directory and
nothing else, the same bytes on every run, and one version everywhere it is stated.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = [sys.executable, str(ROOT / "tools" / "package_skill.py")]
sys.path.insert(0, str(ROOT / "tools"))
import package_skill  # noqa: E402


def test_archive_holds_the_skill_directory_and_nothing_else(tmp_path):
    out = tmp_path / "a.zip"
    assert subprocess.run(TOOL + [str(out)], capture_output=True).returncode == 0
    names = zipfile.ZipFile(out).namelist()
    on_disk = sorted(
        "thai-docx/" + p.relative_to(ROOT / "skills" / "thai-docx").as_posix()
        for p in (ROOT / "skills" / "thai-docx").rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    )
    assert sorted(names) == on_disk
    assert {"thai-docx/SKILL.md", "thai-docx/LICENSE.txt", "thai-docx/scripts/thai_docx.js", "thai-docx/scripts/thai_docx/__main__.py"} <= set(names)
    for kept_out in ("tools/", "tests/", "docs/", "gates.yaml", ".github/", "__pycache__"):
        assert not any(kept_out in n for n in names), kept_out


def test_archive_is_the_same_bytes_on_every_run(tmp_path, monkeypatch):
    for name in ("a.zip", "b.zip"):
        subprocess.run(TOOL + [str(tmp_path / name)], check=True, capture_output=True)
    assert (tmp_path / "a.zip").read_bytes() == (tmp_path / "b.zip").read_bytes()
    # bytecode a run leaves in the skill directory is not packed, and changes nothing
    copy = tmp_path / "skill"
    shutil.copytree(ROOT / "skills" / "thai-docx", copy, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    monkeypatch.setattr(package_skill, "SKILL", copy)
    package_skill.pack(tmp_path / "c.zip")
    (copy / "scripts" / "thai_docx" / "__pycache__").mkdir()
    (copy / "scripts" / "thai_docx" / "__pycache__" / "build.cpython-311.pyc").write_bytes(b"\0")
    (copy / "scripts" / "stray.pyc").write_bytes(b"\0")
    package_skill.pack(tmp_path / "d.zip")
    assert (tmp_path / "c.zip").read_bytes() == (tmp_path / "d.zip").read_bytes() == (tmp_path / "a.zip").read_bytes()


def test_every_stated_version_is_the_same():
    found = package_skill.versions()
    skill, init, bundle = found["SKILL.md metadata.version"], found["thai_docx.__version__"], found["thai_docx.js VERSION"]
    assert skill == init == bundle, found


def test_tag_check_refuses_a_version_nobody_states():
    done = subprocess.run(TOOL + ["--tag", "v99.0.0"], capture_output=True, text=True)
    assert done.returncode == 1 and '"ok": false' in done.stdout
