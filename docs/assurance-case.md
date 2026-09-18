# Assurance case

Why thai-docx can be trusted to do what it says about security, and nothing more. It gives the
security requirements, the threat model and trust boundaries, and the argument — with the tests
that hold each claim — that secure design principles are applied and common weaknesses are
countered. The limits themselves are decided in
[ADR 0030](adr/0030-script-limits-read-by-tests-in-both-implementations.md) and
[ADR 0017](adr/0017-files-read-by-stated-rules.md); this page ties them together.

## 1. What is being assured

The scripts in `skills/thai-docx/scripts/` (Python package and JavaScript file) running on a user's
machine or in an AI client's sandbox, invoked by an agent or a person, with the rights of whoever
runs them. Out of scope: the AI client and its sandbox, the model's own behaviour, the office
application that opens the result, and the development tools under `tools/` (reported upstream).

## 2. Security requirements

| # | requirement | from |
|---|---|---|
| R1 | Make no network connection; start no process; evaluate no code from input or from outside the skill. | ADR 0030 §1–2 |
| R2 | Write only the output path given, the one profile file a `profile save`/`import` names in the profile directories, and the path given to `profile export`. | ADR 0030 §3 |
| R3 | Read images only from the Markdown file's tree or a directory named with `--allow-dir`, and only PNG or JPEG by magic bytes. | ADR 0030 §4 |
| R4 | Read a profile only as JSON of at most 64 KiB that passes the settings schema; a profile is data and can hold nothing a flag could not. | ADR 0030 §5, ADR 0024 |
| R5 | Read no environment variable except the platform's own lookup of the home directory. | ADR 0030 §6 |
| R6 | Put no user name, host name, clock or document text into document properties, output or logs. | ADR 0030 §7–8 |
| R7 | Survive hostile .docx input: refuse DOCTYPE, oversized or malformed packages without exhausting memory or following external references. | ADR 0030 §9, ADR 0017 |
| R8 | Survive hostile Markdown: bounded nesting, no silent drop of content, refusal named by line. | ADR 0022, ADR 0023 |

What users cannot expect: sandboxing (the client's job), confidentiality of documents from the
agent that writes them, or protection against an agent that ignores SKILL.md and writes its own code.

## 3. Threat model

```
 ┌──────────── untrusted ────────────┐      ┌────── trusted: the skill folder ──────┐
 │ Markdown (from a user or an agent)│      │ SKILL.md, references, scripts, assets │
 │ images the Markdown names         │ ───▶ │   parse · check · write · pack        │ ───▶ OUT.docx
 │ a .docx sent to `check`           │  B1  │                                       │  B2  profile file
 │ a profile file from someone else  │      └───────────────────────────────────────┘
 │ the user's message (grill --said) │                    ▲ B3: file system (read/write limits)
 └───────────────────────────────────┘
```

- **B1 — input boundary.** Every byte of Markdown, image, .docx, profile or message is untrusted.
- **B2 — output boundary.** What is written must not carry more than the input and settings asked
  for (no local files, no identity).
- **B3 — file-system boundary.** The scripts run with the invoker's rights; the limits above keep
  what they touch to named paths.

### Attack surface

| entry point | who controls it | reached through |
|---|---|---|
| Markdown text and front matter | a user, or content an agent copied from elsewhere | `build` |
| image paths and image bytes | the Markdown's author | `build` |
| a .docx file | anyone who sends one | `check` |
| a profile file | anyone who shares one | `build --profile PATH`, `profile import` |
| command-line flags and names | the agent or the user | every command |
| the user's message | the user, or text pasted into the chat | `grill --said` |
| instructions the agent follows | SKILL.md and references in the installed folder; a prompt injection hidden in Markdown the agent reads | the client |
| the code users run | pull requests, CI actions, test tools, the release workflow | the repository and the release archive |

A prompt injection in a document the agent reads can make the agent misuse the commands, but not
widen what the commands do: the limits of §2 hold whatever the arguments.

| threat | entry | example | countered by |
|---|---|---|---|
| T1 local file disclosure | Markdown image path | `![](~/.ssh/id_rsa)`, `![](link/../../etc/passwd)`, a symlink out of the tree | R3: resolved path must stay under the allowed roots; magic bytes; the same resolution rule in both runtimes (ADR 0017) |
| T2 XML external entity / billion laughs | .docx to `check` | `<!DOCTYPE … <!ENTITY …>` | R7: DOCTYPE refused before parsing |
| T3 zip bomb, zip tricks | .docx to `check` | huge declared sizes, entries inflating past their size, overlapping records, zip64 | R7: part and total size caps (32 MiB / 64 MiB), stated zip reading rules |
| T4 resource exhaustion by nesting | Markdown | 10,000 nested quotes or lists | R8: depth limit 100, refused with its line |
| T5 arbitrary write / path traversal | profile name, output path | `profile save ../../.bashrc` | R2: a profile name is a name, never a path; writes only named files |
| T6 code or setting injection | profile file | extra keys, huge file, non-JSON | R4: size cap, schema of the build's own flags |
| T7 XML injection into the output | Markdown text, front matter | `</w:t><w:hyperlink…>` in text | escaping of every text and attribute; the checker and fidelity check refuse a package whose text differs |
| T8 data exfiltration | any | network call, telemetry | R1: no network code; test over the JavaScript file's modules |
| T9 identity leak | output | author = OS user | R6: properties only from front matter |
| T10 supply-chain tampering of the release | release archive | swapped zip on the release page | build in CI from the tag, provenance attestation verified before attaching; no run-time dependencies |

## 4. Secure design principles applied

| principle | where |
|---|---|
| Economy of mechanism | standard library only; one command per job; short readers of zip and XML by stated rules |
| Fail-safe defaults | refuse and write nothing on any doubt: unknown Markdown, bad flag values, failed self-check |
| Complete mediation | every read and write path goes through the checks of R2–R4 at the point of use |
| Open design | all code, decisions, threats and evidence are public |
| Separation of privilege | changes to main need the required checks for everyone; code owners guard workflows and gates |
| Least privilege | no network, no subprocess, bounded file access; CI workflows run with `contents: read` unless a job needs more |
| Least common mechanism | no shared state between runs; no caches, no daemons |
| Psychological acceptability | defaults need no questions; refusals name the line and the reason |
| Limited attack surface | four commands, JSON out, no plugins, no configuration from the environment |
| Input validation with allowlists | Markdown dialect and HTML tag allowlist, flag value sets and ranges, image types by magic bytes, profile schema |

## 5. Security assessment

The most likely and most harmful problems, in order, as assessed on 2026-09-17:

1. **A local file embedded in a document that is then sent on** (T1) — likely, because agents write
   image paths; harmful, because the document leaves the machine. Countered by R3, tested.
2. **A crafted .docx sent to `check`** (T2, T3) — likely wherever users check files from others;
   denial of service or entity expansion. Countered by R7, tested.
3. **A tampered release archive** (T10) — rare, severe. Countered by building from the tag in CI and
   attesting; users can verify (SECURITY.md).
4. **A malicious profile** (T5, T6) — shared files are the design; limited to settings. Countered by
   R2 and R4, tested.
5. **Deep or huge Markdown** (T4) — resource exhaustion only. Countered by R8, tested.
6. **A compromised development dependency or action** — cannot reach users' machines (no run-time
   dependencies), but could alter a release. Countered by hash- and SHA-pinning, code owners on
   workflows, the dependency check (`deps`, OSV-Scanner) required before merge, and CodeQL's
   security-extended queries, whose alerts of medium severity or higher block a merge.

## 6. Common weaknesses countered, with evidence

| CWE | weakness | held by |
|---|---|---|
| CWE-611 | XML external entities | `tests/test_check.py::test_doctype_is_refused_before_parsing` |
| CWE-409 | decompression bomb | `tests/test_check.py::test_oversized_package_is_refused`; zip campaigns in `docs/evidence/2026-09-15-javascript-matches-python.md` |
| CWE-22, CWE-59 | path traversal, link following | `tests/test_build.py::test_image_outside_the_markdown_directory_is_refused_unless_allowed`, `::test_remote_and_non_image_files_are_refused`; ADR 0017 image paths |
| CWE-674, CWE-400 | uncontrolled recursion, resource exhaustion | `tests/test_markdown.py::test_nesting_past_the_limit_stops_with_its_line`; `tests/test_js_parity.py::test_deep_nesting_is_read_or_refused_the_same_way` |
| CWE-91 | XML injection | `tests/test_build.py::test_special_characters_are_escaped`; the fidelity check on every build |
| CWE-73, CWE-20 | external control of file name, improper input validation | `tests/test_profiles.py::test_a_profile_is_refused_when_it_is_not_data_the_build_takes` and the profile tests |
| CWE-94, CWE-829 | code injection, inclusion from untrusted sphere | `tests/test_js_parity.py::test_bundle_stays_within_the_script_limits` (no network, subprocess or eval modules in the JavaScript file); `tests/test_script_limits.py::test_the_python_package_stays_within_the_script_limits` (the same, read from the Python source) |
| CWE-200 | exposure of information | `tests/test_build.py::test_docprops_carry_only_front_matter` |

Each gate that holds these tests records the planted defects it was seen to catch in `docs/evidence/`.

## 7. Residual risks

- Limits 1, 2 and 6 are read from the source in both implementations (ADR 0030); reach the source does not
  spell (`getattr(os, "system")`, a module name built at run time) is still left to review.
- `xml.etree.ElementTree` (expat) is used on untrusted input; DOCTYPE is refused first, and size is
  capped, but a new expat weakness would reach the checker.
- The agent may ignore SKILL.md and write its own document code; the skill cannot prevent that.
- One maintainer reviews all changes (see GOVERNANCE.md).

## 8. Keeping this current

A change to ADR 0030 or 0017, a new input type, or a new command updates this page in the same pull
request, and the security review (`docs/evidence/*-security-review.md`) is repeated at least once a
year or before a release that changes a boundary. The last one was
[2026-09-18](evidence/2026-09-18-security-review.md), on 0.1.1: every requirement held, no finding.
