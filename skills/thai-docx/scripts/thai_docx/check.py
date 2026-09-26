# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""`thai_docx check FILE.docx` — report, by number, every cause in ADR 0004 the file
still carries, plus the two things ADR 0023 and 0040 make the checker refuse.

Findings, each with a `code`:

    1        compatibilityMode is not declared exactly once as 15
    2        a run whose text is complex script (Thai, and ooxml.COMPLEX_SCRIPT's others) lacks <w:cs/> (ADR 0039: a run whose
             text is not complex script must not be asked to carry it, and a file built
             with --force-cs-whole-doc carries it everywhere, which is not a finding)
    3        <w:noProof/> appears somewhere
    4        two adjacent runs carry identical formatting (a word may be split)
    5        a complex-script twin is missing (cs font, szCs, bCs, iCs), or a bullet
             level uses the Symbol font
    order    a property stands in the wrong place for the schema (Word ignores it): in a run's,
             a paragraph's or a paragraph mark's properties, a section's, a table's, a row's, a
             cell's, a style, a numbering level, the settings
    invisible  a character a reader cannot see is in the text: a zero-width one, any other format
               character, a noncharacter
    doctype  an XML part declares a DOCTYPE — refused before parsing (ADR 0040 §9)
    size     the package would decompress past the cap — refused (ADR 0040 §9)
    package  not a WordprocessingML package, or a Strict one (ISO/IEC 29500 Strict), which
             names every element in another namespace and would read as an empty document

The parts are found as Word finds them: the main document by the package's relationship, and
its headers, footers, notes, comments, styles, numbering and settings by the document's — a
part is not known by its file name (a first-page header may be `headerFirst.xml`). A switch
such as `<w:cs w:val="0"/>` is read as the off it says. Deleted text is text.

Warnings never fail the check; today there is one: a complex-script font the
checker does not know to carry Thai glyphs (ADR 0020).

Role: decider — exit 0 when there are no findings, 1 when there are, 2 when the
file could not be examined at all. The output is one JSON line, and never carries
the document's text (ADR 0040 §8).
"""

from __future__ import annotations

import json
import pathlib
import re
from xml.etree import ElementTree as ET

from . import package
from .ooxml import (
    INVISIBLE,
    LVL_ORDER,
    PPR_ORDER,
    RPR_ORDER,
    SECTPR_ORDER,
    SETTINGS_ORDER,
    STYLE_ORDER,
    TBLPR_ORDER,
    TCPR_ORDER,
    THAI_FONTS,
    TRPR_ORDER,
    is_on,
    is_complex,
    is_thai,
    local,
    rank,
    unseen,
    w,
)

MAX_PART = 32 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
COMPAT_URI = "http://schemas.microsoft.com/office/word"
# the names Word gives the parts that hold text: read by name as well as by relationship, so a
# part no relationship reaches is not skipped for that
TEXT_PARTS = re.compile(r"word/(document|comments|footnotes|endnotes|header[0-9]*|footer[0-9]*)\.xml")  # fullmatch
RELATIONSHIPS = ("http://schemas.openxmlformats.org/officeDocument/2006/relationships/",
                 "http://purl.oclc.org/ooxml/officeDocument/relationships/")
TEXT_KINDS = ("header", "footer", "footnotes", "endnotes", "comments")
STRICT_W = "http://purl.oclc.org/ooxml/wordprocessingml/main"
RPR_RANK, PPR_RANK, SETTINGS_RANK = rank(RPR_ORDER), rank(PPR_ORDER), rank(SETTINGS_ORDER)
LVL_RANK, STYLE_RANK = rank(LVL_ORDER), rank(STYLE_ORDER)
# the property lists a table and a section hold, wherever they stand — a body, a paragraph, a style
STRUCTURE = (("sectPr", rank(SECTPR_ORDER)), ("tblPr", rank(TBLPR_ORDER)), ("trPr", rank(TRPR_ORDER)),
             ("tcPr", rank(TCPR_ORDER)))
DOCTYPE = re.compile(rb"<!DOCTYPE", re.IGNORECASE)
DECLARED_ENCODING = re.compile("\ufeff?<\\?xml[^>]*?[ \\t\\r\\n]encoding[ \\t\\r\\n]*=[ \\t\\r\\n]*[\"']([^\"']*)[\"']")


class Report:
    def __init__(self, path: str):
        self.path = path
        self.error: str | None = None  # the path could not be read at all: not about the document
        self.findings: list[dict] = []
        self.warnings: list[dict] = []
        self.counts: dict[str, int] = {}
        self.numbering: dict | None = None  # which way the document's numbers are made (ADR 0037)

    def find(self, code: str, part: str, message: str, **where) -> None:
        self.findings.append({"code": code, "part": part, "message": message, **where})

    def warn(self, code: str, part: str, message: str, **where) -> None:
        entry = {"code": code, "part": part, "message": message, **where}
        if entry not in self.warnings:  # one font named by three styles is one warning
            self.warnings.append(entry)

    @property
    def ok(self) -> bool:
        return self.error is None and not self.findings

    def as_dict(self) -> dict:
        if self.error is not None:
            return {"ok": False, "file": self.path, "error": self.error}
        return {
            "ok": self.ok,
            "file": self.path,
            "counts": self.counts,
            "findings": self.findings,
            "warnings": self.warnings,
            **({"numbering": self.numbering} if self.numbering is not None else {}),
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
    # every entry, not only the parts read: repair copies the others as they are, and one
    # encrypted or compressed some other way was written back under flags that said otherwise
    for info in infos:
        if info.method not in (0, 8) or info.flags & 0x1:
            report.find("package", info.name, "entry uses encryption or a compression method other than stored or deflate")
            return None
    parts = {}
    for info in infos:
        if not info.name.endswith((".xml", ".rels")):
            continue
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
        # UTF-8 only — what Word writes, and what both implementations read (ADR 0015). Decided
        # on the bytes: a NUL is valid UTF-8 and never valid XML, and it is what UTF-16 and UCS-4
        # are full of — a part in either, with no byte-order mark, decoded as UTF-8 and went to
        # a parser that read it as UTF-16, past the DOCTYPE refusal, which reads bytes as ASCII
        if b"\x00" in data:
            report.find("package", name, "XML part is not UTF-8")
            continue
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


def _ascii_lower(name: str) -> str:
    # a part name matches in any case (OPC); ASCII only, which both runtimes lower alike
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in name)


def _resolve(source: str, target: str) -> str:
    """A relationship's target as a part name: relative to the folder of `source`, or to the
    package's root when it begins with a slash."""
    path = [] if target.startswith("/") else source.split("/")[:-1]
    for segment in target.split("/"):
        if segment == "..":
            if path:
                path.pop()
        elif segment not in ("", "."):
            path.append(segment)
    return "/".join(path)


def _related(names: dict[str, str], tree_of, source: str) -> list[tuple[str, str]]:
    """(kind, part) for each relationship of `source` ("" for the package's own) to a part the
    package holds. `names` maps each part name, lowered, to the name itself."""
    folder, _, file = source.rpartition("/")
    root = tree_of(names.get(_ascii_lower((folder + "/" if folder else "") + "_rels/" + file + ".rels"), ""))
    out = []
    for rel in [] if root is None else list(root):
        kind = rel.get("Type") or ""
        prefix = next((p for p in RELATIONSHIPS if kind.startswith(p)), None)
        if local(rel.tag) != "Relationship" or rel.get("TargetMode") == "External" or prefix is None:
            continue
        name = names.get(_ascii_lower(_resolve(source, rel.get("Target") or "")))
        if name is not None:
            out.append((kind[len(prefix):], name))
    return out


def part_roles(names: list[str], tree_of) -> dict:
    """Which part is which, as Word finds them: the main document by the package's relationship
    (else `word/document.xml`), then its text parts, styles, numbering and settings by the
    document's (else by the names Word gives them). `names` in package order; `tree_of(name)` is
    that part parsed, or None. The text parts come in package order."""
    lowered = {_ascii_lower(n): n for n in reversed(names)}
    main = next((n for kind, n in _related(lowered, tree_of, "") if kind == "officeDocument"), None)
    if main is None and "word/document.xml" in names:
        main = "word/document.xml"
    roles: dict = {"document": main, "text": [], "footnotes": None, "styles": None, "numbering": None, "settings": None}
    if main is None:
        return roles
    text = {main} | {n for n in names if TEXT_PARTS.fullmatch(n)}
    for kind, name in _related(lowered, tree_of, main):
        if kind in TEXT_KINDS:
            text.add(name)
        if kind in ("footnotes", "styles", "numbering", "settings") and roles[kind] is None:
            roles[kind] = name
    for kind in ("footnotes", "styles", "numbering", "settings"):
        if roles[kind] is None and "word/" + kind + ".xml" in names:
            roles[kind] = "word/" + kind + ".xml"
    roles["text"] = [n for n in names if n in text]
    return roles


def part_roles_of(parts: dict[str, bytes]) -> dict:
    """`part_roles` for a package the checker has already read without a finding that refuses it."""
    def tree_of(name: str):
        if not name.endswith(".rels") or name not in parts:
            return None
        try:
            return ET.fromstring(parts[name])
        except ET.ParseError:
            return None
    return part_roles(list(parts), tree_of)


def _canonical(el: ET.Element | None) -> tuple:
    """A run's formatting as a comparable value; rsid attributes are noise. Flat — each element
    opens, its children follow, and it closes — and built with a stack of its own, because the
    input sets the depth and neither implementation reads by recursion where it does (ADR 0017)."""
    if el is None:
        return ()
    out: list = []
    pending: list = [el]
    while pending:
        node = pending.pop()
        if node is None:
            out.append(None)  # the element before it closes here
            continue
        attrs = tuple(sorted((local(k), v) for k, v in node.attrib.items() if not local(k).startswith("rsid")))
        out.append((local(node.tag), attrs))
        pending.append(None)
        pending.extend(reversed(list(node)))
    return tuple(out)


def _check_order(el: ET.Element, ranks: dict[str, int], part: str, report: Report, what: str) -> None:
    last_rank, last_name = -1, ""
    for child in el:
        name = local(child.tag)
        if name not in ranks:  # an extension element: not this schema's concern
            continue
        if ranks[name] < last_rank:
            report.find(
                "order", part, f"in {what}, <w:{name}> must come before <w:{last_name}>"
            )
            return
        last_rank, last_name = ranks[name], name


def _check_structure(root: ET.Element, part: str, report: Report) -> None:
    for tag, ranks in STRUCTURE:
        for el in root.iter(w(tag)):
            _check_order(el, ranks, part, report, "w:" + tag)


def _check_rpr_twins(rpr: ET.Element, part: str, report: Report, what: str, thai: bool = True) -> None:
    """`thai` says whether the text this rPr formats holds Thai; the font warning
    is only worth raising then — a □ in Arial needs no Thai glyphs."""
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


def _check_settings(part: str, root: ET.Element, report: Report) -> None:
    _check_order(root, SETTINGS_RANK, part, report, "w:settings")
    modes = [
        cs.get(w("val"))
        for cs in root.iter(w("compatSetting"))
        if cs.get(w("name")) == "compatibilityMode" and cs.get(w("uri")) == COMPAT_URI
    ]
    if modes != ["15"]:
        report.find("1", part, "compatibilityMode declared as " + (", ".join(str(m) for m in modes) or "nothing") + "; must be exactly one 15")


def _check_text_part(name: str, root: ET.Element, report: Report, roles: dict) -> None:
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
            # deleted text is text: a reviewer reads it, and rejecting the deletion brings it back
            texts = [t for t in run if t.tag in (w("t"), w("delText"))]
            has_text = bool(texts)
            thai = any(is_thai(ch) for t in texts for ch in (t.text or ""))  # the font warning's: Thai glyphs
            complex_text = any(is_complex(ch) for t in texts for ch in (t.text or ""))
            if rpr is not None:
                _check_order(rpr, RPR_RANK, name, report, "a run's w:rPr")
                _check_rpr_twins(rpr, name, report, "a run", thai)
            if has_text:
                report.counts["runs"] = report.counts.get("runs", 0) + 1
                cs = None if rpr is None else rpr.find(w("cs"))
                marked = cs is not None and is_on(cs)
                # one direction only: a run that holds no complex script may carry the marker,
                # because --force-cs-whole-doc writes it on every run and that file is ours too
                if complex_text and not marked:
                    report.find("2", name, "a run whose text is complex script has no <w:cs/> element")
                if marked:
                    lang = rpr.find(w("lang"))
                    if lang is not None and lang.get(w("bidi")) == "th-TH":
                        report.counts["thai_language_runs"] = report.counts.get("thai_language_runs", 0) + 1
                for t in texts:
                    text = t.text or ""
                    # the five by name first, as they always were; then any other in text order
                    label = next((label for ch, label in INVISIBLE.items() if ch in text), None)
                    if label is None:
                        label = next((named for named in map(unseen, text) if named is not None), None)
                    if label is not None:
                        report.find("invisible", name, f"text contains {label}")
            shape = _canonical(rpr)
            if has_text and prev_has_text and shape == previous:
                report.find("4", name, "two adjacent runs carry identical formatting; a word may be split across them")
            previous, prev_has_text = shape, has_text
    for p in root.iter(w("p")):
        ppr = p.find(w("pPr"))
        if ppr is not None:
            _check_order(ppr, PPR_RANK, name, report, "a paragraph's w:pPr")
            mark = ppr.find(w("rPr"))
            if mark is not None:
                # the paragraph mark's own properties: no text, so no marker is asked of them
                _check_order(mark, RPR_RANK, name, report, "a paragraph mark's w:rPr")
                _check_rpr_twins(mark, name, report, "a paragraph mark", False)
    _check_structure(root, name, report)
    report.counts["paragraphs"] = report.counts.get("paragraphs", 0) + len(root.findall(f".//{w('p')}"))
    if name == roles["document"]:
        report.counts["tables"] = len(root.findall(f".//{w('tbl')}"))
    if name == roles["footnotes"]:
        report.counts["footnotes"] = len(
            [f for f in root.iter(w("footnote")) if f.get(w("type")) not in ("separator", "continuationSeparator")]
        )


def _check_styles(name: str, root: ET.Element, report: Report) -> None:
    # what a tracked change says the formatting was: history, not formatting any text has
    history = {id(el) for change in root.iter() if change.tag in (w("rPrChange"), w("pPrChange"))
               for el in change.iter() if el is not change}
    for style in root.iter(w("style")):
        _check_order(style, STYLE_RANK, name, report, "w:style")
    for rpr in root.iter(w("rPr")):
        _check_order(rpr, RPR_RANK, name, report, "a style's w:rPr")
        if id(rpr) not in history:
            _check_rpr_twins(rpr, name, report, "a style")
    for ppr in root.iter(w("pPr")):
        _check_order(ppr, PPR_RANK, name, report, "a style's w:pPr")
    _check_structure(root, name, report)


def _check_numbering(name: str, root: ET.Element, report: Report) -> None:
    for lvl in root.iter(w("lvl")):
        fmt = lvl.find(w("numFmt"))
        fonts = lvl.find(f"{w('rPr')}/{w('rFonts')}")
        if fmt is not None and fmt.get(w("val")) == "bullet" and fonts is not None:
            if any(v == "Symbol" for v in fonts.attrib.values()):
                report.find("5", name, "a bullet level uses the Symbol font; bullets need a Thai-capable font")
        _check_order(lvl, LVL_RANK, name, report, "w:lvl")
        ppr = lvl.find(w("pPr"))
        if ppr is not None:
            _check_order(ppr, PPR_RANK, name, report, "a numbering level's w:pPr")
        rpr = lvl.find(w("rPr"))
        if rpr is not None:
            _check_order(rpr, RPR_RANK, name, report, "a numbering level's w:rPr")
            # the number or the bullet: its font need not carry Thai, but its twins are asked
            _check_rpr_twins(rpr, name, report, "a numbering level", False)


def check(path) -> Report:
    """`path` is a file path, or a file-like object with the package's bytes."""
    if isinstance(path, (str, pathlib.Path)):
        report = Report(str(path))
        try:
            data = package.read_regular(str(path), package.MAX_FILE)
        except OSError as exc:
            # a name typed wrong is not a damaged document: `error`, as `build` answers it
            report.error = "cannot read " + str(path) + ": " + package.os_error(exc)
            return report
    else:
        report = Report("<bytes>")
        data = path.read(package.MAX_FILE + 1)
    parts = _read_parts(data, report)
    if parts is None:
        return report
    trees = _parse(parts, report)
    roles = part_roles(list(parts), trees.get)
    document = roles["document"]
    if document is None:
        report.find("package", "", "no main document (word/document.xml, or the part _rels/.rels names);"
                                   " not a WordprocessingML package")
        return report
    if document not in trees:
        return report  # not UTF-8 or not well-formed, and found so above
    if trees[document].tag != w("document"):
        if trees[document].tag.startswith("{" + STRICT_W + "}"):
            report.find("package", document, "Strict Open XML (ISO/IEC 29500 Strict) is not read: every element"
                                              " would be missed; save it from Word as Word Document (.docx)")
        else:
            report.find("package", document, "the main document is not a WordprocessingML document")
        return report
    named = {n for n in (roles["styles"], roles["numbering"], roles["settings"]) if n} | set(roles["text"])
    for name, root in trees.items():
        if (name.startswith("word/") or name in named) and any(is_on(e) for e in root.iter(w("noProof"))):
            report.find("3", name, "<w:noProof/> switches Thai proofing — and Thai line breaking — off")
    settings = roles["settings"] or "word/settings.xml"
    if settings not in trees:
        report.find("1", settings, "no settings part; compatibilityMode is not declared")
    else:
        _check_settings(settings, trees[settings], report)
    for name in roles["text"]:
        if name in trees:
            _check_text_part(name, trees[name], report, roles)
    if roles["styles"] in trees:
        _check_styles(roles["styles"], trees[roles["styles"]], report)
    if roles["numbering"] in trees:
        _check_numbering(roles["numbering"], trees[roles["numbering"]], report)
    report.numbering = numbering_kind(trees[document], trees.get(roles["styles"] or ""), trees.get(roles["numbering"] or ""))
    return report


WRITTEN_HEADING = re.compile(r"(?:(?:บทที่|ภาคผนวก)\s|[0-9๐-๙]+(?:\.[0-9๐-๙]+)*\.?\s)")
WRITTEN_CAPTION = re.compile(r"(?:ตารางที่|รูปที่|Table|Figure)\s*[0-9๐-๙ก-ฮA-Za-z]+(?:[-.][0-9๐-๙]+)?")
WRITTEN_ITEM = re.compile(r"[0-9๐-๙]+[.)](?![0-9๐-๙])")  # "1." "2)" — not "98.3"


def numbering_kind(document: ET.Element, styles: ET.Element | None, numbering: ET.Element | None) -> dict:
    """Which way the document's numbers are made, heading by heading, caption by caption and item
    by item (ADR 0037, what ships first): **automatic**, the application counting — a heading in
    a style tied to a numbering definition, a `SEQ` field in a caption, a list item numbered by
    `w:numPr`; or **written**, the number as text at the head of the paragraph, the build's own
    kind. Both is `mixed`; neither, `none`. It is read, not changed: this is what lets the
    assistant ask which the document should be, before anything renumbers it."""
    heading_styles, caption_styles, counted_styles, listing_styles = set(), set(), set(), set()
    for style in [] if styles is None else styles.iter(w("style")):
        sid, name = style.get(w("styleId")) or "", (style.find(w("name")).get(w("val")) or "").lower() if style.find(w("name")) is not None else ""
        if name.startswith("heading ") or sid.lower().startswith("heading"):
            heading_styles.add(sid)
        if "caption" in name or "caption" in sid.lower():
            caption_styles.add(sid)
        if name.startswith("toc ") or name == "table of figures" or sid.lower().startswith(("toc", "tableoffigures")):
            listing_styles.add(sid)  # the lines a contents or figures field lists, not numbers of their own
        num = style.find(f"{w('pPr')}/{w('numPr')}/{w('numId')}")
        if num is not None and num.get(w("val")) not in (None, "0"):
            counted_styles.add(sid)
    formats: dict[tuple[str, str], str] = {}
    if numbering is not None:
        abstract = {a.get(w("abstractNumId")): a for a in numbering.iter(w("abstractNum"))}
        for lvl in numbering.iter(w("lvl")):
            tied = lvl.find(w("pStyle"))
            if tied is not None:
                counted_styles.add(tied.get(w("val")))
        for num in numbering.iter(w("num")):
            ref = num.find(w("abstractNumId"))
            for lvl in [] if ref is None or ref.get(w("val")) not in abstract else abstract[ref.get(w("val"))].iter(w("lvl")):
                fmt = lvl.find(w("numFmt"))
                formats[(num.get(w("numId")), lvl.get(w("ilvl")))] = "" if fmt is None else fmt.get(w("val")) or ""
    found = {"automatic": {"headings": 0, "captions": 0, "lists": 0}, "written": {"headings": 0, "captions": 0, "lists": 0}}
    for p in document.iter(w("p")):
        ppr = p.find(w("pPr"))
        style_el = None if ppr is None else ppr.find(w("pStyle"))
        style = "" if style_el is None else style_el.get(w("val")) or ""
        num_id = None if ppr is None else ppr.find(f"{w('numPr')}/{w('numId')}")
        ilvl = None if ppr is None else ppr.find(f"{w('numPr')}/{w('ilvl')}")
        own_num = None if num_id is None else num_id.get(w("val"))
        text = "".join(t.text or "" for t in p.iter(w("t")))
        fields = " ".join([t.text or "" for t in p.iter(w("instrText"))] + [f.get(w("instr")) or "" for f in p.iter(w("fldSimple"))])
        if style in listing_styles:
            continue
        if style in heading_styles:
            if own_num not in (None, "0") or (own_num is None and style in counted_styles):
                found["automatic"]["headings"] += 1
            elif WRITTEN_HEADING.match(text):
                found["written"]["headings"] += 1
        elif re.search(r"\bSEQ\b", fields):
            found["automatic"]["captions"] += 1
        elif style in caption_styles or WRITTEN_CAPTION.match(text):
            if WRITTEN_CAPTION.match(text):
                found["written"]["captions"] += 1
        elif own_num not in (None, "0"):
            level = "0" if ilvl is None else ilvl.get(w("val")) or "0"
            if formats.get((own_num, level), "") not in ("bullet", "none"):
                found["automatic"]["lists"] += 1
        elif WRITTEN_ITEM.match(text):
            found["written"]["lists"] += 1
    automatic, written = any(found["automatic"].values()), any(found["written"].values())
    kind = "mixed" if automatic and written else "automatic" if automatic else "written" if written else "none"
    return {"kind": kind, **found}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] == "--help":
        print(json.dumps({"ok": False, "error": "usage: thai_docx check FILE.docx"}))
        return 2
    report = check(argv[0])
    print(json.dumps(report.as_dict(), ensure_ascii=False))
    if report.error is not None:
        return 2
    if any(f["code"] in ("package", "doctype", "size") for f in report.findings):
        return 2
    return 0 if report.ok else 1
