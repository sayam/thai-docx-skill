# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""A minimal, correct WordprocessingML package for the checker's tests.

`good()` returns the parts of a document that carries none of the five causes of
ADR 0004; a test plants one violation by string replacement and expects the
checker to name it. `pack()` zips parts with a fixed timestamp, so a fixture is
the same bytes on every run.
"""

from __future__ import annotations

import io
import zipfile

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'

RUN_PROPS = '<w:cs/><w:lang w:val="en-US" w:bidi="th-TH"/>'
BOLD_PROPS = '<w:b/><w:bCs/><w:cs/><w:lang w:val="en-US" w:bidi="th-TH"/>'


def run(text: str, props: str = RUN_PROPS) -> str:
    return f'<w:r><w:rPr>{props}</w:rPr><w:t xml:space="preserve">{text}</w:t></w:r>'


def good() -> dict[str, str]:
    return {
        "[Content_Types].xml": XML
        + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
        '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
        "</Types>",
        "_rels/.rels": XML
        + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"'
        ' Target="word/document.xml"/>'
        "</Relationships>",
        "word/_rels/document.xml.rels": XML
        + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>'
        "</Relationships>",
        "word/document.xml": XML
        + f"<w:document {W}><w:body>"
        '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>' + run("หัวข้อทดสอบ") + "</w:p>"
        "<w:p>" + run("ข้อความทดสอบ ") + run("ตัวหนา", BOLD_PROPS) + run(" ท้ายประโยค") + "</w:p>"
        '<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr>' + run("รายการ") + "</w:p>"
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="2160" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>'
        "</w:body></w:document>",
        "word/styles.xml": XML
        + f"<w:styles {W}><w:docDefaults><w:rPrDefault><w:rPr>"
        '<w:rFonts w:ascii="TH Sarabun New" w:hAnsi="TH Sarabun New" w:cs="TH Sarabun New" w:eastAsia="TH Sarabun New"/>'
        '<w:sz w:val="32"/><w:szCs w:val="32"/><w:cs/><w:lang w:val="en-US" w:eastAsia="en-US" w:bidi="th-TH"/>'
        "</w:rPr></w:rPrDefault></w:docDefaults>"
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>'
        '<w:pPr><w:keepNext/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:bCs/><w:sz w:val="40"/><w:szCs w:val="40"/></w:rPr></w:style>'
        "</w:styles>",
        "word/settings.xml": XML
        + f"<w:settings {W}><w:compat>"
        '<w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>'
        "</w:compat></w:settings>",
        "word/numbering.xml": XML
        + f'<w:numbering {W}><w:abstractNum w:abstractNumId="0"><w:lvl w:ilvl="0">'
        '<w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>'
        '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>'
        '<w:rPr><w:rFonts w:ascii="TH Sarabun New" w:hAnsi="TH Sarabun New" w:cs="TH Sarabun New"/></w:rPr>'
        '</w:lvl></w:abstractNum><w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num></w:numbering>',
    }


def pack(parts: dict[str, str | bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in parts.items():
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, data.encode("utf-8") if isinstance(data, str) else data)
    return buf.getvalue()


def replaced(parts: dict[str, str], part: str, old: str, new: str, count: int = 1) -> dict[str, str]:
    """`parts` with `old` swapped for `new` in one part — and proof the swap happened.

    `count` is `str.replace`'s: one occurrence by default, -1 for every one."""
    assert old in parts[part], f"{old!r} is not in {part}; the mutation would be a no-op"
    out = dict(parts)
    out[part] = parts[part].replace(old, new, count)
    return out
