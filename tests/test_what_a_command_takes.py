# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""What every command reads, writes and accepts, held in both implementations at once.

Each case runs the Python and the JavaScript command lines on the same input and asks
two things: that they answer alike (ADR 0008), and that the answer is the one decided —
one JSON line whatever happens; exit 2 for input a user can change; nothing written over
the file a command was given; only regular files read, each to a ceiling; only text taken
as text; a profile name that no shell reads. The review of 0.2.0 found each of these
broken in one implementation or both.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

from docx_fixture import good, pack, replaced

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
GOLDEN = ROOT / "tests" / "golden"
PY = [sys.executable, str(ROOT / "skills" / "thai-docx" / "scripts" / "thai_docx")]
JS = ["node", str(ROOT / "skills" / "thai-docx" / "scripts" / "thai_docx.js")]
POSIX = os.name == "posix"


@pytest.fixture(autouse=True)
def _node():
    if shutil.which("node"):
        return
    if os.environ.get("CI"):
        pytest.fail("Node.js is required in CI: the JavaScript implementation is a gate, not an option")
    pytest.skip("Node.js is not installed")


def one(cli: list[str], args: list[str], cwd: pathlib.Path, env: dict | None = None) -> tuple[int, dict]:
    home = cwd / "home"
    full = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), **(env or {})}
    done = subprocess.run(cli + args, cwd=cwd, capture_output=True, timeout=30, env=full)
    lines = done.stdout.decode("utf-8").splitlines()
    assert len(lines) == 1 and done.stderr == b"", (cli[0], args, done.stdout[-600:], done.stderr[-600:])
    return done.returncode, json.loads(lines[0])


def both(args: list[str], cwd: pathlib.Path, env: dict | None = None, setup=None) -> tuple[int, dict]:
    """The one answer both implementations give; a difference fails here. Each starts from an
    empty home, then `setup`, so what one saves is not there for the other."""
    answers = []
    for cli in (PY, JS):
        shutil.rmtree(cwd / "home", ignore_errors=True)
        if setup is not None:
            setup()
        answers.append(one(cli, args, cwd, env))
    py, js = answers
    assert py == js, f"{args}:\n python: {py}\n     js: {js}"
    return py


def sha(path: pathlib.Path) -> bytes:
    return path.read_bytes()


# --- nothing is written over the file a command was given --------------------------------


@pytest.mark.skipif(not POSIX, reason="symbolic and hard links as POSIX makes them")
def test_the_input_is_never_the_output(tmp_path):
    (tmp_path / "in.md").write_text("# หัวเรื่อง\n\nเนื้อความ\n", encoding="utf-8")
    (tmp_path / "soft.md").symlink_to(tmp_path / "in.md")
    os.link(tmp_path / "in.md", tmp_path / "hard.md")
    shutil.copy(FIXTURES / "legacy-python-docx-default.docx", tmp_path / "in.docx")
    (tmp_path / "soft.docx").symlink_to(tmp_path / "in.docx")
    os.link(tmp_path / "in.docx", tmp_path / "hard.docx")
    markdown, package = sha(tmp_path / "in.md"), sha(tmp_path / "in.docx")
    for out in ("in.md", "soft.md", "hard.md", "./in.md"):
        code, result = both(["build", "in.md", out], tmp_path)
        assert code == 2 and result["error"].startswith("the output is the Markdown file itself"), result
    for out in ("in.docx", "soft.docx", "hard.docx"):
        code, result = both(["repair", "in.docx", out], tmp_path)
        assert code == 2 and result["error"].startswith("the output is the file to repair"), result
    assert sha(tmp_path / "in.md") == markdown and sha(tmp_path / "in.docx") == package


# --- only regular files are read, each to a ceiling ------------------------------------------


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="a FIFO as POSIX makes one")
def test_a_file_that_is_not_a_regular_file_is_refused_before_it_is_opened(tmp_path):
    """Opening a FIFO waits for a writer that never comes; each reader asks first."""
    for name in ("fifo.md", "fifo.png", "fifo.json", "fifo.docx"):
        os.mkfifo(tmp_path / name)
    (tmp_path / "in.md").write_text("ก ![x](fifo.png)\n", encoding="utf-8")
    assert both(["build", "fifo.md", "out.docx"], tmp_path)[1]["error"] == "cannot read fifo.md: not a regular file"
    assert both(["build", "in.md", "out.docx"], tmp_path)[1]["error"] == "image 'fifo.png': not a regular file"
    assert both(["profile", "show", "./fifo.json"], tmp_path)[1]["error"] == "cannot read fifo.json: not a regular file"
    assert both(["check", "fifo.docx"], tmp_path)[1]["error"] == "cannot read fifo.docx: not a regular file"
    assert both(["repair", "fifo.docx", "out.docx"], tmp_path)[1]["error"] == "cannot read fifo.docx: not a regular file"
    assert not (tmp_path / "out.docx").exists()


def test_a_markdown_file_past_its_ceiling_is_refused_not_read_whole(tmp_path):
    with open(tmp_path / "big.md", "wb") as f:  # sparse: one byte past the ceiling costs no disk
        f.truncate(16 * 1024 * 1024 + 1)
    code, result = both(["build", "big.md", "out.docx"], tmp_path)
    assert code == 2 and result["error"] == "cannot read big.md: larger than 16 MiB"


# --- only text is taken as text -------------------------------------------------------------


def test_an_argument_in_another_encoding_is_refused_the_same_way(tmp_path):
    """Python keeps a byte that is not UTF-8 as a lone surrogate and Node as U+FFFD; both
    refuse either, rather than a traceback in one and a document with U+FFFD in the other."""
    (tmp_path / "in.md").write_text("ก\n", encoding="utf-8")
    latin = os.fsdecode(b"A\xff") if POSIX else "A�"
    for args, at in ((["build", "in.md", "out.docx", "--font", latin], 5),
                     (["build", "in.md", "out.docx", "--header", "ลับ�"], 5),
                     (["check", os.fsdecode(b"\xff.docx") if POSIX else "�.docx"], 2)):
        code, result = both(args, tmp_path)
        assert code == 2 and result["error"].startswith("argument " + str(at) + " is not UTF-8 text"), result
    assert not (tmp_path / "out.docx").exists()


def test_a_number_too_long_for_a_float_is_refused_not_a_traceback(tmp_path):
    (tmp_path / "in.md").write_text("ก\n", encoding="utf-8")
    long = "1" + "0" * 400
    assert both(["build", "in.md", "out.docx", "--indent", long], tmp_path)[1]["error"].startswith("--indent takes")
    assert both(["build", "in.md", "out.docx", "--margins", long + ",1,1,1"], tmp_path)[1]["error"].startswith("--margins takes")


# --- repair's --font is read as the build reads it, and escaped where it is written ------------


def test_the_font_given_to_repair_is_read_like_the_builds_and_escaped(tmp_path):
    parts = replaced(good(), "word/styles.xml", ' w:cs="TH Sarabun New" w:eastAsia="TH Sarabun New"/>',
                     ' w:eastAsia="TH Sarabun New"/>')
    (tmp_path / "in.docx").write_bytes(pack(parts))
    code, result = both(["repair", "in.docx", "out.docx", "--font", 'X"/><w:evil w:a="'], tmp_path)
    assert result["ok"], result
    import zipfile
    with zipfile.ZipFile(tmp_path / "out.docx") as z:
        styles = z.read("word/styles.xml").decode("utf-8")
    assert "<w:evil" not in styles and 'w:cs="X&quot;/&gt;&lt;w:evil w:a=&quot;"' in styles
    code, result = both(["repair", "in.docx", "long.docx", "--font", "F" * 65], tmp_path)
    assert code == 2 and result["error"] == "--font takes a font name of 1 to 64 characters"
    assert not (tmp_path / "long.docx").exists()


def test_a_file_with_nothing_to_repair_is_an_answer_not_an_error(tmp_path):
    shutil.copy(GOLDEN / "sample-default.docx", tmp_path / "clean.docx")
    code, result = both(["repair", "clean.docx", "out.docx"], tmp_path)
    assert code == 0 and result["ok"] and result["repaired"] == {} and "error" not in result
    assert result["warnings"][0]["code"] == "clean" and not (tmp_path / "out.docx").exists()


# --- a profile name no shell reads; a profile that is data, read the same way ----------------


def test_a_profile_name_is_letters_digits_dash_and_underscore(tmp_path):
    for name in ("x$(touch pwned)", "a\nb", "a;b", "a b", "`id`", ".hidden", "-x"):
        code, result = both(["profile", "save", name, "--size", "14"], tmp_path)
        assert code == 2, (name, result)
    assert both(["profile", "save", "--help"], tmp_path)[1]["error"].startswith("usage: thai_docx profile")
    for name in ("วิทยานิพนธ์", "thesis-v1", "report_2"):
        code, result = both(["profile", "save", name, "--size", "14"], tmp_path)
        assert code == 0 and result["name"] == name, result
    assert not (tmp_path / "pwned").exists()


def test_grill_never_hands_back_a_word_a_shell_would_read(tmp_path):
    for said in ("thai-docx grill save to x$(touch${IFS}pwned)", "thai-docx grill from ./a$(b).json",
                 "thai-docx grill from x`id`"):
        code, result = both(["grill", "--said", said], tmp_path)
        assert code == 2 and not result["ok"], (said, result)


def test_a_profile_that_is_not_a_profile_is_named_not_obeyed(tmp_path):
    cases = {
        '{"schema": 1, "settings": {"size": [1]}}': '"size" takes a number',
        '{"schema": 1, "settings": {"margins": 5}}': '"margins" takes a list of numbers',
        '{"schema": 1, "settings": {"toc": "yes"}}': '"toc" takes true or false',
        '{"schema": 1, "settings": {"font": 12}}': '"font" takes text',
        '{"schema": 1, "settings": {"size": 1e400}}': '"size" takes a number',
        '{"schema": 1, "settings": {"size": 1' + "0" * 400 + "}}": '"size" takes a number',
        '{"schema": true, "settings": {}}': '"schema" must be 1',
        '{"schema": 1.0, "settings": {}}': '"schema" must be 1',
        '{"schema": 1, "id": "\\ud800", "settings": {}}': "holds a lone surrogate",
        '{"__proto__": {"schema": 1, "settings": {"font": "X"}}}': '"schema" must be 1',
        '{"schema": 1, "settings": {"__proto__": {"font": "X"}}}': 'unknown setting "__proto__"',
        "[" * 30000 + "]" * 30000: "not JSON",
    }
    for text, said in cases.items():
        (tmp_path / "p.json").write_text(text, encoding="utf-8")
        code, result = both(["profile", "show", "./p.json"], tmp_path)
        assert code == 2 and said in result["error"], (text[:60], result)
    (tmp_path / "p.json").write_bytes(b'{"schema": 1, "id": "bad\xff", "settings": {}}')
    assert both(["profile", "show", "./p.json"], tmp_path)[1]["error"].endswith(": not UTF-8 text")


def test_a_profile_is_replaced_whole_or_not_at_all(tmp_path):
    """A write that fails leaves the profile that was there, byte for byte."""
    home = tmp_path / "home" / ".thai-docx" / "profiles"
    before = b'{\n  "id": "p",\n  "schema": 1,\n  "settings": {\n    "size": 14\n  }\n}\n'

    def there(blocked: bool):
        def setup():
            home.mkdir(parents=True)
            (home / "p.json").write_bytes(before)
            if blocked:
                (home / "p.json.partial").mkdir()  # the place the new file would be written first
        return setup

    (tmp_path / "bad.json").write_text('{"schema": 1, "id": "p", "version": "\\udc80", "settings": {}}', encoding="utf-8")
    assert both(["profile", "import", "bad.json"], tmp_path, setup=there(False))[0] == 2
    assert (home / "p.json").read_bytes() == before
    code, result = both(["profile", "save", "p", "--size", "18"], tmp_path, setup=there(True))
    assert code == 2 and result["error"].startswith("cannot write "), result
    assert (home / "p.json").read_bytes() == before


# --- one JSON line, whatever happens ------------------------------------------------------------


def test_help_is_the_usage_line(tmp_path):
    for args in (["build", "--help"], ["check", "--help"], ["repair", "--help"], ["profile", "save", "--help"]):
        code, result = both(args, tmp_path)
        assert code == 2 and result["error"].startswith("usage: thai_docx"), (args, result)


def test_a_pipe_that_is_not_utf8_still_gets_the_json_line(tmp_path):
    """Python prints in the pipe's encoding unless told; Node writes UTF-8 always."""
    (tmp_path / "in.md").write_text("ก\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path, env={"PYTHONIOENCODING": "ascii"})
    assert code == 0 and result["settings"]["chapter_label"] == "บทที่"


@pytest.mark.skipif(not POSIX, reason="a working directory removed from under a process, as POSIX allows")
def test_a_working_directory_that_is_gone_is_said_not_a_traceback(tmp_path):
    gone = tmp_path / "gone"
    for cli in (PY, JS):
        gone.mkdir()
        done = subprocess.run(["sh", "-c", 'cd "$1" && rmdir "$1" && shift && exec "$@"', "sh", str(gone), *cli, "profile", "list"],
                              capture_output=True, timeout=30, env={**os.environ, "HOME": str(tmp_path / "home")})
        assert done.returncode == 2 and done.stderr == b"", (cli[0], done.stderr[-400:])
        assert json.loads(done.stdout)["error"].startswith("the working directory no longer exists")


def test_a_defect_is_one_json_line_and_exit_1_not_a_traceback(tmp_path):
    """Nesting deeper than a runtime's stack inside one run's properties once stopped both
    implementations with a trace, at depths that differ by runtime. Whatever stops a command,
    the agent is told in the one line it reads, and told not to retry."""
    deep = "<w:x>" * 5000 + "</w:x>" * 5000
    parts = replaced(good(), "word/document.xml", "<w:rPr><w:cs/>", "<w:rPr>" + deep + "<w:cs/>")
    (tmp_path / "deep.docx").write_bytes(pack(parts))
    code, result = both(["check", "deep.docx"], tmp_path)
    assert code in (1, 2) and result["ok"] is False


def test_the_entry_answers_before_any_command_runs(monkeypatch, capsys):
    """The same three answers, in process: what the command lines above reach through a shell."""
    from thai_docx import __main__ as entry

    assert entry.main(["check", "a\udcff.docx"]) == 2
    assert json.loads(capsys.readouterr().out)["error"].startswith("argument 2 is not UTF-8 text")

    def gone():
        raise FileNotFoundError(2, "No such file or directory")

    monkeypatch.setattr(entry.os, "getcwd", gone)
    assert entry.main(["profile", "list"]) == 2
    assert json.loads(capsys.readouterr().out)["error"].startswith("the working directory no longer exists")
    monkeypatch.undo()

    def broken(_argv):
        raise RuntimeError("planted")

    monkeypatch.setitem(entry.COMMANDS, "check", broken)
    assert entry.main(["check", "x.docx"]) == 1
    assert json.loads(capsys.readouterr().out)["error"].startswith("a defect in thai-docx stopped this command")
