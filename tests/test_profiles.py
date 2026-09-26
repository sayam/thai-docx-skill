# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Profiles (ADR 0024): settings saved as data, used again, exported and imported —
holding nothing a command line could not, and never read or written outside the profile
directories of ADR 0040."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from thai_docx import build as b
from thai_docx import profiles as p

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "thai-docx" / "scripts" / "thai_docx"


@pytest.fixture()
def home(tmp_path, monkeypatch):
    """A home and a working directory of their own: the searched places are under them."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    return tmp_path


def run(*args, cwd=None) -> dict:
    done = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, cwd=cwd)
    assert done.stderr == "", done.stderr
    return json.loads(done.stdout)


def test_a_profile_holds_only_settings_a_flag_could_set():
    """Every setting the build takes is a profile key, and each writes its own flag."""
    assert sorted(p.FLAGS) == sorted(b.DEFAULTS)
    for key, (kind, flag) in p.FLAGS.items():
        assert flag in b.USAGE, key
        assert kind in ("value", "switch", "off", "list", "option")
    # the flags a profile writes are read back as the same settings
    opts, _, _ = b.parse_args(["--size", "14", "--align", "thai", "--margins", "1,2,1,2", "--toc",
                               "--no-repeat-table-header", "--page-numbers", "top-center", "--table-size", "12.5",
                               "--header", "ลับ", "--indent", "0.5", "in.md", "out.docx"])
    settings = p.settings_of(opts)
    again, _, _ = b.parse_args(p.as_flags(settings) + ["in.md", "out.docx"])
    assert again == opts and p.settings_of(again) == settings
    assert settings["size"] == 14 and settings["margins"] == [1.0, 2.0, 1.0, 2.0] and settings["header"] == "ลับ"
    assert "font" not in settings, "only what differs from the defaults is written"


def test_save_show_export_import_and_build_with_a_profile(home):
    saved = run("profile", "save", "thesis", "--size", "15", "--align", "thai", "--line-spacing", "1.5",
                "--page-numbers", "bottom-center", "--thai-digits")
    path = pathlib.Path(saved["path"])
    assert saved["ok"] and saved["where"] == "home" and path == home / "home" / ".thai-docx" / "profiles" / "thesis.json"
    # nothing was there to replace, but the skill ships a thesis, and this one now hides it
    assert saved["replaced"] is False and saved["shadows"] == "skill" and len(saved["warnings"]) == 1
    assert path.read_text(encoding="utf-8") == p.canonical({"id": "thesis", "schema": 1, "settings": saved["settings"]})
    assert saved["settings"] == {"size": 15, "line_spacing": 1.5, "align": "thai", "page_numbers": "bottom-center", "thai_digits": True}

    shown = run("profile", "show", "thesis")
    assert shown["settings"] == saved["settings"] and shown["sha256"] == saved["sha256"]
    assert shown["resolved"]["size_pt"] == 15 and shown["resolved"]["font"] == b.DEFAULTS["font"]

    exported = run("profile", "export", "thesis", "share/thesis.json")
    assert exported["ok"] and pathlib.Path("share/thesis.json").read_bytes() == path.read_bytes()
    assert "profile import thesis.json" in exported["share"]

    # someone else's machine: a home of their own, the file arrives by any channel
    other = home / "other"
    other.mkdir()
    imported = run("profile", "import", str(home / "share" / "thesis.json"), "--name", "from-a-friend", cwd=other)
    assert imported["ok"] and imported["replaced"] is False and imported["sha256"] == saved["sha256"]
    again = run("profile", "import", str(home / "share" / "thesis.json"), "--name", "from-a-friend", cwd=other)
    assert again["replaced"] is True and again["warnings"] == ["replaced the profile from-a-friend that was there before"]
    assert json.loads(pathlib.Path(imported["path"]).read_text(encoding="utf-8"))["id"] == "from-a-friend"

    (home / "in.md").write_text("ก\n", encoding="utf-8")
    built = run("build", "in.md", "out.docx", "--profile", "thesis")
    assert built["ok"] and built["profile"]["name"] == "thesis" and built["profile"]["sha256"] == saved["sha256"]
    assert built["settings"]["size_pt"] == 15 and built["settings"]["align"] == "thai"
    # a flag typed after the profile wins; the profile's other settings stay
    over = run("build", "in.md", "out.docx", "--profile", "thesis", "--size", "18")
    assert over["settings"]["size_pt"] == 18 and over["settings"]["line_spacing"] == 1.5


def test_the_project_comes_before_the_home_and_a_path_before_both(home):
    assert run("profile", "save", "house", "--size", "15")["replaced"] is False
    # saving under a name already used replaces that profile, and says so
    again = run("profile", "save", "house", "--size", "14")
    assert again["replaced"] is True and again["warnings"] == ["replaced the profile house that was there before"]
    run("profile", "save", "house", "--size", "16", "--project")
    listed = run("profile", "list")["profiles"]
    # the skill ships one of its own, which every list also shows
    assert [(r["name"], r["where"], r["used"]) for r in listed if r["name"] == "house"] == [
        ("house", "project", True), ("house", "home", False)]
    assert run("profile", "show", "house")["resolved"]["size_pt"] == 16
    (home / "elsewhere").mkdir()
    run("profile", "export", "house", "elsewhere/house.json")
    assert run("profile", "show", "elsewhere/house.json")["where"] == "path"


def test_save_from_another_profile_adds_to_it(home):
    run("profile", "save", "base", "--size", "14", "--toc")
    saved = run("profile", "save", "report", "--from", "base", "--page-numbers", "top-center", "--size", "15")
    assert saved["settings"] == {"size": 15, "toc": True, "page_numbers": "top-center"}


def test_a_profile_is_refused_when_it_is_not_data_the_build_takes(home):
    (home / "p.json").write_text('{"schema": 1, "settings": {"size": 500}}\n', encoding="utf-8")
    assert "--size takes a number of points from 1 to 400" in run("profile", "show", "p.json")["error"]
    (home / "p.json").write_text('{"schema": 1, "settings": {"font_size": 12}}\n', encoding="utf-8")
    assert 'unknown setting "font_size"' in run("profile", "show", "p.json")["error"]
    (home / "p.json").write_text('{"schema": 1, "settings": {}, "command": "rm -rf /"}\n', encoding="utf-8")
    assert 'unknown key "command"' in run("profile", "show", "p.json")["error"]
    (home / "p.json").write_text('{"schema": 2, "settings": {}}\n', encoding="utf-8")
    assert '"schema" must be 1' in run("profile", "show", "p.json")["error"]
    (home / "p.json").write_text('{"schema": 1, "settings": {"size": 14}, "title": {"fr": "x"}}\n', encoding="utf-8")
    assert '"title" takes th and/or en' in run("profile", "show", "p.json")["error"]
    (home / "p.json").write_text("not json\n", encoding="utf-8")
    assert run("profile", "show", "p.json")["error"].endswith(": not JSON")
    (home / "big.json").write_text('{"schema": 1, "settings": {}, "version": "' + "x" * 70000 + '"}', encoding="utf-8")
    assert "larger than 64 KiB" in run("profile", "show", "big.json")["error"]
    if pathlib.Path("/dev/zero").exists():
        # a file with no end is not a regular file, and is refused before it is opened
        assert run("profile", "show", "/dev/zero")["error"] == "cannot read /dev/zero: not a regular file"
    assert "no profile named 'ghost'" in run("profile", "show", "ghost")["error"]
    for name in ("../escape", "a/b", "", ".hidden", "x" * 65):
        assert "is not a name" in run("profile", "save", name, "--size", "14")["error"], name
        assert "is not a name" in run("profile", "import", "p.json", "--name", name)["error"], name
    # the name a file carries is judged too: an id is not a place to write
    (home / "sneaky.json").write_text('{"id": "../../escape", "schema": 1, "settings": {"size": 14}}\n', encoding="utf-8")
    assert "is not a name" in run("profile", "import", "sneaky.json")["error"]
    assert not (home.parent / "escape.json").exists()
    assert run("build", "in.md", "out.docx", "--profile", "ghost")["error"].startswith("no profile named")


def test_the_command_says_how_when_it_is_used_wrongly(home):
    for args in (["profile"], ["profile", "nonsense"], ["profile", "list", "extra"], ["profile", "show"]):
        assert run(*args)["error"].startswith("usage: thai_docx profile"), args
    assert run("nonsense")["error"].startswith("usage: thai_docx check")


def test_a_saved_profile_gives_the_same_document_as_the_flags(home, tmp_path):
    (home / "in.md").write_text("# ก\n\nข\n\n| ก | ข |\n|---|---|\n| 1 | 2 |\n", encoding="utf-8")
    flags = ["--size", "15", "--align", "thai", "--table-widths", "auto", "--page-numbers", "bottom-center",
             "--heading-numbers", "--indent", "0.5", "--header", "ลับ"]
    direct = run("build", "in.md", "flags.docx", *flags)
    run("profile", "save", "house", *flags)
    viaprofile = run("build", "in.md", "profile.docx", "--profile", "house")
    assert direct["sha256"] == viaprofile["sha256"] and direct["settings"] == viaprofile["settings"]


def test_default_takes_settings_out_of_a_profile_before_any_flag(home):
    """ADR 0029: a flag can only add to a profile; --default gives settings back to their
    defaults, so an answer of "no" can undo a profile's "yes"."""
    assert run("profile", "save", "thesis", "--toc", "--size", "15", "--page-numbers")["ok"]
    derived = run("profile", "save", "v1", "--from", "thesis", "--default", "toc", "--default=page_numbers", "--align", "thai")
    assert derived["settings"] == {"size": 15, "align": "thai"}
    (home / "in.md").write_text("# ก\n\nข\n", encoding="utf-8")
    once = run("build", "in.md", "a.docx", "--profile", "thesis", "--default", "toc,page_numbers", "--align", "thai")
    assert once["settings"]["toc"] is False and once["settings"]["page_numbers"] is False
    assert once["sha256"] == run("build", "in.md", "b.docx", "--profile", "v1")["sha256"]
    assert once["profile"]["sha256"] == run("profile", "show", "thesis")["sha256"], "the profile used is reported as it is"
    # without a profile the settings already are their defaults
    plain = run("build", "in.md", "c.docx", "--default", "toc")
    assert plain["ok"] and plain["sha256"] == run("build", "in.md", "d.docx")["sha256"]
    for args, error in ((["--default", "font_size"], '--default: unknown setting "font_size"'),
                        (["--default"], "--default needs a value")):
        refused = run("build", "in.md", "e.docx", "--profile", "thesis", *args)
        assert refused["ok"] is False and refused["error"].startswith(error), refused


def test_the_shipped_example_is_an_example_and_it_builds(home, tmp_path):
    """The skill ships one profile and one document beside it. They are an example to copy,
    not a format anyone must follow — so the example says so itself, invents every name in it,
    and builds clean with no warning a user would have to act on."""
    skill = ROOT / "skills" / "thai-docx"
    profile = json.loads((skill / "profiles" / "thesis.json").read_text(encoding="utf-8"))
    assert profile["id"] == "thesis" and profile["schema"] == 1
    assert set(profile["settings"]) <= {s["key"] for s in __import__("thai_docx.settings", fromlist=["SETTINGS"]).SETTINGS}
    assert run("profile", "show", "thesis")["ok"], "found by name, from the skill's own directory"
    assert [(r["where"], r["used"]) for r in run("profile", "list")["profiles"] if r["name"] == "thesis"] == [("skill", True)]

    readme = (skill / "examples" / "README.md").read_text(encoding="utf-8")
    assert "not a standard" in readme and "do not renumber themselves" in readme, "it says what it is and what it costs"

    out = tmp_path / "thesis.docx"
    result = run("build", skill / "examples" / "thesis.md", out, "--profile", "thesis")
    assert result["ok"] and result["findings"] == [] and result["warnings"] == [], result
    assert result["profile"]["name"] == "thesis" and result["settings"]["thai_digits"] is True
    assert result["counts"]["tables"] == 2 and result["counts"]["images"] == 1 and result["counts"]["footnotes"] == 1

    # a user's own of the same name wins over the shipped one, and takes what it likes from it
    mine = run("profile", "save", "thesis", "--from", "thesis", "--default", "thai_digits")
    assert mine["ok"] and mine["where"] == "home" and "thai_digits" not in mine["settings"]
    assert [(r["where"], r["used"]) for r in run("profile", "list")["profiles"] if r["name"] == "thesis"] == [
        ("home", True), ("skill", False)], "the user's own wins, and the shipped one is still shown"
