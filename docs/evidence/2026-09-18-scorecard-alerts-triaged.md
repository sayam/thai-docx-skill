# 2026-09-18 — the Scorecard alerts on main: one fixed, five accepted with their reasons

What this proves: every alert OpenSSF Scorecard raised on `main` after its workflow was added was
read and answered — one by changing a setting, five by recording why the project accepts the score
— so the security tab shows what is actually open, not a backlog nobody has read.

Environment: Scorecard v5.5.0 through `ossf/scorecard-action` v2.4.4 (`.github/workflows/scorecard.yml`),
uploading SARIF to code scanning; the run of 2026-09-17 on `main`, score 5.5.

## The six alerts

| # | check | what it said | answer |
|---|---|---|---|
| 13 | Branch-Protection (5/10) | admin settings not applied to administrators; one approving review, not two; last push approval off | **partly fixed**: `require_last_push_approval` is now on in the `review` ruleset. The other two are the cost of one maintainer: the admin bypass is how the sole code owner merges at all, and a second approver does not exist (GOVERNANCE.md, "Continuity"). |
| 14 | Dependency-Update-Tool (0/10) | no update tool configuration found | **accepted, deliberate**: no bot opens version bumps here. The maintainer bumps by hand in a pull request that names the version and its hash, and the required `deps` job (OSV-Scanner) fails on a known vulnerability (CONTRIBUTING.md, "Dependencies"). |
| 15 | SAST (8/10) | 17 of the last 30 commits were checked by a SAST tool | **accepted, temporary**: CodeQL has run on every pull request and push to `main` since 2026-09-18; the window still holds commits from before it. It rises as new commits land. |
| 16 | Fuzzing (0/10) | no fuzzer integration found | **accepted**: no fuzzer Scorecard recognises. The parser is held to commonmark.js and cmark-gfm on 100,000 generated inputs and the two implementations to each other (`docs/evidence/2026-09-15-parser-held-to-references.md`), which Scorecard cannot see. Revisit if the project adopts `atheris`. |
| 17 | Code-Review (0/10) | 0 of 23 changesets were approved | **accepted**: one maintainer writes and merges every change (GOVERNANCE.md). The required checks — `scans`, `commits`, `tests`, `lint`, `deps` and CodeQL's results — stand where a second reviewer would. |
| 18 | Maintained (0/10) | the repository was created within the last 90 days | **accepted, structural**: created 2026-09-14; the check scores 0 until about 2026-12-13, whatever the project does. |

Each was dismissed on GitHub with its reason, so the code-scanning tab is empty for both tools:
CodeQL's twelve were closed on 2026-09-18 as well (`docs/evidence/2026-09-18-codeql-alerts-triaged.md`).

## What changed in the repository

- The `review` ruleset now requires approval of the last push. It does not change how the
  maintainer merges (the admin bypass), and it means that once a second reviewer exists, an
  approval no longer covers a push made after it.

## Not proved here

- That the score moves: the next scheduled Scorecard run will say. Branch-Protection cannot reach
  10 without a second maintainer, and Code-Review and Contributors cannot move at all until
  someone else takes part.
