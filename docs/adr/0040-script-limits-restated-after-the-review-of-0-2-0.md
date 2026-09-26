# 0040 — Bundled scripts run with the agent's rights: the limits, restated with what the review of 0.2.0 found

- Status: accepted
- Decided: 2026-09-26
- Supersedes: 0030
- Amends: [0008](0008-two-zero-dependency-implementations-byte-identical.md) (the two implementations
  give the same bytes on the same Unicode version, not on any)

## Where it came from

Three readings of 0.2.0 on 2026-09-24 — a review of the code, two outside reports checked finding
by finding, and a review run to the project's own quality prompt — found places where a script
read, wrote or accepted more than 0030 allows, or more than 0030 thought to name
([record](../evidence/2026-09-24-three-readings-of-0.2.0.md)):

- `repair` and `build` would write over their own input: the same path, a symlink to it or a hard
  link (R3, R6).
- A FIFO given as an image or a profile hung the build; images and Markdown were read with no cap,
  and JavaScript `repair` read its input whole (D4, D-05).
- A link with any scheme was written into the document as an external target (B8).
- `&`, `<` or `"` in a caption label broke the field that carried it, and `repair --font` was
  written into the XML unescaped (B5, D-02).
- A profile name could hold shell metacharacters and a newline, and `grill` handed it back in a
  command for the agent to run; `--help` was saved as a name (B4, B6).
- A lone surrogate from the command line was a traceback in Python and a silent U+FFFD in
  JavaScript; bytes that are not UTF-8 were a traceback (B2, D-04).
- Five invisible characters were refused, the rest of their kind were not, and the noncharacters
  the parser said it refused were let through (B-03, C-11).
- `--allow-dir /` widened the image limit to the whole machine, and `--allow-dir ''` to the
  working directory (D-16).
- `repair` read comments and CDATA as markup, and wrote a file its own checker then refused (R1, R2).
- Emphasis and link labels are decided by the runtime's Unicode tables, so Python and Node on
  different Unicode versions gave different text for `_เน้น_🫩` (C-01).

The limits of 0030 did not move; what they cover did. They are restated in full.

## Decision

Every script under `skills/thai-docx/scripts/` obeys these limits. Items 1, 2, 6–8 and 10 are 0030's,
unchanged.

1. No network: no sockets, no HTTP clients, no `fetch`.
2. No subprocesses, no `eval` or `exec`, no package installs at run time, no code loaded from
   outside the skill. A profile is data and is never executed.
3. **Writes** only:
   - the output path the command was given, and **never the input it was given** — not the same
     path, not a symlink to it, not a hard link to it — in `build` and in `repair`;
   - on `profile save` and `profile import`, the one profile file that command names, in
     `~/.thai-docx/profiles/` or `./.thai-docx/profiles/`, those directories created if missing,
     only after refusing a name that is a path, and whole or not at all: an existing profile is
     replaced only by a file that was written completely;
   - on `profile export`, the one path the user gave.
4. **Reads** only regular files — judged on the file once opened, opened without waiting, so a FIFO
   cannot hang the open and nothing changes between the look and the read — each with a ceiling it
   checks by reading one byte past it rather than by asking the size first:
   - Markdown, at most 16 MiB;
   - images, at most 32 MiB each, only from the Markdown file's own directory tree or from a
     directory named with `--allow-dir`, and only when the magic bytes say PNG or JPEG.
     `--allow-dir` refuses the filesystem root and the empty string;
   - profiles, at most 64 KiB, only from the four places of 0024, only JSON, checked against
     0024's shape before anything uses them;
   - a .docx given to `check` or `repair`, within the checker's caps (item 9).
5. **Accepts as text** only Unicode scalar values. A lone surrogate, or bytes that are not UTF-8, in
   an argument, a profile or the Markdown is refused with exit 2 and the place it was found — in
   both implementations alike. An argument holding U+FFFD is refused too: Node puts U+FFFD where
   a byte was not UTF-8 and cannot tell it from one typed, so refusing both is the only answer
   the two implementations can give alike. Every format character (category `Cf`) and every noncharacter is
   refused the same way, from one list both implementations read. Newly refused by that: the soft
   hyphen (U+00AD), the bidi marks and controls, and the tag characters that spell the flags of
   England, Scotland and Wales. The zero-width joiner, and with it every emoji sequence built on
   it, was refused before. A byte-order mark at the start of the Markdown is still dropped
   before anything is read.
6. The home directory is found through the platform's own call — `os.path.expanduser("~")`,
   `os.homedir()` — and no other environment variable is read. In JavaScript this adds `os` to the
   modules the file may require (`fs`, `path`, `os`), and `process.env` stays forbidden.
7. Document properties hold only what front matter supplies — no OS user name, no host name, no
   clock. A profile adds nothing to them.
8. Output and logs carry counts, verdicts and settings, never document text.
9. Before parsing a .docx it did not write, the checker refuses XML carrying a DOCTYPE and caps the
   decompressed size. `repair` never writes a file its checker finds a fault in that the input did
   not have; a part whose finding lies inside a comment or CDATA is left as it came, and the finding
   stays under `remaining` with a warning saying why.
10. Fixtures, evidence and any profile shipped in this public repository use synthetic content only.
11. **Writes a value into markup only escaped, at the point it is written.** A value that reaches a
    field instruction — a table or figure label — refuses `"` and `\`, which the field syntax would
    read as its own. A font name given to `repair` is checked and escaped like one given to `build`.
12. **Links** are written only with the scheme `http`, `https` or `mailto`, in any case. A link with
    no scheme (`#top`, `other.docx`) is written as it is today. Any other scheme stops the build with
    exit 2 and the line.
13. **A profile name** is Unicode letters, digits, `-` and `_`, and nothing else. A name that shadows
    a profile the skill ships is saved with a warning naming what it hides.

Decided at the same time, and recorded here so that one record answers the review:

- **Same bytes on the same Unicode version** (amends 0008). `references/limits.md` states that
  output is byte-identical between the implementations when their runtimes share a Unicode
  version, and names the constructs that depend on it. Shipping the tables the parser needs as an
  asset both implementations read — which could move golden bytes — is weighed for 0.3.
- **A numbered list may start at `0`**, in both numbering modes (C-02). No golden starts at `0`, so
  no golden moves.
- **`พ.ศ.` cut into several runs** (B-05) waits for the five-application reading after 0.2.1 is
  tagged; any change is 0.3's, because it moves bytes.
- The guide's examples save profiles as `my-thesis`, not `thesis` (E-02, A-03).
- The three readings of 2026-09-24 are one evidence record, short, naming what was found and
  what was run, not who or what ran it.

Left out on purpose: sandboxing the scripts, as in 0011 and 0030 — that is the client's job; a
setting or variable that moves the profile directories; refusing a relative link or an anchor,
which would stop every hand-made table of contents; and changing the build's bytes in 0.2.1 — a
limit that needs a byte change waits for 0.3 and its own five-application reading.

## Why

0030's reason stands: a limit a person has to remember is a limit that drifts, so each is held by a
test with a planted violation and a clean input, in both implementations. What the review showed is
that a limit written as a list of *places* ("reads images from the tree") leaves out the *kind* of
thing read — a FIFO, a file of any size, the file being written — and a limit written as a list of
*characters* leaves out the rest of their class. So the limits now name the class: regular files
with a ceiling, Unicode scalar values, format characters as a category, schemes by allowlist.
A refusal with exit 2 and a line number is what the parser already does for HTML outside its list
(0022); links and text now answer the same way, so an agent reading the output learns one shape.

## Expires when

A client needs the scripts to write somewhere else, profiles must be fetched from a service rather
than handed over as files, a document needs a link scheme outside the three, or the implementations
carry their own Unicode tables (then 0008's amendment falls away).
