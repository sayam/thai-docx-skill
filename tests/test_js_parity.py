# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""The JavaScript implementation matches the Python one (ADR 0008): the same
reading of Markdown, the same .docx bytes, the same checker report on sound and
damaged packages (ADR 0017), and the same command line — output, exit code and
file. The committed bundle is the one the sources build.
"""

from __future__ import annotations

import base64
import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

import parity
from thai_docx import markdown as md

ROOT = parity.ROOT
sys.path.insert(0, str(ROOT / "tools"))
import oracle_set  # noqa: E402
PY_CLI = [sys.executable, str(ROOT / "skills" / "thai-docx" / "scripts" / "thai_docx")]
BUNDLE = ROOT / "skills" / "thai-docx" / "scripts" / "thai_docx.js"
JS_CLI = ["node", str(BUNDLE)]


@pytest.fixture(autouse=True)
def _node():
    if shutil.which("node"):
        return
    if os.environ.get("CI"):
        pytest.fail("Node.js is required in CI: the JavaScript implementation is a gate, not an option")
    pytest.skip("Node.js is not installed")


def _first_difference(py: list, js: list, inputs: list) -> str:
    for i, (a, b) in enumerate(zip(py, js, strict=False)):  # lengths may differ; the caller compares them
        if a != b:
            return f"case {i}: input {inputs[i]!r:.300}\n python: {str(a):.600}\n     js: {str(b):.600}"
    return f"lengths differ: {len(py)} and {len(js)}"


# --- the bundle ------------------------------------------------------------------


def test_bundle_is_built_from_the_committed_sources():
    for tool in ("bundle_js.py", "measure_xml_names.py"):
        done = subprocess.run([sys.executable, str(ROOT / "tools" / tool), "--check"], capture_output=True, text=True)
        assert done.returncode == 0, done.stdout + done.stderr


def test_bundle_stays_within_the_script_limits():
    """ADR 0030 §1–2 for the JavaScript file: only fs, os and path, no network, no
    child processes, no code built from strings."""
    source = BUNDLE.read_text(encoding="utf-8")
    assert sorted(set(re.findall(r"require\(\s*\"([^\"]+)\"\s*\)", source))) == ["fs", "os", "path"]
    assert "require(" not in re.sub(r"require\(\s*\"(fs|os|path)\"\s*\)", "", source).replace('typeof require !== "undefined"', "")
    for forbidden in (r"child_process", r"\beval\(", r"\bFunction\(", r"\bfetch\(", r"XMLHttpRequest", r"WebSocket", r"\bimport\(", r"process\.env",
                      r"\bDate\b", r"Math\.random"):
        hits = [line[:120] for line in source.splitlines() if re.search(forbidden, line) and not line.lstrip().startswith("//")]
        assert not hits, f"{forbidden!r} in the bundle: {hits[:2]}"


# --- Markdown, build, check --------------------------------------------------------


def test_markdown_is_read_the_same():
    texts = parity.markdown_texts(0, 1500)  # CommonMark, GFM and wide-Unicode text
    js = parity.run_js({"op": "ast", "texts": texts})
    py = [parity.py_ast(t) for t in texts]
    assert py == js, _first_difference(py, js, texts)


def test_build_gives_the_same_result_and_bytes():
    cases = parity.build_cases(0, 400)
    js = parity.run_js(parity.js_build_request(cases))
    py = [parity.py_build(c) for c in cases]
    assert py == js, _first_difference(py, js, cases)
    assert sum(1 for r in py if r["bytes"]) > 150, "too few cases got as far as writing a package"


def test_check_gives_the_same_report():
    corpus = parity.package_corpus(0, 1500)
    js = parity.run_js({"op": "check", "packages": [base64.b64encode(p).decode() for p in corpus]})
    py = [parity.py_check(p) for p in corpus]
    assert py == js, _first_difference(py, js, [p[:80] for p in corpus])
    messages = {f["message"] for r in py for f in r["findings"][:1]}
    for expected in ("not a zip package", "entry cannot be read (corrupt data or checksum)", "entry name appears more than once",
                     "XML is not well-formed", "XML part is not UTF-8"):
        assert expected in messages, f"the corpus never produced {expected!r}"
    assert sum(1 for r in py if r["ok"]) > 50, "too few sound packages in the corpus"


def test_check_decides_each_named_rule_the_same():
    """ADR 0017 rules 9 and the XML reader, one package per rule: the verdict is the
    one written down, and the JavaScript reader gives it too."""
    named = parity.named_packages()
    js = parity.run_js({"op": "check", "packages": [base64.b64encode(p).decode() for _, p, _ in named]})
    assert len(js) == len(named)
    for (what, package, expected), from_js in zip(named, js, strict=True):
        py = parity.py_check(package)
        assert (py["findings"][0]["message"] if py["findings"] else None) == expected, f"{what}: python says {py['findings'][:1]}"
        assert py == from_js, f"{what}:\n python: {py}\n     js: {from_js}"


def test_sara_am_written_the_long_way_is_read_the_same():
    """ADR 0034: the generated corpus never writes ำ the long way, so the two characters
    that look like it are put to both implementations here — same text out, same warning."""
    long_way, short_way = "\u0e17\u0e4d\u0e32", "\u0e17\u0e33"
    texts = [
        long_way + "\n", short_way + "\n", short_way + " " + long_way + "\n",
        "# " + long_way + "\n\n- " + long_way + "\n\n| " + long_way + " |\n|---|\n| " + short_way + " |\n",
        "**" + long_way + "**\n", "`" + long_way + "`\n", "\u0e4d\n", "\u0e32\u0e4d\n",
    ]
    js = parity.run_js({"op": "ast", "texts": texts})
    py = [parity.py_ast(t) for t in texts]
    assert py == js, _first_difference(py, js, texts)
    assert [len(r["warnings"]) for r in py] == [1, 0, 1, 3, 1, 1, 0, 0]


def test_deep_nesting_is_read_or_refused_the_same_way():
    """Past markdown.MAX_DEPTH every later step recurses, so both refuse there, with the
    same message and line, rather than overflow a stack at a depth that depends on the
    runtime — where Python once crashed and Node answered."""
    limit = md.MAX_DEPTH
    texts = []
    for n in (limit - 2, limit, limit * 10):
        texts += [
            ">" * n + " ก\n",
            "".join("  " * i + "- ก\n" for i in range(n // 2 + 1)),
            "*ก " * n + "ข" + " ก*" * n + "\n",
            "| a |\n|---|\n| " + "*ก " * n + "ข" + " ก*" * n + " |\n",
        ]
    js = parity.run_js({"op": "ast", "texts": texts})
    py = [parity.py_ast(t) for t in texts]
    assert py == js, _first_difference(py, js, texts)
    assert {r.get("error", "read") for r in py} == {"read", f"blocks nested more than {limit} deep are not supported",
                                                    f"inline formatting nested more than {limit} deep is not supported"}
    cases = [{"text": t, "args": []} for t in texts]
    built = parity.run_js(parity.js_build_request(cases))
    assert [parity.py_build(c) for c in cases] == built


# --- the command line ----------------------------------------------------------------


def _scenarios(tmp: pathlib.Path) -> list[list[str]]:
    doc, elsewhere = tmp / "doc", tmp / "elsewhere"
    (doc / "sub").mkdir(parents=True)
    elsewhere.mkdir()
    shutil.copy(parity.FIXTURES / "sample.md", doc / "in.md")
    shutil.copy(parity.FIXTURES / "pixel.png", doc / "pixel.png")
    shutil.copy(parity.FIXTURES / "pixel.png", elsewhere / "p.png")
    (doc / "sub" / "เอกสาร.md").write_text("# หัวเรื่อง\n\n![ภาพ](รูป.png)\n", encoding="utf-8")
    shutil.copy(parity.FIXTURES / "pixel.png", doc / "sub" / "รูป.png")
    # a link into the directory, then back out of it: `..` applies to where the link leads
    (doc / "up").symlink_to(elsewhere)
    (doc / "updots.md").write_text("![x](up/../elsewhere/p.png) ![y](up/p.png)\n", encoding="utf-8")
    (elsewhere / "p.png").with_name("chain").symlink_to("p.png")
    (doc / "chain.md").write_text("![x](up/chain)\n", encoding="utf-8")
    (doc / "absolute.md").write_text(f"![x]({doc / 'pixel.png'})\n", encoding="utf-8")
    (doc / "absolute-out.md").write_text(f"![x]({elsewhere / 'p.png'})\n", encoding="utf-8")
    # a Markdown file reached through a link: its images are looked for beside the real file
    (elsewhere / "real.md").write_text("ก\n\n![x](p.png)\n", encoding="utf-8")
    (doc / "via-link.md").symlink_to(elsewhere / "real.md")
    (doc / "outside.md").write_text("ก\n\n![x](../elsewhere/p.png)\n", encoding="utf-8")
    (doc / "link.md").write_text("![x](link.png)\n", encoding="utf-8")
    (doc / "link.png").symlink_to(elsewhere / "p.png")
    (doc / "loop.md").write_text("![x](loop.png)\n", encoding="utf-8")
    (doc / "loop.png").symlink_to(doc / "loop.png")
    (doc / "html.md").write_text("ก <span>x</span>\n", encoding="utf-8")
    (doc / "deep.md").write_text(">" * 1000 + " ก\n", encoding="utf-8")  # once a Python traceback
    (doc / "latin1.md").write_bytes("caf\xe9".encode("latin-1"))
    (doc / "dir.md").mkdir()
    (doc / "unreadable.png").write_bytes(parity.PNG)
    (doc / "unreadable.png").chmod(0)
    (doc / "perm.md").write_text("![x](unreadable.png)\n", encoding="utf-8")
    (tmp / "not-a-zip.docx").write_bytes(b"not a zip")
    with open(tmp / "huge.docx", "wb") as f:  # sparse: one byte past the cap costs no disk
        f.truncate(64 * 1024 * 1024 + 1)
    for f in ("sample-default.docx", "sample-all-flags.docx"):
        shutil.copy(parity.GOLDEN / f, tmp / f)
    shutil.copy(parity.FIXTURES / "legacy-python-docx-default.docx", tmp / "legacy.docx")
    # a package whose only fault is the order of a run's properties
    import zipfile as _zipfile
    with _zipfile.ZipFile(parity.GOLDEN / "sample-default.docx") as _z:
        _parts = {n: _z.read(n) for n in _z.namelist()}
    _parts["word/document.xml"] = _parts["word/document.xml"].replace(
        b'<w:cs/><w:lang w:val="en-US" w:bidi="th-TH"/>',
        b'<w:lang w:val="en-US" w:bidi="th-TH"/><w:cs/>', 1)
    from thai_docx import package as _package
    (tmp / "out-of-order.docx").write_bytes(_package.pack(list(_parts.items())))
    shutil.copytree(parity.FIXTURES / "thesis", tmp / "thesis")
    # profiles a run can read: one in the project, one written by hand, one refused (ADR 0024)
    project = tmp / ".thai-docx" / "profiles"
    project.mkdir(parents=True)
    (project / "report.json").write_text(
        '{\n  "id": "report",\n  "schema": 1,\n  "settings": {\n    "align": "thai",\n    "line_spacing": 1.5,\n'
        '    "margins": [\n      1.0,\n      1.0,\n      1.0,\n      1.5\n    ],\n    "page_numbers": "bottom-center",\n'
        '    "size": 15,\n    "thai_digits": true\n  },\n  "title": {\n    "th": "รายงาน",\n    "en": "Report"\n  }\n}\n',
        encoding="utf-8")
    (tmp / "loose.json").write_text('{"schema": 1, "settings": {"size": 14}}\n', encoding="utf-8")
    (tmp / "bad-key.json").write_text('{"schema": 1, "settings": {"font_size": 14}}\n', encoding="utf-8")
    (tmp / "bad-value.json").write_text('{"schema": 1, "settings": {"size": 500}}\n', encoding="utf-8")
    (tmp / "bad-json.json").write_text("{not json", encoding="utf-8")
    (tmp / "bad-shape.json").write_text('{"schema": 2, "settings": {}}\n', encoding="utf-8")
    (tmp / "sneaky.json").write_text('{"id": "../../escape", "schema": 1, "settings": {"size": 14}}\n', encoding="utf-8")
    (tmp / "big.json").write_text('{"schema": 1, "settings": {}, "version": "' + "x" * 70000 + '"}', encoding="utf-8")
    out = "out.docx"
    return [
        ["build", "doc/in.md", out],
        ["build", "doc/in.md", out, "--toc", "--page-numbers", "--hide-spelling-errors", "--align", "thai", "--paper", "letter", "--size", "15",
         "--margins", "1,1,1,1"],
        ["build", "doc/sub/เอกสาร.md", "ผล.docx", "--font=Sarabun"],
        ["build", "doc/outside.md", out],
        ["build", "doc/outside.md", out, "--allow-dir", "elsewhere"],
        ["build", "doc/link.md", out],
        ["build", "doc/link.md", out, "--allow-dir", str(tmp / "elsewhere")],
        ["build", "doc/loop.md", out],
        ["build", "doc/updots.md", out],
        ["build", "doc/updots.md", out, "--allow-dir", "doc/up"],
        ["build", "doc/chain.md", out, "--allow-dir", "elsewhere/"],
        ["build", "doc/absolute.md", out],
        ["build", "doc/absolute-out.md", out],
        ["build", str(tmp / "doc" / "via-link.md"), out],
        ["build", "doc/./sub/../in.md", out, "--allow-dir", "."],
        ["build", "doc/perm.md", out],
        ["build", "doc/html.md", out],
        ["build", "doc/deep.md", out],
        ["build", "doc/latin1.md", out],
        ["build", "doc/dir.md", out],
        ["build", "doc/missing.md", out],
        ["build", "doc/in.md", "no/such/dir/out.docx"],
        ["build", "doc/in.md", "doc"],
        ["build", "doc/in.md", out, "--margins", "1,2"],
        ["build", "doc/in.md", out, "--indent", "0.5", "--align=thai"],
        ["build", "doc/in.md", out, "--indent", "7"],
        ["build", "doc/in.md", out, "--line-spacing", "1.5", "--indent", "0.5"],
        ["build", "doc/in.md", out, "--line-spacing", "4"],
        ["build", "doc/in.md", out, "--page-numbers", "bottom-center"],
        ["build", "doc/in.md", out, "--landscape", "--paper", "letter", "--indent", "0.5"],
        ["build", "doc/in.md", out, "--landscape", "--margins", "3.5,1,3.5,1"],
        ["build", "doc/in.md", out, "--paper", "f14", "--toc"],
        ["build", "doc/in.md", out, "--page-numbers", "bottom-center", "--no-page-number-first"],
        ["build", "doc/in.md", out, "--no-page-number-first"],
        ["build", "doc/in.md", out, "--table-widths", "auto"],
        ["build", "doc/in.md", out, "--table-size", "12.5", "--size", "15"],
        ["build", "doc/in.md", out, "--table-size", "401"],
        ["build", "doc/in.md", out, "--header", "เอกสารลับ", "--footer", "สำนักงาน", "--page-numbers", "--no-page-number-first", "--thai-digits"],
        ["build", "doc/in.md", out, "--header"],
        ["build", "doc/in.md", out, "--chapter-label", "Chapter", "--table-label=Table", "--figure-label", "Fig."],
        ["build", "doc/in.md", out, "--chapter-label", "บท%"],
        ["build", "doc/in.md", out, "--front-page-numbers", "roman"],
        ["build", "doc/in.md", out, "--appendix-numbers", "lower-roman", "--appendix-label", "ผนวก"],
        ["build", "doc/in.md", out, "--table-widths", "Auto"],
        ["build", "doc/in.md", out, "--heading-numbers", "--toc", "--thai-digits"],
        ["build", "doc/in.md", out, "--paper", "f4"],
        ["build", "doc/in.md", out, "--thai-digits", "--page-numbers", "top-center", "--toc"],
        ["build", "doc/in.md", out, "--page-numbers=top-center", "--toc"],
        ["build", "doc/in.md", out, "--page-numbers", "--toc"],
        ["build", "doc/in.md", out, "--page-numbers=bottom"],
        ["build", "doc/in.md", "--page-numbers", "top-center", out],
        ["build", "doc/in.md", out, "--no-repeat-table-header", "--align", "thai"],
        ["build", "doc/in.md"],
        ["build", "doc/in.md", out, "extra"],
        ["build", "doc/in.md", out, "--allow-dir"],
        ["build", "doc/in.md", out, "--font", "Papyrus"],
        ["build"],
        ["check", "sample-default.docx"],
        ["check", "sample-all-flags.docx"],
        ["check", "legacy.docx"],
        ["check", "not-a-zip.docx"],
        ["check", "huge.docx"],
        ["check", "missing.docx"],
        # repair: the same file out of both, or the same refusal (ADR 0037, 0008)
        ["repair", "legacy.docx", "repaired.docx"],
        ["repair", "out-of-order.docx", "ordered.docx"],   # properties in the wrong order
        ["repair", "sample-default.docx", "clean.docx"],   # nothing to repair: nothing written
        ["repair", "not-a-zip.docx", "nope.docx"],
        ["repair", "missing.docx", "nope.docx"],
        ["repair", "legacy.docx"],                          # one path is not two
        ["repair", "legacy.docx", "dir.md"],                # a path that cannot be written
        ["check", "doc"],
        ["check"],
        ["check", "a.docx", "b.docx"],
        [],
        ["convert", "x"],
        # the release oracle's thesis variants, whose goldens are held below
        *(["build", "thesis/thesis.md", out, *flags] for source, flags, *_ in list(oracle_set.VARIANTS.values())[1:]),
        # profiles (ADR 0024): saved, listed, shown, exported, imported, built with
        ["profile"],
        ["profile", "list"],
        ["profile", "show", "report"],
        ["profile", "show", "loose.json"],
        ["profile", "show", "missing"],
        ["profile", "show", "../outside"],
        ["profile", "save", "mine", "--size", "14", "--indent", "0.5", "--header", "ลับ", "--margins", "1,1,1,1"],
        # whole numbers that are floats: Python writes 1.0, and so must the JavaScript
        ["profile", "save", "whole", "--indent", "1", "--line-spacing", "2", "--margins", "1,2,1,2", "--size", "16"],
        ["profile", "save", "mine", "--from", "report", "--toc", "--no-repeat-table-header"],
        ["profile", "save", "mine", "--size", "0"],
        ["profile", "save", "bad name", "--size", "14"],
        ["profile", "export", "report", "shared.json"],
        ["profile", "export", "missing"],
        ["profile", "import", "loose.json", "--name", "borrowed"],
        ["profile", "import", "bad-key.json"],
        ["profile", "import", "bad-value.json"],
        ["profile", "import", "bad-json.json"],
        ["profile", "import", "bad-shape.json"],
        ["profile", "show", "big.json"],
        *([["profile", "show", "/dev/zero"]] if os.path.exists("/dev/zero") else []),  # no size: read only to the limit
        ["profile", "import", "loose.json", "--name", "a/b"],
        ["profile", "import", "sneaky.json"],
        ["build", "doc/in.md", out, "--profile", "report"],
        ["build", "doc/in.md", out, "--profile", "report", "--size", "18", "--align", "left"],
        ["build", "doc/in.md", out, "--profile", "loose.json"],
        ["build", "doc/in.md", out, "--profile", "missing"],
        ["build", "doc/in.md", out, "--profile"],
        ["build", "thesis/thesis.md", out, "--chapter-title-on-new-line", "--toc"],
        ["build", "doc/in.md", out, "--chapter-title-on-new-line"],  # a document with no regions: the warning
        # flags whose structure the document lacks share a warning per structure (ADR 0028)
        ["build", "doc/in.md", out, "--chapter-label", "บท", "--appendix-label", "Appendix", "--appendix-numbers", "decimal", "--front-page-numbers",
         "decimal", "--figure-label", "ภาพ"],
        ["build", "doc/sub/เอกสาร.md", out, "--table-widths", "auto", "--no-repeat-table-header", "--table-label", "ตาราง"],
        # grill mode is the user's word (ADR 0029): both read the message the same way
        ["grill", "--said", "thai-docx grill"],
        ["grill", "--said", "ขอ THAI_DOCX\tGRILL หน่อย"],
        ["grill", "--said", "ทำไฟล์ word ให้หน่อย ใส่สารบัญ เลขหน้า บทที่ ตารางที่"],
        ["grill", "--said", ""],
        ["grill", "--said", "ก" * 20050 + " thai-docx grill"],
        ["grill", "--said", "THAİ-DOCX GRILL"],  # a letter no ASCII fold touches: neither mode changes
        ["grill", "--said", "thai docx grill from report"],  # the two words joined by a space
        # a character outside the BMP is one character in both, not two (ADR 0029's cap)
        ["grill", "--said", "\U0001F600" * 10000 + " thai-docx grill"],
        ["grill"],
        ["grill", "--message", "thai-docx grill"],
        # grill from a profile, save as another (ADR 0029), and --default
        ["grill", "--said", "thai-docx grill from report save to report-v1"],
        ["grill", "--said", "ขอ thai-docx grill จาก report เฉพาะ toc,2,page-numbers"],
        ["grill", "--said", "THAI_DOCX GRILL บันทึกเป็นv2 only 9"],
        ["grill", "--said", "thai-docx grill from ./.thai-docx//profiles/report.json"],
        ["grill", "--said", "thai-docx grill from missing"],
        ["grill", "--said", "thai-docx grill save to ../x"],
        ["grill", "--said", "thai-docx grill only margins"],
        ["grill", "--said", "thai-docx grill from report from report"],
        ["profile", "show", "./.thai-docx//profiles/./report.json"],
        ["profile", "save", "mine", "--from", "report", "--default", "thai_digits,page_numbers", "--default=size", "--toc"],
        ["build", "doc/in.md", out, "--profile", "report", "--default", "align,line_spacing"],
        ["build", "doc/in.md", out, "--profile", "report", "--default", "bogus"],
        ["build", "doc/in.md", out, "--default"],
    ]


def _run(cmd: list[str], args: list[str], cwd: pathlib.Path) -> tuple:
    for leftover in ("out.docx", "ผล.docx", "shared.json"):
        (cwd / leftover).unlink(missing_ok=True)
    # both implementations start each run from the same home: profiles saved or imported
    # by one must not be there for the other (ADR 0024)
    shutil.rmtree(cwd / "home", ignore_errors=True)
    env = {**os.environ, "HOME": str(cwd / "home"), "USERPROFILE": str(cwd / "home")}
    # a bounded wait: a path walk that never ends must fail this test, not hang the job
    done = subprocess.run(cmd + args, cwd=cwd, capture_output=True, timeout=60, env=env)
    written = {name: (cwd / name).read_bytes() for name in ("out.docx", "ผล.docx", "shared.json") if (cwd / name).exists()}
    home = cwd / "home" / ".thai-docx" / "profiles"
    written.update({"home/" + p.name: p.read_bytes() for p in sorted(home.glob("*.json"))} if home.is_dir() else {})
    return done.returncode, done.stdout.decode("utf-8"), done.stderr.decode("utf-8"), written


def test_a_writer_defect_is_refused_the_same_way(tmp_path):
    """The one road to exit 1 from build: the writer breaks a cause and its own check
    refuses the package. No input reaches it, so the same defect is planted in both."""
    python_lang = "LANG = '<w:cs/><w:lang w:val=\"en-US\"/>'"
    js_lang = "const LANG = '<w:cs/><w:lang w:val=\"en-US\"/>';"
    assert python_lang in (ROOT / "skills/thai-docx/scripts/thai_docx/writer.py").read_text(encoding="utf-8")
    source = BUNDLE.read_text(encoding="utf-8")
    assert source.count(js_lang) == 1
    broken = tmp_path / "broken.cjs"
    # the run loses <w:cs/>, which is cause 1's fix and finding 2 (ADR 0038)
    broken.write_text(source.replace(js_lang, "const LANG = '<w:lang w:val=\"en-US\"/>';"), encoding="utf-8")
    (tmp_path / "in.md").write_text("ก\n", encoding="utf-8")
    planted = ("import sys; sys.path.insert(0, sys.argv[1]); from thai_docx import writer, __main__; "
               "writer.LANG = '<w:lang w:val=\"en-US\"/>'; sys.exit(__main__.main(sys.argv[2:]))")
    args = ["build", "in.md", "out.docx"]
    py = _run([sys.executable, "-c", planted, str(ROOT / "skills/thai-docx/scripts")], args, tmp_path)
    js = _run(["node", str(broken)], args, tmp_path)
    assert py[0] == 1 and '"code": "2"' in py[1] and py[3] == {}, py[:2]
    assert py == js, f"\n python: {py[:3]}\n     js: {js[:3]}"


def test_command_line_is_the_same(tmp_path):
    if os.geteuid() == 0:
        pytest.skip("running as root: an unreadable file is readable")
    runs = []
    for args in _scenarios(tmp_path):
        py, js = _run(PY_CLI, args, tmp_path), _run(JS_CLI, args, tmp_path)
        assert py[2] == "", f"{args}: python wrote to stderr: {py[2][-800:]}"
        assert py == js, f"{args}:\n python: {py[:3]}\n     js: {js[:3]}"
        runs.append((args, py))
    codes = {tuple(a[:1]) + (code,) for a, (code, *_rest) in runs}
    assert {("build", 0), ("build", 2), ("check", 0), ("check", 1), ("check", 2)} <= codes  # build exits 1 only on a writer defect
    default = next(r for a, r in runs if a == ["build", "doc/in.md", "out.docx"])
    assert default[3]["out.docx"] == (parity.GOLDEN / "sample-default.docx").read_bytes()
    all_flags = runs[1][1]
    assert all_flags[3]["out.docx"] == (parity.GOLDEN / "sample-all-flags.docx").read_bytes()
    thesis = [(a, r) for a, r in runs if a[:2] == ["build", "thesis/thesis.md"]]
    # thesis has one more run
    for (args, run), (_source, _flags, golden, *_) in zip(thesis, list(oracle_set.VARIANTS.values())[1:], strict=False):
        assert run[0] == 0 and run[3]["out.docx"] == (parity.GOLDEN / f"{golden}.docx").read_bytes(), args
    assert len(thesis) == 5  # the four golden variants, then --chapter-title-on-new-line
    assert thesis[4][1][3]["out.docx"] not in [(parity.GOLDEN / f"{g}.docx").read_bytes()
                                               for _s, _f, g, *_ in oracle_set.VARIANTS.values()]
