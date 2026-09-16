// thai-docx — build: the JavaScript port of scripts/thai_docx/build.py. The same
// Markdown, images and settings give the same bytes (ADR 0008).

const PAPER = { a4: [11906, 16838], letter: [12240, 15840], f14: [12240, 18720] }; // f14: 8.5 x 13 in, folio
const PAGE_NUMBERS = ["top-right", "top-center", "bottom-center"]; // the first is --page-numbers with no position
const DEFAULTS = {
  font: "TH Sarabun New",
  size: 16,
  paper: "a4",
  landscape: false,
  margins: [1.0, 1.0, 1.0, 1.5],
  indent: 0.0,
  line_spacing: 1.0, // multiple of single spacing; code and footnotes stay single
  align: "left",
  toc: false,
  heading_numbers: false, // 1. / 1.1 / 1.1.1 from # down, numbered by Word
  page_numbers: false, // or where the number goes: one of PAGE_NUMBERS
  page_number_on_first: true, // false leaves the first page without its number
  header: null, // text centred at the top of every page
  footer: null, // text centred at the bottom of every page
  thai_digits: false, // page, list and footnote numbers Word generates; never the text
  hide_spelling_errors: false,
  repeat_table_header: true, // the header row of every table repeats on each page
  table_widths: "equal", // or "auto": by the longest text in each column
  table_size: null, // points for the text in table cells; null: the body size
  chapter_label: "บทที่", // before the chapter number, in <!-- chapters --> (ADR 0021)
  table_label: "ตารางที่", // before a table caption's number
  figure_label: "รูปที่", // before a figure caption's number
  front_page_numbers: "thai-letters", // page numbers before the chapters: one of FRONT_NUMBERS
  appendix_label: "ภาคผนวก", // before an appendix number, in <!-- appendices -->
  appendix_numbers: "thai-letters", // one of APPENDIX_NUMBERS
  chapter_title_on_new_line: false, // "บทที่ 1" on its own line, the title under it (ADR 0027)
};
const CODE_FONT = "Consolas";
const SYMBOL_FONT = "Segoe UI Symbol";
const NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships";
const REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/";
const XML_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n';
const EMU_PER_PX = 9525;
const EMU_PER_TWIP = 635;
let LANG = '<w:cs/><w:lang w:val="en-US" w:bidi="th-TH"/>';
const MIN_TEXT_TWIPS = 1440;
// Thai marks above and below a consonant take no width of their own when a column is measured
const THAI_MARKS = new Set([0x0e31, 0x0e34, 0x0e35, 0x0e36, 0x0e37, 0x0e38, 0x0e39, 0x0e3a, 0x0e47, 0x0e48, 0x0e49, 0x0e4a, 0x0e4b, 0x0e4c, 0x0e4d, 0x0e4e]);
// Word's own table default; with no table style it would otherwise be 0 and text touches the borders
const CELL_MARGINS = '<w:tblCellMar><w:left w:w="108" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar>';
const USAGE = "usage: thai_docx build IN.md OUT.docx [--font NAME] [--size PT] [--paper a4|letter|f14] [--landscape] [--margins T,R,B,L] [--indent IN] [--line-spacing N] [--align left|thai] [--toc] [--heading-numbers] [--page-numbers [top-right|top-center|bottom-center]] [--no-page-number-first] [--header TEXT] [--footer TEXT] [--chapter-label TEXT] [--table-label TEXT] [--figure-label TEXT] [--front-page-numbers thai-letters|lower-roman|upper-roman|decimal] [--appendix-label TEXT] [--appendix-numbers thai-letters|upper-letters|decimal|upper-roman] [--chapter-title-on-new-line] [--thai-digits] [--hide-spelling-errors] [--table-widths equal|auto] [--table-size PT] [--no-repeat-table-header] [--profile NAME|PATH] [--allow-dir DIR]";
const NUMBER = /^[0-9]+(?:\.[0-9]+)?$/;

class BuildError extends Error {
  constructor(what) {
    super(what);
    this.what = what;
  }
}

function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function attr(s) {
  return '"' + esc(s).replace(/"/g, "&quot;").replace(/\t/g, "&#9;").replace(/\n/g, "&#10;").replace(/\r/g, "&#13;") + '"';
}

// Width and height in twips; landscape turns the paper, the margins stay top, right, bottom, left.
function pageSize(opts) {
  const [pw, ph] = PAPER[opts.paper];
  return opts.landscape ? [ph, pw] : [pw, ph];
}

function halfUp(x) {
  return Math.floor(x + 0.5);
}

function imageSize(data) {
  const sig = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
  if (data.length >= 24 && sig.every((v, i) => data[i] === v) && data[12] === 0x49 && data[13] === 0x48 && data[14] === 0x44 && data[15] === 0x52) {
    const wpx = rd32be(data, 16);
    const hpx = rd32be(data, 20);
    if (wpx && hpx) return ["png", wpx, hpx];
    throw new BuildError("image has no width or height");
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
        if (wpx && hpx) return ["jpeg", wpx, hpx];
        throw new BuildError("image has no width or height");
      }
      if (length < 2) break;
      i += 2 + length;
    }
  }
  throw new BuildError("image is not a PNG or JPEG file (by its bytes, not its name)");
}

// --- heading styles from front matter (ADR 0020) ---

const HEADING_KEY = /^heading-([1-6])$/;
const NEAR_HEADING_KEY = /^(?:h|heading)[-_ ]?[0-9]+$/i; // a slip worth a warning
const LENGTH = /^(-?)([0-9]+(?:\.[0-9]+)?)(in|cm|pt)$/;
const POINTS = /^([0-9]+(?:\.[0-9]+)?)pt$/;
const COLOR = /^#[0-9A-Fa-f]{6}$/;
const MAX_LENGTH_TWIPS = 14400; // 10 in
const ALIGN = { left: "left", center: "center", right: "right", justify: "both", "thai-distribute": "thaiDistribute" };
const UNDERLINE = { solid: "single", double: "double", dotted: "dotted", dashed: "dash", wavy: "wave", thick: "thick" }; // thick: Word's, not CSS
const HEADING_PROPERTIES = [
  "font-family", "font-size", "color", "font-weight", "font-style", "text-decoration", "text-align",
  "margin-left", "text-indent", "margin-top", "margin-bottom", "line-height", "page-break-before",
];
const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);

// `name: value; name: value` — `;` inside double quotes belongs to the value.
function declarations(value, line, key) {
  const pieces = [];
  let current = "";
  let quoted = false;
  for (const ch of value) {
    if (ch === '"') quoted = !quoted;
    if (ch === ";" && !quoted) {
      pieces.push(current);
      current = "";
    } else {
      current += ch;
    }
  }
  if (quoted) throw new Unsupported(line, key + ": a double quote is not closed");
  pieces.push(current);
  const out = [];
  for (let piece of pieces) {
    piece = stripChars(piece, " \t");
    if (!piece) continue;
    const colon = piece.indexOf(":");
    if (colon < 0) throw new Unsupported(line, key + ": '" + piece + "' is not a property: value pair");
    out.push([stripChars(piece.slice(0, colon), " \t"), stripChars(piece.slice(colon + 1), " \t")]);
  }
  return out;
}

function cssLength(val, line, where, negative) {
  const m = LENGTH.exec(val);
  if (val === "0") return 0;
  if (m === null || (m[1] && !negative)) {
    throw new Unsupported(line, where + " takes a length in in, cm or pt" + (negative ? "" : " that is not negative") + ", e.g. 0.5in");
  }
  const x = Number(m[2]);
  const twips = m[3] === "in" ? halfUp(x * 1440) : m[3] === "cm" ? halfUp((x * 1440) / 2.54) : halfUp(x * 20);
  if (twips > MAX_LENGTH_TWIPS) throw new Unsupported(line, where + " is at most 10in");
  return m[1] ? -twips : twips;
}

// `heading-1` … `heading-6` in the front matter → Map level → properties, and warnings
// for keys that look meant as one. A property or value outside ADR 0020 stops the build.
function headingStyles(doc) {
  const styles = new Map();
  const warnings = [];
  const decoration = " takes none, or underline and line-through, the underline solid, double, dotted, dashed, wavy or thick";
  for (const [key, value] of doc.frontMatter) {
    const line = doc.frontMatterLines.get(key);
    const m = HEADING_KEY.exec(key);
    if (m === null) {
      if (NEAR_HEADING_KEY.test(key)) warnings.push("line " + line + ": front matter key '" + key + "' is not used; heading styles are heading-1 to heading-6");
      continue;
    }
    const props = {};
    for (let [name, val] of declarations(value, line, key)) {
      const where = key + ": " + name;
      if (name === "font-family") {
        if (val.length >= 2 && val[0] === val[val.length - 1] && (val[0] === '"' || val[0] === "'")) val = val.slice(1, -1);
        let bad = !val || codePointLength(val) > 64 || val.includes('"');
        for (const c of val) if (forbiddenChar(c) !== null) bad = true;
        if (bad) throw new Unsupported(line, where + " takes a font name of 1 to 64 characters");
        props.font = val;
      } else if (name === "font-size") {
        const pm = POINTS.exec(val);
        if (pm === null || !(Number(pm[1]) >= 1 && Number(pm[1]) <= 400)) throw new Unsupported(line, where + " takes points from 1pt to 400pt, e.g. 20pt");
        props.size = Number(pm[1]);
      } else if (name === "color") {
        if (!COLOR.test(val)) throw new Unsupported(line, where + " takes #RRGGBB, e.g. #1F4E79");
        props.color = val.slice(1).toUpperCase();
      } else if (name === "font-weight") {
        if (val !== "bold" && val !== "normal") throw new Unsupported(line, where + " takes bold or normal");
        props.bold = val === "bold";
      } else if (name === "font-style") {
        if (val !== "italic" && val !== "normal") throw new Unsupported(line, where + " takes italic or normal");
        props.italic = val === "italic";
      } else if (name === "text-decoration") {
        // CSS's `line || style`, in any order; the style is the underline's (Word has no styled strike)
        const words = val.split(/[ \t]+/).filter((x) => x);
        let under = false;
        let strike = false;
        let style = null;
        let bad = !words.length;
        for (const word of words.length === 1 && words[0] === "none" ? [] : words) {
          if (word === "underline" && !under) under = true;
          else if (word === "line-through" && !strike) strike = true;
          else if (has(UNDERLINE, word) && style === null) style = UNDERLINE[word];
          else bad = true;
        }
        if (bad || (style && !under)) throw new Unsupported(line, where + decoration);
        props.underline = under ? style || "single" : null;
        props.strike = strike;
      } else if (name === "text-align") {
        if (!has(ALIGN, val)) throw new Unsupported(line, where + " takes left, center, right, justify or thai-distribute");
        props.jc = ALIGN[val];
      } else if (name === "margin-left") {
        props.left = cssLength(val, line, where, false);
      } else if (name === "text-indent") {
        props.first = cssLength(val, line, where, true);
      } else if (name === "margin-top") {
        props.before = cssLength(val, line, where, false);
      } else if (name === "margin-bottom") {
        props.after = cssLength(val, line, where, false);
      } else if (name === "line-height") {
        if (!NUMBER.test(val) || !(Number(val) >= 1 && Number(val) <= 3)) throw new Unsupported(line, where + " takes a multiple of single spacing from 1 to 3");
        props.line = halfUp(Number(val) * 240);
      } else if (name === "page-break-before") {
        if (val !== "always" && val !== "auto") throw new Unsupported(line, where + " takes always or auto");
        props.break = val === "always";
      } else {
        throw new Unsupported(line, key + ": unknown property '" + name + "'; the heading properties are " + HEADING_PROPERTIES.join(", "));
      }
    }
    styles.set(Number(m[1]), props);
  }
  return [styles, warnings];
}

// --- regions, sections and captions (ADR 0021) ---

const REGIONS = ["front", "chapters", "back", "appendices"];
const ORDER = "front, chapters, back, appendices, back"; // a second back only after the appendices
// page numbers before the chapters, and appendix numbers: flag value → Word's number format
const FRONT_NUMBERS = { "thai-letters": "thaiLetters", "lower-roman": "lowerRoman", "upper-roman": "upperRoman", decimal: "decimal" };
const APPENDIX_NUMBERS = { "thai-letters": "thaiLetters", "upper-letters": "upperLetter", decimal: "decimal", "upper-roman": "upperRoman" };
function hasThai(text) {
  for (const ch of text) if (ch >= "\u0e00" && ch <= "\u0e7f") return true;
  return false;
}

const THAI_LETTERS = [..."กขคงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ"]; // as appendices are lettered: no ฃ or ฅ
const ROMAN = [[1000, "M"], [900, "CM"], [500, "D"], [400, "CD"], [100, "C"], [90, "XC"], [50, "L"], [40, "XL"], [10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"]];

// n in a chapter or appendix number format, as the caption's field result shows it.
function numberText(n, fmt, thai) {
  if (fmt === "thai-letters") return THAI_LETTERS[(n - 1) % THAI_LETTERS.length].repeat(Math.floor((n - 1) / THAI_LETTERS.length) + 1);
  if (fmt === "upper-letters") return String.fromCharCode(65 + ((n - 1) % 26)).repeat(Math.floor((n - 1) / 26) + 1);
  if (fmt === "upper-roman") {
    let out = "";
    for (const [value, letters] of ROMAN) {
      while (n >= value) {
        out += letters;
        n -= value;
      }
    }
    return out;
  }
  return thai ? thaiDigits(String(n)) : String(n);
}
const SECTION_MARK = "\x00"; // between sections in the body; the input can hold no control character
const LIST_FIELDS = { toc: 'TOC \\o "1-3" \\h \\z \\u', "list-of-tables": 'TOC \\h \\z \\c "Table"', "list-of-figures": 'TOC \\h \\z \\c "Figure"' };
const CAPTION_PREFIX = { table: "Table:", figure: "Figure:" };
const PLAIN_KEYS = ["link", "code", "b", "i", "strike", "u", "sup", "sub"];
const thaiDigits = (s) => s.replace(/[0-9]/g, (d) => "๐๑๒๓๔๕๖๗๘๙"[Number(d)]);

// "table" or "figure" for a paragraph that opens with plain `Table:` or `Figure:`.
function captionKind(b) {
  if (b.t !== "paragraph" || !b.inlines.length) return null;
  const first = b.inlines[0];
  if (first.t !== "text" || PLAIN_KEYS.some((k) => first[k])) return null;
  for (const kind of ["table", "figure"]) {
    const prefix = CAPTION_PREFIX[kind];
    const s = first.s;
    if (s.startsWith(prefix) && (s.length === prefix.length || s[prefix.length] === " " || s[prefix.length] === "\t")) return kind;
  }
  return null;
}

function captionRest(b, kind) {
  const first = b.inlines[0];
  const s = first.s.slice(CAPTION_PREFIX[kind].length).replace(/^[ \t]+/, "");
  return (s ? [{ ...first, s }] : []).concat(b.inlines.slice(1));
}

// `Figure:` on the line under an image, with no blank line: one paragraph, no caption.
function figureInImageParagraph(b) {
  if (b.t !== "paragraph") return false;
  let seenImage = false;
  for (const n of b.inlines) {
    if (n.t === "image") seenImage = true;
    else if (n.t === "hardbreak" || (n.t === "text" && !stripChars(n.s, " \t"))) continue;
    else if (n.t === "text" && seenImage && !PLAIN_KEYS.some((k) => n[k])) {
      const s = n.s.replace(/^[ \t]+/, "");
      return s.startsWith("Figure:") && (s.length === 7 || s[7] === " " || s[7] === "\t");
    } else return false;
  }
  return false;
}

// `Table:` on the line under a table, with no blank line: the table's last row.
function tableEndsInCaption(b) {
  if (b.t !== "table" || b.rows.length < 2) return false;
  const last = b.rows[b.rows.length - 1];
  return last[0].length > 0 && captionKind({ t: "paragraph", inlines: last[0] }) === "table" && !last.slice(1).some((cell) => cell.length);
}

function imageOnly(b) {
  return b.t === "paragraph" && b.inlines.some((n) => n.t === "image") &&
    b.inlines.every((n) => n.t === "image" || (n.t === "text" && !stripChars(n.s, " \t")));
}

// The top-level blocks as ADR 0021 arranges them → [items, the region of each section,
// warnings]. No region comment: no sections, and captions numbered through the document.
function layout(doc, opts) {
  const seen = [];
  const ranks = [];
  for (const b of doc.blocks) {
    if (b.t === "directive" && REGIONS.includes(b.name)) {
      const rank = b.name === "back" && seen.includes("appendices") ? 4 : REGIONS.indexOf(b.name);
      if (ranks.includes(rank)) {
        const again = b.name === "back" ? "; a second <!-- back --> comes only after <!-- appendices -->" : "; each region comment comes once";
        throw new Unsupported(b.line, "<!-- " + b.name + " --> is given twice" + again);
      }
      if (ranks.length && rank < ranks[ranks.length - 1]) {
        throw new Unsupported(b.line, "<!-- " + b.name + " --> comes after <!-- " + seen[seen.length - 1] + " -->; the regions go " + ORDER);
      }
      seen.push(b.name);
      ranks.push(rank);
    }
  }
  const sectioned = seen.length > 0;
  const items = [];
  const regions = sectioned ? ["cover"] : [];
  const warnings = [];
  let region = "cover";
  let pending = null;
  let hasContent = false;
  let chapter = 0;
  let appendix = 0;
  let counters = { table: 0, figure: 0 };
  const blocks = doc.blocks;
  blocks.forEach((b, i) => {
    if (b.t === "directive" && REGIONS.includes(b.name)) {
      pending = b.name;
      return;
    }
    const heading1 = b.t === "heading" && b.level === 1;
    const item = { block: b, region: pending === null ? region : pending };
    if (sectioned && hasContent && (pending !== null || heading1)) {
      item.new_section = true;
      regions.push(item.region);
    } else if (sectioned && pending !== null) {
      regions[regions.length - 1] = pending;
    }
    region = item.region;
    pending = null;
    hasContent = true;
    if (sectioned && heading1) {
      counters = { table: 0, figure: 0 };
      if (region === "chapters") {
        chapter += 1;
        item.number = opts.chapter_label + " " + numberText(chapter, "decimal", opts.thai_digits);
      } else if (region === "appendices") {
        appendix += 1;
        item.number = opts.appendix_label + " " + numberText(appendix, opts.appendix_numbers, opts.thai_digits);
      }
    }
    let kind = captionKind(b);
    if (kind === "table" && !(i + 1 < blocks.length && blocks[i + 1].t === "table")) {
      warnings.push("line " + b.line + ": 'Table:' makes a caption only in the paragraph just before a table; kept as text");
      kind = null;
    }
    if (kind === "figure" && !(i > 0 && imageOnly(blocks[i - 1]))) {
      warnings.push("line " + b.line + ": 'Figure:' makes a caption only in the paragraph just after an image on its own; kept as text");
      kind = null;
    }
    if (figureInImageParagraph(b)) {
      warnings.push("line " + b.line + ": 'Figure:' shares a paragraph with the image above it; leave a blank line between them to make a caption");
    }
    if (tableEndsInCaption(b)) {
      warnings.push("line " + b.line + ": the table's last row starts with 'Table:'; a caption goes before the table, on its own line");
    }
    if (kind !== null) {
      counters[kind] += 1;
      let chap = "";
      if (region === "chapters" && chapter) chap = numberText(chapter, "decimal", opts.thai_digits);
      else if (region === "appendices" && appendix) chap = numberText(appendix, opts.appendix_numbers, opts.thai_digits);
      const seq = numberText(counters[kind], "decimal", opts.thai_digits);
      item.caption = { kind, label: opts[kind + "_label"], chapter: chap, seq, reset: sectioned, inlines: captionRest(b, kind) };
      if (kind === "table") item.keep_next = true;
      else items[items.length - 1].keep_next = true;
    }
    items.push(item);
  });
  return [items, regions, warnings];
}

// Close a section in the properties of its last top-level paragraph — a table's is the
// empty paragraph after it — so no empty paragraph can spill onto a page of its own.
function endSection(xml, sect) {
  const at = xml.lastIndexOf("<w:p>");
  if (xml.startsWith("<w:p><w:pPr/>", at)) return xml.slice(0, at) + "<w:p><w:pPr>" + sect + "</w:pPr>" + xml.slice(at + "<w:p><w:pPr/>".length);
  const end = xml.indexOf("</w:pPr>", at);
  return xml.slice(0, end) + sect + xml.slice(end);
}

const LIST_KINDS = { "list-of-tables": "table", "list-of-figures": "figure" };

// An entry is one line: a heading broken over two lines reads as one in the list.
function oneLine(text) {
  return text.split("\n").join(" ");
}

// What a table of contents, tables or figures holds, as [heading level, text]. Written
// into the field so an application that never updates fields still shows it; Word, which
// does update, replaces it with its own — with the page numbers only a layout knows
// (ADR 0027).
function listEntries(items, name) {
  const out = [];
  for (const item of items) {
    const b = item.block;
    if (name === "toc") {
      if (!item.caption && b.t === "heading" && b.level <= 3) {
        out.push([b.level, oneLine((item.number === undefined ? "" : item.number + " ") + inlineText(b.inlines))]);
      }
    } else if (item.caption && item.caption.kind === LIST_KINDS[name]) {
      out.push([1, oneLine(captionText(item.caption))]);
    }
  }
  return out;
}

// What a caption paragraph reads as: its label and number, then the Markdown's text.
function captionText(c) {
  const number = (c.chapter ? c.chapter + "-" : "") + c.seq;
  return c.label + " " + number + (c.inlines.length ? " " + inlineText(c.inlines) : "");
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
    this.nums = [];
    this.docPr = 0;
    [this.headingProps, this.styleWarnings] = headingStyles(doc);
    [this.items, this.regions, this.layoutWarnings] = layout(doc, opts);
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
    p.push(LANG);
    return "<w:rPr>" + p.join("") + "</w:rPr>";
  }

  textRun(node, bold) {
    const body = node.s.split("\t").map((piece) => '<w:t xml:space="preserve">' + esc(piece) + "</w:t>").join("<w:tab/>");
    return "<w:r>" + this.runProps(node, bold) + body + "</w:r>";
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
      else if (t === "hardbreak") out.push("<w:r><w:rPr>" + LANG + "</w:rPr><w:br/></w:r>");
      else if (t === "task") {
        const mark = n.checked ? "☑ " : "☐ ";
        out.push('<w:r><w:rPr><w:rFonts w:ascii="' + SYMBOL_FONT + '" w:hAnsi="' + SYMBOL_FONT + '" w:cs="' + SYMBOL_FONT + '"/>' +
          LANG + '</w:rPr><w:t xml:space="preserve">' + mark + "</w:t></w:r>");
      } else if (t === "footnote_ref") {
        out.push('<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/>' + LANG + '</w:rPr><w:footnoteReference w:id="' + n.id + '"/></w:r>');
      } else if (t === "image") {
        out.push(this.image(n));
      }
      i++;
    }
    if (!out.length) out.push("<w:r><w:rPr>" + LANG + '</w:rPr><w:t xml:space="preserve"></w:t></w:r>');
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
    this.docPr += 1;
    const k = String(this.docPr);
    return (
      "<w:r><w:rPr>" + LANG + "</w:rPr><w:drawing>" +
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
    return '<w:jc w:val="left"/>';
  }

  // --chapter-title-on-new-line: the number Word writes keeps the first line and the
  // heading's own text starts the next one. OOXML gives a level no such suffix — nothing, a
  // space or a tab — so the break belongs to the heading (ADR 0027).
  titleBreak(item) {
    if (!this.opts.chapter_title_on_new_line || item.number === undefined) return "";
    return "<w:r><w:rPr>" + LANG + "</w:rPr><w:br/></w:r>";
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
      } else if (b.t === "heading" && this.regions.length && item.region !== "chapters" && this.numberedLevels().has(b.level)) {
        // appendices take their own list ("ภาคผนวก ก"); headings in any other region, none
        this.counts.headings += 1;
        const num = item.region === "appendices"
          ? '<w:numPr><w:ilvl w:val="' + (b.level - 1) + '"/><w:numId w:val="' + (this.headingNumId() + 1) + '"/></w:numPr>'
          : '<w:numPr><w:numId w:val="0"/></w:numPr>';
        out.push(this.paragraph(b.inlines, "Heading" + b.level, num, false, this.titleBreak(item)));
      } else if (b.t === "heading" && this.titleBreak(item)) {
        this.counts.headings += 1;
        out.push(this.paragraph(b.inlines, "Heading" + b.level, "", false, this.titleBreak(item)));
      } else {
        out.push(this.blocks([b], 0, false, true, Boolean(item.keep_next)));
      }
    }
    return out.join("");
  }

  // Label, chapter number and SEQ number, bold, with their results written in — an
  // application that never updates fields still shows them — then the caption text.
  caption(c, keepNext) {
    this.counts.paragraphs += 1;
    const bold = "<w:b/><w:bCs/>";
    const run = (text, rpr) => "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:t xml:space="preserve">' + esc(text) + "</w:t></w:r>";
    let ppr = '<w:pStyle w:val="Caption"/>' + (keepNext ? "<w:keepNext/>" : "") + (c.kind === "figure" ? '<w:jc w:val="center"/>' : "");
    ppr += this.latinJc(ppr, captionText(c));
    let out = "<w:p><w:pPr>" + ppr + "</w:pPr>" + run(c.label + " ", bold);
    if (c.chapter) out += this.fieldRuns("STYLEREF 1 \\s", c.chapter, bold) + run("-", bold);
    const seq = "SEQ " + c.kind[0].toUpperCase() + c.kind.slice(1) + " \\* " + (this.opts.thai_digits ? "ThaiArabic" : "ARABIC") + (c.reset ? " \\s 1" : "");
    out += this.fieldRuns(seq, c.seq, bold);
    const rest = c.inlines;
    if (rest.length && rest[0].t === "text") {
      // the space joins the first text run: a run of its own would sit beside one formatted alike (cause 4)
      out += this.inlines([{ ...rest[0], s: " " + rest[0].s }, ...rest.slice(1)]);
    } else if (rest.length) {
      out += run(" ", "") + this.inlines(rest);
    }
    return out + "</w:p>";
  }

  fieldRuns(instr, result, rpr) {
    return (
      "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:fldChar w:fldCharType="begin"/></w:r>' +
      "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:instrText xml:space="preserve"> ' + instr + " </w:instrText></w:r>" +
      "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:fldChar w:fldCharType="separate"/></w:r>' +
      "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:t xml:space="preserve">' + result + "</w:t></w:r>" +
      "<w:r><w:rPr>" + rpr + LANG + '</w:rPr><w:fldChar w:fldCharType="end"/></w:r>'
    );
  }

  // Heading levels Word numbers: the chapter level whenever there are chapters, the rest with --heading-numbers.
  numberedLevels() {
    const rest = this.opts.heading_numbers ? [2, 3, 4, 5, 6] : [];
    if (this.hasChapters) return new Set([1, ...rest]);
    return new Set(this.opts.heading_numbers ? [1, ...rest] : []);
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

  list(b, level, quote) {
    let numId;
    if (b.ordered) {
      numId = this.nums.length + 2;
      this.nums.push([numId, b.start, level]);
    } else {
      numId = 1;
    }
    const out = [];
    for (const item of b.items) {
      this.counts.list_items += 1;
      let first, rest;
      if (item.length && item[0].t === "paragraph") {
        first = item[0].inlines;
        rest = item.slice(1);
      } else {
        first = [];
        rest = item;
      }
      let ppr;
      if (first.length && first[0].t === "task") ppr = '<w:ind w:left="' + 720 * (level + 1) + '"/>';
      else ppr = '<w:numPr><w:ilvl w:val="' + Math.min(level, 8) + '"/><w:numId w:val="' + numId + '"/></w:numPr>';
      out.push(this.paragraph(first, "ListParagraph", ppr));
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
    const char = (kind) => "<w:r><w:rPr>" + LANG + '</w:rPr><w:fldChar w:fldCharType="' + kind + '"/></w:r>';
    const instruction = "<w:r><w:rPr>" + LANG + '</w:rPr><w:instrText xml:space="preserve"> ' + instr + " </w:instrText></w:r>";
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
        "<w:r><w:rPr>" + LANG + '</w:rPr><w:t xml:space="preserve">' + esc(text) + "</w:t></w:r>" + closing + "</w:p>"
      );
    });
    return out.join("");
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
    const heading = (n, pt, bold, italic) => {
      const p = this.headingProps.get(n) || {};
      const face = has(p, "font") ? attr(p.font) : "";
      if (has(p, "size")) pt = p.size;
      const rpr =
        (face ? "<w:rFonts w:ascii=" + face + " w:hAnsi=" + face + " w:cs=" + face + " w:eastAsia=" + face + "/>" : "") +
        ((has(p, "bold") ? p.bold : bold) ? "<w:b/><w:bCs/>" : "") + ((has(p, "italic") ? p.italic : italic) ? "<w:i/><w:iCs/>" : "") +
        (p.strike ? "<w:strike/>" : "") +
        (has(p, "color") ? '<w:color w:val="' + p.color + '"/>' : "") +
        '<w:sz w:val="' + hp(pt) + '"/><w:szCs w:val="' + hp(pt) + '"/>' +
        (p.underline ? '<w:u w:val="' + p.underline + '"/>' : "");
      const num = this.numberedLevels().has(n) ? '<w:numPr><w:ilvl w:val="' + (n - 1) + '"/><w:numId w:val="' + this.headingNumId() + '"/></w:numPr>' : "";
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
        "<w:pPr><w:keepNext/><w:keepLines/>" + (p.break ? "<w:pageBreakBefore/>" : "") + num + spacing + ind +
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
    if (this.items.some((item) => item.caption)) applied += own("Caption", "caption", '<w:spacing w:before="120" w:after="120"/>');
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
      heading(1, size + 4, true, false) + heading(2, size + 2, true, false) + heading(3, size, true, false) +
      heading(4, size, true, true) + heading(5, size, true, false) + heading(6, size, false, true) +
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

  // After every ordered list's numId, which the body has handed out by the time styles are written.
  headingNumId() {
    return this.nums.length + 2;
  }

  numberingXml() {
    const font = attr(this.opts.font);
    const fmt = this.opts.thai_digits ? "thaiNumbers" : "decimal";
    let bullet = "";
    let decimal = "";
    // a level with no font of its own is drawn in the application's default, which need not
    // carry Thai: WPS showed "บทที่ ๑" as Latin letters until every level named one
    const half = String(halfUp(this.opts.size * 2));
    const levelFont = "<w:rPr><w:rFonts w:ascii=" + font + " w:hAnsi=" + font + " w:cs=" + font + "/>" +
      '<w:sz w:val="' + half + '"/><w:szCs w:val="' + half + '"/>' + LANG + "</w:rPr>";
    for (let l = 0; l < 9; l++) {
      bullet += '<w:lvl w:ilvl="' + l + '"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>' +
        '<w:pPr><w:ind w:left="' + 720 * (l + 1) + '" w:hanging="360"/></w:pPr>' + levelFont + "</w:lvl>";
      decimal += '<w:lvl w:ilvl="' + l + '"><w:start w:val="1"/><w:numFmt w:val="' + fmt + '"/><w:lvlText w:val="%' + (l + 1) + '."/><w:lvlJc w:val="left"/>' +
        '<w:pPr><w:ind w:left="' + 720 * (l + 1) + '" w:hanging="360"/></w:pPr>' + levelFont + "</w:lvl>";
    }
    let nums = '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>' + this.nums.map(([nid, start, level]) =>
      '<w:num w:numId="' + nid + '"><w:abstractNumId w:val="1"/><w:lvlOverride w:ilvl="' + Math.min(level, 8) +
      '"><w:startOverride w:val="' + start + '"/></w:lvlOverride></w:num>').join("");
    let headings = "";
    const levelsOn = this.numberedLevels();
    if (levelsOn.size) {
      // "1." for a # heading — "บทที่ 1" with chapters — then "1.1", "1.1.1" ... followed by a space, no hanging indent
      let levels = "";
      for (let l = 0; l < 9; l++) {
        const text = l === 0 ? (this.hasChapters ? this.opts.chapter_label + " %1" : "%1.") : Array.from({ length: l + 1 }, (_, k) => "%" + (k + 1)).join(".");
        levels += '<w:lvl w:ilvl="' + l + '"><w:start w:val="1"/><w:numFmt w:val="' + fmt + '"/>' +
          (levelsOn.has(l + 1) ? '<w:pStyle w:val="Heading' + (l + 1) + '"/>' : "") +
          '<w:suff w:val="space"/><w:lvlText w:val=' + attr(text) + '/><w:lvlJc w:val="left"/>' + levelFont + "</w:lvl>";
      }
      headings = '<w:abstractNum w:abstractNumId="2"><w:multiLevelType w:val="multilevel"/>' + levels + "</w:abstractNum>";
      nums += '<w:num w:numId="' + this.headingNumId() + '"><w:abstractNumId w:val="2"/></w:num>';
    }
    if (this.regions.includes("appendices")) {
      // "ภาคผนวก ก", then "ก.1", "ก.1.1" with --heading-numbers; set on each heading, linked to no style
      let first = APPENDIX_NUMBERS[this.opts.appendix_numbers];
      if (first === "decimal" && this.opts.thai_digits) first = "thaiNumbers";
      let levels = "";
      for (let l = 0; l < 9; l++) {
        const text = l === 0 ? this.opts.appendix_label + " %1" : Array.from({ length: l + 1 }, (_, k) => "%" + (k + 1)).join(".");
        levels += '<w:lvl w:ilvl="' + l + '"><w:start w:val="1"/><w:numFmt w:val="' + (l === 0 ? first : fmt) + '"/>' +
          '<w:suff w:val="space"/><w:lvlText w:val=' + attr(text) + '/><w:lvlJc w:val="left"/>' + levelFont + "</w:lvl>";
      }
      headings += '<w:abstractNum w:abstractNumId="3"><w:multiLevelType w:val="multilevel"/>' + levels + "</w:abstractNum>";
      nums += '<w:num w:numId="' + (this.headingNumId() + 1) + '"><w:abstractNumId w:val="3"/></w:num>';
    }
    return (
      XML_DECL + '<w:numbering xmlns:w="' + W + '">' +
      '<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="hybridMultilevel"/>' + bullet + "</w:abstractNum>" +
      '<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="hybridMultilevel"/>' + decimal + "</w:abstractNum>" +
      headings + nums + "</w:numbering>"
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
    parts.push(
      "<w:compat>" +
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

function docxText(parts, footnoteCount) {
  const out = [];
  const paragraphs = (root) => {
    for (const p of root.iter(w("p"))) {
      const pieces = [];
      let seen = false;
      let afterMark = false;
      for (const el of p.iter()) {
        const tag = el.tag;
        if (tag === w("footnoteRef")) {
          afterMark = true;
          seen = true;
        } else if (tag === w("t")) {
          pieces.push(el.text || "");
          seen = true;
          afterMark = false;
        } else if (tag === w("tab")) {
          if (!afterMark) pieces.push("\t");
          afterMark = false;
          seen = true;
        } else if (tag === w("br")) {
          pieces.push("\n");
          seen = true;
        } else if (tag === w("drawing")) {
          seen = true;
        }
      }
      if (seen) out.push(pieces.join(""));
    }
  };
  paragraphs(parseXml(fromUtf8(parts.get("word/document.xml"))));
  if (footnoteCount) {
    const root = parseXml(fromUtf8(parts.get("word/footnotes.xml")));
    for (const note of root.iter(w("footnote"))) if (note.get(w("type")) === null) paragraphs(note);
  }
  return out;
}

// `line N: …` messages in line order; messages on one line keep theirs.
function byLine(messages) {
  return messages.map((m, k) => [parseInt(m.split(":")[0].split(" ")[1], 10), k, m]).sort((a, b) => a[0] - b[0] || a[1] - b[1]).map((x) => x[2]);
}

function expectedText(doc, opts) {
  const out = [];
  opts = opts || DEFAULTS;
  const items = layout(doc, opts)[0];
  if (opts.toc) out.push(...listEntries(items, "toc").map(([, text]) => text)); // the entries the field carries
  for (const item of items) {
    if (item.caption) out.push(captionText(item.caption));
    else if (item.block.t === "directive" && LIST_FIELDS[item.block.name] !== undefined) {
      out.push(...listEntries(items, item.block.name).map(([, text]) => text));
    } else if (opts.chapter_title_on_new_line && item.number !== undefined && item.block.t === "heading") {
      out.push(...plainText([item.block]).map((line) => "\n" + line));
    } else out.push(...plainText([item.block]));
  }
  for (const label of doc.footnoteOrder) {
    const blocks = doc.footnotes.get(label);
    if (!blocks.length || blocks[0].t !== "paragraph") out.push("");
    out.push(...plainText(blocks));
  }
  return out.map((s) => s.normalize("NFC"));
}

function settingsJson(opts) {
  const [top, right, bottom, left] = opts.margins;
  return {
    font: opts.font,
    size_pt: Number.isInteger(opts.size) ? opts.size : new PyFloat(opts.size),
    paper: opts.paper,
    landscape: opts.landscape,
    margins_in: { top: new PyFloat(top), right: new PyFloat(right), bottom: new PyFloat(bottom), left: new PyFloat(left) },
    first_line_indent_in: new PyFloat(opts.indent),
    line_spacing: new PyFloat(opts.line_spacing),
    align: opts.align,
    toc: opts.toc,
    heading_numbers: opts.heading_numbers,
    page_numbers: opts.page_numbers,
    page_number_on_first: opts.page_number_on_first,
    header: opts.header,
    footer: opts.footer,
    thai_digits: opts.thai_digits,
    hide_spelling_errors: opts.hide_spelling_errors,
    repeat_table_header: opts.repeat_table_header,
    table_widths: opts.table_widths,
    table_size_pt: opts.table_size === null ? null : Number.isInteger(opts.table_size) ? opts.table_size : new PyFloat(opts.table_size),
    chapter_label: opts.chapter_label,
    table_label: opts.table_label,
    figure_label: opts.figure_label,
    front_page_numbers: opts.front_page_numbers,
    appendix_label: opts.appendix_label,
    appendix_numbers: opts.appendix_numbers,
    chapter_title_on_new_line: opts.chapter_title_on_new_line,
  };
}

// The build from Markdown text to package bytes: [outcome, bytes-or-null].
// `readImage(src)` returns [resolvedPath, Uint8Array] or throws BuildError.
function buildText(text, opts, readImage) {
  let doc, writer, parts;
  try {
    doc = parseMarkdown(text);
    writer = new Writer(doc, opts, readImage);
    parts = writer.pkg();
  } catch (e) {
    if (e instanceof Unsupported) return [{ error: e.what, line: e.line }, null];
    if (e instanceof BuildError) return [{ error: e.what }, null];
    throw e;
  }
  const data = packZip(parts);
  const report = checkBytes(data, "<bytes>");
  const findings = report.findings.slice();
  // a flag that changed nothing is said out loud, never dropped in silence
  const settingsWarnings = [];
  if (opts.chapter_title_on_new_line && !writer.items.some((item) => item.number !== undefined)) {
    settingsWarnings.push("--chapter-title-on-new-line changed nothing: the document has no" +
      " <!-- chapters --> or <!-- appendices --> comment, so no heading carries a number");
  }
  if (!findings.length) {
    const expected = expectedText(doc, opts);
    const actual = docxText(new Map(parts), doc.footnoteOrder.length);
    const same = expected.length === actual.length && expected.every((v, i) => v === actual[i]);
    if (!same) {
      let idx = Math.min(expected.length, actual.length);
      for (let i = 0; i < Math.min(expected.length, actual.length); i++) {
        if (expected[i] !== actual[i]) {
          idx = i;
          break;
        }
      }
      findings.push({ code: "fidelity", part: "word/document.xml",
        message: "paragraph " + (idx + 1) + " does not match the Markdown (" + expected.length + " paragraphs expected, " + actual.length + " written)" });
    }
  }
  const outcome = {
    counts: { ...writer.counts, runs: report.counts.runs || 0 },
    warnings: byLine([...writer.styleWarnings, ...writer.layoutWarnings, ...doc.warnings]).map((m) => ({ code: "markdown", message: m }))
      .concat(settingsWarnings.map((m) => ({ code: "settings", message: m }))).concat(report.warnings),
    findings,
    sha256: sha256Hex(data),
    bytes: data.length,
  };
  return [outcome, findings.length ? null : data];
}

function parseArgs(argv) {
  const opts = { ...DEFAULTS, margins: DEFAULTS.margins.slice() };
  const positional = [];
  const allow = [];
  const valued = ["--font", "--size", "--paper", "--margins", "--indent", "--line-spacing", "--align", "--table-widths", "--table-size", "--header", "--footer", "--chapter-label", "--table-label", "--figure-label", "--front-page-numbers", "--appendix-label", "--appendix-numbers", "--allow-dir"];
  const switches = {
    "--landscape": ["landscape", true], "--toc": ["toc", true], "--heading-numbers": ["heading_numbers", true], "--no-page-number-first": ["page_number_on_first", false],
    "--chapter-title-on-new-line": ["chapter_title_on_new_line", true],
    "--thai-digits": ["thai_digits", true], "--hide-spelling-errors": ["hide_spelling_errors", true],
    "--no-repeat-table-header": ["repeat_table_header", false],
  };
  let i = 0;
  while (i < argv.length) {
    const arg = argv[i];
    if (arg.startsWith("--")) {
      const eqAt = arg.indexOf("=");
      const name = eqAt < 0 ? arg : arg.slice(0, eqAt);
      const eq = eqAt >= 0;
      let value = eq ? arg.slice(eqAt + 1) : "";
      if (name === "--page-numbers") {
        // the position is optional: taken only when it names one
        let given = eq;
        if (!eq && i + 1 < argv.length && PAGE_NUMBERS.includes(argv[i + 1])) {
          given = true;
          value = argv[i + 1];
          i += 1;
        }
        if (given && !PAGE_NUMBERS.includes(value)) throw new BuildError("--page-numbers takes top-right, top-center or bottom-center");
        opts.page_numbers = given ? value : PAGE_NUMBERS[0];
        i += 1;
        continue;
      }
      if (Object.prototype.hasOwnProperty.call(switches, name)) {
        if (eq) throw new BuildError(name + " takes no value");
        const [key, on] = switches[name];
        opts[key] = on;
        i += 1;
        continue;
      }
      if (!valued.includes(name)) throw new BuildError("unknown option " + name);
      if (!eq) {
        if (i + 1 >= argv.length) throw new BuildError(name + " needs a value");
        value = argv[i + 1];
        i += 1;
      }
      i += 1;
      if (name === "--font") {
        let bad = !value || codePointLength(value) > 64;
        for (const c of value) if (forbiddenChar(c) !== null) bad = true;
        if (bad) throw new BuildError("--font takes a font name of 1 to 64 characters");
        opts.font = value;
      } else if (name === "--size") {
        if (!NUMBER.test(value) || !(Number(value) >= 1 && Number(value) <= 400)) throw new BuildError("--size takes a number of points from 1 to 400");
        opts.size = Number(value);
      } else if (name === "--front-page-numbers") {
        if (!Object.prototype.hasOwnProperty.call(FRONT_NUMBERS, value)) throw new BuildError("--front-page-numbers takes " + Object.keys(FRONT_NUMBERS).join(", "));
        opts.front_page_numbers = value;
      } else if (name === "--appendix-numbers") {
        if (!Object.prototype.hasOwnProperty.call(APPENDIX_NUMBERS, value)) throw new BuildError("--appendix-numbers takes " + Object.keys(APPENDIX_NUMBERS).join(", "));
        opts.appendix_numbers = value;
      } else if (name === "--chapter-label" || name === "--table-label" || name === "--figure-label" || name === "--appendix-label") {
        let bad = !value || codePointLength(value) > 40;
        for (const c of value) if (c === "\t" || c === "\n" || c === "%" || forbiddenChar(c) !== null) bad = true;
        if (bad) throw new BuildError(name + " takes text of 1 to 40 characters on one line, without %");
        opts[name.slice(2).replace("-", "_")] = value;
      } else if (name === "--header" || name === "--footer") {
        let bad = !value || codePointLength(value) > 200;
        for (const c of value) if (c === "\t" || c === "\n" || forbiddenChar(c) !== null) bad = true;
        if (bad) throw new BuildError(name + " takes text of 1 to 200 characters on one line");
        opts[name.slice(2)] = value;
      } else if (name === "--table-size") {
        if (!NUMBER.test(value) || !(Number(value) >= 1 && Number(value) <= 400)) throw new BuildError("--table-size takes a number of points from 1 to 400");
        opts.table_size = Number(value);
      } else if (name === "--paper") {
        if (!Object.prototype.hasOwnProperty.call(PAPER, value)) throw new BuildError("--paper takes a4, letter or f14");
        opts.paper = value;
      } else if (name === "--margins") {
        const vals = value.split(",");
        if (vals.length !== 4 || !vals.every((v) => NUMBER.test(v))) throw new BuildError("--margins takes four non-negative numbers: top,right,bottom,left");
        opts.margins = vals.map(Number);
      } else if (name === "--indent") {
        if (!NUMBER.test(value)) throw new BuildError("--indent takes a non-negative number of inches");
        opts.indent = Number(value);
      } else if (name === "--line-spacing") {
        if (!NUMBER.test(value) || !(Number(value) >= 1 && Number(value) <= 3)) throw new BuildError("--line-spacing takes a multiple of single spacing from 1 to 3");
        opts.line_spacing = Number(value);
      } else if (name === "--align") {
        if (value !== "left" && value !== "thai") throw new BuildError("--align takes left or thai");
        opts.align = value;
      } else if (name === "--table-widths") {
        if (value !== "equal" && value !== "auto") throw new BuildError("--table-widths takes equal or auto");
        opts.table_widths = value;
      } else if (name === "--allow-dir") {
        allow.push(value);
      }
      continue;
    }
    positional.push(arg);
    i += 1;
  }
  if (positional.length !== 2) throw new BuildError(USAGE);
  if (!opts.page_number_on_first && !opts.page_numbers) throw new BuildError("--no-page-number-first needs --page-numbers");
  const [pw, ph] = pageSize(opts);
  const [top, right, bottom, left] = opts.margins.map((m) => halfUp(m * 1440));
  if (pw - left - right < MIN_TEXT_TWIPS || ph - top - bottom < MIN_TEXT_TWIPS) throw new BuildError("--margins leave less than one inch for text");
  if (pw - left - right - halfUp(opts.indent * 1440) < MIN_TEXT_TWIPS) throw new BuildError("--indent leaves less than one inch for text");
  return [opts, positional, allow];
}
