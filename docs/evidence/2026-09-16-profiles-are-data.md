# 2026-09-16 — profiles: settings as data, shared as a file

What this proves: a profile holds only settings a flag could set and is checked the way flags
are; a profile is found in the project, then the home, then the skill, and a path before all
three; saving and importing write inside the profile directories and nowhere else; and Python
and JavaScript answer every profile command with the same bytes (gate `profiles-are-data`,
ADR 0024, 0025).

Environment: Linux, Python 3.13.3, pytest 8.4.2, Node.js 24.15; the working tree of this
record, not yet committed. All profiles and documents in the tests are written for the
purpose (ADR 0025 §10). Every test runs with a `HOME` and a working directory of its own, so
no file outside the temporary tree is read or written.

## 1. The tests

`tests/test_profiles.py` (6 tests, Python only) and the profile part of
`tests/test_js_parity.py`: 21 `profile` commands and 5 builds with `--profile`, each run by
both implementations, output and written files compared byte for byte. 187 in the suite on
Python 3.13.

The settings a profile may hold are not a second list to keep: `test_a_profile_holds_only
_settings_a_flag_could_set` asserts `profiles.FLAGS` and `build.DEFAULTS` have the same keys
and that each flag it writes is one `build.USAGE` gives — a setting added to the build with
no profile entry fails there, before any document is built.

## 2. Defects planted in what the tests hold

Each row: one change to `profiles.py` or `js/55-profiles.js`, the JavaScript rebuilt by
`tools/bundle_js.py`, the named test file run, every red test read, then the file restored
and its sha256 compared with the original. Control run: 16 passed.

| planted defect | red |
|---|---|
| the rule that a name is not a path is dropped | not data the build takes |
| the name a save or import writes under is unchecked | not data the build takes |
| a flag typed after the profile loses to it | save, show, export, import, build |
| the written form stops sorting its keys | save, show, export, import, build |
| save writes the defaults too | only settings a flag could set; save from another; save … build |
| an unknown key in a profile is kept | not data the build takes |
| a setting outside a flag's range is taken | not data the build takes |
| the 64 KiB cap is lifted | not data the build takes |
| the home is searched before the project | the project before the home |
| JavaScript writes under a name it did not check | command line is the same |
| JavaScript reads `1.0` as an integer | command line is the same |
| JavaScript saves floats as integers | command line is the same |
| JavaScript writes the profile compactly | command line is the same |

All 13 red.

Two of these were green when first run and are here because the gap was real:

- **JavaScript saves floats as integers.** `--indent 1` is a float in Python and wrote `1.0`;
  the JavaScript wrote `1`, and no case saved a whole-numbered float. Fixed by adding
  `profile save whole --indent 1 --line-spacing 2 --margins 1,2,1,2 --size 16` to the parity
  cases — the file's bytes are part of what the run compares.
- **A name taken from the imported file was checked twice.** `import` without `--name` took
  the file's `"id"`, and both the import and `target()` refused a name that is a path, so no
  input could turn the import-level check red. The redundant check was removed in both
  implementations (repo lesson L-0003) and the sole remaining guard is now planted above and
  red, with `{"id": "../../escape"}` as the input:
  `tests/test_profiles.py` asserts the error and that no file appears beside the profile
  directory; the same file is imported in the parity cases, so both runtimes refuse it alike.

## 3. Not proved here

- That a profile shared between two machines carries what the sender meant: `export` writes
  the file it read, and `import` on another home is tested, but only within one tree.
- Rendering (ADR 0012): what a profile builds is a document like any other, checked by the
  goldens of `2026-09-16-options-structure-goldens-and-mutations.md`.
- Profiles the skill could ship in `skills/thai-docx/profiles/`: the search order is tested; the
  skill ships no profile of its own, so the directory does not exist.
