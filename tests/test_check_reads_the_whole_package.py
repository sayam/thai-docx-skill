# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""What `check` reads, read whole — and what `repair` then puts right.

The review of 0.2.0 found the checker answering `ok` on files it had not read: a Strict package
read as an empty one, an "off" read as "on", a header found by its file name and missed under
another, properties it never looked at — a numbering level's twins, a paragraph mark's, a
deleted run's text, the order of a section's, a table's, a level's. Each case runs both command
lines (ADR 0008) on one planted file: the finding is there, and a repair takes it away.
"""

from __future__ import annotations

import zipfile

from docx_fixture import RUN_PROPS, good, pack, replaced
from test_what_a_command_takes import _node, both  # noqa: F401  the fixture runs here too

STRICT_W = "http://purl.oclc.org/ooxml/wordprocessingml/main"
TRANSITIONAL_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
RELS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
DATE = 'w:author="a" w:date="2026-01-01T00:00:00Z"'


def checked(tmp_path, parts) -> tuple[int, dict]:
    (tmp_path / "in.docx").write_bytes(pack(parts))
    return both(["check", "in.docx"], tmp_path)


def repaired(tmp_path, parts) -> dict:
    """What the repair of `parts` put right, which must leave nothing its checker finds. The
    marker it takes out of the fixture's docDefaults (ADR 0039) is every case's, and set aside."""
    (tmp_path / "in.docx").write_bytes(pack(parts))
    code, result = both(["repair", "in.docx", "out.docx"], tmp_path)
    assert code == 0 and result["ok"] and result["remaining"] == [], result
    assert both(["check", "out.docx"], tmp_path)[1]["findings"] == []
    return {code: n for code, n in result["repaired"].items() if code != "unmarked"}


def codes(result: dict) -> list[tuple[str, str]]:
    return [(f["code"], f["part"]) for f in result["findings"]]


def test_a_strict_package_is_refused_not_read_as_empty(tmp_path):
    parts = {name: (data.replace(TRANSITIONAL_W, STRICT_W) if name.startswith("word/") else data)
             for name, data in good().items()}
    parts["_rels/.rels"] = parts["_rels/.rels"].replace(
        RELS + "officeDocument", "http://purl.oclc.org/ooxml/officeDocument/relationships/officeDocument")
    code, result = checked(tmp_path, parts)
    assert code == 2 and codes(result) == [("package", "word/document.xml")], result
    assert "Strict" in result["findings"][0]["message"]


def test_an_off_switch_is_read_as_off(tmp_path):
    off = replaced(good(), "word/document.xml", "<w:cs/>", '<w:cs w:val="0"/>')
    code, result = checked(tmp_path, off)
    assert code == 1 and codes(result) == [("2", "word/document.xml")], result
    assert repaired(tmp_path, off) == {"2": 1}
    for spelling in ('w:val="0"', 'w:val="false"', 'w:val="off"'):
        proofing = replaced(good(), "word/document.xml", "<w:cs/>", f"<w:noProof {spelling}/><w:cs/>")
        code, result = checked(tmp_path, proofing)
        assert code == 0 and result["findings"] == [], (spelling, result)


def test_a_part_is_found_by_its_relationship_not_its_name(tmp_path):
    parts = good()
    parts["word/_rels/document.xml.rels"] = parts["word/_rels/document.xml.rels"].replace(
        "</Relationships>", f'<Relationship Id="rId9" Type="{RELS}header" Target="headerFirst.xml"/></Relationships>')
    parts["word/headerFirst.xml"] = (f'<w:hdr xmlns:w="{TRANSITIONAL_W}"><w:p><w:r><w:t>หัวกระดาษ</w:t></w:r></w:p></w:hdr>')
    code, result = checked(tmp_path, parts)
    assert code == 1 and codes(result) == [("2", "word/headerFirst.xml")], result
    assert repaired(tmp_path, parts) == {"2": 1}

    renamed = {("word/Document2.xml" if n == "word/document.xml" else
                "word/_rels/Document2.xml.rels" if n == "word/_rels/document.xml.rels" else n): d
               for n, d in good().items()}
    renamed["_rels/.rels"] = renamed["_rels/.rels"].replace('Target="word/document.xml"', 'Target="/word/Document2.xml"')
    code, result = checked(tmp_path, renamed)
    assert code == 0 and result["counts"]["paragraphs"] == 3, result


def test_a_numbering_level_has_its_twins_checked(tmp_path):
    level = replaced(good(), "word/numbering.xml", 'w:cs="TH Sarabun New"/></w:rPr>',
                     'w:cs="TH Sarabun New"/><w:sz w:val="32"/></w:rPr>')
    code, result = checked(tmp_path, level)
    assert code == 1 and codes(result) == [("5", "word/numbering.xml")], result
    assert repaired(tmp_path, level) == {"5": 1}


def test_formatting_a_revision_replaced_is_not_a_finding(tmp_path):
    history = replaced(good(), "word/styles.xml", '<w:szCs w:val="40"/></w:rPr></w:style>',
                       f'<w:szCs w:val="40"/><w:rPrChange w:id="1" {DATE}><w:rPr><w:b/></w:rPr></w:rPrChange>'
                       "</w:rPr></w:style>")
    code, result = checked(tmp_path, history)
    assert code == 0 and result["findings"] == [], result


def test_a_paragraph_marks_properties_are_checked(tmp_path):
    mark = replaced(good(), "word/document.xml", '<w:pStyle w:val="Heading1"/></w:pPr>',
                    '<w:pStyle w:val="Heading1"/><w:rPr><w:b/></w:rPr></w:pPr>')
    code, result = checked(tmp_path, mark)
    assert code == 1 and codes(result) == [("5", "word/document.xml")], result
    assert repaired(tmp_path, mark) == {"5": 1}
    backwards = replaced(good(), "word/document.xml", '<w:pStyle w:val="Heading1"/></w:pPr>',
                         '<w:pStyle w:val="Heading1"/><w:rPr><w:cs/><w:b/><w:bCs/></w:rPr></w:pPr>')
    code, result = checked(tmp_path, backwards)
    assert code == 1 and codes(result) == [("order", "word/document.xml")], result
    assert repaired(tmp_path, backwards) == {"order": 1}


def test_deleted_text_is_text(tmp_path):
    deleted = replaced(good(), "word/document.xml", "<w:sectPr>",
                       f'<w:p><w:del w:id="2" {DATE}><w:r><w:delText>ข้อความที่ลบ</w:delText></w:r></w:del></w:p><w:sectPr>')
    code, result = checked(tmp_path, deleted)
    assert code == 1 and codes(result) == [("2", "word/document.xml")], result
    assert result["counts"]["runs"] == 6
    assert repaired(tmp_path, deleted) == {"2": 1}
    with zipfile.ZipFile(tmp_path / "out.docx") as z:
        assert "<w:r><w:rPr><w:cs/></w:rPr><w:delText>ข้อความที่ลบ</w:delText></w:r>" in z.read("word/document.xml").decode()


def test_the_order_of_every_property_list_is_checked(tmp_path):
    table = ("<w:tbl><w:tblPr><w:tblBorders/><w:tblW w:w=\"0\" w:type=\"auto\"/></w:tblPr><w:tblGrid><w:gridCol/></w:tblGrid>"
             "<w:tr><w:trPr><w:tblHeader/><w:cantSplit/><w:del w:id=\"3\" " + DATE + "/><w:jc w:val=\"center\"/></w:trPr>"
             "<w:tc><w:tcPr><w:vAlign w:val=\"top\"/><w:tcW w:w=\"0\" w:type=\"auto\"/></w:tcPr>"
             "<w:p>" + f'<w:r><w:rPr>{RUN_PROPS}</w:rPr><w:t>ช่อง</w:t></w:r>' + "</w:p></w:tc></w:tr></w:tbl>")
    planted = {
        "w:sectPr": replaced(good(), "word/document.xml", '<w:pgSz w:w="11906" w:h="16838"/><w:pgMar',
                             '<w:titlePg/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar'),
        "w:tblPr": replaced(good(), "word/document.xml", "<w:sectPr>", table + "<w:sectPr>"),
        "w:lvl": replaced(good(), "word/numbering.xml", '<w:start w:val="1"/><w:numFmt w:val="bullet"/>',
                          '<w:numFmt w:val="bullet"/><w:start w:val="1"/>'),
        "w:style": replaced(good(), "word/styles.xml", '<w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>',
                            '<w:basedOn w:val="Normal"/><w:name w:val="heading 1"/>'),
    }
    for element, parts in planted.items():
        code, result = checked(tmp_path, parts)
        found = [f["message"] for f in result["findings"]]
        assert code == 1 and {f["code"] for f in result["findings"]} == {"order"}, (element, result)
        assert any(message.startswith("in " + element) or element in message for message in found), (element, found)
        assert repaired(tmp_path, parts).keys() == {"order"}, element
    # the three that a table holds are each read, not only the first
    code, result = checked(tmp_path, planted["w:tblPr"])
    assert len(result["findings"]) == 3 and ["in w:tblPr" in m or "in w:trPr" in m or "in w:tcPr" in m
                                             for m in (f["message"] for f in result["findings"])] == [True] * 3, result
