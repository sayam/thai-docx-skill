"""SKILL.md tells the agent the truth (ADR 0007, 0014, 0026): it passes the Agent
Skills validator, stays within its ceiling, and every default, flag, finding code,
command and snippet it gives is the one the skill has — run from the archive a user
downloads, not from this checkout.
"""

from __future__ import annotations

import io
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import zipfile

import pytest
from skills_ref.validator import validate

from thai_docx import build as b
from thai_docx import fidelity as fi
from thai_docx import layout as lo
from thai_docx import grill as gr
from thai_docx import profiles as pf

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "thai-docx"
SKILL_MD = (SKILL / "SKILL.md").read_text(encoding="utf-8")
INTERVIEW = (SKILL / "references" / "interview.md").read_text(encoding="utf-8")
HEADING_STYLES = (SKILL / "references" / "heading-styles.md").read_text(encoding="utf-8")
CHAPTERS = (SKILL / "references" / "chapters.md").read_text(encoding="utf-8")
PROFILES = (SKILL / "references" / "profiles.md").read_text(encoding="utf-8")
FIXTURES = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "tools"))
import package_skill  # noqa: E402


def _table(markdown: str, heading: str) -> list[list[str]]:
    """The rows of the first table under `## heading`, header and rule dropped."""
    section = markdown.split("\n## " + heading, 1)[1].split("\n## ", 1)[0]
    rows = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    return [[cell.strip() for cell in row.strip("|").split("|")] for row in rows[2:]]


def _flags(text: str) -> set[str]:
    return set(re.findall(r"(?<![\w-])--[a-z][a-z-]+", text))


@pytest.fixture(scope="module")
def unpacked(tmp_path_factory) -> pathlib.Path:
    """The skill as a user gets it: the release archive, unpacked."""
    where = tmp_path_factory.mktemp("download")
    package_skill.pack(where / "thai-docx.zip")
    zipfile.ZipFile(where / "thai-docx.zip").extractall(where)
    return where / "thai-docx"


# --- the specification ----------------------------------------------------------------


def test_skill_passes_the_agent_skills_validator(unpacked):
    assert validate(SKILL) == []
    assert validate(unpacked) == []


def test_skill_md_stays_within_its_ceiling():
    """Every client loads the whole body when the skill activates, on every model (ADR
    0007): under the specification's 500 lines, and a byte ceiling that makes growth a
    decision rather than a drift."""
    body = SKILL_MD.split("---", 2)[2]
    assert len(body.splitlines()) < 500
    assert len(SKILL_MD.encode("utf-8")) <= 12_000, len(SKILL_MD.encode("utf-8"))
    for link in re.findall(r"\]\(((?:references|scripts|assets)/[^)#]+)\)", SKILL_MD):
        assert (SKILL / link).is_file(), link


# --- what it says the build does ----------------------------------------------------------


def test_settings_table_states_the_defaults_and_flags_that_change_them():
    d = b.DEFAULTS
    margins = ", ".join(f"{m:g}" for m in d["margins"])
    expected = {
        "font": d["font"],
        "size": f"{d['size']} pt",
        "paper": d["paper"].upper(),
        "orientation": "landscape" if d["landscape"] else "portrait",
        "margins, inches": f"{margins} (top, right, bottom, left)",
        "first-line indent, inches": "none" if not d["indent"] else f"{d['indent']:g}",
        "line spacing": f"{d['line_spacing']:g}",
        "alignment": d["align"],
        "table of contents": "none" if not d["toc"] else "yes",
        "heading numbers": "none" if not d["heading_numbers"] else "yes",
        "page numbers": "none" if not d["page_numbers"] else "yes",
        "header / footer text": "none" if d["header"] is None and d["footer"] is None else "yes",
        "page, list and footnote numbers": "๑ ๒ ๓" if d["thai_digits"] else "1 2 3",
        "spelling squiggles": "hidden" if d["hide_spelling_errors"] else "shown",
        "table column widths": d["table_widths"],
        "table text size": "as the body" if d["table_size"] is None else f"{d['table_size']} pt",
        "caption and chapter labels": f"{d['table_label']}, {d['figure_label']}, {d['chapter_label']}",
        "page numbers before the chapters": {"thai-letters": "ก ข ค"}[d["front_page_numbers"]],
        "appendix numbers": d["appendix_label"] + " " + {"thai-letters": "ก"}[d["appendix_numbers"]],
        "table header row": "repeats on every page" if d["repeat_table_header"] else "first page only",
    }
    key = {
        "font": "font", "size": "size", "paper": "paper", "orientation": "landscape", "margins, inches": "margins", "first-line indent, inches": "indent", "line spacing": "line_spacing", "alignment": "align",
        "table of contents": "toc", "heading numbers": "heading_numbers", "page numbers": "page_numbers", "spelling squiggles": "hide_spelling_errors",
        "page, list and footnote numbers": "thai_digits", "header / footer text": "header",
        "table header row": "repeat_table_header", "table column widths": "table_widths", "table text size": "table_size", "caption and chapter labels": "table_label",
        "page numbers before the chapters": "front_page_numbers", "appendix numbers": "appendix_numbers",
    }
    rows = _table(SKILL_MD, "Settings")
    assert {r[0]: r[1] for r in rows} == expected
    for name, _, flag in rows:
        example = shlex.split(re.search(r"`([^`]+)`", flag).group(1))
        opts, _, _ = b.parse_args(example + ["in.md", "out.docx"])
        changed = {k for k in opts if opts[k] != b.DEFAULTS[k]}
        assert changed == {key[name]}, f"{name}: {example} changes {changed or 'nothing'}"


def test_every_flag_named_is_a_flag_the_build_takes_and_every_flag_is_named():
    """Every flag is named where the agent reads it — SKILL.md or a file it sends them to —
    and nothing names a flag the commands do not have."""
    usage = _flags(b.USAGE) | _flags(pf.USAGE) | _flags(gr.USAGE)  # build, profile, grill
    read_by_the_agent = (SKILL_MD, INTERVIEW, CHAPTERS, PROFILES, HEADING_STYLES)
    assert set().union(*(_flags(t) for t in read_by_the_agent)) == usage
    for text in read_by_the_agent:
        assert _flags(text) <= usage


def test_interview_asks_nine_questions_with_choices_in_each_language():
    """ADR 0026: nine fixed questions, choice a the default, the same choices in both
    languages, and a flag or a command for every choice but a."""
    shapes = []
    for language in ("**Thai**", "**English**"):
        block = INTERVIEW.split(language, 1)[1].split("\n**", 1)[0].split("\n## ", 1)[0]
        questions = re.findall(r"^> (\d)\. (.*)$", block, re.M)
        assert [n for n, _ in questions] == [str(n) for n in range(1, 10)], language
        shapes.append([re.findall(r"(?:^| · |— )([a-d])\) ", line) for _, line in questions])
    assert shapes[0] == shapes[1] and all(choices[0] == "a" and len(choices) >= 2 for choices in shapes[0])
    mapped = {row[0] for row in _table(INTERVIEW, "From answers to flags")}
    assert mapped == {str(n) for n, choices in enumerate(shapes[0], 1) if len(choices) >= 2}
    for row in _table(INTERVIEW, "From answers to flags"):
        for flag in re.findall(r"`([^`]+)`", row[2]):
            if "NAME" in flag or " N" in flag or "T,R,B,L" in flag:
                continue
            if flag.startswith("profile ") or flag in _flags(pf.USAGE):  # question 9 runs a command
                continue
            b.parse_args(shlex.split(flag) + ["in.md", "out.docx"])


def test_heading_styles_section_names_every_property_and_its_example_builds():
    """ADR 0020: the table is the parser's list, and the example is one the build takes."""
    documented = [p for row in _table(HEADING_STYLES, "Properties") for p in re.findall(r"`([a-z-]+)`", row[0])]
    assert sorted(documented) == sorted(lo.HEADING_PROPERTIES)
    section = SKILL_MD.split("\n## Heading styles", 1)[1].split("\n## ", 1)[0]
    example = re.search(r"```markdown\n(.*?)```", section, re.S).group(1)
    outcome, data = b.build_text(example + "\n# หัวข้อ\n\n## ย่อย\n", dict(b.DEFAULTS), lambda src: None)
    assert data and outcome["findings"] == [] and outcome["warnings"] == [], outcome
    for value in re.findall(r"`([^`]+)`", "".join(row[1] for row in _table(HEADING_STYLES, "Properties"))):
        if value in ("1pt", "400pt", "#RRGGBB", "1", "3"):
            continue
        for name in re.findall(r"`([a-z-]+)`", next(row[0] for row in _table(HEADING_STYLES, "Properties") if f"`{value}`" in row[1])):
            front = f"---\nheading-1: {name}: {value}\n---\n\n# ก\n"
            if name == "text-decoration" and value in lo.UNDERLINE:
                front = front.replace(value, "underline " + value)
            if name == "font-family":
                continue
            outcome, data = b.build_text(front, dict(b.DEFAULTS), lambda src: None)
            assert data, (name, value, outcome)


def test_chapters_example_builds_as_the_section_says(tmp_path):
    """ADR 0021: the example the agent reads is one the build takes, with the numbers the rules name."""
    example = re.search(r"```markdown\n(.*?)```", CHAPTERS, re.S).group(1)
    section = CHAPTERS.split("\n## The rules", 1)[1]
    png = (FIXTURES / "pixel.png").read_bytes()
    outcome, data = b.build_text(example, dict(b.DEFAULTS), lambda src: (src, png))
    assert data and outcome["findings"] == [] and outcome["warnings"] == [], outcome
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        parts = {n: zf.read(n) for n in zf.namelist()}
    text = fi.docx_text(parts, 0)
    captions = [t for t in text if t.startswith(("ตารางที่", "รูปที่"))]
    assert captions == ["ตารางที่ 1-1 ผลการสำรวจ", "ตารางที่ ก-1 ผู้ตอบแบบสอบถาม",  # the list of tables holds them (ADR 0027)
                        "ตารางที่ 1-1 ผลการสำรวจ", "รูปที่ 1-1 ขั้นตอนการทำงาน", "ตารางที่ ก-1 ผู้ตอบแบบสอบถาม"]
    assert text[1:8] == ["สารบัญ", "สารบัญ", "สารบัญตาราง", "บทที่ 1 บทนำ", "บรรณานุกรม", "ภาคผนวก ก แบบสอบถาม", "ประวัติผู้เขียน"]
    assert "ตารางที่ 1-1" in section and "รูปที่ 1-1" in section and "ตารางที่ ก-1" in section and "ก ข ค" in section
    assert _flags(CHAPTERS) <= _flags(b.USAGE)


def test_finding_codes_table_names_every_code_the_checker_reports():
    source = (SKILL / "scripts" / "thai_docx" / "check.py").read_text(encoding="utf-8")
    emitted = set(re.findall(r'\.find\(\s*"([^"]+)"', source))
    documented = {code for row in _table(SKILL_MD, "Check an existing .docx") for code in re.findall(r"`([^`]+)`", row[0])}
    assert documented == emitted


# --- its commands, run from the download ------------------------------------------------


def _sh_commands(markdown: str) -> list[list[str]]:
    blocks = re.findall(r"```sh\n(.*?)```", markdown, re.S)
    return [shlex.split(line) for block in blocks for line in block.splitlines() if line.strip()]


def _run(argv: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=60)


def test_commands_in_skill_md_run_as_written_from_the_download(unpacked, tmp_path):
    if not shutil.which("node"):
        if os.environ.get("CI"):
            pytest.fail("Node.js is required in CI")
        pytest.skip("Node.js is not installed")
    shutil.copy(FIXTURES / "sample.md", tmp_path / "report.md")
    shutil.copy(FIXTURES / "pixel.png", tmp_path / "pixel.png")
    commands = _sh_commands(SKILL_MD)
    builds = [c for c in commands if "build" in c and "--profile" not in c]
    checks = [c for c in commands if "check" in c]
    profile = [c for c in commands if "profile" in c or "--profile" in c]  # save, build --profile, export, import
    assert len(builds) == 2 and len(checks) == 2 and len(profile) == 4, commands
    outputs = []
    for argv in builds:
        argv = [a.replace("<skill>", str(unpacked)) for a in argv]
        argv[0] = sys.executable if argv[0] == "python3" else argv[0]
        done = _run(argv, tmp_path)
        result = json.loads(done.stdout)
        assert done.returncode == 0 and result["ok"] and done.stderr == "", done.stdout + done.stderr
        outputs.append((tmp_path / "report.docx").read_bytes())
        (tmp_path / "report.docx").rename(tmp_path / "file.docx")
        for check in checks:
            check = [a.replace("<skill>", str(unpacked)) for a in check]
            check[0] = sys.executable if check[0] == "python3" else check[0]
            done = _run(check, tmp_path)
            assert done.returncode == 0 and json.loads(done.stdout)["ok"], done.stdout
    assert outputs[0] == outputs[1], "SKILL.md says both runtimes give the same file"
    # the profile commands, in the order they are written, in a home of this test's own
    env = {**os.environ, "HOME": str(tmp_path / "home"), "USERPROFILE": str(tmp_path / "home")}
    for argv in profile:
        argv = [a.replace("<skill>", str(unpacked)) for a in argv]
        argv[0] = sys.executable if argv[0] == "python3" else argv[0]
        done = subprocess.run(argv, cwd=tmp_path, capture_output=True, text=True, timeout=60, env=env)
        result = json.loads(done.stdout)
        assert done.returncode == 0 and result["ok"] and done.stderr == "", argv[1:]
    assert json.loads((tmp_path / "thesis.json").read_text(encoding="utf-8"))["settings"] == {"size": 15, "align": "thai"}


def test_skill_md_sends_the_mode_decision_to_the_script(unpacked, tmp_path):
    """ADR 0026: SKILL.md does not tell the agent when the interview applies — it tells it
    to hand the script the user's message and obey the mode that comes back. The section
    therefore never names the phrase that turns the interview on: only the script knows it."""
    section = SKILL_MD.split("\n## Grill mode", 1)[1].split("\n## ", 1)[0]
    assert "thai-docx grill" not in section, "the trigger is the script's to know, not the agent's to judge"
    assert '"mode": "build"' in section and '"mode": "grill"' in section
    grill = [c for c in _sh_commands(SKILL_MD) if "grill" in c]
    assert len(grill) == 1 and grill[0][-2] == "--said", grill
    for said, mode in ((grill[0][-1], "build"), ("ขอ thai-docx grill หน่อย", "grill")):
        argv = [a.replace("<skill>", str(unpacked)) for a in grill[0][:-1]] + [said]
        argv[0] = sys.executable if argv[0] == "python3" else argv[0]
        done = _run(argv, tmp_path)
        assert done.returncode == 0 and json.loads(done.stdout)["mode"] == mode, done.stdout


def test_a_refusal_answers_as_skill_md_says(unpacked, tmp_path):
    (tmp_path / "report.md").write_text("ข้อความ\n\nก <span>x</span>\n", encoding="utf-8")
    done = _run([sys.executable, str(unpacked / "scripts" / "thai_docx"), "build", "report.md", "report.docx"], tmp_path)
    result = json.loads(done.stdout)
    assert done.returncode == 2 and "error" in result and result["line"] == 3
    assert not (tmp_path / "report.docx").exists()


def test_the_no_shell_snippet_runs_in_a_bare_sandbox(unpacked):
    if not shutil.which("node"):
        if os.environ.get("CI"):
            pytest.fail("Node.js is required in CI")
        pytest.skip("Node.js is not installed")
    snippet = re.search(r"```js\n(.*?)```", SKILL_MD, re.S).group(1)
    driver = """
const vm = require("vm"), fs = require("fs");
const [bundle, png] = process.argv.slice(1);
const sandbox = vm.createContext({ TextEncoder, TextDecoder });
vm.runInContext(fs.readFileSync(bundle, "utf8").replace(/^#!.*\\n/, ""), sandbox);
sandbox.markdown = "# รายงาน\\n\\nข้อความ**ตัวหนา**ภาษาไทย\\n\\n![แผนภูมิ](chart.png)\\n";
sandbox.pngBytes = new Uint8Array(fs.readFileSync(png));
vm.runInContext("var docxBytes; " + SNIPPET.replace("const report", "docxBytes = bytes; const report") + "; this.out = { result, n: bytes && bytes.length, report };", sandbox);
process.stdout.write(JSON.stringify(sandbox.out));
""".replace("SNIPPET", json.dumps(snippet))
    done = subprocess.run(
        ["node", "-e", driver, str(unpacked / "scripts" / "thai_docx.js"), str(FIXTURES / "pixel.png")],
        capture_output=True, text=True, timeout=60,
    )
    out = json.loads(done.stdout or "{}")
    assert done.returncode == 0 and out.get("result", {}).get("ok") and out["n"] > 0, done.stdout + done.stderr
    assert out["report"]["ok"] and out["report"]["findings"] == []
