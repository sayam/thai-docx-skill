# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Profiles: a file of settings a user saves, shares and uses again (ADR 0024).

    thai_docx profile list
    thai_docx profile show NAME
    thai_docx profile save NAME [--from NAME [--default SETTING,…]] [--project] [build flags]
    thai_docx profile export NAME [OUT.json]
    thai_docx profile import FILE.json [--name NAME] [--project]
    thai_docx build IN.md OUT.docx --profile NAME|PATH [--default SETTING,…] [flags]

A profile holds settings and nothing else. Its values are checked by turning them into
the build's own flags, so a profile can hold nothing a command line could not, and a
flag typed after it wins (ADR 0024). Reads and writes stay inside the profile
directories of ADR 0030.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib

from . import build as b
from . import settings as st

SCHEMA = 1
DIR_NAME = ".thai-docx"
KEYS = ("schema", "id", "title", "description", "version", "source", "maintainer", "settings")
TEXT_KEYS = ("id", "version", "source", "maintainer")
MAX_TEXT = 200
MAX_BYTES = 64 * 1024  # a profile is settings; anything larger is not one (ADR 0030)
# setting → how it is written as a flag, from the registry (ADR 0028); "switch" flags say the value that turns them on
FLAGS: dict[str, tuple[str, str]] = {s["key"]: (s["kind"], s["flag"]) for s in st.SETTINGS}


class ProfileError(Exception):
    def __init__(self, what: str):
        super().__init__(what)
        self.what = what


def number(x) -> str:
    """A number as a flag takes it, the same text from both implementations."""
    return str(int(x)) if isinstance(x, bool) is False and float(x) == int(x) else repr(float(x))


def as_flags(settings: dict) -> list[str]:
    """The settings as the flags that set them, in one fixed order."""
    out: list[str] = []
    for key, (kind, flag) in FLAGS.items():
        if key not in settings:
            continue
        value = settings[key]
        if kind == "switch":
            if value is True:
                out.append(flag)
        elif kind == "off":
            if value is False:
                out.append(flag)
        elif kind == "list":
            out += [flag, ",".join(number(v) for v in value)]
        elif value is not None and value is not False:
            out += [flag, value if isinstance(value, str) else number(value)]
    return out


def settings_of(opts: dict) -> dict:
    """What a profile would hold for these options: every setting that is not the default."""
    out = {}
    for key in FLAGS:
        value = list(opts[key]) if key == "margins" else opts[key]
        if value != (list(b.DEFAULTS[key]) if key == "margins" else b.DEFAULTS[key]):
            out[key] = value
    return out


def canonical(profile: dict) -> str:
    """One written form: sorted keys, two spaces, UTF-8 as itself, one final newline."""
    return json.dumps(profile, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def digest(settings: dict) -> str:
    return hashlib.sha256(canonical(settings).encode("utf-8")).hexdigest()


def validate(data, where: str) -> dict:
    """A profile as ADR 0024 allows it, or ProfileError naming the file and the key."""
    if not isinstance(data, dict):
        raise ProfileError(where + ": a profile is a JSON object")
    if data.get("schema") != SCHEMA:
        raise ProfileError(where + ': "schema" must be ' + str(SCHEMA))
    for key in data:
        if key not in KEYS:
            raise ProfileError(where + ': unknown key "' + key + '"; a profile holds ' + ", ".join(KEYS))
    for key in TEXT_KEYS:
        if key in data and (not isinstance(data[key], str) or not data[key] or len(data[key]) > MAX_TEXT):
            raise ProfileError(where + ': "' + key + '" takes text of 1 to ' + str(MAX_TEXT) + " characters")
    for key in ("title", "description"):
        value = data.get(key, {})
        if not isinstance(value, dict) or any(k not in ("th", "en") for k in value) or any(
            not isinstance(v, str) or len(v) > MAX_TEXT for v in value.values()
        ):
            raise ProfileError(where + ': "' + key + '" takes th and/or en text of at most ' + str(MAX_TEXT) + " characters")
    settings = data.get("settings")
    if not isinstance(settings, dict):
        raise ProfileError(where + ': "settings" must be an object')
    for key in settings:
        if key not in FLAGS:
            raise ProfileError(where + ': unknown setting "' + key + '"; the settings are ' + ", ".join(FLAGS))
    try:
        b.parse_args(as_flags(settings) + ["in.md", "out.docx"])
    except b.BuildError as exc:
        raise ProfileError(where + ": " + exc.what) from None
    return data


def directories(skill: pathlib.Path | None = None) -> list[tuple[str, pathlib.Path]]:
    """Where a name is looked for, first match winning (ADR 0024, 0025)."""
    skill = skill or pathlib.Path(__file__).resolve().parent.parent.parent
    home = os.path.expanduser("~")
    return [
        ("project", pathlib.Path(".").resolve() / DIR_NAME / "profiles"),
        ("home", pathlib.Path(home) / DIR_NAME / "profiles"),
        ("skill", skill / "profiles"),
    ]


def is_path(name: str) -> bool:
    return "/" in name or "\\" in name or name.endswith(".json")


def check_name(name: str) -> str:
    """A name, never a path: what a profile is saved, imported or looked for under."""
    if not name or len(name) > 64 or any(c in name for c in '\\/:*?"<>| \t') or name.startswith("."):
        raise ProfileError("profile name '" + name + "' is not a name; use letters, digits, - or _")
    return name


def find(name: str) -> tuple[str, pathlib.Path]:
    if is_path(name):
        return "path", pathlib.Path(name)
    check_name(name)
    for where, directory in directories():
        path = directory / (name + ".json")
        if path.is_file():
            return where, path
    raise ProfileError("no profile named '" + name + "'; `thai_docx profile list` shows the ones there are")


def read(path: pathlib.Path) -> dict:
    # read at most one byte past the limit, rather than ask the size first: a file that
    # changes between the two, or has no size (/dev/zero), cannot get past it
    try:
        with path.open("rb") as f:
            raw = f.read(MAX_BYTES + 1)
    except OSError as exc:
        raise ProfileError("cannot read " + str(path) + ": " + b.os_error(exc)) from None
    if len(raw) > MAX_BYTES:
        raise ProfileError(str(path) + ": larger than 64 KiB; a profile is settings")
    try:
        text = raw.decode("utf-8")
    except ValueError:
        raise ProfileError(str(path) + ": not UTF-8 text") from None
    try:
        data = json.loads(text)
    except ValueError:
        # the two implementations read JSON with their own parsers; the fault is the file
        raise ProfileError(str(path) + ": not JSON") from None
    return validate(data, str(path))


def load(name: str) -> tuple[dict, str, pathlib.Path]:
    where, path = find(name)
    return read(path), where, path


def write(profile: dict, path: pathlib.Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical(profile), encoding="utf-8")
    except OSError as exc:
        raise ProfileError("cannot write " + str(path) + ": " + b.os_error(exc)) from None


def target(name: str, project: bool) -> pathlib.Path:
    check_name(name)
    where = "project" if project else "home"
    directory = dict(directories())[where]
    return directory / (name + ".json")


def listing() -> list[dict]:
    """Every profile found, in search order; a name found twice says which one a build uses."""
    out, seen = [], set()
    for where, directory in directories():
        for path in sorted(directory.glob("*.json")) if directory.is_dir() else []:
            name = path.stem
            try:
                data = read(path)
                title = data.get("title", {})
                row = {"name": name, "where": where, "path": str(path), "title": title, "settings": len(data["settings"])}
            except ProfileError as exc:
                row = {"name": name, "where": where, "path": str(path), "error": exc.what}
            row["used"] = name not in seen
            seen.add(name)
            out.append(row)
    return out


# --- the command ----------------------------------------------------------------------


USAGE = ("usage: thai_docx profile list | show NAME | save NAME [--from NAME [--default SETTING[,SETTING]]] [--project] [build flags] | "
         "export NAME [OUT.json] | import FILE.json [--name NAME] [--project]")


def _flag(argv: list[str], name: str) -> tuple[list[str], str | None]:
    """Take `--name VALUE` or `--name=VALUE` out of argv; None when it is not there."""
    out, value, i = [], None, 0
    while i < len(argv):
        head, eq, tail = argv[i].partition("=")
        if head == name:
            if eq:
                value = tail
            elif i + 1 < len(argv):
                value, i = argv[i + 1], i + 1
            else:
                raise ProfileError(name + " needs a value")
            i += 1
            continue
        out.append(argv[i])
        i += 1
    return out, value


def _defaults(argv: list[str]) -> tuple[list[str], list[str]]:
    """Take every `--default SETTING[,SETTING]` out of argv: the settings a profile gives
    back to their defaults before any flag applies (ADR 0029)."""
    out, keys, i = [], [], 0
    while i < len(argv):
        head, eq, tail = argv[i].partition("=")
        if head != "--default":
            out.append(argv[i])
            i += 1
            continue
        if not eq and i + 1 >= len(argv):
            raise ProfileError("--default needs a value")
        value = tail if eq else argv[i + 1]
        i += 1 if eq else 2
        for key in value.split(","):
            if key not in FLAGS:
                raise ProfileError('--default: unknown setting "' + key + '"; the settings are ' + ", ".join(FLAGS))
            keys.append(key)
    return out, keys


def main(argv: list[str]) -> int:
    try:
        result = run(argv)
    except ProfileError as exc:
        print(json.dumps({"ok": False, "error": exc.what}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


def _replacing(result: dict) -> dict:
    """A save or import that took the place of a profile says so where the user will hear it."""
    if result["replaced"]:
        result["warnings"] = ["replaced the profile " + result["name"] + " that was there before"]
    return result


def run(argv: list[str]) -> dict:
    if not argv:
        raise ProfileError(USAGE)
    command, rest = argv[0], argv[1:]
    if command == "list" and not rest:
        return {"ok": True, "profiles": listing()}
    if command == "show" and len(rest) == 1:
        data, where, path = load(rest[0])
        opts, _, _ = b.parse_args(as_flags(data["settings"]) + ["in.md", "out.docx"])
        return {"ok": True, "name": path.stem, "where": where, "path": str(path),
                "settings": data["settings"], "resolved": b.settings_json(opts), "sha256": digest(data["settings"])}
    if command == "save" and rest:
        name, rest = rest[0], rest[1:]
        rest, project = ([a for a in rest if a != "--project"], "--project" in rest)
        rest, reset = _defaults(rest)
        rest, base = _flag(rest, "--from")
        settings = {k: v for k, v in load(base)[0]["settings"].items() if k not in reset} if base else {}
        try:
            opts, _, _ = b.parse_args(as_flags(settings) + rest + ["in.md", "out.docx"])
        except b.BuildError as exc:
            raise ProfileError(exc.what) from None
        profile = {"schema": SCHEMA, "id": name, "settings": settings_of(opts)}
        path = target(name, project)
        existed = path.is_file()
        write(profile, path)
        return _replacing({"ok": True, "name": name, "where": "project" if project else "home", "path": str(path),
                           "replaced": existed, "settings": profile["settings"], "sha256": digest(profile["settings"])})
    if command == "export" and 1 <= len(rest) <= 2:
        data, _where, path = load(rest[0])
        out = pathlib.Path(rest[1]) if len(rest) == 2 else pathlib.Path(path.stem + ".json")
        write(data, out)
        return {"ok": True, "name": path.stem, "path": str(out), "sha256": digest(data["settings"]),
                "share": "send this file; the other side runs `thai_docx profile import " + out.name + "`"}
    if command == "import" and rest:
        source, rest = rest[0], rest[1:]
        rest, project = ([a for a in rest if a != "--project"], "--project" in rest)
        rest, name = _flag(rest, "--name")
        if rest:
            raise ProfileError(USAGE)
        if name is not None:
            check_name(name)  # a name the user typed is judged before the file is read
        data = read(pathlib.Path(source))
        name = name or str(data.get("id") or pathlib.Path(source).stem)  # target() judges it
        data["id"] = name
        path = target(name, project)
        existed = path.is_file()
        write(data, path)
        return _replacing({"ok": True, "name": name, "where": "project" if project else "home", "path": str(path),
                           "replaced": existed, "settings": data["settings"], "sha256": digest(data["settings"])})
    raise ProfileError(USAGE)


# --- the build's --profile ---------------------------------------------------------------


def expand(argv: list[str]) -> tuple[list[str], dict | None]:
    """`--profile NAME` → the profile's flags before the rest, less the settings `--default`
    names, and what to report."""
    rest, reset = _defaults(argv)
    rest, name = _flag(rest, "--profile")
    if name is None:
        return rest, None
    data, where, path = load(name)
    used = {"name": path.stem, "where": where, "path": str(path), "sha256": digest(data["settings"])}
    return as_flags({k: v for k, v in data["settings"].items() if k not in reset}) + rest, used
