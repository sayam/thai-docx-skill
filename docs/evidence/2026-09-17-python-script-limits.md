# 2026-09-17 — the Python package held to the script limits by a test

What this proves: limits 1, 2 and 6 of ADR 0025 — no network, no subprocesses, no code built
from strings, no environment read — which the record left to review for the Python package, are
now read from its source by `tests/test_script_limits.py`, as `test_bundle_stays_within_the_script_limits`
already reads them from the JavaScript file; and the test reports each kind of breach.

Environment: Linux, Python 3.13, pytest from `requirements/dev.txt`. Base: `main` after the
coding-standards change.

## What the test reads

Every `*.py` under `skills/thai-docx/scripts/` (15 files), parsed with `ast`:

- **Imports** only from: `__future__`, `errno`, `hashlib`, `io`, `json`, `math`, `os`, `pathlib`,
  `re`, `stat`, `struct`, `sys`, `typing`, `unicodedata`, `xml.etree`, `zlib`, and the package
  itself. That is exactly what the package imported on 2026-09-17.
- **`os`**: none of `environ`, `getenv`, `putenv`, `unsetenv`, `system`, `popen`, `fork`, `kill`,
  `startfile`, `posix_spawn`, or any `exec*` / `spawn*`, whether used as `os.name` or imported
  from `os`.
- **Calls**: none of `eval`, `exec`, `compile`, `__import__`, `breakpoint`.

## Planted breaches

`test_the_limits_catch_what_they_name` writes each into a file of its own and requires a finding;
a clean file (`os.path.join`, `json`, `xml.etree`) must give none.

| planted | reported as |
|---|---|
| `import socket` | imports socket |
| `from urllib.request import urlopen` | imports from urllib.request |
| `import subprocess` | imports subprocess |
| `os.environ['HOME']` | uses os.environ |
| `from os import getenv` | imports os.getenv |
| `os.system('true')` | uses os.system |
| `os.execv(...)` | uses os.execv |
| `eval('1')` | calls eval |
| `__import__('socket')` | calls __import__ |

The same breaches planted in the real package (`import socket` in `fidelity.py`, `os.getenv` in
`profiles.py`) turned `test_the_python_package_stays_within_the_script_limits` red; reverted, green.

## Not proved here

- Indirect reach the source does not spell: `getattr(os, "system")`, `builtins.eval`, a module
  name built at run time. A reviewer still reads for those (ADR 0025).
- `open()` is allowed: where the package writes is limit 3, held by the tests of the build and
  the profiles.
