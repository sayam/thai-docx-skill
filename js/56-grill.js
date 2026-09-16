// Grill mode is the user's word, not the agent's choice (ADR 0026) — the port of
// thai_docx/grill.py. The agent hands the command the user's own message; the command,
// not the model, says which mode the build is in.

const GRILL_USAGE = "usage: thai_docx grill --said \"the user's own message, word for word\"";
const GRILL_PHRASE = "thai-docx grill";
const GRILL_MAX_CHARS = 20000;

// The message as the phrase is looked for in it: ASCII case folded, `_` read as `-`,
// every run of whitespace one space. ASCII only, so both implementations fold alike.
function grillPlain(message) {
  const out = [];
  let space = false;
  for (const ch of message) {
    if (/\s/.test(ch)) {
      space = out.length !== 0;
      continue;
    }
    if (space) out.push(" ");
    space = false;
    let c = ch;
    if (c >= "A" && c <= "Z") c = String.fromCharCode(c.charCodeAt(0) + 32);
    out.push(c === "_" ? "-" : c);
  }
  return out.join("");
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

function grillRun(argv) {
  if (argv.length !== 2 || argv[0] !== "--said") return { ok: false, error: GRILL_USAGE };
  let message = argv[1];
  if (message.length > GRILL_MAX_CHARS) message = message.slice(0, GRILL_MAX_CHARS);
  if (grillMode(message) === "grill") {
    return { ok: true, mode: "grill", language: grillLanguage(message),
             questions: "references/interview.md",
             next: "ask the nine questions exactly as references/interview.md gives them, then build" };
  }
  return { ok: true, mode: "build",
           next: "build at once with the announced defaults; ask nothing first" };
}
