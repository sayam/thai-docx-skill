// The CommonMark reference implementation (commonmark.js 0.31.2) reduced to the
// canonical sequence tests/oracle.py builds — the strict oracle for the core
// dialect. Reads a JSON array of Markdown strings on stdin, writes a JSON array
// of canonical sequences (or {"error": ...}) on stdout. Test-only.
'use strict';
const fs = require('fs');
const path = require('path');
const cm = require(path.join(__dirname, 'node_modules', 'commonmark'));

const TAG = /^<(\/?)([A-Za-z][A-Za-z0-9-]*)/;

function inline(node) {
  const items = [];
  const flags = { b: 0, i: 0 };
  const tags = { sup: 0, sub: 0, u: 0, kbd: 0 };
  const fl = (code) => {
    const f = [];
    if (flags.b) f.push('b');
    if (flags.i) f.push('i');
    if (code || tags.kbd) f.push('code');
    if (tags.u) f.push('u');
    if (tags.sup) f.push('sup');
    else if (tags.sub) f.push('sub');
    return f;
  };
  let link = null;
  const walk = (parent) => {
    for (let n = parent.firstChild; n; n = n.next) {
      switch (n.type) {
        case 'text': items.push(['t', n.literal, fl(false), link]); break;
        case 'code': items.push(['t', n.literal, fl(true), link]); break;
        case 'softbreak': items.push(['soft', ' ', fl(false), link]); break;
        case 'linebreak': items.push(['br']); break;
        case 'emph': flags.i++; walk(n); flags.i--; break;
        case 'strong': flags.b++; walk(n); flags.b--; break;
        case 'link': { const saved = link; link = n.destination; walk(n); link = saved; break; }
        case 'image': items.push(['img', n.destination]); break;
        case 'html_inline': {
          const c = n.literal;
          if (c.startsWith('<!--')) break;
          const m = TAG.exec(c);
          if (!m) { items.push(['html', c]); break; }
          const name = m[2].toLowerCase();
          if (name === 'br') items.push(['br']);
          else if (name in tags) tags[name] = Math.max(0, tags[name] + (m[1] ? -1 : 1));
          else items.push(['html', c]);
          break;
        }
        default: items.push(['unknown', n.type]);
      }
    }
  };
  walk(node);
  return items;
}

function blocks(parent, out) {
  for (let n = parent.firstChild; n; n = n.next) {
    switch (n.type) {
      case 'heading': out.push(['h', n.level, inline(n)]); break;
      case 'paragraph': out.push(['p', inline(n)]); break;
      case 'code_block': {
        const c = n.literal;
        out.push(['code', c.endsWith('\n') ? c.slice(0, -1) : c]);
        break;
      }
      case 'thematic_break': out.push(['hr']); break;
      case 'block_quote': out.push(['bq']); blocks(n, out); out.push(['/bq']); break;
      case 'list': {
        const ordered = n.listType === 'ordered';
        out.push(ordered ? ['ol', n.listStart] : ['ul']);
        blocks(n, out);
        out.push([ordered ? '/ol' : '/ul']);
        break;
      }
      case 'item': out.push(['li']); blocks(n, out); out.push(['/li']); break;
      case 'html_block': out.push(['html_block', n.literal]); break;
      default: out.push(['unknown', n.type]);
    }
  }
}

const inputs = JSON.parse(fs.readFileSync(0, 'utf8'));
const results = inputs.map((text) => {
  try {
    const out = [];
    blocks(new cm.Parser().parse(text), out);
    return out;
  } catch (e) {
    return { error: String(e) };
  }
});
process.stdout.write(JSON.stringify(results));
