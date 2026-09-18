# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""thai_docx — build a Thai-correct .docx from Markdown, or check one.

    python3 scripts/thai_docx check   FILE.docx
    python3 scripts/thai_docx build   IN.md OUT.docx [flags]
    python3 scripts/thai_docx profile list | show | save | export | import
    python3 scripts/thai_docx grill   --said "the user's own message"

Standard library only; no network, no subprocesses (ADR 0030).
"""

from __future__ import annotations

import json
import pathlib
import sys

if __package__ in (None, ""):
    # `python3 scripts/thai_docx …` runs this file as a script, not a package.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from thai_docx import build, check, grill, profiles
else:
    from . import build, check, grill, profiles


def main(argv: list[str]) -> int:
    if argv and argv[0] == "check":
        return check.main(argv[1:])
    if argv and argv[0] == "build":
        return build.main(argv[1:])
    if argv and argv[0] == "profile":
        return profiles.main(argv[1:])
    if argv and argv[0] == "grill":
        return grill.main(argv[1:])
    print(json.dumps({"ok": False, "error": "usage: thai_docx check FILE.docx | build IN.md OUT.docx | profile ... | grill --said ..."}))
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
