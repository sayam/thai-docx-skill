# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""The settings registry (ADR 0028): one entry per setting, the same entries in both
implementations, and everything that describes a setting derived from them — the parser,
the defaults, the report, the flags a profile holds, and the reference the agent reads."""

from __future__ import annotations

import json
import pathlib
import re
import shlex
import subprocess
import sys

from thai_docx import build as b
from thai_docx import grill as g
from thai_docx import profiles as pf
from thai_docx import settings as st

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "skills" / "thai-docx" / "scripts" / "thai_docx.js"
sys.path.insert(0, str(ROOT / "tools"))
import gen_settings_docs  # noqa: E402


def _js_settings() -> list:
    done = subprocess.run(["node", "-e", "process.stdout.write(JSON.stringify(require(process.argv[1]).SETTINGS))", str(BUNDLE)],
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0 and done.stderr == "", done.stderr
    return json.loads(done.stdout)


def test_both_implementations_hold_the_same_entries():
    """Data, not behaviour — the parity suite proves the behaviour. `doc` is the reference's
    wording, which only the Python generator reads."""
    python = json.loads(json.dumps([{k: v for k, v in s.items() if k != "doc"} for s in st.SETTINGS]))
    js = _js_settings()
    assert [s["key"] for s in js] == [s["key"] for s in python]
    for mine, theirs in zip(python, js, strict=True):
        assert mine == theirs, mine["key"]


def test_both_implementations_ask_the_same_questions():
    """The interview is data in both (ADR 0029): the same questions, choices and labels."""
    done = subprocess.run(["node", "-e", "process.stdout.write(JSON.stringify(require(process.argv[1]).QUESTIONS))", str(BUNDLE)],
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout) == json.loads(json.dumps(st.QUESTIONS))
    for q in st.QUESTIONS:
        assert 2 <= len(q["choices"]) <= 4 and all(len(c["label"]) == 2 and all(c["label"]) for c in q["choices"]), q["key"]
        for c in q["choices"]:
            if "set" in c:
                opts, _, _ = st.parse_args(pf.as_flags(c["set"]) + ["in.md", "out.docx"])
                assert all(g._same(opts[k], v) for k, v in c["set"].items()), (q["key"], c)
        assert ("set" in q["choices"][0]) is (q["key"] != "save")
        if q["key"] != "save":
            assert all(g._same(st.DEFAULTS[k], v) for k, v in q["choices"][0]["set"].items()), "choice a is the default"


def test_every_entry_is_whole_and_every_flag_once():
    kinds = {"value", "option", "list", "switch", "off"}
    reads = {"text", "points", "number", "numbers", "choice", "position"}
    flags = [s["flag"] for s in st.SETTINGS]
    assert len(set(flags)) == len(flags) and len({s["key"] for s in st.SETTINGS}) == len(flags)
    for s in st.SETTINGS:
        assert s["kind"] in kinds and s["layer"] in st.LAYERS, s["key"]
        assert ("read" in s) is (s["kind"] not in ("switch", "off")), s["key"]
        if "read" in s:
            assert s["read"][0] in reads and s["takes"], s["key"]
        assert s.get("needs") in (None, *st.DEFAULTS, *st.STRUCTURES), s["key"]
        assert s.get("clashes") in (None, *st.CLASHES), s["key"]
        assert s["flag"].startswith("--") and len(s["doc"]) == 3, s["key"]
    assert st.USAGE == b.USAGE and set(re.findall(r"--[a-z-]+", st.USAGE)) == set(flags) | {"--profile", "--default", "--allow-dir"}


def test_the_parser_the_report_and_the_profile_come_from_the_registry():
    assert b.DEFAULTS is st.DEFAULTS and b.parse_args is st.parse_args
    assert list(pf.FLAGS) == [s["key"] for s in st.SETTINGS]
    assert list(st.settings_json(st.DEFAULTS)) == [s["report"][0] for s in st.SETTINGS]
    for s in st.SETTINGS:
        assert pf.FLAGS[s["key"]] == (s["kind"], s["flag"])


def test_each_refusal_is_the_registry_s_words():
    for s in st.SETTINGS:
        if "read" not in s or s["read"][0] == "position":
            continue
        try:
            st.parse_args([s["flag"], "\x01", "in.md", "out.docx"])
        except st.BuildError as exc:
            assert exc.what == s["flag"] + " takes " + s["takes"]
        else:
            raise AssertionError(s["flag"] + " took a control character")


def test_the_reference_is_generated_and_every_example_changes_its_own_setting():
    assert gen_settings_docs.main(["--check"]) == 0, "run python3 tools/gen_settings_docs.py"
    for s in st.SETTINGS:
        example = shlex.split(re.search(r"`([^`]+)`", s["doc"][2]).group(1))
        needed = [st.BY_KEY[s["needs"]]["flag"]] if s.get("needs") in st.DEFAULTS else []
        opts, _, _ = st.parse_args(needed + example + ["in.md", "out.docx"])
        changed = {k for k in opts if opts[k] != st.DEFAULTS[k]}
        assert changed == {s["key"], *([s["needs"]] if needed else [])}, s["key"]


def test_the_reference_states_each_default():
    d = st.DEFAULTS
    margins = ", ".join(f"{m:g}" for m in d["margins"])
    shows = {
        "font": d["font"], "size": f"{d['size']} pt", "paper": d["paper"].upper(),
        "landscape": "landscape" if d["landscape"] else "portrait",
        "margins": f"{margins} (top, right, bottom, left)", "indent": "none" if not d["indent"] else f"{d['indent']:g}",
        "line_spacing": f"{d['line_spacing']:g}", "align": d["align"],
        "hide_spelling_errors": "hidden" if d["hide_spelling_errors"] else "shown",
        "toc": "yes" if d["toc"] else "none", "heading_numbers": "yes" if d["heading_numbers"] else "none",
        "page_numbers": "yes" if d["page_numbers"] else "none", "page_number_on_first": "shown" if d["page_number_on_first"] else "none",
        "header": d["header"] or "none", "footer": d["footer"] or "none",
        "thai_digits": "๑ ๒ ๓" if d["thai_digits"] else "1 2 3",
        "auto_numbering": "counted by the application" if d["auto_numbering"] else "written by the build, the same in every application",
        "repeat_table_header": "repeats on every page" if d["repeat_table_header"] else "first page only",
        "table_widths": d["table_widths"], "table_size": "as the body" if d["table_size"] is None else f"{d['table_size']} pt",
        "chapter_label": d["chapter_label"], "table_label": d["table_label"], "figure_label": d["figure_label"],
        "caption_hanging_indent": "start at the margin, like the first" if not d["caption_hanging_indent"] else f"{d['caption_hanging_indent']:g}",
        "center_images": "centred" if d["center_images"] else "starts at the left margin",
        "caption_matches_object": "as wide as the picture" if d["caption_matches_object"] else "the width of the text",
        "front_page_numbers": {"thai-letters": "ก ข ค"}[d["front_page_numbers"]],
        "appendix_label": d["appendix_label"], "appendix_numbers": {"thai-letters": "ก ข ค"}[d["appendix_numbers"]],
        "chapter_title_on_new_line": "beside its number" if not d["chapter_title_on_new_line"] else "under its number",
    }
    assert {s["key"]: s["doc"][1] for s in st.SETTINGS} == shows


# what the document holds, from nothing to all of it; the edges are a region comment with no
# heading under it, a table inside a quote, and a front comment with nothing after it
DOCUMENTS = {
    "plain": "ข้อความ\n",
    "headings": "# หัวข้อ\n\n## ย่อย\n\nข้อความ\n",
    "quoted table": "> | ก | ข |\n> |---|---|\n> | 1 | 22 |\n",
    "table caption": "Table: ผล\n\n| ก | ข |\n|---|---|\n| 1 | 22 |\n",
    "figure caption": "![x](p.png)\n\nFigure: ภาพ\n",
    "chapters, no heading": "<!-- chapters -->\n\nข้อความ\n",
    "chapters": "<!-- chapters -->\n\n# บทนำ\n\nข้อความ\n",
    "appendices": "<!-- appendices -->\n\n# แบบสอบถาม\n\nข้อความ\n",
    "front at the end": "ปก\n\n<!-- front -->\n",
    "front": "ปก\n\n<!-- front -->\n\n# บทคัดย่อ\n\nข้อความ\n\n<!-- chapters -->\n\n# บทนำ\n",
    "toc comment": "# หัว\n\n<!-- toc -->\n",
}
PNG = (ROOT / "tests" / "fixtures" / "pixel.png").read_bytes()


def _built(text: str, argv: list[str]) -> dict:
    opts, _, _ = st.parse_args(argv + ["in.md", "out.docx"])
    result, _ = b.build_text(text, opts, lambda src: (src, PNG))
    assert result.get("findings") == [], result
    return result


def test_a_flag_is_said_to_have_changed_nothing_exactly_when_it_changed_no_byte():
    """The structure a setting needs is data (ADR 0028). For every such setting and every
    document: without the structure, the file is the same with the flag as without it, and
    the build says so; with it, nothing is said."""
    branches: dict[str, set[bool]] = {}
    for name, text in DOCUMENTS.items():
        plain = _built(text, [])
        assert [w for w in plain["warnings"] if w["code"] == "settings"] == [], name
        for s in st.SETTINGS:
            if s.get("needs") not in st.STRUCTURES:
                continue
            example = shlex.split(re.search(r"`([^`]+)`", s["doc"][2]).group(1))
            given = _built(text, example)
            said = [w["message"] for w in given["warnings"] if w["code"] == "settings"]
            branches.setdefault(s["key"], set()).add(given["sha256"] == plain["sha256"])
            if given["sha256"] == plain["sha256"]:
                assert said == [s["flag"] + " changed nothing: " + st.STRUCTURES[s["needs"]][1]], (name, s["flag"])
            else:
                assert said == [], (name, s["flag"], said)
    assert all(seen == {True, False} for seen in branches.values()), "every setting both warned about and not"


def test_flags_that_need_the_same_structure_share_one_warning_and_a_duplicate_is_named():
    all_of_them = ["--chapter-label", "บท", "--appendix-label", "Appendix", "--appendix-numbers", "decimal", "--no-repeat-table-header"]
    said = [w["message"] for w in _built(DOCUMENTS["plain"], all_of_them)["warnings"]]
    assert said == [
        "--no-repeat-table-header changed nothing: the document has no table",
        "--chapter-label changed nothing: no heading carries a chapter number; a # heading under <!-- chapters --> does",
        "--appendix-label and --appendix-numbers changed nothing: no heading carries an appendix letter;"
        " a # heading under <!-- appendices --> does",
    ]
    twice = _built(DOCUMENTS["toc comment"], ["--toc"])
    assert [w["message"] for w in twice["warnings"]] == [
        "--toc: the document places a table of contents with <!-- toc --> as well, so it now has two"]
    assert _built(DOCUMENTS["headings"], ["--toc"])["warnings"] == []
