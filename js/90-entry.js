// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// thai-docx — entry: the command line under Node.js, and the ThaiDocx object for a
// sandbox that runs JavaScript with no file system (ADR 0007, 0008, 0030).

const OS_ERRORS = { ENOENT: "No such file or directory", EACCES: "Permission denied", EISDIR: "Is a directory", ENOTDIR: "Not a directory",
  ENOTREG: "not a regular file" };

function osError(e) {
  return OS_ERRORS[e && e.code] || "cannot be read";
}

function codedError(code) {
  const e = new Error(code);
  e.code = code;
  return e;
}

// At most `cap + 1` bytes of a regular file, so a caller sees that it is over the cap without
// asking the size first — read_regular() in thai_docx/package.py. The file is opened without
// waiting — a FIFO would otherwise wait for a writer — and what was opened is what is judged,
// so nothing can change between the look and the read. A directory is refused as the OS
// would name it; anything else that is not a regular file is refused before a byte is read.
function readRegular(fs, p, cap) {
  const fd = fs.openSync(p, fs.constants.O_RDONLY | (fs.constants.O_NONBLOCK || 0));
  try {
    const st = fs.fstatSync(fd);
    if (st.isDirectory()) throw codedError("EISDIR");
    if (!st.isFile()) throw codedError("ENOTREG");
    const buf = new Uint8Array(Math.min(st.size, cap) + 1);
    let n = 0;
    for (;;) {
      const got = fs.readSync(fd, buf, n, buf.length - n, null);
      if (got === 0 || (n += got) === buf.length) break;
    }
    return buf.subarray(0, n);
  } finally {
    fs.closeSync(fd);
  }
}

// Do two paths name one file — the same path, a symbolic link to it, or a hard link? A path
// that does not exist names no file yet (same_file() in thai_docx/package.py).
function sameFile(fs, a, b) {
  try {
    const one = fs.statSync(a, { bigint: true });
    const two = fs.statSync(b, { bigint: true });
    return one.dev === two.dev && one.ino === two.ino;
  } catch {
    return false;
  }
}

const MAX_MARKDOWN = 16 * 1024 * 1024;
const MAX_IMAGE = 32 * 1024 * 1024;

const MAX_LINKS = 40;

function splitRoot(path, p) {
  if (path.sep === "\\") {
    const m = /^(?:[A-Za-z]:|[\\/]{2}[^\\/]+[\\/][^\\/]+)?/.exec(p);
    return [m[0] + "\\", p.slice(m[0].length).split(/[\\/]/).filter((x) => x !== "" && x !== ".")];
  }
  return ["/", p.split("/").filter((x) => x !== "" && x !== ".")];
}

function parentOf(path, p, root) {
  let q = p;
  while (q.endsWith(path.sep)) q = q.slice(0, -1);
  const cut = q.lastIndexOf(path.sep);
  return cut < root.length ? root : q.slice(0, cut);
}

// The path as the file system walks it — the same walk as real_path() in
// thai_docx/build.py: each component's symbolic link followed, `..` taken from
// what is already resolved; a missing component, or a link past the fortieth,
// stays as written (ADR 0030 §4).
function realPath(fs, path, p) {
  if (!path.isAbsolute(p)) p = process.cwd() + path.sep + p;
  let [root, parts] = splitRoot(path, p);
  const pending = parts.reverse();
  let resolved = root;
  let links = 0;
  while (pending.length) {
    const part = pending.pop();
    if (part === "..") {
      resolved = parentOf(path, resolved, root);
      continue;
    }
    const candidate = resolved.endsWith(path.sep) ? resolved + part : resolved + path.sep + part;
    let isLink;
    try {
      isLink = fs.lstatSync(candidate).isSymbolicLink();
    } catch {
      isLink = false;
    }
    if (!isLink || links >= MAX_LINKS) {
      resolved = candidate;
      continue;
    }
    links++;
    let target;
    try {
      target = fs.readlinkSync(candidate);
    } catch {
      resolved = candidate;
      continue;
    }
    if (path.isAbsolute(target)) {
      [root, parts] = splitRoot(path, target);
      resolved = root;
    } else {
      parts = splitRoot(path, path.sep + target)[1];
    }
    for (let i = parts.length - 1; i >= 0; i--) pending.push(parts[i]);
  }
  return resolved;
}

function inside(path, p, dir) {
  return p === dir || p.startsWith(dir.endsWith(path.sep) ? dir : dir + path.sep);
}

function nodeBuild(mdPath, outPath, opts, allowDirs) {
  const fs = require("fs");
  const path = require("path");
  const result = { ok: false, file: outPath, settings: settingsJson(opts) };
  if (sameFile(fs, mdPath, outPath)) {
    result.error = "the output is the Markdown file itself; the build writes a new file, never over its input";
    return result;
  }
  let raw;
  try {
    raw = readRegular(fs, mdPath, MAX_MARKDOWN);
  } catch (e) {
    result.error = "cannot read " + mdPath + ": " + osError(e);
    return result;
  }
  if (raw.length > MAX_MARKDOWN) {
    result.error = "cannot read " + mdPath + ": larger than 16 MiB";
    return result;
  }
  const text = fromUtf8(raw);
  if (text === null) {
    result.error = "cannot read " + mdPath + ": not UTF-8 text";
    return result;
  }
  const resolved = realPath(fs, path, mdPath);
  const mdDir = parentOf(path, resolved, splitRoot(path, resolved)[0]);
  const roots = [mdDir, ...allowDirs.map((d) => realPath(fs, path, d))];
  const readImage = (src) => {
    const p = realPath(fs, path, path.isAbsolute(src) ? src : mdDir + path.sep + src);
    if (!roots.some((root) => inside(path, p, root))) {
      throw new BuildError("image '" + src + "' lies outside the Markdown file's directory; pass --allow-dir for its directory (ADR 0030 §4)");
    }
    let b;
    try {
      b = readRegular(fs, p, MAX_IMAGE);
    } catch (e) {
      throw new BuildError("image '" + src + "': " + osError(e));
    }
    if (b.length > MAX_IMAGE) throw new BuildError("image '" + src + "': larger than 32 MiB");
    return [p, b];
  };
  const [outcome, data] = buildText(text, opts, readImage);
  Object.assign(result, outcome);
  if (data === null) return result;
  try {
    fs.writeFileSync(outPath, data);
  } catch (e) {
    result.error = "cannot write " + outPath + ": " + osError(e);
    return result;
  }
  result.ok = true;
  return result;
}

function nodeCheck(argv) {
  if (argv.length !== 1 || argv[0] === "--help") {
    process.stdout.write(pyDumps({ ok: false, error: "usage: thai_docx check FILE.docx" }) + "\n");
    return 2;
  }
  const fs = require("fs");
  // at most one byte past the cap is read, as the Python checker reads it
  let bytes;
  try {
    bytes = readRegular(fs, argv[0], MAX_FILE);
  } catch (e) {
    // a name typed wrong is not a damaged document: `error`, as `build` answers it
    const report = new Report(argv[0]);
    report.error = "cannot read " + argv[0] + ": " + osError(e);
    process.stdout.write(pyDumps(report.asDict()) + "\n");
    return 2;
  }
  const report = checkBytes(bytes, argv[0]);
  process.stdout.write(pyDumps(report.asDict()) + "\n");
  if (report.findings.some((f) => f.code === "package" || f.code === "doctype" || f.code === "size")) return 2;
  return report.ok ? 0 : 1;
}

const MADE_WORSE = "the repair made a file its own checker faults";

function nodeRepair(argv) {
  let font = null;
  let thaiLanguage = false;
  let csAll = false;
  if (argv.indexOf("--thai-language") !== -1) {
    argv = argv.filter((a) => a !== "--thai-language");
    thaiLanguage = true;
  }
  if (argv.indexOf("--force-cs-whole-doc") !== -1) {
    argv = argv.filter((a) => a !== "--force-cs-whole-doc");
    csAll = true;
  }
  if (argv.length === 4 && argv[2] === "--font") {
    try {
      font = readValue("--font", argv[3]); // read as the build reads it
    } catch (e) {
      if (!(e instanceof BuildError)) throw e;
      process.stdout.write(pyDumps({ ok: false, error: e.what }) + "\n");
      return 2;
    }
    argv = argv.slice(0, 2);
  }
  if (argv.length !== 2 || argv.includes("--help")) {
    process.stdout.write(pyDumps({ ok: false, error: REPAIR_USAGE }) + "\n");
    return 2;
  }
  const fs = require("fs");
  const [inPath, outPath] = argv;
  const result = { ok: false, file: outPath };
  if (sameFile(fs, inPath, outPath)) {
    result.error = "the output is the file to repair; repair writes a new file, never over the one given (ADR 0037)";
    process.stdout.write(pyDumps(result) + "\n");
    return 2;
  }
  let data;
  try {
    data = readRegular(fs, inPath, MAX_FILE);
  } catch (e) {
    result.error = "cannot read " + inPath + ": " + osError(e);
    process.stdout.write(pyDumps(result) + "\n");
    return 2;
  }
  const before = checkBytes(data, inPath);
  const refused = before.findings.filter((f) => f.code === "package" || f.code === "doctype" || f.code === "size");
  if (refused.length) {
    // the same answer `check` gives: a file it cannot read is refused, not repaired
    result.error = inPath + ": " + refused[0].message;
    process.stdout.write(pyDumps(result) + "\n");
    return 2;
  }
  const ents = readZipDirectory(data);
  const parts = new Map(ents.map((e) => [e.name, readZipEntry(data, e)]));
  const foreign = foreignPrefix(parts);
  if (foreign !== null) {
    result.error = foreign + " writes WordprocessingML under a prefix other than w:; this version repairs" +
      " only the prefix Word writes, so nothing was written";
    process.stdout.write(pyDumps(result) + "\n");
    return 2;
  }
  const [replace, repaired, chosen, leftNames] = repairParts(parts, before.findings, font, thaiLanguage, csAll);
  const left = leftNames.filter((name) => before.findings.some((f) => f.part === name)).map((name) => ({ code: "left",
    message: name + " holds a comment, a CDATA section or a processing instruction; it is left as it came, and its findings with it" }));
  if (!replace.size && !before.findings.length) {
    // a clean file is an answer, not a fault: nothing to repair, so nothing is written
    delete result.file;
    Object.assign(result, { ok: true, repaired: {}, remaining: [], warnings: [{ code: "clean", message:
      "nothing here needs a repair; no file was written, and " + inPath + " can be used as it is" }].concat(before.warnings) });
    process.stdout.write(pyDumps(result) + "\n");
    return 0;
  }
  if (!replace.size) {
    result.repaired = {};
    result.remaining = before.findings;
    result.error = "nothing here is a repair this version makes; the findings say what is wrong";
    process.stdout.write(pyDumps(result) + "\n");
    return 2;
  }
  const out = repackZip(data, ents, Object.fromEntries(replace));
  // a repair answers for the file it writes: a fault its own checker finds there that the input
  // did not have is this version's, and nothing is written (exit 1)
  const after = checkBytes(out, outPath);
  const had = new Set(before.findings.map((f) => f.code + "\u0000" + f.part));
  const made = after.findings.filter((f) => !had.has(f.code + "\u0000" + f.part));
  if (made.length) {
    result.error = MADE_WORSE + " (" + made[0].code + " in " + made[0].part + "); nothing was written";
    process.stdout.write(pyDumps(result) + "\n");
    return 1;
  }
  const now = new Map(parts);
  for (const [k, v] of replace) now.set(k, v);
  // the text is the user's (ADR 0023, 0037): every part a reader sees, not only the body — a
  // difference of one character writes nothing
  const was = packageText(parts), is = packageText(now);
  if (was.length !== is.length || was.some((t, i) => t !== is[i])) {
    result.error = "the repair would have changed the document's text; nothing was written";
    process.stdout.write(pyDumps(result) + "\n");
    return 2;
  }
  const marked = repaired["thai-language"] || 0;
  delete repaired["thai-language"];
  // a finding in a part left as it came is still there by design, not a repair that failed
  const still = new Set(after.findings.filter((f) => !leftNames.includes(f.part)).map((f) => f.code));
  for (const code of Object.keys(repaired)) {
    if (still.has(code)) {
      result.error = "finding " + code + " is still there after the repair; nothing was written";
      process.stdout.write(pyDumps(result) + "\n");
      return 2;
    }
  }
  try {
    fs.writeFileSync(outPath, out);
  } catch (e) {
    result.error = "cannot write " + outPath + ": " + osError(e);
    process.stdout.write(pyDumps(result) + "\n");
    return 2;
  }
  result.ok = true;
  result.repaired = repaired;
  result.remaining = after.findings;
  result.warnings = (chosen ? [chosen] : []).concat(left, after.warnings);
  if (marked) {
    result.warnings = result.warnings.concat([{ code: "thai-language", message:
      'the Thai complex-script language w:bidi="th-TH" was written into ' + marked +
      " run properties, as --thai-language asked" }]);
  }
  result.sha256 = sha256Hex(out);
  result.bytes = out.length;
  process.stdout.write(pyDumps(result) + "\n");
  return after.findings.length ? 1 : 0;
}

function refuseLine(message, code) {
  process.stdout.write(pyDumps({ ok: false, error: message }) + "\n");
  return code;
}

// An argument that held bytes of another encoding: Node puts U+FFFD in each one's place and
// cannot tell it from one typed, Python keeps a lone surrogate — so both refuse either, and give
// the same answer for the same argument.
function notText(arg) {
  return arg.includes("\ufffd") || /[\ud800-\udbff](?![\udc00-\udfff])|(?<![\ud800-\udbff])[\udc00-\udfff]/.test(arg);
}

function cliMain(argv) {
  const bad = argv.findIndex(notText);
  if (bad >= 0) return refuseLine("argument " + (bad + 1) + " is not UTF-8 text; a name or value in another encoding cannot be read", 2);
  try {
    process.cwd();
  } catch {
    return refuseLine("the working directory no longer exists; run the command from one that does", 2);
  }
  try {
    return cliCommand(argv);
  } catch {
    // SKILL.md reads exit 1 as a defect in this skill: that is what this is
    return refuseLine("a defect in thai-docx stopped this command; do not retry — report it with the input that caused it", 1);
  }
}

function cliCommand(argv) {
  if (argv.length && argv[0] === "check") return nodeCheck(argv.slice(1));
  if (argv.length && argv[0] === "repair") return nodeRepair(argv.slice(1));
  if (argv.length && argv[0] === "grill") {
    const result = grillRun(argv.slice(1));
    process.stdout.write(pyDumps(result) + "\n");
    return result.ok ? 0 : 2;
  }
  if (argv.length && argv[0] === "profile") {
    let result;
    try {
      result = profileRun(argv.slice(1));
    } catch (e) {
      if (!(e instanceof ProfileError)) throw e;
      process.stdout.write(pyDumps({ ok: false, error: e.what }) + "\n");
      return 2;
    }
    process.stdout.write(pyDumps(result) + "\n");
    return 0;
  }
  if (argv.length && argv[0] === "build") {
    let opts, positional, allow, used;
    try {
      let rest;
      [rest, used] = profileExpand(argv.slice(1));
      [opts, positional, allow] = parseArgs(rest);
    } catch (e) {
      if (!(e instanceof BuildError) && !(e instanceof ProfileError)) throw e;
      process.stdout.write(pyDumps({ ok: false, error: e.what }) + "\n");
      return 2;
    }
    const result = nodeBuild(positional[0], positional[1], opts, allow);
    if (used !== null) result.profile = used;
    process.stdout.write(pyDumps(result) + "\n");
    if (result.ok) return 0;
    return "error" in result ? 2 : 1;
  }
  process.stdout.write(pyDumps({ ok: false, error: "usage: thai_docx check FILE.docx | build IN.md OUT.docx | repair IN.docx OUT.docx | profile ... | grill --said ..." }) + "\n");
  return 2;
}

// For a JavaScript sandbox (no files): build from Markdown text. `args` are the
// command's flags, e.g. ["--toc"]; `images` maps a Markdown image path to its bytes.
// Returns { result, bytes } — result is the JSON line the command would print
// (without "file"), bytes the .docx, or null when the build refused.
function buildDocument(markdown, args, images) {
  let opts;
  try {
    [opts] = parseArgs([...(args || []), "in.md", "out.docx"]);
  } catch (e) {
    if (!(e instanceof BuildError)) throw e;
    return { result: { ok: false, error: e.what }, bytes: null };
  }
  const table = images || {};
  const readImage = (src) => {
    if (src.split(/[\\/]/).includes("..") || src.startsWith("/") || src.startsWith("\\")) {
      throw new BuildError("image '" + src + "' lies outside the Markdown file's directory; pass --allow-dir for its directory (ADR 0030 §4)");
    }
    if (!Object.prototype.hasOwnProperty.call(table, src)) throw new BuildError("image '" + src + "': No such file or directory");
    return [src, table[src]];
  };
  const result = { ok: false, settings: settingsJson(opts) };
  const [outcome, data] = buildText(markdown, opts, readImage);
  Object.assign(result, outcome);
  result.ok = data !== null;
  return { result: JSON.parse(pyDumps(result)), bytes: data };
}

function checkDocument(bytes) {
  return JSON.parse(pyDumps(checkBytes(bytes, "<bytes>").asDict()));
}
