# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""`thai_docx build IN.md OUT.docx [flags]` — Markdown to a .docx that passes
`thai_docx check`, with the content unchanged (ADR 0023) and the same bytes on
every run and in both implementations (ADR 0008).

The flow, and nothing else (ADR 0028): parse the Markdown, lay it out (layout.py), write
the package (writer.py, parts.py), pack it, check it (check.py), compare it with the
Markdown (fidelity.py), report. The output is written only when the package passes the
checker and the fidelity check; otherwise nothing is written and the JSON line says why.
Standard library only; reads the Markdown file and the images it names, writes one file
(ADR 0030).

Byte stability: zip entries are *stored*, not deflated — deflate output differs
between zlib builds. No clock, host name or user name enters any part. Escaping,
rounding and messages are spelled out here rather than borrowed from the
standard library, so the JavaScript port can say exactly the same (ADR 0015).
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import pathlib
import re
import stat

from . import check as check_mod
from . import markdown as md
from . import package
from .fidelity import docx_text, expected_text
from .parts import Package
from .settings import (  # noqa: F401  the names callers know the build's settings by
    DEFAULTS, PAPER, USAGE, BuildError, parse_args, settings_json, settings_warnings,
)

os_error = package.os_error  # the same words for the same errno in build and check


pack = package.pack  # stored entries, fixed metadata (ADR 0017)


def by_line(messages: list[str]) -> list[str]:
    """`line N: …` messages in line order; messages on one line keep theirs."""
    return sorted(messages, key=lambda m: int(m.split(":")[0].split()[1]))


# --- entry ---------------------------------------------------------------------


def build_text(text: str, opts: dict, read_image) -> tuple[dict, bytes | None]:
    """The whole build except reading the Markdown and writing the file: the part
    both implementations must agree on byte for byte."""
    result: dict = {}
    try:
        doc = md.parse(text)
        writer = Package(doc, opts, read_image)
        parts = writer.package()
    except md.Unsupported as exc:
        return {"error": exc.what, "line": exc.line}, None
    except BuildError as exc:
        return {"error": exc.what}, None
    data = pack(parts)
    report = check_mod.check(io.BytesIO(data))
    findings = list(report.findings)
    if not findings:
        expected, actual = expected_text(doc, opts), docx_text(dict(parts), len(doc.footnote_order))
        if expected != actual:
            # the runs may differ in length; the first difference, or where the shorter ends
            idx = next((i for i, (a, b) in enumerate(zip(expected, actual)) if a != b), min(len(expected), len(actual)))  # noqa: B905
            findings.append({"code": "fidelity", "part": "word/document.xml",
                             "message": "paragraph " + str(idx + 1) + " does not match the Markdown (" + str(len(expected))
                             + " paragraphs expected, " + str(len(actual)) + " written)"})
    items = writer.items
    present = {name for name, there in (
        ("tables", writer.counts["tables"] > 0),
        ("table captions", any(item.get("caption", {}).get("kind") == "table" for item in items)),
        ("figure captions", any(item.get("caption", {}).get("kind") == "figure" for item in items)),
        ("chapters or appendices", writer.has_chapters),
        ("numbered headings", any("number" in item for item in items)),
        ("appendices", "appendices" in writer.regions),
        ("appendix headings", any("number" in item and item["region"] == "appendices" for item in items)),
        ("chapter headings", any("number" in item and item["region"] == "chapters" for item in items)),
        ("front", "front" in writer.regions),
        ("numbers", writer.has_ordered_list or any("number" in item or "caption" in item for item in items)),
        ("toc comment", any(item["block"]["t"] == "directive" and item["block"]["name"] == "toc" for item in items)),
    ) if there}
    result.update(
        counts={**writer.counts, "runs": report.counts.get("runs", 0)},
        warnings=[{"code": "markdown", "message": m} for m in by_line(writer.style_warnings + writer.layout_warnings + doc.warnings)]
        + [{"code": "settings", "message": m} for m in settings_warnings(opts, present)] + report.warnings,
        findings=findings,
        sha256=hashlib.sha256(data).hexdigest(),
        bytes=len(data),
    )
    # `size` is not a defect in the builder: it says the images the user asked for do not fit
    # in a .docx. SKILL.md reads exit 1 as "a defect in this skill; do not retry", so this
    # leaves by the other door — `error`, exit 2, the door for input a user can change.
    too_big = next((f for f in findings if f["code"] == "size"), None)
    if too_big is not None:
        result["findings"] = [f for f in findings if f is not too_big]
        result["error"] = ("the document does not fit in a .docx — " + too_big["message"].replace("; refused", "")
                           + "; images are what makes a document this large, so use smaller ones")
        return result, None
    return result, (None if findings else data)


MAX_LINKS = 40


def _split_root(path: str) -> tuple[str, list[str]]:
    drive, rest = os.path.splitdrive(path)
    parts = re.split(r"[\\/]", rest) if os.sep == "\\" else rest.split("/")
    return drive + os.sep, [part for part in parts if part not in ("", ".")]


def _parent(path: str, root: str) -> str:
    cut = path.rstrip(os.sep).rfind(os.sep)
    return root if cut < len(root) else path[:cut]


def real_path(path: str) -> str:
    """The path as the file system walks it: each component's symbolic link
    followed, `..` taken from what is already resolved. A component that does not
    exist, or a link past the fortieth, stays as written. js/90-entry.js walks it
    the same way, so both implementations judge ADR 0030 §4 on the same file."""
    if not os.path.isabs(path):
        path = os.getcwd() + os.sep + path
    root, pending = _split_root(path)
    pending.reverse()
    resolved, links = root, 0
    while pending:
        part = pending.pop()
        if part == "..":
            resolved = _parent(resolved, root)
            continue
        candidate = resolved + part if resolved.endswith(os.sep) else resolved + os.sep + part
        try:
            is_link = stat.S_ISLNK(os.lstat(candidate).st_mode)
        except (OSError, ValueError):
            is_link = False
        if not is_link or links >= MAX_LINKS:
            resolved = candidate
            continue
        links += 1
        try:
            target = os.readlink(candidate)
        except (OSError, ValueError):
            resolved = candidate
            continue
        if os.path.isabs(target):
            root, parts = _split_root(target)
            resolved = root
        else:
            _, parts = _split_root(os.sep + target)
        pending.extend(reversed(parts))
    return resolved


def _inside(path: str, directory: str) -> bool:
    return path == directory or path.startswith(directory if directory.endswith(os.sep) else directory + os.sep)


def image_reader(md_dir: str, allow_dirs: list[str]):
    roots = [md_dir] + allow_dirs

    def read(src: str) -> tuple[str, bytes]:
        path = real_path(src if os.path.isabs(src) else md_dir + os.sep + src)
        if not any(_inside(path, root) for root in roots):
            raise BuildError("image '" + src + "' lies outside the Markdown file's directory; pass --allow-dir for its directory (ADR 0030 §4)")
        try:
            with open(path, "rb") as f:
                return path, f.read()
        except OSError as exc:
            raise BuildError("image '" + src + "': " + os_error(exc)) from None
        except ValueError:  # a path the OS cannot name, e.g. with a NUL
            raise BuildError("image '" + src + "': cannot be read") from None

    return read


def build(md_path, out_path, opts: dict, allow_dirs: list) -> dict:
    md_path, out_path = str(md_path), str(out_path)
    result: dict = {"ok": False, "file": out_path, "settings": settings_json(opts)}
    src = pathlib.Path(md_path)
    try:
        raw = src.read_bytes()
    except OSError as exc:
        result["error"] = "cannot read " + md_path + ": " + os_error(exc)
        return result
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        result["error"] = "cannot read " + md_path + ": not UTF-8 text"
        return result
    resolved = real_path(md_path)
    reader = image_reader(_parent(resolved, _split_root(resolved)[0]), [real_path(str(d)) for d in allow_dirs])
    outcome, data = build_text(text, opts, reader)
    result.update(outcome)
    if data is None:
        return result
    try:
        pathlib.Path(out_path).write_bytes(data)
    except OSError as exc:
        result["error"] = "cannot write " + out_path + ": " + os_error(exc)
        return result
    result["ok"] = True
    return result


def main(argv: list[str]) -> int:
    from . import profiles  # here: profiles reads this module's defaults and flags

    try:
        argv, used = profiles.expand(argv)
        opts, (md_path, out_path), allow = parse_args(argv)
    except (BuildError, profiles.ProfileError) as exc:
        print(json.dumps({"ok": False, "error": exc.what}, ensure_ascii=False))
        return 2
    result = build(md_path, out_path, opts, allow)
    if used is not None:
        result["profile"] = used
    print(json.dumps(result, ensure_ascii=False))
    if result["ok"]:
        return 0
    return 2 if "error" in result else 1
