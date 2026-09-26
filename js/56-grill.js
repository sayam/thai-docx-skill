// SPDX-FileCopyrightText: 2026 Sayam Sriphua
// SPDX-License-Identifier: MIT
// Grill mode is the user's word, not the agent's choice (ADR 0029, restating 0026) — the
// port of thai_docx/grill.py. The agent hands the command the user's own message; the
// command, not the model, says which mode the build is in — and, in grill mode, which
// questions to ask, which choice each setting holds now, and what every choice means.

const GRILL_USAGE = "usage: thai_docx grill --said \"the user's own message, word for word\"";
// grillFold reads `_` as `-`; the space is the third way ADR 0029 lets the two words of
// the name be joined, and it cannot be folded — a space is what separates the phrase's
// own words — so the pattern allows it there and nowhere else.
const GRILL_PHRASE = /thai[- ]docx grill/;
const GRILL_MAX_CHARS = 20000;
// the words that may follow the phrase (ADR 0029): part → [English, Thai]
const GRILL_PARTS = { from: ["from", "จาก"], save_to: ["save to", "บันทึกเป็น"], only: ["only", "เฉพาะ"] };

// What separates words, one list written out for both implementations: str.isspace() and the
// JavaScript \s disagreed on U+001C, U+0085 and U+FEFF, so one read `from test` and the other
// did not. The spaces a person types, and no others.
const GRILL_WHITESPACE = new Set([" ", "\t", "\n", "\r", "\f", "\v", "\u00a0", "\u3000"]);

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
    if (GRILL_WHITESPACE.has(ch)) {
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

// The language the questions are asked in: the one most of the user's words are in, the phrase
// aside — Thai on a tie. One Thai title in an English request is not a Thai request.
function grillLanguage(message) {
  let said = grillPlain(message);
  const at = GRILL_PHRASE.exec(said);
  if (at !== null) said = said.slice(0, at.index) + said.slice(at.index + at[0].length);
  let thai = 0, latin = 0;
  for (const word of said.split(" ")) {
    if ([...word].some((ch) => ch >= "฀" && ch <= "๿")) thai += 1;
    else if (/[a-z]/.test(word)) latin += 1;
  }
  return thai && thai >= latin ? "th" : "en";
}

function grillMode(message) {
  return GRILL_PHRASE.test(grillPlain(message)) ? "grill" : "build";
}

// The part whose words begin at rest[i], where its value begins, and the value when the Thai
// word carries it joined on (`บันทึกเป็นv2`).
function grillPartAt(rest, i) {
  for (const [name, [english, thai]] of Object.entries(GRILL_PARTS)) {
    const said = english.split(" ");
    const here = rest.slice(i, i + said.length).map(grillFold);
    if (here.length === said.length && here.every((w, k) => w === said[k])) return [name, i + said.length, null];
    if (rest[i].startsWith(thai)) return [name, i + 1, rest[i].slice(thai.length) || null];
  }
  return [null, i, null];
}

function grillAfterPhrase(message) {
  const joined = grillWords(message).join(" ");
  const here = GRILL_PHRASE.exec(grillPlain(message));
  const rest = joined.slice(here.index + here[0].length).split(" ");
  return rest.length && rest[0] === "" ? rest.slice(1) : rest;
}

// A `from`, `save to` or `only` later in the message than the reading went, with the word
// after it: said, it would be lost without a word, and the user answers nine questions
// believing the interview began from their profile.
function grillUnread(message) {
  const rest = grillAfterPhrase(message);
  const [, stop] = grillRead(rest);
  for (let j = stop; j < rest.length; j++) {
    const [part, valueAt, joined] = grillPartAt(rest, j);
    if (part !== null) return rest.slice(j, valueAt + (joined ? 0 : 1)).join(" ");
  }
  return null;
}

// `from`, `save to` and `only`, read from the words directly after the phrase, as the user
// wrote them; the first word that is none of them ends the reading.
function grillParts(message) {
  return grillRead(grillAfterPhrase(message))[0];
}

function grillRead(rest) {
  const found = {};
  let i = 0;
  while (i < rest.length) {
    let [part, at, value] = grillPartAt(rest, i);
    if (part === null) break;
    i = at;
    if (Object.prototype.hasOwnProperty.call(found, part)) throw new GrillError("'" + GRILL_PARTS[part][0] + "' is given twice");
    if (value === null) {
      if (i >= rest.length) throw new GrillError("'" + GRILL_PARTS[part][0] + "' needs a word after it");
      value = rest[i];
      i += 1;
    }
    found[part] = value;
  }
  return [found, i];
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

// `from` goes back to the agent inside a command it will run: a name is held to
// profileCheckName, and a path to the characters a path needs and no shell reads
const PATH_MARKS = "-_./\\:";

function grillCarried(source) {
  if (!profileIsPath(source)) {
    profileCheckName(source);
    return;
  }
  for (const c of source) {
    if (!PATH_MARKS.includes(c) && !/^[\p{L}\p{M}\p{N}]$/u.test(c)) {
      throw new GrillError("'from' is carried into a command, so a path there holds letters, digits and " +
        [...PATH_MARKS].join(" ") + " only: " + source);
    }
  }
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
  // characters, not units of storage: a character outside the BMP is two UTF-16 units
  // and one character, and Python counts it as one (ADR 0029, ADR 0008)
  const said = [...message];
  const cut = said.length - GRILL_MAX_CHARS;
  // the cap is a decision (ADR 0029), but a cap that says nothing is a trap: the phrase may be
  // in the part that was dropped, and the agent would read "build" as the answer
  if (cut > 0) message = said.slice(0, GRILL_MAX_CHARS).join("");
  if (grillMode(message) !== "grill") {
    const answer = { ok: true, mode: "build",
                     next: "build at once with the announced defaults; ask nothing first" };
    if (cut > 0) {
      answer.warnings = ["the message was read to its first " + GRILL_MAX_CHARS + " characters; "
        + cut + " were not read, and the phrase may be among them"];
    }
    return answer;
  }
  let found, start = null, now = { ...DEFAULTS }, saveTo = null, only = null;
  try {
    found = grillParts(message);
    if (Object.prototype.hasOwnProperty.call(found, "from")) {
      grillCarried(found.from);
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
  const answer = { ok: true, mode: "grill", language: lang, start, save_to: saveTo,
    questions: grillQuestions(now, lang, only, saveTo),
    next: "ask these questions as references/interview.md says, the current choice marked; an unanswered" +
      " question keeps its current choice. ARGS are the args of the chosen choices, in order, with the" +
      " user's value in place of a placeholder. Then " + then };
  const stray = grillUnread(message);
  if (stray !== null) {
    answer.warnings = ["'" + stray + "' was not read: from, save to and only are read only directly after" +
      " the phrase, so tell the user, and ask whether to start again with it there"];
  }
  return answer;
}
