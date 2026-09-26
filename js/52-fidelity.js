// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// thai-docx — fidelity: the port of scripts/thai_docx/fidelity.py. The text the package must hold,
// from the Markdown, and the text it does hold, read back from its XML (ADR 0023).

const XML_SPACE_ATTR = "{http://www.w3.org/XML/1998/namespace}space";

// Each paragraph's text under `root`, appended to `out`. A tab is text, except the one that
// separates a footnote's mark from its body. A w:t that does not say xml:space="preserve" loses
// the space at its ends, as an application reading it may drop it and Word does — so a space a
// writer left there without the attribute is not counted as text it kept.
function paragraphsInto(root, out) {
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
        const text = el.text || "";
        pieces.push(el.get(XML_SPACE_ATTR) === "preserve" ? text : text.replace(/^[ \t\n\r]+|[ \t\n\r]+$/g, ""));
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
}

function docxText(parts, footnoteCount) {
  const out = [];
  paragraphsInto(parseXml(fromUtf8(parts.get("word/document.xml"))), out);
  if (footnoteCount) {
    const root = parseXml(fromUtf8(parts.get("word/footnotes.xml")));
    for (const note of root.iter(w("footnote"))) if (note.get(w("type")) === null) paragraphsInto(note, out);
  }
  return out;
}

// The text of every part a reader sees — body, headers, footers, notes, comments — each
// paragraph as fidelity reads it, the parts in name order (package_text() in repair.py).
function packageText(parts) {
  const out = [];
  for (const name of [...parts.keys()].sort()) {
    if (TEXT_PARTS.test(name)) paragraphsInto(parseXml(fromUtf8(parts.get(name))), out);
  }
  return out;
}

function expectedText(doc, opts) {
  const out = [];
  opts = opts || DEFAULTS;
  const [items] = layout(doc, opts);
  // one answer for the whole document, as the writer takes it (ADR 0036)
  const numbersAreText = !opts.auto_numbering;
  if (opts.toc) out.push(...listEntries(items, "toc").map(([, text]) => text)); // the entries the field carries
  for (const item of items) {
    if (item.caption) out.push(captionText(item.caption));
    else if (item.block.t === "directive" && LIST_FIELDS[item.block.name] !== undefined) {
      out.push(...listEntries(items, item.block.name).map(([, text]) => text));
    } else if (item.block.t === "heading" && item.number !== undefined && numbersAreText) {
      // the number is text in the heading's own paragraph, not one an application draws (ADR 0036)
      const join = opts.chapter_title_on_new_line ? "\n" : " ";
      out.push(...plainText([item.block], true, opts.thai_digits).map((line) => item.number + join + line));
    } else if (item.block.t === "heading" && item.number !== undefined && opts.chapter_title_on_new_line) {
      // the application draws the number; the break after it is still the build's
      out.push(...plainText([item.block]).map((line) => "\n" + line));
    } else out.push(...plainText([item.block], numbersAreText, opts.thai_digits));
  }
  for (const label of doc.footnoteOrder) {
    const blocks = doc.footnotes.get(label);
    if (!blocks.length || blocks[0].t !== "paragraph") out.push("");
    out.push(...plainText(blocks, numbersAreText, opts.thai_digits));
  }
  return out.map((s) => s.normalize("NFC"));
}
