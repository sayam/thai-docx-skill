// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// Repair a .docx this skill did not write: the attributes that break Thai, never the text
// (ADR 0037) — the port of thai_docx/repair.py, whose docstring lists the findings this
// version repairs (1, 2, 3, 5 and order) and reports every other one.
//
// A part is edited as text, not re-serialised from a tree: a tree would rewrite prefixes,
// attribute order and empty-element spelling across the whole part, and ADR 0037 allows only
// the attributes named. Every tag is read the one way XML writes it (ATTRS below).

const REPAIR_USAGE = 'usage: thai_docx repair IN.docx OUT.docx [--font "TH Sarabun New"] [--thai-language]' +
  " [--force-cs-whole-doc]";
// Every start tag is read the one way XML writes it: a quoted value may hold `>` or `/`, in
// either quote, and a tag that ends `/>` is empty. Read any other way, a `>` inside a value
// ended the tag in the middle of it and the part was written back broken.
const ATTRS = "(?:\\s(?:[^<>\"'/]|/(?!>)|\"[^\"]*\"|'[^']*')*)?";

// `<name …>` or `<name …/>`; group 1 is the `/` of an empty element.
function opening(name, flags) {
  return new RegExp("<" + name + ATTRS + "(\\/?)>", flags === undefined ? "g" : flags);
}

// the one run shape a split may touch: properties, if any, then one w:t holding text and
// nothing else — no tab, no break, no second w:t, which a split would read as text
const RE_SIMPLE_INNER = new RegExp("^(<w:rPr" + ATTRS + ">[\\s\\S]*?<\\/w:rPr>)?(<w:t" + ATTRS + ">)([^<]*)<\\/w:t>$");
const RE_PRESERVE = /xml:space\s*=\s*["']preserve["']/;
// a run's text: its w:t, and its w:delText — deleted text is text (check.py says why)
const RE_T_START = new RegExp("<w:(?:t|delText)" + ATTRS + ">");

class RepairError extends Error {}
const RE_NO_PROOF = new RegExp("<w:noProof" + ATTRS + "(?:\\/>|>\\s*<\\/w:noProof>)", "g");
const RE_COMPAT_SETTING = new RegExp("<w:compatSetting" + ATTRS + "(?:\\/>|>\\s*<\\/w:compatSetting\\s*>)", "g"); // either close
const RE_ATTR = /([\w:]+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g;
const VALUE = "\\s*=\\s*(?:\"[^\"]*\"|'[^']*')";
// What a part says in its tags, and only there (repair.py says why: D-03, D-05)
// one pass from the left: what is not markup is stepped over whole, so nothing inside it is read
const RE_START_TAG = /(<!--[\s\S]*?-->|<!\[CDATA\[[\s\S]*?\]\]>|<\?[\s\S]*?\?>)|<([A-Za-z_][\w.:-]*)((?:\s+[^\s=/>]+\s*=\s*(?:"[^"]*"|'[^']*'))*)\s*\/?>/g;
const RE_ATTRIBUTE = /([^\s=/>]+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g;

// Each start tag's name and its attributes, as [name, value] in the order written, whichever
// quote holds the value.
function* startTags(xml) {
  for (const m of xml.matchAll(RE_START_TAG)) {
    if (m[1] === undefined) yield [m[2], [...m[3].matchAll(RE_ATTRIBUTE)].map((a) => [a[1], a[2] !== undefined ? a[2] : a[3]])];
  }
}

// `raw` with one more attribute in its start tag, however the element closes — _with_attribute()
// in thai_docx/repair.py says why
function withAttribute(raw, attribute) {
  const at = new RegExp("^<[^\\s/>]+" + ATTRS).exec(raw)[0].length;
  return raw.slice(0, at).replace(/\s+$/, "") + " " + attribute + raw.slice(at);
}

function tagAttrs(tag) {
  const out = new Map();
  for (const m of tag.matchAll(RE_ATTR)) out.set(m[1], m[2] !== undefined ? m[2] : m[3]);
  return out;
}

// A switch that says off (ST_OnOff), as the checker reads it.
function saysOff(tag) {
  const value = tagAttrs(tag).get("w:val");
  return value !== undefined && OFF.has(value);
}

// Where the run properties of every run whose text holds no complex script are: code, whose
// <w:noProof/> the checker does not report (repair.py's _proofless_code; B-D2).
function prooflessSpans(xml) {
  const spans = [];
  const re = new RegExp(RE_RUN_START.source, "g");
  for (let m = re.exec(xml); m !== null; m = re.exec(xml)) {
    if (m[1]) continue;
    const startEnd = m.index + m[0].length;
    const inner = xml.slice(startEnd, endOf(xml, startEnd, "w:r")[0]);
    const rpr = new RegExp("^<w:rPr" + ATTRS + "(\\/?)>").exec(inner);
    if (rpr === null || rpr[1] || Array.from(runText(inner)).some(isComplex)) continue;
    spans.push([startEnd + rpr[0].length, startEnd + endOf(inner, rpr[0].length, "w:rPr")[0]]);
  }
  return spans;
}

// Every <w:noProof/> that switches proofing off gone. Removing it leaves the default, which is
// proofing on; one that says w:val="0" says that already, and stays, and so does one on code.
function removeNoProof(xml) {
  let count = 0;
  const code = prooflessSpans(xml);
  const out = xml.replace(RE_NO_PROOF, (found, ...rest) => {
    const at = rest[rest.length - 2];
    if (saysOff(found) || code.some(([a, b]) => a <= at && at < b)) return found;
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
        const set = tag.replace(/(w:val\s*=\s*)(?:"[^"]*"|'[^']*')/, '$1"15"');
        tag = set === tag ? withAttribute(tag, 'w:val="15"') : set;
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
const RE_RUN_START = opening("w:r");
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

// `element` among `children`, at the place Word writes it (RPR_NAMES). Nothing already there
// moves: the schema lets a run's properties come in any order.
function insertChild(children, name, element) {
  const rank = RPR_NAMES.indexOf(name.slice(2));
  for (let i = 0; i < children.length; i++) {
    const local = children[i][0].slice(2);
    const at = RPR_NAMES.indexOf(local);
    if (at !== -1 && at > rank) return [...children.slice(0, i), [name, element], ...children.slice(i)];
  }
  return [...children, [name, element]];
}

// `children` without `name`. Removing the marker is how a run says it is not complex script:
// the element has no "off" spelling that Word writes (ADR 0039).
function dropChild(children, name) {
  return children.filter(([there]) => there !== name);
}

// One w:rPr put right: [its new inner XML, code 2 repairs, code 5 repairs, language marks,
// markers taken off a run whose text is not complex script]. `mark` true writes the marker,
// false takes it away, null leaves it as it is — which is what a style gets when the caller
// asked for every run to be marked instead.
function fixRpr(inner, font, mark, thaiLanguage) {
  let children = childrenOf(inner);
  const byName = new Map(children);
  let two = 0, five = 0, marked = 0, unmarked = 0;

  for (const [latin, twin] of [["w:sz", "w:szCs"], ["w:b", "w:bCs"], ["w:i", "w:iCs"]]) {
    if (byName.has(latin) && !byName.has(twin)) {
      const attrs = new RegExp("(\\sw:val" + VALUE + ")").exec(byName.get(latin));
      children = insertChild(children, twin, "<" + twin + (attrs ? attrs[1] : "") + "/>");
      byName.set(twin, "");
      five += 1;
    }
  }

  const fonts = byName.get("w:rFonts");
  if (fonts !== undefined) {
    const hasLatin = LATIN_FONT.some((a) => new RegExp(a + "\\s*=\\s*[\"']").test(fonts));
    const hasCs = /w:cs(?:theme)?\s*=\s*["']/.test(fonts);
    if (hasLatin && !hasCs) {
      const put = withAttribute(fonts, 'w:cs="' + font + '"');
      children = children.map(([n, raw]) => [n, n === "w:rFonts" ? put : raw]);
      five += 1;
    }
  }

  const cs = byName.get("w:cs");
  const csOn = cs !== undefined && !saysOff(cs.slice(0, cs.indexOf(">") + 1));
  if (mark === false && csOn) {
    children = dropChild(children, "w:cs");
    unmarked += 1; // not a finding of its own, so it is counted apart from the code 2 repairs
  }
  if (mark) {
    if (cs === undefined) {
      children = insertChild(children, "w:cs", "<w:cs/>");
      two += 1;
    } else if (!csOn) { // <w:cs w:val="0"/> says the run is not complex script: say it is
      children = children.map(([n, raw]) => [n, n === "w:cs" ? "<w:cs/>" : raw]);
      two += 1;
    }
    if (thaiLanguage) {
      // the Thai complex-script language, only where the caller asked for it (ADR 0038)
      const lang = byName.get("w:lang");
      if (lang === undefined) {
        children = insertChild(children, "w:lang", '<w:lang w:bidi="th-TH"/>');
        marked += 1;
      } else if (!/w:bidi\s*=\s*["']th-TH["']/.test(lang)) {
        const put = new RegExp("w:bidi" + VALUE).test(lang)
          ? lang.replace(new RegExp("w:bidi" + VALUE), 'w:bidi="th-TH"')
          : withAttribute(lang, 'w:bidi="th-TH"');
        children = children.map(([n, raw]) => [n, n === "w:lang" ? put : raw]);
        marked += 1;
      }
    }
  }

  return [children.map(([, raw]) => raw).join(""), two, five, marked, unmarked];
}

// Every `element` in the part with its children in the order the schema fixes.
//
// The elements the schema names are put in that order, **in the places they already occupy**;
// anything it does not name keeps its own place, because the checker skips those and moving
// them would change more than the finding asked for. A permutation is the same bytes in a
// different order, so the part's length never changes and the positions of the other elements
// hold while this walks them.
function reorder(xml, element, order) {
  const rank = rankOf(order);
  // One walk, written out once: the part was once rebuilt whole at every element put right,
  // which took twenty seconds on a part of nine kilobytes. An element of this name can hold
  // another (w:rPrChange holds a w:rPr), so the inner one is put right first, inside the walk
  // of its own element.
  const region = (text) => {
    const out = [];
    let pos = 0, count = 0;
    const re = opening(element);
    for (let m = re.exec(text); m !== null; m = re.exec(text)) {
      if (m.index < pos || m[1]) continue;
      const at = m.index + m[0].length;
      const [innerEnd, elementEnd] = endOf(text, at, element);
      const [pieces, inside] = region(text.slice(at, innerEnd));
      count += inside;
      let inner = pieces.join("");
      const children = childrenOf(inner);
      const known = [];
      for (let i = 0; i < children.length; i++) {
        if (rank.has(children[i][0].slice(2))) known.push([i, children[i]]);
      }
      // a stable sort, so two children of one name keep the order they were written in
      const ordered = known.map((pair, i) => [pair, i])
        .sort((a, b) => (rank.get(a[0][1][0].slice(2)) - rank.get(b[0][1][0].slice(2))) || (a[1] - b[1]))
        .map(([pair]) => pair);
      if (!known.every((pair, i) => pair[1][1] === ordered[i][1][1])) {
        for (let i = 0; i < known.length; i++) children[known[i][0]] = ordered[i][1];
        inner = children.map(([, raw]) => raw).join("");
        count += 1;
      }
      out.push(text.slice(pos, at), inner, text.slice(innerEnd, elementEnd));
      pos = elementEnd;
      re.lastIndex = pos;
    }
    out.push(text.slice(pos));
    return [out, count];
  };
  const [pieces, count] = region(xml);
  return count ? [pieces.join(""), count] : [xml, 0];
}

// The five named entities XML defines, back to the characters they stand for. A numeric
// reference is never unescaped here: a run whose text holds one is not split at all.
function unescapeXml(text) {
  return text.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'").replace(/&amp;/g, "&");
}

// Everything the run's own w:t and w:delText elements hold, as the text reads.
function runText(inner) {
  let text = "";
  const re = new RegExp("<w:(t|delText)" + ATTRS + ">([\\s\\S]*?)<\\/w:\\1>", "g");
  for (let m = re.exec(inner); m !== null; m = re.exec(inner)) text += unescapeXml(m[2]);
  return text;
}

// A run whose text holds both scripts, cut where the script changes (ADR 0039) — or null when
// this run is not one to cut. Only the plain shape is cut: run properties, if any, then one w:t
// and nothing else. A run carrying a field, a drawing, a tab or a break is left whole, and so is
// one whose text holds a numeric character reference, because re-escaping that would change the
// text, which repair may never do (ADR 0023).
// A piece of nothing but format characters (U+200B, U+200D, U+00AD …) belongs to the text
// beside it: cut out on its own it would be a run of its own in the middle of a Thai word, for
// no script it has.
function withInvisiblesJoined(pieces) {
  const out = [];
  let pending = "";
  for (let [complexScript, piece] of pieces) {
    if (/^\p{Cf}*$/u.test(piece)) {
      if (out.length) out[out.length - 1][1] += piece;
      else pending += piece;
      continue;
    }
    piece = pending + piece;
    pending = "";
    if (out.length && out[out.length - 1][0] === complexScript) out[out.length - 1][1] += piece;
    else out.push([complexScript, piece]);
  }
  return out.length ? out : [[false, pending]];
}

// A run Word writes right to left (repair.py's _right_to_left says why: B-08).
function rightToLeft(rprInner) {
  const m = /<w:rtl(?:\s[^>]*)?\/?>/.exec(rprInner);
  return m !== null && !saysOff(m[0]);
}

function splitRun(start, inner, font, counts, thaiLanguage) {
  const m = RE_SIMPLE_INNER.exec(inner);
  if (m === null || m[3].indexOf("&#") !== -1) return null;
  const [, rprRaw] = m;
  let [, , topen] = m;
  const text = unescapeXml(m[3]);
  if (!RE_PRESERVE.test(topen)) {
    if (text !== text.replace(/^[ \t\n\r]+|[ \t\n\r]+$/g, "")) return null; // space an application drops at the ends; cut, it would be kept
    // a space at a cut is inside the text, and only xml:space keeps it there
    topen = topen.slice(0, -1).replace(/\s+$/, "") + ' xml:space="preserve">';
  }
  const pieces = withInvisiblesJoined(scriptRuns(text, "", "", thaiLanguage));
  if (pieces.length < 2) return null;
  const rprInner = rprRaw === undefined ? "" : rprRaw.slice(rprRaw.indexOf(">") + 1, -"</w:rPr>".length);
  if (rightToLeft(rprInner)) return null;
  let out = "";
  for (const [complexScript, piece] of pieces) {
    // the Thai language on Thai alone (B-09)
    const [newBody, two, five, marked, unmarked] = fixRpr(rprInner, font, complexScript, thaiLanguage && Array.from(piece).some(isThai));
    counts["2"] = (counts["2"] || 0) + two;
    counts["5"] = (counts["5"] || 0) + five;
    counts["thai-language"] = (counts["thai-language"] || 0) + marked;
    counts.unmarked = (counts.unmarked || 0) + unmarked;
    out += start + (newBody ? "<w:rPr>" + newBody + "</w:rPr>" : "") + topen + esc(piece) + "</w:t></w:r>";
  }
  counts.split = (counts.split || 0) + 1;
  return out;
}

function fixRuns(xml, font, counts, thaiLanguage, csAll) {
  let out = "", pos = 0;
  const re = new RegExp(RE_RUN_START.source, "g");
  for (let m = re.exec(xml); m !== null; m = re.exec(xml)) {
    if (m.index < pos || m[1]) continue; // <w:r/> holds nothing to mark
    const startEnd = m.index + m[0].length;
    const [innerEnd, elementEnd] = endOf(xml, startEnd, "w:r");
    const inner = xml.slice(startEnd, innerEnd);
    const split = csAll ? null : splitRun(xml.slice(m.index, startEnd), inner, font, counts, thaiLanguage);
    if (split !== null) {
      out += xml.slice(pos, m.index) + split;
      pos = elementEnd;
      re.lastIndex = pos;
      continue;
    }
    out += xml.slice(pos, startEnd) + fixRun(inner, font, counts, thaiLanguage, csAll);
    pos = innerEnd;
    re.lastIndex = pos;
  }
  return out + xml.slice(pos);
}

function fixRun(inner, font, counts, thaiLanguage, csAll) {
  const hasText = RE_T_START.test(inner);
  const mark = csAll ? true : hasText && Array.from(runText(inner)).some(isComplex);
  const rpr = new RegExp("^<w:rPr" + ATTRS + "(\\/?)>").exec(inner);
  let body, restFrom, head = "";
  if (rpr !== null && rpr[1]) {
    body = "";
    restFrom = rpr[0].length;
  } else if (rpr !== null) {
    const [bodyEnd, elementEnd] = endOf(inner, rpr[0].length, "w:rPr");
    body = inner.slice(rpr[0].length, bodyEnd);
    restFrom = elementEnd;
  } else if (mark) {
    body = "";
    restFrom = 0;
  } else {
    return fixRuns(inner, font, counts, thaiLanguage, csAll); // nothing of ours here; look deeper
  }
  const markHere = rightToLeft(body) ? null : mark; // its complex-script properties are in use already (B-08)
  const thai = thaiLanguage && Array.from(runText(inner)).some(isThai); // the Thai language on Thai alone (B-09)
  const [newBody, two, five, marked, unmarked] = fixRpr(body, font, hasText ? markHere : null, thai);
  counts["2"] = (counts["2"] || 0) + two;
  counts["5"] = (counts["5"] || 0) + five;
  counts["thai-language"] = (counts["thai-language"] || 0) + marked;
  counts.unmarked = (counts.unmarked || 0) + unmarked;
  if (newBody) head = "<w:rPr>" + newBody + "</w:rPr>";
  else if (rpr !== null) head = inner.slice(0, restFrom);
  return head + fixRuns(inner.slice(restFrom), font, counts, thaiLanguage, csAll);
}

// The w:rPr that is a child of this element — a paragraph mark's, a numbering level's — given
// its twins. It formats no run's text, so no marker is written into it or taken out.
function fixOwnRpr(inner, font) {
  for (const [name, raw] of childrenOf(inner)) {
    if (name !== "w:rPr") continue;
    const start = new RegExp("^<w:rPr" + ATTRS + "(\\/?)>").exec(raw);
    if (start[1]) return [inner, 0];
    const [newBody, , five] = fixRpr(raw.slice(start[0].length, raw.length - "</w:rPr>".length), font, null, false);
    if (!five) return [inner, 0];
    // the first w:rPr in this text is this one: what stands before it in a w:pPr or a w:lvl
    // holds none
    const at = inner.indexOf(raw);
    return [inner.slice(0, at) + start[0] + newBody + "</w:rPr>" + inner.slice(at + raw.length), five];
  }
  return [inner, 0];
}

// Every paragraph mark's properties given their twins; a w:pPr inside a tracked change is what
// the paragraph was, and is left as it was.
function fixMarks(xml, font, counts) {
  let out = "", pos = 0;
  const re = opening("w:pPr");
  for (let m = re.exec(xml); m !== null; m = re.exec(xml)) {
    if (m.index < pos || m[1]) continue;
    const startEnd = m.index + m[0].length;
    const [innerEnd] = endOf(xml, startEnd, "w:pPr");
    const [inner, five] = fixOwnRpr(xml.slice(startEnd, innerEnd), font);
    counts["5"] = (counts["5"] || 0) + five;
    out += xml.slice(pos, startEnd) + inner;
    pos = innerEnd;
    re.lastIndex = pos;
  }
  return out + xml.slice(pos);
}

function fixTextPart(xml, font, thaiLanguage, csAll) {
  const counts = {};
  const out = fixMarks(fixRuns(xml, font, counts, thaiLanguage, csAll), font, counts);
  const kept = {};
  for (const [k, v] of Object.entries(counts)) if (v) kept[k] = v;
  return [out, kept];
}

// A style's w:rPr needs its twins; it formats no text, so no Thai marks are added.
// A style's w:rPr needs its twins; it formats no text, so no marker is written into one. The
// marker is taken *out*, though, and that is the half without which the rest does nothing: w:cs
// inherits down docDefaults and the styles to a run, so a run that leaves it off is only saying
// "whatever the chain says" (ADR 0039). Asked to mark every run instead, the chain is left
// exactly as it was — each run then says it for itself.
function fixStyles(xml, font, csAll) {
  let out = "", pos = 0, five = 0, unmarked = 0;
  const re = opening("w:rPr");
  for (let m = re.exec(xml); m !== null; m = re.exec(xml)) {
    if (m.index < pos || m[1]) continue;
    const startEnd = m.index + m[0].length;
    const [innerEnd] = endOf(xml, startEnd, "w:rPr");
    const [newBody, , n, , off] = fixRpr(xml.slice(startEnd, innerEnd), font, csAll ? null : false, false);
    five += n;
    unmarked += off;
    out += xml.slice(pos, startEnd) + newBody;
    pos = innerEnd;
    re.lastIndex = pos;
  }
  return [out + xml.slice(pos), five, unmarked];
}

// A bullet level drawn in Symbol has no Thai glyphs; give it the document's font. And every
// level's properties their twins.
function fixNumbering(xml, font) {
  let out = "", pos = 0, five = 0;
  const re = opening("w:lvl");
  for (let m = re.exec(xml); m !== null; m = re.exec(xml)) {
    if (m.index < pos || m[1]) continue;
    const startEnd = m.index + m[0].length;
    const [innerEnd] = endOf(xml, startEnd, "w:lvl");
    let level = xml.slice(startEnd, innerEnd);
    if ([...level.matchAll(opening("w:numFmt"))].some((f) => tagAttrs(f[0]).get("w:val") === "bullet")) {
      const fonts = new RegExp("<w:rFonts" + ATTRS + "\\/>").exec(level);
      if (fonts !== null && fonts[0].includes('"Symbol"')) {
        level = level.slice(0, fonts.index) + fonts[0].split('"Symbol"').join('"' + font + '"')
          + level.slice(fonts.index + fonts[0].length);
        five += 1;
      }
    }
    const [put, n] = fixOwnRpr(level, font);
    level = put;
    five += n;
    out += xml.slice(pos, startEnd) + level;
    pos = innerEnd;
    re.lastIndex = pos;
  }
  return [out + xml.slice(pos), five];
}

// The font a run that names none is given — as written into the attribute, and as its name — and
// why (ADR 0037): what the user asked for, else the complex-script font this document already
// uses most, else the skill's default.
function complexScriptFont(parts, asked) {
  if (asked) {
    // what Word reads of the name, as the build writes it — said where it is written
    const kept = fontCut(asked);
    const why = kept === null ? "the font the command was given" : fontCutSaid("the font the command was given", asked, kept);
    // an attribute value, escaped where it is written and by what escapes the build's
    // (repair.py says why); a font found in the document below is taken from an attribute already
    if (kept !== null) asked = kept;
    return [attr(asked).slice(1, -1), asked, why];
  }
  const counted = new Map();
  for (const [name, bytes] of parts) {
    // the XML parts only: an image or a font holds no run properties, and reading one as text
    // is how the two implementations came apart (a picture is not valid UTF-8)
    if (!name.startsWith("word/") || !name.endsWith(".xml")) continue;
    for (const [tag, attributes] of startTags(fromUtf8(bytes))) {
      if (tag !== "w:rFonts") continue;
      for (const [key, found] of attributes) {
        // only a font the checker itself would accept: writing one it warns about would trade
        // a finding for a warning, which is not a repair
        if (key !== "w:cs" || !THAI_FONTS.has(found.toLowerCase())) continue;
        counted.set(found, (counted.get(found) || 0) + 1);
      }
    }
  }
  if (counted.size) {
    let best = null;
    for (const name of [...counted.keys()].sort(byCodePoints)) {
      if (best === null || counted.get(name) > counted.get(best)) best = name;
    }
    // a name the checker accepts holds nothing an attribute escapes
    return [best, best, "the complex-script font this document uses most"];
  }
  return [DEFAULTS.font, DEFAULTS.font, "this skill's default, as the document names none"];
}

// How deep an element may stand in elements of its own name for repair to edit it (repair.py
// says why: D-07), and the element that stands deepest, read with a stack as repair.py reads it.
const MAX_NESTING = 100;
const RE_NESTED_TAG = /<(\/?)([A-Za-z_][\w.:-]*)(?:\s+[^\s=/>]+\s*=\s*(?:"[^"]*"|'[^']*'))*\s*(\/?)>/g;

function deepestNesting(xml) {
  const open = [];
  const depth = new Map();
  let best = "", most = 0;
  for (const m of xml.matchAll(RE_NESTED_TAG)) {
    const [, closing, name, empty] = m;
    if (closing) {
      if (open.length) {
        depth.set(open[open.length - 1], depth.get(open[open.length - 1]) - 1);
        open.pop();
      }
      continue;
    }
    const n = (depth.get(name) || 0) + 1;
    if (n > most) {
      best = name;
      most = n;
    }
    if (!empty) {
      depth.set(name, n);
      open.push(name);
    }
  }
  return [best, most];
}

function isXmlPart(name) {
  return name.startsWith("word/") && asciiLower(name).endsWith(".xml");
}

// A comment, a CDATA section or a processing instruction past the declaration: text that reads
// like tags and is not. Word writes none of them; a part that holds one is left as it came
// rather than edited around them.
function holdsWhatIsNotMarkup(xml) {
  return xml.includes("<!--") || xml.includes("<![CDATA[") || xml.indexOf("<?", 2) !== -1;
}

// The first part that writes WordprocessingML under a prefix other than `w`, or binds `w` to
// something else: every pattern here spells `w:`, and would read such a part wrongly.
function foreignPrefix(parts) {
  for (const name of [...parts.keys()].sort(byCodePoints)) {
    if (!isXmlPart(name)) continue;
    for (const [, attributes] of startTags(fromUtf8(parts.get(name)))) {
      for (const [key, uri] of attributes) {
        if ((key === "xmlns" || key.startsWith("xmlns:")) && (uri === W) !== (key === "xmlns:w")) return name;
      }
    }
  }
  return null;
}

// The parts to write anew, how many of each code were repaired, the font chosen, and the parts
// left as they came because they hold what is not markup.
const ORDERS = [["w:rPr", RPR_ORDER], ["w:pPr", PPR_ORDER], ["w:settings", SETTINGS_ORDER], ["w:sectPr", SECTPR_ORDER],
  ["w:tblPr", TBLPR_ORDER], ["w:trPr", TRPR_ORDER], ["w:tcPr", TCPR_ORDER], ["w:lvl", LVL_ORDER], ["w:style", STYLE_ORDER]];

function repairParts(allParts, findings, font, thaiLanguage, csAll) {
  // found as the checker finds them: by relationship, not by file name
  const roles = partRolesOf(allParts);
  const { styles, numbering, settings } = roles;
  const mine = new Set([...roles.text, styles, numbering, settings].filter((n) => n !== null));
  const ours = (n) => isXmlPart(n) || mine.has(n);
  const left = [...allParts.keys()].filter((n) => ours(n) && holdsWhatIsNotMarkup(fromUtf8(allParts.get(n)))).sort(byCodePoints);
  const parts = new Map([...allParts].filter(([n]) => ours(n) && !left.includes(n)));
  const codes = new Set(findings.map((f) => f.code));
  const replace = new Map();
  const repaired = {};
  if (codes.has("1") && parts.has(settings)) {
    const [put, n] = oneCompatibilityMode(fromUtf8(parts.get(settings)));
    if (n) {
      replace.set(settings, utf8(put));
      repaired["1"] = n;
    }
  }
  if (codes.has("3")) {
    // the XML parts only (above): a picture's bytes can spell <w:noProof/> by chance
    for (const [name, bytes] of parts) {
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
      if (!mine.has(name)) continue;
      let out = fromUtf8(replace.get(name) || bytes), n = 0;
      for (const [element, table] of ORDERS) {
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
  // by default there is always something to look at: a run of Latin that carries the marker is
  // not a finding, so nothing in `codes` would ask for this pass, and taking it off is the
  // repair (ADR 0039). Asked to mark every run instead, this is the work it always was.
  if (codes.has("2") || codes.has("5") || thaiLanguage || !csAll) {
    const [csFont, csName, why] = complexScriptFont(parts, font);
    const text = new Set(roles.text); // a set: a search of a list per part was quadratic (D-13)
    for (const [name, bytes] of parts) {
      if (!text.has(name)) continue;
      const [put, counts] = fixTextPart(fromUtf8(replace.get(name) || bytes), csFont, thaiLanguage, csAll);
      if (Object.keys(counts).length) {
        replace.set(name, utf8(put));
        for (const [code, n] of Object.entries(counts)) repaired[code] = (repaired[code] || 0) + n;
      }
    }
    if (parts.has(styles)) {
      const [put, n, off] = fixStyles(fromUtf8(replace.get(styles) || parts.get(styles)), csFont, csAll);
      if (n || off) {
        replace.set(styles, utf8(put));
        if (n) repaired["5"] = (repaired["5"] || 0) + n;
        if (off) repaired.unmarked = (repaired.unmarked || 0) + off;
      }
    }
    if (parts.has(numbering)) {
      const [put, n] = fixNumbering(fromUtf8(replace.get(numbering) || parts.get(numbering)), csFont);
      if (n) {
        replace.set(numbering, utf8(put));
        repaired["5"] = (repaired["5"] || 0) + n;
      }
    }
    // said only where it was written (repair.py says why), by its name as check shows one
    const written = '"' + csFont + '"';
    const count = (text) => text.split(written).length - 1;
    let after = 0, before = 0;
    for (const [name, bytes] of replace) {
      after += count(fromUtf8(bytes));
      if (parts.has(name)) before += count(fromUtf8(parts.get(name)));
    }
    if (after > before) {
      chosen = { code: "font", message: "complex-script font written where a run named none: '" + quoted(csName) + "' — " + why };
    }
  }
  return [replace, repaired, chosen, left];
}
