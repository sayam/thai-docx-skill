"""thai_docx — build a Thai-correct .docx from Markdown, or check one.

    python3 scripts/thai_docx check  FILE.docx
    python3 scripts/thai_docx build  IN.md OUT.docx [flags]     (not yet: v0.1)

Standard library only; no network, no subprocesses (ADR 0011).
"""

from __future__ import annotations

import json
import pathlib
import sys

if __package__ in (None, ""):
    # `python3 scripts/thai_docx …` runs this file as a script, not a package.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from thai_docx import check
else:
    from . import check


def main(argv: list[str]) -> int:
    if argv and argv[0] == "check":
        return check.main(argv[1:])
    if argv and argv[0] == "build":
        print(json.dumps({"ok": False, "error": "build is not implemented yet"}))
        return 2
    print(json.dumps({"ok": False, "error": "usage: thai_docx check FILE.docx | build IN.md OUT.docx"}))
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
