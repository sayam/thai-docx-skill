# 0030 — Bundled scripts run with the agent's rights: the limits, restated with both implementations read by tests

- Status: accepted
- Decided: 2026-09-18
- Supersedes: 0025

## Where it came from

0025 restated the limits for profiles and said that limits 1, 2 and 6 were "enforced by tests
over the JavaScript file and by review of the Python package". Review is not a gate: nothing went
red when the Python reached somewhere new. On 2026-09-18 `tests/test_script_limits.py` began
reading the Python package the way `test_bundle_stays_within_the_script_limits` reads the
JavaScript file, and CodeQL's security-extended queries began running on every change. The limits
themselves did not move, so they are restated here in full, with how each is held brought up to
date.

## Decision


Every script under `skills/thai-docx/scripts/` obeys these limits:

1. No network: no sockets, no HTTP clients, no `fetch`.
2. No subprocesses, no `eval` or `exec`, no package installs at run time, no code loaded
   from outside the skill. A profile is data and is never executed.
3. **Writes** only:
   - the output path the build was given;
   - on `profile save` and `profile import`, the one profile file that command names, in
     `~/.thai-docx/profiles/` or `./.thai-docx/profiles/`, those directories created if
     missing, and only after refusing a name that is a path;
   - on `profile export`, the one path the user gave.
4. **Reads images** only from the Markdown file's own directory tree, or from a directory
   the user names with `--allow-dir`, and only when the file's magic bytes say PNG or JPEG.
   `![](~/.ssh/id_rsa)` must not embed a key into a document that is then sent on.
5. **Reads profiles** only from the four places of 0024, only files that are JSON, at most
   64 KiB, checked against 0024's shape before anything uses them.
6. The home directory is found through the platform's own call — `os.path.expanduser("~")`,
   `os.homedir()` — and no other environment variable is read; there is none to relocate
   profiles. In JavaScript this adds `os` to the modules the file may require (`fs`,
   `path`, `os`), and `process.env` stays forbidden.
7. Document properties hold only what front matter supplies — no OS user name, no host
   name, no clock. A profile adds nothing to them.
8. Output and logs carry counts, verdicts and settings, never document text.
9. Before parsing a .docx it did not write, the checker refuses XML carrying a DOCTYPE and
   caps the decompressed size.
10. Fixtures, evidence and any profile shipped in this public repository use synthetic
    content only.

Limits 1, 2 and 6 are read from the source of **both** implementations by tests — `ast` over every
module of the Python package (gate `python-stays-within-the-script-limits`) and a read of the
JavaScript bundle (gate `javascript-matches-python`) — and what the source does not spell, such as
`getattr(os, "system")` or a module name built at run time, is still left to review. Limits 3–5 and
9 are held by tests with a planted violation and a clean input, and a bound is preferred to a check:
a profile is read one byte past its 64 KiB limit rather than measured first (`docs/evidence/2026-09-18-codeql-alerts-triaged.md`).

Left out on purpose: sandboxing the scripts, as in 0011 — that is the client's job; and a
setting or variable that moves the profile directories, which would make "where did this
come from" unanswerable from the report.

## Why

The reasons of 0011 and 0025 stand: nothing here transmits data, and short limits make the scripts
reviewable. What changed is who checks: a limit a person has to remember is a limit that drifts, and
the same fault — asking a file's size and then reading it whole — sat in both implementations until
a tool read the code. A test that names the modules a script may import also tells a contributor
what the answer is before review does.

## Expires when

A client needs the scripts to write somewhere else, profiles must be fetched from a service rather
than handed over as files, or the limits themselves change.
