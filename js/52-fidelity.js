// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// thai-docx — fidelity: the port of scripts/thai_docx/fidelity.py. The text the package must hold,
// from the Markdown, and the text it does hold, read back from its XML (ADR 0023).

function docxText(parts, footnoteCount) {
  const out = [];
  const paragraphs = (root) => {
    for (const p of root.iter(w("p"))) {
      const pieces = [];
      let seen = false;
      let afterMark = false;
      for (const el of p.iter()) {
        const tag = el.tag;
        if (tag === w("footnoteRef")) {
          afterMark = true;
          seen = true;
        } else if (tag === w("t")) {
          pieces.push(el.text || "");
          seen = true;
          afterMark = false;
        } else if (tag === w("tab")) {
          if (!afterMark) pieces.push("\t");
          afterMark = false;
          seen = true;
        } else if (tag === w("br")) {
          pieces.push("\n");
          seen = true;
        } else if (tag === w("drawing")) {
          seen = true;
        }
      }
      if (seen) out.push(pieces.join(""));
    }
  };
  paragraphs(parseXml(fromUtf8(parts.get("word/document.xml"))));
  if (footnoteCount) {
    const root = parseXml(fromUtf8(parts.get("word/footnotes.xml")));
    for (const note of root.iter(w("footnote"))) if (note.get(w("type")) === null) paragraphs(note);
  }
  return out;
}

function expectedText(doc, opts) {
  const out = [];
  opts = opts || DEFAULTS;
  const items = layout(doc, opts)[0];
  if (opts.toc) out.push(...listEntries(items, "toc").map(([, text]) => text)); // the entries the field carries
  for (const item of items) {
    if (item.caption) out.push(captionText(item.caption));
    else if (item.block.t === "directive" && LIST_FIELDS[item.block.name] !== undefined) {
      out.push(...listEntries(items, item.block.name).map(([, text]) => text));
    } else if (item.block.t === "heading" && item.number !== undefined) {
      // the number is text in the heading's paragraph now, not a number an application draws
      const join = opts.chapter_title_on_new_line ? "\n" : " ";
      out.push(...plainText([item.block], opts.thai_digits).map((line) => item.number + join + line));
    } else out.push(...plainText([item.block], opts.thai_digits));
  }
  for (const label of doc.footnoteOrder) {
    const blocks = doc.footnotes.get(label);
    if (!blocks.length || blocks[0].t !== "paragraph") out.push("");
    out.push(...plainText(blocks, opts.thai_digits));
  }
  return out.map((s) => s.normalize("NFC"));
}
