// thai-docx — settings: the port of scripts/thai_docx/settings.py. Every setting is one
// entry, and the defaults, the usage line, the parser, the reported settings and the flags
// a profile may hold are derived from the entries (ADR 0028). A test holds these entries
// equal to Python's.

const PAPER = { a4: [11906, 16838], letter: [12240, 15840], f14: [12240, 18720] }; // f14: 8.5 x 13 in, folio
const PAGE_NUMBERS = ["top-right", "top-center", "bottom-center"]; // the first is --page-numbers with no position
// page numbers before the chapters, and appendix numbers: flag value → Word's number format
const FRONT_NUMBERS = { "thai-letters": "thaiLetters", "lower-roman": "lowerRoman", "upper-roman": "upperRoman", decimal: "decimal" };
const APPENDIX_NUMBERS = { "thai-letters": "thaiLetters", "upper-letters": "upperLetter", decimal: "decimal", "upper-roman": "upperRoman" };
const MIN_TEXT_TWIPS = 1440;
const LAYERS = { 1: "page and type", 2: "page furniture", 3: "tables", 4: "headings", 5: "thesis structure" };

const LABEL = "text of 1 to 40 characters on one line, without %";
const SETTINGS = [
  { key: "font", flag: "--font", kind: "value", default: "TH Sarabun New", layer: 1,
    read: ["text", 64, ""], takes: "a font name of 1 to 64 characters", usage: "NAME", report: ["font", "value"] },
  { key: "size", flag: "--size", kind: "value", default: 16, layer: 1,
    read: ["points", 1, 400], takes: "a number of points from 1 to 400", usage: "PT", report: ["size_pt", "value"] },
  { key: "paper", flag: "--paper", kind: "value", default: "a4", layer: 1,
    read: ["choice", Object.keys(PAPER)], takes: "a4, letter or f14", report: ["paper", "value"] },
  { key: "landscape", flag: "--landscape", kind: "switch", default: false, layer: 1, report: ["landscape", "value"] },
  { key: "margins", flag: "--margins", kind: "list", default: [1.0, 1.0, 1.0, 1.5], layer: 1, // top, right, bottom, left — inches
    read: ["numbers", 4], takes: "four non-negative numbers: top,right,bottom,left", usage: "T,R,B,L", report: ["margins_in", "sides"] },
  { key: "indent", flag: "--indent", kind: "value", default: 0.0, layer: 1, // first line of body paragraphs — inches
    read: ["number", null, null], takes: "a non-negative number of inches", usage: "IN", report: ["first_line_indent_in", "float"] },
  { key: "line_spacing", flag: "--line-spacing", kind: "value", default: 1.0, layer: 1, // code and footnotes stay single
    read: ["number", 1, 3], takes: "a multiple of single spacing from 1 to 3", usage: "N", report: ["line_spacing", "float"] },
  { key: "align", flag: "--align", kind: "value", default: "left", layer: 1,
    read: ["choice", ["left", "thai"]], takes: "left or thai", report: ["align", "value"] },
  { key: "toc", flag: "--toc", kind: "switch", default: false, layer: 4, report: ["toc", "value"] },
  { key: "heading_numbers", flag: "--heading-numbers", kind: "switch", default: false, layer: 4, // 1. / 1.1 / 1.1.1, numbered by Word
    report: ["heading_numbers", "value"] },
  { key: "page_numbers", flag: "--page-numbers", kind: "option", default: false, layer: 2, // or one of PAGE_NUMBERS
    read: ["position", PAGE_NUMBERS], takes: "top-right, top-center or bottom-center", report: ["page_numbers", "value"] },
  { key: "page_number_on_first", flag: "--no-page-number-first", kind: "off", default: true, layer: 2,
    needs: "page_numbers", report: ["page_number_on_first", "value"] },
  { key: "header", flag: "--header", kind: "option", default: null, layer: 2, // centred at the top of every page
    read: ["text", 200, "\t\n"], takes: "text of 1 to 200 characters on one line", usage: "TEXT", report: ["header", "value"] },
  { key: "footer", flag: "--footer", kind: "option", default: null, layer: 2, // centred at the bottom of every page
    read: ["text", 200, "\t\n"], takes: "text of 1 to 200 characters on one line", usage: "TEXT", report: ["footer", "value"] },
  { key: "thai_digits", flag: "--thai-digits", kind: "switch", default: false, layer: 2, // numbers Word generates; never the text
    report: ["thai_digits", "value"] },
  { key: "hide_spelling_errors", flag: "--hide-spelling-errors", kind: "switch", default: false, layer: 1,
    report: ["hide_spelling_errors", "value"] },
  { key: "repeat_table_header", flag: "--no-repeat-table-header", kind: "off", default: true, layer: 3,
    report: ["repeat_table_header", "value"] },
  { key: "table_widths", flag: "--table-widths", kind: "value", default: "equal", layer: 3, // or by the longest text
    read: ["choice", ["equal", "auto"]], takes: "equal or auto", report: ["table_widths", "value"] },
  { key: "table_size", flag: "--table-size", kind: "option", default: null, layer: 3, // null: the body size
    read: ["points", 1, 400], takes: "a number of points from 1 to 400", usage: "PT", report: ["table_size_pt", "value"] },
  { key: "chapter_label", flag: "--chapter-label", kind: "value", default: "บทที่", layer: 5,
    read: ["text", 40, "\t\n%"], takes: LABEL, usage: "TEXT", report: ["chapter_label", "value"] },
  { key: "table_label", flag: "--table-label", kind: "value", default: "ตารางที่", layer: 5,
    read: ["text", 40, "\t\n%"], takes: LABEL, usage: "TEXT", report: ["table_label", "value"] },
  { key: "figure_label", flag: "--figure-label", kind: "value", default: "รูปที่", layer: 5,
    read: ["text", 40, "\t\n%"], takes: LABEL, usage: "TEXT", report: ["figure_label", "value"] },
  { key: "front_page_numbers", flag: "--front-page-numbers", kind: "value", default: "thai-letters", layer: 5,
    read: ["choice", Object.keys(FRONT_NUMBERS)], takes: Object.keys(FRONT_NUMBERS).join(", "), report: ["front_page_numbers", "value"] },
  { key: "appendix_label", flag: "--appendix-label", kind: "value", default: "ภาคผนวก", layer: 5,
    read: ["text", 40, "\t\n%"], takes: LABEL, usage: "TEXT", report: ["appendix_label", "value"] },
  { key: "appendix_numbers", flag: "--appendix-numbers", kind: "value", default: "thai-letters", layer: 5,
    read: ["choice", Object.keys(APPENDIX_NUMBERS)], takes: Object.keys(APPENDIX_NUMBERS).join(", "), report: ["appendix_numbers", "value"] },
  { key: "chapter_title_on_new_line", flag: "--chapter-title-on-new-line", kind: "switch", default: false, layer: 5,
    report: ["chapter_title_on_new_line", "value"] },
];

const DEFAULTS = Object.fromEntries(SETTINGS.map((s) => [s.key, s.default]));
const BY_FLAG = new Map(SETTINGS.map((s) => [s.flag, s]));
const USAGE = "usage: thai_docx build IN.md OUT.docx " + SETTINGS.map((s) =>
  "[" + s.flag +
  (s.kind === "switch" || s.kind === "off" ? ""
    : s.read[0] === "position" ? " [" + s.read[1].join("|") + "]"
    : s.read[0] === "choice" ? " " + s.read[1].join("|")
    : " " + s.usage) +
  "]").join(" ") + " [--profile NAME|PATH] [--allow-dir DIR]";
const NUMBER = /^[0-9]+(?:\.[0-9]+)?$/;

class BuildError extends Error {
  constructor(what) {
    super(what);
    this.what = what;
  }
}

function halfUp(x) {
  return Math.floor(x + 0.5);
}

// Width and height in twips; landscape turns the paper, the margins stay top, right, bottom, left.
function pageSize(opts) {
  const [pw, ph] = PAPER[opts.paper];
  return opts.landscape ? [ph, pw] : [pw, ph];
}

// A value as the entry reads it, or BuildError with the entry's own words.
function readSetting(s, value) {
  const how = s.read;
  const refused = () => new BuildError(s.flag + " takes " + s.takes);
  if (how[0] === "text") {
    let bad = !value || codePointLength(value) > how[1];
    for (const c of value) if (how[2].includes(c) || forbiddenChar(c) !== null) bad = true;
    if (bad) throw refused();
    return value;
  }
  if (how[0] === "choice" || how[0] === "position") {
    if (!how[1].includes(value)) throw refused();
    return value;
  }
  if (how[0] === "numbers") {
    const vals = value.split(",");
    if (vals.length !== how[1] || !vals.every((v) => NUMBER.test(v))) throw refused();
    return vals.map(Number);
  }
  if (!NUMBER.test(value) || (how[1] !== null && !(Number(value) >= how[1] && Number(value) <= how[2]))) throw refused();
  return Number(value);
}

function parseArgs(argv) {
  const opts = { ...DEFAULTS, margins: DEFAULTS.margins.slice() };
  const positional = [];
  const allow = [];
  let i = 0;
  while (i < argv.length) {
    const arg = argv[i];
    if (!arg.startsWith("--")) {
      positional.push(arg);
      i += 1;
      continue;
    }
    const eqAt = arg.indexOf("=");
    const name = eqAt < 0 ? arg : arg.slice(0, eqAt);
    let eq = eqAt >= 0;
    let value = eq ? arg.slice(eqAt + 1) : "";
    const s = BY_FLAG.get(name);
    if (s !== undefined && s.kind === "option" && s.read[0] === "position") {
      // the position is optional: taken only when it names one
      if (!eq && i + 1 < argv.length && s.read[1].includes(argv[i + 1])) {
        eq = true;
        value = argv[i + 1];
        i += 1;
      }
      opts[s.key] = eq ? readSetting(s, value) : s.read[1][0];
      i += 1;
      continue;
    }
    if (s !== undefined && (s.kind === "switch" || s.kind === "off")) {
      if (eq) throw new BuildError(name + " takes no value");
      opts[s.key] = s.kind === "switch";
      i += 1;
      continue;
    }
    if (s === undefined && name !== "--allow-dir") throw new BuildError("unknown option " + name);
    if (!eq) {
      if (i + 1 >= argv.length) throw new BuildError(name + " needs a value");
      value = argv[i + 1];
      i += 1;
    }
    i += 1;
    if (s === undefined) allow.push(value);
    else opts[s.key] = readSetting(s, value);
  }
  if (positional.length !== 2) throw new BuildError(USAGE);
  for (const s of SETTINGS) {
    if (s.needs && opts[s.key] !== s.default && opts[s.needs] === DEFAULTS[s.needs]) {
      throw new BuildError(s.flag + " needs " + SETTINGS.find((n) => n.key === s.needs).flag);
    }
  }
  const [pw, ph] = pageSize(opts);
  const [top, right, bottom, left] = opts.margins.map((m) => halfUp(m * 1440));
  if (pw - left - right < MIN_TEXT_TWIPS || ph - top - bottom < MIN_TEXT_TWIPS) throw new BuildError("--margins leave less than one inch for text");
  if (pw - left - right - halfUp(opts.indent * 1440) < MIN_TEXT_TWIPS) throw new BuildError("--indent leaves less than one inch for text");
  return [opts, positional, allow];
}

// The settings as the build reports them, in registry order; numbers Python holds as
// floats are written as floats.
function settingsJson(opts) {
  const out = {};
  for (const s of SETTINGS) {
    const [name, form] = s.report;
    const value = opts[s.key];
    if (form === "float") out[name] = new PyFloat(value);
    else if (form === "sides") out[name] = { top: new PyFloat(value[0]), right: new PyFloat(value[1]), bottom: new PyFloat(value[2]), left: new PyFloat(value[3]) };
    else out[name] = typeof value === "number" && !Number.isInteger(value) ? new PyFloat(value) : value;
  }
  return out;
}
