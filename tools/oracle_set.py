# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Build the synthetic documents a release is opened in, once per application (ADR 0012).

    python3 tools/oracle_set.py OUT_DIR

Each variant is one Markdown fixture and one set of flags. Its file is written once for
every application, named `<variant>-<application>.docx`, with the same bytes in each —
the suffix only says which application a copy, its screenshots and its notes belong to,
after an upload has renamed it. CHECKLIST.md beside them lists what to look at.

The goldens in tests/golden hold the same variants, so the files opened are the files the
tests hold byte for byte.

Role: generator (the documents and the checklist).
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "skills" / "thai-docx" / "scripts"))

from thai_docx import build as b  # noqa: E402

APPLICATIONS = ("word365_windows", "word_mac", "libreoffice_writer", "google_docs", "wps_writer")
# The five-application contract covers the document the skill hands over ready to use. A variant
# built with --auto-numbering is made for Word (ADR 0036, references/limits.md §2): it is opened
# in the reference application, and what the other four draw is recorded in numbering.md rather
# than held to the contract. A variant names the applications it is opened in.
WORD = ("word365_windows",)

# the paragraph, number, page and table options, which sample-options and sample-auto share:
# the pair differs in who counts the numbers and in nothing else
VARIANTS_OPTIONS_FLAGS = [
    "--heading-numbers", "--align", "thai", "--indent", "0.5", "--line-spacing", "1.5", "--thai-digits",
    "--page-numbers", "top-center", "--no-page-number-first", "--header", "ข้อมูลสังเคราะห์ ใช้ทดสอบเท่านั้น",
    "--footer", "มหาวิทยาลัยตัวอย่าง", "--front-page-numbers", "lower-roman", "--appendix-numbers", "upper-letters",
    "--appendix-label", "Appendix", "--table-widths", "auto", "--table-size", "14",
]

# name → (fixture, flags, golden in tests/golden, what this variant is there to show)
VARIANTS = {
    "sample-basic": (FIXTURES / "sample.md", [], "sample-default",
                     "Every Markdown construct once, on the defaults.", APPLICATIONS),
    "sample-text": (FIXTURES / "thesis" / "thesis.md", ["--heading-numbers", "--page-numbers", "bottom-center"], "thesis-text",
                    "A thesis: cover, front pages, chapters, bibliography, appendices; captions and lists; long paragraphs.", APPLICATIONS),
    "sample-options": (FIXTURES / "thesis" / "thesis.md", VARIANTS_OPTIONS_FLAGS, "thesis-options",
                       "The same thesis with the paragraph, number, page and table options.", APPLICATIONS),
    "sample-layout": (FIXTURES / "thesis" / "thesis.md", [
        "--paper", "f14", "--landscape", "--size", "15", "--margins", "1,1,1,1", "--toc",
        "--no-repeat-table-header", "--hide-spelling-errors", "--table-widths", "auto",
    ], "thesis-layout", "The same thesis on F14 landscape, with the settings flags.", APPLICATIONS),
    # the same thesis as sample-options, with the same flags, and the application counting: the
    # two files differ in the numbering and in nothing else, which is what this mode promises
    "sample-auto": (FIXTURES / "thesis" / "thesis.md", [*VARIANTS_OPTIONS_FLAGS, "--auto-numbering"], "thesis-auto",
                    "The same thesis with the application counting (ADR 0036): open it, then edit it. "
                      "Made for Word 365 for Windows on the desktop, so it is opened there and nowhere else. The contract of "
                      "ADR 0012 covers the ready-to-use documents above; Word on the web is not covered for this mode (it cannot "
                      "insert a section break), and what every other application draws with --auto-numbering is recorded in "
                      "references/numbering.md.", WORD),
}

# ADR 0012's items, then what each variant adds
EVERY_APPLICATION = (
    "Content complete: nothing missing against the Markdown",
    "(Word) Type a Latin word into a paragraph, and insert a table from the ribbon: both come out in the document's "
    "font, and the font box names it",
    "SARA AM sits over its own letter: กำหนด ทำงาน คำสำคัญ สม่ำเสมอ — in WPS Writer above all, which is what "
    "the default not writing the Thai language buys (ADR 0038)",
    "(Word) No red underline under a correctly spelled Thai word — on a machine with Thai among its languages, "
    "which is what the default relies on",
    "Bold and italic render on Thai",
    "Bullets show as •; numbered lists count on",
    "Thai lines break inside words, not only at spaces",
    "The font is applied (TH Sarabun New, or the one the flags name)",
    "Tables, links and headings are correct",
    "Footnotes are numbered at the foot of the page",
    "Images stay within the page",
    "□ and ■ show as squares, not as blank space (ADR 0033)",
)
WORD_ONLY = (
    'No "Compatibility Mode" in the title bar',
    "The status bar shows Thai",
    "No squiggles under correctly spelled words",
)
SHOWS = {
    "sample-text": (
        "Cover has no page number; front pages count ก ข ค — note what page 3 shows (ค, or ฃ)",
        "Every # starts a new page; chapter 1 restarts page numbers at 1, at the bottom centre",
        "Headings read บทที่ 1 …, 1.1 …; appendices ภาคผนวก ก, ข, ค; bibliography and ประวัติผู้เขียน unnumbered",
        "The number of a heading (บทที่ 1, 1.1, ภาคผนวก ก) is its heading's size, font and weight, not the body's",
        "Captions read ตารางที่ 1-1, รูปที่ 2-1, ตารางที่ ก-1 — before and after updating fields",
        "Table of contents, list of tables and list of figures fill in after updating fields, in TH Sarabun New",
        "The 40-row results table repeats its header row on every page",
        "Heading 1 centred 20 pt; Heading 2 blue 18 pt; Heading 3 italic",
        "Table cells keep text off the borders; rows no taller than their text",
    ),
    "sample-options": (
        "Body paragraphs Thai distributed, first line indented 0.5 in, line spacing 1.5",
        "The line before a hard break (chapter 1, the paragraph with H₂SO₄ and Ctrl + S) is not spread letter by letter",
        "Front pages count i ii iii; the first page of every section has no number; numbers top centre",
        "Page, list, footnote, heading and caption numbers in Thai digits (๑ ๒ ๓); ตารางที่ ๑-๑",
        "Appendix headings read Appendix A, B, C; captions ตารางที่ A-1",
        "Header text on every page above the page number; footer text on every page",
        "Table columns sized by their text; table text 14 pt",
        "บทคัดย่อ and Abstract, both level 1, are centred alike — an English heading takes its style's alignment (2026-09-19)",
    ),
    "sample-layout": (
        "F14 (8.5 × 13 in) landscape pages; margins 1 in all round; body 15 pt",
        "A table of contents on the cover as well as the one in the front pages (on purpose: the build warns that --toc adds a second)",
        "The long table does not repeat its header row",
        "No spelling squiggles at all",
    ),
    "sample-auto": (
        "As the file opens, before anything is updated: headings read บทที่ ๑, ๑.๑, ๑.๓.๒; appendices ภาคผนวก ก; "
        "captions ตารางที่ ๑-๑, รูปที่ ๒-๑, ตารางที่ ก-๑; numbered lists ๑. ๒. ๓.",
        "After updating every field (Word: Ctrl+A then F9) the captions and the three lists read as they did before",
        "(edit) A new paragraph in the Heading 2 style typed after ๑.๑ takes ๑.๒, and the headings after it move on by one",
        "(edit) A new Heading 1 typed before บทที่ ๒ takes บทที่ ๒; after updating fields the captions below it read ตารางที่ ๓-๑, รูปที่ ๓-๑",
        "(edit) A table caption copied and pasted later in the same chapter takes the next number after updating fields, "
        "and the list of tables gains it",
        "(edit) Everything the ready-to-use variants carry is here too: Thai distributed body, the first-line indent, "
        "line spacing, the heading styles, the chapter and appendix labels, the page numbering of each region",
        "(edit) References → Insert Caption already offers the document's labels (ตารางที่, รูปที่), "
        "numbered by chapter in the document's digits, above a table and below a figure — and the caption it inserts "
        "continues the document's count instead of starting again at 1",
        "(edit) A new item typed inside a numbered list takes the next number, and the items after it move on by one",
    ),
}


# What only the application open can show: typing, editing, updating fields, proofing marks and
# what Word shows around the page. Everything else is on the page as drawn, which a PDF the
# application exports, or a screenshot, shows as well (tools/render_libreoffice.py).
OPEN_PREFIXES = ("(Word)", "(edit)", "(Word only)")
OPEN_WORDS = ("underline", "squiggle", "updating", "status bar", "title bar", "font box", "Compatibility Mode")


def how_read(item: str) -> str:
    """`open` when the item needs the application open, `page` when the drawn page shows it."""
    return "open" if item.startswith(OPEN_PREFIXES) or any(word in item for word in OPEN_WORDS) else "page"


def write(out: pathlib.Path) -> list[dict]:
    """Every variant for every application into `out`, and CHECKLIST.md; the build results."""
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for variant, (source, flags, _golden, _about, applications) in VARIANTS.items():
        for application in applications:
            target = out / f"{variant}-{application}.docx"
            opts, _, allow = b.parse_args(flags + [str(source), str(target)])
            result = b.build(str(source), str(target), opts, allow)
            results.append({"variant": variant, "application": application, **result})
    (out / "CHECKLIST.md").write_text(checklist(results), encoding="utf-8")
    return results


def checklist(results: list[dict]) -> str:
    lines = ["# Release oracle checklist (ADR 0012)", "",
             "Open each file in the application its name ends with. Tick an item when it holds;",
             "a failure that attributes cannot reach gets a known-limitation record.", "",
             "`read`: **page** — on the page as drawn, which a PDF the application exports, or a screenshot,",
             "shows too (`python3 tools/render_libreoffice.py DIR` exports LibreOffice's); **open** — only",
             "with the application open: typing, editing, updating fields, proofing marks, the status bar.", ""]
    for variant, (source, flags, golden, about, applications) in VARIANTS.items():
        sha = {r["sha256"] for r in results if r["variant"] == variant}
        lines += [f"## {variant}", "", about, "",
                  f"- Source: `{source.relative_to(ROOT)}`, flags: `{' '.join(flags) or '(none)'}`",
                  f"- sha256 (every copy, and tests/golden/{golden}.docx): `{', '.join(sorted(sha))}`", ""]
        items = [*EVERY_APPLICATION, *SHOWS.get(variant, ())]
        lines += ["| item | read | " + " | ".join(applications) + " |", "|---|---|" + "---|" * len(applications)]
        lines += ["| " + item + " | " + how_read(item) + " |" + " |" * len(applications) for item in items]
        word_cells = " |" * len(applications) if applications == WORD else " | | — | — | —"
        lines += ["| (Word only) " + item + " | open |" + word_cells + " |" if applications != WORD
                  else "| (Word only) " + item + " | open | |" for item in WORD_ONLY]
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    # a first word that begins with - is a question or a flag, never the directory to write
    # into: `--help` once made a directory of that name and stopped with a trace inside it
    if len(argv) != 1 or argv[0].startswith("-"):
        print(__doc__.split("\n\n")[1].strip())
        return 2
    results = write(pathlib.Path(argv[0]))
    failed = [r for r in results if not r["ok"]]
    for r in results:
        print(("ok   " if r["ok"] else "FAIL ") + r["variant"] + "-" + r["application"] + ".docx", r.get("sha256", r.get("error", r.get("findings"))))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
