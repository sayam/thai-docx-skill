# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""What the review of 0.2.0 found an agent or a reader would be misled by, held line by line.

Each case is a sentence that sent a model the wrong way, or a reader to a command that does not
run where they are: a change that dropped the settings of the last build, an exit code read as
a defect, an example that asked for a table of contents nobody wanted, two sentences on the
grill argument that pointed opposite ways, a path with no `<skill>/` in front, a Thai word no
twelve-year-old reads. Whether a model now does better is measured by the model-equivalence
runs, not here; this holds that the words are there to read.
"""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "thai-docx"
SKILL_MD = (SKILL / "SKILL.md").read_text(encoding="utf-8")
REF = {p.stem: p.read_text(encoding="utf-8") for p in (SKILL / "references").glob("*.md")}
GUIDE = {lang: {p.stem: p.read_text(encoding="utf-8") for p in (ROOT / "docs" / "guide" / lang).glob("*.md")} for lang in ("en", "th")}


def section(text: str, heading: str) -> str:
    return text.split("\n## " + heading, 1)[1].split("\n## ", 1)[0]


def test_a_change_keeps_the_flags_of_the_last_build():
    assert "every flag of the last build plus the flags for what they now ask" in section(SKILL_MD, "Settings")


def test_exit_1_is_read_as_the_command_that_gave_it():
    assert "these are `build`'s" in SKILL_MD
    check = section(SKILL_MD, "Check an existing .docx")
    assert "`check` exits 1 when the user's file has findings" in check and "not a defect" in check
    assert "not a defect in this skill" in " ".join(REF["check"].split())


def test_a_file_the_user_gave_is_changed_only_as_they_say():
    assert "In a file the user gave you, tell them the line" in SKILL_MD


def test_a_document_this_skill_did_not_build_is_never_rewritten_with_code():
    assert "Never rewrite the file with document code" in section(SKILL_MD, "Check an existing .docx")


def test_the_grill_argument_is_passed_whole():
    grill = section(SKILL_MD, "Grill mode")
    assert "is not the user's word" not in grill and "the argument you were invoked with included" in grill
    assert re.search(r"grill --said '[^']+'", grill), "single quotes, so the shell changes nothing"
    assert "`=`" in REF["interview"] and "9b=my-thesis" in REF["interview"]


def test_the_markdown_is_shown_with_the_build_and_nothing_is_asked():
    assert "in the same reply" in SKILL_MD and "ask or keep it plain" not in REF["specs"]
    assert "do not ask" in REF["specs"]


def test_every_command_names_both_runtimes_and_the_skill_directory():
    assert "`node <skill>/scripts/thai_docx.js` in place of `python3 <skill>/scripts/thai_docx`" in SKILL_MD
    for name, text in REF.items():
        for block in re.findall(r"```sh\n(.*?)```", text, re.S):
            for line in block.splitlines():
                if "scripts/thai_docx" in line:
                    assert "<skill>/scripts/thai_docx" in line, (name, line)


def test_the_no_shell_example_asks_for_nothing_nobody_asked_for():
    snippet = re.search(r"```js\n(.*?)```", REF["sandbox"], re.S).group(1)
    assert 'buildDocument(markdown, [],' in snippet and '["--toc"]' not in snippet


def test_page_numbers_mean_the_same_on_every_page():
    assert "| page numbers | `--page-numbers` (top right)" in REF["chapters"]


def test_the_check_page_says_what_its_warnings_are():
    assert "`warnings` never fail the check" in REF["check"]


def test_every_relative_link_the_skill_carries_reaches_a_file():
    for text, base in [(SKILL_MD, SKILL)] + [(t, SKILL / "references") for t in REF.values()]:
        text = re.sub(r"^(`{3,}).*?^\1", "", text, flags=re.S | re.M)  # an example's own links are the example's
        text = re.sub(r"(`+)(?!`).+?(?<!`)\1(?!`)", "", text)  # and a code span's, of any number of backticks
        for target in re.findall(r"\]\(((?!https?:|#|mailto:)[^)#\s]+)", text):
            assert (base / target).exists(), target


def test_the_command_line_guide_serves_windows_too():
    for lang in ("en", "th"):
        page = GUIDE[lang]["command-line"]
        assert "Expand-Archive thai-docx-" in page and "%USERPROFILE%" in page, lang


def test_the_thai_guides_use_one_word_for_a_flag():
    pages = "\n".join(GUIDE["th"].values()) + (ROOT / "docs" / "guide" / "th.md").read_text(encoding="utf-8")
    assert "ธง" not in pages
    assert "| ตัวเลือก (flag) |" in pages and "| อักษรซับซ้อน (complex script) |" in pages


def test_the_phrase_is_described_as_the_script_reads_it():
    assert "with the hyphen" not in GUIDE["en"]["scenarios"] and "(มีขีดกลาง)" not in GUIDE["th"]["scenarios"]


def test_the_english_prompt_page_carries_the_trouble_table():
    prompt = (ROOT / "PROMPT.md").read_text(encoding="utf-8")
    assert "not *Source code*" in prompt
    above = prompt.split("\n---\n", 1)[0]
    assert len(re.findall(r"^\| [^|-][^|]* \| [^|]+ \|$", above, re.M)) == 8  # the header and seven rows
