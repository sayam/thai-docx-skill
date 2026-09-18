# 2026-09-19 — what the installers give you, held by a test

`ROADMAP.md` has carried a promise since 0.1.0: *keep the release archive installable by the common
installers*. Both work, and were measured working on 2026-09-18 against v0.1.1, each in a throwaway
`HOME`. What was missing is the part that makes a promise worth anything — something that goes red
when it stops being true.

## What the two do, and where they differ

| | `gh skill install` | `npx skills add` |
|---|---|---|
| where the files come from | the **latest tagged release** | the default branch, **`main`** |
| an exact version | `--pin v0.1.1` | — |
| look before installing | `gh skill preview` | — |
| what lands | the repository subtree `skills/thai-docx/` — **not** the release archive | the same subtree |
| the files | the same set the archive holds | the same set |
| `SKILL.md` | **rewritten**: keys sorted, `metadata` flattened, quotes dropped, four provenance keys added (`github-repo`, `github-ref`, `github-path`, `github-tree-sha`) | copied as it is |

Neither is wrong, and the difference matters to a user: one gives the version this project tested
and wrote about, the other gives what has been merged since. Both guides now say so, with the
`--pin` and `gh skill preview` commands that make the choice deliberate.

## The two tests

**`test_the_archive_is_the_subtree_the_installers_copy`.** Neither installer reads the archive this
project builds; both copy the subtree. The archive and the subtree must therefore be the same
files — the test beside it already held them to the same *names*, and this one holds them to the
same **bytes**, file by file. It goes red the day packing starts transforming what it packs, which
would put a user who installed with `npx skills add` on different bytes from one who downloaded the
release.

**`test_the_front_matter_survives_being_written_again`.** An installed `SKILL.md` is not this
project's file: `gh skill install` writes the front matter again, sorting the keys, flattening
`metadata` and dropping the quotes around a scalar. So nothing the skill states may depend on the
order of those keys, or on `version` being written as a string. The test models that rewrite — a
twenty-line reader and writer in the test file itself, so it depends on nothing the project has not
declared — and holds the six values across it, plus two things that could go wrong quietly:

- **`version` must keep two dots.** `"0.1.1"` unquoted is still three numbers; a version of one dot
  would become a *number* the moment its quotes came off, and `1.10` would install as `1.1`.
- **No key inside `metadata` may share a name with a top-level key.** Flattening would keep one and
  drop the other without saying which.

Both were checked by breaking them: a `version` of `"1.1"` and a `name` inside `metadata` make the
test fail.

## What this does not do

It does not run either installer. They reach the network and they change as their own projects
change; a test that ran them would be measuring GitHub and npm, not this repository. The
measurement of what they actually do belongs to a dated record — 2026-09-18's, in
`.local/work/2026-09-18-v0.2-repair/PLAN.md` §9 — and to the smoke run the roadmap asks for after
each release. What the tests hold is the half of the promise this repository controls: **the files
they copy, and the front matter they rewrite.**

297 tests pass.
