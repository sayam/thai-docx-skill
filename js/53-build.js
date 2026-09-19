// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// thai-docx — build: the port of scripts/thai_docx/build.py — the flow, and nothing else (ADR 0028).

// `line N: …` messages in line order; messages on one line keep theirs.
function byLine(messages) {
  return messages.map((m, k) => [parseInt(m.split(":")[0].split(" ")[1], 10), k, m]).sort((a, b) => a[0] - b[0] || a[1] - b[1]).map((x) => x[2]);
}

// The build from Markdown text to package bytes: [outcome, bytes-or-null].
// `readImage(src)` returns [resolvedPath, Uint8Array] or throws BuildError.
function buildText(text, opts, readImage) {
  let doc, writer, parts;
  try {
    doc = parseMarkdown(text);
    writer = new Package(doc, opts, readImage);
    parts = writer.pkg();
  } catch (e) {
    if (e instanceof Unsupported) return [{ error: e.what, line: e.line }, null];
    if (e instanceof BuildError) return [{ error: e.what }, null];
    throw e;
  }
  const data = packZip(parts);
  const report = checkBytes(data, "<bytes>");
  const findings = report.findings.slice();
  if (!findings.length) {
    const expected = expectedText(doc, opts);
    const actual = docxText(new Map(parts), doc.footnoteOrder.length);
    const same = expected.length === actual.length && expected.every((v, i) => v === actual[i]);
    if (!same) {
      let idx = Math.min(expected.length, actual.length);
      for (let i = 0; i < Math.min(expected.length, actual.length); i++) {
        if (expected[i] !== actual[i]) {
          idx = i;
          break;
        }
      }
      findings.push({ code: "fidelity", part: "word/document.xml",
        message: "paragraph " + (idx + 1) + " does not match the Markdown (" + expected.length + " paragraphs expected, " + actual.length + " written)" });
    }
  }
  const items = writer.items;
  const present = new Set([
    ["tables", writer.counts.tables > 0],
    ["table captions", items.some((item) => item.caption && item.caption.kind === "table")],
    ["figure captions", items.some((item) => item.caption && item.caption.kind === "figure")],
    ["chapters or appendices", writer.hasChapters],
    ["numbered headings", items.some((item) => item.number !== undefined)],
    ["appendices", writer.regions.includes("appendices")],
    ["appendix headings", items.some((item) => item.number !== undefined && item.region === "appendices")],
    ["chapter headings", items.some((item) => item.number !== undefined && item.region === "chapters")],
    ["front", writer.regions.includes("front")],
    ["numbers", writer.hasOrderedList || items.some((item) => item.number !== undefined || item.caption !== undefined)],
    ["toc comment", items.some((item) => item.block.t === "directive" && item.block.name === "toc")],
  ].filter(([, there]) => there).map(([name]) => name));
  const outcome = {
    counts: { ...writer.counts, runs: report.counts.runs || 0 },
    warnings: byLine([...writer.styleWarnings, ...writer.layoutWarnings, ...doc.warnings]).map((m) => ({ code: "markdown", message: m }))
      .concat(settingsWarnings(opts, present).map((m) => ({ code: "settings", message: m }))).concat(report.warnings),
    findings,
    sha256: sha256Hex(data),
    bytes: data.length,
  };
  // `size` is not a defect in the builder: it says the images the user asked for do not fit
  // in a .docx. SKILL.md reads exit 1 as "a defect in this skill; do not retry", so this
  // leaves by the other door — `error`, exit 2, the door for input a user can change.
  const tooBig = findings.find((f) => f.code === "size");
  if (tooBig) {
    outcome.findings = findings.filter((f) => f !== tooBig);
    outcome.error = "the document does not fit in a .docx — " + tooBig.message.replace("; refused", "")
      + "; images are what makes a document this large, so use smaller ones";
    return [outcome, null];
  }
  return [outcome, findings.length ? null : data];
}

