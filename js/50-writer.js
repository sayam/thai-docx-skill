// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// thai-docx — writer: the port of scripts/thai_docx/writer.py. The body of word/document.xml;
// Package in 51-parts.js adds the other parts. The same Markdown, images and settings give
// the same bytes (ADR 0008).

// A text inline whose run properties are the ones a caption's label carries: bold, nothing else.
function isBoldOnly(node) {
  return Boolean(node.b) && !(node.i || node.strike || node.code || node.u || node.sup || node.sub || node.link);
}

// A text inline that carries any formatting of its own.
function isFormatted(node) {
  return Boolean(node.b || node.i || node.strike || node.code || node.u || node.sup || node.sub || node.link);
}

const CODE_FONT = "Consolas";
// Styles whose own definition fixes the alignment — the styles part writes a <w:jc> into each
// of them. A paragraph in one of these takes its style's alignment, so latinJc leaves it alone.
const STYLE_FIXES_ALIGNMENT = new Set(["Heading1", "Heading2", "Heading3", "Heading4", "Heading5", "Heading6", "CodeBlock"]);
const RE_PSTYLE = /<w:pStyle w:val="([^"]+)"\/>/;
// The box a task list draws, and the font that has it. Not ☐/☑ in Segoe UI Symbol: those
// characters live only in symbol fonts, and the one Windows has is on no other machine, so the
// box vanished everywhere else (ADR 0033). A white and a black square are in every ordinary
// text font, and Arial is on Windows and macOS and is what fontconfig gives for Arial on Linux.
const SYMBOL_FONT = "Arial";
const BOX = "□ ", BOX_CHECKED = "■ ";
const NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships";
const REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/";
const XML_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n';
const DRAWING = "http://schemas.openxmlformats.org/drawingml/2006/main"; // the theme, and a picture's own namespace
const EMU_PER_PX = 9525;
const EMU_PER_TWIP = 635;
// A run says it is complex script where its text is complex script, and says nothing where it is
// not (ADR 0039, amending cause 2 of ADR 0004). Omission is how it says nothing: no style and no
// document default carries the element either, so there is nothing to inherit. Whether the text
// also says *which* complex-script language it is in is --thai-language's to decide (ADR 0038);
// w:bidi="th-TH" reaches no run that holds no complex script, so it goes on the marked runs.
// No run carries w:lang otherwise: docDefaults declares the Latin and East Asian languages once.
const CS = "<w:cs/>";
const CS_THAI = '<w:cs/><w:lang w:bidi="th-TH"/>';
const THAI_FIRST = 0x0e00;
const THAI_LAST = 0x0e7f;

// `C` complex script, `L` not, `N` neutral — it takes the script of the letter beside it. Thai is
// the complex script this skill writes. Arabic digits and ASCII punctuation are not complex
// script, which is measured, not assumed: Word cuts `120 ` out of a Thai sentence and leaves it
// unmarked (2026-09-22, what Word writes when a person types).
function script(ch) {
  const c = ch.codePointAt(0);
  if (c >= THAI_FIRST && c <= THAI_LAST) return "C";
  return /\s/.test(ch) ? "N" : "L";
}

// `text` cut where the script changes, as Word cuts it (ADR 0039). A neutral character takes the
// script of the strong character before it. One that opens the text has none before it, so it
// takes the first strong character instead, and text that is neutral throughout is not complex
// script — neither case was measured in Word, and neither is visible while a run's Latin and
// complex-script fonts and sizes are the same. An empty string is one piece, so an empty
// paragraph still carries a run for fidelity to read.
function scriptRuns(text) {
  const chars = Array.from(text);
  if (!chars.length) return [[false, ""]];
  const marks = chars.map(script);
  const first = marks.find((m) => m !== "N") || "L";
  const out = [];
  let prev = "";
  for (const m of marks) {
    if (m === "N") out.push(prev || first);
    else { out.push(m); prev = m; }
  }
  const pieces = [];
  let start = 0;
  for (let i = 1; i <= chars.length; i += 1) {
    if (i === chars.length || out[i] !== out[start]) {
      pieces.push([out[start] === "C", chars.slice(start, i).join("")]);
      start = i;
    }
  }
  return pieces;
}
// Thai marks above and below a consonant take no width of their own when a column is measured
const THAI_MARKS = new Set([0x0e31, 0x0e34, 0x0e35, 0x0e36, 0x0e37, 0x0e38, 0x0e39, 0x0e3a, 0x0e47, 0x0e48, 0x0e49, 0x0e4a, 0x0e4b, 0x0e4c, 0x0e4d, 0x0e4e]);
// Word's own table default; with no table style it would otherwise be 0 and text touches the borders
const CELL_MARGINS = '<w:tblCellMar><w:left w:w="108" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar>';

function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function attr(s) {
  return '"' + esc(s).replace(/"/g, "&quot;").replace(/\t/g, "&#9;").replace(/\n/g, "&#10;").replace(/\r/g, "&#13;") + '"';
}

function imageSize(data) {
  const sig = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
  if (data.length >= 24 && sig.every((v, i) => data[i] === v) && data[12] === 0x49 && data[13] === 0x48 && data[14] === 0x44 && data[15] === 0x52) {
    const wpx = rd32be(data, 16);
    const hpx = rd32be(data, 20);
    if (!(wpx && hpx)) throw new BuildError("image has no width or height");
    // a signature and an IHDR say how big the picture is, not that its pixels arrived;
    // a copy or a download that stopped has both, and Word draws a blank frame for it
    const end = data.length;
    if (!(data[end - 8] === 0x49 && data[end - 7] === 0x45 && data[end - 6] === 0x4e && data[end - 5] === 0x44)) {
      throw new BuildError("image stops partway: a PNG ends with its IEND chunk and this one does not");
    }
    return ["png", wpx, hpx];
  }
  if (data.length >= 3 && data[0] === 0xff && data[1] === 0xd8 && data[2] === 0xff) {
    let i = 2;
    while (i + 9 <= data.length) {
      if (data[i] !== 0xff) {
        i += 1;
        continue;
      }
      const marker = data[i + 1];
      if (marker === 0xd8 || marker === 0x01 || marker === 0xff || (marker >= 0xd0 && marker <= 0xd7)) {
        i += marker === 0xff ? 1 : 2;
        continue;
      }
      const length = (data[i + 2] << 8) | data[i + 3];
      if ([0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf].includes(marker)) {
        const hpx = (data[i + 5] << 8) | data[i + 6];
        const wpx = (data[i + 7] << 8) | data[i + 8];
        if (!(wpx && hpx)) throw new BuildError("image has no width or height");
        if (!(data[data.length - 2] === 0xff && data[data.length - 1] === 0xd9)) {
          throw new BuildError("image stops partway: a JPEG ends with its end-of-image marker and this one does not");
        }
        return ["jpeg", wpx, hpx];
      }
      if (length < 2) break;
      i += 2 + length;
    }
  }
  throw new BuildError("image is not a PNG or JPEG file (by its bytes, not its name)");
}

function rd32be(b, o) {
  return ((b[o] << 24) | (b[o + 1] << 16) | (b[o + 2] << 8) | b[o + 3]) >>> 0;
}

class Writer {
  constructor(doc, opts, readImage) {
    this.doc = doc;
    this.opts = opts;
    this.readImage = readImage;
    this.rels = [];
    this.media = [];
    this.imageRel = new Map();
    this.docPr = 0;
    this.hasOrderedList = false; // whether --auto-numbering has anything to count (ADR 0028)
    this.imageTwips = 0; // the width the last image was drawn at, for --caption-matches-object
    this.cs = opts.thai_language ? CS_THAI : CS;
    this.csAll = opts.force_cs_whole_doc; // mark every run, as releases before 0.2.0 did
    // a style is not a run: it names the Latin language for an application that reads styles but
    // not docDefaults, and never says complex script, which each run says for itself
    this.styleLang = '<w:lang w:val="en-US"' + (opts.thai_language ? ' w:bidi="th-TH"' : "") + "/>";
    [this.headingProps, this.styleWarnings] = headingStyles(doc);
    [this.items, this.regions, this.layoutWarnings] = layout(doc, opts);
    this.nums = [];
    this.hasChapters = this.regions.includes("chapters") || this.regions.includes("appendices"); // headings Word numbers by region
    this.counts = { headings: 0, paragraphs: 0, list_items: 0, tables: 0, table_rows: 0, code_blocks: 0, images: 0, footnotes: 0, links: 0 };
    const [pw, ph] = pageSize(opts);
    const [top, right, bottom, left] = opts.margins.map((m) => halfUp(m * 1440));
    this.page = [pw, ph, top, right, bottom, left];
    this.textWidthTwips = pw - left - right;
  }

  rel(kind, target, external) {
    const rid = "rId" + (this.rels.length + 1);
    this.rels.push([rid, kind, target, !!external]);
    return rid;
  }

  // What says a run is complex script, or nothing when its text is not.
  marker(complexScript) {
    return complexScript || this.csAll ? this.cs : "";
  }

  // A run's properties, or nothing at all rather than an empty element.
  rpr(props) {
    return props ? "<w:rPr>" + props + "</w:rPr>" : "";
  }

  // `text` as runs, one per stretch of a single script (ADR 0039). Two stretches that end up with
  // the same run properties are one run again: cause 4 of ADR 0004 says contiguous text with the
  // same formatting is one run, and the checker holds the build to it. Under
  // --force-cs-whole-doc every stretch carries the same marker, so this puts the whole text back
  // into the one run releases before 0.2.0 wrote.
  runs(text, props) {
    const grouped = [];
    for (const [complexScript, piece] of scriptRuns(text)) {
      const rpr = this.rpr((props || "") + this.marker(complexScript));
      if (grouped.length && grouped[grouped.length - 1][0] === rpr) grouped[grouped.length - 1][1] += piece;
      else grouped.push([rpr, piece]);
    }
    return grouped.map(([rpr, piece]) =>
      "<w:r>" + rpr + piece.split("\t").map((part) => '<w:t xml:space="preserve">' + esc(part) + "</w:t>").join("<w:tab/>") + "</w:r>"
    ).join("");
  }

  runProps(node, bold) {
    const p = [];
    if (node.link) p.push('<w:rStyle w:val="Hyperlink"/>');
    if (node.code) p.push('<w:rFonts w:ascii="' + CODE_FONT + '" w:hAnsi="' + CODE_FONT + '" w:cs=' + attr(this.opts.font) + "/>");
    if (node.b || bold) p.push("<w:b/><w:bCs/>");
    if (node.i) p.push("<w:i/><w:iCs/>");
    if (node.strike) p.push("<w:strike/>");
    if (node.u) p.push('<w:u w:val="single"/>');
    if (node.sup) p.push('<w:vertAlign w:val="superscript"/>');
    else if (node.sub) p.push('<w:vertAlign w:val="subscript"/>');
    return p.join("");
  }

  textRun(node, bold) {
    return this.runs(node.s, this.runProps(node, bold));
  }

  inlines(nodes, bold) {
    const out = [];
    let i = 0;
    while (i < nodes.length) {
      const n = nodes[i];
      if (n.t === "text" && n.link) {
        let j = i;
        while (j < nodes.length && nodes[j].t === "text" && nodes[j].link === n.link) j++;
        const rid = this.rel(REL + "hyperlink", n.link, true);
        this.counts.links += 1;
        const runs = nodes.slice(i, j).map((x) => this.textRun(x, bold)).join("");
        out.push('<w:hyperlink r:id="' + rid + '" w:history="1">' + runs + "</w:hyperlink>");
        i = j;
        continue;
      }
      const t = n.t;
      if (t === "text") out.push(this.textRun(n, bold));
      else if (t === "hardbreak") out.push("<w:r>" + this.rpr(this.marker(false)) + "<w:br/></w:r>");
      else if (t === "task") {
        const mark = n.checked ? BOX_CHECKED : BOX;
        out.push(this.runs(mark, '<w:rFonts w:ascii="' + SYMBOL_FONT + '" w:hAnsi="' + SYMBOL_FONT + '" w:cs="' + SYMBOL_FONT + '"/>'));
      } else if (t === "footnote_ref") {
        out.push("<w:r>" + this.rpr('<w:rStyle w:val="FootnoteReference"/>' + this.marker(false)) + '<w:footnoteReference w:id="' + n.id + '"/></w:r>');
      } else if (t === "image") {
        out.push(this.image(n));
      }
      i++;
    }
    if (!out.length) out.push(this.runs(""));
    return out.join("");
  }

  image(node) {
    const src = node.src;
    if (/^[A-Za-z][A-Za-z0-9+.-]*:/.test(src)) {
      throw new BuildError("image '" + src + "': remote images are not supported; only local PNG or JPEG files");
    }
    const [path, data] = this.readImage(src);
    if (!this.imageRel.has(path)) {
      const [kind, wpx, hpx] = imageSize(data);
      const n = this.media.length + 1;
      this.media.push(["word/media/image" + n + "." + kind, data]);
      const rid = this.rel(REL + "image", "media/image" + n + "." + kind);
      this.imageRel.set(path, [rid, wpx, hpx]);
      this.counts.images += 1;
    }
    const [rid, wpx, hpx] = this.imageRel.get(path);
    let cx = BigInt(wpx) * BigInt(EMU_PER_PX);
    let cy = BigInt(hpx) * BigInt(EMU_PER_PX);
    const maxCx = BigInt(this.textWidthTwips) * BigInt(EMU_PER_TWIP);
    if (cx > maxCx) {
      cy = (cy * maxCx) / cx;
      cx = maxCx;
    }
    this.imageTwips = Number(cx / BigInt(EMU_PER_TWIP)); // what --caption-matches-object measures against
    this.docPr += 1;
    const k = String(this.docPr);
    return (
      "<w:r>" + this.rpr(this.marker(false)) + "<w:drawing>" +
      '<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="' + cx + '" cy="' + cy + '"/>' +
      '<wp:docPr id="' + k + '" name="Picture ' + k + '" descr=' + attr(node.alt) + "/>" +
      '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">' +
      '<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="Picture ' + k + '"/><pic:cNvPicPr/></pic:nvPicPr>' +
      '<pic:blipFill><a:blip r:embed="' + rid + '"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>' +
      '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="' + cx + '" cy="' + cy + '"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>' +
      "</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>"
    );
  }

  paragraph(inlines, style, ppr, bold, lead) {
    const head = (style ? '<w:pStyle w:val="' + style + '"/>' : "") + (ppr || "");
    this.counts.paragraphs += 1;
    return "<w:p><w:pPr>" + head + this.latinJc(head, inlineText(inlines)) + "</w:pPr>" + (lead || "") + this.inlines(inlines, !!bold) + "</w:p>";
  }

  // Thai distributed fills a line by spreading what is on it, which is how Thai is set — it
  // has no spaces between words — and not how English is: a paragraph with no Thai in it keeps
  // the ordinary left alignment, so "(2024a)" does not come out as "( 2 0 2 4 a)" and a title
  // does not stretch across the page. Alignment only — ADR 0023 stands.
  latinJc(head, text) {
    if (this.opts.align !== "thai" || head.includes("<w:jc ") || !text || hasThai(text)) return "";
    const style = RE_PSTYLE.exec(head);
    if (style !== null && STYLE_FIXES_ALIGNMENT.has(style[1])) return "";
    return '<w:jc w:val="left"/>';
  }

  // --chapter-title-on-new-line: the number keeps the first line and the heading's own text
  // starts the next one.
  titleBreak(item) {
    if (!this.opts.chapter_title_on_new_line || item.number === undefined) return "";
    return "<w:r>" + this.rpr(this.marker(false)) + "<w:br/></w:r>";
  }

  // Whether the build writes this document's numbers itself (ADR 0036). One answer for the
  // whole document, never a number here and a field there: a document that renumbers its
  // headings but not its captions goes wrong silently the first time a reader inserts a
  // chapter. The build writes them unless --auto-numbering asks otherwise, because a written
  // number reads the same in all five applications and a counted one does not: LibreOffice
  // draws thaiNumbers as 1, 2, 3, and answers a caption's STYLEREF with the chapter's title.
  // With --auto-numbering the application counts, whole, and references/numbering.md says
  // what each of the other four draws.
  numbersAreText() {
    return !this.opts.auto_numbering;
  }

  // A field and the result the build already knows, between `separate` and `end`.
  fieldRuns(instr, result, rpr) {
    return (
      "<w:r>" + this.rpr(rpr + this.marker(false)) + '<w:fldChar w:fldCharType="begin"/></w:r>' +
      "<w:r>" + this.rpr(rpr + this.marker(false)) + '<w:instrText xml:space="preserve"> ' + instr + " </w:instrText></w:r>" +
      "<w:r>" + this.rpr(rpr + this.marker(false)) + '<w:fldChar w:fldCharType="separate"/></w:r>' +
      this.runs(result, rpr) +
      "<w:r>" + this.rpr(rpr + this.marker(false)) + '<w:fldChar w:fldCharType="end"/></w:r>'
    );
  }

  // Heading levels the numbering part numbers.
  numberedLevels() {
    const rest = this.opts.heading_numbers ? [2, 3, 4, 5, 6] : [];
    if (this.hasChapters) return new Set([1, ...rest]);
    return new Set(this.opts.heading_numbers ? [1, ...rest] : []);
  }

  headingNumId() {
    return this.nums.length + 2;
  }

  // A heading's inlines and what goes before them: its number, written into the paragraph as
  // text (ADR 0036). The number carries no run properties of its own, so it takes the heading
  // style's. Where the first word is unformatted the number joins its run rather than sitting
  // in one beside it, formatted alike (cause 4).
  numberedHeading(item) {
    const b = item.block;
    const inlines = b.inlines;
    if (!this.numbersAreText()) {
      // the numbering part numbers the heading, through its style or its own list
      let ppr = "";
      if (this.regions.length && item.region !== "chapters" && this.numberedLevels().has(b.level)) {
        // appendices take their own list ("ภาคผนวก ก"); headings in any other region, none
        ppr = item.region === "appendices"
          ? '<w:numPr><w:ilvl w:val="' + (b.level - 1) + '"/><w:numId w:val="' + (this.headingNumId() + 1) + '"/></w:numPr>'
          : '<w:numPr><w:numId w:val="0"/></w:numPr>';
      }
      return [inlines, ppr, this.titleBreak(item)];
    }
    if (item.number === undefined) return [inlines, "", ""];
    const brk = this.titleBreak(item);
    if (!brk && inlines.length && inlines[0].t === "text" && !isFormatted(inlines[0])) {
      return [[{ ...inlines[0], s: item.number + " " + inlines[0].s }, ...inlines.slice(1)], "", ""];
    }
    const text = brk ? item.number : item.number + " ";
    return [inlines, "", this.runs(text) + brk];
  }

  // `body` marks the document's own top level: only its paragraphs take the first-line
  // indent — not headings, lists, quotes, tables, code or footnotes.
  // The document's own top level, as layout() arranged it: sections apart by
  // SECTION_MARK, captions, directives, and headings outside the chapters unnumbered.
  body() {
    const out = [];
    for (const item of this.items) {
      const b = item.block;
      if (item.new_section) out.push(SECTION_MARK);
      if (item.caption) {
        out.push(this.caption(item.caption, Boolean(item.keep_next)));
      } else if (b.t === "directive") {
        out.push(this.field(LIST_FIELDS[b.name], "", listEntries(this.items, b.name)));
      } else if (b.t === "heading") {
        this.counts.headings += 1;
        const [inlines, ppr, lead] = this.numberedHeading(item);
        out.push(this.paragraph(inlines, "Heading" + b.level, ppr, false, lead));
      } else {
        out.push(this.blocks([b], 0, false, true, Boolean(item.keep_next)));
      }
    }
    return out.join("");
  }

  // Label and number, bold, then the caption text. Where the document's numbers are the
  // build's own (ADR 0036) the number is text. With --auto-numbering it is the pair of fields
  // Word's own Insert Caption writes — the chapter from a STYLEREF, the count from a SEQ named
  // after the label and starting again at each chapter, in Thai digits when those are asked for
  // — with the results written in, so an application that never updates fields still shows them.
  // settings.xml carries the label itself (captionsXml).
  caption(c, keepNext) {
    this.counts.paragraphs += 1;
    const bold = "<w:b/><w:bCs/>";
    const run = (text, rpr) => this.runs(text, rpr);
    // --caption-hanging-indent: the label and number keep the margin and every line after the
    // first is indented, so a caption that runs on reads as one block beside its number
    const hang = halfUp(this.opts.caption_hanging_indent * 1440);
    const [boxLeft, boxRight] = this.captionBox(c);
    const attrs = (boxLeft + hang ? ' w:left="' + (boxLeft + hang) + '"' : "") + (boxRight ? ' w:right="' + boxRight + '"' : "");
    const ind = attrs || hang ? "<w:ind" + attrs + (hang ? ' w:hanging="' + hang + '"' : "") + "/>" : "";
    let ppr = '<w:pStyle w:val="' + CAPTION_STYLE[c.kind] + '"/>' + (keepNext ? "<w:keepNext/>" : "") + ind +
      (c.kind === "figure" ? '<w:jc w:val="center"/>' : "");
    ppr += this.latinJc(ppr, captionText(c));
    const rest = c.inlines;
    if (!this.numbersAreText()) {
      let plain = "<w:p><w:pPr>" + ppr + "</w:pPr>" + run(c.label + " ", bold);
      if (c.chapter) plain += this.fieldRuns("STYLEREF 1 \\s", c.chapter, bold) + run("-", bold);
      // the counter is named after the label, which is what Word's own Insert Caption names it:
      // a caption a reader inserts then continues this document's numbering instead of
      // starting a second count beside it
      const seq = "SEQ " + c.label + " \\* " + (this.opts.thai_digits ? "ThaiArabic" : "ARABIC") +
        (c.reset ? " \\s 1" : "");
      plain += this.fieldRuns(seq, c.seq, bold);
      if (rest.length && rest[0].t === "text") plain += this.inlines([{ ...rest[0], s: " " + rest[0].s }, ...rest.slice(1)]);
      else if (rest.length) plain += run(" ", "") + this.inlines(rest);
      return plain + "</w:p>";
    }
    const head = c.label + " " + ((c.chapter ? c.chapter + "-" : "") + c.seq);
    if (rest.length && rest[0].t === "text" && isBoldOnly(rest[0])) {
      // the caption opens in bold, as the label does: one run, or two formatted alike (cause 4)
      return "<w:p><w:pPr>" + ppr + "</w:pPr>" + this.inlines([{ ...rest[0], s: head + " " + rest[0].s }, ...rest.slice(1)]) + "</w:p>";
    }
    let out = "<w:p><w:pPr>" + ppr + "</w:pPr>" + run(head, bold);
    if (rest.length && rest[0].t === "text") {
      // the space joins the first text run: a run of its own would sit beside one formatted alike (cause 4)
      out += this.inlines([{ ...rest[0], s: " " + rest[0].s }, ...rest.slice(1)]);
    } else if (rest.length) {
      out += run(" ", "") + this.inlines(rest);
    }
    return out + "</w:p>";
  }

  // The indents that make a caption as wide as the picture it belongs to, in twips
  // (--caption-matches-object), or [0, 0] for a caption that fills the text width. Only a
  // picture: a table is written at the full width of the text, so its caption already ends
  // where it does. The width is the one the image was drawn at — its own, or the text width
  // where the picture was wider — and where --center-images centres the picture the slack is
  // split, so the caption's box is the picture's box. The width is the last picture written,
  // which is this caption's: a Figure: caption is made only where the paragraph just before it
  // holds a picture and nothing else (48-layout.js).
  captionBox(c) {
    if (!(this.opts.caption_matches_object && c.kind === "figure" && this.imageTwips)) return [0, 0];
    const slack = Math.max(this.textWidthTwips - this.imageTwips, 0);
    const left = this.opts.center_images ? Math.floor(slack / 2) : 0;
    return [left, slack - left];
  }

  blocks(blocks, level, quote, body, keepNext) {
    level = level || 0;
    const out = [];
    const firstLine = body ? halfUp(this.opts.indent * 1440) : 0;
    for (const b of blocks) {
      const t = b.t;
      const ind = level ? '<w:ind w:left="' + 720 * level + '"/>' : "";
      if (t === "heading") {
        this.counts.headings += 1;
        out.push(this.paragraph(b.inlines, "Heading" + b.level));
      } else if (t === "paragraph") {
        if (this.opts.center_images && imageOnly(b)) {
          // a picture on a line of its own is centred, and takes no first-line indent: an
          // indent would move it off the centre its caption is measured against
          out.push(this.paragraph(b.inlines, null, (keepNext ? "<w:keepNext/>" : "") + '<w:jc w:val="center"/>'));
          continue;
        }
        const ppr = (keepNext ? "<w:keepNext/>" : "") + (firstLine ? '<w:ind w:firstLine="' + firstLine + '"/>' : ind);
        out.push(this.paragraph(b.inlines, quote ? "Quote" : level ? "ListParagraph" : null, ppr));
      } else if (t === "code") {
        this.counts.code_blocks += 1;
        for (const line of b.lines.length ? b.lines : [""]) {
          out.push(this.paragraph([{ t: "text", s: line }], "CodeBlock", ind));
        }
      } else if (t === "quote") {
        out.push(this.blocks(b.blocks, level, true));
      } else if (t === "break") {
        this.counts.paragraphs += 1;
        out.push('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="808080"/></w:pBdr></w:pPr></w:p>');
      } else if (t === "list") {
        out.push(this.list(b, level, quote));
      } else if (t === "table") {
        out.push(this.table(b));
      }
    }
    return out.join("");
  }

  // A bullet is drawn by the numbering part, which every application reads the same way. An
  // ordered list's number is written as text instead (ADR 0036): its format is one a reader may
  // not have — LibreOffice draws thaiNumbers as 1, 2, 3 — and the hanging indent and the tab
  // after the marker put it where the numbering put it.
  list(b, level, quote) {
    const out = [];
    const written = this.numbersAreText();
    this.hasOrderedList = this.hasOrderedList || b.ordered;
    let numId = 0;
    if (b.ordered && !written) {
      numId = this.nums.length + 2;
      this.nums.push([numId, b.start, level]);
    }
    const indent = '<w:ind w:left="' + 720 * (level + 1) + '" w:hanging="360"/>';
    for (let n = 0; n < b.items.length; n++) {
      const item = b.items[n];
      this.counts.list_items += 1;
      let first, rest;
      if (item.length && item[0].t === "paragraph") {
        first = item[0].inlines;
        rest = item.slice(1);
      } else {
        first = [];
        rest = item;
      }
      let ppr, lead = "";
      if (first.length && first[0].t === "task") {
        ppr = '<w:ind w:left="' + 720 * (level + 1) + '"/>';
      } else if (b.ordered && !written) {
        ppr = '<w:numPr><w:ilvl w:val="' + Math.min(level, 8) + '"/><w:numId w:val="' + numId + '"/></w:numPr>';
      } else if (b.ordered) {
        const marker = numberText(b.start + n, "decimal", this.opts.thai_digits) + ".";
        ppr = indent;
        lead = this.runs(marker) + "<w:r>" + this.rpr(this.marker(false)) + "<w:tab/></w:r>";
      } else {
        ppr = '<w:numPr><w:ilvl w:val="' + Math.min(level, 8) + '"/><w:numId w:val="1"/></w:numPr>';
      }
      out.push(this.paragraph(first, "ListParagraph", ppr, false, lead));
      out.push(this.blocks(rest, level + 1, quote));
    }
    return out.join("");
  }

  // Twips per column, filling the text width. `auto`: each column a quarter of an equal
  // share, and the rest shared by the longest line of text the column holds.
  columnWidths(b) {
    const n = b.aligns.length;
    const width = this.textWidthTwips;
    if (this.opts.table_widths === "equal") return new Array(n).fill(Math.floor(width / n));
    const need = new Array(n).fill(1);
    for (const row of b.rows) {
      row.forEach((cell, ci) => {
        for (const line of inlineText(cell).split("\n")) {
          let count = 0;
          for (const c of line) if (!THAI_MARKS.has(c.codePointAt(0))) count += 1;
          need[ci] = Math.max(need[ci], count);
        }
      });
    }
    const floor = Math.floor(width / (4 * n));
    const spare = width - floor * n;
    const total = need.reduce((a, k) => a + k, 0);
    const widths = need.map((k) => floor + Math.floor((spare * k) / total));
    widths[n - 1] += width - widths.reduce((a, k) => a + k, 0);
    return widths;
  }

  table(b) {
    this.counts.tables += 1;
    const widths = this.columnWidths(b);
    const grid = widths.map((col) => '<w:gridCol w:w="' + col + '"/>').join("");
    const borders = ["top", "left", "bottom", "right", "insideH", "insideV"].map((s) => "<w:" + s + ' w:val="single" w:sz="4" w:space="0" w:color="808080"/>').join("");
    const rows = [];
    b.rows.forEach((row, ri) => {
      this.counts.table_rows += 1;
      const cells = row.map((cell, ci) => {
        const jc = b.aligns[ci];
        // no space after: the body's 6 pt would leave every row taller than its text
        const ppr = (this.opts.table_size !== null ? '<w:pStyle w:val="TableText"/>' : "") + '<w:spacing w:after="0"/>' + (jc === "center" || jc === "right" ? '<w:jc w:val="' + jc + '"/>' : "");
        return '<w:tc><w:tcPr><w:tcW w:w="' + widths[ci] + '" w:type="dxa"/></w:tcPr>' + this.paragraph(cell, null, ppr, ri === 0) + "</w:tc>";
      });
      rows.push("<w:tr>" + (ri === 0 && this.opts.repeat_table_header ? "<w:trPr><w:tblHeader/></w:trPr>" : "") + cells.join("") + "</w:tr>");
    });
    return (
      '<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders>' + borders + "</w:tblBorders>" +
      '<w:tblLayout w:type="autofit"/>' + CELL_MARGINS + "</w:tblPr><w:tblGrid>" + grid + "</w:tblGrid>" + rows.join("") + "</w:tbl>" +
      "<w:p><w:pPr/></w:p>"
    );
  }

  // A field paragraph, and — for a list of contents, tables or figures — the entries it
  // already holds between `separate` and `end`, one paragraph each (ADR 0027). The field
  // opens in the first entry and closes in the last, as Word writes it.
  field(instr, ppr, entries) {
    const char = (kind) => "<w:r>" + this.rpr(this.marker(false)) + '<w:fldChar w:fldCharType="' + kind + '"/></w:r>';
    const instruction = "<w:r>" + this.rpr(this.marker(false)) + '<w:instrText xml:space="preserve"> ' + instr + " </w:instrText></w:r>";
    if (!entries || !entries.length) {
      return "<w:p><w:pPr>" + (ppr || "") + "</w:pPr>" + char("begin") + instruction + char("separate") + char("end") + "</w:p>";
    }
    this.counts.paragraphs += entries.length;
    const out = [];
    entries.forEach(([level, text], i) => {
      const opening = i === 0 ? char("begin") + instruction + char("separate") : "";
      const closing = i === entries.length - 1 ? char("end") : "";
      const entryPpr = '<w:pStyle w:val="TOC' + Math.min(level, 3) + '"/>';
      out.push(
        "<w:p><w:pPr>" + entryPpr + this.latinJc(entryPpr, text) + "</w:pPr>" + opening +
        this.runs(text) + closing + "</w:p>"
      );
    });
    return out.join("");
  }
}
