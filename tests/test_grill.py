"""Grill mode is the user's word (ADR 0026): the mode comes from the message the user
typed, read by the script, not from what a model makes of the request."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

from thai_docx import grill as g

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
    assert asked == {"ok": True, "mode": "grill", "language": "en",
                     "questions": "references/interview.md",
                     "next": "ask the nine questions exactly as references/interview.md gives them, then build"}
    assert run("grill", "--said", "ขอ thai-docx grill หน่อย")["language"] == "th"
    built = run("grill", "--said", LONG_REQUEST)
    assert built["mode"] == "build" and "ask nothing first" in built["next"]
    assert "language" not in built, "the language matters only when questions are asked"


def test_a_message_the_command_did_not_see_is_no_message():
    for args in (["grill"], ["grill", "--said"], ["grill", "thai-docx grill"],
                 ["grill", "--said", "a", "b"], ["grill", "--message", "thai-docx grill"]):
        assert run(*args)["error"] == g.USAGE, args


def test_a_very_long_message_is_read_to_its_cap():
    """A message is read to 20,000 characters, as any other input has its bound."""
    assert run("grill", "--said", "ก" * g.MAX_CHARS + " thai-docx grill")["mode"] == "build"
    assert run("grill", "--said", "ก" * 10 + " thai-docx grill")["mode"] == "grill"
    assert g.run(["--said", "x" * 300000]) == {"ok": True, "mode": "build", "next": g.run(["--said", "x"])["next"]}
