// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
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
// what a document may hold that a setting needs (ADR 0028): the name an entry says in `needs`
// or `clashes` → why the flag did nothing
const STRUCTURES = {
  tables: "the document has no table",
  "table captions": "the document has no 'Table:' caption",
  "figure captions": "the document has no 'Figure:' caption",
  captions: "the document has no 'Table:' or 'Figure:' caption",
  images: "the document has no image on a line of its own",
  "chapters or appendices": "the document has no <!-- chapters --> or <!-- appendices --> comment",
  "numbered headings": "no heading carries a chapter or appendix number; a # heading under <!-- chapters --> or <!-- appendices --> does",
  appendices: "the document has no <!-- appendices --> comment",
  "appendix headings": "no heading carries an appendix letter; a # heading under <!-- appendices --> does",
  "chapter headings": "no heading carries a chapter number; a # heading under <!-- chapters --> does",
  front: "the document has no <!-- front --> comment",
  numbers: "the document has no numbered heading, ordered list or caption",
};
const CLASHES = {
  "toc comment": "the document places a table of contents with <!-- toc --> as well, so it now has two",
};

const LABEL = 'text of 1 to 40 characters on one line, without %, " or \\';
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
  { key: "toc", flag: "--toc", kind: "switch", default: false, layer: 4, clashes: "toc comment", report: ["toc", "value"] },
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
  { key: "thai_language", flag: "--thai-language", kind: "switch", default: false, layer: 1,
    report: ["thai_language", "value"] },
  { key: "force_cs_whole_doc", flag: "--force-cs-whole-doc", kind: "switch", default: false, layer: 1, // ADR 0039
    report: ["force_cs_whole_doc", "value"] },
  { key: "thai_digits", flag: "--thai-digits", kind: "switch", default: false, layer: 2, // numbers Word generates; never the text
    report: ["thai_digits", "value"] },
  { key: "auto_numbering", flag: "--auto-numbering", kind: "switch", default: false, layer: 2, // who counts: the build, or the application
    needs: "numbers", report: ["auto_numbering", "value"] },
  { key: "hide_spelling_errors", flag: "--hide-spelling-errors", kind: "switch", default: false, layer: 1,
    report: ["hide_spelling_errors", "value"] },
  { key: "repeat_table_header", flag: "--no-repeat-table-header", kind: "off", default: true, layer: 3,
    needs: "tables", report: ["repeat_table_header", "value"] },
  { key: "table_widths", flag: "--table-widths", kind: "value", default: "equal", layer: 3, // or by the longest text
    read: ["choice", ["equal", "auto"]], takes: "equal or auto", needs: "tables", report: ["table_widths", "value"] },
  { key: "table_size", flag: "--table-size", kind: "option", default: null, layer: 3, // null: the body size
    read: ["points", 1, 400], takes: "a number of points from 1 to 400", usage: "PT", report: ["table_size_pt", "value"] },
  { key: "chapter_label", flag: "--chapter-label", kind: "value", default: "บทที่", layer: 5,
    read: ["text", 40, '\t\n%"\\'], takes: LABEL, usage: "TEXT", needs: "chapter headings", report: ["chapter_label", "value"] },
  { key: "table_label", flag: "--table-label", kind: "value", default: "ตารางที่", layer: 5,
    read: ["text", 40, '\t\n%"\\'], takes: LABEL, usage: "TEXT", needs: "table captions", report: ["table_label", "value"] },
  { key: "figure_label", flag: "--figure-label", kind: "value", default: "รูปที่", layer: 5,
    read: ["text", 40, '\t\n%"\\'], takes: LABEL, usage: "TEXT", needs: "figure captions", report: ["figure_label", "value"] },
  { key: "caption_hanging_indent", flag: "--caption-hanging-indent", kind: "value", default: 0.0, layer: 5, // inches
    read: ["number", 0, 4], takes: "a number of inches from 0 to 4", usage: "IN",
    needs: "captions", report: ["caption_hanging_indent_in", "float"] },
  { key: "center_images", flag: "--center-images", kind: "switch", default: false, layer: 5,
    needs: "images", report: ["center_images", "value"] },
  { key: "caption_matches_object", flag: "--caption-matches-object", kind: "switch", default: false, layer: 5,
    needs: "figure captions", report: ["caption_matches_object", "value"] },
  { key: "front_page_numbers", flag: "--front-page-numbers", kind: "value", default: "thai-letters", layer: 5,
    read: ["choice", Object.keys(FRONT_NUMBERS)], takes: Object.keys(FRONT_NUMBERS).join(", "), needs: "front", report: ["front_page_numbers", "value"] },
  { key: "appendix_label", flag: "--appendix-label", kind: "value", default: "ภาคผนวก", layer: 5,
    read: ["text", 40, '\t\n%"\\'], takes: LABEL, usage: "TEXT", needs: "appendix headings", report: ["appendix_label", "value"] },
  { key: "appendix_numbers", flag: "--appendix-numbers", kind: "value", default: "thai-letters", layer: 5,
    read: ["choice", Object.keys(APPENDIX_NUMBERS)], takes: Object.keys(APPENDIX_NUMBERS).join(", "), needs: "appendix headings", report: ["appendix_numbers", "value"] },
  { key: "chapter_title_on_new_line", flag: "--chapter-title-on-new-line", kind: "switch", default: false, layer: 5,
    needs: "numbered headings", report: ["chapter_title_on_new_line", "value"] },
];

const DEFAULTS = Object.fromEntries(SETTINGS.map((s) => [s.key, s.default]));
const BY_FLAG = new Map(SETTINGS.map((s) => [s.flag, s]));
const USAGE = "usage: thai_docx build IN.md OUT.docx " + SETTINGS.map((s) =>
  "[" + s.flag +
  (s.kind === "switch" || s.kind === "off" ? ""
    : s.read[0] === "position" ? " [" + s.read[1].join("|") + "]"
    : s.read[0] === "choice" ? " " + s.read[1].join("|")
    : " " + s.usage) +
  "]").join(" ") + " [--profile NAME|PATH [--default SETTING[,SETTING]]] [--allow-dir DIR]";
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
  // a number too long for a float is infinite, and an infinite length is not one
  if (how[0] === "numbers") {
    const vals = value.split(",");
    if (vals.length !== how[1] || !vals.every((v) => NUMBER.test(v) && Number.isFinite(Number(v)))) throw refused();
    return vals.map(Number);
  }
  if (!NUMBER.test(value) || !Number.isFinite(Number(value)) ||
      (how[1] !== null && !(Number(value) >= how[1] && Number(value) <= how[2]))) throw refused();
  return Number(value);
}

// One flag's value, read as the build reads it — for a command that takes the flag without
// the rest of the build's (repair's --font).
function readValue(flag, value) {
  return readSetting(BY_FLAG.get(flag), value);
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
    if (name === "--help") throw new BuildError(USAGE);
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
    if (s.needs && has(DEFAULTS, s.needs) && opts[s.key] !== s.default && opts[s.needs] === DEFAULTS[s.needs]) {
      throw new BuildError(s.flag + " needs " + SETTINGS.find((n) => n.key === s.needs).flag);
    }
  }
  // Word's SEQ field names its counter with one word, so a caption label written as one takes
  // no space; numbers the build writes as text carry the label as text, where a space is fine
  if (opts.auto_numbering) {
    for (const key of ["table_label", "figure_label"]) {
      if (/[ \t\n\r\f\v\u00a0\u3000]/.test(opts[key])) {
        throw new BuildError(SETTINGS.find((x) => x.key === key).flag + " takes no space with --auto-numbering: Word's SEQ field names a counter with one word");
      }
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

function joinFlags(flags) {
  return flags.length === 1 ? flags[0] : flags.slice(0, -1).join(", ") + " and " + flags[flags.length - 1];
}

// A flag that changed nothing is said out loud, never dropped in silence: one warning for
// each structure the document lacks, naming every flag given that needed it; then one for
// each flag that duplicates what the document already places.
function settingsWarnings(opts, present) {
  const missing = new Map();
  for (const s of SETTINGS) {
    if (s.needs && has(STRUCTURES, s.needs) && !present.has(s.needs) && opts[s.key] !== s.default) {
      if (!missing.has(s.needs)) missing.set(s.needs, []);
      missing.get(s.needs).push(s.flag);
    }
  }
  const out = [...missing].map(([need, flags]) => joinFlags(flags) + " changed nothing: " + STRUCTURES[need]);
  for (const s of SETTINGS) {
    if (s.clashes && present.has(s.clashes) && opts[s.key] !== s.default) out.push(s.flag + ": " + CLASHES[s.clashes]);
  }
  return out;
}

// The nine questions of grill mode, in order (ADR 0029): the port of QUESTIONS in settings.py.
// A choice sets settings (`set`), or takes a value the user types (`other`), or says where the
// answers are kept (`save`). Labels are [Thai, English].
const QUESTIONS = [
  { key: "font", text: ["ฟอนต์", "Font"], choices: [
    { set: {"font": "TH Sarabun New"}, label: ["TH Sarabun New", "TH Sarabun New"] },
    { set: {"font": "TH SarabunPSK"}, label: ["TH SarabunPSK", "TH SarabunPSK"] },
    { set: {"font": "Sarabun"}, label: ["Sarabun", "Sarabun"] },
    { other: {"font": "NAME"}, label: ["อื่น ๆ: พิมพ์ชื่อฟอนต์", "Other: the font name"] },
  ] },
  { key: "size", text: ["ขนาดตัวอักษร", "Font size"], choices: [
    { set: {"size": 16}, label: ["16 pt", "16 pt"] },
    { set: {"size": 14}, label: ["14 pt", "14 pt"] },
    { set: {"size": 15}, label: ["15 pt", "15 pt"] },
    { other: {"size": "N"}, label: ["อื่น ๆ: พิมพ์ขนาด", "Other: the size"] },
  ] },
  { key: "paper", text: ["กระดาษและขอบ", "Paper and margins"], choices: [
    { set: {"paper": "a4", "margins": [1.0,  1.0,  1.0,  1.5]}, label: ["A4 ขอบซ้าย 1.5 นิ้ว ด้านอื่น 1 นิ้ว", "A4, left 1.5 in, others 1 in"] },
    { set: {"paper": "a4", "margins": [1.0,  1.0,  1.0,  1.0]}, label: ["A4 ขอบ 1 นิ้วทุกด้าน", "A4, 1 in all round"] },
    { set: {"paper": "letter", "margins": [1.0,  1.0,  1.0,  1.5]}, label: ["Letter ขอบซ้าย 1.5 นิ้ว ด้านอื่น 1 นิ้ว", "Letter, left 1.5 in, others 1 in"] },
    { other: {"paper": "PAPER", "margins": "T,R,B,L"}, label: ["อื่น ๆ: กระดาษ และขอบ บน ขวา ล่าง ซ้าย เป็นนิ้ว", "Other: paper, and margins top, right, bottom, left in inches"] },
  ] },
  { key: "align", text: ["การจัดย่อหน้า", "Paragraph alignment"], choices: [
    { set: {"align": "left"}, label: ["ชิดซ้าย", "Left"] },
    { set: {"align": "thai"}, label: ["กระจายแบบไทย", "Thai distributed"] },
  ] },
  { key: "indent", text: ["ย่อหน้าบรรทัดแรกของเนื้อความ", "First-line indent of body paragraphs"], choices: [
    { set: {"indent": 0.0}, label: ["ไม่ย่อ", "None"] },
    { set: {"indent": 0.5}, label: ["0.5 นิ้ว", "0.5 in"] },
    { set: {"indent": 1.0}, label: ["1 นิ้ว", "1 in"] },
    { other: {"indent": "N"}, label: ["อื่น ๆ: พิมพ์เป็นนิ้ว", "Other: inches"] },
  ] },
  { key: "toc", text: ["สารบัญ", "Table of contents"], choices: [
    { set: {"toc": false}, label: ["ไม่ใส่", "No"] },
    { set: {"toc": true}, label: ["ใส่", "Yes"] },
  ] },
  { key: "page-numbers", text: ["เลขหน้า", "Page numbers"], choices: [
    { set: {"page_numbers": false}, label: ["ไม่ใส่", "No"] },
    { set: {"page_numbers": "top-right"}, label: ["ใส่", "Yes"] },
  ] },
  { key: "squiggles", text: ["เส้นหยักตรวจคำสะกด", "Spelling squiggles"], choices: [
    { set: {"hide_spelling_errors": false}, label: ["แสดง", "Show"] },
    { set: {"hide_spelling_errors": true}, label: ["ซ่อน (ซ่อนคำที่สะกดผิดจริงด้วย)", "Hide (hides real typos too)"] },
  ] },
  { key: "save", text: ["บันทึกการตั้งค่านี้ไว้ใช้ครั้งต่อไป", "Keep these settings for next time"], choices: [
    { save: null, label: ["ไม่บันทึก", "No"] },
    { save: "home", label: ["บันทึกเป็นของฉัน: พิมพ์ชื่อ", "Yes, as mine: the name"] },
    { save: "project", label: ["บันทึกไว้ในโปรเจกต์นี้: พิมพ์ชื่อ", "Yes, in this project: the name"] },
  ] },
];
