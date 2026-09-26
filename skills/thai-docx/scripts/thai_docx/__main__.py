# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""thai_docx — build a Thai-correct .docx from Markdown, or check one.

    python3 scripts/thai_docx check   FILE.docx
    python3 scripts/thai_docx build   IN.md OUT.docx [flags]
    python3 scripts/thai_docx repair  IN.docx OUT.docx
    python3 scripts/thai_docx profile list | show | save | export | import
    python3 scripts/thai_docx grill   --said "the user's own message"

Standard library only; no network, no subprocesses (ADR 0030).
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

if __package__ in (None, ""):
    # `python3 scripts/thai_docx …` runs this file as a script, not a package.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from thai_docx import build, check, grill, profiles, repair
else:
    from . import build, check, grill, profiles, repair


COMMANDS = {"check": check.main, "build": build.main, "repair": repair.main, "profile": profiles.main, "grill": grill.main}


def not_text(arg: str) -> bool:
    """An argument that held bytes of another encoding. Python keeps each such byte as a lone
    surrogate; Node puts U+FFFD in its place and cannot tell it from one typed, so both refuse
    either, and give the same answer for the same argument."""
    return "\ufffd" in arg or any("\ud800" <= c <= "\udfff" for c in arg)


def refuse(message: str, code: int) -> int:
    print(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
    return code


def main(argv: list[str]) -> int:
    bad = next((i for i, arg in enumerate(argv) if not_text(arg)), None)
    if bad is not None:
        return refuse("argument " + str(bad + 1) + " is not UTF-8 text; a name or value in another encoding cannot be read", 2)
    try:
        os.getcwd()
    except OSError:
        return refuse("the working directory no longer exists; run the command from one that does", 2)
    command = COMMANDS.get(argv[0]) if argv else None
    if command is None:
        return refuse("usage: thai_docx check FILE.docx | build IN.md OUT.docx"
                      " | repair IN.docx OUT.docx | profile ... | grill --said ...", 2)
    try:
        return command(argv[1:])
    except Exception:  # noqa: BLE001  whatever it was, the answer is still one JSON line
        # SKILL.md reads exit 1 as a defect in this skill: that is what this is
        return refuse("a defect in thai-docx stopped this command; do not retry — report it with the input that caused it", 1)


if __name__ == "__main__":
    # the JSON line is UTF-8 whatever the terminal or pipe was set to, as Node writes it
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
