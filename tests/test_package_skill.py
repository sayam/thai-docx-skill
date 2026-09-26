# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""What a person who only uses the skill receives (ADR 0018): the skill directory and
nothing else, the same bytes on every run, and one version everywhere it is stated.
"""

from __future__ import annotations

import pathlib
import re
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


def test_the_citation_names_the_release_the_changelog_names(tmp_path, monkeypatch):
    """CITATION.cff's version and date were kept by hand and read by nothing; the tag check
    reads them now, and a citation one release behind refuses the tag."""
    assert package_skill.versions()["CITATION.cff version"] == package_skill.versions()["CHANGELOG.md newest release"]
    days = package_skill.dates()
    assert len(set(days.values())) == 1 and "(missing)" not in days.values(), days
    root = tmp_path / "root"
    root.mkdir()
    for name in ("CHANGELOG.md", "CITATION.cff"):
        shutil.copy(ROOT / name, root / name)
    monkeypatch.setattr(package_skill, "ROOT", root)
    cff = (root / "CITATION.cff").read_text(encoding="utf-8")
    (root / "CITATION.cff").write_text(re.sub(r"(?m)^version: .*$", "version: 0.1.9", cff), encoding="utf-8")
    assert package_skill.versions()["CITATION.cff version"] == "0.1.9"
    assert package_skill.main(["--tag", "v" + package_skill.versions()["CHANGELOG.md newest release"]]) == 1
    (root / "CITATION.cff").write_text(re.sub(r"(?m)^date-released: .*$", "date-released: '2026-01-01'", cff), encoding="utf-8")
    assert package_skill.main(["--tag", "v" + package_skill.versions()["CHANGELOG.md newest release"]]) == 1


def test_tag_check_refuses_a_version_nobody_states():
    done = subprocess.run(TOOL + ["--tag", "v99.0.0"], capture_output=True, text=True)
    assert done.returncode == 1 and '"ok": false' in done.stdout


# --- what the installers copy, and what one of them rewrites (ROADMAP, 0.2.0) ---------
#
# `npx skills add` copies the repository subtree `skills/thai-docx/` byte for byte, and
# `gh skill install` copies the same subtree out of the latest release. Neither reads the
# archive this project builds — so the archive and the subtree must be the same files, or a
# user's copy differs from the one the release evidence was written about.


def test_the_archive_is_the_subtree_the_installers_copy(tmp_path):
    """The archive holds the subtree's bytes, file by file — `pack` copies, it does not
    transform. The test beside this one holds the two to the same *names*; this one goes red
    the day packing starts rewriting what it packs, which would put a user who installed with
    `npx skills add` on different bytes from one who downloaded the release."""
    out = tmp_path / "a.zip"
    subprocess.run(TOOL + [str(out)], check=True, capture_output=True)
    with zipfile.ZipFile(out) as z:
        for name in z.namelist():
            on_disk = ROOT / "skills" / "thai-docx" / name[len("thai-docx/"):]
            assert z.read(name) == on_disk.read_bytes(), name


def _front_matter(text: str) -> dict:
    """SKILL.md's front matter, as a reader that knows this one shape: flat `key: value`
    lines and one nested block. Written here rather than taken from a library, so the test
    depends on nothing the project has not declared."""
    block = text.split("---", 2)[1]
    out: dict = {}
    where = out
    for line in block.splitlines():
        if not line.strip():
            continue
        key, _colon, value = line.partition(":")
        value = value.strip()
        if line.startswith("  "):
            where[key.strip()] = value.strip('"')
        elif value == "":
            where = out[key.strip()] = {}
        else:
            where = out
            out[key.strip()] = value.strip('"')
    return out


def _as_an_installer_writes_it(front: dict) -> str:
    """What `gh skill install` does to the front matter it copies: the keys sorted, the
    nested block flattened, every scalar written without its quotes, and its own provenance
    keys added."""
    flat = {}
    for key, value in front.items():
        if isinstance(value, dict):
            flat.update(value)
        else:
            flat[key] = value
    flat["github-repo"] = "sayam/thai-docx-skill"
    flat["github-ref"] = "refs/tags/v" + front["metadata"]["version"]
    return "---\n" + "".join(f"{k}: {flat[k]}\n" for k in sorted(flat)) + "---\n"


def test_the_front_matter_survives_being_written_again():
    """A user's installed copy is not this file: one installer rewrites the front matter,
    sorting the keys, flattening `metadata` and dropping the quotes around a scalar. Nothing
    the skill states may depend on the order, or on `version` being written as a string."""
    front = _front_matter((ROOT / "skills" / "thai-docx" / "SKILL.md").read_text(encoding="utf-8"))
    assert set(front) == {"name", "description", "license", "compatibility", "metadata"}
    assert set(front["metadata"]) == {"author", "version"}

    again = _front_matter(_as_an_installer_writes_it(front) + "\n# thai-docx\n")
    assert again["name"] == front["name"]
    assert again["description"] == front["description"]
    assert again["license"] == front["license"]
    assert again["compatibility"] == front["compatibility"]
    assert again["author"] == front["metadata"]["author"]
    # the one that could change meaning: 0.1.1 unquoted is still the three numbers, and
    # a version of one dot (1.1) would become a number the moment its quotes came off
    assert again["version"] == front["metadata"]["version"]
    assert front["metadata"]["version"].count(".") == 2, front["metadata"]["version"]

    # and the description a rewritten front matter carries is still within the Claude apps'
    # limit, which is what `test_description_fits_the_claude_apps_upload` holds for ours
    assert len(again["description"]) <= 200

    # flattening is lossy if a nested key shares a name with a top-level one: the installer
    # would keep one and drop the other, without saying which
    assert not set(front["metadata"]) & set(front), (set(front["metadata"]) & set(front))
