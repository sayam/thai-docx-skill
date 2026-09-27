# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""The Python package stays within the script limits (ADR 0040 §1, §2 and §6), read from its
source rather than taken on review: it imports only a named list of standard modules, reaches
no process, environment or network through `os`, and builds no code from strings. The
JavaScript file is held to the same limits in `test_js_parity.py`.
"""

from __future__ import annotations

import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "thai-docx" / "scripts"

# what the package may import; anything else — socket, subprocess, urllib, http, ctypes,
# importlib, shutil, tempfile — is a change of design and needs a decision record first
ALLOWED = {
    "__future__", "errno", "hashlib", "io", "json", "math", "os", "pathlib", "re", "stat", "struct",
    "sys", "typing", "unicodedata", "xml.etree", "zlib", "thai_docx",
}
# the names of os a script could use to start a process, read the environment or leave the files
FORBIDDEN_OS = {
    "environ", "environb", "getenv", "getenvb", "putenv", "unsetenv", "system", "popen", "fork", "forkpty",
    "kill", "killpg", "startfile", "posix_spawn", "posix_spawnp",
}
FORBIDDEN_OS_PREFIXES = ("exec", "spawn")
FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__", "breakpoint"}


def _sources() -> list[pathlib.Path]:
    return sorted(SCRIPTS.rglob("*.py"))


def _findings(path: pathlib.Path, root: pathlib.Path = ROOT) -> list[str]:
    """Each breach in one file. `os` under any name it is imported as, and reached by name only:
    `getattr` with a name that is not written out, `vars()`, `__dict__` and `__builtins__` are each
    a way round a reading by name (the review of 0.3.0, F-07)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    names_os = {"os"} | {a.asname for n in ast.walk(tree) if isinstance(n, ast.Import)
                         for a in n.names if a.name == "os" and a.asname}
    for node in ast.walk(tree):
        where = f"{path.relative_to(root)}:{getattr(node, 'lineno', 0)}"
        if isinstance(node, ast.Import):
            found += [f"{where} imports {a.name}" for a in node.names if not _allowed(a.name)]
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and not _allowed(node.module or ""):
                found.append(f"{where} imports from {node.module}")
            if node.module == "os":
                found += [f"{where} imports os.{a.name}" for a in node.names if _forbidden_os(a.name)]
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in names_os:
            if _forbidden_os(node.attr) or node.attr == "__dict__":
                found.append(f"{where} uses os.{node.attr}")
        elif isinstance(node, ast.Name) and node.id == "__builtins__":
            found.append(f"{where} reaches __builtins__")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                found.append(f"{where} calls {node.func.id}")
            elif node.func.id == "vars":
                found.append(f"{where} calls vars")
            elif node.func.id in ("getattr", "setattr") and node.args and isinstance(node.args[0], ast.Name) \
                    and node.args[0].id in names_os:
                name = node.args[1] if len(node.args) > 1 else None
                if not (isinstance(name, ast.Constant) and isinstance(name.value, str)) or _forbidden_os(name.value):
                    found.append(f"{where} reaches os by getattr")
    return found


def _allowed(module: str) -> bool:
    return any(module == name or module.startswith(name + ".") for name in ALLOWED)


def _forbidden_os(name: str) -> bool:
    return name in FORBIDDEN_OS or name.startswith(FORBIDDEN_OS_PREFIXES)


def test_the_python_package_stays_within_the_script_limits():
    sources = _sources()
    assert len(sources) >= 14, "the package was not found"
    findings = [f for path in sources for f in _findings(path)]
    assert not findings, "\n".join(findings)


def test_the_limits_catch_what_they_name(tmp_path):
    """Each kind of breach, planted in a file of its own, is reported."""
    planted = {
        "net.py": "import socket\n",
        "http.py": "from urllib.request import urlopen\n",
        "proc.py": "import subprocess\n",
        "env.py": "import os\nhome = os.environ['HOME']\n",
        "env_from.py": "from os import getenv\n",
        "shell.py": "import os\nos.system('true')\n",
        "exec.py": "import os\nos.execv('/bin/true', ['true'])\n",
        "code.py": "eval('1')\n",
        "dynamic.py": "__import__('socket')\n",
        # past a name-by-name reading (the review of 0.3.0, F-07)
        "alias.py": "import os as _os\n_os.system('true')\n",
        "alias_env.py": "import os as o\nh = o.environ\n",
        "getattr.py": "import os\ngetattr(os, 'system')('true')\n",
        "getattr_dynamic.py": "import os\nname = 'sys' + 'tem'\ngetattr(os, name)('true')\n",
        "dict.py": "import os\nos.__dict__['system']('true')\n",
        "builtins.py": "getattr(__builtins__, 'eval')('1')\n",
        "vars.py": "import os\nvars(os)['system']('true')\n",
    }
    for name, text in planted.items():
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        assert _findings(path, tmp_path), name
    clean = tmp_path / "clean.py"
    clean.write_text("import os\nimport json\nfrom xml.etree import ElementTree\nprint(os.path.join('a', 'b'))\n"
                     "flags = getattr(os, 'O_NOFOLLOW', 0)\n", encoding="utf-8")
    assert _findings(clean, tmp_path) == []


def test_running_the_package_leaves_no_cache(tmp_path):
    """Every run wrote sixteen `.pyc` files into the installed skill's folder: a write ADR 0040
    does not name. One is left, the entry point's, which the interpreter writes before any line
    of the skill runs; `-B` leaves none. The test may start a process; the scripts may not."""
    import shutil
    import subprocess
    import sys
    copy = tmp_path / "thai-docx"
    shutil.copytree(SCRIPTS.parent, copy, ignore=shutil.ignore_patterns("__pycache__"))
    for flags, left in (([], ["__main__"]), (["-B"], [])):
        done = subprocess.run([sys.executable, *flags, str(copy / "scripts" / "thai_docx"), "check", str(tmp_path / "none.docx")],
                              capture_output=True, timeout=30)
        assert done.returncode == 2, done.stdout
        assert sorted(p.name.split(".")[0] for p in copy.rglob("*.pyc")) == left, flags
        shutil.rmtree(copy / "scripts" / "thai_docx" / "__pycache__", ignore_errors=True)
