// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-FileCopyrightText: 2014 John MacFarlane
// SPDX-License-Identifier: MIT AND BSD-2-Clause
// thai-docx — markdown: the JavaScript port of scripts/thai_docx/markdown.py, itself
// a port of commonmark.js 0.31.2 (BSD-2-Clause; LICENSES/commonmark.js.txt). Kept
// line for line with the Python file; ADR 0015 is the character model both follow.

const ENTITIES = /*@@ENTITIES@@*/ null;

const FLAGS = ["b", "i", "strike", "code", "u", "sup", "sub"];
const ALLOWED_TAGS = ["br", "sup", "sub", "u", "kbd"];
const CODE_INDENT = 4;

// Deepest nesting of blocks, and of inline formatting within a block, that is read —
// as MAX_DEPTH in thai_docx/markdown.py.
const MAX_DEPTH = 100;

class Unsupported extends Error {
  constructor(line, what) {
    super("line " + line + ": " + what);
    this.line = line;
    this.what = what;
  }
}

// --- the character model (ADR 0015) ----------------------------------------------

const WS = " \t\n\x0b\x0c\r";
const RE_ZS = /^\p{Zs}$/u;
const RE_PS = /^[\p{P}\p{S}]$/u;
// ำ has a compatibility decomposition into these two, and no composition back (ADR 0034)
const NIKHAHIT = "\u0e4d", SARA_AA = "\u0e32", SARA_AM = "\u0e33";

function isSpaceOrTab(ch) {
  return ch === " " || ch === "\t";
}

function isUnicodeWhitespace(ch) {
  return ch === "" || "\t\n\x0c\r".indexOf(ch) !== -1 || RE_ZS.test(ch);
}

function isUnicodePunctuation(ch) {
  return ch !== "" && RE_PS.test(ch);
}

function stripWs(s) {
  return stripChars(s, WS);
}

function normalizeLabel(label) {
  return stripWs(label).replace(/[ \t\r\n]+/g, " ").toLowerCase().toUpperCase();
}

function hex4(cp) {
  return cp.toString(16).toUpperCase().padStart(4, "0");
}

function forbiddenChar(ch) {
  const cp = ch.codePointAt(0);
  if (Object.prototype.hasOwnProperty.call(INVISIBLE, ch)) return INVISIBLE[ch];
  if ((cp < 0x20 && ch !== "\t" && ch !== "\n") || (cp >= 0x7f && cp <= 0x9f)) return "U+" + hex4(cp) + ", a control character";
  if (cp === 0xfffe || cp === 0xffff) return "U+" + hex4(cp) + ", a noncharacter";
  return null;
}

// --- shared regular expressions (ASCII classes only) ------------------------------

const ESCAPABLE = "[!\"#$%&'()*+,./:;<=>?@\\[\\\\\\]^_`{|}~-]";
const ENTITY = "&(?:#[xX][A-Fa-f0-9]{1,6}|#[0-9]{1,7}|[A-Za-z][A-Za-z0-9]{1,31});";
const TAGNAME = "[A-Za-z][A-Za-z0-9-]*";
const ATTRNAME = "[A-Za-z_:][A-Za-z0-9:._-]*";
const S = "[ \\t\\n\\x0b\\x0c\\r]";
const ATTRVALUE = "(?:[^\"'=<>`\\x00-\\x20]+|'[^']*'|\"[^\"]*\")";
const OPENTAG = "<" + TAGNAME + "(?:" + S + "+" + ATTRNAME + "(?:" + S + "*=" + S + "*" + ATTRVALUE + ")?)*" + S + "*/?>";
const CLOSETAG = "</" + TAGNAME + S + "*>";
const HTMLCOMMENT = "<!-->|<!--->|<!--[\\s\\S]*?-->";
const PI = "<\\?[\\s\\S]*?\\?>";
const DECLARATION = "<![A-Za-z]+[^>]*>";
const CDATA = "<!\\[CDATA\\[[\\s\\S]*?\\]\\]>";

const reEscapableOne = new RegExp("^" + ESCAPABLE + "$");
const reEntityOrEscapedSrc = "\\\\" + ESCAPABLE + "|" + ENTITY;
const reEntityHere = sticky(ENTITY);
const reHtmlTag = sticky("(?:(" + OPENTAG + ")|(" + CLOSETAG + ")|(" + HTMLCOMMENT + ")|" + PI + "|" + DECLARATION + "|" + CDATA + ")");
const reTagName = new RegExp("^</?(" + TAGNAME + ")");
const reLinkTitle = sticky(
  "(?:\"(?:\\\\" + ESCAPABLE + "|\\\\[^\\\\]|[^\\\\\"\\x00])*\"" +
    "|'(?:\\\\" + ESCAPABLE + "|\\\\[^\\\\]|[^\\\\'\\x00])*'" +
    "|\\((?:\\\\" + ESCAPABLE + "|\\\\[^\\\\]|[^\\\\()\\x00])*\\))"
);
const reLinkDestinationBraces = sticky("<(?:[^<>\\n\\\\\\x00]|\\\\[^\\n])*>");
const reLinkLabel = sticky("\\[(?:[^\\\\\\[\\]]|\\\\[\\s\\S]){0,1000}\\]");
const reEmailAutolink = sticky(
  "<([a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)>"
);
const reAutolink = sticky("<[A-Za-z][A-Za-z0-9.+-]{1,31}:[^<>\\x00-\\x20]*>");
const reSpnl = sticky(" *(?:\\n *)?");
const reWhitespaceCharOne = /^[ \t\n\v\f\r]$/;
const reFinalSpace = / *$/;
const reInitialSpace = sticky(" *");
const reSpaceAtEndOfLine = sticky(" *(?:\\n|$)");
const reTicks = /`+/g;
const reTicksHere = sticky("`+");
const reMain = sticky("[^\\n`\\[\\]\\\\!<&*_~$]+");

const reHtmlBlockOpen = [
  null,
  new RegExp("^<(?:script|pre|textarea|style)(?:" + S + "|>|$)", "i"),
  /^<!--/,
  /^<[?]/,
  /^<![A-Za-z]/,
  /^<!\[CDATA\[/,
  new RegExp(
    "^<[/]?(?:address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|" +
      "dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[123456]|head|header|hr|html|" +
      "iframe|legend|li|link|main|menu|menuitem|nav|noframes|ol|optgroup|option|p|param|search|section|summary|" +
      "table|tbody|td|tfoot|th|thead|title|tr|track|ul)(?:" + S + "|[/]?[>]|$)",
    "i"
  ),
  new RegExp("^(?:" + OPENTAG + "|" + CLOSETAG + ")" + S + "*$", "i"),
];
const reHtmlBlockClose = [null, /<\/(?:script|pre|textarea|style)>/i, /-->/, /\?>/, />/, /\]\]>/];
const reThematicBreak = /^(?:\*[ \t]*){3,}$|^(?:_[ \t]*){3,}$|^(?:-[ \t]*){3,}$/;
const reMaybeSpecial = /^[#`~*+_=<>0-9$[|:-]/;
const reNonSpace = /[^ \t\f\v\r\n]/;
const reBulletListMarker = /^[*+-]/;
const reOrderedListMarker = /^([0-9]{1,9})([.)])/;
const reAtxHeadingMarker = /^#{1,6}(?:[ \t]+|$)/;
const reCodeFence = /^`{3,}(?![\s\S]*`)|^~{3,}/;
const reClosingCodeFence = /^(?:`{3,}|~{3,})(?=[ \t]*$)/;
const reMathFence = /^\$\$/;
const reClosingMathFence = /^\$\$[ \t]*$/;
const reSetextHeadingLine = /^(?:=+|-+)[ \t]*$/;
const reFootnoteDef = /^\[\^([^\] ]+)\]:/;
const reTask = /^\[([ xX])\][ \t]+/;
const reTableDelimCell = /^:?-+:?$/;

function decodeEntity(ref, line) {
  if (ref[1] === "#") {
    const cp = ref[2] === "x" || ref[2] === "X" ? parseInt(ref.slice(3, -1), 16) : parseInt(ref.slice(2, -1), 10);
    if (cp === 0 || (cp >= 0xd800 && cp <= 0xdfff) || cp > 0x10ffff) return "�";
    const ch = String.fromCodePoint(cp);
    const label = ch === "\n" ? "a line break" : forbiddenChar(ch);
    if (label !== null) throw new Unsupported(line, "character reference " + ref + " is " + label + "; the build refuses it (ADR 0015)");
    return ch;
  }
  const name = ref.slice(1, -1);
  return Object.prototype.hasOwnProperty.call(ENTITIES, name) ? ENTITIES[name] : ref;
}

function unescapeString(s, line) {
  if (s.indexOf("\\") === -1 && s.indexOf("&") === -1) return s;
  return s.replace(new RegExp(reEntityOrEscapedSrc, "g"), (m) => (m[0] === "\\" ? m[1] : decodeEntity(m, line || 0)));
}

// --- nodes ------------------------------------------------------------------------

class Node {
  constructor(type, line) {
    this.type = type;
    this.parent = this.firstChild = this.lastChild = this.prev = this.next = null;
    this.open = true;
    this.line = line || 0;
    this.stringContent = "";
    this.literal = null;
    this.info = null;
    this.level = 0;
    this.listData = null;
    this.fenceChar = null;
    this.fenceLength = 0;
    this.fenceOffset = 0;
    this.isFenced = false;
    this.htmlType = 0;
    this.destination = null;
    this.title = null;
    this.label = null;
    this.aligns = null;
    this.rows = null;
    this.task = null;
    this.math = false;
    this.taskOk = false;
    this.extended = false;
    this.tableFailed = false;
    this.lines = null;
  }

  appendChild(child) {
    child.unlink();
    child.parent = this;
    if (this.lastChild !== null) {
      this.lastChild.next = child;
      child.prev = this.lastChild;
      this.lastChild = child;
    } else {
      this.firstChild = this.lastChild = child;
    }
  }

  insertAfter(sibling) {
    sibling.unlink();
    sibling.next = this.next;
    if (sibling.next !== null) sibling.next.prev = sibling;
    sibling.prev = this;
    this.next = sibling;
    sibling.parent = this.parent;
    if (sibling.next === null) sibling.parent.lastChild = sibling;
  }

  unlink() {
    if (this.prev !== null) this.prev.next = this.next;
    else if (this.parent !== null) this.parent.firstChild = this.next;
    if (this.next !== null) this.next.prev = this.prev;
    else if (this.parent !== null) this.parent.lastChild = this.prev;
    this.parent = this.next = this.prev = null;
  }

  children() {
    const out = [];
    for (let c = this.firstChild; c !== null; c = c.next) out.push(c);
    return out;
  }
}

function textNode(s) {
  const n = new Node("text");
  n.literal = s;
  return n;
}

// --- blocks -----------------------------------------------------------------------

function peekCh(s, pos) {
  return pos < s.length ? s[pos] : "";
}

class BlockParser {
  constructor() {
    this.doc = new Node("document", 1);
    this.tip = this.doc;
    this.oldtip = this.doc;
    this.line = "";
    this.lineNumber = 0;
    this.offset = 0;
    this.column = 0;
    this.nextNonspace = 0;
    this.nextNonspaceColumn = 0;
    this.indent = 0;
    this.indented = false;
    this.blank = false;
    this.partiallyConsumedTab = false;
    this.allClosed = true;
    this.lastMatchedContainer = this.doc;
    this.refmap = new Map();
    this.refLines = new Map();  // label → [the line its definition is on, the label as written]
    this.refsUsed = new Set();  // labels some link or image actually referred to
    this.footnoteDefs = new Map();
    this.lastLineLength = 0;
    this.warnings = [];
  }

  findNextNonspace() {
    const line = this.line;
    let i = this.offset;
    let cols = this.column;
    while (i < line.length) {
      const c = line[i];
      if (c === " ") {
        i++;
        cols++;
      } else if (c === "\t") {
        i++;
        cols += 4 - (cols % 4);
      } else break;
    }
    this.blank = i >= line.length || line[i] === "\n" || line[i] === "\r";
    this.nextNonspace = i;
    this.nextNonspaceColumn = cols;
    this.indent = this.nextNonspaceColumn - this.column;
    this.indented = this.indent >= CODE_INDENT;
  }

  advanceNextNonspace() {
    this.offset = this.nextNonspace;
    this.column = this.nextNonspaceColumn;
    this.partiallyConsumedTab = false;
  }

  advanceOffset(count, columns) {
    const line = this.line;
    while (count > 0 && this.offset < line.length) {
      const c = line[this.offset];
      if (c === "\t") {
        const charsToTab = 4 - (this.column % 4);
        if (columns) {
          this.partiallyConsumedTab = charsToTab > count;
          const charsToAdvance = Math.min(charsToTab, count);
          this.column += charsToAdvance;
          if (!this.partiallyConsumedTab) this.offset += 1;
          count -= charsToAdvance;
        } else {
          this.partiallyConsumedTab = false;
          this.column += charsToTab;
          this.offset += 1;
          count -= 1;
        }
      } else {
        this.partiallyConsumedTab = false;
        this.offset += 1;
        this.column += 1;
        count -= 1;
      }
    }
  }

  addLine() {
    if (this.partiallyConsumedTab) {
      this.offset += 1;
      const charsToTab = 4 - (this.column % 4);
      this.tip.stringContent += " ".repeat(charsToTab);
    }
    const text = this.line.slice(this.offset);
    if (this.tip.type === "table") {
      if (!reNonSpace.test(text)) return;
      const cells = tableCells(text);
      const width = this.tip.aligns.length;
      if (cells.length > width) {
        throw new Unsupported(this.lineNumber, "table row has " + cells.length + " cells; the header has " + width + " — nothing may be dropped");
      }
      while (cells.length < width) cells.push("");
      this.tip.rows.push([this.lineNumber, cells]);
      return;
    }
    if (this.tip.type === "paragraph") this.tip.lines.push([this.lineNumber, text, this.indented]);
    this.tip.stringContent += text + "\n";
  }

  addChild(tag) {
    while (!canContain(this.tip.type, tag)) this.finalize(this.tip, this.lineNumber - 1);
    let depth = 1;
    for (let above = this.tip; above.parent !== null; above = above.parent) depth++;
    if (depth > MAX_DEPTH) throw new Unsupported(this.lineNumber, "blocks nested more than " + MAX_DEPTH + " deep are not supported");
    const child = new Node(tag, this.lineNumber);
    if (tag === "paragraph") child.lines = [];
    this.tip.appendChild(child);
    this.tip = child;
    return child;
  }

  closeUnmatchedBlocks() {
    if (!this.allClosed) {
      while (this.oldtip !== this.lastMatchedContainer) {
        const parent = this.oldtip.parent;
        this.finalize(this.oldtip, this.lineNumber - 1);
        this.oldtip = parent;
      }
      this.allClosed = true;
    }
  }

  // eslint-disable-next-line no-unused-vars -- the signature of commonmark.js and markdown.py, which callers keep
  finalize(block, lineNumber) {
    const above = block.parent;
    block.open = false;
    FINALIZE[block.type](this, block);
    this.tip = above;
  }

  incorporateLine(ln) {
    let container = this.doc;
    this.oldtip = this.tip;
    this.offset = 0;
    this.column = 0;
    this.blank = false;
    this.partiallyConsumedTab = false;
    this.lineNumber += 1;
    this.line = ln;

    for (;;) {
      const lastChild = container.lastChild;
      if (lastChild === null || !lastChild.open) break;
      container = lastChild;
      this.findNextNonspace();
      const res = CONTINUE[container.type](this, container);
      if (res === 0) continue;
      if (res === 1) {
        container = container.parent;
        break;
      }
      this.lastLineLength = ln.length;
      return;
    }

    this.allClosed = container === this.oldtip;
    this.lastMatchedContainer = container;

    let matchedLeaf = container.type !== "paragraph" && container.type !== "table" && ACCEPTS_LINES[container.type];
    while (!matchedLeaf) {
      this.findNextNonspace();
      if (!this.indented && !reMaybeSpecial.test(ln.slice(this.nextNonspace))) {
        this.advanceNextNonspace();
        break;
      }
      let started = false;
      for (const start of BLOCK_STARTS) {
        const res = start(this, container);
        if (res === 1) {
          container = this.tip;
          started = true;
          break;
        }
        if (res === 2) {
          container = this.tip;
          matchedLeaf = true;
          started = true;
          break;
        }
      }
      if (!started) {
        this.advanceNextNonspace();
        break;
      }
    }

    if (!this.allClosed && !this.blank && this.tip.type === "paragraph") {
      this.addLine();
    } else {
      this.closeUnmatchedBlocks();
      const t = container.type;
      if (ACCEPTS_LINES[t]) {
        this.addLine();
        if (t === "html_block" && container.htmlType >= 1 && container.htmlType <= 5 && reHtmlBlockClose[container.htmlType].test(ln.slice(this.offset))) {
          this.lastLineLength = ln.length;
          this.finalize(container, this.lineNumber);
        }
      } else if (this.offset < ln.length && !this.blank) {
        const para = this.addChild("paragraph");
        this.advanceNextNonspace();
        const item = para.parent;
        if (item.type === "item" && item.taskOk && item.line === this.lineNumber && para.prev === null) {
          const m = reTask.exec(ln.slice(this.offset));
          if (m) {
            para.task = m[1] !== " ";
            this.advanceOffset(m[0].length, false);
          }
        }
        this.addLine();
      }
    }
    this.lastLineLength = ln.length;
  }

  parse(text) {
    const lines = text.split("\n");
    if (text.endsWith("\n")) lines.pop();
    for (const ln of lines) this.incorporateLine(ln);
    while (this.tip !== null) this.finalize(this.tip, lines.length);
    return this.doc;
  }
}

function canContain(parent, child) {
  if (parent === "document" || parent === "block_quote" || parent === "footnote_def") {
    return child !== "item" && !(parent === "footnote_def" && child === "footnote_def");
  }
  if (parent === "item") return child !== "item";
  if (parent === "list") return child === "item";
  return false;
}

const ACCEPTS_LINES = {
  document: false, list: false, item: false, block_quote: false, footnote_def: false,
  heading: false, thematic_break: false, code_block: true, html_block: true, paragraph: true, table: true,
};

const CONTINUE = {
  document: () => 0,
  list: () => 0,
  block_quote(p) {
    const ln = p.line;
    if (!p.indented && peekCh(ln, p.nextNonspace) === ">") {
      p.advanceNextNonspace();
      p.advanceOffset(1, false);
      if (isSpaceOrTab(peekCh(ln, p.offset))) p.advanceOffset(1, true);
      return 0;
    }
    return 1;
  },
  item(p, c) {
    if (p.blank) {
      if (c.firstChild === null) return 1;
      p.advanceNextNonspace();
    } else if (p.indent >= c.listData.marker_offset + c.listData.padding) {
      p.advanceOffset(c.listData.marker_offset + c.listData.padding, true);
    } else {
      return 1;
    }
    return 0;
  },
  footnote_def(p) {
    if (p.blank) {
      p.advanceNextNonspace();
      return 0;
    }
    if (p.indent >= CODE_INDENT) {
      p.advanceOffset(CODE_INDENT, true);
      return 0;
    }
    return 1;
  },
  heading: () => 1,
  thematic_break: () => 1,
  code_block(p, c) {
    const ln = p.line;
    const indent = p.indent;
    if (c.isFenced) {
      let closing;
      let lengthOk;
      if (indent <= 3) {
        const rest = ln.slice(p.nextNonspace);
        if (c.math) {
          closing = reClosingMathFence.exec(rest);
          lengthOk = closing !== null;
        } else {
          closing = peekCh(ln, p.nextNonspace) === c.fenceChar ? reClosingCodeFence.exec(rest) : null;
          lengthOk = closing !== null && closing[0].length >= c.fenceLength;
        }
        if (closing !== null && lengthOk) {
          p.lastLineLength = p.offset + indent + closing[0].length;
          p.finalize(c, p.lineNumber);
          return 2;
        }
      }
      let i = c.fenceOffset;
      while (i > 0 && isSpaceOrTab(peekCh(ln, p.offset))) {
        p.advanceOffset(1, true);
        i--;
      }
    } else if (indent >= CODE_INDENT) {
      p.advanceOffset(CODE_INDENT, true);
    } else if (p.blank) {
      p.advanceNextNonspace();
    } else {
      return 1;
    }
    return 0;
  },
  html_block: (p, c) => (p.blank && (c.htmlType === 6 || c.htmlType === 7) ? 1 : 0),
  paragraph: (p) => (p.blank ? 1 : 0),
  table(p) {
    if (p.blank) return 1;
    const rest = p.line.slice(p.nextNonspace);
    return tableCells(rest).length === 0 ? 1 : 0;
  },
};

function finalizeDocument(p, doc) {
  const empty = [];
  const walk = (node) => {
    for (const child of node.children()) {
      if (child.type === "paragraph") {
        if (takeReferences(p, child)) empty.push(child);
      } else if (child.type !== "table") walk(child);
    }
  };
  walk(doc);
  for (const node of empty) node.unlink();
}

function takeReferences(p, b) {
  let content = b.stringContent;
  let hasDefs = false;
  while (peekCh(content, 0) === "[") {
    const pos = new InlineParser(p, b.line).parseReference(content, p.refmap);
    if (!pos) break;
    const consumed = content.slice(0, pos);
    content = content.slice(pos);
    hasDefs = true;
    const drop = consumed.split("\n").length - 1;
    b.lines = b.lines.slice(drop);
  }
  b.stringContent = content;
  return hasDefs && !reNonSpace.test(content);
}

function finalizeCodeBlock(p, b) {
  if (b.isFenced) {
    const content = b.stringContent;
    const nl = content.indexOf("\n");
    const firstLine = content.slice(0, nl);
    const rest = content.slice(nl + 1);
    if (b.math) {
      b.info = "math";
      b.literal = (stripWs(firstLine) ? stripWs(firstLine) + "\n" : "") + rest;
    } else {
      b.info = unescapeString(stripWs(firstLine), b.line);
      b.literal = rest;
    }
  } else {
    const lines = b.stringContent.split("\n");
    while (/^[ \t]*$/.test(lines[lines.length - 1])) lines.pop();
    b.literal = lines.join("\n") + "\n";
  }
  b.stringContent = "";
}

function finalizeHtmlBlock(p, b) {
  if (b.htmlType === 2) {
    if (!reHtmlBlockClose[2].test(b.stringContent)) throw new Unsupported(b.line, "HTML comment is never closed");
    const rest = b.stringContent.replace(new RegExp(HTMLCOMMENT, "g"), "");
    if (reNonSpace.test(rest)) throw new Unsupported(b.line, "an HTML comment block also holds text; put the text outside the comment");
    return;
  }
  throw new Unsupported(b.line, "HTML blocks are not supported; only <br>, <sup>, <sub>, <u>, <kbd> inside text, and comments");
}

const noop = () => {};
const FINALIZE = {
  document: finalizeDocument, list: noop, block_quote: noop, item: noop, footnote_def: noop, heading: noop,
  thematic_break: noop, code_block: finalizeCodeBlock, html_block: finalizeHtmlBlock, paragraph: noop, table: noop,
};

function startBlockQuote(p) {
  if (!p.indented && peekCh(p.line, p.nextNonspace) === ">") {
    p.advanceNextNonspace();
    p.advanceOffset(1, false);
    if (isSpaceOrTab(peekCh(p.line, p.offset))) p.advanceOffset(1, true);
    p.closeUnmatchedBlocks();
    p.addChild("block_quote");
    return 1;
  }
  return 0;
}

function startAtxHeading(p) {
  if (!p.indented) {
    const m = reAtxHeadingMarker.exec(p.line.slice(p.nextNonspace));
    if (m) {
      p.advanceNextNonspace();
      p.advanceOffset(m[0].length, false);
      p.closeUnmatchedBlocks();
      const h = p.addChild("heading");
      h.level = stripChars(m[0], " \t").length;
      let content = p.line.slice(p.offset);
      content = content.replace(/^[ \t]*#+[ \t]*$/, "");
      content = content.replace(/[ \t]+#+[ \t]*$/, "");
      h.stringContent = content;
      p.advanceOffset(p.line.length - p.offset, false);
      return 2;
    }
  }
  return 0;
}

function startFencedCode(p) {
  if (!p.indented) {
    const m = reCodeFence.exec(p.line.slice(p.nextNonspace));
    if (m) {
      const fenceLength = m[0].length;
      p.closeUnmatchedBlocks();
      const c = p.addChild("code_block");
      c.isFenced = true;
      c.fenceLength = fenceLength;
      c.fenceChar = m[0][0];
      c.fenceOffset = p.indent;
      p.advanceNextNonspace();
      p.advanceOffset(fenceLength, false);
      return 2;
    }
  }
  return 0;
}

function startMathFence(p) {
  if (!p.indented && reMathFence.test(p.line.slice(p.nextNonspace))) {
    const rest = p.line.slice(p.nextNonspace + 2);
    p.closeUnmatchedBlocks();
    const c = p.addChild("code_block");
    c.isFenced = true;
    c.math = true;
    c.fenceOffset = p.indent;
    p.warnings.push("line " + p.lineNumber + ": display math kept as literal LaTeX; typeset math is not supported in v0.1");
    p.advanceNextNonspace();
    p.advanceOffset(2, false);
    const stripped = rstripChars(rest, " \t");
    if (stripped.endsWith("$$") && stripWs(stripped).length > 2) {
      c.stringContent = stripWs(stripped.slice(0, -2)) + "\n";
      p.advanceOffset(p.line.length - p.offset, false);
      p.finalize(c, p.lineNumber);
      return 2;
    }
    return 2;
  }
  return 0;
}

function startHtmlBlock(p, container) {
  if (!p.indented && peekCh(p.line, p.nextNonspace) === "<") {
    const s = p.line.slice(p.nextNonspace);
    for (let blockType = 1; blockType <= 7; blockType++) {
      if (reHtmlBlockOpen[blockType].test(s) &&
          (blockType < 7 || (container.type !== "paragraph" && !(!p.allClosed && !p.blank && p.tip.type === "paragraph")))) {
        p.closeUnmatchedBlocks();
        const b = p.addChild("html_block");
        b.htmlType = blockType;
        return 2;
      }
    }
  }
  return 0;
}

function splitRow(line) {
  const result = [];
  let current = "";
  let last = 0;
  let escaped = false;
  for (let pos = 0; pos < line.length; pos++) {
    const ch = line[pos];
    if (ch === "|") {
      if (!escaped) {
        result.push(current + line.slice(last, pos));
        current = "";
        last = pos + 1;
      } else {
        current += line.slice(last, pos - 1);
        last = pos;
      }
    }
    escaped = ch === "\\";
  }
  result.push(current + line.slice(last));
  return result;
}

function tableDelimiter(row) {
  if (!row || "|-:".indexOf(row[0]) === -1) return null;
  if (row.length < 2 || "|-: \t".indexOf(row[1]) === -1) return null;
  if (row[0] === "-" && isSpaceOrTab(row[1])) return null;
  for (const ch of row) if ("|-: \t".indexOf(ch) === -1) return null;
  const cols = row.split("|");
  const aligns = [];
  for (let i = 0; i < cols.length; i++) {
    const t = stripWs(cols[i]);
    if (!t) {
      if (i === 0 || i === cols.length - 1) continue;
      return null;
    }
    if (!reTableDelimCell.test(t)) return null;
    if (t[t.length - 1] === ":") aligns.push(t[0] === ":" ? "center" : "right");
    else aligns.push(t[0] === ":" ? "left" : null);
  }
  return aligns;
}

function tableCells(row) {
  const cells = splitRow(stripWs(row));
  if (cells.length && cells[0] === "") cells.shift();
  if (cells.length && cells[cells.length - 1] === "") cells.pop();
  return cells;
}

function startTable(p, container) {
  if (p.indented || container.type !== "paragraph" || !container.lines.length || container.tableFailed) return 0;
  const aligns = tableDelimiter(p.line.slice(p.nextNonspace));
  if (aligns === null) return 0;
  const [headerNo, header, headerIndented] = container.lines[container.lines.length - 1];
  const cells = tableCells(header);
  if (headerIndented || !cells.length || cells.length !== aligns.length) {
    container.tableFailed = true;
    return 0;
  }
  p.closeUnmatchedBlocks();
  const para = container;
  const table = new Node("table", headerNo);
  table.aligns = aligns;
  table.rows = [[headerNo, cells]];
  const linesBefore = para.lines.slice(0, -1);
  para.insertAfter(table);
  if (!linesBefore.length && para.task !== null) {
    para.lines = [];
    para.stringContent = "";
    p.finalize(para, p.lineNumber - 1);
  } else if (linesBefore.length) {
    para.lines = linesBefore;
    para.stringContent = linesBefore.map((l) => l[1] + "\n").join("");
    p.finalize(para, p.lineNumber - 1);
  } else {
    para.unlink();
  }
  p.tip = table;
  p.advanceOffset(p.line.length - p.offset, false);
  return 2;
}

function startSetextHeading(p, container) {
  if (!p.indented && container.type === "paragraph") {
    const m = reSetextHeadingLine.exec(p.line.slice(p.nextNonspace));
    if (m) {
      p.closeUnmatchedBlocks();
      let content = container.stringContent;
      while (peekCh(content, 0) === "[") {
        const pos = new InlineParser(p, container.line).parseReference(content, p.refmap);
        if (!pos) break;
        container.lines = container.lines.slice(content.slice(0, pos).split("\n").length - 1);
        content = content.slice(pos);
      }
      if (reNonSpace.test(content)) {
        const heading = new Node("heading", container.line);
        heading.level = m[0][0] === "=" ? 1 : 2;
        heading.stringContent = content;
        heading.lines = container.lines;
        container.insertAfter(heading);
        if (container.task !== null) {
          container.stringContent = "";
          container.lines = [];
          container.open = false;
        } else {
          container.unlink();
        }
        p.tip = heading;
        p.advanceOffset(p.line.length - p.offset, false);
        return 2;
      }
      container.stringContent = content;
      return 0;
    }
  }
  return 0;
}

function startThematicBreak(p) {
  if (!p.indented && reThematicBreak.test(p.line.slice(p.nextNonspace))) {
    p.closeUnmatchedBlocks();
    p.addChild("thematic_break");
    p.advanceOffset(p.line.length - p.offset, false);
    return 2;
  }
  return 0;
}

function parseListMarker(p, container) {
  const rest = p.line.slice(p.nextNonspace);
  const data = { type: null, tight: true, bullet_char: null, start: null, delimiter: null, padding: null, marker_offset: p.indent };
  if (p.indent >= 4) return null;
  let m = reBulletListMarker.exec(rest);
  if (m) {
    data.type = "bullet";
    data.bullet_char = m[0][0];
  } else {
    m = reOrderedListMarker.exec(rest);
    if (m && (container.type !== "paragraph" || m[1] === "1")) {
      data.type = "ordered";
      data.start = parseInt(m[1], 10);
      data.delimiter = m[2];
    } else {
      return null;
    }
  }
  let nextc = peekCh(p.line, p.nextNonspace + m[0].length);
  if (!(nextc === "" || nextc === "\t" || nextc === " ")) return null;
  if (container.type === "paragraph" && !reNonSpace.test(p.line.slice(p.nextNonspace + m[0].length))) return null;
  p.advanceNextNonspace();
  p.advanceOffset(m[0].length, true);
  const spacesStartCol = p.column;
  const spacesStartOffset = p.offset;
  for (;;) {
    p.advanceOffset(1, true);
    nextc = peekCh(p.line, p.offset);
    if (!(p.column - spacesStartCol < 5 && isSpaceOrTab(nextc))) break;
  }
  const blankItem = peekCh(p.line, p.offset) === "";
  const spacesAfterMarker = p.column - spacesStartCol;
  if (spacesAfterMarker >= 5 || spacesAfterMarker < 1 || blankItem) {
    data.padding = m[0].length + 1;
    p.column = spacesStartCol;
    p.offset = spacesStartOffset;
    if (isSpaceOrTab(peekCh(p.line, p.offset))) p.advanceOffset(1, true);
  } else {
    data.padding = m[0].length + spacesAfterMarker;
  }
  return data;
}

function listsMatch(a, b) {
  return a.type === b.type && a.delimiter === b.delimiter && a.bullet_char === b.bullet_char;
}

function startListItem(p, container) {
  if (!p.indented || container.type === "list") {
    const firstOnLine = !stripChars(p.line.slice(0, p.nextNonspace), " \t");
    const data = parseListMarker(p, container);
    if (data !== null) {
      p.closeUnmatchedBlocks();
      if (p.tip.type !== "list" || !listsMatch(container.listData, data)) {
        const lst = p.addChild("list");
        lst.listData = data;
      }
      const item = p.addChild("item");
      item.listData = data;
      item.taskOk = firstOnLine;
      return 1;
    }
  }
  return 0;
}

function startIndentedCode(p) {
  if (p.indented && p.tip.type !== "paragraph" && !p.blank) {
    p.advanceOffset(CODE_INDENT, true);
    p.closeUnmatchedBlocks();
    p.addChild("code_block");
    return 2;
  }
  return 0;
}

function startFootnoteDef(p) {
  if (p.indented) return 0;
  const m = reFootnoteDef.exec(p.line.slice(p.nextNonspace));
  if (!m) return 0;
  p.advanceNextNonspace();
  p.advanceOffset(m[0].length, false);
  while (isSpaceOrTab(peekCh(p.line, p.offset))) p.advanceOffset(1, false);
  p.closeUnmatchedBlocks();
  const fn = p.addChild("footnote_def");
  fn.label = m[1];
  if (p.footnoteDefs.has(fn.label)) throw new Unsupported(p.lineNumber, "footnote [^" + fn.label + "] is defined twice");
  p.footnoteDefs.set(fn.label, fn);
  return 1;
}

const BLOCK_STARTS = [
  startBlockQuote, startAtxHeading, startFencedCode, startMathFence, startHtmlBlock, startFootnoteDef,
  startSetextHeading, startThematicBreak, startListItem, startIndentedCode, startTable,
];

// --- inlines ----------------------------------------------------------------------

const UNDEFINED = {};

class InlineParser {
  constructor(bp, line) {
    this.bp = bp;
    this.subject = "";
    this.pos = 0;
    this.delimiters = null;
    this.brackets = null;
    this.refmap = bp.refmap;
    this.baseLine = line;
    this.lineStarts = [0];
  }

  lineAt(pos) {
    let n = 0;
    for (let i = 0; i < this.lineStarts.length; i++) if (this.lineStarts[i] <= pos) n = i;
    return this.baseLine + n;
  }

  match(re) {
    re.lastIndex = this.pos;
    const m = re.exec(this.subject);
    if (m === null) return null;
    this.pos = re.lastIndex;
    return m[0];
  }

  search(re) {
    re.lastIndex = this.pos;
    const m = re.exec(this.subject);
    if (m === null) return null;
    this.pos = re.lastIndex;
    return m[0];
  }

  peek() {
    return this.pos < this.subject.length ? this.subject[this.pos] : "";
  }

  spnl() {
    this.match(reSpnl);
    return true;
  }

  parse(block) {
    this.subject = stripWs(block.stringContent);
    this.lineStarts = [0];
    for (let i = 0; i < this.subject.length; i++) if (this.subject[i] === "\n") this.lineStarts.push(i + 1);
    this.pos = 0;
    this.delimiters = null;
    this.brackets = null;
    while (this.parseInline(block));
    block.stringContent = "";
    this.processEmphasis(null);
  }

  parseInline(block) {
    const c = this.peek();
    if (c === "") return false;
    let res;
    if (c === "\n") res = this.parseNewline(block);
    else if (c === "\\") res = this.parseBackslash(block);
    else if (c === "`") res = this.parseBackticks(block);
    else if (c === "*" || c === "_" || c === "~") res = this.handleDelim(c, block);
    else if (c === "[") res = this.parseOpenBracket(block);
    else if (c === "!") res = this.parseBang(block);
    else if (c === "]") res = this.parseCloseBracket(block);
    else if (c === "<") res = this.parseAutolink(block) || this.parseHtmlTag(block);
    else if (c === "&") res = this.parseEntity(block);
    else if (c === "$") res = this.parseMath(block);
    else res = this.parseString(block);
    if (!res) {
      this.pos += 1;
      block.appendChild(textNode(c));
    }
    return true;
  }

  parseNewline(block) {
    this.pos += 1;
    const lastc = block.lastChild;
    if (lastc !== null && lastc.type === "text" && lastc.literal.endsWith(" ")) {
      const hardbreak = lastc.literal.length >= 2 && lastc.literal[lastc.literal.length - 2] === " ";
      lastc.literal = lastc.literal.replace(reFinalSpace, "");
      block.appendChild(new Node(hardbreak ? "linebreak" : "softbreak"));
    } else {
      block.appendChild(new Node("softbreak"));
    }
    this.match(reInitialSpace);
    return true;
  }

  parseBackslash(block) {
    const subj = this.subject;
    this.pos += 1;
    if (this.peek() === "\n") {
      this.pos += 1;
      block.appendChild(new Node("linebreak"));
    } else if (this.pos < subj.length && reEscapableOne.test(subj[this.pos])) {
      block.appendChild(textNode(subj[this.pos]));
      this.pos += 1;
    } else {
      block.appendChild(textNode("\\"));
    }
    return true;
  }

  parseBackticks(block) {
    const ticks = this.match(reTicksHere);
    if (ticks === null) return false;
    const afterOpenTicks = this.pos;
    for (;;) {
      const matched = this.search(reTicks);
      if (matched === null) break;
      if (matched === ticks) {
        const node = new Node("code");
        const contents = this.subject.slice(afterOpenTicks, this.pos - ticks.length).replace(/\n/g, " ");
        if (contents && /[^ ]/.test(contents) && contents[0] === " " && contents[contents.length - 1] === " ") {
          node.literal = contents.slice(1, -1);
        } else {
          node.literal = contents;
        }
        block.appendChild(node);
        return true;
      }
    }
    this.pos = afterOpenTicks;
    block.appendChild(textNode(ticks));
    return true;
  }

  scanDelims(cc) {
    let numdelims = 0;
    const startpos = this.pos;
    while (this.peek() === cc) {
      numdelims++;
      this.pos++;
    }
    if (numdelims === 0) return null;
    const charBefore = startpos === 0 ? "\n" : cpBefore(this.subject, startpos);
    const charAfter = cpAt(this.subject, this.pos) || "\n";
    const afterWs = isUnicodeWhitespace(charAfter);
    const afterPunct = isUnicodePunctuation(charAfter);
    const beforeWs = isUnicodeWhitespace(charBefore);
    const beforePunct = isUnicodePunctuation(charBefore);
    const left = !afterWs && (!afterPunct || beforeWs || beforePunct);
    const right = !beforeWs && (!beforePunct || afterWs || afterPunct);
    let canOpen, canClose;
    if (cc === "_") {
      canOpen = left && (!right || beforePunct);
      canClose = right && (!left || afterPunct);
    } else {
      canOpen = left;
      canClose = right;
    }
    if (cc === "~" && numdelims > 2) canOpen = canClose = false;
    this.pos = startpos;
    return [numdelims, canOpen, canClose];
  }

  handleDelim(cc, block) {
    const res = this.scanDelims(cc);
    if (res === null) return false;
    const [numdelims, canOpen, canClose] = res;
    const startpos = this.pos;
    this.pos += numdelims;
    const node = textNode(this.subject.slice(startpos, this.pos));
    block.appendChild(node);
    if (canOpen || canClose) {
      const d = { cc, numdelims, origdelims: numdelims, node, previous: this.delimiters, next: null, canOpen, canClose };
      if (d.previous !== null) d.previous.next = d;
      this.delimiters = d;
    }
    return true;
  }

  removeDelimiter(delim) {
    if (delim.previous !== null) delim.previous.next = delim.next;
    if (delim.next === null) this.delimiters = delim.previous;
    else delim.next.previous = delim.previous;
  }

  removeDelimitersBetween(bottom, top) {
    if (bottom.next !== top) {
      bottom.next = top;
      top.previous = bottom;
    }
  }

  processEmphasis(stackBottom) {
    const openersBottom = new Array(15).fill(stackBottom);
    let closer = this.delimiters;
    while (closer !== null && closer.previous !== stackBottom) closer = closer.previous;
    while (closer !== null) {
      const closercc = closer.cc;
      if (!closer.canClose) {
        closer = closer.next;
        continue;
      }
      let opener = closer.previous;
      let openerFound = false;
      let idx;
      if (closercc === "_") idx = 2 + (closer.canOpen ? 3 : 0) + (closer.origdelims % 3);
      else if (closercc === "*") idx = 8 + (closer.canOpen ? 3 : 0) + (closer.origdelims % 3);
      else idx = 14;
      while (opener !== null && opener !== stackBottom && opener !== openersBottom[idx]) {
        if (closercc === "~") {
          if (opener.cc === "~" && opener.canOpen && opener.numdelims === closer.numdelims) {
            openerFound = true;
            break;
          }
        } else {
          const oddMatch = (closer.canOpen || opener.canClose) && closer.origdelims % 3 !== 0 && (opener.origdelims + closer.origdelims) % 3 === 0;
          if (opener.cc === closer.cc && opener.canOpen && !oddMatch) {
            openerFound = true;
            break;
          }
        }
        opener = opener.previous;
      }
      const oldCloser = closer;
      if (!openerFound) {
        closer = closer.next;
      } else {
        const useDelims = closercc === "~" ? closer.numdelims : closer.numdelims >= 2 && opener.numdelims >= 2 ? 2 : 1;
        const openerInl = opener.node;
        const closerInl = closer.node;
        opener.numdelims -= useDelims;
        closer.numdelims -= useDelims;
        openerInl.literal = openerInl.literal.slice(0, openerInl.literal.length - useDelims);
        closerInl.literal = closerInl.literal.slice(0, closerInl.literal.length - useDelims);
        const emph = new Node(closercc === "~" ? "strikethrough" : useDelims === 1 ? "emph" : "strong");
        let tmp = openerInl.next;
        while (tmp !== null && tmp !== closerInl) {
          const nxt = tmp.next;
          tmp.unlink();
          emph.appendChild(tmp);
          tmp = nxt;
        }
        openerInl.insertAfter(emph);
        this.removeDelimitersBetween(opener, closer);
        if (opener.numdelims === 0) {
          openerInl.unlink();
          this.removeDelimiter(opener);
        }
        if (closer.numdelims === 0) {
          closerInl.unlink();
          const tempstack = closer.next;
          this.removeDelimiter(closer);
          closer = tempstack;
        }
      }
      if (!openerFound) {
        openersBottom[idx] = oldCloser.previous;
        if (!oldCloser.canOpen) this.removeDelimiter(oldCloser);
      }
    }
    while (this.delimiters !== null && this.delimiters !== stackBottom) this.removeDelimiter(this.delimiters);
  }

  addBracket(node, index, image) {
    if (this.brackets !== null) this.brackets.bracketAfter = true;
    this.brackets = { node, previous: this.brackets, previousDelimiter: this.delimiters, index, image, active: true, bracketAfter: false };
  }

  removeBracket() {
    this.brackets = this.brackets.previous;
  }

  parseOpenBracket(block) {
    const startpos = this.pos;
    this.pos += 1;
    const node = textNode("[");
    block.appendChild(node);
    this.addBracket(node, startpos, false);
    return true;
  }

  parseBang(block) {
    const startpos = this.pos;
    this.pos += 1;
    if (this.peek() === "[") {
      this.pos += 1;
      const node = textNode("![");
      block.appendChild(node);
      this.addBracket(node, startpos + 1, true);
    } else {
      block.appendChild(textNode("!"));
    }
    return true;
  }

  parseLinkLabel() {
    const m = this.match(reLinkLabel);
    if (m === null || m.length > 1001) return 0;
    return m.length;
  }

  parseLinkDestination() {
    const res = this.match(reLinkDestinationBraces);
    if (res === null) {
      if (this.peek() === "<") return null;
      const savepos = this.pos;
      let openparens = 0;
      let c;
      for (;;) {
        c = this.peek();
        if (c === "") break;
        if (c === "\\" && reEscapableOne.test(peekCh(this.subject, this.pos + 1))) {
          this.pos += 1;
          if (this.peek() !== "") this.pos += 1;
        } else if (c === "(") {
          this.pos += 1;
          openparens += 1;
        } else if (c === ")") {
          if (openparens < 1) break;
          this.pos += 1;
          openparens -= 1;
        } else if (reWhitespaceCharOne.test(c)) {
          break;
        } else {
          this.pos += 1;
        }
      }
      if (this.pos === savepos && c !== ")") return null;
      if (openparens !== 0) return null;
      return unescapeString(this.subject.slice(savepos, this.pos), this.lineAt(savepos));
    }
    return unescapeString(res.slice(1, -1), this.lineAt(this.pos));
  }

  parseLinkTitle() {
    const title = this.match(reLinkTitle);
    if (title === null) return null;
    return unescapeString(title.slice(1, -1), this.lineAt(this.pos));
  }

  parseCloseBracket(block) {
    let matched = false;
    let dest = null;
    let title = null;
    this.pos += 1;
    const startpos = this.pos;
    let opener = this.brackets;
    if (opener === null) {
      block.appendChild(textNode("]"));
      return true;
    }
    if (!opener.active) {
      block.appendChild(textNode("]"));
      this.removeBracket();
      return true;
    }
    let isImage = opener.image;
    if (isImage && this.subject.slice(opener.index + 1, opener.index + 2) === "^") {
      isImage = false;
      opener.node.literal = "!";
      const bang = opener.node;
      opener.node = textNode("[");
      bang.insertAfter(opener.node);
      opener.image = false;
    }
    const savepos = this.pos;
    if (this.peek() === "(") {
      this.pos += 1;
      this.spnl();
      dest = this.parseLinkDestination();
      if (dest !== null) {
        this.spnl();
        if (reWhitespaceCharOne.test(peekCh(this.subject, this.pos - 1))) title = this.parseLinkTitle();
        this.spnl();
        if (this.peek() === ")") {
          this.pos += 1;
          matched = true;
        }
      }
      if (!matched) this.pos = savepos;
    }
    if (!matched) {
      const beforelabel = this.pos;
      const n = this.parseLinkLabel();
      let reflabel = null;
      if (n > 2) reflabel = this.subject.slice(beforelabel, beforelabel + n);
      else if (!opener.bracketAfter) reflabel = this.subject.slice(opener.index, startpos);
      if (n === 0) this.pos = savepos;
      if (reflabel) {
        const label = normalizeLabel(reflabel.slice(1, -1));
        const link = this.refmap.get(label);
        if (link !== undefined) {
          this.bp.refsUsed.add(label);
          [dest, title] = link;
          matched = true;
        }
      }
    }
    if (matched) {
      const node = new Node(isImage ? "image" : "link");
      node.destination = dest;
      node.title = title || "";
      let tmp = opener.node.next;
      while (tmp !== null) {
        const nxt = tmp.next;
        tmp.unlink();
        node.appendChild(tmp);
        tmp = nxt;
      }
      block.appendChild(node);
      this.processEmphasis(opener.previousDelimiter);
      this.removeBracket();
      opener.node.unlink();
      if (!isImage) {
        let o = this.brackets;
        while (o !== null) {
          if (!o.image) o.active = false;
          o = o.previous;
        }
      }
      return true;
    }
    const inner = this.subject.slice(opener.index + 1, startpos - 1);
    if (inner.startsWith("^") && inner.length > 1 && !/[ \t\n]/.test(inner) && this.bp.footnoteDefs.has(inner.slice(1))) {
      const node = new Node("footnote_ref");
      node.label = inner.slice(1);
      let tmp = opener.node.next;
      while (tmp !== null) {
        const nxt = tmp.next;
        tmp.unlink();
        tmp = nxt;
      }
      block.appendChild(node);
      this.processEmphasis(opener.previousDelimiter);
      this.removeBracket();
      if (isImage) opener.node.literal = "!";
      else opener.node.unlink();
      this.pos = startpos;
      return true;
    }
    this.removeBracket();
    this.pos = startpos;
    block.appendChild(textNode("]"));
    return true;
  }

  parseAutolink(block) {
    let m = this.match(reEmailAutolink);
    if (m !== null) {
      const dest = m.slice(1, -1);
      const node = new Node("link");
      node.destination = "mailto:" + dest;
      node.title = "";
      node.appendChild(textNode(dest));
      block.appendChild(node);
      return true;
    }
    m = this.match(reAutolink);
    if (m !== null) {
      const dest = m.slice(1, -1);
      const node = new Node("link");
      node.destination = dest;
      node.title = "";
      node.appendChild(textNode(dest));
      block.appendChild(node);
      return true;
    }
    return false;
  }

  parseHtmlTag(block) {
    const start = this.pos;
    reHtmlTag.lastIndex = this.pos;
    const m = reHtmlTag.exec(this.subject);
    if (m === null) return false;
    this.pos = reHtmlTag.lastIndex;
    const raw = m[0];
    const line = this.lineAt(start);
    if (m[3] !== undefined) {
      block.appendChild(new Node("html_comment"));
      return true;
    }
    if (m[1] !== undefined || m[2] !== undefined) {
      const name = reTagName.exec(raw)[1].toLowerCase();
      if (name === "br" && m[2] !== undefined) {
        block.appendChild(new Node("linebreak"));
        return true;
      }
      if (ALLOWED_TAGS.includes(name)) {
        if (name === "br") {
          block.appendChild(new Node("linebreak"));
          return true;
        }
        const node = new Node("html_tag");
        node.label = name;
        node.literal = m[2] !== undefined ? "close" : "open";
        block.appendChild(node);
        return true;
      }
      throw new Unsupported(line, "HTML <" + name + "> is not supported; only <br>, <sup>, <sub>, <u>, <kbd> and comments are");
    }
    throw new Unsupported(line, "HTML declarations, processing instructions and CDATA are not supported");
  }

  parseEntity(block) {
    const m = this.match(reEntityHere);
    if (m === null) return false;
    block.appendChild(textNode(decodeEntity(m, this.lineAt(this.pos))));
    return true;
  }

  parseMath(block) {
    const subj = this.subject;
    const i = this.pos;
    const n = subj.length;
    const width = subj.startsWith("$$", i) ? 2 : 1;
    let end;
    if (width === 2) {
      end = subj.indexOf("$$", i + 2);
    } else {
      end = -1;
      if (i + 1 < n && !isUnicodeWhitespace(cpAt(subj, i + 1))) {
        let j = subj.indexOf("$", i + 1);
        while (j !== -1 && (isUnicodeWhitespace(cpBefore(subj, j)) || (j + 1 < n && subj[j + 1] >= "0" && subj[j + 1] <= "9"))) {
          j = subj.indexOf("$", j + 1);
        }
        end = j;
      }
    }
    if (end === -1 || end <= i + width - 1 || end === i + width) return false;
    const node = new Node("code");
    node.literal = subj.slice(i + width, end).replace(/\n/g, " ");
    node.math = true;
    block.appendChild(node);
    this.bp.warnings.push("line " + this.lineAt(i) + ": inline math kept as literal LaTeX; typeset math is not supported in v0.1");
    this.pos = end + width;
    return true;
  }

  parseString(block) {
    const m = this.match(reMain);
    if (m === null) return false;
    block.appendChild(textNode(m));
    return true;
  }

  parseReference(s, refmap) {
    this.subject = s;
    this.pos = 0;
    const startpos = this.pos;
    const matchChars = this.parseLinkLabel();
    if (matchChars === 0) return 0;
    const rawlabel = this.subject.slice(0, matchChars);
    if (this.peek() === ":") {
      this.pos += 1;
    } else {
      this.pos = startpos;
      return 0;
    }
    this.spnl();
    const dest = this.parseLinkDestination();
    if (dest === null) {
      this.pos = startpos;
      return 0;
    }
    const beforetitle = this.pos;
    this.spnl();
    let title = UNDEFINED;
    if (this.pos !== beforetitle) title = this.parseLinkTitle();
    if (title === null) this.pos = beforetitle;
    let atLineEnd = true;
    if (this.match(reSpaceAtEndOfLine) === null) {
      if (title === null) {
        atLineEnd = false;
      } else {
        title = null;
        this.pos = beforetitle;
        atLineEnd = this.match(reSpaceAtEndOfLine) !== null;
      }
    }
    if (!atLineEnd) {
      this.pos = startpos;
      return 0;
    }
    const normlabel = normalizeLabel(rawlabel.slice(1, -1));
    if (normlabel === "") {
      this.pos = startpos;
      return 0;
    }
    if (!refmap.has(normlabel)) {
      refmap.set(normlabel, [dest, title === null || title === UNDEFINED ? "" : title]);
      this.bp.refLines.set(normlabel, [this.lineAt(startpos), rawlabel.slice(1, -1)]);
    }
    return this.pos - startpos;
  }
}

// --- extended autolinks (GFM 6.9) ---------------------------------------------------

const reWww = sticky("www\\.");
const reUrlScheme = sticky("https?://");
const reDomain = sticky("[A-Za-z0-9_-]+(?:\\.[A-Za-z0-9_-]+)*");
const reEntityTail = /&[A-Za-z0-9]+;$/;

function countChar(s, ch, start, end) {
  let n = 0;
  for (let i = start; i < end; i++) if (s[i] === ch) n++;
  return n;
}

function autolinkEnd(s, start) {
  let m = matchAt(reUrlScheme, s, start);
  if (m === null) m = matchAt(reWww, s, start);
  if (m === null) return -1;
  const dstart = m[0].startsWith("http") ? start + m[0].length : start;
  const d = matchAt(reDomain, s, dstart);
  if (d === null) return -1;
  const dEnd = dstart + d[0].length;
  const labels = d[0].split(".");
  if (labels.length < 2 || labels[labels.length - 1].indexOf("_") !== -1 || labels[labels.length - 2].indexOf("_") !== -1) return -1;
  let end = dEnd;
  while (end < s.length && !isUnicodeWhitespace(cpAt(s, end)) && s[end] !== "<") end++;
  while (end > dEnd) {
    const last = s[end - 1];
    if ("?!.,:*_~'\"".indexOf(last) !== -1) end -= 1;
    else if (last === ")" && countChar(s, ")", start, end) > countChar(s, "(", start, end)) end -= 1;
    else if (last === ";" && reEntityTail.test(s.slice(start, end))) end = start + reEntityTail.exec(s.slice(start, end)).index;
    else break;
  }
  return end;
}

const reEmailLocalOne = /^[A-Za-z0-9._+-]$/;
const reEmailDomain = sticky("[A-Za-z0-9_-]+(?:\\.[A-Za-z0-9_-]+)*");

function splitEmails(s) {
  const pieces = [];
  let last = 0;
  let i = 0;
  while (i < s.length) {
    if (s[i] === "@") {
      let start = i;
      while (start > last && reEmailLocalOne.test(s[start - 1])) start -= 1;
      const d = matchAt(reEmailDomain, s, i + 1);
      if (start < i && d !== null) {
        const end = i + 1 + d[0].length;
        if (s.slice(i + 1, end).indexOf(".") !== -1 && "-_".indexOf(s[end - 1]) === -1) {
          if (start > last) pieces.push([s.slice(last, start), null]);
          pieces.push([s.slice(start, end), "mailto:" + s.slice(start, end)]);
          last = i = end;
          continue;
        }
      }
    }
    i += 1;
  }
  if (last < s.length) pieces.push([s.slice(last), null]);
  return pieces;
}

function splitUrls(s) {
  const pieces = [];
  let last = 0;
  let i = 0;
  while (i < s.length) {
    const before = i ? cpBefore(s, i) : "";
    const wwwOk = s.startsWith("www.", i) && (i === 0 || isUnicodeWhitespace(before) || "*_~(".indexOf(before) !== -1);
    const urlOk = s[i] === "h" && (i === 0 || !/^[A-Za-z0-9]$/.test(before));
    if (wwwOk || urlOk) {
      const end = autolinkEnd(s, i);
      if (end > i) {
        if (i > last) pieces.push([s.slice(last, i), null]);
        const url = s.slice(i, end);
        pieces.push([url, url.startsWith("http") ? url : "http://" + url]);
        i = last = end;
        continue;
      }
    }
    i += 1;
  }
  if (last < s.length) pieces.push([s.slice(last), null]);
  return pieces;
}

function splitAutolinks(s) {
  const pieces = [];
  for (const [text, url] of splitUrls(s)) {
    if (url === null) pieces.push(...splitEmails(text));
    else pieces.push([text, url]);
  }
  return pieces;
}

function linkExtended(parent) {
  let node = parent.firstChild;
  while (node !== null) {
    if (node.type === "text") {
      while (node.next !== null && node.next.type === "text") {
        node.literal += node.next.literal;
        node.next.unlink();
      }
    }
    node = node.next;
  }
  node = parent.firstChild;
  while (node !== null) {
    const nxt = node.next;
    if (node.type === "text") {
      const pieces = splitAutolinks(node.literal);
      if (pieces.some(([, url]) => url !== null)) {
        let anchor = node;
        for (const [text, url] of pieces) {
          let fresh;
          if (url === null) fresh = textNode(text);
          else {
            fresh = new Node("link");
            fresh.destination = url;
            fresh.title = "";
            fresh.extended = true;
            fresh.appendChild(textNode(text));
          }
          anchor.insertAfter(fresh);
          anchor = fresh;
        }
        node.unlink();
      }
    } else if (node.type === "emph" || node.type === "strong" || node.type === "strikethrough") {
      linkExtended(node);
    }
    node = nxt;
  }
}

// --- to the writer's tree -------------------------------------------------------------

class MdDocument {
  constructor() {
    this.blocks = [];
    this.footnotes = new Map();
    this.footnoteOrder = [];
    this.frontMatter = new Map();
    this.frontMatterLines = new Map(); // key -> the line it was last given on
    this.warnings = [];
    this.pending = new Map();
  }
}

function parseMarkdown(text) {
  const doc = new MdDocument();
  text = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  if (text.startsWith("﻿")) text = text.slice(1);
  text = text.normalize("NFC");
  const rawLines = text.split("\n");
  const longSaraAm = [];
  for (let no = 1; no <= rawLines.length; no++) {
    for (const ch of rawLines[no - 1]) {
      const label = forbiddenChar(ch);
      if (label !== null) throw new Unsupported(no, "text contains " + label + "; the build refuses it (ADR 0005, 0015)");
    }
    // ำ written the long way. No normalisation joins these: NFC leaves them apart and NFKC
    // takes ำ the other way, into these two. So it is named and left alone (ADR 0034).
    if (rawLines[no - 1].includes(NIKHAHIT + SARA_AA)) longSaraAm.push(no);
  }
  const lines = text.split("\n");
  const offset = frontMatter(lines, doc);
  const body = [...new Array(offset).fill(""), ...lines.slice(offset)].join("\n");
  const bp = new BlockParser();
  const root = bp.parse(body);
  resolveInlines(bp, root);
  doc.blocks = toBlocks(bp, root, doc);
  for (const [label, fn] of bp.footnoteDefs) {
    if (!doc.footnotes.has(label)) {
      throw new Unsupported(fn.line, "footnote [^" + fn.label + "] is defined but never referenced; nothing may be dropped silently (ADR 0005)");
    }
  }
  // a link definition nobody refers to is dropped by CommonMark itself. This project promises
  // that nothing goes silently (references/markdown.md), so it is named — a warning, not a
  // refusal, because unlike a footnote it takes no room in the document either way.
  for (const [label, [line, written]] of bp.refLines) {
    if (!bp.refsUsed.has(label)) {
      bp.warnings.push("line " + line + ": the link definition [" + written
        + "] is never used; it is not written into the document");
    }
  }
  for (const no of longSaraAm) {
    bp.warnings.push("line " + no + ": " + NIKHAHIT + " followed by " + SARA_AA + " looks like "
      + SARA_AM + " but is two characters; it is written as it stands and a search for "
      + SARA_AM + " will not find it");
  }
  doc.warnings = bp.warnings
    .map((m, k) => [parseInt(m.split(":")[0].split(" ")[1], 10), k, m])
    .sort((a, b) => a[0] - b[0] || a[1] - b[1])
    .map((x) => x[2]);
  return doc;
}

const reFrontMatterLine = /^([A-Za-z_][A-Za-z0-9_-]*):(?:[ \t]+([^\n]*))?$/;

function frontMatter(lines, doc) {
  if (!lines.length || lines[0] !== "---") return 0;
  const found = new Map();
  const at = new Map();
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    if ((line === "---" || line === "...") && found.size) {
      for (const [k, v] of found) doc.frontMatter.set(k, v);
      for (const [k, n] of at) doc.frontMatterLines.set(k, n);
      return i + 1;
    }
    if (!stripChars(line, " \t")) continue;
    const m = reFrontMatterLine.exec(line);
    if (m === null) return 0;
    let v = stripWs(m[2] === undefined ? "" : m[2]);
    if (v.length >= 2 && v[0] === v[v.length - 1] && (v[0] === '"' || v[0] === "'")) v = v.slice(1, -1);
    found.set(m[1], v);
    at.set(m[1], i + 1);
  }
  return 0;
}

// Refuse inline formatting nested past MAX_DEPTH, before any walk recurses into it.
function inlineDepthWithin(block, line) {
  const stack = [...block.children()].map((n) => [n, 1]);
  while (stack.length) {
    const [node, depth] = stack.pop();
    if (depth > MAX_DEPTH) throw new Unsupported(line, "inline formatting nested more than " + MAX_DEPTH + " deep is not supported");
    for (const n of node.children()) stack.push([n, depth + 1]);
  }
}

function resolveInlines(bp, node) {
  for (const child of node.children()) {
    if (child.type === "paragraph" || child.type === "heading") {
      new InlineParser(bp, child.line).parse(child);
      inlineDepthWithin(child, child.line);
      linkExtended(child);
    } else if (child.type === "table") {
      const parsed = [];
      for (const [no, cells] of child.rows) {
        const row = [];
        for (const cell of cells) {
          const holder = new Node("paragraph", no);
          holder.stringContent = cell;
          new InlineParser(bp, no).parse(holder);
          inlineDepthWithin(holder, no);
          linkExtended(holder);
          row.push(holder);
        }
        parsed.push(row);
      }
      child.rows = parsed;
    } else if (child.firstChild !== null) {
      resolveInlines(bp, child);
    }
  }
}

function toInlines(bp, block, doc) {
  const out = [];
  const tags = { sup: 0, sub: 0, u: 0, kbd: 0 };
  const walk = (node, flags, link, extended) => {
    for (const n of node.children()) {
      const t = n.type;
      if (t === "text" || t === "code") {
        const f = { ...flags };
        if (t === "code") f.code = true;
        out.push(["text", n.literal, f, link, { ...tags }, extended]);
      } else if (t === "softbreak") {
        out.push(["soft", " ", { ...flags }, link, { ...tags }, extended]);
      } else if (t === "linebreak") {
        out.push(["hard"]);
      } else if (t === "emph" || t === "strong" || t === "strikethrough") {
        const key = t === "emph" ? "i" : t === "strong" ? "b" : "strike";
        walk(n, { ...flags, [key]: true }, link, false);
      } else if (t === "link") {
        walk(n, flags, n.destination, n.extended);
      } else if (t === "image") {
        out.push(["image", n.destination, plainOf(n)]);
      } else if (t === "footnote_ref") {
        if (!doc.footnotes.has(n.label)) {
          doc.footnoteOrder.push(n.label);
          doc.footnotes.set(n.label, []);
        }
        out.push(["fn", n.label, doc.footnoteOrder.indexOf(n.label) + 1]);
      } else if (t === "html_tag") {
        const delta = n.literal === "open" ? 1 : -1;
        tags[n.label] = Math.max(0, tags[n.label] + delta);
      }
    }
  };
  walk(block, {}, null, false);
  const result = block.task !== null ? [{ t: "task", checked: block.task }] : [];
  for (let i = 0; i < out.length; i++) {
    const item = out[i];
    const kind = item[0];
    if (kind === "text" || kind === "soft") {
      let s = item[1];
      if (kind === "soft") {
        const prev = neighbour(out, i, -1);
        const nxt = neighbour(out, i, 1);
        if (nxt === null || prev === null) s = "";
        else if (prev && nxt && isThai(prev) && isThai(nxt)) s = "";
        else s = " ";
      }
      const flags = item[2];
      const link = item[3];
      const tagsNow = item[4];
      result.push({
        t: "text", s, b: !!flags.b, i: !!flags.i, strike: !!flags.strike, code: !!(flags.code || tagsNow.kbd),
        u: !!tagsNow.u, sup: !!tagsNow.sup, sub: !!tagsNow.sub && !tagsNow.sup, link, autolink: !!(item[5] && link),
      });
    } else if (kind === "hard") {
      result.push({ t: "hardbreak" });
    } else if (kind === "image") {
      result.push({ t: "image", src: item[1], alt: item[2] });
    } else if (kind === "fn") {
      result.push({ t: "footnote_ref", label: item[1], id: item[2] });
    }
  }
  return mergeInlines(result);
}

function neighbour(out, i, step) {
  let j = i + step;
  while (j >= 0 && j < out.length && out[j][0] === "text" && !out[j][1]) j += step;
  if (!(j >= 0 && j < out.length)) return null;
  if (out[j][0] === "text") return step < 0 ? cpBefore(out[j][1], out[j][1].length) : cpAt(out[j][1], 0);
  return "";
}

function mergeInlines(nodes) {
  const out = [];
  for (const node of nodes) {
    if (node.t === "text" && !node.s) continue;
    const prev = out.length ? out[out.length - 1] : null;
    if (node.t === "text" && prev !== null && prev.t === "text" && FLAGS.every((f) => prev[f] === node[f]) && prev.link === node.link && prev.autolink === node.autolink) {
      prev.s += node.s;
    } else {
      out.push({ ...node });
    }
  }
  return out;
}

function plainOf(node) {
  const parts = [];
  for (const n of node.children()) {
    if (n.type === "text" || n.type === "code") parts.push(n.literal);
    else if (n.type === "softbreak" || n.type === "linebreak") parts.push(" ");
    else if (n.firstChild !== null) parts.push(plainOf(n));
  }
  return parts.join("");
}

const DIRECTIVES = ["front", "chapters", "back", "appendices", "toc", "list-of-tables", "list-of-figures"];
const RE_DIRECTIVE = /^<!--[ \t]*([a-z-]+)[ \t]*-->$/;

const RE_NEAR_DIRECTIVE = /^<!--[ \t]*([A-Za-z][A-Za-z _-]{0,30}?)[ \t]*-->$/;
const DIRECTIVE_ALIASES = new Map([["chapter", "chapters"], ["appendix", "appendices"], ["list-of-table", "list-of-tables"],
  ["list-of-figure", "list-of-figures"], ["table-of-contents", "toc"], ["contents", "toc"]]);

function editDistance(a, b) {
  const row = Array.from({ length: b.length + 1 }, (_, k) => k);
  for (let i = 1; i <= a.length; i++) {
    let prev = row[0];
    row[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const old = row[j];
      row[j] = Math.min(row[j] + 1, row[j - 1] + 1, prev + (a[i - 1] === b[j - 1] ? 0 : 1));
      prev = old;
    }
  }
  return row[b.length];
}

// The directive a comment of a word or two looks meant as: the same but for case or
// spacing, a known slip (chapter, appendix), or one or two letters off a long name.
function meantDirective(body) {
  const m = RE_NEAR_DIRECTIVE.exec(body);
  if (m === null) return null;
  const word = m[1].toLowerCase().replace(/[ _]+/g, "-");
  if (DIRECTIVES.includes(word)) return word;
  if (DIRECTIVE_ALIASES.has(word)) return DIRECTIVE_ALIASES.get(word);
  for (const name of DIRECTIVES) if (editDistance(word, name) <= (name.length >= 6 ? 2 : 1)) return name;
  return null;
}

function toBlocks(bp, node, doc) {
  const out = [];
  for (const child of node.children()) {
    const t = child.type;
    if (t === "heading") {
      out.push({ t: "heading", level: child.level, inlines: toInlines(bp, child, doc), line: child.line });
    } else if (t === "paragraph") {
      out.push({ t: "paragraph", inlines: toInlines(bp, child, doc), line: child.line });
    } else if (t === "html_block") {
      // a comment alone at the top level may be a directive (ADR 0021); any other renders
      // nothing — with a warning when it looks meant as one, so none is lost silently
      const body = stripChars(child.stringContent, " \t\n");
      const d = RE_DIRECTIVE.exec(body);
      if (node.type === "document" && d && DIRECTIVES.includes(d[1])) {
        out.push({ t: "directive", name: d[1], line: child.line });
      } else {
        const meant = meantDirective(body);
        if (meant && d && d[1] === meant) {
          bp.warnings.push("line " + child.line + ": <!-- " + meant + " --> works only at the top level, not inside a list, quotation or footnote; read as a comment");
        } else if (meant) {
          bp.warnings.push("line " + child.line + ": " + body + " is read as a comment; the comment that works is <!-- " + meant + " -->");
        }
      }
    } else if (t === "code_block") {
      const lines = (child.literal || "").split("\n");
      if (lines.length && lines[lines.length - 1] === "") lines.pop();
      out.push({ t: "code", lines, info: child.info || (child.math ? "math" : ""), math: child.math });
    } else if (t === "block_quote") {
      out.push({ t: "quote", blocks: toBlocks(bp, child, doc) });
    } else if (t === "list") {
      const items = child.children().map((item) => toBlocks(bp, item, doc));
      const data = child.listData;
      out.push({ t: "list", ordered: data.type === "ordered", start: data.start || 1, items });
    } else if (t === "thematic_break") {
      out.push({ t: "break" });
    } else if (t === "table") {
      const rows = child.rows.map((row) => row.map((cell) => toInlines(bp, cell, doc)));
      out.push({ t: "table", aligns: child.aligns, rows, line: child.line });
    } else if (t === "footnote_def") {
      doc.pending.set(child.label, toBlocks(bp, child, doc));
    }
  }
  if (node.type === "document") {
    for (const label of doc.footnoteOrder) doc.footnotes.set(label, doc.pending.get(label));
  }
  return out;
}

const THAI_DIGITS = { "0": "\u0e50", "1": "\u0e51", "2": "\u0e52", "3": "\u0e53", "4": "\u0e54",
  "5": "\u0e55", "6": "\u0e56", "7": "\u0e57", "8": "\u0e58", "9": "\u0e59" };

function thaiDigits(text) {
  let out = "";
  for (const ch of text) out += THAI_DIGITS[ch] === undefined ? ch : THAI_DIGITS[ch];
  return out;
}

// Every paragraph's text, in document order. Hard breaks are newlines; task markers are □/■
// (ADR 0033); an ordered list's number is text and comes with the tab after it (ADR 0035); a
// bullet is drawn by the numbering part and is not text.
function plainText(blocks, numbersAreText, thai) {
  const out = [];
  for (const b of blocks) {
    const t = b.t;
    if (t === "paragraph" || t === "heading") out.push(inlineText(b.inlines));
    else if (t === "code") out.push(...(b.lines.length ? b.lines : [""]));
    else if (t === "quote") out.push(...plainText(b.blocks, numbersAreText, thai));
    else if (t === "list") {
      for (let n = 0; n < b.items.length; n++) {
        const item = b.items[n];
        const task = item.length && item[0].t === "paragraph" && item[0].inlines.length && item[0].inlines[0].t === "task";
        let marker = "";
        if (numbersAreText && b.ordered && !task) {
          const number = String(b.start + n);
          marker = (thai ? thaiDigits(number) : number) + ".\t";
        }
        if (!item.length || item[0].t !== "paragraph") {
          out.push(marker);
          out.push(...plainText(item, numbersAreText, thai));
          continue;
        }
        const lines = plainText(item, numbersAreText, thai);
        if (lines.length) out.push(marker + lines[0], ...lines.slice(1));
        else out.push(marker);
      }
    } else if (t === "table") {
      for (const row of b.rows) for (const cell of row) out.push(inlineText(cell));
    }
  }
  return out;
}

function inlineText(inlines) {
  const parts = [];
  for (const n of inlines) {
    if (n.t === "text") parts.push(n.s);
    else if (n.t === "hardbreak") parts.push("\n");
    else if (n.t === "task") parts.push(n.checked ? "■ " : "□ ");
  }
  return parts.join("");
}
