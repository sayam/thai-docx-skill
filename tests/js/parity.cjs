// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// The JavaScript implementation, driven the way tests/test_js_parity.py drives the
// Python one, so the two can be compared. Reads one JSON request on stdin:
//   {"op": "ast",   "texts": [...]}
//   {"op": "build", "cases": [{"text", "args", "images": {src: base64}}]}
//   {"op": "check", "packages": [base64, ...]}
// and writes a JSON array of results. Test-only.
"use strict";
const fs = require("fs");
const path = require("path");
const T = require(path.join(__dirname, "..", "..", "skills", "thai-docx", "scripts", "thai_docx.js"));

function astOf(text) {
  try {
    const doc = T.parseMarkdown(text);
    return {
      blocks: doc.blocks,
      footnotes: doc.footnoteOrder.map((label) => [label, doc.footnotes.get(label)]),
      front_matter: [...doc.frontMatter.entries()],
      warnings: doc.warnings,
    };
  } catch (e) {
    if (e && e.what !== undefined) return { error: e.what, line: e.line };
    return { crash: String(e && e.stack) };
  }
}

const req = JSON.parse(fs.readFileSync(0, "utf8"));
let out;
if (req.op === "ast") {
  out = req.texts.map(astOf);
} else if (req.op === "build") {
  out = req.cases.map((c) => {
    try {
      const images = {};
      for (const [k, v] of Object.entries(c.images || {})) images[k] = new Uint8Array(Buffer.from(v, "base64"));
      const { result, bytes } = T.buildDocument(c.text, c.args, images);
      return { result, bytes: bytes === null ? null : Buffer.from(bytes).toString("base64") };
    } catch (e) {
      return { crash: String(e && e.stack) };
    }
  });
} else if (req.op === "repack") {
  // the package again, with the named parts rewritten: the bytes, base64
  out = req.cases.map((c) => {
    try {
      const b = new Uint8Array(Buffer.from(c.package, "base64"));
      const replace = {};
      for (const [k, v] of Object.entries(c.replace || {})) replace[k] = new Uint8Array(Buffer.from(v, "base64"));
      const again = T.repackZip(b, T.readZipDirectory(b), replace);
      return { bytes: Buffer.from(again).toString("base64") };
    } catch (e) {
      if (e && e.message !== undefined) return { error: e.message };
      return { crash: String(e && e.stack) };
    }
  });
} else if (req.op === "check") {
  out = req.packages.map((b64) => {
    try {
      return T.checkDocument(new Uint8Array(Buffer.from(b64, "base64")));
    } catch (e) {
      return { crash: String(e && e.stack) };
    }
  });
}
process.stdout.write(JSON.stringify(out));
