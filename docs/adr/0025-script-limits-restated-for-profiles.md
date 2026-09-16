# 0025 — Bundled scripts run with the agent's rights: the limits, restated for profiles

- Status: accepted
- Decided: 2026-09-16
- Supersedes: 0011

## Where it came from

0011 set eight limits, among them "writes only the output path it was given" and a list of
what may be read. Profiles (0024) need more: a file saved in a directory of the user's, a
file exported where the user says, a file imported from where they put it, and the home
directory found. The limits are restated here in full so there is one list, not a list and
an exception.

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

Limits 1–2 and 6 are enforced by tests over the JavaScript file and by review of the Python
package; 3–5 and 9 by tests with a planted violation and a clean input.

Left out on purpose: sandboxing the scripts, as in 0011 — that is the client's job; and a
setting or variable that moves the profile directories, which would make "where did this
come from" unanswerable from the report.

## Why

The reasons of 0011 stand: nothing here transmits data, and short limits make the scripts
reviewable. Profiles widen writing by exactly three files a user asked for by name, each
under a directory the user owns, and widen reading by files that must parse as settings
before they are used — a profile cannot reach a key, a document, or the network, because it
can hold nothing but the flags this skill already takes.

## Expires when

A client needs the scripts to write somewhere else, or profiles must be fetched from a
service rather than handed over as files.
