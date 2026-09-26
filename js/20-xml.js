// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// thai-docx — XML: the element tree Python's xml.etree.ElementTree builds, for the
// parts the checker reads. Namespaced tags are "{uri}local"; attributes keep only
// non-xmlns names; `text` is the text before the first child. Malformed XML — an
// undefined entity, an unbound prefix, a mismatched or duplicated name, a character
// XML does not allow — throws, as expat does. A DOCTYPE never reaches here: the
// checker refuses it on the raw bytes (ADR 0040 §9).

class XmlError extends Error {}

const XML_NS = "http://www.w3.org/XML/1998/namespace";
const XMLNS_NS = "http://www.w3.org/2000/xmlns/";
// Name characters as expat classifies them, measured by tools/measure_xml_names.py
const XML_NAMES = /*@@XML_NAMES@@*/ null;
const nameClass = (ranges) => "[" + ranges.map(([a, b]) => "\\u" + a.toString(16).padStart(4, "0") + (a === b ? "" : "-\\u" + b.toString(16).padStart(4, "0"))).join("") + "]";
// a name without a colon; expat, reading namespaces, allows one colon between two of these
const RE_NCNAME = new RegExp(nameClass(XML_NAMES.start) + nameClass(XML_NAMES.char) + "*", "y");
const RE_S = /[ \t\n]*/y;
// eslint-disable-next-line no-control-regex -- these are the characters XML 1.0 does not allow
const RE_INVALID_CHAR = /[\x00-\x08\x0B\x0C\x0E-\x1F￾￿]/;

class XElement {
  constructor(tag) {
    this.tag = tag;
    this.attrib = new Map();
    this.children = [];
    this.text = null;
  }

  get(name) {
    return this.attrib.has(name) ? this.attrib.get(name) : null;
  }

  // ElementTree's find(tag): the first direct child with that tag.
  find(tag) {
    for (const c of this.children) if (c.tag === tag) return c;
    return null;
  }

  findall(tag) {
    return this.children.filter((c) => c.tag === tag);
  }

  // ElementTree's iter(tag): this element and every descendant, in document order.
  *iter(tag) {
    const stack = [this];
    while (stack.length) {
      const el = stack.pop();
      if (tag === undefined || el.tag === tag) yield el;
      for (let i = el.children.length - 1; i >= 0; i--) stack.push(el.children[i]);
    }
  }

  // find(".//tag"): the first descendant (not this element) with that tag.
  findDescendant(tag) {
    for (const el of this.iter(tag)) if (el !== this) return el;
    return null;
  }

  countDescendants(tag) {
    let n = 0;
    for (const el of this.iter(tag)) if (el !== this) n++;
    return n;
  }
}

function parseXml(source) {
  let s = source.replace(/\r\n?/g, "\n");
  if (s.charCodeAt(0) === 0xfeff) s = s.slice(1);
  if (RE_INVALID_CHAR.test(s)) throw new XmlError("invalid character");
  let pos = 0;
  const n = s.length;

  const fail = (what) => {
    throw new XmlError(what + " at " + pos);
  };
  const skipS = () => {
    RE_S.lastIndex = pos;
    RE_S.exec(s);
    pos = RE_S.lastIndex;
  };
  const ncname = () => {
    RE_NCNAME.lastIndex = pos;
    const m = RE_NCNAME.exec(s);
    if (m === null) fail("name expected");
    pos = RE_NCNAME.lastIndex;
    return m[0];
  };
  // an element or attribute name: one colon at most, with a name on each side (a
  // second colon is refused by every caller, which expects space, =, / or > next)
  const name = () => {
    let qname = ncname();
    if (s[pos] === ":") {
      pos++;
      qname += ":" + ncname();
    }
    return qname;
  };
  const reference = () => {
    // at "&"
    const end = s.indexOf(";", pos);
    if (end < 0) fail("unterminated reference");
    const body = s.slice(pos + 1, end);
    pos = end + 1;
    if (body[0] === "#") {
      let cp;
      if (/^#x[0-9A-Fa-f]+$/.test(body)) cp = parseInt(body.slice(2), 16);
      else if (/^#[0-9]+$/.test(body)) cp = parseInt(body.slice(1), 10);
      else fail("bad character reference");
      const ok = cp === 0x9 || cp === 0xa || cp === 0xd || (cp >= 0x20 && cp <= 0xd7ff) || (cp >= 0xe000 && cp <= 0xfffd) || (cp >= 0x10000 && cp <= 0x10ffff);
      if (!ok) fail("character reference to a character XML does not allow");
      return String.fromCodePoint(cp);
    }
    switch (body) {
      case "amp": return "&";
      case "lt": return "<";
      case "gt": return ">";
      case "apos": return "'";
      case "quot": return '"';
      default: fail("undefined entity");
    }
    return "";
  };
  const comment = () => {
    // at "<!--"
    const end = s.indexOf("-->", pos + 4);
    if (end < 0) fail("unterminated comment");
    const body = s.slice(pos + 4, end);
    if (body.indexOf("--") !== -1 || body.endsWith("-")) fail("-- inside a comment");
    pos = end + 3;
  };
  const pi = () => {
    // at "<?"
    pos += 2;
    const target = ncname(); // a colon after it is refused below: space or ?> must follow
    if (target.toLowerCase() === "xml") fail("misplaced XML declaration");
    const end = s.indexOf("?>", pos);
    if (end < 0) fail("unterminated processing instruction");
    if (end > pos && !/[ \t\n]/.test(s[pos])) fail("bad processing instruction");
    pos = end + 2;
  };
  const misc = () => {
    for (;;) {
      skipS();
      if (s.startsWith("<!--", pos)) comment();
      else if (s.startsWith("<?", pos)) pi();
      else return;
    }
  };

  // XML declaration
  if (s.startsWith("<?xml", pos) && /[ \t\n?]/.test(s[pos + 5] || "")) {
    const end = s.indexOf("?>", pos);
    if (end < 0) fail("unterminated XML declaration");
    const decl = s.slice(pos + 5, end);
    if (!/^[ \t\n]+version[ \t\n]*=[ \t\n]*("[A-Za-z0-9._-]*"|'[A-Za-z0-9._-]*')([ \t\n]+encoding[ \t\n]*=[ \t\n]*("[A-Za-z][A-Za-z0-9._-]*"|'[A-Za-z][A-Za-z0-9._-]*'))?([ \t\n]+standalone[ \t\n]*=[ \t\n]*("(yes|no)"|'(yes|no)'))?[ \t\n]*$/.test(decl)) fail("bad XML declaration");
    pos = end + 2;
  }
  misc();
  if (s[pos] !== "<") fail("no root element");

  const scopes = [new Map([["xml", XML_NS]])];
  const lookup = (prefix) => {
    for (let i = scopes.length - 1; i >= 0; i--) if (scopes[i].has(prefix)) return scopes[i].get(prefix);
    return undefined;
  };
  const expand = (qname, isAttr) => {
    const colon = qname.indexOf(":");
    if (colon === -1) {
      if (isAttr) return qname;
      const ns = lookup("");
      return ns ? "{" + ns + "}" + qname : qname;
    }
    const prefix = qname.slice(0, colon);
    const ns = lookup(prefix);
    if (ns === undefined) fail("unbound prefix");
    return "{" + ns + "}" + qname.slice(colon + 1);
  };

  // A start tag, at its "<": the name, attributes and namespace scope. Returns the
  // element, its qualified name, and whether it closed itself ("/>").
  const startTag = () => {
    pos += 1;
    const qname = name();
    const raw = [];
    const seen = new Set();
    for (;;) {
      const before = pos;
      skipS();
      if (s[pos] === ">" || s.startsWith("/>", pos)) break;
      if (pos === before) fail("space expected between attributes");
      const an = name();
      skipS();
      if (s[pos] !== "=") fail("= expected");
      pos++;
      skipS();
      const q = s[pos];
      if (q !== '"' && q !== "'") fail("quoted value expected");
      pos++;
      let value = "";
      for (;;) {
        if (pos >= n) fail("unterminated attribute value");
        const c = s[pos];
        if (c === q) { pos++; break; }
        if (c === "<") fail("< in attribute value");
        if (c === "&") { value += reference(); continue; }
        value += c === "\t" || c === "\n" ? " " : c;
        pos++;
      }
      if (seen.has(an)) fail("duplicate attribute");
      seen.add(an);
      raw.push([an, value]);
    }
    const scope = new Map();
    for (const [an, value] of raw) {
      // expat's reserved names: `xml` binds only its own namespace and that namespace
      // no other prefix; `xmlns` is never declared, and its namespace never bound
      if (an === "xmlns") {
        if (value === XML_NS || value === XMLNS_NS) fail("reserved namespace");
        scope.set("", value);
      } else if (an.startsWith("xmlns:")) {
        const prefix = an.slice(6);
        if (prefix === "xmlns") fail("reserved prefix");
        if (value === "") fail("empty namespace for a prefix");
        if ((prefix === "xml") !== (value === XML_NS) || value === XMLNS_NS) fail("reserved namespace");
        scope.set(prefix, value);
      }
    }
    scopes.push(scope);
    const el = new XElement(expand(qname, false));
    const expandedSeen = new Set();
    for (const [an, value] of raw) {
      if (an === "xmlns" || an.startsWith("xmlns:")) continue;
      const key = expand(an, true);
      if (expandedSeen.has(key)) fail("duplicate expanded attribute");
      expandedSeen.add(key);
      el.attrib.set(key, value);
    }
    if (s.startsWith("/>", pos)) {
      pos += 2;
      scopes.pop();
      return [el, qname, true];
    }
    pos += 1; // ">"
    return [el, qname, false];
  };

  // An element and everything inside it. Open elements are kept on a stack, not in
  // recursion, so any depth expat reads is read here too.
  const element = () => {
    const [root, rootName, rootClosed] = startTag();
    if (rootClosed) return root;
    const open = [{ el: root, qname: rootName, text: "", textDone: false }];
    let ampAt = -2; // where the next "&" is; -1 when there is none left
    while (open.length) {
      const top = open[open.length - 1];
      const addText = (t) => {
        if (!top.textDone) top.text += t;
      };
      if (pos >= n) fail("unclosed element");
      const c = s[pos];
      if (c === "<") {
        if (s.startsWith("</", pos)) {
          pos += 2;
          const closing = name();
          if (closing !== top.qname) fail("mismatched end tag");
          skipS();
          if (s[pos] !== ">") fail("> expected");
          pos++;
          if (!top.textDone) top.el.text = top.text === "" ? null : top.text;
          scopes.pop();
          open.pop();
          continue;
        }
        if (s.startsWith("<!--", pos)) { comment(); continue; }
        if (s.startsWith("<?", pos)) { pi(); continue; }
        if (s.startsWith("<![CDATA[", pos)) {
          const end = s.indexOf("]]>", pos + 9);
          if (end < 0) fail("unterminated CDATA");
          addText(s.slice(pos + 9, end));
          pos = end + 3;
          continue;
        }
        if (s.startsWith("<!", pos)) fail("markup declaration in content");
        if (!top.textDone) {
          top.el.text = top.text === "" ? null : top.text;
          top.textDone = true;
        }
        const [child, childName, childClosed] = startTag();
        top.el.children.push(child);
        if (!childClosed) open.push({ el: child, qname: childName, text: "", textDone: false });
        continue;
      }
      if (c === "&") { addText(reference()); continue; }
      const next = s.indexOf("<", pos);
      // the next "&" is searched for again only once pos has passed it: searching from
      // every text chunk scanned to the end of a part with none, quadratic in its size
      if (ampAt !== -1 && ampAt < pos) ampAt = s.indexOf("&", pos);
      let end = next < 0 ? n : next;
      if (ampAt >= 0 && ampAt < end) end = ampAt;
      const chunk = s.slice(pos, end);
      if (chunk.indexOf("]]>") !== -1) fail("]]> in content");
      addText(chunk);
      pos = end;
    }
    return root;
  };

  const root = element();
  misc();
  if (pos !== n) fail("content after the root element");
  return root;
}
