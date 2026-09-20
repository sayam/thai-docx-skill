# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""The package around the body: document.xml's sections, styles, numbering, settings,
footnotes, headers and footers, core properties, content types and relationships.
"""

from __future__ import annotations

from .layout import CAPTION_STYLE, CAPTION_STYLE_NAME, list_entries
from .ooxml import W
from .settings import APPENDIX_NUMBERS, FRONT_NUMBERS, half_up
from .writer import CODE_FONT, DRAWING, LANG, NS_R, REL, SECTION_MARK, XML, Writer, attr, esc


def _end_section(xml: str, sect: str) -> str:
    """Close a section in the properties of its last top-level paragraph — a table's is the
    empty paragraph after it — so no empty paragraph can spill onto a page of its own."""
    at = xml.rindex("<w:p>")
    if xml.startswith("<w:p><w:pPr/>", at):
        return xml[:at] + "<w:p><w:pPr>" + sect + "</w:pPr>" + xml[at + len("<w:p><w:pPr/>"):]
    end = xml.index("</w:pPr>", at)
    return xml[:end] + sect + xml[end:]


# the built-in look of Heading 1 … 6: (points above the body size, bold, italic)
HEADING_LOOK = ((4, True, False), (2, True, False), (0, True, False), (0, True, True), (0, True, False), (0, False, True))


class Package(Writer):
    """A Writer that also writes every other part, and the whole package in order."""

    def heading_run(self, n: int) -> tuple[str | None, str]:
        """Heading n's font as the front matter names it (None: the document's), and the rest of
        its run properties in schema order — the built-in look, with what heading-n changes
        (ADR 0020). The style and the number Word draws for the heading both take them."""
        p = self.heading_props.get(n, {})
        more, bold, italic = HEADING_LOOK[n - 1]
        pt = p.get("size", self.opts["size"] + more)
        half = str(half_up(pt * 2))
        return p.get("font"), (
            ("<w:b/><w:bCs/>" if p.get("bold", bold) else "") + ("<w:i/><w:iCs/>" if p.get("italic", italic) else "")
            + ("<w:strike/>" if p.get("strike") else "")
            + ('<w:color w:val="' + p["color"] + '"/>' if "color" in p else "")
            + '<w:sz w:val="' + half + '"/><w:szCs w:val="' + half + '"/>'
            + ('<w:u w:val="' + p["underline"] + '"/>' if p.get("underline") else "")
        )

    def document_xml(self, body: str) -> str:
        pw, ph, top, right, bottom, left = self.page
        rids = []  # (kind, numbered part, plain part)
        for kind in self.page_parts():
            numbered = self.rel(REL + kind, kind + "1.xml")
            rids.append((kind, numbered, self.rel(REL + kind, kind + "2.xml") if self.plain_page_part() else None))
        toc = self.field('TOC \\o "1-3" \\h \\z \\u', entries=list_entries(self.items, "toc")) + "<w:p><w:pPr/></w:p>" if self.opts["toc"] else ""
        numbers = "thaiNumbers" if self.opts["thai_digits"] else "decimal"

        def sect(region: str | None, start: bool) -> str:
            """A cover shows the plain parts; front pages count ก ข ค from ก, the rest from 1."""
            refs = ""
            for kind, numbered, plain in rids:
                if region == "cover":
                    refs += '<w:' + kind + 'Reference w:type="default" r:id="' + plain + '"/>'
                    continue
                refs += '<w:' + kind + 'Reference w:type="default" r:id="' + numbered + '"/>'
                if self.title_page():
                    refs += '<w:' + kind + 'Reference w:type="first" r:id="' + plain + '"/>'
            if region is None:
                pg = '<w:pgNumType w:fmt="thaiNumbers"/>' if self.opts["thai_digits"] else ""
            elif region == "cover":
                pg = ""
            else:
                front = FRONT_NUMBERS[self.opts["front_page_numbers"]]
                front = "thaiNumbers" if front == "decimal" and self.opts["thai_digits"] else front
                pg = '<w:pgNumType w:fmt="' + (front if region == "front" else numbers) + '"' + (' w:start="1"' if start else "") + "/>"
            return (
                "<w:sectPr>" + refs + self.footnote_format() + '<w:pgSz w:w="' + str(pw) + '" w:h="' + str(ph) + '"'
                + (' w:orient="landscape"' if self.opts["landscape"] else "") + "/>"
                '<w:pgMar w:top="' + str(top) + '" w:right="' + str(right) + '" w:bottom="' + str(bottom) + '" w:left="' + str(left)
                + '" w:header="720" w:footer="720" w:gutter="0"/>' + pg
                + ("<w:titlePg/>" if self.title_page() and region != "cover" else "") + "</w:sectPr>"
            )

        if not self.regions:
            body += sect(None, False)
        else:
            pieces, started = body.split(SECTION_MARK), set()
            for k, region in enumerate(self.regions):
                group = "front" if region == "front" else "cover" if region == "cover" else "numbered"
                xml = sect(region, group not in started)
                started.add(group)
                pieces[k] = pieces[k] + xml if k == len(self.regions) - 1 else _end_section(pieces[k], xml)
            body = "".join(pieces)
        return (
            XML + '<w:document xmlns:w="' + W + '" xmlns:r="' + NS_R + '" '
            'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
            'xmlns:a="' + DRAWING + '" '
            'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            "<w:body>" + toc + body + "</w:body></w:document>"
        )

    def footnotes_xml(self) -> str:
        parts = [
            '<w:footnote w:type="separator" w:id="-1"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
            '<w:r><w:separator/></w:r></w:p></w:footnote>',
            '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
            '<w:r><w:continuationSeparator/></w:r></w:p></w:footnote>',
        ]
        mark = ('<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/>' + LANG + "</w:rPr><w:footnoteRef/></w:r>"
                "<w:r><w:rPr>" + LANG + "</w:rPr><w:tab/></w:r>")
        for fid, label in enumerate(self.doc.footnote_order, 1):
            self.counts["footnotes"] += 1
            blocks = self.doc.footnotes[label]
            if blocks and blocks[0]["t"] == "paragraph":
                first, rest = blocks[0]["inlines"], blocks[1:]
            else:
                first, rest = [], blocks
            self.counts["paragraphs"] += 1
            body = '<w:p><w:pPr><w:pStyle w:val="FootnoteText"/></w:pPr>' + mark + self.inlines(first) + "</w:p>" + self.blocks(rest)
            parts.append('<w:footnote w:id="' + str(fid) + '">' + body + "</w:footnote>")
        return XML + '<w:footnotes xmlns:w="' + W + '" xmlns:r="' + NS_R + '">' + "".join(parts) + "</w:footnotes>"

    def styles_xml(self) -> str:
        font = attr(self.opts["font"])
        size = self.opts["size"]
        small = max(size - 3, 1)

        def hp(pt: float) -> str:
            return str(half_up(pt * 2))

        jc = '<w:jc w:val="thaiDistribute"/>' if self.opts["align"] == "thai" else ""

        def heading(n: int) -> str:
            """The built-in look, with what the front matter's heading-n changes (ADR 0020)."""
            p = self.heading_props.get(n, {})
            name, rest = self.heading_run(n)
            face = attr(name) if name is not None else ""
            rpr = ("<w:rFonts w:ascii=" + face + " w:hAnsi=" + face + " w:cs=" + face + " w:eastAsia=" + face + "/>" if face else "") + rest
            spacing = '<w:spacing w:before="' + str(p.get("before", 240 if n == 1 else 200)) + '" w:after="' + str(p.get("after", 80)) + '"'
            spacing += (' w:line="' + str(p["line"]) + '" w:lineRule="auto"/>') if "line" in p else "/>"
            num = ('<w:numPr><w:ilvl w:val="' + str(n - 1) + '"/><w:numId w:val="' + str(self.heading_num_id()) + '"/></w:numPr>'
                   if self.heading_numbering() and n in self.numbered_levels() else "")
            ind = ""
            if "left" in p or "first" in p:
                ind = "<w:ind" + (' w:left="' + str(p["left"]) + '"' if "left" in p else "")
                if "first" in p:
                    ind += (' w:hanging="' + str(-p["first"]) + '"') if p["first"] < 0 else (' w:firstLine="' + str(p["first"]) + '"')
                ind += "/>"
            return (
                '<w:style w:type="paragraph" w:styleId="Heading' + str(n) + '"><w:name w:val="heading ' + str(n)
                + '"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
                "<w:pPr><w:keepNext/><w:keepLines/>" + ("<w:pageBreakBefore/>" if p.get("break") else "") + num + spacing + ind
                + '<w:jc w:val="' + p.get("jc", "left") + '"/><w:outlineLvl w:val="' + str(n - 1) + '"/></w:pPr>'
                "<w:rPr>" + rpr + "</w:rPr></w:style>"
            )

        def own(style_id: str, name: str, ppr: str = "") -> str:
            """A style Word applies itself (a TOC entry, a header): missing from the file, Word
            takes its own template's definition — another font and size — so it is written out."""
            return (
                '<w:style w:type="paragraph" w:styleId="' + style_id + '"><w:name w:val="' + name
                + '"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/>'
                + ("<w:pPr>" + ppr + "</w:pPr>" if ppr else "")
                + "<w:rPr><w:rFonts w:ascii=" + font + " w:hAnsi=" + font + " w:cs=" + font + " w:eastAsia=" + font + "/>"
                '<w:sz w:val="' + hp(size) + '"/><w:szCs w:val="' + hp(size) + '"/></w:rPr></w:style>'
            )

        applied = ""
        if self.opts["toc"]:
            applied += own("TOC1", "toc 1") + own("TOC2", "toc 2", '<w:ind w:left="240"/>') + own("TOC3", "toc 3", '<w:ind w:left="480"/>')
        for kind in self.page_parts():
            applied += own(kind.capitalize(), kind)
        kinds = {item["caption"]["kind"] for item in self.items if "caption" in item}
        if kinds:
            # a caption style of its own for each kind: the list of tables and the list of figures
            # collect the paragraphs in one style, where they used to collect SEQ fields (ADR 0036)
            applied += own("Caption", "caption", '<w:spacing w:before="120" w:after="120"/>')
            for kind in sorted(kinds):
                applied += ('<w:style w:type="paragraph" w:styleId="' + CAPTION_STYLE[kind] + '"><w:name w:val="'
                            + CAPTION_STYLE_NAME[kind] + '"/><w:basedOn w:val="Caption"/><w:next w:val="Normal"/></w:style>')
        if any(item["block"]["t"] == "directive" and item["block"]["name"] != "toc" for item in self.items):
            applied += own("TableofFigures", "table of figures")
        if any(item["block"]["t"] == "directive" and item["block"]["name"] == "toc" for item in self.items) and not self.opts["toc"]:
            applied += own("TOC1", "toc 1") + own("TOC2", "toc 2", '<w:ind w:left="240"/>') + own("TOC3", "toc 3", '<w:ind w:left="480"/>')
        if self.opts["table_size"] is not None:
            pt = hp(self.opts["table_size"])
            applied += ('<w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/><w:basedOn w:val="Normal"/><w:qFormat/>'
                        '<w:rPr><w:sz w:val="' + pt + '"/><w:szCs w:val="' + pt + '"/></w:rPr></w:style>')

        return (
            XML + '<w:styles xmlns:w="' + W + '">'
            "<w:docDefaults><w:rPrDefault><w:rPr>"
            "<w:rFonts w:ascii=" + font + " w:hAnsi=" + font + " w:cs=" + font + " w:eastAsia=" + font + "/>"
            '<w:sz w:val="' + hp(size) + '"/><w:szCs w:val="' + hp(size) + '"/><w:cs/><w:lang w:val="en-US" w:eastAsia="en-US" w:bidi="th-TH"/>'
            "</w:rPr></w:rPrDefault><w:pPrDefault><w:pPr>"
            '<w:spacing w:after="120" w:line="' + str(half_up(self.opts["line_spacing"] * 240)) + '" w:lineRule="auto"/>' + jc
            + "</w:pPr></w:pPrDefault></w:docDefaults>"
            # Normal repeats what the defaults above already say: an application that reads
            # styles but not w:docDefaults (WPS numbers one) then still has the font and size
            '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:rPr>'
            "<w:rFonts w:ascii=" + font + " w:hAnsi=" + font + " w:cs=" + font + " w:eastAsia=" + font + "/>"
            '<w:sz w:val="' + hp(size) + '"/><w:szCs w:val="' + hp(size) + '"/>' + LANG + "</w:rPr></w:style>"
            + "".join(heading(n) for n in range(1, 7))
            + '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:qFormat/>'
            '<w:pPr><w:ind w:left="720"/><w:contextualSpacing/></w:pPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/><w:qFormat/>'
            '<w:pPr><w:ind w:left="720" w:right="720"/></w:pPr><w:rPr><w:i/><w:iCs/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="CodeBlock"><w:name w:val="Code Block"/><w:basedOn w:val="Normal"/>'
            '<w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr><w:rPr><w:rFonts w:ascii="'
            + CODE_FONT + '" w:hAnsi="' + CODE_FONT + '" w:cs=' + font + '/><w:sz w:val="' + hp(small) + '"/><w:szCs w:val="' + hp(small)
            + '"/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="FootnoteText"><w:name w:val="footnote text"/><w:basedOn w:val="Normal"/>'
            '<w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:left="360" w:hanging="360"/></w:pPr><w:rPr><w:sz w:val="'
            + hp(small) + '"/><w:szCs w:val="' + hp(small) + '"/></w:rPr></w:style>'
            '<w:style w:type="character" w:styleId="FootnoteReference"><w:name w:val="footnote reference"/>'
            '<w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>'
            '<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:rPr><w:rFonts w:ascii=' + font + " w:hAnsi=" + font
            + " w:cs=" + font + '/><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr></w:style>'
            + applied +
            "</w:styles>"
        )

    def heading_numbering(self) -> bool:
        """Whether the package numbers the headings: not where the numbers are the build's own
        text, and not where no heading takes a number at all."""
        return not self.numbers_are_text() and any(
            "number" in item and item["region"] != "appendices" for item in self.items)

    def numbering_xml(self) -> str:
        """The bullet list, and — unless the numbers are the build's own text (ADR 0036) — the
        ordered lists, the headings and the appendices."""
        font, size = attr(self.opts["font"]), self.opts["size"]
        fmt = "thaiNumbers" if self.opts["thai_digits"] else "decimal"
        # a level with no font of its own is drawn in the application's default, which need
        # not carry Thai: WPS showed "บทที่ ๑" as Latin letters until every level named one
        half = str(half_up(size * 2))
        level_font = ("<w:rPr><w:rFonts w:ascii=" + font + " w:hAnsi=" + font + " w:cs=" + font + "/>"
                      '<w:sz w:val="' + half + '"/><w:szCs w:val="' + half + '"/>' + LANG + "</w:rPr>")

        def heading_font(ilvl: int) -> str:
            """A heading level's number is drawn as its heading is — "บทที่ 1" at Heading 1's size,
            not the body's — naming the font all the same; levels past Heading 6 have none."""
            if ilvl >= len(HEADING_LOOK):
                return level_font
            name, rest = self.heading_run(ilvl + 1)
            face = attr(name) if name is not None else font
            return "<w:rPr><w:rFonts w:ascii=" + face + " w:hAnsi=" + face + " w:cs=" + face + "/>" + rest + LANG + "</w:rPr>"
        bullet = "".join(
            '<w:lvl w:ilvl="' + str(ilvl) + '"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>'
            '<w:pPr><w:ind w:left="' + str(720 * (ilvl + 1)) + '" w:hanging="360"/></w:pPr>' + level_font + "</w:lvl>"
            for ilvl in range(9)
        )
        decimal = "".join(
            '<w:lvl w:ilvl="' + str(ilvl) + '"><w:start w:val="1"/><w:numFmt w:val="' + fmt + '"/><w:lvlText w:val="%' + str(ilvl + 1)
            + '."/><w:lvlJc w:val="left"/>'
            '<w:pPr><w:ind w:left="' + str(720 * (ilvl + 1)) + '" w:hanging="360"/></w:pPr>' + level_font + "</w:lvl>"
            for ilvl in range(9)
        )
        nums = '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>' + "".join(
            '<w:num w:numId="' + str(nid) + '"><w:abstractNumId w:val="1"/><w:lvlOverride w:ilvl="' + str(min(level, 8))
            + '"><w:startOverride w:val="' + str(start) + '"/></w:lvlOverride></w:num>'
            for nid, start, level in self.nums
        )
        if self.numbers_are_text():
            return (
                XML + '<w:numbering xmlns:w="' + W + '">'
                '<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="hybridMultilevel"/>' + bullet + "</w:abstractNum>"
                '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num></w:numbering>'
            )
        headings = ""
        # a list only where a heading takes a number: a label that reaches no heading changes no
        # byte, and the settings registry says so (ADR 0028)
        levels_on = self.numbered_levels() if self.heading_numbering() else set()
        if levels_on:
            # "1." for a # heading — "บทที่ 1" with chapters — then "1.1", "1.1.1" ... followed by a space, no hanging indent
            def lvl_text(ilvl: int) -> str:
                if ilvl == 0:
                    return self.opts["chapter_label"] + " %1" if self.has_chapters else "%1."
                return ".".join("%" + str(k + 1) for k in range(ilvl + 1))

            levels = "".join(
                '<w:lvl w:ilvl="' + str(ilvl) + '"><w:start w:val="1"/><w:numFmt w:val="' + fmt + '"/>'
                + ('<w:pStyle w:val="Heading' + str(ilvl + 1) + '"/>' if ilvl + 1 in levels_on else "")
                + '<w:suff w:val="space"/><w:lvlText w:val=' + attr(lvl_text(ilvl)) + '/><w:lvlJc w:val="left"/>' + heading_font(ilvl) + "</w:lvl>"
                for ilvl in range(9)
            )
            headings = '<w:abstractNum w:abstractNumId="2"><w:multiLevelType w:val="multilevel"/>' + levels + "</w:abstractNum>"
            nums += '<w:num w:numId="' + str(self.heading_num_id()) + '"><w:abstractNumId w:val="2"/></w:num>'
        if any("number" in item and item["region"] == "appendices" for item in self.items):
            # "ภาคผนวก ก", then "ก.1", "ก.1.1" with --heading-numbers; set on each heading, linked to no style
            first = APPENDIX_NUMBERS[self.opts["appendix_numbers"]]
            first = "thaiNumbers" if first == "decimal" and self.opts["thai_digits"] else first
            headings += '<w:abstractNum w:abstractNumId="3"><w:multiLevelType w:val="multilevel"/>' + "".join(
                '<w:lvl w:ilvl="' + str(ilvl) + '"><w:start w:val="1"/><w:numFmt w:val="' + (first if ilvl == 0 else fmt) + '"/>'
                + '<w:suff w:val="space"/><w:lvlText w:val='
                + attr(self.opts["appendix_label"] + " %1" if ilvl == 0 else ".".join("%" + str(k + 1) for k in range(ilvl + 1)))
                + '/><w:lvlJc w:val="left"/>' + heading_font(ilvl) + "</w:lvl>"
                for ilvl in range(9)
            ) + "</w:abstractNum>"
            nums += '<w:num w:numId="' + str(self.heading_num_id() + 1) + '"><w:abstractNumId w:val="3"/></w:num>'
        return (
            XML + '<w:numbering xmlns:w="' + W + '">'
            '<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="hybridMultilevel"/>' + bullet + "</w:abstractNum>"
            # the ordered lists' definition only where there is one: a flag that reaches nothing
            # changes no byte, and the settings registry says so (ADR 0028)
            + ('<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="hybridMultilevel"/>' + decimal + "</w:abstractNum>"
               if self.nums else "")
            + headings + nums + "</w:numbering>"
        )

    def captions_xml(self) -> str:
        """The caption labels the document uses, so Word's own Insert Caption offers them.

        Only where the application counts (`--auto-numbering`): a reader who inserts a caption
        there continues the document's numbering, and one who inserts a caption into a document
        whose numbers are text would start a counter of its own beside them — the half-numbered
        document ADR 0036 refuses. Word keeps a label the user makes in their own profile, not in
        the file; written here, the label travels with the document, already carrying its number
        format, its chapter number and the side of the table or figure it belongs on."""
        if self.numbers_are_text():
            return ""
        kinds = [k for k in ("table", "figure") if any(item.get("caption", {}).get("kind") == k for item in self.items)]
        if not kinds:
            return ""
        fmt = "thaiNumbers" if self.opts["thai_digits"] else "decimal"
        chapter = "1" if self.regions else "0"
        # a table's caption goes above it and a figure's below it, as the build writes them
        pos = {"table": "above", "figure": "below"}
        return "<w:captions>" + "".join(
            "<w:caption w:name=" + attr(self.opts[kind + "_label"]) + ' w:pos="' + pos[kind] + '" w:chapNum="' + chapter
            + '" w:heading="0" w:noLabel="0" w:numFmt="' + fmt + '" w:sep="hyphen"/>'
            for kind in kinds
        ) + "</w:captions>"

    def theme_xml(self) -> str:
        """The theme, naming this document's font as the document's own.

        A package with no theme leaves Word to resolve `+Body` and `+Headings` against its own
        built-in Office theme, and everything Word makes afterwards — a table it inserts, the
        `Caption` style it creates the first time a caption is inserted — comes out in that
        theme's Latin font instead of the document's, with the font box showing no name at all.
        `w:themeFontLang` in settings.xml already says which language takes which theme font; this
        is the part it points at. Generated matter carries what an application would otherwise
        supply (ADR 0027).

        Nothing in the document refers to the theme: every style names its fonts outright, so the
        theme changes no run this build writes. It is there for what the reader adds."""
        font = attr(self.opts["font"])
        faces = "".join("<a:" + tag + " typeface=" + font + "/>" for tag in ("latin", "ea", "cs"))
        # a colour scheme is required, and these are the twelve the Office theme names
        colours = "".join(
            "<a:" + tag + ">" + ('<a:sysClr val="' + val + '" lastClr="' + last + '"/>' if val.startswith("window")
                                 else '<a:srgbClr val="' + val + '"/>') + "</a:" + tag + ">"
            for tag, val, last in (
                ("dk1", "windowText", "000000"), ("lt1", "window", "FFFFFF"), ("dk2", "44546A", ""),
                ("lt2", "E7E6E6", ""), ("accent1", "4472C4", ""), ("accent2", "ED7D31", ""),
                ("accent3", "A5A5A5", ""), ("accent4", "FFC000", ""), ("accent5", "5B9BD5", ""),
                ("accent6", "70AD47", ""), ("hlink", "0563C1", ""), ("folHlink", "954F72", ""))
        )
        # three of each is what the format asks for; a document this skill writes uses none of them
        fill = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
        line = '<a:ln w="6350" cap="flat" cmpd="sng" algn="ctr">' + fill + '<a:prstDash val="solid"/></a:ln>'
        return (
            XML + '<a:theme xmlns:a="' + DRAWING + '" name="Office Theme"><a:themeElements>'
            '<a:clrScheme name="Office">' + colours + "</a:clrScheme>"
            '<a:fontScheme name="Office"><a:majorFont>' + faces + "</a:majorFont>"
            "<a:minorFont>" + faces + "</a:minorFont></a:fontScheme>"
            '<a:fmtScheme name="Office">'
            "<a:fillStyleLst>" + fill * 3 + "</a:fillStyleLst>"
            "<a:lnStyleLst>" + line * 3 + "</a:lnStyleLst>"
            "<a:effectStyleLst>" + "<a:effectStyle><a:effectLst/></a:effectStyle>" * 3 + "</a:effectStyleLst>"
            "<a:bgFillStyleLst>" + fill * 3 + "</a:bgFillStyleLst>"
            "</a:fmtScheme></a:themeElements></a:theme>"
        )

    def settings_xml(self) -> str:
        parts = []
        if self.opts["hide_spelling_errors"]:
            parts.append("<w:hideSpellingErrors/><w:hideGrammaticalErrors/>")
        parts.append('<w:defaultTabStop w:val="720"/><w:characterSpacingControl w:val="doNotCompress"/>')
        if self.opts["toc"] or any(item["block"]["t"] == "directive" for item in self.items):
            parts.append('<w:updateFields w:val="true"/>')
        if self.doc.footnote_order:
            fmt = '<w:numFmt w:val="thaiNumbers"/>' if self.opts["thai_digits"] else ""
            parts.append("<w:footnotePr>" + fmt + '<w:footnote w:id="-1"/><w:footnote w:id="0"/></w:footnotePr>')
        uri = ' w:uri="http://schemas.microsoft.com/office/word" '
        # Thai distributed spreads a line that ends in a manual break letter by letter across
        # the page ("ภ า ษ า ไ ท ย"); Word's "don't expand character spaces on a line ending
        # with SHIFT+RETURN" keeps such a line as it is. It goes before every compatSetting.
        shift_return = "<w:doNotExpandShiftReturn/>" if self.opts["align"] == "thai" else ""
        parts.append(
            "<w:compat>" + shift_return +
            '<w:compatSetting w:name="compatibilityMode"' + uri + 'w:val="15"/>'
            '<w:compatSetting w:name="overrideTableStyleFontSizeAndJustification"' + uri + 'w:val="1"/>'
            '<w:compatSetting w:name="enableOpenTypeFeatures"' + uri + 'w:val="1"/>'
            '<w:compatSetting w:name="doNotFlipMirrorIndents"' + uri + 'w:val="1"/>'
            '<w:compatSetting w:name="differentiateMultirowTableHeaders"' + uri + 'w:val="1"/>'
            "</w:compat>"
            '<w:themeFontLang w:val="en-US" w:bidi="th-TH"/>'
        )
        parts.append(self.captions_xml())
        return XML + '<w:settings xmlns:w="' + W + '">' + "".join(parts) + "</w:settings>"

    def footnote_format(self) -> str:
        """Thai-digit footnote marks, for the section; settings.xml says the same for the document."""
        return '<w:footnotePr><w:numFmt w:val="thaiNumbers"/></w:footnotePr>' if self.opts["thai_digits"] and self.doc.footnote_order else ""

    def page_number_part(self) -> str:
        """Where the page number goes; only when there is one."""
        return "footer" if self.opts["page_numbers"].startswith("bottom-") else "header"

    def page_parts(self) -> list[str]:
        """"header", "footer", both or neither: where --header, --footer and --page-numbers put something."""
        where = self.opts["page_numbers"]
        return [kind for kind in ("header", "footer")
                if self.opts[kind] is not None or (where and self.page_number_part() == kind)]

    def plain_page_part(self) -> bool:
        """A header or footer without the page number: for a first page without it, and a cover."""
        return self.title_page() or (bool(self.regions) and self.regions[0] == "cover")

    def title_page(self) -> bool:
        return bool(self.opts["page_numbers"]) and not self.opts["page_number_on_first"]

    def page_part_xml(self, kind: str, first: bool) -> str:
        """The text of --header or --footer, centred, then the page number when it goes
        here — except on a first page that goes without it. A part with neither is written
        out empty, so no application falls back to the numbered one."""
        style = '<w:pStyle w:val="' + kind.capitalize() + '"/>'
        body = ""
        if self.opts[kind] is not None:
            body += ("<w:p><w:pPr>" + style + '<w:jc w:val="center"/></w:pPr><w:r><w:rPr>' + LANG + '</w:rPr><w:t xml:space="preserve">'
                     + esc(self.opts[kind]) + "</w:t></w:r></w:p>")
        if self.opts["page_numbers"] and self.page_number_part() == kind and not first:
            body += self.field("PAGE", style + '<w:jc w:val="' + self.opts["page_numbers"].split("-")[1] + '"/>')
        tag = "hdr" if kind == "header" else "ftr"
        return XML + "<w:" + tag + ' xmlns:w="' + W + '">' + (body or "<w:p><w:pPr>" + style + "</w:pPr></w:p>") + "</w:" + tag + ">"

    def core_xml(self) -> str:
        fm = self.doc.front_matter
        inner = ""
        if fm.get("title"):
            inner += "<dc:title>" + esc(fm["title"]) + "</dc:title>"
        if fm.get("author"):
            inner += "<dc:creator>" + esc(fm["author"]) + "</dc:creator>"
        return (
            XML + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/">' + inner + "</cp:coreProperties>"
        )

    def package(self) -> list[tuple[str, bytes]]:
        body = self.body()
        document = self.document_xml(body)
        overrides = [
            ("/word/document.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"),
            ("/word/styles.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"),
            ("/word/settings.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"),
            ("/word/numbering.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"),
            ("/word/theme/theme1.xml", "application/vnd.openxmlformats-officedocument.theme+xml"),
            ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
        ]
        self.rel(REL + "styles", "styles.xml")
        self.rel(REL + "settings", "settings.xml")
        self.rel(REL + "numbering", "numbering.xml")
        self.rel(REL + "theme", "theme/theme1.xml")
        footnotes = None
        if self.doc.footnote_order:
            self.rel(REL + "footnotes", "footnotes.xml")
            overrides.append(("/word/footnotes.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"))
            footnotes = self.footnotes_xml()
        page_parts = []  # (part name, xml)
        for kind in self.page_parts():
            for n, first in (("1", False), ("2", True)) if self.plain_page_part() else (("1", False),):
                overrides.append(("/word/" + kind + n + ".xml", "application/vnd.openxmlformats-officedocument.wordprocessingml." + kind + "+xml"))
                page_parts.append(("word/" + kind + n + ".xml", self.page_part_xml(kind, first)))
        defaults = ('<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                    '<Default Extension="xml" ContentType="application/xml"/>')
        for ext in sorted({name.rsplit(".", 1)[1] for name, _ in self.media}):
            defaults += '<Default Extension="' + ext + '" ContentType="image/' + ext + '"/>'
        parts: list[tuple[str, str | bytes]] = [
            ("[Content_Types].xml", XML + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' + defaults
             + "".join('<Override PartName="' + p + '" ContentType="' + ct + '"/>' for p, ct in overrides) + "</Types>"),
            ("_rels/.rels", XML + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Id="rId1" Type="' + REL + 'officeDocument" Target="word/document.xml"/>'
             '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"'
             ' Target="docProps/core.xml"/>'
             "</Relationships>"),
            ("docProps/core.xml", self.core_xml()),
            ("word/document.xml", document),
            ("word/styles.xml", self.styles_xml()),
            ("word/settings.xml", self.settings_xml()),
            ("word/numbering.xml", self.numbering_xml()),
            ("word/theme/theme1.xml", self.theme_xml()),
        ]
        if footnotes is not None:
            parts.append(("word/footnotes.xml", footnotes))
        parts.extend(page_parts)
        parts.append(("word/_rels/document.xml.rels", XML + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                      + "".join('<Relationship Id="' + rid + '" Type="' + kind + '" Target=' + attr(target)
                                + (' TargetMode="External"/>' if ext else "/>")
                                for rid, kind, target, ext in self.rels)
                      + "</Relationships>"))
        parts.extend(self.media)
        return [(name, data.encode("utf-8") if isinstance(data, str) else data) for name, data in parts]
