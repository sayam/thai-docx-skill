# 2026-09-18 — security review of thai-docx 0.1.1

Scope: `skills/thai-docx/scripts/` — the Python package and the generated JavaScript file — at
`main` 76788f2 (v0.1.1), against the security requirements R1–R8 and the boundaries B1–B3 of
[`docs/assurance-case.md`](../assurance-case.md). Out of scope, as §1 of that page says: the AI
client and its sandbox, the model's behaviour, the office application that opens the result, and
the development tools under `tools/`.

**Who did what.** The maintainer, Sayam Sriphua, read every code path named below on 2026-09-18
and accepted this record. The assistant (Claude, in Claude Code) named the paths, wrote the input
script, ran it, and drafted the table from what it saw. Tools were aids, not the review: CodeQL
security-extended (no open alert on `main`, 2026-09-18), `ruff --select S`, OSV-Scanner through the
required `deps` job, and the suite (222 tests).

**Method.** For each requirement: read the code that enforces it in both implementations, run an
input that tries to get past it, and say whether anything did. The inputs are a script,
`.local/work/2026-09-18-security-review/probe.sh`, run in a temporary home; nothing in it touches a
real profile directory.

## Requirements

| req | code read | input tried | result | verdict |
|---|---|---|---|---|
| R1 no network, no process, no code from strings | `tests/test_script_limits.py` (the module allowlist it enforces), `build.py`, `profiles.py`, `js/55-profiles.js`, `js/90-entry.js` | both limit tests; a search for `environ`, `getenv`, `require(` outside the three Node-only modules | tests pass; the package imports only the sixteen standard modules of the allowlist; the bundle requires only `fs`, `os`, `path` | **holds** |
| R2 writes only named paths | `profiles.py: check_name, find, target, write`, `build.py: build`, `js/55-profiles.js` | `profile save ../../escape`, `profile save a/b`, `build in.md sub/dir/out.docx`, `profile export missing ../../outside.json` | every one refused; `check_name` rejects a name with `/`, `\`, `:`, `*`, `?`, quotes, `<`, `>`, `|`, a space, a leading dot, or more than 64 characters, and `target` builds the path from a directory the code owns plus that name | **holds.** `profile export` writes the path the user gave, which is what R2 allows; reading a profile by path is likewise allowed and bounded by R4 |
| R3 images from the Markdown's tree, PNG or JPEG by bytes | `build.py: real_path, _inside, image_reader`, `writer.py: _image_size` | `![](../secret.txt)`, a symlink inside the tree pointing out of it, a text file named `fake.png`, a real PNG | the first three refused ("lies outside the Markdown file's directory", "not a PNG or JPEG file (by its bytes, not its name)"), the real PNG built | **holds.** `real_path` walks each component itself, follows at most 40 links and takes `..` from what is already resolved, so a link cannot hop out and back in; a component that does not exist stays literal and the later `open` fails |
| R4 a profile is checked settings, at most 64 KiB | `profiles.py: read, validate`, `js/55-profiles.js: profileRead` | a 70 KB profile, an extra key `command`, non-JSON, `/dev/zero`, `font` set to `../../etc/passwd` | refused: "larger than 64 KiB", `unknown key "command"`, "not JSON", "larger than 64 KiB". The font value was accepted | **holds.** A setting is only ever written into XML — `attr(self.opts["font"])` in `parts.py` and `writer.py` — and no code opens a path built from a setting; a font name that looks like a path is a name that no font matches |
| R5 no environment but the home lookup | `profiles.py:122` (`os.path.expanduser("~")`), `js/55-profiles.js` (`os.homedir()`) | a search for `environ`/`getenv` over both implementations; `THAI_DOCX_HOME=… profile save` | no match at all; the variable changed nothing, the profile went to `$HOME/.thai-docx/profiles/` | **holds.** `expanduser` reads `HOME` through the platform call, which is the exception ADR 0030 §6 names; there is no setting or variable that moves the profile directories |
| R6 no identity, host name or clock in the output | `parts.py: core_xml` and the package writer, `package.py: pack` | build with `title`/`author` front matter, then read `docProps/core.xml`, the zip entry dates and `word/document.xml` | properties held exactly the two front-matter values; every entry is dated 1980-01-01; the OS user name appears nowhere | **holds.** `core_xml` writes only `dc:title` and `dc:creator`, and only when the front matter sets them |
| R7 hostile .docx | `check.py: _read_parts, _parse` (`MAX_PART`, `MAX_TOTAL`, `DOCTYPE`), `package.py: entries, read` (`MAX_FILE`) | a package declaring a DOCTYPE, one inflating to 40 MB, a truncated zip, a file that is not a zip; the DOCTYPE case through the JavaScript too | findings `doctype`, `size` ("would decompress to 41943051 bytes; refused"), `package` twice; the JavaScript gave the same finding | **holds.** Before any XML is parsed: the file is capped at 64 MiB, duplicate entry names are refused, the declared total and each part are capped, only stored and deflate entries are read, encryption is refused, inflation is bounded to the declared size + 1 and checked against it and the CRC, and DOCTYPE is refused |
| R8 hostile Markdown | `markdown.py: MAX_DEPTH` and the block parser, `parts.py`/`writer.py` escaping, `fidelity.py`, `build.py: build_text` | 300 nested quotes, text carrying `</w:t></w:r><w:hyperlink …>`, a 200,000-character line | nesting refused with its line ("blocks nested more than 100 deep are not supported"); the injection came out as text — no `<w:hyperlink` in the document; the long line built | **holds.** Every build checks its own output with the checker and compares the document's text with the Markdown's, and writes nothing when either finds something |

## Findings

None. No input in this review reached past a limit, and nothing read in the code paths above
allows one to.

Two things are worth naming without being findings:

1. `profile export` and `build` write where the user says. That is the design (R2), and it is the
   agent's arguments, not a file's content, that decide it — a profile cannot move a write.
2. `xml.etree.ElementTree` (expat) parses XML that came from someone else, after DOCTYPE, size and
   entry checks. `ruff --select S` reports this as S314, three times; the mitigation is those
   checks, not the parser.

## What this review did not do

- Read for reach the source does not spell — `getattr(os, "system")`, a module name built at run
  time — which ADR 0030 leaves to a reader. A search for `getattr` in the package found none.
- Exercise Windows path handling; `real_path` handles drive letters and `\`, and that half was
  read, not run.
- Fuzz the zip or XML readers beyond the generated-input campaigns already recorded
  (`docs/evidence/2026-09-15-javascript-matches-python.md`).

## Residual risks accepted

- A new weakness in expat would reach the checker, after the gates above.
- One maintainer reviews every change (GOVERNANCE.md, "Continuity"); the required checks stand
  where a second reviewer would.
- An agent can ignore SKILL.md and write its own document code; the skill cannot prevent that, and
  a prompt injection in a document an agent reads can misuse the commands without widening what
  they do.

## Next review

Before any release that changes a boundary (ADR 0030 or 0017), and at least by 2027-09-18.
