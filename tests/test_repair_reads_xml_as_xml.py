# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""repair reads a part as XML is written, and answers for the file it writes (ADR 0037, 0039).

repair edits bytes, not a tree, so that nothing it was not asked to change is changed. That is
only safe while every pattern reads a tag the way XML writes one: a `>` inside a quoted value, a
value in single quotes, an empty `<w:r/>`, a run holding a tab, a prefix other than `w`, a
comment or a CDATA section, a picture whose bytes happen to spell a tag. And a cut run must say
`xml:space="preserve"`, or the space at the cut is not text any more. Each case below broke one
implementation or both in the review of 0.2.0; each runs through both command lines.

Then the guards: text compared in every part a reader sees, not only the body; a fault the
checker finds in the output that the input did not have writes nothing, and is this version's
fault (exit 1); and a repair that would change one character writes nothing — shown on planted
repairs, since a correct repair never reaches them.
"""

from __future__ import annotations

import io
import re
import time
import zipfile
from xml.etree import ElementTree as ET

import pytest

from docx_fixture import good, pack
from test_what_a_command_takes import _node, both  # noqa: F401  the fixture runs here too
from thai_docx import repair as rp
from thai_docx.check import check

W_URI = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{" + W_URI + "}"
BARE = '<w:r><w:t xml:space="preserve">ข้อความไทย</w:t></w:r>'  # finding 2: Thai without <w:cs/>


def body(tmp_path, runs: str, name: str = "in.docx", parts: dict | None = None):
    """A package whose first paragraph holds `runs`."""
    parts = parts or good()
    xml = parts["word/document.xml"]
    parts["word/document.xml"] = re.sub(r"<w:p>.*?</w:p>", lambda _m: "<w:p>" + runs + "</w:p>", xml, count=1, flags=re.S)
    (tmp_path / name).write_bytes(pack(parts))
    return tmp_path / name


def part(path, name: str) -> str:
    with zipfile.ZipFile(path) as z:
        return z.read(name).decode("utf-8")


def texts(path) -> list[str]:
    """Each w:t's text and each tab, paragraph by paragraph, across the body — read here, not by
    the code under test; a w:t without xml:space loses the space at its ends, as Word reads it."""
    root = ET.fromstring(part(path, "word/document.xml"))
    out = []
    for p in root.iter(W + "p"):
        pieces = []
        for el in p.iter():
            if el.tag == W + "t":
                keep = el.get("{http://www.w3.org/XML/1998/namespace}space") == "preserve"
                pieces.append((el.text or "") if keep else (el.text or "").strip(" \t\n\r"))
            elif el.tag == W + "tab":
                pieces.append("\t")
        out.append("".join(pieces))
    return out


# --- the text survives the cut -----------------------------------------------------------------


def test_a_cut_run_keeps_the_space_at_the_cut(tmp_path):
    """Word writes xml:space only where it needs it, so `ไทย English ไทย` comes without it. Cut
    at the script, `ไทย ` and `English ` end in a space that only xml:space keeps."""
    src = body(tmp_path, "<w:r><w:t>ไทย English ไทย</w:t></w:r>")
    code, result = both(["repair", "in.docx", "out.docx"], tmp_path)
    assert result["ok"] and result["repaired"].get("split") == 1, result
    for tag, text in re.findall(r"(<w:t(?:\s[^>]*)?>)([^<]*)</w:t>", part(tmp_path / "out.docx", "word/document.xml")):
        if text != text.strip():
            assert 'xml:space="preserve"' in tag, (tag, text)
    assert texts(tmp_path / "out.docx") == texts(src)


def test_a_run_with_a_tab_is_marked_whole_not_cut_through_its_markup(tmp_path):
    src = body(tmp_path, "<w:r><w:t>ไทย</w:t><w:tab/><w:t>English</w:t></w:r>")
    code, result = both(["repair", "in.docx", "out.docx"], tmp_path)
    assert result["ok"] and result["repaired"].get("2") == 1 and "split" not in result["repaired"], result
    assert texts(tmp_path / "out.docx") == texts(src) and "<w:tab/>" in part(tmp_path / "out.docx", "word/document.xml")


def test_an_invisible_character_inside_a_thai_word_is_not_a_place_to_cut(tmp_path):
    """The word stays one run: the character has no script of its own to be cut out for."""
    word = '<w:r><w:rPr><w:cs/></w:rPr><w:t xml:space="preserve">รายงาน\u200dการประชุม</w:t></w:r>'
    body(tmp_path, word)
    code, result = both(["repair", "in.docx", "out.docx"], tmp_path)
    assert "split" not in result.get("repaired", {}), result
    assert word in part(tmp_path / "out.docx", "word/document.xml")
    assert [f["code"] for f in result["remaining"]] == ["invisible"]


# --- a tag is read as XML writes it ------------------------------------------------------------


def test_a_greater_than_inside_an_attribute_is_not_the_end_of_the_tag(tmp_path):
    body(tmp_path, '<w:r w:rsidR="a>b"><w:t xml:space="preserve" w:x="c>d">ข้อความ</w:t></w:r>')
    code, result = both(["repair", "in.docx", "out.docx"], tmp_path)
    assert result["ok"] and result["repaired"].get("2") == 1, result
    assert check(str(tmp_path / "out.docx")).ok
    assert 'w:rsidR="a>b"' in part(tmp_path / "out.docx", "word/document.xml")


def test_an_empty_run_is_passed_over(tmp_path):
    body(tmp_path, "<w:r /><w:r/>" + BARE)
    code, result = both(["repair", "in.docx", "out.docx"], tmp_path)
    assert result["ok"] and result["repaired"].get("2") == 1, result


def test_a_single_quoted_size_gets_its_twin_with_the_same_value(tmp_path):
    body(tmp_path, "<w:r><w:rPr><w:sz w:val='40'/><w:cs/></w:rPr><w:t xml:space=\"preserve\">ไทย</w:t></w:r>")
    code, result = both(["repair", "in.docx", "out.docx"], tmp_path)
    assert result["ok"] and result["repaired"].get("5") == 1, result
    assert "<w:szCs w:val='40'/>" in part(tmp_path / "out.docx", "word/document.xml")


@pytest.mark.parametrize("declared", [
    ('xmlns:w="' + W_URI + '"', "xmlns:x=\"" + W_URI + "\""),                  # WordprocessingML under x:
    ('xmlns:w="' + W_URI + '"', 'xmlns:x="' + W_URI + '" xmlns:w="urn:other"'),  # w: bound elsewhere
])
def test_a_part_under_another_prefix_is_refused_not_half_repaired(tmp_path, declared):
    parts = good()
    was, now = declared
    xml = parts["word/document.xml"].replace(was, now, 1)
    if "urn:other" not in now:
        xml = re.sub(r"<(/?)w:", r"<\1x:", xml).replace(" w:", " x:")
    parts["word/document.xml"] = xml
    (tmp_path / "in.docx").write_bytes(pack(parts))
    code, result = both(["repair", "in.docx", "out.docx"], tmp_path)
    assert code == 2 and "under a prefix other than w:" in result["error"], result
    assert not (tmp_path / "out.docx").exists()


def test_a_part_holding_a_comment_or_cdata_is_left_as_it_came(tmp_path):
    """What reads like a tag and is not: the part is not edited around it, and says so."""
    parts = good()
    parts["word/header1.xml"] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:hdr xmlns:w="' + W_URI + '">'
        "<w:p><w:r><w:rPr><w:noProof/></w:rPr><w:t><![CDATA[a<b ]]></w:t></w:r></w:p><!-- <w:r> --></w:hdr>")
    parts["word/document.xml"] = parts["word/document.xml"].replace("<w:rPr>", "<w:rPr><w:noProof/>", 1)
    (tmp_path / "in.docx").write_bytes(pack(parts))
    header = part(tmp_path / "in.docx", "word/header1.xml")
    code, result = both(["repair", "in.docx", "out.docx"], tmp_path)
    assert result["ok"], result
    assert part(tmp_path / "out.docx", "word/header1.xml") == header
    assert "<w:noProof/>" not in part(tmp_path / "out.docx", "word/document.xml")
    assert any(w["code"] == "left" and w["message"].startswith("word/header1.xml") for w in result["warnings"])
    assert [(f["code"], f["part"]) for f in result["remaining"]] == [("3", "word/header1.xml")]


def test_a_picture_is_left_byte_for_byte_whatever_its_bytes_spell(tmp_path):
    """Only XML parts are edited: a picture that happens to hold `<w:noProof/>` is not one."""
    parts = good()
    parts["word/document.xml"] = parts["word/document.xml"].replace("<w:rPr>", "<w:rPr><w:noProof/>", 1)
    picture = b"\x89PNG\r\n\x1a\n\xff\xfe<w:noProof/>\x00\x01"
    buf = io.BytesIO(pack(parts))
    with zipfile.ZipFile(buf, "a") as z:
        z.writestr("word/media/image1.png", picture)
    (tmp_path / "in.docx").write_bytes(buf.getvalue())
    code, result = both(["repair", "in.docx", "out.docx"], tmp_path)
    assert result["ok"] and result["repaired"].get("3") == 1, result
    with zipfile.ZipFile(tmp_path / "out.docx") as z:
        assert z.read("word/media/image1.png") == picture


def test_putting_properties_in_order_takes_time_in_proportion_to_the_part(tmp_path):
    """Once the whole part was copied at every element put right: twenty seconds for nine
    kilobytes, and far longer for a real document."""
    runs = '<w:r><w:rPr><w:lang w:val="en-US"/><w:cs/></w:rPr><w:t xml:space="preserve">ไทย</w:t></w:r>' * 20000
    body(tmp_path, runs)
    began = time.monotonic()
    code, result = both(["repair", "in.docx", "out.docx"], tmp_path)
    assert result["ok"] and result["repaired"].get("order") == 20000, result
    assert time.monotonic() - began < 30


# --- the guards, shown on planted repairs --------------------------------------------------------


def test_a_repair_that_changes_a_character_writes_nothing(tmp_path, monkeypatch):
    """No correct repair reaches this guard, so a wrong one is planted: the split drops the last
    character of every piece it writes."""
    src = body(tmp_path, "<w:r><w:t>ไทย English ไทย</w:t></w:r>")
    real = rp._escape
    monkeypatch.setattr(rp, "_escape", lambda text: real(text.decode("utf-8")[:-1].encode("utf-8")))
    result = rp.repair(str(src), str(tmp_path / "out.docx"))
    assert result["error"] == "the repair would have changed the document's text; nothing was written"
    assert not (tmp_path / "out.docx").exists()


def test_the_text_of_a_header_is_compared_too(tmp_path, monkeypatch):
    parts = good()
    parts["word/header1.xml"] = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:hdr xmlns:w="' + W_URI
                                 + '"><w:p>' + BARE + "</w:p></w:hdr>")
    (tmp_path / "in.docx").write_bytes(pack(parts))
    real = rp.fix_text_part

    def dropping(xml, *args, **kwargs):
        out, counts = real(xml, *args, **kwargs)
        return (out.replace("ข้อความไทย".encode(), "ข้อความ".encode()) if b"<w:hdr" in xml else out), counts

    monkeypatch.setattr(rp, "fix_text_part", dropping)
    result = rp.repair(str(tmp_path / "in.docx"), str(tmp_path / "out.docx"))
    assert result["error"] == "the repair would have changed the document's text; nothing was written"


def test_a_repair_that_breaks_the_package_writes_nothing_and_is_this_versions_fault(tmp_path, monkeypatch, capsys):
    src = body(tmp_path, BARE)
    real = rp.fix_text_part
    monkeypatch.setattr(rp, "fix_text_part", lambda xml, *a, **k: (real(xml, *a, **k)[0] + b"<w:r>", {"2": 1}))
    assert rp.main([str(src), str(tmp_path / "out.docx")]) == 1
    assert capsys.readouterr().out.count(rp.MADE_WORSE) == 1 and not (tmp_path / "out.docx").exists()
