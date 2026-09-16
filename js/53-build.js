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
  // a flag that changed nothing is said out loud, never dropped in silence
  const settingsWarnings = [];
  if (opts.chapter_title_on_new_line && !writer.items.some((item) => item.number !== undefined)) {
    settingsWarnings.push("--chapter-title-on-new-line changed nothing: the document has no" +
      " <!-- chapters --> or <!-- appendices --> comment, so no heading carries a number");
  }
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
  const outcome = {
    counts: { ...writer.counts, runs: report.counts.runs || 0 },
    warnings: byLine([...writer.styleWarnings, ...writer.layoutWarnings, ...doc.warnings]).map((m) => ({ code: "markdown", message: m }))
      .concat(settingsWarnings.map((m) => ({ code: "settings", message: m }))).concat(report.warnings),
    findings,
    sha256: sha256Hex(data),
    bytes: data.length,
  };
  return [outcome, findings.length ? null : data];
}

