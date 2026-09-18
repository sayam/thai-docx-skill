// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// Repair a .docx this skill did not write: the attributes that break Thai, never the text
// (ADR 0032) — the port of thai_docx/repair.py. This version repairs two findings and
// reports every other one:
//
//   1  compatibilityMode is not exactly one 15 — set it, or drop the ones that are not 15
//   3  <w:noProof/> switches Thai proofing, and Thai line breaking, off — remove it
//
// A part is edited as text, not re-serialised from a tree: a tree would rewrite prefixes,
// attribute order and empty-element spelling across the whole part, and ADR 0032 allows only
// the attributes named. Both elements below are empty ones, so the shapes are few.

const REPAIR_USAGE = "usage: thai_docx repair IN.docx OUT.docx";
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

// The parts to write anew, and how many of each code were repaired.
function repairParts(parts, findings) {
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
  return [replace, repaired];
}
