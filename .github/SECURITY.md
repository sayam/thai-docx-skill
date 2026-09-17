# Security policy

## Reporting a vulnerability

Use GitHub's private vulnerability reporting for this repository:
**Security → Report a vulnerability** on
<https://github.com/sayam/thai-docx-skill/security/advisories/new>. It is the only
channel; no address is published here.

## What to expect

- Acknowledgement within **3 days** of the report.
- An assessment — confirmed, not reproducible, or out of scope — within **14 days**.
- A fix or a mitigation before disclosure, and coordinated disclosure no later than
  **90 days** after the report unless we agree otherwise with you.
- Credit in the release notes and the advisory, if you want it.

## Supported versions

The latest release receives fixes. Download a tagged release archive rather than
using `main`.

## Scope

- The skill: `skills/thai-docx/` — the Python package, the JavaScript file, and the
  instructions in `SKILL.md` an agent follows.
- This repository's workflows and release process.

What the scripts are designed never to do is written down in `docs/adr/0025`: no network;
no subprocesses, `eval` or code loaded from outside the skill; no environment variable read
beyond the platform's own lookup of the home directory; writing only the output path, the one profile file `profile save` or `import` names in the
profile directories, and the path `profile export` is given; reading images only from the
Markdown file's directory or one named with `--allow-dir`; profiles only as checked JSON of
at most 64 KiB; DOCTYPE and oversized packages refused. A way to make them do any of it is
in scope, and so is a profile file that makes a build do what its flags could not.

The bundled verifiable-gates tools under `tools/` are reported upstream:
<https://github.com/sayam/verifiable-gates/security>.
