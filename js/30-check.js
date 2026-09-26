// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// thai-docx — check: the JavaScript port of scripts/thai_docx/check.py. Findings,
// messages, counts and their order match it exactly (ADR 0004, 0023, 0008, 0040).

const OOXML = /*@@OOXML@@*/ null;

const W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main";
const RPR_ORDER = OOXML.rpr_order;
const PPR_ORDER = OOXML.ppr_order;
const SETTINGS_ORDER = OOXML.settings_order;
const SECTPR_ORDER = OOXML.sectpr_order;
const TBLPR_ORDER = OOXML.tblpr_order;
const TRPR_ORDER = OOXML.trpr_order;
const TCPR_ORDER = OOXML.tcpr_order;
const LVL_ORDER = OOXML.lvl_order;
const STYLE_ORDER = OOXML.style_order;

// Each name's place in an order; the names of a list inside it share one (ooxml.py's rank).
function rankOf(order) {
  const out = new Map();
  order.forEach((entry, i) => {
    for (const name of typeof entry === "string" ? [entry] : entry) out.set(name, i);
  });
  return out;
}

// ST_OnOff: "off" is one of these values, "on" any other or none (ooxml.py's is_on).
const OFF = new Set(["0", "false", "off"]);
function isOn(el) {
  return !OFF.has(el.get(w("val")));
}
const INVISIBLE = OOXML.invisible;
// Every other format character (Unicode category Cf), from the list both implementations read,
// so neither asks its own runtime's Unicode tables, which differ in version (ADR 0008).
const FORMAT = new Set(OOXML.format.flatMap(([first, last]) => Array.from({ length: last - first + 1 }, (_, k) => String.fromCodePoint(first + k))));

// U+FDD0 to U+FDEF, and the last two code points of every plane.
function isNoncharacter(cp) {
  return (cp >= 0xfdd0 && cp <= 0xfdef) || (cp & 0xfffe) === 0xfffe;
}

// How a character a reader cannot see is named in a message, or null.
function unseen(ch) {
  if (Object.prototype.hasOwnProperty.call(INVISIBLE, ch)) return INVISIBLE[ch];
  const cp = ch.codePointAt(0);
  if (FORMAT.has(ch)) return "U+" + cp.toString(16).toUpperCase().padStart(4, "0") + ", a format character";
  if (isNoncharacter(cp)) return "U+" + cp.toString(16).toUpperCase().padStart(4, "0") + ", a noncharacter";
  return null;
}
const THAI_FONTS = new Set(OOXML.thai_fonts);

const MAX_PART = 32 * 1024 * 1024;
const MAX_TOTAL = 64 * 1024 * 1024;
const MAX_FILE = 64 * 1024 * 1024;
const COMPAT_URI = "http://schemas.microsoft.com/office/word";
const TEXT_PARTS = /^word\/(document|comments|footnotes|endnotes|header[0-9]*|footer[0-9]*)\.xml$/;
const RELATIONSHIPS = ["http://schemas.openxmlformats.org/officeDocument/2006/relationships/",
  "http://purl.oclc.org/ooxml/officeDocument/relationships/"];
const TEXT_KINDS = ["header", "footer", "footnotes", "endnotes", "comments"];
const STRICT_W = "http://purl.oclc.org/ooxml/wordprocessingml/main";

function w(tag) {
  return "{" + W + "}" + tag;
}

function local(tag) {
  const i = tag.lastIndexOf("}");
  return i < 0 ? tag : tag.slice(i + 1);
}

const RPR_RANK = rankOf(RPR_ORDER), PPR_RANK = rankOf(PPR_ORDER), SETTINGS_RANK = rankOf(SETTINGS_ORDER);
const LVL_RANK = rankOf(LVL_ORDER), STYLE_RANK = rankOf(STYLE_ORDER);
const STRUCTURE = [["sectPr", rankOf(SECTPR_ORDER)], ["tblPr", rankOf(TBLPR_ORDER)], ["trPr", rankOf(TRPR_ORDER)],
  ["tcPr", rankOf(TCPR_ORDER)]];

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
  // every entry, not only the parts read (check.py says why)
  for (const e of entries) {
    if ((e.method !== 0 && e.method !== 8) || (e.flags & 0x1)) {
      report.find("package", e.name, "entry uses encryption or a compression method other than stored or deflate");
      return null;
    }
  }
  const parts = new Map();
  for (const e of entries) {
    if (!e.name.endsWith(".xml") && !e.name.endsWith(".rels")) continue;
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
    // Decided on the bytes: a NUL is valid UTF-8 and never valid XML, and it is what UTF-16 and
    // UCS-4 are full of (check.py's _parse says why that matters there)
    if (data.includes(0)) {
      report.find("package", name, "XML part is not UTF-8");
      continue;
    }
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

// A part name matches in any case (OPC); ASCII only, which both runtimes lower alike.
function asciiLower(name) {
  return name.replace(/[A-Z]/g, (c) => String.fromCharCode(c.charCodeAt(0) + 32));
}

// A relationship's target as a part name: relative to the folder of `source`, or to the
// package's root when it begins with a slash.
function resolvePart(source, target) {
  const path = target.startsWith("/") ? [] : source.split("/").slice(0, -1);
  for (const segment of target.split("/")) {
    if (segment === "..") {
      if (path.length) path.pop();
    } else if (segment !== "" && segment !== ".") path.push(segment);
  }
  return path.join("/");
}

// [kind, part] for each relationship of `source` ("" for the package's own) to a part the
// package holds. `names` maps each part name, lowered, to the name itself.
function related(names, treeOf, source) {
  const cut = source.lastIndexOf("/");
  const folder = cut < 0 ? "" : source.slice(0, cut), file = source.slice(cut + 1);
  const relsName = names.get(asciiLower((folder ? folder + "/" : "") + "_rels/" + file + ".rels"));
  const root = relsName === undefined ? null : treeOf(relsName);
  const out = [];
  for (const rel of root === null ? [] : root.children) {
    const kind = rel.get("Type") || "";
    const prefix = RELATIONSHIPS.find((p) => kind.startsWith(p));
    if (local(rel.tag) !== "Relationship" || rel.get("TargetMode") === "External" || prefix === undefined) continue;
    const name = names.get(asciiLower(resolvePart(source, rel.get("Target") || "")));
    if (name !== undefined) out.push([kind.slice(prefix.length), name]);
  }
  return out;
}

// Which part is which, as Word finds them (check.py's part_roles says how).
function partRoles(names, treeOf) {
  const lowered = new Map();
  for (let i = names.length - 1; i >= 0; i--) lowered.set(asciiLower(names[i]), names[i]);
  const found = related(lowered, treeOf, "").find(([kind]) => kind === "officeDocument");
  let main = found === undefined ? null : found[1];
  if (main === null && names.includes("word/document.xml")) main = "word/document.xml";
  const roles = { document: main, text: [], footnotes: null, styles: null, numbering: null, settings: null };
  if (main === null) return roles;
  const text = new Set([main, ...names.filter((n) => TEXT_PARTS.test(n))]);
  for (const [kind, name] of related(lowered, treeOf, main)) {
    if (TEXT_KINDS.includes(kind)) text.add(name);
    if (["footnotes", "styles", "numbering", "settings"].includes(kind) && roles[kind] === null) roles[kind] = name;
  }
  for (const kind of ["footnotes", "styles", "numbering", "settings"]) {
    if (roles[kind] === null && names.includes("word/" + kind + ".xml")) roles[kind] = "word/" + kind + ".xml";
  }
  roles.text = names.filter((n) => text.has(n));
  return roles;
}

// partRoles for a package the checker has already read without a finding that refuses it.
function partRolesOf(parts) {
  return partRoles([...parts.keys()], (name) => {
    if (!name.endsWith(".rels") || !parts.has(name)) return null;
    const text = fromUtf8(parts.get(name));
    if (text === null) return null;
    try {
      return parseXml(text);
    } catch (e) {
      if (!(e instanceof XmlError)) throw e;
      return null;
    }
  });
}

// A run's formatting as a comparable value; rsid attributes are noise. Flat — each element
// opens, its children follow, and it closes — and built with a stack of its own, because the
// input sets the depth and neither implementation reads by recursion where it does (ADR 0017).
function canonical(el) {
  if (el === null) return "";
  const out = [];
  const pending = [el];
  while (pending.length) {
    const node = pending.pop();
    if (node === null) {
      out.push("/"); // the element before it closes here
      continue;
    }
    const attrs = [];
    for (const [k, v] of node.attrib) if (!local(k).startsWith("rsid")) attrs.push([local(k), v]);
    attrs.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0));
    out.push(JSON.stringify([local(node.tag), attrs]));
    pending.push(null);
    for (let i = node.children.length - 1; i >= 0; i--) pending.push(node.children[i]);
  }
  return out.join("\n");
}

function checkOrder(el, ranks, part, report, what) {
  let lastRank = -1;
  let lastName = "";
  for (const child of el.children) {
    const name = local(child.tag);
    if (!ranks.has(name)) continue;
    const at = ranks.get(name);
    if (at < lastRank) {
      report.find("order", part, "in " + what + ", <w:" + name + "> must come before <w:" + lastName + ">");
      return;
    }
    lastRank = at;
    lastName = name;
  }
}

function checkStructure(root, part, report) {
  for (const [tag, ranks] of STRUCTURE) for (const el of root.iter(w(tag))) checkOrder(el, ranks, part, report, "w:" + tag);
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

function checkSettings(part, root, report) {
  checkOrder(root, SETTINGS_RANK, part, report, "w:settings");
  const modes = [];
  for (const cs of root.iter(w("compatSetting"))) {
    if (cs.get(w("name")) === "compatibilityMode" && cs.get(w("uri")) === COMPAT_URI) modes.push(cs.get(w("val")));
  }
  if (!(modes.length === 1 && modes[0] === "15")) {
    const shown = modes.map((m) => (m === null ? "None" : m)).join(", ");
    report.find("1", part, "compatibilityMode declared as " + (shown || "nothing") + "; must be exactly one 15");
  }
}

function checkTextPart(name, root, report, roles) {
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
      // deleted text is text (check.py says why)
      const texts = run.children.filter((c) => c.tag === w("t") || c.tag === w("delText"));
      const hasText = texts.length > 0;
      let thai = false;
      for (const t of texts) for (const ch of t.text || "") if (isThai(ch)) thai = true;
      if (rpr !== null) {
        checkOrder(rpr, RPR_RANK, name, report, "a run's w:rPr");
        checkRprTwins(rpr, name, report, "a run", thai);
      }
      if (hasText) {
        report.counts.runs = (report.counts.runs || 0) + 1;
        const cs = rpr === null ? null : rpr.find(w("cs"));
        const marked = cs !== null && isOn(cs);
        // one direction only: a run that holds no complex script may carry the marker, because
        // --force-cs-whole-doc writes it on every run and that file is ours too
        if (thai && !marked) {
          report.find("2", name, "a run whose text is complex script has no <w:cs/> element");
        }
        if (marked) {
          const lang = rpr.find(w("lang"));
          if (lang !== null && lang.get(w("bidi")) === "th-TH") {
            report.counts.thai_language_runs = (report.counts.thai_language_runs || 0) + 1;
          }
        }
        for (const t of texts) {
          const text = t.text || "";
          // the five by name first, as they always were; then any other in text order
          let label = null;
          for (const ch of Object.keys(INVISIBLE)) {
            if (text.indexOf(ch) !== -1) {
              label = INVISIBLE[ch];
              break;
            }
          }
          if (label === null) {
            for (const ch of text) {
              label = unseen(ch);
              if (label !== null) break;
            }
          }
          if (label !== null) report.find("invisible", name, "text contains " + label);
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
    if (ppr === null) continue;
    checkOrder(ppr, PPR_RANK, name, report, "a paragraph's w:pPr");
    const mark = ppr.find(w("rPr"));
    if (mark !== null) {
      checkOrder(mark, RPR_RANK, name, report, "a paragraph mark's w:rPr");
      checkRprTwins(mark, name, report, "a paragraph mark", false);
    }
  }
  checkStructure(root, name, report);
  report.counts.paragraphs = (report.counts.paragraphs || 0) + root.countDescendants(w("p"));
  if (name === roles.document) report.counts.tables = root.countDescendants(w("tbl"));
  if (name === roles.footnotes) {
    let k = 0;
    for (const f of root.iter(w("footnote"))) {
      const type = f.get(w("type"));
      if (type !== "separator" && type !== "continuationSeparator") k++;
    }
    report.counts.footnotes = k;
  }
}

function checkStyles(name, root, report) {
  // what a tracked change says the formatting was: history, not formatting any text has
  const history = new Set();
  for (const change of root.iter()) {
    if (change.tag !== w("rPrChange") && change.tag !== w("pPrChange")) continue;
    for (const el of change.iter()) if (el !== change) history.add(el);
  }
  for (const style of root.iter(w("style"))) checkOrder(style, STYLE_RANK, name, report, "w:style");
  for (const rpr of root.iter(w("rPr"))) {
    checkOrder(rpr, RPR_RANK, name, report, "a style's w:rPr");
    if (!history.has(rpr)) checkRprTwins(rpr, name, report, "a style", true);
  }
  for (const ppr of root.iter(w("pPr"))) checkOrder(ppr, PPR_RANK, name, report, "a style's w:pPr");
  checkStructure(root, name, report);
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
    checkOrder(lvl, LVL_RANK, name, report, "w:lvl");
    const ppr = lvl.find(w("pPr"));
    if (ppr !== null) checkOrder(ppr, PPR_RANK, name, report, "a numbering level's w:pPr");
    const rpr = lvl.find(w("rPr"));
    if (rpr !== null) {
      checkOrder(rpr, RPR_RANK, name, report, "a numbering level's w:rPr");
      checkRprTwins(rpr, name, report, "a numbering level", false);
    }
  }
}

// Check a package's bytes; `label` is what the report names as its file.
function checkBytes(bytes, label) {
  const report = new Report(label);
  const parts = readParts(bytes, report);
  if (parts === null) return report;
  const trees = parseParts(parts, report);
  const roles = partRoles([...parts.keys()], (name) => (trees.has(name) ? trees.get(name) : null));
  const document = roles.document;
  if (document === null) {
    report.find("package", "", "no main document (word/document.xml, or the part _rels/.rels names);" +
      " not a WordprocessingML package");
    return report;
  }
  if (!trees.has(document)) return report;  // not UTF-8 or not well-formed, and found so above
  const tag = trees.get(document).tag;
  if (tag !== w("document")) {
    if (tag.startsWith("{" + STRICT_W + "}")) {
      report.find("package", document, "Strict Open XML (ISO/IEC 29500 Strict) is not read: every element" +
        " would be missed; save it from Word as Word Document (.docx)");
    } else report.find("package", document, "the main document is not a WordprocessingML document");
    return report;
  }
  const named = new Set([roles.styles, roles.numbering, roles.settings, ...roles.text].filter((n) => n !== null));
  for (const [name, root] of trees) {
    if (!name.startsWith("word/") && !named.has(name)) continue;
    let off = true;
    for (const el of root.iter(w("noProof"))) if (isOn(el)) off = false;
    if (!off) report.find("3", name, "<w:noProof/> switches Thai proofing — and Thai line breaking — off");
  }
  const settings = roles.settings || "word/settings.xml";
  if (!trees.has(settings)) report.find("1", settings, "no settings part; compatibilityMode is not declared");
  else checkSettings(settings, trees.get(settings), report);
  for (const name of roles.text) if (trees.has(name)) checkTextPart(name, trees.get(name), report, roles);
  if (roles.styles !== null && trees.has(roles.styles)) checkStyles(roles.styles, trees.get(roles.styles), report);
  if (roles.numbering !== null && trees.has(roles.numbering)) checkNumbering(roles.numbering, trees.get(roles.numbering), report);
  return report;
}
