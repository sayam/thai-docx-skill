"""`thai_docx build IN.md OUT.docx [flags]` — Markdown to a .docx that passes
`thai_docx check`, with the content unchanged (ADR 0005) and the same bytes on
every run (ADR 0008).

The output is written only when the package passes the checker and the fidelity
check; otherwise nothing is written and the JSON line says why. Standard library
only; reads the Markdown file and the images it names, writes one file (ADR 0011).

Byte stability: zip entries are *stored*, not deflated — deflate output differs
between zlib builds, and the JavaScript port has to produce the same bytes. No
clock, host name or user name enters any part.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import re
import struct
import unicodedata
import zipfile
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

from . import check as check_mod
from . import markdown as md
from .ooxml import W, w

PAPER = {"a4": (11906, 16838), "letter": (12240, 15840)}
DEFAULTS = {
    "font": "TH Sarabun New",
    "size": 16,
    "paper": "a4",
    "margins": (1.0, 1.0, 1.0, 1.5),  # top, right, bottom, left — inches
    "align": "left",
    "toc": False,
    "page_numbers": False,
    "hide_spelling_errors": False,
}
CODE_FONT = "Consolas"
SYMBOL_FONT = "Segoe UI Symbol"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
EMU_PER_PX = 9525  # at 96 dpi
EMU_PER_TWIP = 635
LANG = '<w:cs/><w:lang w:val="en-US" w:bidi="th-TH"/>'


class BuildError(Exception):
    def __init__(self, what: str, line: int | None = None):
        super().__init__(what)
        self.what = what
        self.line = line


# --- images --------------------------------------------------------------------


def _image_size(data: bytes) -> tuple[str, int, int]:
    if data.startswith(b"\x89PNG\r\n\x1a\n") and data[12:16] == b"IHDR":
        wpx, hpx = struct.unpack(">II", data[16:24])
        return "png", wpx, hpx
    if data.startswith(b"\xff\xd8\xff"):
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            length = struct.unpack(">H", data[i + 2:i + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                hpx, wpx = struct.unpack(">HH", data[i + 5:i + 9])
                return "jpeg", wpx, hpx
            i += 2 + length
    raise BuildError("image is not a PNG or JPEG file (by its bytes, not its name)")


# --- the writer ----------------------------------------------------------------


class Writer:
    def __init__(self, doc: md.Document, opts: dict, md_dir: pathlib.Path, allow_dirs: list[pathlib.Path]):
        self.doc, self.opts = doc, opts
        self.md_dir, self.allow_dirs = md_dir, allow_dirs
        self.rels: list[tuple[str, str, str, bool]] = []  # id, type, target, external
        self.media: dict[str, tuple[str, bytes]] = {}  # part name -> (content type, bytes)
        self.image_rel: dict[pathlib.Path, tuple[str, int, int]] = {}
        self.footnote_ids: dict[str, int] = {}
        self.nums: list[tuple[int, int, int]] = []  # numId, abstractId, start(level0)
        self.doc_pr = 0
        self.counts = {"headings": 0, "paragraphs": 0, "list_items": 0, "tables": 0, "table_rows": 0,
                       "code_blocks": 0, "images": 0, "footnotes": 0, "links": 0}
        pw, ph = PAPER[opts["paper"]]
        top, right, bottom, left = (int(round(m * 1440)) for m in opts["margins"])
        self.page = (pw, ph, top, right, bottom, left)
        self.text_width_twips = pw - left - right

    def rel(self, kind: str, target: str, external: bool = False) -> str:
        rid = f"rId{len(self.rels) + 1}"
        self.rels.append((rid, kind, target, external))
        return rid

    # -- inlines --

    def run_props(self, node: dict, extra: str = "") -> str:
        p = []
        if node.get("link"):
            p.append('<w:rStyle w:val="Hyperlink"/>')
        if node.get("code"):
            p.append(f'<w:rFonts w:ascii="{CODE_FONT}" w:hAnsi="{CODE_FONT}" w:cs={quoteattr(self.opts["font"])}/>')
        if node.get("b") or "b" in extra:
            p.append("<w:b/><w:bCs/>")
        if node.get("i"):
            p.append("<w:i/><w:iCs/>")
        if node.get("strike"):
            p.append("<w:strike/>")
        if node.get("u"):
            p.append('<w:u w:val="single"/>')
        if node.get("sup"):
            p.append('<w:vertAlign w:val="superscript"/>')
        elif node.get("sub"):
            p.append('<w:vertAlign w:val="subscript"/>')
        p.append(LANG)
        return "<w:rPr>" + "".join(p) + "</w:rPr>"

    def text_run(self, node: dict, extra: str = "") -> str:
        return f'<w:r>{self.run_props(node, extra)}<w:t xml:space="preserve">{escape(node["s"])}</w:t></w:r>'

    def inlines(self, nodes: list[dict], extra: str = "") -> str:
        out = []
        i = 0
        while i < len(nodes):
            n = nodes[i]
            if n["t"] == "text" and n.get("link"):
                j = i
                while j < len(nodes) and nodes[j]["t"] == "text" and nodes[j].get("link") == n["link"]:
                    j += 1
                rid = self.rel(REL + "hyperlink", n["link"], external=True)
                self.counts["links"] += 1
                runs = "".join(self.text_run(x, extra) for x in nodes[i:j])
                out.append(f'<w:hyperlink r:id="{rid}" w:history="1">{runs}</w:hyperlink>')
                i = j
                continue
            if n["t"] == "text":
                out.append(self.text_run(n, extra))
            elif n["t"] == "hardbreak":
                out.append(f"<w:r><w:rPr>{LANG}</w:rPr><w:br/></w:r>")
            elif n["t"] == "task":
                mark = "☑ " if n["checked"] else "☐ "
                out.append(f'<w:r><w:rPr><w:rFonts w:ascii="{SYMBOL_FONT}" w:hAnsi="{SYMBOL_FONT}" w:cs="{SYMBOL_FONT}"/>{LANG}</w:rPr><w:t xml:space="preserve">{mark}</w:t></w:r>')
            elif n["t"] == "footnote_ref":
                fid = self.footnote_ids.setdefault(n["label"], len(self.footnote_ids) + 1)
                out.append(f'<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/>{LANG}</w:rPr><w:footnoteReference w:id="{fid}"/></w:r>')
            elif n["t"] == "image":
                out.append(self.image(n))
            i += 1
        if not out:  # an empty heading still has to be a paragraph with text (fidelity)
            out.append(f'<w:r><w:rPr>{LANG}</w:rPr><w:t xml:space="preserve"></w:t></w:r>')
        return "".join(out)

    def image(self, node: dict) -> str:
        src = node["src"]
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", src):
            raise BuildError(f"image {src!r}: remote images are not supported; only local PNG or JPEG files")
        path = (self.md_dir / src).resolve()
        if not any(path == root or root in path.parents for root in [self.md_dir] + self.allow_dirs):
            raise BuildError(f"image {src!r} lies outside the Markdown file's directory; pass --allow-dir for its directory (ADR 0011 §4)")
        if path not in self.image_rel:
            try:
                data = path.read_bytes()
            except OSError as exc:
                raise BuildError(f"image {src!r}: {exc.strerror}")
            kind, wpx, hpx = _image_size(data)
            n = len(self.media) + 1
            part = f"word/media/image{n}.{kind}"
            self.media[part] = (f"image/{kind}", data)
            rid = self.rel(REL + "image", f"media/image{n}.{kind}")
            self.image_rel[path] = (rid, wpx, hpx)
            self.counts["images"] += 1
        rid, wpx, hpx = self.image_rel[path]
        cx, cy = wpx * EMU_PER_PX, hpx * EMU_PER_PX
        max_cx = self.text_width_twips * EMU_PER_TWIP
        if cx > max_cx:
            cy = cy * max_cx // cx
            cx = max_cx
        self.doc_pr += 1
        alt = quoteattr(node["alt"])
        return (
            f"<w:r><w:rPr>{LANG}</w:rPr><w:drawing>"
            f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
            f'<wp:docPr id="{self.doc_pr}" name="Picture {self.doc_pr}" descr={alt}/>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="Picture {self.doc_pr}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            "</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>"
        )

    # -- blocks --

    def paragraph(self, inlines: list[dict], style: str | None = None, ppr: str = "", extra: str = "") -> str:
        head = (f'<w:pStyle w:val="{style}"/>' if style else "") + ppr
        self.counts["paragraphs"] += 1
        return f"<w:p><w:pPr>{head}</w:pPr>{self.inlines(inlines, extra)}</w:p>"

    def blocks(self, blocks: list[dict], level: int = 0, quote: bool = False) -> str:
        out = []
        for b in blocks:
            t = b["t"]
            if t == "heading":
                self.counts["headings"] += 1
                out.append(self.paragraph(b["inlines"], f"Heading{b['level']}"))
            elif t == "paragraph":
                ppr = f'<w:ind w:left="{720 * level}"/>' if level else ""
                out.append(self.paragraph(b["inlines"], "Quote" if quote else ("ListParagraph" if level else None), ppr))
            elif t == "code":
                self.counts["code_blocks"] += 1
                ind = f'<w:ind w:left="{720 * level}"/>' if level else ""
                lines = b["lines"] or [""]
                for line in lines:
                    out.append(self.paragraph([{"t": "text", "s": line}], "CodeBlock", ind))
            elif t == "quote":
                out.append(self.blocks(b["blocks"], level, quote=True))
            elif t == "break":
                self.counts["paragraphs"] += 1
                out.append('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="808080"/></w:pBdr></w:pPr></w:p>')
            elif t == "list":
                out.append(self.list(b, level, quote))
            elif t == "table":
                out.append(self.table(b))
        return "".join(out)

    def list(self, b: dict, level: int, quote: bool) -> str:
        if b["ordered"]:
            num_id = len(self.nums) + 2
            self.nums.append((num_id, 1, b["start"], level))
        else:
            num_id = 1
        out = []
        for item in b["items"]:
            self.counts["list_items"] += 1
            first, rest = (item[0], item[1:]) if item and item[0]["t"] == "paragraph" else (None, item)
            if first is not None:
                if first["inlines"] and first["inlines"][0]["t"] == "task":
                    ppr = f'<w:ind w:left="{720 * (level + 1)}"/>'
                else:
                    ppr = f'<w:numPr><w:ilvl w:val="{min(level, 8)}"/><w:numId w:val="{num_id}"/></w:numPr>'
                out.append(self.paragraph(first["inlines"], "ListParagraph", ppr))
            out.append(self.blocks(rest, level + 1, quote))
        return "".join(out)

    def table(self, b: dict) -> str:
        self.counts["tables"] += 1
        ncols = len(b["aligns"])
        col = self.text_width_twips // ncols
        grid = "".join(f'<w:gridCol w:w="{col}"/>' for _ in range(ncols))
        borders = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="808080"/>' for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
        rows = []
        for ri, row in enumerate(b["rows"]):
            self.counts["table_rows"] += 1
            cells = []
            for ci, cell in enumerate(row):
                jc = b["aligns"][ci]
                ppr = f'<w:jc w:val="{jc}"/>' if jc and jc != "left" else ""
                cells.append(f'<w:tc><w:tcPr><w:tcW w:w="{col}" w:type="dxa"/></w:tcPr>{self.paragraph(cell, None, ppr, "b" if ri == 0 else "")}</w:tc>')
            trpr = "<w:trPr><w:tblHeader/></w:trPr>" if ri == 0 else ""
            rows.append(f"<w:tr>{trpr}{''.join(cells)}</w:tr>")
        return (
            f'<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders>{borders}</w:tblBorders>'
            f'<w:tblLayout w:type="autofit"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>{"".join(rows)}</w:tbl>'
            "<w:p><w:pPr/></w:p>"
        )

    # -- parts --

    def field(self, instr: str, ppr: str = "") -> str:
        return (
            f"<w:p><w:pPr>{ppr}</w:pPr>"
            f'<w:r><w:rPr>{LANG}</w:rPr><w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r><w:rPr>{LANG}</w:rPr><w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
            f'<w:r><w:rPr>{LANG}</w:rPr><w:fldChar w:fldCharType="separate"/></w:r>'
            f'<w:r><w:rPr>{LANG}</w:rPr><w:fldChar w:fldCharType="end"/></w:r></w:p>'
        )

    def document_xml(self, body: str) -> str:
        pw, ph, top, right, bottom, left = self.page
        header = ""
        if self.opts["page_numbers"]:
            rid = self.rel(REL + "header", "header1.xml")
            header = f'<w:headerReference w:type="default" r:id="{rid}"/>'
        toc = ""
        if self.opts["toc"]:
            toc = self.field('TOC \\o "1-3" \\h \\z \\u') + '<w:p><w:pPr/></w:p>'
        sect = (
            f"<w:sectPr>{header}<w:pgSz w:w=\"{pw}\" w:h=\"{ph}\"/>"
            f'<w:pgMar w:top="{top}" w:right="{right}" w:bottom="{bottom}" w:left="{left}" w:header="720" w:footer="720" w:gutter="0"/>'
            "</w:sectPr>"
        )
        return (
            XML + f'<w:document xmlns:w="{W}" xmlns:r="{NS_R}" '
            'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f"<w:body>{toc}{body}{sect}</w:body></w:document>"
        )

    def footnotes_xml(self) -> str:
        parts = [
            '<w:footnote w:type="separator" w:id="-1"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:separator/></w:r></w:p></w:footnote>',
            '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>',
        ]
        for label, fid in sorted(self.footnote_ids.items(), key=lambda kv: kv[1]):
            self.counts["footnotes"] += 1
            blocks = self.doc.footnotes[label]
            first, rest = (blocks[0], blocks[1:]) if blocks and blocks[0]["t"] == "paragraph" else (None, blocks)
            mark = f'<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/>{LANG}</w:rPr><w:footnoteRef/></w:r><w:r><w:rPr>{LANG}</w:rPr><w:tab/></w:r>'
            body = ""
            if first is not None:
                self.counts["paragraphs"] += 1
                body = f'<w:p><w:pPr><w:pStyle w:val="FootnoteText"/></w:pPr>{mark}{self.inlines(first["inlines"])}</w:p>'
            else:
                body = f'<w:p><w:pPr><w:pStyle w:val="FootnoteText"/></w:pPr>{mark}</w:p>'
            body += self.blocks(rest)
            parts.append(f'<w:footnote w:id="{fid}">{body}</w:footnote>')
        return XML + f'<w:footnotes xmlns:w="{W}" xmlns:r="{NS_R}">' + "".join(parts) + "</w:footnotes>"

    def styles_xml(self) -> str:
        font = quoteattr(self.opts["font"])
        size = self.opts["size"]
        hp = lambda pt: int(round(pt * 2))
        jc = '<w:jc w:val="thaiDistribute"/>' if self.opts["align"] == "thai" else ""

        def heading(n, pt, bold, italic):
            rpr = ("<w:b/><w:bCs/>" if bold else "") + ("<w:i/><w:iCs/>" if italic else "") + f'<w:sz w:val="{hp(pt)}"/><w:szCs w:val="{hp(pt)}"/>'
            return (
                f'<w:style w:type="paragraph" w:styleId="Heading{n}"><w:name w:val="heading {n}"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
                f'<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="{240 if n == 1 else 200}" w:after="80"/><w:jc w:val="left"/><w:outlineLvl w:val="{n - 1}"/></w:pPr>'
                f"<w:rPr>{rpr}</w:rPr></w:style>"
            )

        return (
            XML + f'<w:styles xmlns:w="{W}">'
            "<w:docDefaults><w:rPrDefault><w:rPr>"
            f"<w:rFonts w:ascii={font} w:hAnsi={font} w:cs={font} w:eastAsia={font}/>"
            f'<w:sz w:val="{hp(size)}"/><w:szCs w:val="{hp(size)}"/><w:cs/><w:lang w:val="en-US" w:eastAsia="en-US" w:bidi="th-TH"/>'
            "</w:rPr></w:rPrDefault><w:pPrDefault><w:pPr>"
            f'<w:spacing w:after="120" w:line="264" w:lineRule="auto"/>{jc}'
            "</w:pPr></w:pPrDefault></w:docDefaults>"
            '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
            + heading(1, size + 4, True, False) + heading(2, size + 2, True, False) + heading(3, size, True, False)
            + heading(4, size, True, True) + heading(5, size, True, False) + heading(6, size, False, True)
            + '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:ind w:left="720"/><w:contextualSpacing/></w:pPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:ind w:left="720" w:right="720"/></w:pPr><w:rPr><w:i/><w:iCs/></w:rPr></w:style>'
            f'<w:style w:type="paragraph" w:styleId="CodeBlock"><w:name w:val="Code Block"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr><w:rPr><w:rFonts w:ascii="{CODE_FONT}" w:hAnsi="{CODE_FONT}" w:cs={font}/><w:sz w:val="{hp(size - 3)}"/><w:szCs w:val="{hp(size - 3)}"/></w:rPr></w:style>'
            f'<w:style w:type="paragraph" w:styleId="FootnoteText"><w:name w:val="footnote text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:left="360" w:hanging="360"/></w:pPr><w:rPr><w:sz w:val="{hp(size - 3)}"/><w:szCs w:val="{hp(size - 3)}"/></w:rPr></w:style>'
            '<w:style w:type="character" w:styleId="FootnoteReference"><w:name w:val="footnote reference"/><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>'
            '<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr></w:style>'
            "</w:styles>"
        )

    def numbering_xml(self) -> str:
        font = quoteattr(self.opts["font"])
        bullet = "".join(
            f'<w:lvl w:ilvl="{l}"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>'
            f'<w:pPr><w:ind w:left="{720 * (l + 1)}" w:hanging="360"/></w:pPr><w:rPr><w:rFonts w:ascii={font} w:hAnsi={font} w:cs={font}/></w:rPr></w:lvl>'
            for l in range(9)
        )
        decimal = "".join(
            f'<w:lvl w:ilvl="{l}"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%{l + 1}."/><w:lvlJc w:val="left"/>'
            f'<w:pPr><w:ind w:left="{720 * (l + 1)}" w:hanging="360"/></w:pPr></w:lvl>'
            for l in range(9)
        )
        nums = '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>' + "".join(
            f'<w:num w:numId="{nid}"><w:abstractNumId w:val="{aid}"/><w:lvlOverride w:ilvl="{min(level, 8)}"><w:startOverride w:val="{start}"/></w:lvlOverride></w:num>'
            for nid, aid, start, level in self.nums
        )
        return (
            XML + f'<w:numbering xmlns:w="{W}">'
            f'<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="hybridMultilevel"/>{bullet}</w:abstractNum>'
            f'<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="hybridMultilevel"/>{decimal}</w:abstractNum>'
            f"{nums}</w:numbering>"
        )

    def settings_xml(self) -> str:
        parts = []
        if self.opts["hide_spelling_errors"]:
            parts.append("<w:hideSpellingErrors/><w:hideGrammaticalErrors/>")
        parts.append('<w:defaultTabStop w:val="720"/><w:characterSpacingControl w:val="doNotCompress"/>')
        if self.opts["toc"]:
            parts.append('<w:updateFields w:val="true"/>')
        if self.footnote_ids:
            parts.append('<w:footnotePr><w:footnote w:id="-1"/><w:footnote w:id="0"/></w:footnotePr>')
        parts.append(
            "<w:compat>"
            '<w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>'
            '<w:compatSetting w:name="overrideTableStyleFontSizeAndJustification" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
            '<w:compatSetting w:name="enableOpenTypeFeatures" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
            '<w:compatSetting w:name="doNotFlipMirrorIndents" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
            '<w:compatSetting w:name="differentiateMultirowTableHeaders" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/>'
            "</w:compat>"
            '<w:themeFontLang w:val="en-US" w:bidi="th-TH"/>'
        )
        return XML + f'<w:settings xmlns:w="{W}">' + "".join(parts) + "</w:settings>"

    def header_xml(self) -> str:
        return XML + f'<w:hdr xmlns:w="{W}">' + self.field("PAGE", '<w:jc w:val="right"/>') + "</w:hdr>"

    def core_xml(self) -> str:
        fm = self.doc.front_matter
        inner = ""
        if fm.get("title"):
            inner += f"<dc:title>{escape(fm['title'])}</dc:title>"
        if fm.get("author"):
            inner += f"<dc:creator>{escape(fm['author'])}</dc:creator>"
        return (
            XML + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            f'xmlns:dc="http://purl.org/dc/elements/1.1/">{inner}</cp:coreProperties>'
        )

    def package(self) -> dict[str, bytes]:
        body = self.blocks(self.doc.blocks)
        unreferenced = [l for l in self.doc.footnote_order if l not in self.footnote_ids]
        if unreferenced:
            raise BuildError(f"footnote [^{unreferenced[0]}] is defined but never referenced; nothing may be dropped silently (ADR 0005)")
        document = self.document_xml(body)
        parts: dict[str, str | bytes] = {}
        overrides = [
            ("/word/document.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"),
            ("/word/styles.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"),
            ("/word/settings.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"),
            ("/word/numbering.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"),
            ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
        ]
        doc_rels = [
            self.rel(REL + "styles", "styles.xml"),
            self.rel(REL + "settings", "settings.xml"),
            self.rel(REL + "numbering", "numbering.xml"),
        ]
        if self.footnote_ids:
            self.rel(REL + "footnotes", "footnotes.xml")
            overrides.append(("/word/footnotes.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"))
            parts["word/footnotes.xml"] = self.footnotes_xml()
        if self.opts["page_numbers"]:
            overrides.append(("/word/header1.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"))
            parts["word/header1.xml"] = self.header_xml()
        defaults = '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
        for ext in sorted({ct.split("/")[1] for ct, _ in self.media.values()}):
            defaults += f'<Default Extension="{ext}" ContentType="image/{ext}"/>'
        parts["[Content_Types].xml"] = (
            XML + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' + defaults
            + "".join(f'<Override PartName="{p}" ContentType="{ct}"/>' for p, ct in overrides) + "</Types>"
        )
        parts["_rels/.rels"] = (
            XML + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{REL}officeDocument" Target="word/document.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            "</Relationships>"
        )
        parts["docProps/core.xml"] = self.core_xml()
        parts["word/document.xml"] = document
        parts["word/styles.xml"] = self.styles_xml()
        parts["word/settings.xml"] = self.settings_xml()
        parts["word/numbering.xml"] = self.numbering_xml()
        parts["word/_rels/document.xml.rels"] = (
            XML + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(
                f'<Relationship Id="{rid}" Type="{kind}" Target={quoteattr(target)}' + (' TargetMode="External"/>' if ext else "/>")
                for rid, kind, target, ext in self.rels
            )
            + "</Relationships>"
        )
        for name, (_ct, data) in self.media.items():
            parts[name] = data
        order = ["[Content_Types].xml", "_rels/.rels", "docProps/core.xml", "word/document.xml", "word/styles.xml",
                 "word/settings.xml", "word/numbering.xml", "word/footnotes.xml", "word/header1.xml",
                 "word/_rels/document.xml.rels"]
        ordered = [n for n in order if n in parts] + sorted(n for n in parts if n not in order)
        return {k: (parts[k].encode("utf-8") if isinstance(parts[k], str) else parts[k]) for k in ordered}


def pack(parts: dict[str, bytes]) -> bytes:
    """Stored entries, fixed timestamp, no OS-specific attributes — the bytes the
    JavaScript port reproduces. Part order is the order given."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        for name, data in parts.items():
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 0
            info.external_attr = 0o600 << 16  # what zipfile would set anyway; explicit so the port can match it
            zf.writestr(info, data)
    return buf.getvalue()


# --- fidelity (ADR 0005) -------------------------------------------------------


def _docx_text(parts: dict[str, bytes]) -> list[str]:
    """Every paragraph's text from the package, in the order plain_text() gives it."""
    out = []

    def paragraphs(root):
        for p in root.iter(w("p")):
            pieces, seen = [], False
            for el in p.iter():
                if el.tag == w("t"):
                    pieces.append(el.text or "")
                    seen = True
                elif el.tag == w("br") and el.get(w("type")) != "page":
                    pieces.append("\n")
                    seen = True
                elif el.tag == w("drawing"):
                    seen = True
            if seen:
                out.append("".join(pieces))

    paragraphs(ET.fromstring(parts["word/document.xml"]))
    if "word/footnotes.xml" in parts:
        root = ET.fromstring(parts["word/footnotes.xml"])
        notes = [f for f in root.iter(w("footnote")) if f.get(w("type")) is None]
        for note in sorted(notes, key=lambda f: int(f.get(w("id")))):
            paragraphs(note)
    return out


def _expected_text(doc: md.Document, footnote_ids: dict[str, int]) -> list[str]:
    out = md.plain_text(doc.blocks)
    for label, _fid in sorted(footnote_ids.items(), key=lambda kv: kv[1]):
        out.extend(md.plain_text(doc.footnotes[label]))
    return [unicodedata.normalize("NFC", s) for s in out]


# --- entry ---------------------------------------------------------------------


def build(md_path: pathlib.Path, out_path: pathlib.Path, opts: dict, allow_dirs: list[pathlib.Path]) -> dict:
    result: dict = {"ok": False, "file": str(out_path), "settings": _settings(opts)}
    try:
        text = md_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        result["error"] = f"cannot read {md_path}: {exc}"
        return result
    try:
        doc = md.parse(text)
        writer = Writer(doc, opts, md_path.resolve().parent, [d.resolve() for d in allow_dirs])
        parts = writer.package()
    except md.Unsupported as exc:
        result.update(error=exc.what, line=exc.line)
        return result
    except BuildError as exc:
        result["error"] = exc.what
        return result
    data = pack(parts)
    report = check_mod.check(io.BytesIO(data))
    findings = list(report.findings)
    expected, actual = _expected_text(doc, writer.footnote_ids), _docx_text(parts)
    if expected != actual:
        idx = next((i for i, (a, b) in enumerate(zip(expected, actual)) if a != b), min(len(expected), len(actual)))
        findings.append({"code": "fidelity", "part": "word/document.xml",
                         "message": f"paragraph {idx + 1} of the document does not match the Markdown ({len(expected)} paragraphs expected, {len(actual)} written)"})
    result.update(
        counts={**writer.counts, "runs": report.counts.get("runs", 0)},
        warnings=[{"code": "markdown", "message": m} for m in doc.warnings] + report.warnings,
        findings=findings,
        sha256=hashlib.sha256(data).hexdigest(),
        bytes=len(data),
    )
    if findings:
        return result
    try:
        out_path.write_bytes(data)
    except OSError as exc:
        result["error"] = f"cannot write {out_path}: {exc.strerror}"
        return result
    result["ok"] = True
    return result


def _settings(opts: dict) -> dict:
    top, right, bottom, left = opts["margins"]
    return {
        "font": opts["font"], "size_pt": opts["size"], "paper": opts["paper"],
        "margins_in": {"top": top, "right": right, "bottom": bottom, "left": left},
        "align": opts["align"], "toc": opts["toc"], "page_numbers": opts["page_numbers"],
        "hide_spelling_errors": opts["hide_spelling_errors"],
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="thai_docx build", add_help=True)
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--font", default=DEFAULTS["font"])
    ap.add_argument("--size", type=float, default=DEFAULTS["size"], help="body size in points")
    ap.add_argument("--paper", choices=sorted(PAPER), default=DEFAULTS["paper"])
    ap.add_argument("--margins", default=None, help="top,right,bottom,left in inches (default 1,1,1,1.5)")
    ap.add_argument("--align", choices=("left", "thai"), default=DEFAULTS["align"])
    ap.add_argument("--toc", action="store_true")
    ap.add_argument("--page-numbers", action="store_true")
    ap.add_argument("--hide-spelling-errors", action="store_true")
    ap.add_argument("--allow-dir", action="append", default=[], help="a directory images may be read from besides the Markdown file's own")
    try:
        a = ap.parse_args(argv)
    except SystemExit:
        return 2
    opts = dict(DEFAULTS)
    opts.update(font=a.font, size=a.size if a.size != int(a.size) else int(a.size), paper=a.paper, align=a.align,
                toc=a.toc, page_numbers=a.page_numbers, hide_spelling_errors=a.hide_spelling_errors)
    if a.margins:
        try:
            m = tuple(float(x) for x in a.margins.split(","))
            if len(m) != 4 or any(x < 0 for x in m):
                raise ValueError
        except ValueError:
            print(json.dumps({"ok": False, "error": "--margins takes four non-negative numbers: top,right,bottom,left"}))
            return 2
        opts["margins"] = m
    result = build(pathlib.Path(a.input), pathlib.Path(a.output), opts, [pathlib.Path(d) for d in a.allow_dir])
    print(json.dumps(result, ensure_ascii=False))
    if result["ok"]:
        return 0
    return 2 if "error" in result else 1
