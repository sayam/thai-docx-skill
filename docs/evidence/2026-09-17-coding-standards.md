# 2026-09-17 — coding standards: PEP 8 through ruff, ESLint's recommended rules, and what each catches

What this proves: the `lint` job holds the Python to PEP 8 (ruff's pycodestyle errors and
warnings, lines of at most 150 characters) with pyflakes and bugbear, and the JavaScript parts
in `js/` to ESLint's recommended rules; the 122 Python and 19 JavaScript findings were fixed
without changing what the skill writes; and both linters fail on a planted defect.

Environment: Linux, Python 3.13, ruff from `requirements/dev.txt`, Node.js 24, ESLint 10.10.0 and
`@eslint/js` 10.0.1 from `tests/js/package-lock.json` (`npm ci --ignore-scripts`). Base: `main`
134ec32.

## Why 150 columns

The 8,339 non-blank lines of the project's own Python, measured before the change:

| limit | lines too long | lines that fit |
|---|---|---|
| 79 (PEP 8) | 3,928 | 76.6% |
| 99 | 863 | 89.5% |
| 120 | 361 | |
| 150 | 84 | 99.0% |

No width near 100 is a natural break; 150 is where 99% of the code already stood. Kept by the
maintainer on 2026-09-17.

## Nothing changed

- `python3 -m pytest -q tests`: 217 passed, the goldens byte for byte.
- `python3 tools/bundle_js.py` regenerates exactly the patched `scripts/thai_docx.js`.
- `python3 tools/gates_doctor.py`: pass.

## Planted defects

| planted | tool | result |
|---|---|---|
| an unused function reading an undefined name, appended to `js/53-build.js` | ESLint | exit 1: `no-unused-vars`, `no-undef` |
| `const plantedFs = require("fs")` in `js/52-fidelity.js`, a part that may not reach Node | ESLint | exit 1: `no-undef` on `require`, `no-unused-vars` |
| `l = 1` and a 172-column line in `fidelity.py` | ruff | exit 1: E741, E501 |

Each was reverted; both linters pass again.
