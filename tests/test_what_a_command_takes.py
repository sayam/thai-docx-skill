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


def test_the_entry_answers_before_any_command_runs(monkeypatch, capsys):
    """The same three answers, in process: what the command lines above reach through a shell —
    and the last, whatever stops a command, is one JSON line telling the agent not to retry."""
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


def test_a_profile_that_hides_another_of_its_name_says_so(tmp_path):
    """The guides' first save was `profile save thesis`, which hid the thesis profile the skill
    ships with nothing said: from then on `--profile thesis` and `grill from thesis` took two
    settings where the example holds eight."""
    code, result = both(["profile", "save", "thesis", "--size", "15"], tmp_path)
    assert code == 0 and result["shadows"] == "skill", result
    assert result["warnings"] == ["the profile thesis that the skill ships is now hidden by this one:"
                                  " --profile thesis and grill from thesis use this one"]
    code, result = both(["profile", "save", "my-thesis", "--size", "15"], tmp_path)
    assert code == 0 and "shadows" not in result and "warnings" not in result, result


def test_allow_dir_never_opens_the_whole_machine(tmp_path):
    """`--allow-dir /` widened the picture limit to every file there is, and `--allow-dir ''`
    to the working directory, which nobody named."""
    (tmp_path / "in.md").write_text("ก\n", encoding="utf-8")
    (tmp_path / "root").symlink_to("/") if POSIX else None
    for value in (["/"], ["root"] if POSIX else ["/"], ["/tmp/.."]):
        code, result = both(["build", "in.md", "out.docx", "--allow-dir", value[0]], tmp_path)
        assert code == 2 and result["error"].startswith("--allow-dir names the filesystem's root"), (value, result)
    code, result = both(["build", "in.md", "out.docx", "--allow-dir", ""], tmp_path)
    assert code == 2 and result["error"] == "--allow-dir takes a directory; an empty one names none", result
    assert not (tmp_path / "out.docx").exists()


# --- what the review of 0.2.0 left for 0.2.2 -------------------------------------------------


def test_profile_export_writes_where_it_is_told_and_makes_no_folder(tmp_path):
    """`export PATH` made every missing folder above PATH; only the two profile folders are the
    skill's to make (ADR 0040)."""
    def saved():
        one(PY, ["profile", "save", "mine", "--size", "15"], tmp_path)
    code, result = both(["profile", "export", "mine", "a/b/c/mine.json"], tmp_path, setup=saved)
    assert code == 2 and result["error"].startswith("cannot write a/b/c/mine.json"), result
    assert not (tmp_path / "a").exists()
    code, result = both(["profile", "export", "mine", "mine.json"], tmp_path, setup=saved)
    assert code == 0 and (tmp_path / "mine.json").is_file(), result


def test_an_entry_encrypted_anywhere_in_the_package_is_refused(tmp_path):
    """Only the XML parts were asked; repair then copied an encrypted picture under flags that
    said it was not."""
    parts = replaced(good(), "word/document.xml", "<w:cs/>", "<w:noProof/><w:cs/>")
    data = bytearray(pack({**parts, "word/media/image1.png": b"\x89PNG not really"}))
    name = b"word/media/image1.png"
    # the encryption bit set in the entry's local and central headers, as a writer that
    # encrypted it would; the bytes themselves do not matter to what is asked
    for signature, flags_at, name_at in ((b"PK\x03\x04", 6, 30), (b"PK\x01\x02", 8, 46)):
        at = data.find(signature)
        while data[at + name_at:at + name_at + len(name)] != name:
            at = data.find(signature, at + 1)
        data[at + flags_at] |= 0x1
    (tmp_path / "in.docx").write_bytes(bytes(data))
    for args in (["check", "in.docx"], ["repair", "in.docx", "out.docx"]):
        code, result = both(args, tmp_path)
        assert code == 2 and "entry uses encryption" in json.dumps(result), (args, result)
    assert both(["check", "in.docx"], tmp_path)[1]["findings"][0]["part"] == "word/media/image1.png"
    assert not (tmp_path / "out.docx").exists()


def test_an_unused_definition_is_named_at_its_own_line(tmp_path):
    """Every definition after the first in a paragraph was said to be on the first one's line."""
    (tmp_path / "in.md").write_text("[a]: /1\n[b]:\n  /2\n[c]: /3\n\ntext [a]\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 0 and [w["message"].split(":")[0] for w in result["warnings"]] == ["line 2", "line 4"], result


def test_a_drive_path_is_a_path_not_a_remote_image(tmp_path):
    """`C:\\…` was answered as a URL: "remote images are not supported"."""
    for src in ("C:\\Users\\x\\p.png", "C:/Users/x/p.png"):
        (tmp_path / "in.md").write_text("![p](" + src + ")\n", encoding="utf-8")
        code, result = both(["build", "in.md", "out.docx"], tmp_path)
        assert code == 2 and "remote" not in result["error"], (src, result)
    (tmp_path / "in.md").write_text("![p](https://example.org/p.png)\n", encoding="utf-8")
    assert "remote images are not supported" in both(["build", "in.md", "out.docx"], tmp_path)[1]["error"]


def test_a_flag_that_reaches_nothing_says_so(tmp_path):
    """limits.md §6 promised a warning for a flag that changes nothing; these two gave none."""
    (tmp_path / "th.md").write_text("# หัวข้อ\n\nข้อความ **หนา**\n", encoding="utf-8")
    (tmp_path / "en.md").write_text("# Title\n\nEnglish only text.\n", encoding="utf-8")
    plain = both(["build", "th.md", "out.docx"], tmp_path)[1]
    code, result = both(["build", "th.md", "out.docx", "--force-cs-whole-doc"], tmp_path)
    assert result["sha256"] == plain["sha256"], "the flag did change a byte; the warning would be false"
    assert {"code": "settings", "message": "--force-cs-whole-doc changed nothing: every run is Thai text,"
            " and is marked complex script already"} in result["warnings"], result
    code, result = both(["build", "en.md", "out.docx", "--thai-language"], tmp_path)
    # it names the language in the styles all the same, so it did change bytes: not "changed nothing"
    assert result["sha256"] != both(["build", "en.md", "out.docx"], tmp_path)[1]["sha256"]
    assert {"code": "settings", "message": "--thai-language reached no run: the document has no Thai text,"
            " and only the styles name the language"} in result["warnings"], result
    for args in (["en.md", "out.docx", "--force-cs-whole-doc"], ["th.md", "out.docx", "--thai-language"]):
        assert not [w for w in both(["build", *args], tmp_path)[1]["warnings"] if w["code"] == "settings"], args


def test_a_caption_is_never_given_less_than_an_inch(tmp_path):
    """A hang past the text, or a caption box as narrow as a small picture, wrote a line of no
    width, or of less than none."""
    import struct
    import zlib

    def png(width: int) -> bytes:
        rows = b"".join(b"\x00" + b"\xff\xff\xff" * width for _ in range(40))
        chunk = lambda kind, data: struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))  # noqa: E731
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, 40, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))
    (tmp_path / "small.png").write_bytes(png(40))
    (tmp_path / "wide.png").write_bytes(png(400))
    (tmp_path / "in.md").write_text("![a](small.png)\n\nFigure: ขั้นตอน\n\n![b](wide.png)\n\nFigure: กว้าง\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx", "--margins", "1,3.6,1,3.6", "--caption-hanging-indent", "4"], tmp_path)
    assert code == 2 and result["error"] == "--caption-hanging-indent leaves less than one inch for text", result
    code, result = both(["build", "in.md", "out.docx", "--caption-matches-object", "--caption-hanging-indent", "0.75"], tmp_path)
    assert code == 0 and [w["message"] for w in result["warnings"]] == [
        "line 3: the picture is too narrow for a caption of its width; the caption takes the width of the text"], result
    import zipfile
    with zipfile.ZipFile(tmp_path / "out.docx") as z:
        document = z.read("word/document.xml").decode("utf-8")
    assert '<w:ind w:left="1080" w:hanging="1080"/>' in document and 'w:right="' in document


def test_a_footnote_label_matches_in_any_case(tmp_path):
    """cmark-gfm matches a footnote as it matches a link label; `[^A]` and `[^a]` were refused
    as a footnote defined and never referenced."""
    (tmp_path / "in.md").write_text("ก[^A] ข[^a]\n\n[^a]: หมายเหตุ\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 0 and result["counts"]["footnotes"] == 1, result
    (tmp_path / "in.md").write_text("ก[^A]\n\n[^a]: หนึ่ง\n\n[^A]: สอง\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 2 and result["error"] == "footnote [^A] is defined twice", result


def test_an_extended_autolink_is_found_as_cmark_gfm_finds_it(tmp_path):
    """A Thai domain was no link, `mailto:` was text beside a link, and `&amp;` at a URL's end
    went into the link (cmark-gfm, measured). `xmpp:` stays text: ADR 0040 links to http,
    https and mailto only."""
    import re
    import urllib.parse
    import zipfile
    cases = {
        "ดู www.ตัวอย่าง.ไทย ครับ": ["http://www.ตัวอย่าง.ไทย"],
        "https://ตัวอย่าง.ไทย/ก": ["https://ตัวอย่าง.ไทย/ก"],
        "ติดต่อ mailto:me@x.example": ["mailto:me@x.example"],
        "xmpp:me@x.example": [],
        "https://x.example/a&amp;": ["https://x.example/a"],
        "https://x.example/a;": ["https://x.example/a"],
        "me@x.example1": [],
    }
    for text, targets in cases.items():
        (tmp_path / "in.md").write_text(text + "\n", encoding="utf-8")
        code, result = both(["build", "in.md", "out.docx"], tmp_path)
        assert code == 0 and result["counts"]["links"] == len(targets), (text, result)
        with zipfile.ZipFile(tmp_path / "out.docx") as z:
            rels = z.read("word/_rels/document.xml.rels").decode("utf-8")
        # a target is written percent-encoded (B-07), as cmark-gfm writes its href
        written = [urllib.parse.quote(t, safe=":/@") for t in targets]
        assert re.findall(r'Target="([^"]*)" TargetMode="External"', rels) == written, (text, rels)


def test_a_phrase_past_the_first_20000_characters_is_found_in_the_last(tmp_path):
    """E-23: the phrase at the end of a long message was never read, and the agent built at once.
    SKILL.md now has it run the command again on the message's last 20,000 characters; this
    holds that the second run finds the phrase and the first says why to make it."""
    message = "ก" * 20001 + " thai-docx grill"
    code, first = both(["grill", "--said", message], tmp_path)
    assert first["mode"] == "build" and any("may be among them" in w for w in first["warnings"]), first
    code, again = both(["grill", "--said", message[-20000:]], tmp_path)
    assert code == 0 and again["mode"] == "grill", again


def test_repair_says_it_wrote_a_font_only_where_it_did(tmp_path):
    """The `font` warning came with every mark or twin repaired, where no font was written;
    an agent reads it out to the user (repair.md). It comes only where one was."""
    marked_only = replaced(good(), "word/document.xml", "<w:cs/>", "")
    (tmp_path / "in.docx").write_bytes(pack(marked_only))
    code, result = both(["repair", "in.docx", "out.docx"], tmp_path)
    assert code == 0 and result["repaired"].get("2") and not [w for w in result["warnings"] if w["code"] == "font"], result
    shutil.copy(FIXTURES / "legacy-python-docx-default.docx", tmp_path / "legacy.docx")
    code, result = both(["repair", "legacy.docx", "out.docx"], tmp_path)
    assert [w["code"] for w in result["warnings"]].count("font") == 1, result


def test_a_picture_refused_is_named(tmp_path):
    """"image is not a PNG or JPEG file" did not say which, in a document of several pictures."""
    (tmp_path / "bad.png").write_bytes(b"not a picture")
    (tmp_path / "in.md").write_text("![a](bad.png)\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 2 and result["error"] == "image 'bad.png' is not a PNG or JPEG file (by its bytes, not its name)", result


def test_a_thai_mark_out_of_place_is_named(tmp_path):
    """B-10: `ำ` written the long way was named, but a mark with no letter before it (`นำ้`) and a
    letter with two tone marks went through in silence. Each is named, once a line, and left as
    typed; marks typed out of order on one letter are put in order by NFC, and are not named."""
    (tmp_path / "in.md").write_text("น้ำ นำ้ ก้่ข\n\nกิ่ ปุ่ม ก็ ฤๅ\n\n่ต้น\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 0 and [w["message"] for w in result["warnings"]] == [
        "line 1: a Thai mark (U+0E49) with no letter before it; it is written as it stands",
        "line 1: a letter with two tone marks; it is written as it stands",
        "line 5: a Thai mark (U+0E48) with no letter before it; it is written as it stands"], result
    (tmp_path / "in.md").write_text("ปุ่ม\n", encoding="utf-8")  # the tone typed before the vowel
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 0 and result["warnings"] == [], result


def test_punctuation_between_thai_is_not_cut_out_of_it(tmp_path):
    """B-05: every ASCII mark was a Latin run of its own, so `พ.ศ.` was four runs and `๑.๑` three,
    a word cut apart. Punctuation with Thai on both sides is Thai; between Thai and English it
    goes with the English, as Word puts the comma (2026-09-22, what Word writes)."""
    import re
    import zipfile
    (tmp_path / "in.md").write_text("ปี พ.ศ. 2567 ข้อ ๑.๑ คำว่า “อ้างอิง” (ร้อยละ 98.3) ครบ\n\nเอกสารภาษาไทย, Markdown\n",
                                    encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 0 and result["findings"] == [], result
    with zipfile.ZipFile(tmp_path / "out.docx") as z:
        document = z.read("word/document.xml").decode("utf-8")
    runs = [(bool(cs), text) for cs, text in re.findall(r'<w:r>(<w:rPr><w:cs/></w:rPr>)?<w:t xml:space="preserve">([^<]*)</w:t></w:r>', document)]
    assert runs == [(True, "ปี พ.ศ"), (False, ". 2567 "), (True, "ข้อ ๑.๑ คำว่า “อ้างอิง” (ร้อยละ "), (False, "98.3) "),
                    (True, "ครบ"), (True, "เอกสารภาษาไทย"), (False, ", Markdown")], runs


def test_every_complex_script_is_marked_checked_and_repaired(tmp_path):
    """B-09: "complex script" was the Thai block, so a Lao, Khmer, Arabic or Devanagari run in a
    Thai document was written as Latin — Word takes its font and size from the Latin slot — and
    the checker passed it. One list of the complex scripts, in assets/ooxml.json, now marks the
    run, finds it unmarked, and marks it in a repair."""
    import zipfile
    text = "ภาษาไทย ກຳລັງ ພາສາລາວ และ العربية และ ខ្មែរ และ हिन्दी จบ"
    (tmp_path / "in.md").write_text(text + "\n\nEnglish only.\n", encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx"], tmp_path)
    assert code == 0 and result["findings"] == [], result
    with zipfile.ZipFile(tmp_path / "out.docx") as z:
        document = z.read("word/document.xml").decode("utf-8")
    assert '<w:r><w:rPr><w:cs/></w:rPr><w:t xml:space="preserve">' + text + "</w:t></w:r>" in document
    assert '<w:r><w:t xml:space="preserve">English only.</w:t></w:r>' in document
    lao = replaced(good(), "word/document.xml", "<w:t xml:space=\"preserve\">รายการ</w:t>",
                   "<w:t xml:space=\"preserve\">ພາສາລາວ</w:t>")
    unmarked = replaced(lao, "word/document.xml", '<w:rPr><w:cs/><w:lang w:val="en-US" w:bidi="th-TH"/></w:rPr><w:t xml:space="preserve">ພາສາລາວ',
                        '<w:rPr><w:lang w:val="en-US" w:bidi="th-TH"/></w:rPr><w:t xml:space="preserve">ພາສາລາວ')
    (tmp_path / "in.docx").write_bytes(pack(unmarked))
    code, result = both(["check", "in.docx"], tmp_path)
    assert code == 1 and [f["code"] for f in result["findings"]] == ["2"], result
    code, result = both(["repair", "in.docx", "fixed.docx"], tmp_path)
    assert code == 0 and result["repaired"].get("2") == 1 and result["remaining"] == [], result


def test_a_captioned_table_is_named_and_an_empty_toc_is_said(tmp_path):
    """B-13: a table with a `Table:` caption was nameless to a screen reader and to Word's
    accessibility check; `--toc` in a document with no heading wrote an empty field and said
    nothing, where every other flag that reaches nothing says so."""
    import zipfile
    (tmp_path / "in.md").write_text('Table: ผล & "ค่า"\n\n| ก | ข |\n|---|---|\n| 1 | 2 |\n\n| ค |\n|---|\n| 3 |\n',
                                    encoding="utf-8")
    code, result = both(["build", "in.md", "out.docx", "--toc"], tmp_path)
    assert code == 0 and result["findings"] == [], result
    assert [w["message"] for w in result["warnings"]] == [
        "--toc has no heading to list: the document has none, so the table of contents is empty"], result
    with zipfile.ZipFile(tmp_path / "out.docx") as z:
        document = z.read("word/document.xml").decode("utf-8")
    assert document.count("<w:tblCaption ") == 1
    assert '<w:tblCaption w:val="ตารางที่ 1 ผล &amp; &quot;ค่า&quot;"/></w:tblPr>' in document
    (tmp_path / "in.md").write_text("# หัวข้อ\n\nข้อความ\n", encoding="utf-8")
    assert both(["build", "in.md", "out.docx", "--toc"], tmp_path)[1]["warnings"] == []
