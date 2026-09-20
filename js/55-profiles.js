// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// thai-docx — profiles: the JavaScript port of scripts/thai_docx/profiles.py. A profile
// holds settings and nothing else; its values are checked by turning them into the
// build's own flags (ADR 0024), and reads and writes stay inside the profile
// directories (ADR 0030).

const PROFILE_SCHEMA = 1;
const PROFILE_DIR = ".thai-docx";
const PROFILE_KEYS = ["schema", "id", "title", "description", "version", "source", "maintainer", "settings"];
const PROFILE_TEXT_KEYS = ["id", "version", "source", "maintainer"];
const PROFILE_MAX_TEXT = 200;
const PROFILE_MAX_BYTES = 64 * 1024; // a profile is settings; anything larger is not one (ADR 0030)
// setting → how it is written as a flag, from the registry (ADR 0028); "switch" flags say the value that turns them on
const PROFILE_FLAGS = Object.fromEntries(SETTINGS.map((s) => [s.key, [s.kind, s.flag]]));
const FLOAT_SETTINGS = SETTINGS.filter((s) => s.read && (s.read[0] === "number" || s.read[0] === "numbers")).map((s) => s.key); // Python writes these as floats

class ProfileError extends Error {
  constructor(what) {
    super(what);
    this.what = what;
  }
}

// A number as a flag takes it, the same text from both implementations.
function profileNumber(x) {
  const v = x instanceof PyFloat ? x.value : x;
  return Number.isInteger(v) ? String(v) : String(v);
}

// The settings as the flags that set them, in one fixed order.
function profileAsFlags(settings) {
  const out = [];
  for (const key of Object.keys(PROFILE_FLAGS)) {
    if (!Object.prototype.hasOwnProperty.call(settings, key)) continue;
    const [kind, flag] = PROFILE_FLAGS[key];
    const raw = settings[key];
    const value = raw instanceof PyFloat ? raw.value : raw;
    if (kind === "switch") {
      if (value === true) out.push(flag);
    } else if (kind === "off") {
      if (value === false) out.push(flag);
    } else if (kind === "list") {
      out.push(flag, value.map(profileNumber).join(","));

    } else if (value !== null && value !== false && value !== undefined) {
      out.push(flag, typeof value === "string" ? value : profileNumber(value));
    }
  }
  return out;
}

// What a profile would hold for these options: every setting that is not the default.
function profileSettingsOf(opts) {
  const out = {};
  for (const key of Object.keys(PROFILE_FLAGS)) {
    const value = opts[key];
    const fallback = DEFAULTS[key];
    const same = Array.isArray(value) ? value.length === fallback.length && value.every((v, i) => v === fallback[i]) : value === fallback;
    if (same) continue;
    if (key === "margins") out[key] = value.map((v) => new PyFloat(v));
    else if (FLOAT_SETTINGS.includes(key)) out[key] = new PyFloat(value);
    else out[key] = value;
  }
  return out;
}

// One written form: sorted keys, two spaces, UTF-8 as itself, one final newline —
// json.dumps(ensure_ascii=False, indent=2, sort_keys=True) in Python.
function canonicalJson(value, indent) {
  const pad = indent === undefined ? "" : indent;
  if (value === null || value === undefined) return "null";
  if (value === true) return "true";
  if (value === false) return "false";
  if (value instanceof PyFloat) return Number.isInteger(value.value) ? value.value.toFixed(1) : String(value.value);
  if (typeof value === "number") return String(value);
  if (typeof value === "string") return pyString(value);
  const inner = pad + "  ";
  if (Array.isArray(value)) {
    if (!value.length) return "[]";
    return "[\n" + value.map((v) => inner + canonicalJson(v, inner)).join(",\n") + "\n" + pad + "]";
  }
  const keys = Object.keys(value).sort();
  if (!keys.length) return "{}";
  return "{\n" + keys.map((k) => inner + pyString(k) + ": " + canonicalJson(value[k], inner)).join(",\n") + "\n" + pad + "}";
}

function profileCanonical(profile) {
  return canonicalJson(profile, "") + "\n";
}

function profileDigest(settings) {
  return sha256Hex(new TextEncoder().encode(profileCanonical(settings)));
}

// JSON as Python's json.loads reads it: a number written with a fraction or an exponent
// is a float (kept as PyFloat, so it is written back as one), any other is an integer.
// Nothing else is accepted — no NaN, no Infinity, no trailing text.
function jsonParsePy(text, where) {
  let i = 0;
  const fail = () => {
    // the two implementations read JSON with their own parsers; the fault is the file
    throw new ProfileError(where + ": not JSON");
  };
  const ws = () => {
    while (i < text.length && (text[i] === " " || text[i] === "\t" || text[i] === "\n" || text[i] === "\r")) i += 1;
  };
  const literal = (word, value) => {
    if (text.startsWith(word, i)) {
      i += word.length;
      return value;
    }
    return fail();
  };
  const string = () => {
    if (text[i] !== '"') return fail();
    i += 1;
    let out = "";
    while (true) {
      if (i >= text.length) return fail();
      const c = text[i];
      if (c === '"') {
        i += 1;
        return out;
      }
      if (c === "\\") {
        const e = text[i + 1];
        i += 2;
        if (e === "u") {
          const hex = text.slice(i, i + 4);
          if (!/^[0-9A-Fa-f]{4}$/.test(hex)) return fail();
          out += String.fromCharCode(parseInt(hex, 16));
          i += 4;
        } else if ('"\\/'.includes(e)) out += e;
        else if (e === "b") out += "\b";
        else if (e === "f") out += "\f";
        else if (e === "n") out += "\n";
        else if (e === "r") out += "\r";
        else if (e === "t") out += "\t";
        else return fail();
        continue;
      }
      if (c < " ") return fail();
      out += c;
      i += 1;
    }
  };
  const value = () => {
    ws();
    if (i >= text.length) return fail();
    const c = text[i];
    if (c === "{") {
      i += 1;
      const out = {};
      ws();
      if (text[i] === "}") {
        i += 1;
        return out;
      }
      while (true) {
        ws();
        const key = string();
        ws();
        if (text[i] !== ":") return fail();
        i += 1;
        out[key] = value();
        ws();
        if (text[i] === ",") {
          i += 1;
          continue;
        }
        if (text[i] === "}") {
          i += 1;
          return out;
        }
        return fail();
      }
    }
    if (c === "[") {
      i += 1;
      const out = [];
      ws();
      if (text[i] === "]") {
        i += 1;
        return out;
      }
      while (true) {
        out.push(value());
        ws();
        if (text[i] === ",") {
          i += 1;
          continue;
        }
        if (text[i] === "]") {
          i += 1;
          return out;
        }
        return fail();
      }
    }
    if (c === '"') return string();
    if (c === "t") return literal("true", true);
    if (c === "f") return literal("false", false);
    if (c === "n") return literal("null", null);
    const m = /^-?(?:0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?/.exec(text.slice(i));
    if (!m) return fail();
    i += m[0].length;
    const n = Number(m[0]);
    return m[1] || m[2] ? new PyFloat(n) : n;
  };
  const out = value();
  ws();
  if (i !== text.length) fail();
  return out;
}

// A profile as ADR 0024 allows it, or ProfileError naming the file and the key.
function profileValidate(data, where) {
  if (data === null || typeof data !== "object" || Array.isArray(data)) throw new ProfileError(where + ": a profile is a JSON object");
  if (data.schema !== PROFILE_SCHEMA) throw new ProfileError(where + ': "schema" must be ' + PROFILE_SCHEMA);
  for (const key of Object.keys(data)) {
    if (!PROFILE_KEYS.includes(key)) throw new ProfileError(where + ': unknown key "' + key + '"; a profile holds ' + PROFILE_KEYS.join(", "));
  }
  for (const key of PROFILE_TEXT_KEYS) {
    if (Object.prototype.hasOwnProperty.call(data, key) &&
        (typeof data[key] !== "string" || !data[key] || codePointLength(data[key]) > PROFILE_MAX_TEXT)) {
      throw new ProfileError(where + ': "' + key + '" takes text of 1 to ' + PROFILE_MAX_TEXT + " characters");
    }
  }
  for (const key of ["title", "description"]) {
    const value = Object.prototype.hasOwnProperty.call(data, key) ? data[key] : {};
    const bad = value === null || typeof value !== "object" || Array.isArray(value) ||
      Object.keys(value).some((k) => k !== "th" && k !== "en") ||
      Object.values(value).some((v) => typeof v !== "string" || codePointLength(v) > PROFILE_MAX_TEXT);
    if (bad) throw new ProfileError(where + ': "' + key + '" takes th and/or en text of at most ' + PROFILE_MAX_TEXT + " characters");
  }
  const settings = data.settings;
  if (settings === null || typeof settings !== "object" || Array.isArray(settings)) throw new ProfileError(where + ': "settings" must be an object');
  for (const key of Object.keys(settings)) {
    if (!Object.prototype.hasOwnProperty.call(PROFILE_FLAGS, key)) {
      throw new ProfileError(where + ': unknown setting "' + key + '"; the settings are ' + Object.keys(PROFILE_FLAGS).join(", "));
    }
  }
  try {
    parseArgs(profileAsFlags(settings).concat(["in.md", "out.docx"]));
  } catch (e) {
    if (!(e instanceof BuildError)) throw e;
    throw new ProfileError(where + ": " + e.what);
  }
  return data;
}

// Where a name is looked for, first match winning (ADR 0024, 0030).
function profileDirectories() {
  const path = require("path");
  const os = require("os");
  const skill = path.resolve(__dirname, "..");
  return [
    ["project", path.join(path.resolve("."), PROFILE_DIR, "profiles")],
    ["home", path.join(os.homedir(), PROFILE_DIR, "profiles")],
    ["skill", path.join(skill, "profiles")],
  ];
}

function profileIsPath(name) {
  return name.includes("/") || name.includes("\\") || name.endsWith(".json");
}

// A name, never a path: what a profile is saved, imported or looked for under.
function profileCheckName(name) {
  if (!name || codePointLength(name) > 64 || [...'\\/:*?"<>| \t'].some((c) => name.includes(c)) || name.startsWith(".")) {
    throw new ProfileError("profile name '" + name + "' is not a name; use letters, digits, - or _");
  }
  return name;
}

// A path as Python's pathlib writes it: "." and empty components dropped, a leading "//"
// kept, "." for nothing. POSIX only; on Windows the path stays as given.
function profilePathString(p) {
  const path = require("path");
  if (path.sep !== "/") return p;
  const root = p.startsWith("//") && !p.startsWith("///") ? "//" : p.startsWith("/") ? "/" : "";
  return root + p.split("/").filter((x) => x !== "" && x !== ".").join("/") || ".";
}

function profileFind(name) {
  const fs = require("fs");
  const path = require("path");
  if (profileIsPath(name)) return ["path", profilePathString(name)];
  profileCheckName(name);
  for (const [where, directory] of profileDirectories()) {
    const p = path.join(directory, name + ".json");
    try {
      if (fs.statSync(p).isFile()) return [where, p];
    } catch {
      // not there
    }
  }
  throw new ProfileError("no profile named '" + name + "'; `thai_docx profile list` shows the ones there are");
}

function profileRead(p) {
  const fs = require("fs");
  // read at most one byte past the limit, rather than ask the size first: a file that
  // changes between the two, or has no size (/dev/zero), cannot get past it
  const raw = new Uint8Array(PROFILE_MAX_BYTES + 1);
  let n = 0;
  try {
    const fd = fs.openSync(p, "r");
    try {
      let got;
      while (n < raw.length && (got = fs.readSync(fd, raw, n, raw.length - n, null)) > 0) n += got;
    } finally {
      fs.closeSync(fd);
    }
  } catch (e) {
    throw new ProfileError("cannot read " + p + ": " + osError(e));
  }
  if (n > PROFILE_MAX_BYTES) throw new ProfileError(p + ": larger than 64 KiB; a profile is settings");
  const text = new TextDecoder("utf-8").decode(raw.subarray(0, n));
  return profileValidate(jsonParsePy(text, p), p);
}

function profileIsFile(p) {
  const fs = require("fs");
  try {
    return fs.statSync(p).isFile();
  } catch {
    return false;
  }
}

function profileWrite(profile, p) {
  const fs = require("fs");
  const path = require("path");
  try {
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, profileCanonical(profile));
  } catch (e) {
    throw new ProfileError("cannot write " + p + ": " + osError(e));
  }
}

function profileTarget(name, project) {
  const path = require("path");
  profileCheckName(name);
  const where = project ? "project" : "home";
  const directory = profileDirectories().find(([w]) => w === where)[1];
  return path.join(directory, name + ".json");
}

// Every profile found, in search order; a name found twice says which one a build uses.
function profileListing() {
  const fs = require("fs");
  const path = require("path");
  const out = [];
  const seen = new Set();
  for (const [where, directory] of profileDirectories()) {
    let names;
    try {
      names = fs.readdirSync(directory).filter((n) => n.endsWith(".json")).sort();
    } catch {
      names = [];
    }
    for (const file of names) {
      const p = path.join(directory, file);
      const name = file.slice(0, -5);
      let row;
      try {
        const data = profileRead(p);
        row = { name, where, path: p, title: Object.prototype.hasOwnProperty.call(data, "title") ? data.title : {}, settings: Object.keys(data.settings).length };
      } catch (e) {
        if (!(e instanceof ProfileError)) throw e;
        row = { name, where, path: p, error: e.what };
      }
      row.used = !seen.has(name);
      seen.add(name);
      out.push(row);
    }
  }
  return out;
}

const PROFILE_USAGE = "usage: thai_docx profile list | show NAME | save NAME [--from NAME [--default SETTING[,SETTING]]] [--project] [build flags] | " +
  "export NAME [OUT.json] | import FILE.json [--name NAME] [--project]";

// Take `--name VALUE` or `--name=VALUE` out of argv; null when it is not there.
function profileTakeFlag(argv, name) {
  const out = [];
  let value = null;
  let i = 0;
  while (i < argv.length) {
    const at = argv[i].indexOf("=");
    const head = at < 0 ? argv[i] : argv[i].slice(0, at);
    if (head === name) {
      if (at >= 0) value = argv[i].slice(at + 1);
      else if (i + 1 < argv.length) {
        value = argv[i + 1];
        i += 1;
      } else throw new ProfileError(name + " needs a value");
      i += 1;
      continue;
    }
    out.push(argv[i]);
    i += 1;
  }
  return [out, value];
}

// Take every `--default SETTING[,SETTING]` out of argv: the settings a profile gives back
// to their defaults before any flag applies (ADR 0029).
function profileTakeDefaults(argv) {
  const out = [];
  const keys = [];
  let i = 0;
  while (i < argv.length) {
    const at = argv[i].indexOf("=");
    const head = at < 0 ? argv[i] : argv[i].slice(0, at);
    if (head !== "--default") {
      out.push(argv[i]);
      i += 1;
      continue;
    }
    if (at < 0 && i + 1 >= argv.length) throw new ProfileError("--default needs a value");
    const value = at >= 0 ? argv[i].slice(at + 1) : argv[i + 1];
    i += at >= 0 ? 1 : 2;
    for (const key of value.split(",")) {
      if (!Object.prototype.hasOwnProperty.call(PROFILE_FLAGS, key)) {
        throw new ProfileError('--default: unknown setting "' + key + '"; the settings are ' + Object.keys(PROFILE_FLAGS).join(", "));
      }
      keys.push(key);
    }
  }
  return [out, keys];
}

function profileWithout(settings, keys) {
  const out = {};
  for (const [k, v] of Object.entries(settings)) if (!keys.includes(k)) out[k] = v;
  return out;
}

// A save or import that took the place of a profile says so where the user will hear it.
function profileReplacing(result) {
  if (result.replaced) result.warnings = ["replaced the profile " + result.name + " that was there before"];
  return result;
}

function profileRun(argv) {
  const path = require("path");
  if (!argv.length) throw new ProfileError(PROFILE_USAGE);
  const command = argv[0];
  let rest = argv.slice(1);
  if (command === "list" && !rest.length) return { ok: true, profiles: profileListing() };
  if (command === "show" && rest.length === 1) {
    const [where, p] = profileFind(rest[0]);
    const data = profileRead(p);
    const [opts] = parseArgs(profileAsFlags(data.settings).concat(["in.md", "out.docx"]));
    return { ok: true, name: path.basename(p, ".json"), where, path: p, settings: data.settings,
      resolved: settingsJson(opts), sha256: profileDigest(data.settings) };
  }
  if (command === "save" && rest.length) {
    const name = rest[0];
    rest = rest.slice(1);
    const project = rest.includes("--project");
    rest = rest.filter((a) => a !== "--project");
    let base, reset;
    [rest, reset] = profileTakeDefaults(rest);
    [rest, base] = profileTakeFlag(rest, "--from");
    const settings = base === null ? {} : profileWithout(profileRead(profileFind(base)[1]).settings, reset);
    let opts;
    try {
      [opts] = parseArgs(profileAsFlags(settings).concat(rest, ["in.md", "out.docx"]));
    } catch (e) {
      if (!(e instanceof BuildError)) throw e;
      throw new ProfileError(e.what);
    }
    const profile = { schema: PROFILE_SCHEMA, id: name, settings: profileSettingsOf(opts) };
    const p = profileTarget(name, project);
    const existed = profileIsFile(p);
    profileWrite(profile, p);
    return profileReplacing({ ok: true, name, where: project ? "project" : "home", path: p, replaced: existed,
      settings: profile.settings, sha256: profileDigest(profile.settings) });
  }
  if (command === "export" && rest.length >= 1 && rest.length <= 2) {
    const [, p] = profileFind(rest[0]);
    const data = profileRead(p);
    const name = path.basename(p, ".json");
    const out = rest.length === 2 ? rest[1] : name + ".json";
    profileWrite(data, out);
    return { ok: true, name, path: out, sha256: profileDigest(data.settings),
      share: "send this file; the other side runs `thai_docx profile import " + path.basename(out) + "`" };
  }
  if (command === "import" && rest.length) {
    const source = rest[0];
    rest = rest.slice(1);
    const project = rest.includes("--project");
    rest = rest.filter((a) => a !== "--project");
    let name;
    [rest, name] = profileTakeFlag(rest, "--name");
    if (rest.length) throw new ProfileError(PROFILE_USAGE);
    if (name !== null) profileCheckName(name); // a name the user typed is judged before the file is read
    const data = profileRead(source);
    if (name === null) name = String(data.id === undefined || data.id === null ? path.basename(source, ".json") : data.id);
    data.id = name; // profileTarget judges the name
    const p = profileTarget(name, project);
    const existed = profileIsFile(p);
    profileWrite(data, p);
    return profileReplacing({ ok: true, name, where: project ? "project" : "home", path: p, replaced: existed,
      settings: data.settings, sha256: profileDigest(data.settings) });
  }
  throw new ProfileError(PROFILE_USAGE);
}

// `--profile NAME` → the profile's flags before the rest, and what to report.
function profileExpand(argv) {
  const path = require("path");
  const [withoutDefaults, reset] = profileTakeDefaults(argv.slice());
  const [rest, name] = profileTakeFlag(withoutDefaults, "--profile");
  if (name === null) return [rest, null];
  const [where, p] = profileFind(name);
  const data = profileRead(p);
  const used = { name: path.basename(p, ".json"), where, path: p, sha256: profileDigest(data.settings) };
  return [profileAsFlags(profileWithout(data.settings, reset)).concat(rest), used];
}
