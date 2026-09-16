"""`thai_docx build`: faithful to the Markdown (ADR 0005), the same bytes every
run (ADR 0008), and never a file that fails its own checker (ADR 0007).
"""

from __future__ import annotations

import hashlib
import io
import json
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

import pytest

from thai_docx import build as b
from thai_docx import fidelity as fi
from thai_docx import layout as lo
from thai_docx import markdown as md
from thai_docx import parts as pa
from thai_docx import writer as wr
from thai_docx.check import check

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "thai-docx" / "scripts" / "thai_docx"
FIXTURES = ROOT / "tests" / "fixtures"
GOLDEN = ROOT / "tests" / "golden"
ALL_FLAGS = ["--toc", "--page-numbers", "--hide-spelling-errors", "--align", "thai", "--paper", "letter", "--size", "15", "--margins", "1,1,1,1"]
sys.path.insert(0, str(ROOT / "tools"))
import oracle_set  # noqa: E402  the release oracle's variants (ADR 0012) are goldens too
GOLDENS = [("sample-default", FIXTURES / "sample.md", []), ("sample-all-flags", FIXTURES / "sample.md", ALL_FLAGS)] + [
    (golden, source, flags) for source, flags, golden, _about in oracle_set.VARIANTS.values() if golden != "sample-default"
]


def run_cli(*args) -> tuple[int, dict]:
    done = subprocess.run([sys.executable, str(SCRIPT), "build", *map(str, args)], capture_output=True, text=True)
    assert done.stderr == "", done.stderr
    return done.returncode, json.loads(done.stdout)


def build(tmp_path, text: str, **opts) -> tuple[dict, pathlib.Path]:
    src = tmp_path / "in.md"
    src.write_text(text, encoding="utf-8")
    out = tmp_path / "out.docx"
    o = dict(b.DEFAULTS)
    o.update(opts)
    return b.build(src, out, o, []), out


# --- goldens: the same bytes, every run, every machine (ADR 0008) ---


@pytest.mark.parametrize("name,source,flags", GOLDENS)
def test_sample_matches_golden_bytes(tmp_path, name, source, flags):
    out = tmp_path / f"{name}.docx"
    code, result = run_cli(source, out, *flags)
    assert code == 0 and result["ok"], result
    golden = (GOLDEN / f"{name}.docx").read_bytes()
    assert out.read_bytes() == golden, "output differs from the committed golden — a deliberate change regenerates the golden and says so in the commit"
    assert result["sha256"] == hashlib.sha256(golden).hexdigest()


def test_zip_entries_are_stored_with_fixed_metadata():
    with zipfile.ZipFile(GOLDEN / "sample-default.docx") as zf:
        names = [i.filename for i in zf.infolist()]
        assert names[0] == "[Content_Types].xml"
        for info in zf.infolist():
            assert info.compress_type == zipfile.ZIP_STORED
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
            assert info.create_system == 0


def test_docprops_carry_only_front_matter(tmp_path):
    _, out = build(tmp_path, "---\ntitle: ชื่อ\nauthor: ผู้เขียน\n---\n\nก")
    core = zipfile.ZipFile(out).read("docProps/core.xml").decode()
    assert "<dc:title>ชื่อ</dc:title><dc:creator>ผู้เขียน</dc:creator>" in core
    assert "created" not in core and "modified" not in core
    _, out = build(tmp_path, "ก")
    assert zipfile.ZipFile(out).read("docProps/core.xml").decode().endswith("></cp:coreProperties>")


# --- fidelity (ADR 0005) ---


def test_sample_text_round_trips_paragraph_for_paragraph():
    doc = md.parse((FIXTURES / "sample.md").read_text(encoding="utf-8"))
    with zipfile.ZipFile(GOLDEN / "sample-default.docx") as zf:
        parts = {n: zf.read(n) for n in zf.namelist()}
    assert fi.docx_text(parts, len(doc.footnote_order)) == fi.expected_text(doc)
    assert "☐ งานที่ยังไม่ทำ" in fi.docx_text(parts, 1)


def test_a_writer_that_drops_a_character_is_refused(tmp_path, monkeypatch):
    original = wr.Writer.text_run

    def lossy(self, node, extra=""):
        node = dict(node, s=node["s"][:-1]) if node["s"].endswith("ข") else node
        return original(self, node, extra)

    monkeypatch.setattr(wr.Writer, "text_run", lossy)
    result, out = build(tmp_path, "กข")
    assert not result["ok"] and [f["code"] for f in result["findings"]] == ["fidelity"]
    assert "กข" not in json.dumps(result, ensure_ascii=False), "a finding never quotes the document"
    assert not out.exists(), "nothing is written when the check fails"


def test_a_writer_that_breaks_a_cause_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(wr, "LANG", "<w:cs/>")
    monkeypatch.setattr(pa, "LANG", "<w:cs/>")  # the package's other parts name it too
    result, out = build(tmp_path, "ก")
    assert not result["ok"] and {f["code"] for f in result["findings"]} == {"2"}
    assert not out.exists()


def test_empty_heading_is_still_a_paragraph_with_text(tmp_path):
    result, out = build(tmp_path, "#\n\nก")
    assert result["ok"]
    assert '<w:t xml:space="preserve"></w:t>' in zipfile.ZipFile(out).read("word/document.xml").decode()


def test_special_characters_are_escaped(tmp_path):
    result, out = build(tmp_path, 'a & b < c > "d" [e](https://x.example/?a=1&b=2)')
    assert result["ok"]
    doc = zipfile.ZipFile(out).read("word/document.xml").decode()
    assert "a &amp; b &lt; c &gt; \"d\" " in doc
    assert 'Target="https://x.example/?a=1&amp;b=2"' in zipfile.ZipFile(out).read("word/_rels/document.xml.rels").decode()


# --- images and the script limits (ADR 0011, 0022) ---


def test_image_outside_the_markdown_directory_is_refused_unless_allowed(tmp_path):
    other = tmp_path / "elsewhere"
    other.mkdir()
    shutil.copy(FIXTURES / "pixel.png", other / "p.png")
    src_dir = tmp_path / "doc"
    src_dir.mkdir()
    src = src_dir / "in.md"
    src.write_text("![alt](../elsewhere/p.png)", encoding="utf-8")
    out = tmp_path / "out.docx"
    result = b.build(src, out, dict(b.DEFAULTS), [])
    assert "outside" in result["error"] and not out.exists()
    result = b.build(src, out, dict(b.DEFAULTS), [other])
    assert result["ok"] and result["counts"]["images"] == 1


def test_remote_and_non_image_files_are_refused(tmp_path):
    (tmp_path / "fake.png").write_bytes(b"GIF89a not really")
    assert "remote" in build(tmp_path, "![a](https://x.example/p.png)")[0]["error"]
    assert "not a PNG or JPEG" in build(tmp_path, "![a](fake.png)")[0]["error"]
    assert "No such file" in build(tmp_path, "![a](missing.png)")[0]["error"]


def test_image_is_scaled_to_the_text_width(tmp_path):
    shutil.copy(FIXTURES / "pixel.png", tmp_path / "p.png")
    _, out = build(tmp_path, "![a](p.png)", margins=(1, 3.5, 1, 3.5))
    doc = zipfile.ZipFile(out).read("word/document.xml").decode()
    text_width_emu = (b.PAPER["a4"][0] - 2 * int(3.5 * 1440)) * wr.EMU_PER_TWIP  # narrower than 200 px
    cx, cy = text_width_emu, 50 * wr.EMU_PER_PX * text_width_emu // (200 * wr.EMU_PER_PX)
    assert f'cx="{cx}" cy="{cy}"' in doc


def test_jpeg_dimensions_are_read_from_sof():
    jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\xff\xc0\x00\x11\x08\x00\x20\x00\x40\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01" + b"\xff\xd9"
    assert wr._image_size(jpeg) == ("jpeg", 64, 32)


def test_unreferenced_footnote_is_refused(tmp_path):
    result, _ = build(tmp_path, "ก\n\n[^x]: never used")
    assert "never referenced" in result["error"]


# --- settings (ADR 0026) ---


def test_defaults_are_announced_and_flags_change_the_package(tmp_path):
    result, out = build(tmp_path, "ก")
    assert result["settings"] == {
        "font": "TH Sarabun New", "size_pt": 16, "paper": "a4", "landscape": False,
        "margins_in": {"top": 1.0, "right": 1.0, "bottom": 1.0, "left": 1.5},
        "first_line_indent_in": 0.0, "line_spacing": 1.0, "align": "left", "toc": False, "heading_numbers": False, "page_numbers": False, "page_number_on_first": True, "header": None, "footer": None, "thai_digits": False, "hide_spelling_errors": False, "repeat_table_header": True, "table_widths": "equal", "table_size_pt": None,
        "chapter_label": "บทที่", "table_label": "ตารางที่", "figure_label": "รูปที่",
        "front_page_numbers": "thai-letters", "appendix_label": "ภาคผนวก", "appendix_numbers": "thai-letters",
        "chapter_title_on_new_line": False,
    }
    settings = zipfile.ZipFile(out).read("word/settings.xml").decode()
    assert "hideSpellingErrors" not in settings and "updateFields" not in settings

    result, out = build(tmp_path, "ก", font="Sarabun", size=14, hide_spelling_errors=True, toc=True, page_numbers="top-right", align="thai")
    assert result["ok"] and result["warnings"] == []
    with zipfile.ZipFile(out) as zf:
        settings, styles, doc = (zf.read(f"word/{n}.xml").decode() for n in ("settings", "styles", "document"))
        assert "<w:hideSpellingErrors/><w:hideGrammaticalErrors/>" in settings and '<w:updateFields w:val="true"/>' in settings
        assert 'w:cs="Sarabun"' in styles and '<w:sz w:val="28"/><w:szCs w:val="28"/>' in styles and 'thaiDistribute' in styles
        assert "TOC \\o" in doc and "headerReference" in doc and " PAGE " in zf.read("word/header1.xml").decode()


def test_table_header_row_repeats_unless_turned_off(tmp_path):
    table = "| ก | ข |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n"
    for flags, repeats in (([], 1), (["--no-repeat-table-header"], 0)):
        opts, _, _ = b.parse_args(flags + ["in.md", "out.docx"])
        result, out = build(tmp_path, table, **opts)
        doc = zipfile.ZipFile(out).read("word/document.xml").decode()
        assert result["ok"] and result["settings"]["repeat_table_header"] == bool(repeats)
        assert doc.count("<w:tblHeader/>") == repeats and doc.count("<w:tr>") == 3
        # text clear of the borders, and rows no taller than their text
        assert doc.count(wr.CELL_MARGINS) == 1 and doc.count('<w:pPr><w:spacing w:after="0"/></w:pPr>') == 6
    with pytest.raises(b.BuildError, match="takes no value"):
        b.parse_args(["--no-repeat-table-header=yes", "in.md", "out.docx"])


def test_first_line_indent_reaches_body_paragraphs_only(tmp_path):
    text = (
        "# หัวเรื่อง\n\nย่อหน้าแรก\n\n## รอง\n\nย่อหน้าสอง[^1]\n\n> คำพูด\n\n- รายการ\n\n  ต่อในรายการ\n\n"
        "| ก |\n|---|\n| ข |\n\n    โค้ด\n\nย่อหน้าสาม\n\n[^1]: เชิงอรรถ\n\n    ย่อหน้าที่สองของเชิงอรรถ\n"
    )
    result, out = build(tmp_path, text, indent=0.5)
    assert result["ok"] and result["settings"]["first_line_indent_in"] == 0.5
    with zipfile.ZipFile(out) as zf:
        doc, notes = zf.read("word/document.xml").decode(), zf.read("word/footnotes.xml").decode()
    indented = [p for p in doc.split("<w:p>") if 'w:firstLine="720"' in p]
    assert len(indented) == 3 and all(p.startswith('<w:pPr><w:ind w:firstLine="720"/></w:pPr>') for p in indented)
    assert "firstLine" not in notes
    for other in ("หัวเรื่อง", "รอง", "คำพูด", "รายการ", "ต่อในรายการ", ">ข<", "โค้ด"):
        assert not any(other in p for p in indented), other
    # no indent writes no w:ind at all, so the goldens keep their bytes
    result, out = build(tmp_path, text)
    assert "firstLine" not in zipfile.ZipFile(out).read("word/document.xml").decode()


def test_indent_flag_takes_inches_and_leaves_room_for_text():
    opts, _, _ = b.parse_args(["--indent", "1", "in.md", "out.docx"])
    assert opts["indent"] == 1.0
    for bad, message in ((["--indent", "-1"], "non-negative"), (["--indent", "abc"], "non-negative"), (["--indent", "6"], "less than one inch")):
        with pytest.raises(b.BuildError, match=message):
            b.parse_args(bad + ["in.md", "out.docx"])


def test_table_size_sets_the_cell_text_size_through_a_style(tmp_path):
    text = "ย่อหน้า\n\n| ก | ข |\n|---|--:|\n| 1 | 2 |\n"
    for flags, size in (([], None), (["--table-size", "14"], 14), (["--table-size=12.5"], 12.5)):
        opts, _, _ = b.parse_args(flags + ["in.md", "out.docx"])
        result, out = build(tmp_path, text, **opts)
        with zipfile.ZipFile(out) as zf:
            doc, styles = zf.read("word/document.xml").decode(), zf.read("word/styles.xml").decode()
        assert result["ok"] and result["findings"] == [] and result["settings"]["table_size_pt"] == size
        if size is None:
            assert "TableText" not in styles and "TableText" not in doc
            continue
        half = str(int(size * 2))
        assert (f'<w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/><w:basedOn w:val="Normal"/><w:qFormat/>'
                f'<w:rPr><w:sz w:val="{half}"/><w:szCs w:val="{half}"/></w:rPr></w:style>') in styles
        assert doc.count('<w:pPr><w:pStyle w:val="TableText"/><w:spacing w:after="0"/>') == 4, "every cell, and only cells"
        assert '<w:pPr><w:pStyle w:val="TableText"/><w:spacing w:after="0"/><w:jc w:val="right"/></w:pPr>' in doc
    for bad in (["--table-size", "0"], ["--table-size", "14pt"], ["--table-size", "401"]):
        with pytest.raises(b.BuildError, match="--table-size takes a number of points from 1 to 400"):
            b.parse_args(bad + ["in.md", "out.docx"])


def test_table_widths_auto_follows_the_longest_text_in_each_column(tmp_path):
    # marks above and below take no width; the <br> splits a cell into lines measured apart
    table = "| ลำดับ | รายการ | หมายเหตุ |\n|---:|---|---|\n| 1 | ปากกาลูกลื่นสีน้ำเงิน | ab<br>c |\n| 12 | x | y |\n"
    width = b.PAPER["a4"][0] - 1440 - 2160
    for flags, expected in (
        ([], [width // 3] * 3),
        (["--table-widths", "auto"], None),
    ):
        opts, _, _ = b.parse_args(flags + ["in.md", "out.docx"])
        result, out = build(tmp_path, table, **opts)
        doc = zipfile.ZipFile(out).read("word/document.xml").decode()
        grid = [int(x) for x in re.findall(r'<w:gridCol w:w="(\d+)"/>', doc)]
        assert result["ok"] and result["settings"]["table_widths"] == opts["table_widths"]
        if expected is None:
            need = [4, 15, 7]  # ลำดับ less its ั; ปากกาลูกลื่นสีน้ำเงิน less 6 marks; หมายเหตุ less its ุ
            floor = width // 12
            expected = [floor + (width - 3 * floor) * k // sum(need) for k in need]
            expected[-1] += width - sum(expected)
            assert sum(grid) == width and grid[1] > grid[2] > grid[0] >= floor
        assert grid == expected
        cells = [int(x) for x in re.findall(r'<w:tcW w:w="(\d+)" w:type="dxa"/>', doc)]
        assert cells == expected * 3, "every cell takes its column's width"
    with pytest.raises(b.BuildError, match="takes equal or auto"):
        b.parse_args(["--table-widths", "fit", "in.md", "out.docx"])


def test_page_numbers_go_where_the_flag_places_them(tmp_path):
    cases = (
        (["--page-numbers"], "top-right", "header", "hdr", "right"),
        (["--page-numbers", "top-center"], "top-center", "header", "hdr", "center"),
        (["--page-numbers=bottom-center"], "bottom-center", "footer", "ftr", "center"),
    )
    for flags, where, kind, tag, jc in cases:
        opts, positional, _ = b.parse_args(flags + ["in.md", "out.docx"])
        assert opts["page_numbers"] == where and positional == ["in.md", "out.docx"]
        result, out = build(tmp_path, "ก", **opts)
        assert result["ok"] and result["settings"]["page_numbers"] == where
        with zipfile.ZipFile(out) as zf:
            names = zf.namelist()
            part = zf.read(f"word/{kind}1.xml").decode()
            doc, types, rels = (zf.read(n).decode() for n in ("word/document.xml", "[Content_Types].xml", "word/_rels/document.xml.rels"))
        other = {"header": "footer", "footer": "header"}[kind]
        assert f"word/{other}1.xml" not in names and f"{other}Reference" not in doc
        assert part.startswith(wr.XML + f"<w:{tag} ") and part.endswith(f"</w:{tag}>") and f'<w:jc w:val="{jc}"/>' in part and " PAGE " in part
        assert f'<w:{kind}Reference w:type="default"' in doc and f"wordprocessingml.{kind}+xml" in types and f'Target="{kind}1.xml"' in rels
    # a following argument is a position only when it names one
    opts, positional, _ = b.parse_args(["--page-numbers", "in.md", "out.docx"])
    assert opts["page_numbers"] == "top-right" and positional == ["in.md", "out.docx"]
    for bad in (["--page-numbers=bottom"], ["--page-numbers="], ["--page-numbers=Top-Center"]):
        with pytest.raises(b.BuildError, match="top-right, top-center or bottom-center"):
            b.parse_args(bad + ["in.md", "out.docx"])


def _heading_style(styles: str, n: int) -> str:
    return styles.split(f'w:styleId="Heading{n}"', 1)[1].split("</w:style>", 1)[0]


def test_front_matter_heading_styles_become_the_word_heading_styles(tmp_path):
    """ADR 0020: heading-1 … heading-6 carry CSS-like properties into Heading 1–6."""
    text = (
        "---\n"
        "title: รายงาน\n"
        'heading-1: font-family: "TH SarabunPSK"; font-size: 20.5pt; color: #1f4e79; font-weight: normal; font-style: italic; text-align: center; page-break-before: always\n'
        "heading-2: text-decoration: underline double line-through; margin-left: 1.27cm; text-indent: -0.25in; margin-top: 18pt; margin-bottom: 0; line-height: 1.5\n"
        "heading-3: text-decoration: wavy underline; text-indent: 0.5in; text-align: thai-distribute\n"
        "---\n\n# บทที่ 1\n\n## ส่วน\n\n### ย่อย\n\n#### ไม่ได้ตั้ง\n"
    )
    result, out = build(tmp_path, text, heading_numbers=True)
    styles = zipfile.ZipFile(out).read("word/styles.xml").decode()
    doc = zipfile.ZipFile(out).read("word/document.xml").decode()
    assert result["ok"] and result["findings"] == [] and result["warnings"] == []
    assert "heading-1" not in doc and "SarabunPSK" not in doc, "front matter never enters the body"
    h1, h2, h3 = (_heading_style(styles, n) for n in (1, 2, 3))
    assert ('<w:pPr><w:keepNext/><w:keepLines/><w:pageBreakBefore/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="2"/></w:numPr>'
            '<w:spacing w:before="240" w:after="80"/><w:jc w:val="center"/><w:outlineLvl w:val="0"/></w:pPr>') in h1
    assert ('<w:rPr><w:rFonts w:ascii="TH SarabunPSK" w:hAnsi="TH SarabunPSK" w:cs="TH SarabunPSK" w:eastAsia="TH SarabunPSK"/>'
            '<w:i/><w:iCs/><w:color w:val="1F4E79"/><w:sz w:val="41"/><w:szCs w:val="41"/></w:rPr>') in h1, "normal weight drops the built-in bold"
    assert ('<w:spacing w:before="360" w:after="0" w:line="360" w:lineRule="auto"/><w:ind w:left="720" w:hanging="360"/><w:jc w:val="left"/>') in h2
    assert '<w:rPr><w:b/><w:bCs/><w:strike/><w:sz w:val="36"/><w:szCs w:val="36"/><w:u w:val="double"/></w:rPr>' in h2
    assert '<w:ind w:firstLine="720"/><w:jc w:val="thaiDistribute"/>' in h3 and '<w:u w:val="wave"/></w:rPr>' in h3
    # a level the front matter leaves alone keeps exactly the built-in style
    _, plain = build(tmp_path, "#### ไม่ได้ตั้ง\n", heading_numbers=True)
    assert _heading_style(styles, 4) == _heading_style(zipfile.ZipFile(plain).read("word/styles.xml").decode(), 4)


def test_front_matter_heading_styles_refuse_what_they_do_not_know_and_warn_on_near_misses(tmp_path):
    for front, line, message in (
        ("heading-1: colour: #FF0000", 2, "unknown property 'colour'"),
        ("title: x\nheading-2: color: red", 3, "heading-2: color takes #RRGGBB"),
        ("heading-1: font-size: 20", 2, "takes points"),
        ("heading-1: margin-left: -1in", 2, "not negative"),
        ("heading-1: text-indent: 10.5in", 2, "at most 10in"),
        ("heading-1: bold", 2, "not a property: value pair"),
        ('heading-1: font-family: "TH; Sarabun', 2, "double quote is not closed"),
        ("heading-1: text-decoration: double line-through", 2, "takes none, or underline"),
        ("heading-1: text-decoration: underline underline", 2, "takes none, or underline"),
        ("heading-1: font-weight: Bold", 2, "takes bold or normal"),
    ):
        result, out = build(tmp_path, "---\n" + front + "\n---\n\n# ก\n")
        assert result.get("line") == line and message in result["error"], (front, result)
        assert not out.exists()
    result, _ = build(tmp_path, "---\nheading1: font-size: 20pt\nh2: color: #000000\nheading-7: x\nauthor: ก\n---\n\n# ก\n")
    assert result["ok"] and [w["message"] for w in result["warnings"]] == [
        f"line {n}: front matter key '{k}' is not used; heading styles are heading-1 to heading-6" for n, k in ((2, "heading1"), (3, "h2"), (4, "heading-7"))
    ]
    result, _ = build(tmp_path, "---\nheading-1: font-family: Papyrus\n---\n\n# ก\n")
    assert result["ok"] and [w["code"] for w in result["warnings"]] == ["font"], "a font with no Thai glyphs warns, as --font does"


THESIS = """ปก

<!-- front -->

# บทคัดย่อ

ย่อ

# สารบัญ

<!-- toc -->

<!-- list-of-tables -->

<!-- chapters -->

# บทนำ

## ที่มา

Table: สาเหตุ

| ก | ข |
|---|---|
| 1 | 2 |

![](p.png)

Figure: ขั้นตอน

# ทฤษฎี

Table: รูปแบบ

| ก | ข |
|---|---|
| 1 | 2 |

<!-- back -->

# ภาคผนวก ก

Table: ข้อมูล

| ก | ข |
|---|---|
| 1 | 2 |
"""


def _sections(doc: str) -> list[str]:
    return re.findall(r"<w:sectPr>.*?</w:sectPr>", doc)


def test_regions_make_a_section_of_every_chapter_and_page_before_and_after(tmp_path):
    """ADR 0021: the cover, each # in front, chapters and back, each a next-page section;
    front pages count ก ข ค from ก, the chapters from 1 on through the back."""
    shutil.copy(FIXTURES / "pixel.png", tmp_path / "p.png")
    opts, _, _ = b.parse_args(["--page-numbers", "bottom-center", "--heading-numbers", "in.md", "out.docx"])
    result, out = build(tmp_path, THESIS, **opts)
    with zipfile.ZipFile(out) as zf:
        doc, styles, numbering, settings = (zf.read(f"word/{n}.xml").decode() for n in ("document", "styles", "numbering", "settings"))
        names = zf.namelist()
    assert result["ok"] and result["findings"] == [] and result["warnings"] == [], result
    sections = _sections(doc)
    assert len(sections) == 6  # cover, บทคัดย่อ, สารบัญ, บทนำ, ทฤษฎี, ภาคผนวก ก
    assert doc.count("<w:sectPr>") == 6 and doc.endswith(sections[-1] + "</w:body></w:document>")
    numbering_of = [re.search(r"<w:pgNumType[^>]*/>", s).group(0) if "pgNumType" in s else "" for s in sections]
    assert numbering_of == ["", '<w:pgNumType w:fmt="thaiLetters" w:start="1"/>', '<w:pgNumType w:fmt="thaiLetters"/>',
                            '<w:pgNumType w:fmt="decimal" w:start="1"/>', '<w:pgNumType w:fmt="decimal"/>', '<w:pgNumType w:fmt="decimal"/>']
    assert 'r:id="rId3"' in sections[0] and all('<w:footerReference w:type="default" r:id="rId2"/>' in s for s in sections[1:])
    assert "word/footer2.xml" in names and "PAGE" not in zipfile.ZipFile(out).read("word/footer2.xml").decode(), "the cover's footer has no number"
    # a section closes inside its last paragraph, never in an empty paragraph of its own
    assert doc.count("</w:sectPr></w:pPr>") == 5
    assert '<w:p><w:pPr><w:sectPr>' + sections[0][len("<w:sectPr>"):] + '</w:pPr><w:r>' in doc, "the cover closes in its own text"
    # chapters: "บทที่ n" on #, 1.1 on ##; headings outside the chapters are unnumbered
    assert '<w:lvlText w:val="บทที่ %1"/>' in numbering and '<w:lvlText w:val="%1.%2"/>' in numbering
    assert doc.count('<w:pStyle w:val="Heading1"/><w:numPr><w:numId w:val="0"/></w:numPr>') == 3  # บทคัดย่อ, สารบัญ, ภาคผนวก ก
    assert '<w:pStyle w:val="Heading1"/></w:pPr><w:r><w:rPr>' + wr.LANG + '</w:rPr><w:t xml:space="preserve">บทนำ' in doc
    # directives become fields, and Word is asked to fill them in
    assert ' TOC \\o "1-3" \\h \\z \\u ' in doc and ' TOC \\h \\z \\c "Table" ' in doc and '<w:updateFields w:val="true"/>' in settings
    assert 'w:styleId="Caption"' in styles and 'w:styleId="TableofFigures"' in styles and 'w:styleId="TOC1"' in styles
    # captions: chapter-number-seq inside the chapters, restarting at every #, plain in the back
    parts = {n: zipfile.ZipFile(out).read(n) for n in names}
    text = fi.docx_text(parts, 0)
    captions = [t for t in text if t.startswith(("ตารางที่", "รูปที่"))]
    assert captions == ["ตารางที่ 1-1 สาเหตุ", "ตารางที่ 2-1 รูปแบบ", "ตารางที่ 1 ข้อมูล",  # the list of tables holds them
                        "ตารางที่ 1-1 สาเหตุ", "รูปที่ 1-1 ขั้นตอน", "ตารางที่ 2-1 รูปแบบ", "ตารางที่ 1 ข้อมูล"]
    # ADR 0027: the lists carry their entries, so an application that never updates a field shows them
    assert text[4:10] == ["บทคัดย่อ", "สารบัญ", "บทที่ 1 บทนำ", "ที่มา", "บทที่ 2 ทฤษฎี", "ภาคผนวก ก"], text[:12]
    assert doc.count('<w:pStyle w:val="TOC1"/>') == 8 and doc.count('<w:pStyle w:val="TOC2"/>') == 1
    assert '<w:fldChar w:fldCharType="separate"/></w:r><w:r><w:rPr>' + wr.LANG + '</w:rPr><w:t xml:space="preserve">บทคัดย่อ</w:t>' in doc
    assert ' STYLEREF 1 \\s ' in doc and ' SEQ Table \\* ARABIC \\s 1 ' in doc and ' SEQ Figure \\* ARABIC \\s 1 ' in doc
    assert '<w:pPr><w:pStyle w:val="Caption"/><w:keepNext/></w:pPr>' in doc, "a table caption stays with its table"
    assert '<w:pPr><w:keepNext/></w:pPr><w:r><w:rPr>' + wr.LANG + '</w:rPr><w:drawing>' in doc, "an image stays with its caption"
    assert '<w:pPr><w:pStyle w:val="Caption"/><w:jc w:val="center"/><w:sectPr>' in doc, "the figure's caption ends chapter 1"


APPENDICES = """<!-- front -->

# บทคัดย่อ

<!-- chapters -->

# บทนำ

<!-- back -->

# บรรณานุกรม

<!-- appendices -->

# แบบสอบถาม

## ส่วนที่ 1

Table: ผู้ตอบ

| ก |
|---|
| 1 |

# ข้อมูลดิบ

Table: ชุดที่ 1

| ก |
|---|
| 1 |

<!-- back -->

# ประวัติผู้เขียน
"""


def test_appendices_are_lettered_and_front_pages_take_the_chosen_numbers(tmp_path):
    cases = (
        ([], "thaiLetters", "ภาคผนวก %1", "thaiLetters", ["ตารางที่ ก-1 ผู้ตอบ", "ตารางที่ ข-1 ชุดที่ 1"]),
        (["--front-page-numbers", "lower-roman", "--appendix-numbers", "upper-letters", "--appendix-label", "Appendix"],
         "lowerRoman", "Appendix %1", "upperLetter", ["ตารางที่ A-1 ผู้ตอบ", "ตารางที่ B-1 ชุดที่ 1"]),
        (["--front-page-numbers=upper-roman", "--appendix-numbers", "upper-roman"], "upperRoman", "ภาคผนวก %1", "upperRoman", ["ตารางที่ I-1 ผู้ตอบ", "ตารางที่ II-1 ชุดที่ 1"]),
        (["--front-page-numbers", "decimal", "--appendix-numbers", "decimal", "--thai-digits"], "thaiNumbers", "ภาคผนวก %1", "thaiNumbers", ["ตารางที่ ๑-๑ ผู้ตอบ", "ตารางที่ ๒-๑ ชุดที่ 1"]),
    )
    for flags, front, label, appendix_fmt, captions in cases:
        opts, _, _ = b.parse_args(flags + ["--heading-numbers", "in.md", "out.docx"])
        result, out = build(tmp_path, APPENDICES, **opts)
        with zipfile.ZipFile(out) as zf:
            parts = {n: zf.read(n) for n in zf.namelist()}
        doc, numbering = parts["word/document.xml"].decode(), parts["word/numbering.xml"].decode()
        assert result["ok"] and result["findings"] == [] and result["warnings"] == [], result
        assert re.findall(r"<w:pgNumType[^>]*/>", doc)[0] == f'<w:pgNumType w:fmt="{front}" w:start="1"/>'
        assert len(_sections(doc)) == 6  # บทคัดย่อ, บทนำ, บรรณานุกรม, แบบสอบถาม, ข้อมูลดิบ, ประวัติผู้เขียน
        appendix = numbering.split('<w:abstractNum w:abstractNumId="3">', 1)[1].split("</w:abstractNum>", 1)[0]
        assert appendix.startswith(f'<w:multiLevelType w:val="multilevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="{appendix_fmt}"/><w:suff w:val="space"/><w:lvlText w:val="{label}"/>')
        assert "pStyle" not in appendix, "set on each appendix heading, so Heading 1 stays the chapters'"
        # no numbered list here: the headings' list is numId 2, the appendices' 3
        assert doc.count('<w:numPr><w:ilvl w:val="0"/><w:numId w:val="3"/></w:numPr>') == 2 and '<w:numPr><w:ilvl w:val="1"/><w:numId w:val="3"/></w:numPr>' in doc
        assert doc.count('<w:pStyle w:val="Heading1"/><w:numPr><w:numId w:val="0"/></w:numPr>') == 3  # บทคัดย่อ, บรรณานุกรม, ประวัติผู้เขียน
        assert [t for t in fi.docx_text(parts, 0) if t.startswith("ตารางที่")] == captions
    assert lo.number_text(27, "upper-letters", False) == "AA" and lo.number_text(3, "thai-letters", False) == "ค" and lo.number_text(14, "upper-roman", False) == "XIV"
    for text, line, message in (
        ("<!-- front -->\n\n# ก\n\n<!-- appendices -->\n\n# ข\n\n<!-- chapters -->\n", 9, "the regions go front, chapters, back, appendices, back"),
        ("<!-- back -->\n\n# ก\n\n<!-- back -->\n", 5, "a second <!-- back --> comes only after <!-- appendices -->"),
        ("<!-- appendices -->\n\n# ก\n\n<!-- back -->\n\n# ข\n\n<!-- back -->\n", 9, "given twice"),
    ):
        result, _ = build(tmp_path, text)
        assert result.get("line") == line and message in result["error"], result
    for bad, message in ((["--front-page-numbers", "thai"], "--front-page-numbers takes thai-letters, lower-roman, upper-roman, decimal"),
                         (["--appendix-numbers", "lower-letters"], "--appendix-numbers takes thai-letters, upper-letters, decimal, upper-roman")):
        with pytest.raises(b.BuildError, match=message):
            b.parse_args(bad + ["in.md", "out.docx"])


def test_comments_and_captions_meant_but_not_taken_are_warned_about_never_dropped_silently(tmp_path):
    shutil.copy(FIXTURES / "pixel.png", tmp_path / "p.png")
    text = (
        "<!-- chapter -->\n\n<!-- Chapters -->\n\n<!-- list of figures -->\n\n<!-- appendix -->\n\n"
        "<!-- todo -->\n\n<!-- note: ตรวจอีกครั้ง -->\n\n"  # ordinary comments stay quiet
        "- รายการ\n\n  <!-- toc -->\n\n"
        "![](p.png)\nFigure: ติดกัน\n\n"
        "| ก | ข |\n|---|---|\n| 1 | 2 |\nTable: ต่อท้าย\n"
    )
    result, out = build(tmp_path, text)
    doc = zipfile.ZipFile(out).read("word/document.xml").decode()
    assert result["ok"] and [w["message"] for w in result["warnings"]] == [
        "line 1: <!-- chapter --> is read as a comment; the comment that works is <!-- chapters -->",
        "line 3: <!-- Chapters --> is read as a comment; the comment that works is <!-- chapters -->",
        "line 5: <!-- list of figures --> is read as a comment; the comment that works is <!-- list-of-figures -->",
        "line 7: <!-- appendix --> is read as a comment; the comment that works is <!-- appendices -->",
        "line 15: <!-- toc --> works only at the top level, not inside a list, quotation or footnote; read as a comment",
        "line 17: 'Figure:' shares a paragraph with the image above it; leave a blank line between them to make a caption",
        "line 20: the table's last row starts with 'Table:'; a caption goes before the table, on its own line",
    ]
    assert len(_sections(doc)) == 1 and "TOC" not in doc and "Caption" not in doc, "warned about, and still read as written"


def test_without_region_comments_captions_count_through_the_document_and_nothing_else_changes(tmp_path):
    text = "Table: หนึ่ง\n\n| ก |\n|---|\n| 1 |\n\n# บท\n\nTable: **สอง** ต่อ\n\n| ก |\n|---|\n| 1 |\n"
    opts, _, _ = b.parse_args(["--thai-digits", "--table-label", "Table", "in.md", "out.docx"])
    result, out = build(tmp_path, text, **opts)
    doc = zipfile.ZipFile(out).read("word/document.xml").decode()
    parts = {n: zipfile.ZipFile(out).read(n) for n in zipfile.ZipFile(out).namelist()}
    assert result["ok"] and result["findings"] == [] and len(_sections(doc)) == 1 and "numId" not in doc
    assert [t for t in fi.docx_text(parts, 0) if t.startswith("Table")] == ["Table ๑ หนึ่ง", "Table ๒ สอง ต่อ"]
    assert ' SEQ Table \\* ThaiArabic ' in doc and "STYLEREF" not in doc
    # the goldens hold that a document with none of this keeps its bytes


def test_region_comments_and_captions_refuse_or_warn_with_their_line(tmp_path):
    for text, line, message in (
        ("<!-- chapters -->\n\n# ก\n\n<!-- front -->\n\n# ข\n", 5, "the regions go front, chapters, back"),
        ("<!-- back -->\n\n# ก\n\n<!-- back -->\n", 5, "given twice"),
    ):
        result, _ = build(tmp_path, text)
        assert result.get("line") == line and message in result["error"], result
    shutil.copy(FIXTURES / "pixel.png", tmp_path / "p.png")
    result, _ = build(tmp_path, "Table: ลอย\n\nข้อความ\n\n![](p.png) และข้อความ\n\nFigure: ลอย\n")
    assert result["ok"] and [w["message"] for w in result["warnings"]] == [
        "line 1: 'Table:' makes a caption only in the paragraph just before a table; kept as text",
        "line 7: 'Figure:' makes a caption only in the paragraph just after an image on its own; kept as text",
    ]
    for bad in (["--chapter-label", "บท%"], ["--figure-label", ""], ["--table-label", "x" * 41]):
        with pytest.raises(b.BuildError, match="takes text of 1 to 40 characters on one line, without %"):
            b.parse_args(bad + ["in.md", "out.docx"])


def test_heading_numbers_come_from_word_numbering_linked_to_the_heading_styles(tmp_path):
    text = "# บทนำ\n\n1. ข้อ\n2. ข้อ\n\n## ที่มา\n\n### ย่อย\n\n# บทที่สอง\n\n3. ต่อ\n"
    for flags, fmt in (([], None), (["--heading-numbers"], "decimal"), (["--heading-numbers", "--thai-digits"], "thaiNumbers")):
        opts, _, _ = b.parse_args(flags + ["in.md", "out.docx"])
        result, out = build(tmp_path, text, **opts)
        with zipfile.ZipFile(out) as zf:
            doc, styles, numbering = (zf.read(f"word/{n}.xml").decode() for n in ("document", "styles", "numbering"))
        assert result["ok"] and result["findings"] == [] and result["settings"]["heading_numbers"] is bool(fmt)
        assert "บทนำ" in doc and "1. บทนำ" not in doc, "the number is Word's, not text"
        if fmt is None:
            assert "numPr" not in styles and 'w:abstractNumId="2"' not in numbering
            continue
        # two ordered lists take numIds 2 and 3, so the headings' is 4
        for n in range(1, 7):
            own = styles.split(f'w:styleId="Heading{n}"', 1)[1].split("</w:style>", 1)[0]
            assert f'<w:pPr><w:keepNext/><w:keepLines/><w:numPr><w:ilvl w:val="{n - 1}"/><w:numId w:val="4"/></w:numPr><w:spacing' in own
        assert numbering.index('w:abstractNumId="2"><w:multiLevelType w:val="multilevel"/>') < numbering.index("<w:num ")
        assert numbering.endswith('<w:num w:numId="4"><w:abstractNumId w:val="2"/></w:num></w:numbering>')
        for level, lvl_text in ((0, "%1."), (1, "%1.%2"), (2, "%1.%2.%3"), (5, "%1.%2.%3.%4.%5.%6")):
            assert (f'<w:lvl w:ilvl="{level}"><w:start w:val="1"/><w:numFmt w:val="{fmt}"/><w:pStyle w:val="Heading{level + 1}"/>'
                    f'<w:suff w:val="space"/><w:lvlText w:val="{lvl_text}"/>') in numbering
    with pytest.raises(b.BuildError, match="takes no value"):
        b.parse_args(["--heading-numbers=1", "in.md", "out.docx"])


def _page_parts(out) -> dict[str, str]:
    with zipfile.ZipFile(out) as zf:
        return {n: zf.read(n).decode() for n in zf.namelist() if re.fullmatch(r"word/(header|footer)\d\.xml", n)}


def test_header_and_footer_text_share_their_place_with_the_page_number(tmp_path):
    centre = '<w:pPr><w:pStyle w:val="{}"/><w:jc w:val="center"/></w:pPr><w:r><w:rPr>' + wr.LANG + '</w:rPr><w:t xml:space="preserve">{}</w:t></w:r></w:p>'
    # text alone: one part, no number
    opts, _, _ = b.parse_args(["--header", "ลับ & <ด่วน>", "in.md", "out.docx"])
    result, out = build(tmp_path, "ก", **opts)
    parts = _page_parts(out)
    assert result["ok"] and result["findings"] == [] and result["settings"]["header"] == "ลับ & <ด่วน>"
    assert list(parts) == ["word/header1.xml"] and centre.format("Header", "ลับ &amp; &lt;ด่วน&gt;") in parts["word/header1.xml"]
    assert "PAGE" not in parts["word/header1.xml"]
    # header text, footer text and a footer number: the text comes first, then the number
    opts, _, _ = b.parse_args(["--header", "ลับ", "--footer", "สำนักงาน", "--page-numbers", "bottom-center", "in.md", "out.docx"])
    result, out = build(tmp_path, "ก", **opts)
    parts = _page_parts(out)
    with zipfile.ZipFile(out) as zf:
        doc, styles = zf.read("word/document.xml").decode(), zf.read("word/styles.xml").decode()
    assert result["ok"] and list(parts) == ["word/header1.xml", "word/footer1.xml"]
    footer = parts["word/footer1.xml"]
    assert footer.index(centre.format("Footer", "สำนักงาน")) < footer.index(" PAGE ")
    assert '<w:sectPr><w:headerReference w:type="default" r:id="rId1"/><w:footerReference w:type="default" r:id="rId2"/><w:pgSz' in doc
    assert 'w:styleId="Header"' in styles and 'w:styleId="Footer"' in styles
    # a first page without its number keeps the text; the other place gets an empty first part
    opts, _, _ = b.parse_args(["--footer", "สำนักงาน", "--page-numbers", "top-center", "--no-page-number-first", "in.md", "out.docx"])
    result, out = build(tmp_path, "ก", **opts)
    parts = _page_parts(out)
    assert result["ok"] and sorted(parts) == ["word/footer1.xml", "word/footer2.xml", "word/header1.xml", "word/header2.xml"]
    assert " PAGE " in parts["word/header1.xml"] and parts["word/header2.xml"].endswith('<w:p><w:pPr><w:pStyle w:val="Header"/></w:pPr></w:p></w:hdr>')
    assert parts["word/footer1.xml"] == parts["word/footer2.xml"] and centre.format("Footer", "สำนักงาน") in parts["word/footer2.xml"]
    for bad in (["--header", ""], ["--footer", "ก\tข"], ["--header", "x" * 201], ["--footer", "a​b"]):
        with pytest.raises(b.BuildError, match="takes text of 1 to 200 characters on one line"):
            b.parse_args(bad + ["in.md", "out.docx"])


def test_first_page_can_go_without_its_number(tmp_path):
    for position, kind, tag in (("top-center", "header", "hdr"), ("bottom-center", "footer", "ftr")):
        opts, _, _ = b.parse_args(["--page-numbers", position, "--no-page-number-first", "in.md", "out.docx"])
        result, out = build(tmp_path, "ก", **opts)
        with zipfile.ZipFile(out) as zf:
            doc, types, rels = (zf.read(n).decode() for n in ("word/document.xml", "[Content_Types].xml", "word/_rels/document.xml.rels"))
            numbered, first = zf.read(f"word/{kind}1.xml").decode(), zf.read(f"word/{kind}2.xml").decode()
        assert result["ok"] and result["findings"] == [] and result["settings"]["page_number_on_first"] is False
        sect = doc[doc.index("<w:sectPr>"):doc.index("</w:sectPr>") + len("</w:sectPr>")]
        assert sect.startswith(f'<w:sectPr><w:{kind}Reference w:type="default" r:id="rId1"/><w:{kind}Reference w:type="first" r:id="rId2"/>')
        assert sect.endswith("<w:titlePg/></w:sectPr>")
        assert f'Id="rId2" Type="{wr.REL}{kind}" Target="{kind}2.xml"' in rels and f'PartName="/word/{kind}2.xml"' in types
        assert " PAGE " in numbered and "PAGE" not in first and first.endswith(f"<w:p><w:pPr><w:pStyle w:val=\"{kind.capitalize()}\"/></w:pPr></w:p></w:{tag}>")
    # without the flag, one part and no title page — the goldens keep their bytes
    opts, _, _ = b.parse_args(["--page-numbers", "in.md", "out.docx"])
    _, out = build(tmp_path, "ก", **opts)
    with zipfile.ZipFile(out) as zf:
        assert "word/header2.xml" not in zf.namelist() and "titlePg" not in zf.read("word/document.xml").decode()
    for bad in (["--no-page-number-first"], ["--no-page-number-first=yes", "--page-numbers"]):
        with pytest.raises(b.BuildError, match="needs --page-numbers|takes no value"):
            b.parse_args(bad + ["in.md", "out.docx"])


def test_landscape_turns_the_paper_and_widens_the_text(tmp_path):
    table = "| ก | ข |\n|---|---|\n| 1 | 2 |\n"
    for flags, (w, h) in (([], (11906, 16838)), (["--landscape"], (16838, 11906)), (["--landscape", "--paper", "letter"], (15840, 12240)),
                              (["--paper", "f14"], (12240, 18720)), (["--landscape", "--paper=f14"], (18720, 12240))):
        opts, _, _ = b.parse_args(flags + ["in.md", "out.docx"])
        result, out = build(tmp_path, table, **opts)
        doc = zipfile.ZipFile(out).read("word/document.xml").decode()
        orient = ' w:orient="landscape"' if opts["landscape"] else ""
        assert result["ok"] and result["settings"]["landscape"] is opts["landscape"]
        assert f'<w:pgSz w:w="{w}" w:h="{h}"{orient}/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="2160"' in doc
        assert f'<w:gridCol w:w="{(w - 1440 - 2160) // 2}"/>' in doc, "tables take the text width of the turned page"
    # the margins that fit a portrait page may not fit a landscape one, and the refusal says so
    b.parse_args(["--margins", "1,1,6.5,1", "in.md", "out.docx"])
    with pytest.raises(b.BuildError, match="less than one inch"):
        b.parse_args(["--landscape", "--margins", "1,1,6.5,1", "in.md", "out.docx"])
    with pytest.raises(b.BuildError, match="takes no value"):
        b.parse_args(["--landscape=yes", "in.md", "out.docx"])


def test_styles_word_applies_itself_carry_the_document_font_and_size(tmp_path):
    """Word applies TOC 1-3 and Header or Footer on its own; a file without them gets Word's
    template definitions, which showed a TOC and a page number in Angsana New 20 pt."""
    font = '<w:rFonts w:ascii="Sarabun" w:hAnsi="Sarabun" w:cs="Sarabun" w:eastAsia="Sarabun"/><w:sz w:val="28"/><w:szCs w:val="28"/>'
    for flags, ids, part in (
        ([], [], None),
        (["--toc", "--page-numbers"], ["TOC1", "TOC2", "TOC3", "Header"], "header1"),
        (["--page-numbers", "bottom-center"], ["Footer"], "footer1"),
    ):
        opts, _, _ = b.parse_args(flags + ["--font", "Sarabun", "--size", "14", "in.md", "out.docx"])
        result, out = build(tmp_path, "# ก\n\nข", **opts)
        with zipfile.ZipFile(out) as zf:
            styles = zf.read("word/styles.xml").decode()
            numbered = zf.read(f"word/{part}.xml").decode() if part else ""
        assert result["ok"] and result["findings"] == []
        for style_id in ("TOC1", "TOC2", "TOC3", "Header", "Footer"):
            written = f'w:styleId="{style_id}"' in styles
            assert written is (style_id in ids), style_id
            if written:
                own = styles.split(f'w:styleId="{style_id}"', 1)[1].split("</w:style>", 1)[0]
                assert font in own, style_id
        if part:
            assert f'<w:pPr><w:pStyle w:val="{ids[-1]}"/><w:jc ' in numbered


def test_the_chapter_title_can_start_its_own_line(tmp_path):
    """--chapter-title-on-new-line: the number Word writes keeps the first line, the title
    starts the next, in the chapters and the appendices; the list still holds one line."""
    text = ("<!-- chapters -->\n\n# บทนำ\n\n## ที่มา\n\nเนื้อหา\n\n"
            "<!-- appendices -->\n\n# แบบสอบถาม\n\nเนื้อหา\n\n<!-- toc -->\n")
    result, out = build(tmp_path, text, chapter_title_on_new_line=True)
    kept = out.read_bytes()
    with zipfile.ZipFile(io.BytesIO(kept)) as zf:
        doc = zf.read("word/document.xml").decode()
        parts = {n: zf.read(n) for n in zf.namelist()}
    assert result["ok"] and result["findings"] == [] and result["warnings"] == []
    breaks = "<w:r><w:rPr>" + wr.LANG + "</w:rPr><w:br/></w:r>"
    assert doc.count(breaks) == 2, "the chapter and the appendix, not the ## heading"
    text_of = fi.docx_text(parts, 0)
    assert "\nบทนำ" in text_of and "\nแบบสอบถาม" in text_of and "ที่มา" in text_of
    assert "บทที่ 1 บทนำ" in text_of, "the list entry is still one line"
    assert result["counts"]["headings"] == 3, "a heading moved to its own line is still a heading"
    build(tmp_path, text)  # the same document without the flag
    with zipfile.ZipFile(out) as zf:
        assert breaks not in zf.read("word/document.xml").decode(), "off by default"
    # a document with no regions has no chapter number to move: the flag says so
    alone, _ = build(tmp_path, "# หัวข้อ\n\nเนื้อหา\n", chapter_title_on_new_line=True)
    assert [w["code"] for w in alone["warnings"]] == ["settings"]
    assert "changed nothing" in alone["warnings"][0]["message"]
    assert result["warnings"] == [], "with regions it does change something"


def test_a_heading_over_two_lines_reads_as_one_in_the_list(tmp_path):
    """A chapter heading may hold a line break — "บทที่ 1" above its title, as a thesis
    sets it — and the list of contents still holds one line (ADR 0027)."""
    text = "<!-- chapters -->\n\nบทนำ\\\nเรื่องทั่วไป\n===\n\nเนื้อหา\n\n<!-- toc -->\n"
    result, out = build(tmp_path, text, toc=True)
    with zipfile.ZipFile(out) as zf:
        doc = zf.read("word/document.xml").decode()
        parts = {n: zf.read(n) for n in zf.namelist()}
    assert result["ok"] and result["findings"] == []
    assert "<w:br/>" in doc, "the heading itself keeps the break"
    assert "บทที่ 1 บทนำ เรื่องทั่วไป" in fi.docx_text(parts, 0), "the entry is one line"
    assert "บทที่ 1 บทนำ\nเรื่องทั่วไป" not in doc


def test_thai_distributed_leaves_a_paragraph_without_thai_alone(tmp_path):
    """--align thai fills a line by spreading what is on it, as Thai is set; a paragraph with
    no Thai in it — an English reference, a Latin caption, a list entry — keeps the ordinary
    left alignment, so "(2024a)" does not come out as "( 2 0 2 4 a)" (ADR 0027)."""
    text = ("ข้อความไทยในย่อหน้านี้\n\nBennett, G., & Hall, T. (2024a). Static analysis tools.\n\n"
            "- English list item\n- รายการภาษาไทย\n\nTable: English caption\n\n| a | b |\n|---|---:|\n| 1 | 2 |\n")
    # a Thai label makes every caption Thai; a Latin one leaves a caption, and the entry a
    # list writes for it, with no Thai at all
    latin = "# Introduction\n\n<!-- list-of-tables -->\n\n"
    for flags, source, latin_lines in ((["--align", "thai"], text, 4), (["--align", "thai", "--table-label", "Table", "--toc"], latin + text, 8)):
        opts, _, _ = b.parse_args(flags + ["in.md", "out.docx"])
        result, out = build(tmp_path, source, **opts)
        with zipfile.ZipFile(out) as zf:
            doc = zf.read("word/document.xml").decode()
            styles = zf.read("word/styles.xml").decode()
        assert result["ok"] and result["findings"] == []
        assert 'w:val="thaiDistribute"' in styles, "the document's own alignment is unchanged"
        said = [(re.findall(r'w:jc w:val="(\w+)"', p), "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)))
                for p in re.findall(r"<w:p>.*?</w:p>", doc, re.S)]
        for jc, said_text in said:
            if not said_text:
                continue
            has_thai = lo.has_thai(said_text)
            assert (jc == []) is has_thai, (jc, said_text[:40])
            assert len(jc) <= 1, "a paragraph that sets its own alignment keeps it: " + said_text[:40]
        # the reference, a list item, two left table cells (the right column keeps its own) — and with Latin labels the caption, the heading and an entry for each
        assert sum(1 for jc, t in said if t and jc == ["left"]) == latin_lines, flags
    # left alignment is untouched by the rule
    plain, out2 = build(tmp_path, text)
    with zipfile.ZipFile(out2) as zf:
        assert 'w:jc w:val="left"' not in zf.read("word/document.xml").decode()


def test_thai_distributed_leaves_a_line_ending_in_a_manual_break_unspread(tmp_path):
    """A hard break in a Thai distributed paragraph: Word spread the line before it letter by
    letter across the page ("ภ า ษ า ไ ท ย", Word for macOS, 2026-09-17). With --align thai
    the document says not to expand a line that ends with SHIFT+RETURN; left alignment has
    nothing to spread and writes nothing."""
    text = "ข้อความภาษาไทยที่ขึ้นบรรทัดใหม่  \nด้วย hard break\n"
    for flags, written in ((["--align", "thai"], True), ([], False)):
        opts, _, _ = b.parse_args(flags + ["in.md", "out.docx"])
        result, out = build(tmp_path, text, **opts)
        with zipfile.ZipFile(out) as zf:
            settings, doc = zf.read("word/settings.xml").decode(), zf.read("word/document.xml").decode()
        assert result["ok"] and result["findings"] == [] and "<w:br/>" in doc
        assert ("<w:compat><w:doNotExpandShiftReturn/><w:compatSetting " in settings) is written, flags


def test_every_generated_run_names_the_font(tmp_path):
    """A numbering level, and the hyperlink style a rebuilt list writes its entries in, are
    drawn in the application's own default when they name no font: WPS showed "บทที่ ๑" as
    Latin letters, and a table of contents it rebuilt changed font (ADR 0027)."""
    opts, _, _ = b.parse_args(["--font", "Sarabun", "--heading-numbers", "--thai-digits", "--toc",
                               "in.md", "out.docx"])
    text = "<!-- chapters -->\n\n# บทนำ\n\n## ที่มา\n\n1. หนึ่ง\n\n- จุด\n\n<!-- appendices -->\n\n# แบบสอบถาม\n"
    result, out = build(tmp_path, text, **opts)
    with zipfile.ZipFile(out) as zf:
        numbering, styles = zf.read("word/numbering.xml").decode(), zf.read("word/styles.xml").decode()
    assert result["ok"] and result["findings"] == []
    font = '<w:rFonts w:ascii="Sarabun" w:hAnsi="Sarabun" w:cs="Sarabun"/>'
    # the font, the size, and the complex-script flag: without <w:cs/> WPS draws Thai in the
    # level's Latin font, which is where "บทที่ ๑" came out as Latin letters
    rpr = "<w:rPr>" + font + '<w:sz w:val="32"/><w:szCs w:val="32"/>' + wr.LANG + "</w:rPr>"
    levels = numbering.count("<w:lvl ")
    assert levels == 4 * 9 and numbering.count(rpr + "</w:lvl>") == levels, "every level"
    link = styles.split('w:styleId="Hyperlink"', 1)[1].split("</w:style>", 1)[0]
    assert font in link, "the entries a rebuilt list writes are hyperlink runs"
    normal = styles.split('w:styleId="Normal"', 1)[1].split("</w:style>", 1)[0]
    assert font.replace("/>", ' w:eastAsia="Sarabun"/>') in normal and "<w:sz " in normal, \
        "Normal repeats the defaults for an application that reads styles but not w:docDefaults"


def test_thai_digits_format_the_numbers_word_generates_and_never_the_text(tmp_path):
    text = "# หัวข้อ 1\n\nปี 2567 ข้อ 12[^1]\n\n1. หนึ่ง\n2. สอง\n\n[^1]: หมายเหตุ 3\n"
    for flags, thai in (([], False), (["--thai-digits"], True)):
        opts, _, _ = b.parse_args(flags + ["--page-numbers", "--toc", "in.md", "out.docx"])
        result, out = build(tmp_path, text, **opts)
        assert result["ok"] and result["findings"] == [] and result["settings"]["thai_digits"] is thai
        with zipfile.ZipFile(out) as zf:
            doc, numbering, settings, header = (zf.read(f"word/{n}.xml").decode() for n in ("document", "numbering", "settings", "header1"))
        sect = doc[doc.index("<w:sectPr>"):]
        assert ('<w:pgNumType w:fmt="thaiNumbers"/></w:sectPr>' in sect) is thai, "page numbers, in the header and the table of contents"
        assert ('<w:footnotePr><w:numFmt w:val="thaiNumbers"/></w:footnotePr><w:pgSz' in sect) is thai
        assert ('<w:footnotePr><w:numFmt w:val="thaiNumbers"/><w:footnote w:id="-1"/>' in settings) is thai
        assert numbering.count('w:numFmt w:val="thaiNumbers"') == (9 if thai else 0) and numbering.count('w:numFmt w:val="bullet"') == 9
        assert " PAGE " in header and "2567" in doc and "12" in doc and "๒" not in doc, "the text keeps its own digits"
    _, out = build(tmp_path, "ก", thai_digits=True)
    assert "footnotePr" not in zipfile.ZipFile(out).read("word/document.xml").decode(), "no footnotes, no footnote format"


def test_line_spacing_sets_body_spacing_and_leaves_code_and_footnotes_single(tmp_path):
    text = "ก[^1]\n\n```\ncode\n```\n\n[^1]: ข\n"
    for flags, line in (([], "240"), (["--line-spacing", "1.5"], "360"), (["--line-spacing=2"], "480"), (["--line-spacing", "1.15"], "276")):
        opts, _, _ = b.parse_args(flags + ["in.md", "out.docx"])
        result, out = build(tmp_path, text, **opts)
        styles = zipfile.ZipFile(out).read("word/styles.xml").decode()
        assert result["ok"] and result["settings"]["line_spacing"] == opts["line_spacing"]
        assert '<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="' + line + '" w:lineRule="auto"/>' in styles
        single = 3 if line == "240" else 2  # the document itself, when it is single, and always CodeBlock and FootnoteText
        assert styles.count('w:line="240"') == single, "Code Block and footnote text stay single"
    for bad in (["--line-spacing", "0.9"], ["--line-spacing", "3.5"], ["--line-spacing", "1,5"], ["--line-spacing"]):
        with pytest.raises(b.BuildError, match="line-spacing"):
            b.parse_args(bad + ["in.md", "out.docx"])


def test_unknown_font_is_a_warning_and_still_builds(tmp_path):
    result, out = build(tmp_path, "ก", font="Papyrus")
    assert result["ok"] and [x["code"] for x in result["warnings"]] == ["font"]


# --- the command as the agent runs it (ADR 0007) ---


def test_cli_exit_codes(tmp_path):
    src = tmp_path / "in.md"
    src.write_text("ก <span>x</span>", encoding="utf-8")
    code, result = run_cli(src, tmp_path / "o.docx")
    assert code == 2 and result["line"] == 1 and "not supported" in result["error"]
    code, result = run_cli(src, tmp_path / "o.docx", "--margins", "1,2")
    assert code == 2 and "four" in result["error"]
    src.write_text("ข้อความทดสอบ", encoding="utf-8")
    code, result = run_cli(src, tmp_path / "o.docx")
    assert code == 0 and result["ok"] and (tmp_path / "o.docx").exists()
    assert "ข้อความทดสอบ" not in json.dumps(result, ensure_ascii=False)
    assert check(tmp_path / "o.docx").ok
