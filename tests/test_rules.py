# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""The rules are one text, and the project's live pages cite records that still stand.

`docs/rules.md` holds the rules a change is decided by: the Thai is the rule, in the
maintainer's words, and the English below it is a translation marked as such. Its last
table is the trace — which decision record applied each rule, and what was seen — so every
link on the page must reach a file, and the pages that decide (GOVERNANCE.md,
`.github/CONTRIBUTING.md`, `docs/architecture.md`) must send a reader there.

A record is a trace of a rule in use, never a rule of its own, so a page that states a rule
**now** cites the record in force. Citing a record the index marks superseded sends the
reader to a rule that no longer holds — the drift of 2026-09-18, found by a reviewer and
written down in `docs/evidence/2026-09-18-records-point-at-the-record-in-force.md` and in
ROADMAP.md as a check worth having. A line may name a superseded record when it names its
successor too ("ADR 0029, restating 0026"): that is history, stated as history.

What is not read: `docs/adr/` (a record cites what was in force when it was written),
`docs/evidence/` and `docs/handoff/` (what was seen on a day), CHANGELOG.md (what a release
carried), and `tools/` (verifiable-gates, installed, with a numbering of its own).
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
RULES = ROOT / "docs" / "rules.md"
INDEX = ROOT / "docs" / "adr" / "README.md"

# | 0023 | [title](0023-….md) | 2026-09-16 | accepted |
ROW = re.compile(r"^\|\s*(\d{4})\s*\|\s*\[[^\]]+\]\(([^)]+)\)\s*\|\s*[\d-]+\s*\|\s*([^|]+?)\s*\|$", re.M)
# "ADR 0023", "ADRs 0012, 0018", "ADR-0004", "adr/0040-…md", "docs/adr/0040"
CITED = re.compile(r"\bADRs?[\s-]+(\d{4}(?:\s*,\s*\d{4})*)|adr/(\d{4})")
SUPERSEDED_BY = re.compile(r"superseded by (\d{4})")
# every rule of docs/rules.md, as its trace table names it
RULES_IN_ORDER = ["0", "1", "2.1", "2.2", "2.3", "3", "4", "5", "6"]


def records() -> dict[str, str]:
    """Each record's number and the status the index gives it."""
    found = {m.group(1): m.group(3) for m in ROW.finditer(INDEX.read_text(encoding="utf-8"))}
    assert len(found) > 30, "the ADR index parsed to almost nothing; the row pattern no longer matches"
    return found


def live_pages() -> list[pathlib.Path]:
    """The pages and sources that state a rule now — what a reader is sent to today."""
    skill = ROOT / "skills" / "thai-docx"
    groups = [
        sorted(p for p in ROOT.glob("*.md") if p.name != "CHANGELOG.md"),
        sorted((ROOT / ".github").glob("*.md")),
        sorted((ROOT / ".github" / "workflows").glob("*.yml")),
        sorted(ROOT.glob("docs/*.md")),
        sorted((ROOT / "docs" / "guide").rglob("*.md")),
        sorted((ROOT / "docs" / "templates").glob("*.md")),
        sorted(skill.rglob("*.md")),
        sorted((skill / "scripts" / "thai_docx").glob("*.py")),
        [skill / "scripts" / "thai_docx.js"],
        sorted(ROOT.glob("js/*.js")),
        sorted((ROOT / "tests").glob("*.py")),
        sorted((ROOT / "tests" / "js").glob("*.cjs")),
        [ROOT / "gates.yaml"],
    ]
    assert all(groups), "a group of live pages came back empty; the globs no longer match the tree"
    return [p for group in groups for p in group]


def citations(line: str) -> set[str]:
    """The record numbers a line cites, in any of the ways this project writes them.

    Once a line says ADR at all, every number shaped like a record on it is a citation:
    "ADR 0037, 0023, 0008", "ADR 0029, restating 0026", "superseded by 0040". Record numbers
    open with a zero, so a year or a version is not mistaken for one.
    """
    found: set[str] = set()
    for m in CITED.finditer(line):
        found |= set(re.findall(r"\d{4}", m.group(1))) if m.group(1) else {m.group(2)}
    if found:
        found |= set(re.findall(r"\b0\d{3}\b", line))
    return found


def drift() -> list[str]:
    """Every live citation of a record the index does not mark accepted, as page:line."""
    index, out = records(), []
    for page in live_pages():
        for no, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            for cited in sorted(citations(line)):
                status = index.get(cited, "is in no row of the index")
                if status.startswith("accepted"):
                    continue
                in_force = SUPERSEDED_BY.search(status)
                if in_force and in_force.group(1) in citations(line):
                    continue  # names the record in force on the same line: history, said as history
                out.append(f"{page.relative_to(ROOT).as_posix()}:{no}: ADR {cited} {status}")
    return out


def test_no_live_page_cites_a_record_that_no_longer_holds():
    """A page stating a rule now points at the record in force (evidence 2026-09-18)."""
    assert drift() == []


def test_a_superseded_record_may_be_named_beside_the_one_that_replaced_it():
    """History said as history passes: the successor is on the line."""
    assert citations("(ADR 0029, restating 0026)") == {"0029", "0026"}
    index = records()
    assert index["0026"].startswith("superseded by 0029") and index["0029"].startswith("accepted")


def test_every_link_on_the_rules_page_reaches_a_file():
    """The trace is evidence only if a reader can follow it."""
    links = re.findall(r"\]\((?!http)([^)#]+)", RULES.read_text(encoding="utf-8"))
    assert links, "the rules page has no links; the trace table is gone"
    assert [link for link in links if not (RULES.parent / link).exists()] == []


def test_the_rules_page_is_thai_first_and_says_the_translation_is_a_translation():
    text = RULES.read_text(encoding="utf-8")
    assert "ฉบับภาษาไทยข้างล่างนี้คือฉบับจริง" in text
    assert "เมื่อสองฉบับต่างกัน ให้ถือตามภาษาไทย" in text
    assert "# Reference translation" in text
    assert "**The Thai above governs.**" in text
    assert text.index("# กฎเหล็ก") < text.index("# Reference translation")


def test_every_rule_has_a_trace_to_a_record_that_stands():
    """Each rule names at least one record, and only records the index marks accepted."""
    text = RULES.read_text(encoding="utf-8")
    table = text[text.index("# ร่องรอย"):text.index("# Reference translation")]
    index = records()
    for rule in RULES_IN_ORDER:
        rows = [row for row in table.splitlines() if row.startswith(f"| {rule} ")]
        assert len(rows) == 1, f"rule {rule} has {len(rows)} rows in the trace table"
        cited = citations(rows[0])
        assert cited, f"rule {rule} names no record"
        assert all(index.get(one, "").startswith("accepted") for one in cited), f"rule {rule} cites a record that does not stand"


def test_the_pages_that_decide_send_the_reader_to_the_rules():
    for page in ("GOVERNANCE.md", ".github/CONTRIBUTING.md", "docs/architecture.md"):
        assert "rules.md" in (ROOT / page).read_text(encoding="utf-8"), f"{page} does not link the rules"


def test_a_dated_measurement_in_the_references_has_a_record_of_that_day():
    """`limits.md` says every line is measured or refused; a measurement is a record, not a word.
    Three steps on editing in Word were written "measured" with no record of them (the review of
    0.2.0, A-02). Every date a reference gives a measurement is the date of a record in
    docs/evidence/, by its name: a date that only appears inside some other record's text is a
    record of something else."""
    days = {p.name[:10] for p in (ROOT / "docs" / "evidence").glob("*.md")}
    for page in sorted((ROOT / "skills" / "thai-docx" / "references").glob("*.md")):
        text = " ".join(page.read_text(encoding="utf-8").split())
        for day in re.findall(r"[Mm]easured[^.]{0,80}?(\d{4}-\d{2}-\d{2})", text):
            assert day in days, (page.name, day)


def test_the_newest_release_record_names_the_bytes_it_read():
    """A record of a release reading named a commit, not the bytes: the goldens' hashes appeared in
    no record (A-02's sibling, F-13). The newest `what-vX.Y.Z-was-read-in` record names every
    golden's sha256, so a golden that moves needs a record of what was read on it."""
    import hashlib
    newest = sorted((ROOT / "docs" / "evidence").glob("*-what-v*-was-read-in.md"))[-1].read_text(encoding="utf-8")
    for golden in sorted((ROOT / "tests" / "golden").glob("*.docx")):
        assert hashlib.sha256(golden.read_bytes()).hexdigest() in newest, golden.name


def test_the_records_found_stale_in_0_2_0_say_what_holds_now():
    """Sentences of accepted records no longer true of the code (F-04, F-06, F-12) each carry a
    Later line saying what holds."""
    adr = {p.name[:4]: " ".join(p.read_text(encoding="utf-8").split()) for p in (ROOT / "docs" / "adr").glob("0*.md")}
    for number, later in (("0039", "−4.1%"), ("0039", "the two records meant different things"), ("0012", "since ADR 0033"),
                          ("0017", "the 100-deep cap is what keeps it within the stack"), ("0018", "`PROMPT.th.md`"),
                          ("0031", "`license: MIT (LICENSE.txt)`"), ("0036", "`tools/oracle_set.py` holds the list")):
        assert later in adr[number], (number, later)


def test_every_picture_the_fixtures_carry_says_where_it_came_from():
    """ADR 0040 §10 asks for synthetic content only, which a reader can check only if the
    picture's origin, or what it holds, is written down somewhere. Two thesis pictures had
    neither (F-14)."""
    records = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "docs" / "evidence").glob("*.md"))
    records += (ROOT / "skills" / "thai-docx" / "examples" / "README.md").read_text(encoding="utf-8")
    pictures = [*(ROOT / "tests" / "fixtures").rglob("*.png"), *(ROOT / "tests" / "fixtures").rglob("*.jpg"),
                *(ROOT / "skills" / "thai-docx" / "examples").glob("*.png")]
    assert len(pictures) >= 4
    for picture in pictures:
        assert picture.name in records, picture.relative_to(ROOT)


def test_every_page_that_says_what_a_merge_needs_names_the_checks_it_needs():
    """F-07: the pages said five checks, or three, where the ruleset on `main` requires six and
    CodeQL's results. Each page that says what a merge needs names the same six."""
    required = ("scans", "commits", "tests", "lint", "deps", "pr-description")
    workflows = "".join(p.read_text(encoding="utf-8") for p in (ROOT / ".github" / "workflows").glob("*.yml"))
    for check in required:
        assert re.search(r"^  " + re.escape(check) + r":$", workflows, re.M), check  # a job of that name exists
    for page in (".github/CONTRIBUTING.md", "GOVERNANCE.md", "docs/architecture.md", ".github/CODEOWNERS"):
        text = (ROOT / page).read_text(encoding="utf-8")
        assert all("`" + check + "`" in text for check in required), page
        assert "CodeQL" in text, page
