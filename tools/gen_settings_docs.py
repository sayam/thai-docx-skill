"""Write the settings reference the agent reads from the settings registry (ADR 0028).

    python3 tools/gen_settings_docs.py           # write skills/thai-docx/references/settings.md
    python3 tools/gen_settings_docs.py --check   # exit 1 if the committed file is stale

Role: generator (writes the reference) and decider (`--check`).
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "thai-docx"
OUT = SKILL / "references" / "settings.md"
sys.path.insert(0, str(SKILL / "scripts"))

from thai_docx import settings as st  # noqa: E402

# what a layer is for, as the agent needs to know it before choosing a flag
INTRO = {
    1: "Every document has these.",
    2: "The header and footer, and how Word draws the numbers it generates.",
    3: "These change only a document that has tables.",
    4: "These change only a document that has headings.",
    5: "These change only a document with region comments or `Table:` / `Figure:` captions — "
       "[chapters.md](chapters.md).",
}


def render() -> str:
    out = [
        "# Settings",
        "",
        "Generated from the settings registry by `tools/gen_settings_docs.py`; do not edit by hand.",
        "",
        "The defaults, and the flag that changes each one. Add a flag only for what the user asked",
        "for; every other setting keeps its default.",
    ]
    for layer, title in st.LAYERS.items():
        out += ["", "## " + title[0].upper() + title[1:], "", INTRO[layer], "", "| setting | default | flag |", "|---|---|---|"]
        for s in st.SETTINGS:
            if s["layer"] == layer:
                name, shows, flag = s["doc"]
                out.append("| " + name + " | " + shows + " | " + flag + " |")
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    text = render()
    if argv == ["--check"]:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("skills/thai-docx/references/settings.md is stale: run python3 tools/gen_settings_docs.py")
            return 1
        print("settings reference is current")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print("wrote " + str(OUT.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
