// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// thai-docx — check: the JavaScript port of scripts/thai_docx/check.py. Findings,
// messages, counts and their order match it exactly (ADR 0004, 0005, 0008, 0011).

const OOXML = /*@@OOXML@@*/ null;

const W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main";
const RPR_ORDER = OOXML.rpr_order;
const PPR_ORDER = OOXML.ppr_order;
const SETTINGS_ORDER = OOXML.settings_order;
const INVISIBLE = OOXML.invisible;
const THAI_FONTS = new Set(OOXML.thai_fonts);

const MAX_PART = 32 * 1024 * 1024;
const MAX_TOTAL = 64 * 1024 * 1024;
const MAX_FILE = 64 * 1024 * 1024;
const COMPAT_URI = "http://schemas.microsoft.com/office/word";
const TEXT_PARTS = /^word\/(document|comments|footnotes|endnotes|header[0-9]*|footer[0-9]*)\.xml$/;

function w(tag) {
  return "{" + W + "}" + tag;
}

function local(tag) {
  const i = tag.lastIndexOf("}");
  return i < 0 ? tag : tag.slice(i + 1);
}

function isThai(ch) {
  return ch >= "฀" && ch <= "๿";
}

class Report {
  constructor(label) {
    this.path = label;
    this.error = null;  // the path could not be read at all: not about the document
    this.findings = [];
    this.warnings = [];
    this.counts = {};
  }

  find(code, part, message) {
    this.findings.push({ code, part, message });
  }

  warn(code, part, message) {
    if (!this.warnings.some((x) => x.code === code && x.part === part && x.message === message)) {
      this.warnings.push({ code, part, message });
    }
  }

  get ok() {
    return this.error === null && this.findings.length === 0;
  }

  asDict() {
    if (this.error !== null) return { ok: false, file: this.path, error: this.error };
    return { ok: this.ok, file: this.path, counts: this.counts, findings: this.findings, warnings: this.warnings };
  }
}

function readParts(bytes, report) {
  if (bytes.length > MAX_FILE) {
    report.find("size", "", "package file is larger than " + MAX_FILE + " bytes; refused");
    return null;
  }
  let entries;
  try {
    entries = readZipDirectory(bytes);
  } catch (e) {
    if (!(e instanceof ZipError)) throw e;
    report.find("package", "", "not a zip package");
    return null;
  }
  const seen = new Set();
  for (const e of entries) {
    if (seen.has(e.name)) {
      report.find("package", e.name, "entry name appears more than once");
      return null;
    }
    seen.add(e.name);
  }
  let total = 0;
  for (const e of entries) total += e.fileSize;
  if (total > MAX_TOTAL || entries.some((e) => e.fileSize > MAX_PART)) {
    report.find("size", "", "package would decompress to " + total + " bytes; refused");
    return null;
  }
  if (!seen.has("word/document.xml")) {
    report.find("package", "", "no word/document.xml; not a WordprocessingML package");
    return null;
  }
  const parts = new Map();
  for (const e of entries) {
    if (!e.name.endsWith(".xml") && !e.name.endsWith(".rels")) continue;
    if ((e.method !== 0 && e.method !== 8) || (e.flags & 0x1)) {
      report.find("package", e.name, "entry uses encryption or a compression method other than stored or deflate");
      return null;
    }
    let data;
    try {
      data = readZipEntry(bytes, e);
    } catch (err) {
      if (!(err instanceof ZipError)) throw err;
      report.find("package", e.name, "entry cannot be read (corrupt data or checksum)");
      return null;
    }
    let latin = "";
    for (let i = 0; i < data.length; i++) latin += String.fromCharCode(data[i]);
    if (/<!DOCTYPE/i.test(latin)) {
      report.find("doctype", e.name, "XML part declares a DOCTYPE; refused");
      return null;
    }
    parts.set(e.name, data);
  }
  return parts;
}

const RE_DECLARED_ENCODING = /^\uFEFF?<\?xml[^>]*?[ \t\r\n]encoding[ \t\r\n]*=[ \t\r\n]*["']([^"']*)["']/;

// No declared encoding, or UTF-8: the only XML both implementations read the same way.
function declaresUtf8(text) {
  const m = RE_DECLARED_ENCODING.exec(text);
  return m === null || ["utf-8", "utf8"].includes(m[1].toLowerCase());
}

function parseParts(parts, report) {
  const trees = new Map();
  for (const [name, data] of parts) {
    const text = data.length >= 2 && ((data[0] === 0xff && data[1] === 0xfe) || (data[0] === 0xfe && data[1] === 0xff)) ? null : fromUtf8(data);
    if (text === null || !declaresUtf8(text)) {
      report.find("package", name, "XML part is not UTF-8");
      continue;
    }
    try {
      trees.set(name, parseXml(text));
    } catch (e) {
      if (!(e instanceof XmlError)) throw e;
      report.find("package", name, "XML is not well-formed");
    }
  }
  return trees;
}

function canonical(el) {
  if (el === null) return "";
  const attrs = [];
  for (const [k, v] of el.attrib) if (!local(k).startsWith("rsid")) attrs.push([local(k), v]);
  attrs.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0));
  return JSON.stringify([local(el.tag), attrs, el.children.map(canonical)]);
}

function checkOrder(el, order, part, report, what) {
  let lastRank = -1;
  let lastName = "";
  for (const child of el.children) {
    const name = local(child.tag);
    const rank = order.indexOf(name);
    if (rank < 0) continue;
    if (rank < lastRank) {
      report.find("order", part, "in " + what + ", <w:" + name + "> must come before <w:" + lastName + ">");
      return;
    }
    lastRank = rank;
    lastName = name;
  }
}

function checkRprTwins(rpr, part, report, what, thai) {
  const fonts = rpr.find(w("rFonts"));
  if (fonts !== null) {
    const latin = ["ascii", "hAnsi", "asciiTheme", "hAnsiTheme"].some((a) => !!fonts.get(w(a)));
    const cs = fonts.get(w("cs")) || fonts.get(w("cstheme"));
    if (latin && !cs) report.find("5", part, "in " + what + ", w:rFonts names a Latin font but no w:cs font");
    else if (thai && cs && !fonts.get(w("cstheme")) && !THAI_FONTS.has(cs.toLowerCase())) {
      report.warn("font", part, "in " + what + ", complex-script font '" + cs + "' is not known to carry Thai glyphs");
    }
  }
  for (const [latin, twin] of [["sz", "szCs"], ["b", "bCs"], ["i", "iCs"]]) {
    if (rpr.find(w(latin)) !== null && rpr.find(w(twin)) === null) {
      report.find("5", part, "in " + what + ", <w:" + latin + "> has no <w:" + twin + "> beside it");
    }
  }
}

function checkSettings(root, report) {
  const part = "word/settings.xml";
  checkOrder(root, SETTINGS_ORDER, part, report, "w:settings");
  const modes = [];
  for (const cs of root.iter(w("compatSetting"))) {
    if (cs.get(w("name")) === "compatibilityMode" && cs.get(w("uri")) === COMPAT_URI) modes.push(cs.get(w("val")));
  }
  if (!(modes.length === 1 && modes[0] === "15")) {
    const shown = modes.map((m) => (m === null ? "None" : m)).join(", ");
    report.find("1", part, "compatibilityMode declared as " + (shown || "nothing") + "; must be exactly one 15");
  }
}

function checkTextPart(name, root, report) {
  for (const parent of root.iter()) {
    if (!parent.children.some((c) => c.tag === w("r"))) continue;
    let previous = null;
    let prevHasText = false;
    for (const run of parent.children) {
      if (run.tag !== w("r")) {
        previous = null;
        prevHasText = false;
        continue;
      }
      const rpr = run.find(w("rPr"));
      const texts = run.findall(w("t"));
      const hasText = texts.length > 0;
      if (rpr !== null) {
        checkOrder(rpr, RPR_ORDER, name, report, "a run's w:rPr");
        let thai = false;
        for (const t of texts) for (const ch of t.text || "") if (isThai(ch)) thai = true;
        checkRprTwins(rpr, name, report, "a run", thai);
      }
      if (hasText) {
        report.counts.runs = (report.counts.runs || 0) + 1;
        if (rpr === null || rpr.find(w("cs")) === null) {
          report.find("2", name, "a run with text has no <w:cs/> element");
        } else {
          const lang = rpr.find(w("lang"));
          if (lang === null || lang.get(w("bidi")) !== "th-TH") report.find("2", name, 'a run with text has no <w:lang w:bidi="th-TH"/>');
        }
        for (const t of texts) {
          for (const ch of Object.keys(INVISIBLE)) {
            if ((t.text || "").indexOf(ch) !== -1) {
              report.find("invisible", name, "text contains " + INVISIBLE[ch]);
              break;
            }
          }
        }
      }
      const shape = canonical(rpr);
      if (hasText && prevHasText && shape === previous) {
        report.find("4", name, "two adjacent runs carry identical formatting; a word may be split across them");
      }
      previous = shape;
      prevHasText = hasText;
    }
  }
  for (const p of root.iter(w("p"))) {
    const ppr = p.find(w("pPr"));
    if (ppr !== null) checkOrder(ppr, PPR_ORDER, name, report, "a paragraph's w:pPr");
  }
  report.counts.paragraphs = (report.counts.paragraphs || 0) + root.countDescendants(w("p"));
  if (name === "word/document.xml") report.counts.tables = root.countDescendants(w("tbl"));
  if (name === "word/footnotes.xml") {
    let k = 0;
    for (const f of root.iter(w("footnote"))) {
      const type = f.get(w("type"));
      if (type !== "separator" && type !== "continuationSeparator") k++;
    }
    report.counts.footnotes = k;
  }
}

function checkStyles(name, root, report) {
  for (const rpr of root.iter(w("rPr"))) {
    checkOrder(rpr, RPR_ORDER, name, report, "a style's w:rPr");
    checkRprTwins(rpr, name, report, "a style", true);
  }
  for (const ppr of root.iter(w("pPr"))) checkOrder(ppr, PPR_ORDER, name, report, "a style's w:pPr");
}

function checkNumbering(name, root, report) {
  for (const lvl of root.iter(w("lvl"))) {
    const fmt = lvl.find(w("numFmt"));
    const rprForFonts = lvl.find(w("rPr"));
    const fonts = rprForFonts === null ? null : rprForFonts.find(w("rFonts"));
    if (fmt !== null && fmt.get(w("val")) === "bullet" && fonts !== null) {
      if ([...fonts.attrib.values()].some((v) => v === "Symbol")) {
        report.find("5", name, "a bullet level uses the Symbol font; bullets need a Thai-capable font");
      }
    }
    const rpr = lvl.find(w("rPr"));
    if (rpr !== null) checkOrder(rpr, RPR_ORDER, name, report, "a numbering level's w:rPr");
  }
}

// Check a package's bytes; `label` is what the report names as its file.
function checkBytes(bytes, label) {
  const report = new Report(label);
  const parts = readParts(bytes, report);
  if (parts === null) return report;
  const trees = parseParts(parts, report);
  for (const [name, root] of trees) {
    if (name.startsWith("word/") && root.findDescendant(w("noProof")) !== null) {
      report.find("3", name, "<w:noProof/> switches Thai proofing — and Thai line breaking — off");
    }
  }
  const settings = trees.get("word/settings.xml");
  if (settings === undefined) report.find("1", "word/settings.xml", "no settings part; compatibilityMode is not declared");
  else checkSettings(settings, report);
  for (const [name, root] of trees) if (TEXT_PARTS.test(name)) checkTextPart(name, root, report);
  if (trees.has("word/styles.xml")) checkStyles("word/styles.xml", trees.get("word/styles.xml"), report);
  if (trees.has("word/numbering.xml")) checkNumbering("word/numbering.xml", trees.get("word/numbering.xml"), report);
  return report;
}
