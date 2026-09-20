// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// Repair a .docx this skill did not write: the attributes that break Thai, never the text
// (ADR 0037) — the port of thai_docx/repair.py. This version repairs two findings and
// reports every other one:
//
//   1  compatibilityMode is not exactly one 15 — set it, or drop the ones that are not 15
//   3  <w:noProof/> switches Thai proofing, and Thai line breaking, off — remove it
//
// A part is edited as text, not re-serialised from a tree: a tree would rewrite prefixes,
// attribute order and empty-element spelling across the whole part, and ADR 0037 allows only
// the attributes named. Both elements below are empty ones, so the shapes are few.

const REPAIR_USAGE = 'usage: thai_docx repair IN.docx OUT.docx [--font "TH Sarabun New"] [--thai-language]';

class RepairError extends Error {}
const RE_NO_PROOF = /<w:noProof(?:\s[^>]*?)?\/>|<w:noProof(?:\s[^>]*?)?>\s*<\/w:noProof>/g;
const RE_COMPAT_SETTING = /<w:compatSetting\s[^>]*?\/>/g;
const RE_ATTR = /([\w:]+)\s*=\s*"([^"]*)"/g;

function tagAttrs(tag) {
  const out = new Map();
  for (const m of tag.matchAll(RE_ATTR)) out.set(m[1], m[2]);
  return out;
}

// Every <w:noProof/> gone. Removing it leaves the default, which is proofing on.
function removeNoProof(xml) {
  let count = 0;
  const out = xml.replace(RE_NO_PROOF, () => {
    count += 1;
    return "";
  });
  return [out, count];
}

// Exactly one compatibilityMode, declared 15: the first is set to 15 and any other is
// dropped. A part that declares none is left alone — writing one means placing an element in
// schema order, which this version does not do.
function oneCompatibilityMode(xml) {
  const found = [];
  for (const m of xml.matchAll(RE_COMPAT_SETTING)) {
    const a = tagAttrs(m[0]);
    if (a.get("w:name") === "compatibilityMode" && a.get("w:uri") === COMPAT_URI) found.push(m);
  }
  if (!found.length) return [xml, 0];
  let changed = 0, out = "", last = 0;
  for (let i = 0; i < found.length; i++) {
    const m = found[i];
    out += xml.slice(last, m.index);
    if (i === 0) {
      let tag = m[0];
      if (tagAttrs(tag).get("w:val") !== "15") {
        const set = tag.replace(/(w:val\s*=\s*)"[^"]*"/, '$1"15"');
        tag = set === tag ? tag.slice(0, -2).replace(/\s+$/, "") + ' w:val="15"/>' : set;
        changed += 1;
      }
      out += tag;
    } else {
      changed += 1; // a second declaration is one more thing that was wrong
    }
    last = m.index + m[0].length;
  }
  out += xml.slice(last);
  return [out, changed];
}


// --- the marks a Thai run needs, and the twins a Latin property needs ------------------

const RE_TAG = /<(\/?)(w:[\w.-]+)((?:[^<>"']|"[^"]*"|'[^']*')*?)(\/?)>/g;
const RE_RUN_START = /<w:r(?:\s[^<>]*?)?>/g;
const LATIN_FONT = ["w:ascii", "w:hAnsi", "w:asciiTheme", "w:hAnsiTheme"];

// Where the element that opened just before `afterStart` ends: [inner end, element end].
// Depth is counted, because a run can hold a drawing that holds runs of its own.
function endOf(xml, afterStart, name) {
  let depth = 1;
  const re = new RegExp(RE_TAG.source, "g");
  re.lastIndex = afterStart;
  for (let m = re.exec(xml); m !== null; m = re.exec(xml)) {
    if (m[2] !== name || m[4]) continue;
    depth += m[1] ? -1 : 1;
    if (depth === 0) return [m.index, m.index + m[0].length];
  }
  throw new RepairError("<" + name + "> is never closed"); // the checker parsed it, so this cannot happen
}

// An element's own children, in order: [name, the raw text of the whole child].
function childrenOf(inner) {
  const out = [];
  let pos = 0;
  for (;;) {
    const re = new RegExp(RE_TAG.source, "g");
    re.lastIndex = pos;
    const m = re.exec(inner);
    if (m === null) return out;
    if (m[4]) {
      out.push([m[2], m[0]]);
      pos = m.index + m[0].length;
      continue;
    }
    const [, elementEnd] = endOf(inner, m.index + m[0].length, m[2]);
    out.push([m[2], inner.slice(m.index, elementEnd)]);
    pos = elementEnd;
  }
}

// `element` among `children`, at the place the schema puts it. Nothing already there moves:
// repairing the order is a different finding.
function insertChild(children, name, element) {
  const rank = RPR_ORDER.indexOf(name.slice(2));
  for (let i = 0; i < children.length; i++) {
    const local = children[i][0].slice(2);
    const at = RPR_ORDER.indexOf(local);
    if (at !== -1 && at > rank) return [...children.slice(0, i), [name, element], ...children.slice(i)];
  }
  return [...children, [name, element]];
}

// One w:rPr put right: [its new inner XML, code 2 repairs, code 5 repairs].
function fixRpr(inner, font, markThai, thaiLanguage) {
  let children = childrenOf(inner);
  const byName = new Map(children);
  let two = 0, five = 0, marked = 0;

  for (const [latin, twin] of [["w:sz", "w:szCs"], ["w:b", "w:bCs"], ["w:i", "w:iCs"]]) {
    if (byName.has(latin) && !byName.has(twin)) {
      const attrs = /(\sw:val\s*=\s*"[^"]*")/.exec(byName.get(latin));
      children = insertChild(children, twin, "<" + twin + (attrs ? attrs[1] : "") + "/>");
      byName.set(twin, "");
      five += 1;
    }
  }

  const fonts = byName.get("w:rFonts");
  if (fonts !== undefined) {
    const hasLatin = LATIN_FONT.some((a) => new RegExp(a + '\\s*=\\s*"').test(fonts));
    const hasCs = /w:cs(?:theme)?\s*=\s*"/.test(fonts);
    if (hasLatin && !hasCs) {
      const put = fonts.slice(0, -2).replace(/\s+$/, "") + ' w:cs="' + font + '"/>';
      children = children.map(([n, raw]) => [n, n === "w:rFonts" ? put : raw]);
      five += 1;
    }
  }

  if (markThai) {
    if (!byName.has("w:cs")) {
      children = insertChild(children, "w:cs", "<w:cs/>");
      two += 1;
    }
    if (thaiLanguage) {
      // the Thai complex-script language, only where the caller asked for it (ADR 0038)
      const lang = byName.get("w:lang");
      if (lang === undefined) {
        children = insertChild(children, "w:lang", '<w:lang w:bidi="th-TH"/>');
        marked += 1;
      } else if (!/w:bidi\s*=\s*"th-TH"/.test(lang)) {
        const put = /w:bidi\s*=\s*"/.test(lang)
          ? lang.replace(/w:bidi\s*=\s*"[^"]*"/, 'w:bidi="th-TH"')
          : lang.slice(0, -2).replace(/\s+$/, "") + ' w:bidi="th-TH"/>';
        children = children.map(([n, raw]) => [n, n === "w:lang" ? put : raw]);
        marked += 1;
      }
    }
  }

  return [children.map(([, raw]) => raw).join(""), two, five, marked];
}

// Every `element` in the part with its children in the order the schema fixes.
//
// The elements the schema names are put in that order, **in the places they already occupy**;
// anything it does not name keeps its own place, because the checker skips those and moving
// them would change more than the finding asked for. A permutation is the same bytes in a
// different order, so the part's length never changes and the positions of the other elements
// hold while this walks them.
function reorder(xml, element, order) {
  const rank = new Map(order.map((name, i) => [name, i]));
  const starts = [];
  const re = new RegExp("<" + element + "(?:\\s[^<>]*?)?>", "g");
  for (let m = re.exec(xml); m !== null; m = re.exec(xml)) starts.push(m.index + m[0].length);
  let count = 0;
  for (let k = starts.length - 1; k >= 0; k--) {  // inner elements first: they sit further on
    const at = starts[k];
    const [innerEnd] = endOf(xml, at, element);
    const children = childrenOf(xml.slice(at, innerEnd));
    const known = [];
    for (let i = 0; i < children.length; i++) {
      if (rank.has(children[i][0].slice(2))) known.push([i, children[i]]);
    }
    if (known.length < 2) continue;
    // a stable sort, so two children of one name keep the order they were written in
    const ordered = known.map((pair, i) => [pair, i])
      .sort((a, b) => (rank.get(a[0][1][0].slice(2)) - rank.get(b[0][1][0].slice(2))) || (a[1] - b[1]))
      .map(([pair]) => pair);
    if (known.every((pair, i) => pair[1][1] === ordered[i][1][1])) continue;
    const put = children.slice();
    for (let i = 0; i < known.length; i++) put[known[i][0]] = ordered[i][1];
    xml = xml.slice(0, at) + put.map(([, raw]) => raw).join("") + xml.slice(innerEnd);
    count += 1;
  }
  return [xml, count];
}

function fixRuns(xml, font, counts, thaiLanguage) {
  let out = "", pos = 0;
  const re = new RegExp(RE_RUN_START.source, "g");
  for (let m = re.exec(xml); m !== null; m = re.exec(xml)) {
    if (m.index < pos) continue;
    const startEnd = m.index + m[0].length;
    const [innerEnd] = endOf(xml, startEnd, "w:r");
    out += xml.slice(pos, startEnd) + fixRun(xml.slice(startEnd, innerEnd), font, counts, thaiLanguage);
    pos = innerEnd;
    re.lastIndex = pos;
  }
  return out + xml.slice(pos);
}

function fixRun(inner, font, counts, thaiLanguage) {
  const hasText = /<w:t(?:\s[^<>]*?)?>/.test(inner);
  const rpr = /^<w:rPr(?:\s[^<>]*?)?(\/?)>/.exec(inner);
  let body, restFrom, head = "";
  if (rpr !== null && rpr[1]) {
    body = "";
    restFrom = rpr[0].length;
  } else if (rpr !== null) {
    const [bodyEnd, elementEnd] = endOf(inner, rpr[0].length, "w:rPr");
    body = inner.slice(rpr[0].length, bodyEnd);
    restFrom = elementEnd;
  } else if (hasText) {
    body = "";
    restFrom = 0;
  } else {
    return fixRuns(inner, font, counts, thaiLanguage); // nothing of ours here; look deeper
  }
  const [newBody, two, five, marked] = fixRpr(body, font, hasText, thaiLanguage);
  counts["2"] = (counts["2"] || 0) + two;
  counts["5"] = (counts["5"] || 0) + five;
  counts["thai-language"] = (counts["thai-language"] || 0) + marked;
  if (newBody) head = "<w:rPr>" + newBody + "</w:rPr>";
  else if (rpr !== null) head = inner.slice(0, restFrom);
  return head + fixRuns(inner.slice(restFrom), font, counts, thaiLanguage);
}

function fixTextPart(xml, font, thaiLanguage) {
  const counts = {};
  const out = fixRuns(xml, font, counts, thaiLanguage);
  const kept = {};
  for (const [k, v] of Object.entries(counts)) if (v) kept[k] = v;
  return [out, kept];
}

// A style's w:rPr needs its twins; it formats no text, so no Thai marks are added.
function fixStyles(xml, font) {
  let out = "", pos = 0, five = 0;
  const re = /<w:rPr(?:\s[^<>]*?)?>/g;
  for (let m = re.exec(xml); m !== null; m = re.exec(xml)) {
    if (m.index < pos) continue;
    const startEnd = m.index + m[0].length;
    const [innerEnd] = endOf(xml, startEnd, "w:rPr");
    const [newBody, , n] = fixRpr(xml.slice(startEnd, innerEnd), font, false, false);
    five += n;
    out += xml.slice(pos, startEnd) + newBody;
    pos = innerEnd;
    re.lastIndex = pos;
  }
  return [out + xml.slice(pos), five];
}

// A bullet level drawn in Symbol has no Thai glyphs; give it the document's font.
function fixNumbering(xml, font) {
  let out = "", pos = 0, five = 0;
  const re = /<w:lvl(?:\s[^<>]*?)?>/g;
  for (let m = re.exec(xml); m !== null; m = re.exec(xml)) {
    if (m.index < pos) continue;
    const startEnd = m.index + m[0].length;
    const [innerEnd] = endOf(xml, startEnd, "w:lvl");
    let level = xml.slice(startEnd, innerEnd);
    if (/<w:numFmt\s[^<>]*?w:val="bullet"/.test(level)) {
      const fonts = /<w:rFonts(?:\s[^<>]*?)?\/>/.exec(level);
      if (fonts !== null && fonts[0].includes('"Symbol"')) {
        level = level.slice(0, fonts.index) + fonts[0].split('"Symbol"').join('"' + font + '"')
          + level.slice(fonts.index + fonts[0].length);
        five += 1;
      }
    }
    out += xml.slice(pos, startEnd) + level;
    pos = innerEnd;
    re.lastIndex = pos;
  }
  return [out + xml.slice(pos), five];
}

// The font a run that names none is given, and why (ADR 0037): what the user asked for, else
// the complex-script font this document already uses most, else the skill's default.
function complexScriptFont(parts, asked) {
  if (asked) return [asked, "the font the command was given"];
  const counted = new Map();
  for (const [name, bytes] of parts) {
    if (!name.startsWith("word/")) continue;
    for (const m of fromUtf8(bytes).matchAll(/w:cs\s*=\s*"([^"]+)"/g)) {
      // only a font the checker itself would accept: writing one it warns about would trade
      // a finding for a warning, which is not a repair
      if (!THAI_FONTS.has(m[1].toLowerCase())) continue;
      counted.set(m[1], (counted.get(m[1]) || 0) + 1);
    }
  }
  if (counted.size) {
    let best = null;
    for (const name of [...counted.keys()].sort()) {
      if (best === null || counted.get(name) > counted.get(best)) best = name;
    }
    return [best, "the complex-script font this document uses most"];
  }
  return [DEFAULTS.font, "this skill's default, as the document names none"];
}

// The parts to write anew, and how many of each code were repaired.
function repairParts(parts, findings, font, thaiLanguage) {
  const codes = new Set(findings.map((f) => f.code));
  const replace = new Map();
  const repaired = {};
  if (codes.has("1") && parts.has("word/settings.xml")) {
    const [settings, n] = oneCompatibilityMode(fromUtf8(parts.get("word/settings.xml")));
    if (n) {
      replace.set("word/settings.xml", utf8(settings));
      repaired["1"] = n;
    }
  }
  if (codes.has("3")) {
    for (const [name, bytes] of parts) {
      if (!name.startsWith("word/")) continue;
      const [xml, n] = removeNoProof(fromUtf8(replace.get(name) || bytes));
      if (n) {
        replace.set(name, utf8(xml));
        repaired["3"] = (repaired["3"] || 0) + n;
      }
    }
  }
  if (codes.has("order")) {
    // runs first, then paragraphs: a w:pPr holds a w:rPr, and moving a whole child keeps the
    // order already put right inside it
    for (const [name, bytes] of parts) {
      const mine = TEXT_PARTS.test(name) ||
        ["word/styles.xml", "word/numbering.xml", "word/settings.xml"].includes(name);
      if (!mine) continue;
      let out = fromUtf8(replace.get(name) || bytes), n = 0;
      for (const [element, table] of [["w:rPr", RPR_ORDER], ["w:pPr", PPR_ORDER], ["w:settings", SETTINGS_ORDER]]) {
        const [put, some] = reorder(out, element, table);
        out = put;
        n += some;
      }
      if (n) {
        replace.set(name, utf8(out));
        repaired["order"] = (repaired["order"] || 0) + n;
      }
    }
  }
  let chosen = null;
  if (codes.has("2") || codes.has("5") || thaiLanguage) {
    const [csFont, why] = complexScriptFont(parts, font);
    for (const [name, bytes] of parts) {
      if (!TEXT_PARTS.test(name)) continue;
      const [put, counts] = fixTextPart(fromUtf8(replace.get(name) || bytes), csFont, thaiLanguage);
      if (Object.keys(counts).length) {
        replace.set(name, utf8(put));
        for (const [code, n] of Object.entries(counts)) repaired[code] = (repaired[code] || 0) + n;
      }
    }
    for (const [name, fix] of [["word/styles.xml", fixStyles], ["word/numbering.xml", fixNumbering]]) {
      if (!parts.has(name)) continue;
      const [put, n] = fix(fromUtf8(replace.get(name) || parts.get(name)), csFont);
      if (n) {
        replace.set(name, utf8(put));
        repaired["5"] = (repaired["5"] || 0) + n;
      }
    }
    if (repaired["2"] || repaired["5"]) {
      chosen = { code: "font", message: "complex-script font written where a run named none: '" + csFont + "' — " + why };
    }
  }
  return [replace, repaired, chosen];
}
