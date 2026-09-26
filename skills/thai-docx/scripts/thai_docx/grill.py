# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Grill mode is the user's word, not the agent's choice (ADR 0029, restating 0026).

The skill's instructions cannot stop a model from choosing the interview for the user —
a request that lists settings reads like an invitation to ask about them. So the decision
is taken out of the reading: the agent hands this command the user's own message and the
command, not the model, says which mode the build is in — and, in grill mode, which
questions to ask, which choice each setting holds now, and what every choice means.

    thai_docx grill --said "ช่วยทำไฟล์ word ให้หน่อย"                        → {"mode": "build"}
    thai_docx grill --said "thai-docx grill"                                → {"mode": "grill", "questions": [...]}
    thai_docx grill --said "thai-docx grill from thesis save to thesis-v1"  → starting from a profile
"""

from __future__ import annotations

import json
import re
import unicodedata

from . import profiles as pf
from . import settings as st

USAGE = 'usage: thai_docx grill --said "the user\'s own message, word for word"'

# The phrase that turns the interview on. Written with any of - _ or a space between the
# two words of the skill's name, in any case, anywhere in the message; `/thai-docx grill`
# holds it too.
# `fold` reads `_` as `-`; the space is the third way ADR 0029 lets the two words of the
# name be joined, and it cannot be folded — a space is what separates the phrase's own
# words — so the pattern allows it there and nowhere else.
PHRASE = re.compile(r"thai[- ]docx grill")
MAX_CHARS = 20000
# the words that may follow the phrase (ADR 0029): part → (English, Thai)
PARTS = {"from": ("from", "จาก"), "save_to": ("save to", "บันทึกเป็น"), "only": ("only", "เฉพาะ")}

THAI_FIRST, THAI_LAST = "฀", "๿"
# What separates words, one list written out for both implementations: str.isspace() and the
# JavaScript \s disagreed on U+001C, U+0085 and U+FEFF, so one read `from test` and the other
# did not. The spaces a person types, and no others.
WHITESPACE = frozenset(" \t\n\r\f\v\u00a0\u3000")


class GrillError(Exception):
    def __init__(self, what: str):
        super().__init__(what)
        self.what = what


def fold(text: str) -> str:
    """ASCII case folded and `_` read as `-`: one character for one, so positions hold."""
    return "".join(chr(ord(ch) + 32) if "A" <= ch <= "Z" else "-" if ch == "_" else ch for ch in text)


def words(message: str) -> list[str]:
    out, current = [], ""
    for ch in message:
        if ch in WHITESPACE:
            if current:
                out.append(current)
            current = ""
        else:
            current += ch
    return out + [current] if current else out


def plain(message: str) -> str:
    """The message as the phrase is looked for in it: ASCII case folded, `_` read as `-`,
    every run of whitespace one space. ASCII only, so both implementations fold alike."""
    return fold(" ".join(words(message)))


def language(message: str) -> str:
    """The language the questions are asked in: the one most of the user's words are in, the
    phrase aside — Thai on a tie. One Thai title in an English request is not a Thai request."""
    at = PHRASE.search(plain(message))
    said = plain(message)
    said = said[:at.start()] + said[at.end():] if at else said
    thai = latin = 0
    for word in said.split(" "):
        if any(THAI_FIRST <= ch <= THAI_LAST for ch in word):
            thai += 1
        elif any("a" <= ch <= "z" for ch in word):
            latin += 1
    return "th" if thai and thai >= latin else "en"


def mode(message: str) -> str:
    return "grill" if PHRASE.search(plain(message)) else "build"


# `from` goes back to the agent inside a command it will run: a name is held to check_name,
# and a path to the characters a path needs and no shell reads
PATH_MARKS = "-_./\\:"


def _carried(source: str) -> None:
    if not pf.is_path(source):
        pf.check_name(source)
    elif not all(c in PATH_MARKS or unicodedata.category(c)[0] in "LMN" for c in source):
        raise GrillError("'from' is carried into a command, so a path there holds letters, digits and "
                         + " ".join(PATH_MARKS) + " only: " + source)


def _part_at(rest: list[str], i: int) -> tuple[str | None, int, str | None]:
    """The part whose words begin at `rest[i]`, where its value begins, and the value when
    the Thai word carries it joined on (`บันทึกเป็นv2`)."""
    for name, (english, thai) in PARTS.items():
        said = english.split(" ")
        if [fold(w) for w in rest[i:i + len(said)]] == said:
            return name, i + len(said), None
        if rest[i].startswith(thai):
            return name, i + 1, rest[i][len(thai):] or None
    return None, i, None


def _after_phrase(message: str) -> list[str]:
    joined = " ".join(words(message))
    rest = joined[PHRASE.search(plain(message)).end():].split(" ")
    return rest[1:] if rest and rest[0] == "" else rest


def unread(message: str) -> str | None:
    """A `from`, `save to` or `only` later in the message than the reading went, with the
    word after it: said, it would be lost without a word, and the user answers nine
    questions believing the interview began from their profile."""
    rest = _after_phrase(message)
    _found, stop = _read(rest)
    for j in range(stop, len(rest)):
        part, value_at, joined = _part_at(rest, j)
        if part is not None:
            return " ".join(rest[j:value_at + (0 if joined else 1)])
    return None


def parts(message: str) -> dict:
    """`from`, `save to` and `only`, read from the words directly after the phrase, as the
    user wrote them; the first word that is none of them ends the reading."""
    return _read(_after_phrase(message))[0]


def _read(rest: list[str]) -> tuple[dict, int]:
    found: dict = {}
    i = 0
    while i < len(rest):
        part, at, value = _part_at(rest, i)
        if part is None:
            break
        i = at
        if part in found:
            raise GrillError("'" + PARTS[part][0] + "' is given twice")
        if value is None:
            if i >= len(rest):
                raise GrillError("'" + PARTS[part][0] + "' needs a word after it")
            value, i = rest[i], i + 1
        found[part] = value
    return found, i


def _same(a, b) -> bool:
    """Two values of one setting: lists item by item, numbers as numbers (16 and 16.0 alike).
    A setting never mixes booleans and numbers, so False and 0 need no rule (L-0003)."""
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b, strict=True))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    return a == b


def _args(chosen: dict, now: dict) -> list[str]:
    """The flags that make a choice true against the settings in force: nothing for what
    already holds, `--default` for a setting going back to its default, its flag otherwise."""
    changed = {k: v for k, v in chosen.items() if not _same(v, now[k])}
    reset = [k for k in changed if _same(changed[k], st.DEFAULTS[k])]
    out = pf.as_flags({k: v for k, v in changed.items() if k not in reset})
    return out + (["--default", ",".join(reset)] if reset else [])


def questions(now: dict, lang: str, only: list[str] | None, save_to: str | None) -> list[dict]:
    k = 0 if lang == "th" else 1
    out = []
    for number, q in enumerate(st.QUESTIONS, 1):
        if (save_to is not None and q["key"] == "save") or (only is not None and q["key"] not in only):
            continue
        choices, matched = [], False
        for letter, c in zip("abcd", q["choices"], strict=False):
            choice: dict = {"letter": letter, "label": c["label"][k]}
            if "set" in c:
                choice["current"] = all(_same(v, now[key]) for key, v in c["set"].items())
                choice["args"] = _args(c["set"], now)
                matched = matched or choice["current"]
            elif "other" in c:
                choice["args"] = [a for key, placeholder in c["other"].items() for a in (st.BY_KEY[key]["flag"], placeholder)]
                choice["other"] = True
            else:
                choice["current"] = c["save"] is None
                choice["args"] = []
                choice["save"] = c["save"]
            choices.append(choice)
        for choice in choices:
            if choice.get("other"):
                choice["current"] = not matched
        out.append({"number": number, "key": q["key"], "text": q["text"][k], "choices": choices})
    return out


def run(argv: list[str]) -> dict:
    if len(argv) != 2 or argv[0] != "--said":
        return {"ok": False, "error": USAGE}
    message = argv[1]
    cut = len(message) - MAX_CHARS
    if cut > 0:
        # the cap is a decision (ADR 0029), but a cap that says nothing is a trap: the phrase
        # may be in the part that was dropped, and the agent would read "build" as the answer
        message = message[:MAX_CHARS]
    if mode(message) != "grill":
        answer = {"ok": True, "mode": "build",
                  "next": "build at once with the announced defaults; ask nothing first"}
        if cut > 0:
            answer["warnings"] = ["the message was read to its first " + str(MAX_CHARS) + " characters; "
                                  + str(cut) + " were not read, and the phrase may be among them"]
        return answer
    try:
        found = parts(message)
        start, now = None, dict(st.DEFAULTS)
        if "from" in found:
            _carried(found["from"])
            data, where, path = pf.load(found["from"])
            now, _, _ = st.parse_args(pf.as_flags(data["settings"]) + ["in.md", "out.docx"])
            start = {"name": found["from"], "where": where, "path": str(path), "settings": data["settings"]}
        save_to = found.get("save_to")
        if save_to is not None:
            if pf.is_path(save_to):
                raise GrillError("'save to' takes a profile name, not a path: " + save_to)
            pf.check_name(save_to)
        only = None
        if "only" in found:
            keys = [q["key"] for q in st.QUESTIONS]
            only = []
            for key in found["only"].split(","):
                key = keys[int(key) - 1] if re.fullmatch(r"[0-9]{1,2}", key) and 1 <= int(key) <= len(keys) else fold(key)
                if key not in keys:
                    raise GrillError("'" + key + "' is not a question; the questions are " + ", ".join(keys))
                only.append(key)
    except (GrillError, pf.ProfileError) as exc:
        return {"ok": False, "error": exc.what}
    lang = language(message)
    base = "--from " + found["from"] + " " if start else ""
    if save_to is not None:
        then = "run `thai_docx profile save " + save_to + " " + base + "ARGS`, then build with `--profile " + save_to + "`"
    else:
        then = ("build with " + ("`--profile " + found["from"] + "` and " if start else "") + "ARGS; for a save choice, first run"
                " `thai_docx profile save NAME " + base + "ARGS` (add `--project` for the project) and build with `--profile NAME`")
    answer = {"ok": True, "mode": "grill", "language": lang, "start": start, "save_to": save_to,
              "questions": questions(now, lang, only, save_to),
              "next": "ask these questions as references/interview.md says, the current choice marked; an unanswered"
                      " question keeps its current choice. ARGS are the args of the chosen choices, in order, with the"
                      " user's value in place of a placeholder. Then " + then}
    stray = unread(message)
    if stray is not None:
        answer["warnings"] = ["'" + stray + "' was not read: from, save to and only are read only directly after"
                              " the phrase, so tell the user, and ask whether to start again with it there"]
    return answer


def main(argv: list[str]) -> int:
    result = run(argv)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 2
