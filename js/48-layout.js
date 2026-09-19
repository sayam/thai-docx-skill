// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// thai-docx — layout: the port of scripts/thai_docx/layout.py. What the parsed document declares,
// before a byte is written: heading styles (ADR 0020), regions, captions and lists (ADR 0021, 0027).

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
const LISTS = ["toc", "list-of-tables", "list-of-figures"]; // the directives the build writes a list for
const CAPTION_PREFIX = { table: "Table:", figure: "Figure:" };
// What a Thai writer reaches for instead. These make no caption — the prefix is one word,
// written in English, so one rule holds in both languages — but a paragraph that opens with
// one of them where a caption would go is a mistake worth naming (ADR 0021).
const THAI_CAPTION_PREFIX = { table: ["ตาราง:", "ตารางที่:"], figure: ["รูป:", "รูปที่:", "ภาพ:", "ภาพที่:"] };
const PLAIN_KEYS = ["link", "code", "b", "i", "strike", "u", "sup", "sub"];

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

function thaiCaptionKind(b) {
  if (b.t !== "paragraph" || !b.inlines.length) return null;
  const first = b.inlines[0];
  if (first.t !== "text" || PLAIN_KEYS.some((k) => first[k])) return null;
  for (const kind of Object.keys(THAI_CAPTION_PREFIX)) {
    for (const prefix of THAI_CAPTION_PREFIX[kind]) {
      const s = first.s;
      if (s.startsWith(prefix) && (s.length === prefix.length || s[prefix.length] === " " || s[prefix.length] === "\t")) return kind;
    }
  }
  return null;
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
  const sub = [0, 0, 0, 0, 0, 0]; // the counter of each heading level (ADR 0035)
  let lastLevel = 0;  // the heading level before this one: a jump leaves a gap in the outline
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
    if (b.t === "heading") {
      countHeading(b.level, sub);
      const number = headingNumber(b.level, sub, sectioned ? region : "chapters", sectioned, chapter, appendix, opts);
      if (number !== null) item.number = number;
    }
    for (const n of b.inlines || []) {
      if (n.t === "image" && !stripChars(n.alt, " \t")) {
        warnings.push("line " + b.line + ": the image '" + n.src
          + "' has no text between the brackets of ![]; a reader who cannot see it is told nothing");
      }
    }
    if (b.t === "heading") {
      if (b.level > lastLevel + 1 && lastLevel) {
        warnings.push("line " + b.line + ": a heading of level " + b.level + " follows one of level "
          + lastLevel + "; the contents and a screen reader read the levels in order");
      }
      lastLevel = b.level;
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
    if (kind === null) {
      const thai = thaiCaptionKind(b);
      const inPlace = (thai === "table" && i + 1 < blocks.length && blocks[i + 1].t === "table") ||
        (thai === "figure" && i > 0 && imageOnly(blocks[i - 1]));
      if (inPlace) {
        warnings.push("line " + b.line + ": a caption is written '" + CAPTION_PREFIX[thai]
          + "' in English, in every language; this paragraph is kept as text");
      }
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

// A heading advances its own level's counter and starts the deeper ones again.
function countHeading(level, sub) {
  sub[level - 1] += 1;
  for (let k = level; k < sub.length; k++) sub[k] = 0;
}

// The number a heading carries, or null for a heading that carries none. Written into the
// document as text rather than left to the application to compute (ADR 0035).
function headingNumber(level, sub, region, sectioned, chapter, appendix, opts) {
  if (level > 1 && !opts.heading_numbers) return null;
  if (sectioned && region !== "chapters" && region !== "appendices") return null;
  const thai = opts.thai_digits;
  let first, label;
  if (region === "appendices") {
    if (!appendix) return null;
    first = numberText(appendix, opts.appendix_numbers, thai);
    label = opts.appendix_label;
  } else if (sectioned) {
    if (!chapter) return null;
    first = numberText(chapter, "decimal", thai);
    label = opts.chapter_label;
  } else {
    if (!opts.heading_numbers) return null;
    first = numberText(sub[0], "decimal", thai);
    label = null;
  }
  if (level === 1) return label === null ? first + "." : label + " " + first;
  const parts = [first];
  for (let k = 1; k < level; k++) parts.push(numberText(sub[k], "decimal", thai));
  return parts.join(".");
}

const LIST_KINDS = { "list-of-tables": "table", "list-of-figures": "figure" };

// An entry is one line: a heading broken over two lines reads as one in the list.
function oneLine(text) {
  return text.split("\n").join(" ");
}

// What a table of contents, tables or figures holds, as [heading level, text, anchor]. The
// build writes the entries itself (ADR 0035): a \c list collects the SEQ fields a caption no
// longer carries, and a \o list would rebuild text the build already knows. The anchor names
// the bookmark whose page a PAGEREF field asks for.
function listEntries(items, name) {
  const out = [];
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const b = item.block;
    if (name === "toc") {
      if (!item.caption && b.t === "heading" && b.level <= 3) {
        out.push([b.level, oneLine((item.number === undefined ? "" : item.number + " ") + inlineText(b.inlines)), anchorName(i)]);
      }
    } else if (item.caption && item.caption.kind === LIST_KINDS[name]) {
      out.push([1, oneLine(captionText(item.caption)), anchorName(i)]);
    }
  }
  return out;
}

// The bookmark a list entry points at. `_Toc` is the prefix Word gives its own.
function anchorName(index) {
  return "_Toc" + (90000000 + index);
}

// What a caption paragraph reads as: its label and number, then the Markdown's text.
function captionText(c) {
  const number = (c.chapter ? c.chapter + "-" : "") + c.seq;
  return c.label + " " + number + (c.inlines.length ? " " + inlineText(c.inlines) : "");
}
