# 0011 — Bundled scripts run with the agent's rights: eight limits

- Status: accepted
- Decided: 2026-09-15

## Where it came from

The maintainer asked whether bundling scripts with a skill breaks any rule, and
whether it conflicts with security practice, Thailand's PDPA or the GDPR. A
script in a skill runs on the user's machine with whatever rights the agent
has, over documents that may hold personal data.

## Decision

Every script under `skills/thai-docx/scripts/` obeys eight limits:

1. No network: no sockets, no HTTP clients, no `fetch`.
2. No subprocesses, no `eval` or `exec`, no package installs at run time.
3. Writes only the output path it was given.
4. Reads images only from the Markdown file's own directory tree, or from a
   directory the user names with `--allow-dir`, and only when the file's magic
   bytes say PNG or JPEG. `![](~/.ssh/id_rsa)` must not embed a key into a
   document that is then sent on.
5. Document properties hold only what front matter supplies — no OS user name,
   no host name, no clock.
6. Output and logs carry counts and verdicts, never document text.
7. Before parsing a .docx it did not write, the checker refuses XML carrying a
   DOCTYPE and caps the decompressed size.
8. Fixtures and evidence screenshots in this public repository use synthetic
   content only.

Limits 1–3 and 5 are enforced by scans; 4 and 7 by tests with a planted
violation and a clean input.

Left out on purpose: sandboxing the scripts. That is the client's job; these
limits make the scripts short to review and keep them to what a user expects.

## Why

The specification allows bundled scripts [S3], and nothing here transmits data,
so the scripts are no channel for personal data to leave the machine. What
remains is minimisation — handle and emit only what the task needs — a
principle in both the GDPR [S19] and the PDPA [S20]. This is an engineering
reading of that principle, not legal advice. Directories list skills whose code
nobody has reviewed [S5]; a script that visibly cannot reach the network or
other files is one a careful user can accept. Limit 5 also serves 0008: clocks
and host names are exactly what make two builds differ.

## Expires when

A feature needs one of the forbidden capabilities. The limit then changes
through a new record, with the risk written down.
