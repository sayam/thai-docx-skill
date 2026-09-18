# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""`thai_docx check FILE.docx` — report, by number, every cause in ADR 0004 the file
still carries, plus the two things ADR 0005 and 0011 make the checker refuse.

Findings, each with a `code`:

    1        compatibilityMode is not declared exactly once as 15
    2        a run with text lacks <w:cs/> or w:lang/@w:bidi="th-TH"
    3        <w:noProof/> appears somewhere
    4        two adjacent runs carry identical formatting (a word may be split)
    5        a complex-script twin is missing (cs font, szCs, bCs, iCs), or a bullet
             level uses the Symbol font
    order    a property stands in the wrong place for the schema (Word ignores it)
    invisible  a zero-width character is in the text
    doctype  an XML part declares a DOCTYPE — refused before parsing (ADR 0030 §9)
    size     the package would decompress past the cap — refused (ADR 0030 §9)
    package  not a WordprocessingML package

Warnings never fail the check; today there is one: a complex-script font the
checker does not know to carry Thai glyphs (ADR 0026).

Role: decider — exit 0 when there are no findings, 1 when there are, 2 when the
file could not be examined at all. The output is one JSON line, and never carries
the document's text (ADR 0030 §8).
"""

from __future__ import annotations

import json
import pathlib
import re
from xml.etree import ElementTree as ET

from . import package
from .ooxml import (
    INVISIBLE,
    PPR_ORDER,
    RPR_ORDER,
    SETTINGS_ORDER,
    THAI_FONTS,
    is_thai,
    local,
    w,
)

MAX_PART = 32 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
COMPAT_URI = "http://schemas.microsoft.com/office/word"
TEXT_PARTS = re.compile(r"word/(document|comments|footnotes|endnotes|header[0-9]*|footer[0-9]*)\.xml")  # fullmatch
DOCTYPE = re.compile(rb"<!DOCTYPE", re.IGNORECASE)
DECLARED_ENCODING = re.compile("\ufeff?<\\?xml[^>]*?[ \\t\\r\\n]encoding[ \\t\\r\\n]*=[ \\t\\r\\n]*[\"']([^\"']*)[\"']")


class Report:
    def __init__(self, path: str):
        self.path = path
        self.findings: list[dict] = []
        self.warnings: list[dict] = []
        self.counts: dict[str, int] = {}

    def find(self, code: str, part: str, message: str, **where) -> None:
        self.findings.append({"code": code, "part": part, "message": message, **where})

    def warn(self, code: str, part: str, message: str, **where) -> None:
        entry = {"code": code, "part": part, "message": message, **where}
        if entry not in self.warnings:  # one font named by three styles is one warning
            self.warnings.append(entry)

    @property
    def ok(self) -> bool:
        return not self.findings

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "file": self.path,
            "counts": self.counts,
            "findings": self.findings,
            "warnings": self.warnings,
        }


def _read_parts(data: bytes, report: Report) -> dict[str, bytes] | None:
    """The package's XML parts, or None with a finding — read by the rules of
    ADR 0017, which js/10-zip.js follows too. Only stored and deflated entries are
    read, and every read is bounded by the declared sizes."""
    if len(data) > package.MAX_FILE:
        report.find("size", "", "package file is larger than " + str(package.MAX_FILE) + " bytes; refused")
        return None
    try:
        infos = package.entries(data)
    except package.PackageError:
        report.find("package", "", "not a zip package")
        return None
    seen = set()
    for info in infos:
        if info.name in seen:
            report.find("package", info.name, "entry name appears more than once")
            return None
        seen.add(info.name)
    total = sum(i.file_size for i in infos)
    if total > MAX_TOTAL or any(i.file_size > MAX_PART for i in infos):
        report.find("size", "", "package would decompress to " + str(total) + " bytes; refused")
        return None
    if "word/document.xml" not in seen:
        report.find("package", "", "no word/document.xml; not a WordprocessingML package")
        return None
    parts = {}
    for info in infos:
        if not info.name.endswith((".xml", ".rels")):
            continue
        if info.method not in (0, 8) or info.flags & 0x1:
            report.find("package", info.name, "entry uses encryption or a compression method other than stored or deflate")
            return None
        try:
            part = package.read(data, info)
        except package.PackageError:
            report.find("package", info.name, "entry cannot be read (corrupt data or checksum)")
            return None
        if DOCTYPE.search(part):
            report.find("doctype", info.name, "XML part declares a DOCTYPE; refused")
            return None
        parts[info.name] = part
    return parts


def _parse(parts: dict[str, bytes], report: Report) -> dict[str, ET.Element]:
    trees = {}
    for name, data in parts.items():
        # UTF-8 only — what Word writes, and what both implementations read (ADR 0015)
        try:
            text = data.decode("utf-8")
            declared = DECLARED_ENCODING.match(text)
            utf8 = data[:2] not in (b"\xff\xfe", b"\xfe\xff") and (declared is None or declared.group(1).lower() in ("utf-8", "utf8"))
        except UnicodeDecodeError:
            utf8 = False
        if not utf8:
            report.find("package", name, "XML part is not UTF-8")
            continue
        try:
            trees[name] = ET.fromstring(data)
        except ET.ParseError:
            report.find("package", name, "XML is not well-formed")
    return trees


def _canonical(el: ET.Element | None) -> tuple:
    """A run's formatting as a comparable value; rsid attributes are noise."""
    if el is None:
        return ()
    attrs = tuple(
        sorted((local(k), v) for k, v in el.attrib.items() if not local(k).startswith("rsid"))
    )
    return (local(el.tag), attrs, tuple(_canonical(c) for c in el))


def _check_order(el: ET.Element, order: list[str], part: str, report: Report, what: str) -> None:
    rank = {name: i for i, name in enumerate(order)}
    last_rank, last_name = -1, ""
    for child in el:
        name = local(child.tag)
        if name not in rank:  # an extension element: not this schema's concern
            continue
        if rank[name] < last_rank:
            report.find(
                "order", part, f"in {what}, <w:{name}> must come before <w:{last_name}>"
            )
            return
        last_rank, last_name = rank[name], name


def _check_rpr_twins(rpr: ET.Element, part: str, report: Report, what: str, thai: bool = True) -> None:
    """`thai` says whether the text this rPr formats holds Thai; the font warning
    is only worth raising then — a ☐ in Segoe UI Symbol needs no Thai glyphs."""
    fonts = rpr.find(w("rFonts"))
    if fonts is not None:
        latin = any(fonts.get(w(a)) for a in ("ascii", "hAnsi", "asciiTheme", "hAnsiTheme"))
        cs = fonts.get(w("cs")) or fonts.get(w("cstheme"))
        if latin and not cs:
            report.find("5", part, f"in {what}, w:rFonts names a Latin font but no w:cs font")
        elif thai and cs and not fonts.get(w("cstheme")) and cs.lower() not in THAI_FONTS:
            report.warn("font", part, "in " + what + ", complex-script font '" + cs + "' is not known to carry Thai glyphs")
    for latin, twin in (("sz", "szCs"), ("b", "bCs"), ("i", "iCs")):
        if rpr.find(w(latin)) is not None and rpr.find(w(twin)) is None:
            report.find("5", part, f"in {what}, <w:{latin}> has no <w:{twin}> beside it")


def _check_settings(root: ET.Element, report: Report) -> None:
    part = "word/settings.xml"
    _check_order(root, SETTINGS_ORDER, part, report, "w:settings")
    modes = [
        cs.get(w("val"))
        for cs in root.iter(w("compatSetting"))
        if cs.get(w("name")) == "compatibilityMode" and cs.get(w("uri")) == COMPAT_URI
    ]
    if modes != ["15"]:
        report.find("1", part, "compatibilityMode declared as " + (", ".join(str(m) for m in modes) or "nothing") + "; must be exactly one 15")


def _check_text_part(name: str, root: ET.Element, report: Report) -> None:
    for parent in root.iter():
        if not any(c.tag == w("r") for c in parent):
            continue
        previous: tuple | None = None
        prev_has_text = False
        for run in parent:
            if run.tag != w("r"):
                # a hyperlink, bookmark or field between two runs keeps them apart:
                # only runs with nothing between them can split a word
                previous, prev_has_text = None, False
                continue
            rpr = run.find(w("rPr"))
            texts = run.findall(w("t"))
            has_text = bool(texts)
            if rpr is not None:
                _check_order(rpr, RPR_ORDER, name, report, "a run's w:rPr")
                thai = any(is_thai(ch) for t in texts for ch in (t.text or ""))
                _check_rpr_twins(rpr, name, report, "a run", thai)
            if has_text:
                report.counts["runs"] = report.counts.get("runs", 0) + 1
                if rpr is None or rpr.find(w("cs")) is None:
                    report.find("2", name, "a run with text has no <w:cs/> element")
                else:
                    lang = rpr.find(w("lang"))
                    if lang is None or lang.get(w("bidi")) != "th-TH":
                        report.find("2", name, 'a run with text has no <w:lang w:bidi="th-TH"/>')
                for t in texts:
                    for ch, label in INVISIBLE.items():
                        if ch in (t.text or ""):
                            report.find("invisible", name, f"text contains {label}")
                            break
            shape = _canonical(rpr)
            if has_text and prev_has_text and shape == previous:
                report.find("4", name, "two adjacent runs carry identical formatting; a word may be split across them")
            previous, prev_has_text = shape, has_text
    for p in root.iter(w("p")):
        ppr = p.find(w("pPr"))
        if ppr is not None:
            _check_order(ppr, PPR_ORDER, name, report, "a paragraph's w:pPr")
    report.counts["paragraphs"] = report.counts.get("paragraphs", 0) + len(root.findall(f".//{w('p')}"))
    if name == "word/document.xml":
        report.counts["tables"] = len(root.findall(f".//{w('tbl')}"))
    if name == "word/footnotes.xml":
        report.counts["footnotes"] = len(
            [f for f in root.iter(w("footnote")) if f.get(w("type")) not in ("separator", "continuationSeparator")]
        )


def _check_styles(name: str, root: ET.Element, report: Report) -> None:
    for rpr in root.iter(w("rPr")):
        _check_order(rpr, RPR_ORDER, name, report, "a style's w:rPr")
        _check_rpr_twins(rpr, name, report, "a style")
    for ppr in root.iter(w("pPr")):
        _check_order(ppr, PPR_ORDER, name, report, "a style's w:pPr")


def _check_numbering(name: str, root: ET.Element, report: Report) -> None:
    for lvl in root.iter(w("lvl")):
        fmt = lvl.find(w("numFmt"))
        fonts = lvl.find(f"{w('rPr')}/{w('rFonts')}")
        if fmt is not None and fmt.get(w("val")) == "bullet" and fonts is not None:
            if any(v == "Symbol" for v in fonts.attrib.values()):
                report.find("5", name, "a bullet level uses the Symbol font; bullets need a Thai-capable font")
        rpr = lvl.find(w("rPr"))
        if rpr is not None:
            _check_order(rpr, RPR_ORDER, name, report, "a numbering level's w:rPr")


def check(path) -> Report:
    """`path` is a file path, or a file-like object with the package's bytes."""
    if isinstance(path, (str, pathlib.Path)):
        report = Report(str(path))
        try:
            with open(path, "rb") as f:
                data = f.read(package.MAX_FILE + 1)
        except OSError:
            data = b""  # judged like any other file that is no zip
    else:
        report = Report("<bytes>")
        data = path.read(package.MAX_FILE + 1)
    parts = _read_parts(data, report)
    if parts is None:
        return report
    trees = _parse(parts, report)
    for name, root in trees.items():
        if name.startswith("word/") and root.find(f".//{w('noProof')}") is not None:
            report.find("3", name, "<w:noProof/> switches Thai proofing — and Thai line breaking — off")
    settings = trees.get("word/settings.xml")
    if settings is None:
        report.find("1", "word/settings.xml", "no settings part; compatibilityMode is not declared")
    else:
        _check_settings(settings, report)
    for name, root in trees.items():
        if TEXT_PARTS.fullmatch(name):
            _check_text_part(name, root, report)
    if "word/styles.xml" in trees:
        _check_styles("word/styles.xml", trees["word/styles.xml"], report)
    if "word/numbering.xml" in trees:
        _check_numbering("word/numbering.xml", trees["word/numbering.xml"], report)
    return report


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(json.dumps({"ok": False, "error": "usage: thai_docx check FILE.docx"}))
        return 2
    report = check(argv[0])
    print(json.dumps(report.as_dict(), ensure_ascii=False))
    if any(f["code"] in ("package", "doctype", "size") for f in report.findings):
        return 2
    return 0 if report.ok else 1
