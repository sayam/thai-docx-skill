"""Grill mode is the user's word, not the agent's choice (ADR 0026).

The skill's instructions cannot stop a model from choosing the interview for the user —
a request that lists settings reads like an invitation to ask about them. So the decision
is taken out of the reading: the agent hands this command the user's own message and the
command, not the model, says which mode the build is in.

    thai_docx grill --said "ช่วยทำไฟล์ word ให้หน่อย"      → {"mode": "build"}
    thai_docx grill --said "thai-docx grill"              → {"mode": "grill"}
"""

from __future__ import annotations

import json

USAGE = 'usage: thai_docx grill --said "the user\'s own message, word for word"'

# The phrase that turns the interview on. Written with any of - _ or a space between the
# two words of the skill's name, in any case, anywhere in the message; `/thai-docx grill`
# holds it too.
PHRASE = "thai-docx grill"
MAX_CHARS = 20000

THAI_FIRST, THAI_LAST = "฀", "๿"


def plain(message: str) -> str:
    """The message as the phrase is looked for in it: ASCII case folded, `_` read as `-`,
    every run of whitespace one space. ASCII only, so both implementations fold alike."""
    out = []
    space = False
    for ch in message:
        if ch.isspace():
            space = out != []
            continue
        if space:
            out.append(" ")
        space = False
        if "A" <= ch <= "Z":
            ch = chr(ord(ch) + 32)
        out.append("-" if ch == "_" else ch)
    return "".join(out)


def language(message: str) -> str:
    """The language the questions are asked in: Thai when the user wrote any Thai."""
    return "th" if any(THAI_FIRST <= ch <= THAI_LAST for ch in message) else "en"


def mode(message: str) -> str:
    return "grill" if PHRASE in plain(message) else "build"


def run(argv: list[str]) -> dict:
    if len(argv) != 2 or argv[0] != "--said":
        return {"ok": False, "error": USAGE}
    message = argv[1]
    if len(message) > MAX_CHARS:
        message = message[:MAX_CHARS]
    if mode(message) == "grill":
        return {"ok": True, "mode": "grill", "language": language(message),
                "questions": "references/interview.md",
                "next": "ask the nine questions exactly as references/interview.md gives them, then build"}
    return {"ok": True, "mode": "build",
            "next": "build at once with the announced defaults; ask nothing first"}


def main(argv: list[str]) -> int:
    result = run(argv)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 2
