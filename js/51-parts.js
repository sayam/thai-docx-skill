// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// thai-docx — parts: the port of scripts/thai_docx/parts.py. The package around the body: sections,
// styles, numbering, settings, footnotes, headers and footers, and the package in order.

// Close a section in the properties of its last top-level paragraph — a table's is the
// empty paragraph after it — so no empty paragraph can spill onto a page of its own.
function endSection(xml, sect) {
  const at = xml.lastIndexOf("<w:p>");
  if (xml.startsWith("<w:p><w:pPr/>", at)) return xml.slice(0, at) + "<w:p><w:pPr>" + sect + "</w:pPr>" + xml.slice(at + "<w:p><w:pPr/>".length);
  const end = xml.indexOf("</w:pPr>", at);
  return xml.slice(0, end) + sect + xml.slice(end);
}

// A Writer that also writes every other part, and the whole package in order.
// the built-in look of Heading 1 … 6: [points above the body size, bold, italic]
const HEADING_LOOK = [[4, true, false], [2, true, false], [0, true, false], [0, true, true], [0, true, false], [0, false, true]];

class Package extends Writer {
  // Heading n's font as the front matter names it (null: the document's), and the rest of its
  // run properties in schema order — the built-in look, with what heading-n changes (ADR 0020).
  // The style and the number Word draws for the heading both take them.
  headingRun(n) {
    const p = this.headingProps.get(n) || {};
    const [more, bold, italic] = HEADING_LOOK[n - 1];
    const pt = has(p, "size") ? p.size : this.opts.size + more;
    const half = String(halfUp(pt * 2));
    return [has(p, "font") ? p.font : null,
      ((has(p, "bold") ? p.bold : bold) ? "<w:b/><w:bCs/>" : "") + ((has(p, "italic") ? p.italic : italic) ? "<w:i/><w:iCs/>" : "") +
      (p.strike ? "<w:strike/>" : "") +
      (has(p, "color") ? '<w:color w:val="' + p.color + '"/>' : "") +
      '<w:sz w:val="' + half + '"/><w:szCs w:val="' + half + '"/>' +
      (p.underline ? '<w:u w:val="' + p.underline + '"/>' : "")];
  }

  documentXml(body) {
    const [pw, ph, top, right, bottom, left] = this.page;
    const rids = []; // [kind, numbered part, plain part]
    for (const kind of this.pageParts()) {
      const numbered = this.rel(REL + kind, kind + "1.xml");
      rids.push([kind, numbered, this.plainPagePart() ? this.rel(REL + kind, kind + "2.xml") : null]);
    }
    const toc = this.opts.toc ? this.field('TOC \\o "1-3" \\h \\z \\u', "", listEntries(this.items, "toc")) + "<w:p><w:pPr/></w:p>" : "";
    const numbers = this.opts.thai_digits ? "thaiNumbers" : "decimal";
    // A cover shows the plain parts; front pages count ก ข ค from ก, the rest from 1.
    const sect = (region, start) => {
      let refs = "";
      for (const [kind, numbered, plain] of rids) {
        if (region === "cover") {
          refs += "<w:" + kind + 'Reference w:type="default" r:id="' + plain + '"/>';
          continue;
        }
        refs += "<w:" + kind + 'Reference w:type="default" r:id="' + numbered + '"/>';
        if (this.titlePage()) refs += "<w:" + kind + 'Reference w:type="first" r:id="' + plain + '"/>';
      }
      let pg;
      if (region === null) pg = this.opts.thai_digits ? '<w:pgNumType w:fmt="thaiNumbers"/>' : "";
      else if (region === "cover") pg = "";
      else {
        let front = FRONT_NUMBERS[this.opts.front_page_numbers];
        if (front === "decimal" && this.opts.thai_digits) front = "thaiNumbers";
        pg = '<w:pgNumType w:fmt="' + (region === "front" ? front : numbers) + '"' + (start ? ' w:start="1"' : "") + "/>";
      }
      return (
        "<w:sectPr>" + refs + this.footnoteFormat() + '<w:pgSz w:w="' + pw + '" w:h="' + ph + '"' + (this.opts.landscape ? ' w:orient="landscape"' : "") + "/>" +
        '<w:pgMar w:top="' + top + '" w:right="' + right + '" w:bottom="' + bottom + '" w:left="' + left +
        '" w:header="720" w:footer="720" w:gutter="0"/>' + pg +
        (this.titlePage() && region !== "cover" ? "<w:titlePg/>" : "") + "</w:sectPr>"
      );
    };
    if (!this.regions.length) {
      body += sect(null, false);
    } else {
      const pieces = body.split(SECTION_MARK);
      const started = new Set();
      this.regions.forEach((region, k) => {
        const group = region === "front" ? "front" : region === "cover" ? "cover" : "numbered";
        const xml = sect(region, !started.has(group));
        started.add(group);
        pieces[k] = k === this.regions.length - 1 ? pieces[k] + xml : endSection(pieces[k], xml);
      });
      body = pieces.join("");
    }
    return (
      XML_DECL + '<w:document xmlns:w="' + W + '" xmlns:r="' + NS_R + '" ' +
      'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" ' +
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" ' +
      'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">' +
      "<w:body>" + toc + body + "</w:body></w:document>"
    );
  }

  footnotesXml() {
    const parts = [
      '<w:footnote w:type="separator" w:id="-1"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:separator/></w:r></w:p></w:footnote>',
      '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>',
    ];
    const mark = '<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/>' + LANG + "</w:rPr><w:footnoteRef/></w:r>" +
      "<w:r><w:rPr>" + LANG + "</w:rPr><w:tab/></w:r>";
    this.doc.footnoteOrder.forEach((label, k) => {
      const fid = k + 1;
      this.counts.footnotes += 1;
      const blocks = this.doc.footnotes.get(label);
      let first, rest;
      if (blocks.length && blocks[0].t === "paragraph") {
        first = blocks[0].inlines;
        rest = blocks.slice(1);
      } else {
        first = [];
        rest = blocks;
      }
      this.counts.paragraphs += 1;
      const body = '<w:p><w:pPr><w:pStyle w:val="FootnoteText"/></w:pPr>' + mark + this.inlines(first) + "</w:p>" + this.blocks(rest);
      parts.push('<w:footnote w:id="' + fid + '">' + body + "</w:footnote>");
    });
    return XML_DECL + '<w:footnotes xmlns:w="' + W + '" xmlns:r="' + NS_R + '">' + parts.join("") + "</w:footnotes>";
  }

  stylesXml() {
    const font = attr(this.opts.font);
    const size = this.opts.size;
    const small = Math.max(size - 3, 1);
    const hp = (pt) => String(halfUp(pt * 2));
    const jc = this.opts.align === "thai" ? '<w:jc w:val="thaiDistribute"/>' : "";
    // The built-in look, with what the front matter's heading-n changes (ADR 0020).
    const heading = (n) => {
      const p = this.headingProps.get(n) || {};
      const [name, rest] = this.headingRun(n);
      const face = name !== null ? attr(name) : "";
      const rpr = (face ? "<w:rFonts w:ascii=" + face + " w:hAnsi=" + face + " w:cs=" + face + " w:eastAsia=" + face + "/>" : "") + rest;
      let spacing = '<w:spacing w:before="' + (has(p, "before") ? p.before : n === 1 ? 240 : 200) + '" w:after="' + (has(p, "after") ? p.after : 80) + '"';
      spacing += has(p, "line") ? ' w:line="' + p.line + '" w:lineRule="auto"/>' : "/>";
      let ind = "";
      if (has(p, "left") || has(p, "first")) {
        ind = "<w:ind" + (has(p, "left") ? ' w:left="' + p.left + '"' : "");
        if (has(p, "first")) ind += p.first < 0 ? ' w:hanging="' + -p.first + '"' : ' w:firstLine="' + p.first + '"';
        ind += "/>";
      }
      return (
        '<w:style w:type="paragraph" w:styleId="Heading' + n + '"><w:name w:val="heading ' + n + '"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>' +
        "<w:pPr><w:keepNext/><w:keepLines/>" + (p.break ? "<w:pageBreakBefore/>" : "") + spacing + ind +
        '<w:jc w:val="' + (has(p, "jc") ? p.jc : "left") + '"/><w:outlineLvl w:val="' + (n - 1) + '"/></w:pPr>' +
        "<w:rPr>" + rpr + "</w:rPr></w:style>"
      );
    };
    // A style Word applies itself (a TOC entry, a header): missing from the file, Word
    // takes its own template's definition — another font and size — so it is written out.
    const own = (styleId, name, ppr) =>
      '<w:style w:type="paragraph" w:styleId="' + styleId + '"><w:name w:val="' + name + '"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/>' +
      (ppr ? "<w:pPr>" + ppr + "</w:pPr>" : "") +
      "<w:rPr><w:rFonts w:ascii=" + font + " w:hAnsi=" + font + " w:cs=" + font + " w:eastAsia=" + font + "/>" +
      '<w:sz w:val="' + hp(size) + '"/><w:szCs w:val="' + hp(size) + '"/></w:rPr></w:style>';
    let applied = "";
    if (this.opts.toc) applied += own("TOC1", "toc 1") + own("TOC2", "toc 2", '<w:ind w:left="240"/>') + own("TOC3", "toc 3", '<w:ind w:left="480"/>');
    for (const kind of this.pageParts()) applied += own(kind[0].toUpperCase() + kind.slice(1), kind);
    const kinds = [...new Set(this.items.filter((item) => item.caption).map((item) => item.caption.kind))].sort();
    if (kinds.length) {
      // a caption style of its own for each kind: the list of tables and the list of figures
      // collect the paragraphs in one style, where they used to collect SEQ fields (ADR 0035)
      applied += own("Caption", "caption", '<w:spacing w:before="120" w:after="120"/>');
      for (const kind of kinds) {
        applied += '<w:style w:type="paragraph" w:styleId="' + CAPTION_STYLE[kind] + '"><w:name w:val="' +
          CAPTION_STYLE_NAME[kind] + '"/><w:basedOn w:val="Caption"/><w:next w:val="Normal"/></w:style>';
      }
    }
    if (this.items.some((item) => item.block.t === "directive" && item.block.name !== "toc")) applied += own("TableofFigures", "table of figures");
    if (this.items.some((item) => item.block.t === "directive" && item.block.name === "toc") && !this.opts.toc) {
      applied += own("TOC1", "toc 1") + own("TOC2", "toc 2", '<w:ind w:left="240"/>') + own("TOC3", "toc 3", '<w:ind w:left="480"/>');
    }
    if (this.opts.table_size !== null) {
      const pt = hp(this.opts.table_size);
      applied += '<w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/><w:basedOn w:val="Normal"/><w:qFormat/>' +
        '<w:rPr><w:sz w:val="' + pt + '"/><w:szCs w:val="' + pt + '"/></w:rPr></w:style>';
    }
    return (
      XML_DECL + '<w:styles xmlns:w="' + W + '">' +
      "<w:docDefaults><w:rPrDefault><w:rPr>" +
      "<w:rFonts w:ascii=" + font + " w:hAnsi=" + font + " w:cs=" + font + " w:eastAsia=" + font + "/>" +
      '<w:sz w:val="' + hp(size) + '"/><w:szCs w:val="' + hp(size) + '"/><w:cs/><w:lang w:val="en-US" w:eastAsia="en-US" w:bidi="th-TH"/>' +
      "</w:rPr></w:rPrDefault><w:pPrDefault><w:pPr>" +
      '<w:spacing w:after="120" w:line="' + halfUp(this.opts.line_spacing * 240) + '" w:lineRule="auto"/>' + jc +
      "</w:pPr></w:pPrDefault></w:docDefaults>" +
      // Normal repeats what the defaults above already say: an application that reads styles
      // but not w:docDefaults (WPS numbers one) then still has the font and size
      '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:rPr>' +
      "<w:rFonts w:ascii=" + font + " w:hAnsi=" + font + " w:cs=" + font + " w:eastAsia=" + font + "/>" +
      '<w:sz w:val="' + hp(size) + '"/><w:szCs w:val="' + hp(size) + '"/>' + LANG + "</w:rPr></w:style>" +
      [1, 2, 3, 4, 5, 6].map((n) => heading(n)).join("") +
      '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:ind w:left="720"/><w:contextualSpacing/></w:pPr></w:style>' +
      '<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:ind w:left="720" w:right="720"/></w:pPr><w:rPr><w:i/><w:iCs/></w:rPr></w:style>' +
      '<w:style w:type="paragraph" w:styleId="CodeBlock"><w:name w:val="Code Block"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr><w:rPr><w:rFonts w:ascii="' +
      CODE_FONT + '" w:hAnsi="' + CODE_FONT + '" w:cs=' + font + '/><w:sz w:val="' + hp(small) + '"/><w:szCs w:val="' + hp(small) + '"/></w:rPr></w:style>' +
      '<w:style w:type="paragraph" w:styleId="FootnoteText"><w:name w:val="footnote text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:left="360" w:hanging="360"/></w:pPr><w:rPr><w:sz w:val="' +
      hp(small) + '"/><w:szCs w:val="' + hp(small) + '"/></w:rPr></w:style>' +
      '<w:style w:type="character" w:styleId="FootnoteReference"><w:name w:val="footnote reference"/><w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>' +
      '<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:rPr><w:rFonts w:ascii=' + font + " w:hAnsi=" + font + " w:cs=" + font + '/><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr></w:style>' +
      applied +
      "</w:styles>"
    );
  }

  // Only the bullet list is numbered by the package now: every other marker and number is
  // written into the document as text (ADR 0035), because an application that does not know a
  // format draws it its own way — thaiNumbers as 1, 2, 3 — and then the same file reads
  // differently in two readers.
  numberingXml() {
    const font = attr(this.opts.font);
    let bullet = "";
    // a level with no font of its own is drawn in the application's default, which need not
    // carry Thai: WPS showed "บทที่ ๑" as Latin letters until every level named one
    const half = String(halfUp(this.opts.size * 2));
    const levelFont = "<w:rPr><w:rFonts w:ascii=" + font + " w:hAnsi=" + font + " w:cs=" + font + "/>" +
      '<w:sz w:val="' + half + '"/><w:szCs w:val="' + half + '"/>' + LANG + "</w:rPr>";
    for (let l = 0; l < 9; l++) {
      bullet += '<w:lvl w:ilvl="' + l + '"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>' +
        '<w:pPr><w:ind w:left="' + 720 * (l + 1) + '" w:hanging="360"/></w:pPr>' + levelFont + "</w:lvl>";
    }
    return (
      XML_DECL + '<w:numbering xmlns:w="' + W + '">' +
      '<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="hybridMultilevel"/>' + bullet + "</w:abstractNum>" +
      '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num></w:numbering>'
    );
  }

  settingsXml() {
    const parts = [];
    if (this.opts.hide_spelling_errors) parts.push("<w:hideSpellingErrors/><w:hideGrammaticalErrors/>");
    parts.push('<w:defaultTabStop w:val="720"/><w:characterSpacingControl w:val="doNotCompress"/>');
    if (this.opts.toc || this.items.some((item) => item.block.t === "directive")) parts.push('<w:updateFields w:val="true"/>');
    if (this.doc.footnoteOrder.length) {
      const fmt = this.opts.thai_digits ? '<w:numFmt w:val="thaiNumbers"/>' : "";
      parts.push("<w:footnotePr>" + fmt + '<w:footnote w:id="-1"/><w:footnote w:id="0"/></w:footnotePr>');
    }
    const uri = ' w:uri="http://schemas.microsoft.com/office/word" ';
    // Thai distributed spreads a line that ends in a manual break letter by letter across the
    // page; Word's "don't expand character spaces on a line ending with SHIFT+RETURN" keeps
    // such a line as it is. It goes before every compatSetting.
    const shiftReturn = this.opts.align === "thai" ? "<w:doNotExpandShiftReturn/>" : "";
    parts.push(
      "<w:compat>" + shiftReturn +
      '<w:compatSetting w:name="compatibilityMode"' + uri + 'w:val="15"/>' +
      '<w:compatSetting w:name="overrideTableStyleFontSizeAndJustification"' + uri + 'w:val="1"/>' +
      '<w:compatSetting w:name="enableOpenTypeFeatures"' + uri + 'w:val="1"/>' +
      '<w:compatSetting w:name="doNotFlipMirrorIndents"' + uri + 'w:val="1"/>' +
      '<w:compatSetting w:name="differentiateMultirowTableHeaders"' + uri + 'w:val="1"/>' +
      "</w:compat>" +
      '<w:themeFontLang w:val="en-US" w:bidi="th-TH"/>'
    );
    return XML_DECL + '<w:settings xmlns:w="' + W + '">' + parts.join("") + "</w:settings>";
  }

  // Thai-digit footnote marks, for the section; settings.xml says the same for the document.
  footnoteFormat() {
    return this.opts.thai_digits && this.doc.footnoteOrder.length ? '<w:footnotePr><w:numFmt w:val="thaiNumbers"/></w:footnotePr>' : "";
  }

  // Where the page number goes; only when there is one.
  pageNumberPart() {
    return this.opts.page_numbers.startsWith("bottom-") ? "footer" : "header";
  }

  // "header", "footer", both or neither: where --header, --footer and --page-numbers put something.
  pageParts() {
    return ["header", "footer"].filter((kind) => this.opts[kind] !== null || (this.opts.page_numbers && this.pageNumberPart() === kind));
  }

  // A header or footer without the page number: for a first page without it, and a cover.
  plainPagePart() {
    return this.titlePage() || (this.regions.length > 0 && this.regions[0] === "cover");
  }

  titlePage() {
    return Boolean(this.opts.page_numbers) && !this.opts.page_number_on_first;
  }

  // The text of --header or --footer, centred, then the page number when it goes
  // here — except on a first page that goes without it. A part with neither is written
  // out empty, so no application falls back to the numbered one.
  pagePartXml(kind, first) {
    const style = '<w:pStyle w:val="' + kind[0].toUpperCase() + kind.slice(1) + '"/>';
    let body = "";
    if (this.opts[kind] !== null) {
      body += "<w:p><w:pPr>" + style + '<w:jc w:val="center"/></w:pPr><w:r><w:rPr>' + LANG + '</w:rPr><w:t xml:space="preserve">' +
        esc(this.opts[kind]) + "</w:t></w:r></w:p>";
    }
    if (this.opts.page_numbers && this.pageNumberPart() === kind && !first) {
      body += this.field("PAGE", style + '<w:jc w:val="' + this.opts.page_numbers.split("-")[1] + '"/>');
    }
    const tag = kind === "header" ? "hdr" : "ftr";
    return XML_DECL + "<w:" + tag + ' xmlns:w="' + W + '">' + (body || "<w:p><w:pPr>" + style + "</w:pPr></w:p>") + "</w:" + tag + ">";
  }

  coreXml() {
    const fm = this.doc.frontMatter;
    let inner = "";
    if (fm.get("title")) inner += "<dc:title>" + esc(fm.get("title")) + "</dc:title>";
    if (fm.get("author")) inner += "<dc:creator>" + esc(fm.get("author")) + "</dc:creator>";
    return (
      XML_DECL + '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" ' +
      'xmlns:dc="http://purl.org/dc/elements/1.1/">' + inner + "</cp:coreProperties>"
    );
  }

  pkg() {
    const body = this.body();
    const document = this.documentXml(body);
    const overrides = [
      ["/word/document.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"],
      ["/word/styles.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"],
      ["/word/settings.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"],
      ["/word/numbering.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"],
      ["/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"],
    ];
    this.rel(REL + "styles", "styles.xml");
    this.rel(REL + "settings", "settings.xml");
    this.rel(REL + "numbering", "numbering.xml");
    let footnotes = null;
    if (this.doc.footnoteOrder.length) {
      this.rel(REL + "footnotes", "footnotes.xml");
      overrides.push(["/word/footnotes.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"]);
      footnotes = this.footnotesXml();
    }
    const pageParts = []; // [part name, xml]
    for (const kind of this.pageParts()) {
      for (const [n, first] of this.plainPagePart() ? [["1", false], ["2", true]] : [["1", false]]) {
        overrides.push(["/word/" + kind + n + ".xml", "application/vnd.openxmlformats-officedocument.wordprocessingml." + kind + "+xml"]);
        pageParts.push(["word/" + kind + n + ".xml", this.pagePartXml(kind, first)]);
      }
    }
    let defaults = '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>';
    const exts = [...new Set(this.media.map(([name]) => name.slice(name.lastIndexOf(".") + 1)))].sort();
    for (const ext of exts) defaults += '<Default Extension="' + ext + '" ContentType="image/' + ext + '"/>';
    const parts = [
      ["[Content_Types].xml", XML_DECL + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' + defaults +
        overrides.map(([p, ct]) => '<Override PartName="' + p + '" ContentType="' + ct + '"/>').join("") + "</Types>"],
      ["_rels/.rels", XML_DECL + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
        '<Relationship Id="rId1" Type="' + REL + 'officeDocument" Target="word/document.xml"/>' +
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>' +
        "</Relationships>"],
      ["docProps/core.xml", this.coreXml()],
      ["word/document.xml", document],
      ["word/styles.xml", this.stylesXml()],
      ["word/settings.xml", this.settingsXml()],
      ["word/numbering.xml", this.numberingXml()],
    ];
    if (footnotes !== null) parts.push(["word/footnotes.xml", footnotes]);
    parts.push(...pageParts);
    parts.push(["word/_rels/document.xml.rels", XML_DECL + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
      this.rels.map(([rid, kind, target, ext]) => '<Relationship Id="' + rid + '" Type="' + kind + '" Target=' + attr(target) + (ext ? ' TargetMode="External"/>' : "/>")).join("") +
      "</Relationships>"]);
    for (const m of this.media) parts.push(m);
    return parts.map(([name, data]) => [name, typeof data === "string" ? utf8(data) : data]);
  }
}
