# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Export every .docx in a directory as LibreOffice Writer draws it: a PDF, and a PNG per page.

    python3 tools/render_libreoffice.py DIR [--match '*-libreoffice_writer.docx'] [--dpi 150]

For the release reading (ADR 0012): the items of CHECKLIST.md marked `page` can be read on these
as well as in the application; the items marked `open` cannot. Writes DIR/render/<name>.pdf and
DIR/render/<name>-<page>.png (the PNGs only where `pdftoppm` is installed).

LibreOffice is `soffice` on the PATH, else the flatpak `org.libreoffice.LibreOffice`, else what
THAI_DOCX_SOFFICE names. It runs with a profile of its own under DIR/render/.profile, whose default
language for complex text layout is Thai: an English installation's is Hindi, which underlines
every Thai word (references/limits.md). A flatpak sees the home directory and not /tmp, so DIR
lies under home for one.

Role: generator (the renders). A reading is still a person's, in the application (ADR 0012).
"""

from __future__ import annotations

import os
import pathlib
import shlex
import shutil
import subprocess
import sys

FLATPAK_APP = "org.libreoffice.LibreOffice"
PROFILE = """<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" \
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<item oor:path="/org.openoffice.Office.Linguistic/General"><prop oor:name="DefaultLocale_CTL" oor:op="fuse">\
<value>th-TH</value></prop></item>
</oor:items>
"""


def soffice(env: dict[str, str] | None = None) -> list[str] | None:
    """The command that runs LibreOffice, or None when there is none."""
    env = os.environ if env is None else env
    if env.get("THAI_DOCX_SOFFICE"):
        return shlex.split(env["THAI_DOCX_SOFFICE"])
    for name in ("soffice", "libreoffice"):
        if shutil.which(name):
            return [name]
    if shutil.which("flatpak"):
        listed = subprocess.run(["flatpak", "info", FLATPAK_APP], capture_output=True)
        if listed.returncode == 0:
            return ["flatpak", "run", FLATPAK_APP]
    return None


def profile(render: pathlib.Path) -> pathlib.Path:
    """A LibreOffice profile of its own, reading complex text as Thai."""
    home = render / ".profile"
    (home / "user").mkdir(parents=True, exist_ok=True)
    (home / "user" / "registrymodifications.xcu").write_text(PROFILE, encoding="utf-8")
    return home


def render(directory: pathlib.Path, dpi: int = 150, match: str = "*.docx") -> list[pathlib.Path]:
    command = soffice()
    if command is None:
        raise SystemExit("LibreOffice was not found: install it, or name it in THAI_DOCX_SOFFICE")
    out = directory / "render"
    out.mkdir(exist_ok=True)
    home = profile(out)
    documents = sorted(directory.glob(match))
    subprocess.run([*command, "-env:UserInstallation=" + home.resolve().as_uri(), "--headless", "--convert-to", "pdf",
                    "--outdir", str(out.resolve()), *[str(d.resolve()) for d in documents]], check=True, capture_output=True)
    pdfs = [out / (d.stem + ".pdf") for d in documents]
    if shutil.which("pdftoppm"):
        for pdf in pdfs:
            subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(pdf), str(out / pdf.stem)], check=True)
    return pdfs


def main(argv: list[str]) -> int:
    dpi, match, rest = 150, "*.docx", list(argv)
    while len(rest) >= 3 and rest[-2] in ("--dpi", "--match"):
        if rest[-2] == "--dpi" and rest[-1].isdigit():
            dpi = int(rest[-1])
        elif rest[-2] == "--match":
            match = rest[-1]
        else:
            break
        rest = rest[:-2]
    if len(rest) != 1 or rest[0].startswith("-") or not pathlib.Path(rest[0]).is_dir():
        print(__doc__.split("\n\n")[1].strip())
        return 2
    for pdf in render(pathlib.Path(rest[0]), dpi, match):
        print(("ok   " if pdf.is_file() else "FAIL ") + str(pdf))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
