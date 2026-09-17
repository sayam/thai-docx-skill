// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// Grill mode is the user's word, not the agent's choice (ADR 0026, restated by 0029) — the
// port of thai_docx/grill.py. The agent hands the command the user's own message; the
// command, not the model, says which mode the build is in — and, in grill mode, which
// questions to ask, which choice each setting holds now, and what every choice means.

const GRILL_USAGE = "usage: thai_docx grill --said \"the user's own message, word for word\"";
const GRILL_PHRASE = "thai-docx grill";
const GRILL_MAX_CHARS = 20000;
// the words that may follow the phrase (ADR 0029): part → [English, Thai]
const GRILL_PARTS = { from: ["from", "จาก"], save_to: ["save to", "บันทึกเป็น"], only: ["only", "เฉพาะ"] };

class GrillError extends Error {
  constructor(what) {
    super(what);
    this.what = what;
  }
}

// ASCII case folded and `_` read as `-`: one character for one, so positions hold.
function grillFold(text) {
  let out = "";
  for (const ch of text) out += ch >= "A" && ch <= "Z" ? String.fromCharCode(ch.charCodeAt(0) + 32) : ch === "_" ? "-" : ch;
  return out;
}

function grillWords(message) {
  const out = [];
  let current = "";
  for (const ch of message) {
    if (/\s/.test(ch)) {
      if (current) out.push(current);
      current = "";
    } else {
      current += ch;
    }
  }
  if (current) out.push(current);
  return out;
}

// The message as the phrase is looked for in it: ASCII case folded, `_` read as `-`,
// every run of whitespace one space. ASCII only, so both implementations fold alike.
function grillPlain(message) {
  return grillFold(grillWords(message).join(" "));
}

// The language the questions are asked in: Thai when the user wrote any Thai.
function grillLanguage(message) {
  for (const ch of message) {
    if (ch >= "฀" && ch <= "๿") return "th";
  }
  return "en";
}

function grillMode(message) {
  return grillPlain(message).includes(GRILL_PHRASE) ? "grill" : "build";
}

// `from`, `save to` and `only`, read from the words directly after the phrase, as the user
// wrote them; the first word that is none of them ends the reading.
function grillParts(message) {
  const joined = grillWords(message).join(" ");
  let rest = joined.slice(grillPlain(message).indexOf(GRILL_PHRASE) + GRILL_PHRASE.length).split(" ");
  if (rest.length && rest[0] === "") rest = rest.slice(1);
  const found = {};
  let i = 0;
  while (i < rest.length) {
    const word = rest[i];
    let value = null;
    let part = null;
    for (const [name, [english, thai]] of Object.entries(GRILL_PARTS)) {
      const said = english.split(" ");
      const here = rest.slice(i, i + said.length).map(grillFold);
      if (here.length === said.length && here.every((w, k) => w === said[k])) {
        part = name;
        i += said.length;
        break;
      }
      if (word.startsWith(thai)) {
        part = name;
        i += 1;
        value = word.slice(thai.length) || null;
        break;
      }
    }
    if (part === null) break;
    if (Object.prototype.hasOwnProperty.call(found, part)) throw new GrillError("'" + GRILL_PARTS[part][0] + "' is given twice");
    if (value === null) {
      if (i >= rest.length) throw new GrillError("'" + GRILL_PARTS[part][0] + "' needs a word after it");
      value = rest[i];
      i += 1;
    }
    found[part] = value;
  }
  return found;
}

function grillSame(a, b) {
  if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((x, k) => grillSame(x, b[k]));
  return a === b;
}

// The flags that make a choice true against the settings in force: nothing for what already
// holds, `--default` for a setting going back to its default, its flag otherwise.
function grillArgs(chosen, now) {
  const changed = {};
  for (const [k, v] of Object.entries(chosen)) if (!grillSame(v, now[k])) changed[k] = v;
  const reset = Object.keys(changed).filter((k) => grillSame(changed[k], DEFAULTS[k]));
  const kept = {};
  for (const [k, v] of Object.entries(changed)) if (!reset.includes(k)) kept[k] = v;
  const out = profileAsFlags(kept);
  return reset.length ? out.concat(["--default", reset.join(",")]) : out;
}

function grillQuestions(now, lang, only, saveTo) {
  const k = lang === "th" ? 0 : 1;
  const out = [];
  QUESTIONS.forEach((q, index) => {
    if ((saveTo !== null && q.key === "save") || (only !== null && !only.includes(q.key))) return;
    const choices = [];
    let matched = false;
    q.choices.forEach((c, n) => {
      const choice = { letter: "abcd"[n], label: c.label[k] };
      if (c.set) {
        choice.current = Object.entries(c.set).every(([key, v]) => grillSame(v, now[key]));
        choice.args = grillArgs(c.set, now);
        matched = matched || choice.current;
      } else if (c.other) {
        choice.args = Object.entries(c.other).flatMap(([key, placeholder]) => [SETTINGS.find((s) => s.key === key).flag, placeholder]);
        choice.other = true;
      } else {
        choice.current = c.save === null;
        choice.args = [];
        choice.save = c.save;
      }
      choices.push(choice);
    });
    for (const choice of choices) if (choice.other) choice.current = !matched;
    out.push({ number: index + 1, key: q.key, text: q.text[k], choices });
  });
  return out;
}

function grillRun(argv) {
  if (argv.length !== 2 || argv[0] !== "--said") return { ok: false, error: GRILL_USAGE };
  let message = argv[1];
  if (message.length > GRILL_MAX_CHARS) message = message.slice(0, GRILL_MAX_CHARS);
  if (grillMode(message) !== "grill") {
    return { ok: true, mode: "build",
             next: "build at once with the announced defaults; ask nothing first" };
  }
  let found, start = null, now = { ...DEFAULTS }, saveTo = null, only = null;
  try {
    found = grillParts(message);
    if (Object.prototype.hasOwnProperty.call(found, "from")) {
      const [where, p] = profileFind(found.from);
      const data = profileRead(p);
      [now] = parseArgs(profileAsFlags(data.settings).concat(["in.md", "out.docx"]));
      start = { name: found.from, where, path: p, settings: data.settings };
    }
    if (Object.prototype.hasOwnProperty.call(found, "save_to")) {
      saveTo = found.save_to;
      if (profileIsPath(saveTo)) throw new GrillError("'save to' takes a profile name, not a path: " + saveTo);
      profileCheckName(saveTo);
    }
    if (Object.prototype.hasOwnProperty.call(found, "only")) {
      const keys = QUESTIONS.map((q) => q.key);
      only = [];
      for (let key of found.only.split(",")) {
        key = /^[0-9]{1,2}$/.test(key) && Number(key) >= 1 && Number(key) <= keys.length ? keys[Number(key) - 1] : grillFold(key);
        if (!keys.includes(key)) throw new GrillError("'" + key + "' is not a question; the questions are " + keys.join(", "));
        only.push(key);
      }
    }
  } catch (e) {
    if (e instanceof GrillError || e instanceof ProfileError) return { ok: false, error: e.what };
    throw e;
  }
  const lang = grillLanguage(message);
  const base = start ? "--from " + found.from + " " : "";
  let then;
  if (saveTo !== null) {
    then = "run `thai_docx profile save " + saveTo + " " + base + "ARGS`, then build with `--profile " + saveTo + "`";
  } else {
    then = "build with " + (start ? "`--profile " + found.from + "` and " : "") + "ARGS; for a save choice, first run" +
      " `thai_docx profile save NAME " + base + "ARGS` (add `--project` for the project) and build with `--profile NAME`";
  }
  return { ok: true, mode: "grill", language: lang, start, save_to: saveTo,
           questions: grillQuestions(now, lang, only, saveTo),
           next: "ask these questions as references/interview.md says, the current choice marked; an unanswered" +
             " question keeps its current choice. ARGS are the args of the chosen choices, in order, with the" +
             " user's value in place of a placeholder. Then " + then };
}
