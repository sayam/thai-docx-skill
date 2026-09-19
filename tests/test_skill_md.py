# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
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
import textwrap
import unicodedata
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
SETTINGS = (SKILL / "references" / "settings.md").read_text(encoding="utf-8")
MARKDOWN = (SKILL / "references" / "markdown.md").read_text(encoding="utf-8")
CHECK = (SKILL / "references" / "check.md").read_text(encoding="utf-8")
SANDBOX = (SKILL / "references" / "sandbox.md").read_text(encoding="utf-8")
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


def test_description_fits_the_claude_apps_upload():
    """The specification allows 1024 characters; the Claude apps' upload allows 200. The
    grill sentence stays whole: without "use this skill" Haiku asked questions of its own,
    or cut the phrase off the message it passed to the script
    (docs/evidence/2026-09-17-a-description-of-200-characters.md). So does the way back
    to the repository."""
    description = re.search(r"^description: (.+)$", SKILL_MD.split("---", 2)[1], re.M).group(1)
    assert len(description) <= 200, len(description)
    assert 'the user\'s message says "thai-docx grill", use this skill to ask its fixed questions' in description
    assert description.endswith(" https://github.com/sayam/thai-docx-skill")


def test_skill_md_stays_within_its_ceiling():
    """Every client loads the whole body when the skill activates, on every model (ADR
    0007): under the specification's 500 lines, and a byte ceiling that makes growth a
    decision rather than a drift."""
    body = SKILL_MD.split("---", 2)[2]
    assert len(body.splitlines()) < 500
    assert len(SKILL_MD.encode("utf-8")) <= 12_000, len(SKILL_MD.encode("utf-8"))
    links = re.findall(r"\]\(((?:references|scripts|assets)/[^)#]+)\)", SKILL_MD)
    for link in links:
        assert (SKILL / link).is_file(), link
    # a reference nothing links to is a file no agent opens
    assert sorted("references/" + p.name for p in (SKILL / "references").iterdir()) == sorted(set(links))


# --- what it says the build does ----------------------------------------------------------


def test_the_defaults_skill_md_names_are_the_build_s():
    """The one line of defaults SKILL.md keeps; every other setting is in the generated
    references/settings.md, held by tests/test_settings.py (ADR 0028)."""
    d = b.DEFAULTS
    top, right, bottom, left = d["margins"]
    assert top == right == bottom != left
    line = (f"Defaults: {d['font']} {d['size']} pt, {d['paper'].upper()} {'landscape' if d['landscape'] else 'portrait'},"
            f" margins {top:g} in (left {left:g} in), {'single' if d['line_spacing'] == 1 else str(d['line_spacing']) + '×'} spacing,"
            f" {d['align']}-aligned, no table of contents or page numbers.")
    assert not d["toc"] and not d["page_numbers"]
    assert line in " ".join(SKILL_MD.split())


def test_every_flag_named_is_a_flag_the_build_takes_and_every_flag_is_named():
    """Every flag is named where the agent reads it — SKILL.md or a file it sends them to —
    and nothing names a flag the commands do not have."""
    usage = _flags(b.USAGE) | _flags(pf.USAGE) | _flags(gr.USAGE)  # build, profile, grill
    read_by_the_agent = (SKILL_MD, INTERVIEW, CHAPTERS, PROFILES, HEADING_STYLES, SETTINGS, MARKDOWN, CHECK, SANDBOX)
    assert set().union(*(_flags(t) for t in read_by_the_agent)) == usage
    for text in read_by_the_agent:
        assert _flags(text) <= usage


def test_the_interview_holds_no_question_the_command_did_not_give():
    """ADR 0029: the questions reach the agent only in the grill command's JSON. On
    2026-09-16 Haiku asked the questions straight from this file without running the
    command; a file with no question in it leaves nothing to ask that way."""
    from thai_docx import settings as st
    for q in st.QUESTIONS:
        for text in q["text"]:
            assert text not in INTERVIEW, text
        for c in q["choices"]:
            for label in c["label"]:
                if len(label) > 3 and label not in ("No", "Yes", "Left", "None", "Show"):
                    assert label not in INTERVIEW, label
    keys = re.search(r"keys, for when the user names only some of them: (.*)\.", " ".join(INTERVIEW.split())).group(1)
    assert re.findall(r"`([a-z-]+)`", keys) == [q["key"] for q in st.QUESTIONS]
    assert "grill --said" in INTERVIEW and '"questions"' in INTERVIEW and '"next"' in INTERVIEW


def test_heading_styles_section_names_every_property_and_its_example_builds():
    """ADR 0020: the table is the parser's list, and the example is one the build takes."""
    documented = [p for row in _table(HEADING_STYLES, "Properties") for p in re.findall(r"`([a-z-]+)`", row[0])]
    assert sorted(documented) == sorted(lo.HEADING_PROPERTIES)
    example = re.search(r"```markdown\n(.*?)```", HEADING_STYLES, re.S).group(1)
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
    # the list of tables holds them, with the tab before each page number (ADR 0035)
    assert captions == ["ตารางที่ 1-1 ผลการสำรวจ\t", "ตารางที่ ก-1 ผู้ตอบแบบสอบถาม\t",
                        "ตารางที่ 1-1 ผลการสำรวจ", "รูปที่ 1-1 ขั้นตอนการทำงาน", "ตารางที่ ก-1 ผู้ตอบแบบสอบถาม"]
    assert text[1:8] == ["สารบัญ", "สารบัญ\t", "สารบัญตาราง\t", "บทที่ 1 บทนำ\t", "บรรณานุกรม\t", "ภาคผนวก ก แบบสอบถาม\t", "ประวัติผู้เขียน\t"]
    assert "ตารางที่ 1-1" in section and "รูปที่ 1-1" in section and "ตารางที่ ก-1" in section and "ก ข ค" in section
    assert _flags(CHAPTERS) <= _flags(b.USAGE)


def test_finding_codes_table_names_every_code_the_checker_reports():
    source = (SKILL / "scripts" / "thai_docx" / "check.py").read_text(encoding="utf-8")
    emitted = set(re.findall(r'\.find\(\s*"([^"]+)"', source))
    documented = {code for row in _table(CHECK, "Codes") for code in re.findall(r"`([^`]+)`", row[0])}
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
    snippet = re.search(r"```js\n(.*?)```", SANDBOX, re.S).group(1)
    driver = """
const vm = require("vm"), fs = require("fs");
const [bundle, png] = process.argv.slice(1);
const sandbox = vm.createContext({ TextEncoder, TextDecoder });
vm.runInContext(fs.readFileSync(bundle, "utf8").replace(/^#!.*\\n/, ""), sandbox);
sandbox.markdown = "# รายงาน\\n\\nข้อความ**ตัวหนา**ภาษาไทย\\n\\n![แผนภูมิ](chart.png)\\n";
sandbox.pngBytes = new Uint8Array(fs.readFileSync(png));
vm.runInContext("var docxBytes; " + SNIPPET.replace("const report", "docxBytes = bytes; const report")
  + "; this.out = { result, n: bytes && bytes.length, report };", sandbox);
process.stdout.write(JSON.stringify(sandbox.out));
""".replace("SNIPPET", json.dumps(snippet))
    done = subprocess.run(
        ["node", "-e", driver, str(unpacked / "scripts" / "thai_docx.js"), str(FIXTURES / "pixel.png")],
        capture_output=True, text=True, timeout=60,
    )
    out = json.loads(done.stdout or "{}")
    assert done.returncode == 0 and out.get("result", {}).get("ok") and out["n"] > 0, done.stdout + done.stderr
    assert out["report"]["ok"] and out["report"]["findings"] == []


# --- the user guides ---------------------------------------------------------------------

GUIDE = ROOT / "docs" / "guide"
PAGES = ("install", "scenarios", "command-line", "troubleshooting")
GUIDES = {
    lang: {"home": (GUIDE / (lang + ".md")).read_text(encoding="utf-8"),
           **{page: (GUIDE / lang / (page + ".md")).read_text(encoding="utf-8") for page in PAGES}}
    for lang in ("th", "en")
}
README = (ROOT / "README.md").read_text(encoding="utf-8")
PROMPTS = {lang: (ROOT / name).read_text(encoding="utf-8") for lang, name in (("en", "PROMPT.md"), ("th", "PROMPT.th.md"))}
# lines that run another program — an installer, a version check — whose flags are not ours
OTHER_PROGRAMS = re.compile(r"^.*(?:\bnpx skills|\bgh skill|\bgh attestation|\bgemini skills|--version).*$", re.M)


def _slug(heading: str) -> str:
    """The anchor GitHub gives a heading: lower case, letters, marks, digits, `-` and `_`
    kept, spaces to `-` (github-slugger)."""
    kept = "".join(c for c in heading.strip().lower()
                   if c in " -_" or unicodedata.category(c)[0] in "LMN")
    return kept.replace(" ", "-")


def test_the_user_guides_say_what_the_skill_does():
    """docs/guide/th.md and en.md and their pages, linked from the README: every example the
    reader types is read by the grill command as the guide says — grill only with the phrase,
    the words after it as written — every flag they name is a flag, and both cover the same
    thirteen scenarios."""
    for lang in GUIDES:
        assert f"https://github.com/sayam/thai-docx-skill/blob/main/docs/guide/{lang}.md" in README
    shapes = []
    for lang, pages in GUIDES.items():
        text = "\n".join(pages.values())
        assert _flags(OTHER_PROGRAMS.sub("", text)) <= _flags(b.USAGE) | _flags(pf.USAGE) | _flags(gr.USAGE), lang
        scenarios = re.findall(r"^## (?:Scenario|สถานการณ์ที่) (\d+)", pages["scenarios"], re.M)
        assert scenarios == [str(n) for n in range(1, 14)], lang
        prompts = [" ".join(block.split()) for block in re.findall(r"```text\n(.*?)```", text, re.S)]
        grilled = []
        for prompt in prompts:
            if gr.mode(prompt) != "grill":
                assert "thai-docx grill" not in prompt.lower(), prompt
                continue
            parts = gr.parts(prompt)
            said = gr.plain(prompt)
            assert ("from" in parts) is (" from " in said or " จาก " in said), prompt
            assert ("save_to" in parts) is (" save to " in said or "บันทึกเป็น" in said), prompt
            assert ("only" in parts) is (" only " in said or "เฉพาะ" in said), prompt
            if "only" in parts:
                keys = [q["key"] for q in __import__("thai_docx.settings", fromlist=["QUESTIONS"]).QUESTIONS]
                assert all(k in keys for k in parts["only"].split(",")), prompt
            grilled.append(sorted(parts))
        shapes.append(sorted(grilled))
    assert shapes[0] == shapes[1], "the same grill examples in both languages"
    assert shapes[0] == sorted([[], ["from", "save_to"], ["from", "save_to"], ["from", "only", "save_to"]])


def test_the_user_guides_link_to_what_is_there_in_both_languages():
    """A link between guide pages reaches a page and a heading that exist, and the Thai and
    English guides have the same pages with the same sections, so neither falls behind."""
    for lang, pages in GUIDES.items():
        for page, text in pages.items():
            here = GUIDE / (lang + ".md") if page == "home" else GUIDE / lang / (page + ".md")
            prose = re.sub(r"^( *)```.*?^\1```", "", text, flags=re.S | re.M)
            for target, anchor in re.findall(r"\]\((?!https?://)([^)#\s]*)(?:#([^)\s]+))?\)", prose):
                path = (here.parent / target).resolve() if target else here
                assert path.is_file(), (here.name, target)
                if anchor:
                    headings = re.findall(r"^#{1,6} (.+)$", path.read_text(encoding="utf-8"), re.M)
                    assert anchor in {_slug(h) for h in headings}, (lang, page, target, anchor)
    for page in GUIDES["th"]:
        th, en = (re.findall(r"^(#{2,3}) ", GUIDES[lang][page], re.M) for lang in ("th", "en"))
        assert th == en, page


def test_the_command_line_guide_runs_as_written_from_the_download(unpacked, tmp_path):
    """Every command the README and the command-line pages give runs from the release
    archive, unpacked as the guide says, and succeeds; the Node.js line gives the same file."""
    shutil.copytree(unpacked, tmp_path / "thai-docx")
    home = tmp_path / "home"
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home)}
    for text in (README, GUIDES["en"]["command-line"], GUIDES["th"]["command-line"]):
        markdown = re.search(r"```markdown\n(.*?)```", GUIDES["th"]["command-line"], re.S).group(1)
        (tmp_path / "report.md").write_text(textwrap.dedent(markdown), encoding="utf-8")
        blocks = re.findall(r"^( *)```sh\n(.*?)^\1```", text, re.S | re.M)
        commands = [shlex.split(line, comments=True) for _, block in blocks for line in block.splitlines()]
        commands = [c for c in commands if c and c[0] in ("python3", "node") and len(c) > 2 and "thai_docx" in c[1]]
        assert commands, "the page gives commands"
        python_build = None
        for argv in commands:
            runtime = argv[0]
            if runtime == "node" and not shutil.which("node"):
                continue
            argv[0] = sys.executable if runtime == "python3" else runtime
            done = subprocess.run(argv, cwd=tmp_path, capture_output=True, text=True, timeout=60, env=env)
            assert done.returncode == 0 and json.loads(done.stdout)["ok"] and done.stderr == "", (argv[1:], done.stdout)
            if argv[2] != "build":
                continue
            this = (argv[3:], (tmp_path / argv[4]).read_bytes())
            if runtime == "python3":
                python_build = this
            else:  # a Node.js line says it gives the file of the Python line before it
                assert this == python_build, "both runtimes give the same file"
        shutil.rmtree(home, ignore_errors=True)


def test_the_markdown_the_guides_show_builds(unpacked, tmp_path):
    """Every Markdown example in the scenarios, in both languages, builds with no error and no
    warning: what the guide says Markdown can hold, it can."""
    shutil.copy(FIXTURES / "pixel.png", tmp_path / "chart.png")
    examples = [block for pages in GUIDES.values() for block in
                re.findall(r"^( *)```markdown\n(.*?)^\1```", pages["scenarios"], re.S | re.M)]
    assert len(examples) == 4
    for n, (indent, block) in enumerate(examples):
        (tmp_path / f"{n}.md").write_text("\n".join(line[len(indent):] for line in block.splitlines()) + "\n", encoding="utf-8")
        done = _run([sys.executable, str(unpacked / "scripts" / "thai_docx"), "build", f"{n}.md", f"{n}.docx"], tmp_path)
        result = json.loads(done.stdout)
        assert done.returncode == 0 and result["ok"] and result["warnings"] == [], (n, done.stdout)


def test_the_archive_the_readme_and_guides_name_is_this_version():
    """The README and the install pages name the release archive by its version; a release
    that bumps SKILL.md without them sends readers to a file that is not the latest."""
    version = re.search(r'^\s*version: "([^"]+)"', SKILL_MD, re.M).group(1)
    texts = [README, *PROMPTS.values()] + [text for pages in GUIDES.values() for text in pages.values()]
    named = {v for text in texts for v in re.findall(r"thai-docx-(\d+\.\d+\.\d+)\.zip", text)}
    assert named == {version}, named


def test_the_prompts_for_chat_apps_give_the_same_rules():
    """PROMPT.md and its step-by-step Thai page PROMPT.th.md hand a chat app the same five rules:
    read SKILL.md, build with the bundled command and no document library, keep the Thai text as
    written, give the file, ask only on thai-docx grill. Each links the other."""
    en = PROMPTS["en"].split("\n---\n", 1)[1]
    th = re.search(r"```text\n(.*?)```", PROMPTS["th"], re.S).group(1)
    for said in (en, th):
        assert "thai-docx/SKILL.md" in said and "python-docx" in said and "thai-docx grill" in said
        assert "python3 <skill>/scripts/thai_docx build doc.md doc.docx" in said
        assert re.findall(r"^[1-5]\. ", said, re.M) == ["1. ", "2. ", "3. ", "4. ", "5. "]
        assert _flags(said) <= _flags(b.USAGE)
    assert "(PROMPT.th.md)" in PROMPTS["en"] and "(PROMPT.md)" in PROMPTS["th"]
