// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// ESLint over js/*.js, the sources of skills/thai-docx/scripts/thai_docx.js: the rules
// @eslint/js calls recommended, and nothing else. Run it from the repository root:
//   tests/js/node_modules/.bin/eslint --config tests/js/eslint.config.cjs js
// The generated bundle is not linted; it is these files joined (tools/bundle_js.py).
"use strict";
const fs = require("fs");
const path = require("path");
const js = require("@eslint/js");
const globals = require("globals");

const ROOT = path.join(__dirname, "..", "..");
const PARTS = fs.readdirSync(path.join(ROOT, "js")).filter((n) => n.endsWith(".js")).sort();
const TEXT = Object.fromEntries(PARTS.map((n) => [n, fs.readFileSync(path.join(ROOT, "js", n), "utf8")]));

// The bundler joins the parts inside one function, so a part uses what another declares
// at its top level, and the bundle's `api` object uses what no part does. Each part is
// linted with the other parts' top-level names as globals, and a top-level name counts as
// used when another part or `api` names it; a name used nowhere is still reported.
const DECLARED = /^(?:async\s+)?(?:function\*?|class|const|let|var)\s+([A-Za-z_$][\w$]*)/gm;
const declared = (n) => [...TEXT[n].matchAll(DECLARED)].map((m) => m[1]);
const bundler = fs.readFileSync(path.join(ROOT, "tools", "bundle_js.py"), "utf8");
const API = [...bundler.match(/^API = \(([^)]*)\)/m)[1].matchAll(/"([\w$]+)"/g)].map((m) => m[1]);
const WRAPPER = { VERSION: "readonly" }; // declared by the bundler before the parts

// The bundle runs under Node.js and in a sandbox with no modules (ADR 0008), so a part may
// use only the globals both share; the command line and the profile files are the parts
// that run only under Node.js, and they alone may reach its names (ADR 0040).
// a name as a regular expression that matches only itself
const escapeRegExp = (text) => text.replace(/[\\^$.*+?()[\]{}|]/g, "\\$&");
const NODE_ONLY = new Set(["55-profiles.js", "90-entry.js"]);
const NODE = { require: "readonly", process: "readonly", __dirname: "readonly" };

module.exports = [
  { basePath: ROOT, files: ["js/*.js"], ...js.configs.recommended },
  ...PARTS.map((name) => {
    const others = PARTS.filter((n) => n !== name);
    const shared = Object.fromEntries(others.flatMap((n) => declared(n).map((v) => [v, "readonly"])));
    const usedElsewhere = declared(name).filter(
      (v) => API.includes(v) || others.some((n) => new RegExp("(?<![\\w$])" + escapeRegExp(v) + "(?![\\w$])").test(TEXT[n])),
    );
    return {
      basePath: ROOT,
      files: ["js/" + name],
      languageOptions: {
        ecmaVersion: "latest",
        sourceType: "script",
        globals: { ...globals["shared-node-browser"], ...(NODE_ONLY.has(name) ? NODE : {}), ...shared, ...WRAPPER },
      },
      rules: {
        // `_` is a value a loop must take and does not use, as in the Python it ports
        "no-unused-vars": ["error", { varsIgnorePattern: "^(?:" + ["_", ...usedElsewhere].map(escapeRegExp).join("|") + ")$" }],
      },
    };
  }),
];
