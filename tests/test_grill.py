# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Grill mode is the user's word (ADR 0029): the mode comes from the message the user
typed, read by the script, not from what a model makes of the request — and so do the
profile it starts from, the name it saves to, and what each answer means against them."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from thai_docx import grill as g
from thai_docx import settings as st

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "thai-docx" / "scripts" / "thai_docx"

# The request that made Haiku choose the interview for the user on 2026-09-16 (L-0008).
LONG_REQUEST = (
    "ช่วยทำวิทยานิพนธ์เป็นไฟล์ word ให้หน่อย มีหน้าปก สารบัญ สารบัญตาราง สารบัญภาพ "
    "แบ่งเป็นบทที่ 1-5 ใส่ ตารางที่ 1-1 ภาคผนวก และเลขหน้า โดยไม่แก้ข้อความ"
)


def run(*args) -> dict:
    done = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    assert done.stderr == "", done.stderr
    return json.loads(done.stdout)


def test_only_the_users_own_word_asks_the_questions():
    for message in ("thai-docx grill", "/thai-docx grill", "THAI-DOCX GRILL",
                    "thai_docx grill", "thai-docx\tgrill", "ขอ thai-docx grill ก่อนนะ"):
        assert g.mode(message) == "grill", message
    for message in ("", "grill", "ทำไฟล์ word ให้หน่อย", "thai-docx", "grill thai-docx",
                    "thaidocx grill", "thai-docx-grill", LONG_REQUEST):
        assert g.mode(message) == "build", message


def test_the_command_says_the_mode_and_the_language():
    asked = run("grill", "--said", "thai-docx grill")
    assert {k: asked[k] for k in ("ok", "mode", "language", "start", "save_to")} == {
        "ok": True, "mode": "grill", "language": "en", "start": None, "save_to": None}
    assert [q["key"] for q in asked["questions"]] == [q["key"] for q in st.QUESTIONS]
    assert all(q["choices"][0]["current"] and q["choices"][0]["args"] == [] for q in asked["questions"]), "no start: a holds"
    thai = run("grill", "--said", "ขอ thai-docx grill หน่อย")
    assert thai["language"] == "th" and thai["questions"][0]["text"] == "ฟอนต์"
    built = run("grill", "--said", LONG_REQUEST)
    assert built["mode"] == "build" and "ask nothing first" in built["next"]
    assert "language" not in built and "questions" not in built, "the questions come only with grill mode"


def test_the_words_after_the_phrase_are_read_in_either_language():
    """ADR 0029: from, save to and only — or จาก, บันทึกเป็น and เฉพาะ — directly after the
    phrase, as the user wrote the names; the first other word ends the reading."""
    assert g.parts("thai-docx grill") == {}
    assert g.parts("thai-docx grill from Thesis_A save to thesis-v1") == {"from": "Thesis_A", "save_to": "thesis-v1"}
    assert g.parts("THAI_DOCX GRILL Save To v2 only font,3") == {"save_to": "v2", "only": "font,3"}
    assert g.parts("ขอ thai-docx grill จาก thesis บันทึกเป็นthesis-v1 เฉพาะ toc หน่อยนะ") == {
        "from": "thesis", "save_to": "thesis-v1", "only": "toc"}
    assert g.parts("thai-docx grill please from thesis") == {}, "the reading ends at the first other word"
    assert g.parts("ทำไฟล์ thai-docx grillจาก thesis") == {"from": "thesis"}
    for message, error in (("thai-docx grill from a from b", "'from' is given twice"),
                           ("thai-docx grill save to", "'save to' needs a word after it"),
                           ("thai-docx grill จาก", "'from' needs a word after it")):
        with pytest.raises(g.GrillError, match=error):
            g.parts(message)
    for message, error in (("thai-docx grill from nobody", "no profile named 'nobody'"),
                           ("thai-docx grill save to ../x", "'save to' takes a profile name, not a path"),
                           ("thai-docx grill save to .hidden", "is not a name"),
                           ("thai-docx grill only font,margins", "'margins' is not a question"),
                           ("thai-docx grill เฉพาะ ๑", "'๑' is not a question")):
        result = g.run(["--said", message])
        assert result["ok"] is False and error in result["error"], (message, result)


@pytest.fixture()
def home(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    run("profile", "save", "thesis", "--toc", "--size", "15", "--align", "thai", "--margins", "1,1,1,1", "--font", "Angsana New")
    return tmp_path


def _choice(result: dict, key: str, letter: str) -> dict:
    question = next(q for q in result["questions"] if q["key"] == key)
    return next(c for c in question["choices"] if c["letter"] == letter)


def test_a_start_profile_marks_what_holds_and_says_what_each_choice_changes(home):
    asked = g.run(["--said", "thai-docx grill from thesis save to thesis-v1"])
    assert asked["start"]["name"] == "thesis" and asked["start"]["where"] == "home" and asked["save_to"] == "thesis-v1"
    assert "save" not in [q["key"] for q in asked["questions"]], "the save question is answered by the message"
    current = {q["key"]: [c["letter"] for c in q["choices"] if c["current"]] for q in asked["questions"]}
    assert current == {"font": ["d"], "size": ["c"], "paper": ["b"], "align": ["b"], "indent": ["a"],
                       "toc": ["b"], "page-numbers": ["a"], "squiggles": ["a"]}
    assert all(c["args"] == [] for q in asked["questions"] for c in q["choices"] if c["current"] and not c.get("other"))
    assert _choice(asked, "toc", "a")["args"] == ["--default", "toc"], "a no that undoes the profile's yes"
    assert _choice(asked, "size", "a")["args"] == ["--default", "size"] and _choice(asked, "size", "b")["args"] == ["--size", "14"]
    assert _choice(asked, "paper", "c")["args"] == ["--paper", "letter", "--default", "margins"]
    assert _choice(asked, "font", "d")["args"] == ["--font", "NAME"] and _choice(asked, "font", "d")["other"] is True
    assert _choice(asked, "page-numbers", "b")["args"] == ["--page-numbers", "top-right"]
    assert "profile save thesis-v1 --from thesis ARGS" in asked["next"] and "--profile thesis-v1" in asked["next"]
    only = g.run(["--said", "ขอ thai-docx grill จาก thesis เฉพาะ 6,size"])
    assert [q["key"] for q in only["questions"]] == ["size", "toc"] and only["language"] == "th"
    assert "--profile thesis" in only["next"] and "profile save NAME --from thesis ARGS" in only["next"]


def test_the_answers_run_as_next_says_give_the_settings_chosen(home):
    """End to end: the user keeps the thesis profile but answers 2b (14 pt) and 6a (no table
    of contents); the args the command gave, run as `next` says, make exactly that profile,
    and a build with it is the build with those settings written out."""
    asked = g.run(["--said", "thai-docx grill from thesis save to thesis-v1"])
    args = _choice(asked, "size", "b")["args"] + _choice(asked, "toc", "a")["args"]
    saved = run("profile", "save", "thesis-v1", "--from", "thesis", *args)
    assert saved["ok"] and saved["settings"] == {"font": "Angsana New", "size": 14, "align": "thai", "margins": [1.0, 1.0, 1.0, 1.0]}
    (home / "in.md").write_text("# ก\n\nข\n", encoding="utf-8")
    with_profile = run("build", "in.md", "a.docx", "--profile", "thesis-v1")
    spelled_out = run("build", "in.md", "b.docx", "--font", "Angsana New", "--size", "14", "--align", "thai", "--margins", "1,1,1,1")
    assert with_profile["sha256"] == spelled_out["sha256"]
    # the same answers without saving: the start profile, less what --default takes back
    once = run("build", "in.md", "c.docx", "--profile", "thesis", *args)
    assert once["sha256"] == spelled_out["sha256"] and once["settings"]["toc"] is False


def test_a_message_the_command_did_not_see_is_no_message():
    for args in (["grill"], ["grill", "--said"], ["grill", "thai-docx grill"],
                 ["grill", "--said", "a", "b"], ["grill", "--message", "thai-docx grill"]):
        assert run(*args)["error"] == g.USAGE, args


def test_the_phrase_is_read_with_a_space_between_the_two_words():
    """ADR 0029: the name's two words may be joined by `-`, `_` or a space, in any case."""
    for said in ("thai-docx grill", "thai_docx grill", "thai docx grill", "Thai Docx Grill",
                 "/thai-docx grill", "ขอ THAI DOCX\tGRILL หน่อย"):
        assert run("grill", "--said", said)["mode"] == "grill", said
    # what the phrase is not: the words joined by anything else, or not joined at all
    # a run of whitespace is one space (plain), so a tab or two spaces still read as the phrase
    assert run("grill", "--said", "thai\tdocx  grill")["mode"] == "grill"
    for said in ("thai.docx grill", "thaidocx grill", "docx grill", "thai docxgrill"):
        assert run("grill", "--said", said)["mode"] == "build", said
    # the words after the phrase are still read from where the phrase ends, whichever
    # way the two words were joined: `from report` names the profile to start from
    assert g.parts("thai docx grill from report") == {"from": "report"}
    assert g.parts("thai-docx grill from report") == {"from": "report"}


def test_the_cap_counts_characters_not_units_of_storage():
    """ADR 0029 says 20,000 characters. A character outside the BMP is one character, so a
    message of 10,000 of them and the phrase is under the cap in both implementations."""
    assert run("grill", "--said", "\U0001F600" * 10000 + " thai-docx grill")["mode"] == "grill"
    assert run("grill", "--said", "\U0001F600" * g.MAX_CHARS + " thai-docx grill")["mode"] == "build"


def test_a_message_read_only_in_part_says_so():
    """A cap that says nothing is a trap: the phrase may be in the part that was dropped."""
    long = run("grill", "--said", "ก" * (g.MAX_CHARS + 5) + " thai-docx grill")
    assert long["mode"] == "build"
    assert "20000 characters" in long["warnings"][0] and "21" in long["warnings"][0]
    assert "warnings" not in run("grill", "--said", "ทำไฟล์ให้หน่อย")


def test_a_very_long_message_is_read_to_its_cap():
    """A message is read to 20,000 characters, as any other input has its bound."""
    assert run("grill", "--said", "ก" * g.MAX_CHARS + " thai-docx grill")["mode"] == "build"
    assert run("grill", "--said", "ก" * 10 + " thai-docx grill")["mode"] == "grill"
    cut = g.run(["--said", "x" * 300000])
    assert cut["mode"] == "build" and cut["next"] == g.run(["--said", "x"])["next"]
    assert cut["warnings"] == ["the message was read to its first 20000 characters; "
                               "280000 were not read, and the phrase may be among them"]
