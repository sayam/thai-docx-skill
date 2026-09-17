# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Inputs and drivers that hold the JavaScript implementation to the Python one
(ADR 0008): the same Markdown reading, the same .docx bytes, the same checker
report. Every generator is seeded; nothing here reads the clock or the network.
"""

from __future__ import annotations

import base64
import json
import random
import struct
import subprocess
import zlib

import oracle
from docx_fixture import good
from docx_fixture import pack as fixture_pack

from thai_docx import build as b
from thai_docx import check as check_mod
from thai_docx import markdown as md

import io
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PARITY_JS = ROOT / "tests" / "js" / "parity.cjs"
FIXTURES = ROOT / "tests" / "fixtures"
GOLDEN = ROOT / "tests" / "golden"


def run_js(request: dict):
    done = subprocess.run(["node", str(PARITY_JS)], input=json.dumps(request), capture_output=True, text=True)
    assert done.returncode == 0 and done.stderr == "", done.stderr[-3000:]
    return json.loads(done.stdout)


def plain(value):
    """What JSON makes of a value — tuples become lists — for comparing with Node."""
    return json.loads(json.dumps(value))


# --- Markdown ------------------------------------------------------------------


def py_ast(text: str) -> dict:
    try:
        doc = md.parse(text)
    except md.Unsupported as exc:
        return {"error": exc.what, "line": exc.line}
    return plain({
        "blocks": doc.blocks,
        "footnotes": [[label, doc.footnotes[label]] for label in doc.footnote_order],
        "front_matter": list(map(list, doc.front_matter.items())),
        "warnings": doc.warnings,
    })


def markdown_texts(start: int, n: int) -> list[str]:
    gens = (oracle.generate_core, oracle.generate_gfm, oracle.generate_wide)
    return [gen(seed) for seed in range(start, start + n) for gen in gens]


# --- build ---------------------------------------------------------------------

PNG = (FIXTURES / "pixel.png").read_bytes()
JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xc0\x00\x11\x08\x00\x20\x00\x40\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01\xff\xd9"
)
IMAGES = {"p.png": PNG, "sub/q.jpg": JPEG, "fake.png": b"GIF89a", "pixel.png": PNG}
IMAGE_LINES = [
    "![a](p.png)", "![ภาพ](sub/q.jpg) and ![again](p.png)", "![x](fake.png)", "![x](../p.png)",
    "![x](/p.png)", "![x](https://e.x/p.png)", "![x](missing.png)", "![x](sub\\..\\p.png)",
]
FLAG_SETS = [
    [], ["--toc"], ["--page-numbers", "--hide-spelling-errors"], ["--align", "thai", "--paper", "letter"],
    ["--size", "15.5", "--margins", "0.5,2,1,0.75"], ["--font", "Sarabun"], ["--font", "Papyrus"],
    ["--size=14", "--align=justify"], ["--size", "401"], ["--margins", "1,1"], ["--bogus"], ["--toc=yes"],
    ["--size", "1e2"], ["--paper"], ["--indent", "0.5"], ["--indent=1", "--align", "thai"], ["--indent", "0.3333333"],
    ["--indent", "-1"], ["--indent", "5.5"], ["--no-repeat-table-header"], ["--no-repeat-table-header=no", "--toc"],
    ["--header", "ลับ"], ["--footer=บริษัท ตัวอย่าง จำกัด", "--page-numbers", "bottom-center", "--no-page-number-first"],
    ["--header", "ร่าง & <ห้ามเผยแพร่>", "--footer", "หน้า", "--page-numbers", "top-center"], ["--header="], ["--header", "ก\tข"],
    ["--footer", "x" * 201],
    ["--table-size", "14"], ["--table-size=13.5", "--table-widths", "auto"], ["--table-size", "0.5"], ["--table-size", "14pt"],
    ["--table-widths", "auto"], ["--table-widths=auto", "--landscape"], ["--table-widths", "equal"], ["--table-widths", "fit"], ["--heading-numbers"],
    ["--heading-numbers", "--thai-digits", "--toc"], ["--heading-numbers=on"], ["--page-numbers", "--no-page-number-first"],
    ["--no-page-number-first", "--page-numbers", "bottom-center", "--toc"], ["--no-page-number-first"],
    ["--no-page-number-first=1", "--page-numbers"], ["--paper", "f14"], ["--paper=f14", "--landscape", "--page-numbers", "bottom-center"],
    ["--paper", "F14"], ["--paper", "folio"], ["--landscape"], ["--landscape", "--paper", "letter", "--margins", "0.5,4,0.5,4"],
    ["--landscape", "--margins", "3.5,1,3.5,1"], ["--landscape=1"], ["--thai-digits"], ["--thai-digits", "--page-numbers", "bottom-center", "--toc"],
    ["--thai-digits=yes"], ["--page-numbers", "top-center"], ["--page-numbers=bottom-center", "--toc"], ["--page-numbers=middle"],
    ["--page-numbers="],
    ["--page-numbers", "bottom-center", "--page-numbers"], ["--line-spacing", "1.15"], ["--line-spacing=2", "--align", "thai"],
    ["--line-spacing", "0.9"], ["--line-spacing", "3.5"], ["--line-spacing", "1.3333333"],
    ["--indent", "4", "--paper", "letter", "--margins", "1,2,1,2"],
]


STRUCTURED = [
    "ปก\n\n<!-- front -->\n\n# บทคัดย่อ\n\nย่อ\n\n# สารบัญ\n\n<!-- toc -->\n\n<!-- list-of-tables -->\n<!-- list-of-figures -->\n\n"
    "<!-- chapters -->\n\n# บทนำ\n\n## ที่มา\n\nTable: สาเหตุ **หนา**\n\n| ก | ข |\n|---|---|\n| 1 | 2 |\n\n![a](p.png)\n\nFigure: ขั้นตอน\n\n"
    "# ทฤษฎี\n\n### ย่อย\n\nTable:\n\n| ก |\n|---|\n| 1 |\n\n<!-- back -->\n\n# ภาคผนวก ก\n\n![](p.png) ![](p.png)\n\nFigure:\tรูปภาคผนวก\n",
    "<!-- chapters -->\n\n# หนึ่ง\n\n- รายการ\n\n# สอง\n\n```\ncode\n```\n\n<!-- back -->\n\n> อ้างอิง\n",
    "Table: หนึ่ง\n\n| ก |\n|---|\n| 1 |\n\n# บท\n\nTable: ลอย\n\nข้อความ\n\n![](p.png) ข้อความ\n\nFigure: ลอย\n\n"
    "**Table:** ไม่ใช่\n\n| ก |\n|---|\n| 1 |\n",
    "<!-- chapters -->\n\n# บท\n\n<!-- back -->\n\n# บรรณานุกรม\n\n<!-- appendices -->\n\n# แบบสอบถาม\n\n"
    "## ส่วน\n\nTable: ผู้ตอบ\n\n| ก |\n|---|\n| 1 |\n\n"
    "![](p.png)\n\nFigure: แบบ\n\n" + "".join("# ภาคผนวก %d\n\nTable: ต\n\n| ก |\n|---|\n| 1 |\n\n" % k for k in range(30))
    + "<!-- back -->\n\n# ประวัติ\n",
    "<!-- appendices -->\n\n# ก\n\n<!-- back -->\n\n<!-- back -->\n", "<!-- back -->\n\n<!-- back -->\n", "<!-- appendices -->\n\n<!-- front -->\n",
    "<!-- chapter -->\n\n# ก\n\n<!-- Chapters -->\n\n<!-- list of figures -->\n\n<!-- todo -->\n\n<!-- TOC -->\n\n"
    "<!-- appendix -->\n\n<!--  backs  -->\n\n<!-- fronts -->\n",
    "- x\n\n  <!-- chapters -->\n\n> <!-- toc -->\n\nก[^1]\n\n[^1]: ข\n\n    <!-- back -->\n",
    "![](p.png)\nFigure: ติดกัน\n\n![](p.png)  \nFigure: hard\n\n![](p.png) **Figure:** หนา\n\n"
    "| ก | ข |\n|---|---|\n| 1 | 2 |\nTable: ต่อท้าย\n\n| ก |\n|---|\nTable: เดี่ยว\n",
    "<!-- back -->\n\n# ก\n\n<!-- front -->\n", "<!-- chapters -->\n<!-- chapters -->\n", "<!-- front -->\n",
    "# ก\n\n<!-- front --> ข้อความ\n\n<!--chapters-->\n\n| ก |\n|---|\n| 1 |\n\n<!-- other -->\n",
]
HEADING_STYLES = [
    'heading-1: font-family: "TH SarabunPSK"; font-size: 20.5pt; color: #1f4e79; font-weight: normal; font-style: italic',
    "heading-2: text-decoration: underline double line-through; text-align: thai-distribute; margin-left: 1.27cm; text-indent: -0.25in",
    "heading-3: margin-top: 18pt; margin-bottom: 0; line-height: 1.5; page-break-before: always; text-decoration: none\n"
    "heading-2: text-align: justify",
    "heading1: font-size: 20pt\nh2: color: #000000\nheading-7: color: #000000\ntitle: x",
    "heading-1: font-family: 'Papyrus'; text-decoration: underline wavy",
    "heading-1: text-indent: 0.3333333cm; margin-left: 10in",
    "heading-1: colour: #FF0000", "heading-1: color: red", "heading-1: font-size: 20", "heading-1: margin-left: -1in",
    "heading-1: margin-left: 10.01in", 'heading-1: font-family: "TH; Sarabun', "heading-1: bold", "heading-1: text-decoration: underline underline",
    "heading-1: text-decoration: double underline", "heading-1: text-decoration: solid line-through", "heading-1: text-decoration: none underline",
    "heading-1: line-height: 4", "heading-2: font-weight: Bold",
    "heading-1: font-family: " + "ก" * 65, "heading-1: ; ; font-size: 12pt;",
]


def build_cases(start: int, n: int) -> list[dict]:
    rng = random.Random(start)
    gens = (oracle.generate_core, oracle.generate_gfm, oracle.generate_wide)
    cases = []
    for seed in range(start, start + n):
        text = gens[seed % 3](seed)
        if rng.random() < 0.3:
            text += "\n\n" + rng.choice(IMAGE_LINES)
        cases.append({"text": text, "args": rng.choice(FLAG_SETS)})
    cases.append({"text": (FIXTURES / "sample.md").read_text(encoding="utf-8"), "args": []})
    heading = "\n\n# บทที่ 1\n\n## ส่วน\n\n### ย่อย\n\nข้อความ\n"
    for text in STRUCTURED:  # ADR 0021: regions, sections, captions and lists alike in both
        for args in ([], ["--heading-numbers", "--page-numbers", "bottom-center", "--no-page-number-first"],
                     ["--thai-digits", "--header", "ลับ", "--figure-label", "ภาพที่"],
                     ["--front-page-numbers", "lower-roman", "--appendix-numbers", "upper-letters", "--appendix-label", "Appendix"],
                     ["--front-page-numbers=decimal", "--appendix-numbers", "upper-roman", "--thai-digits", "--heading-numbers"],
                     ["--appendix-numbers", "decimal", "--front-page-numbers", "upper-roman"]):
            cases.append({"text": text, "args": args})
    for front in HEADING_STYLES:  # ADR 0020: the same styles, warnings and refusals in both
        cases.append({"text": "---\n" + front + "\n---" + heading,
                      "args": rng.choice([[], ["--heading-numbers"], ["--thai-digits", "--heading-numbers"]])})
    return cases


def py_build(case: dict) -> dict:
    """What ThaiDocx.buildDocument gives, computed the Python way."""
    try:
        opts, _, _ = b.parse_args(case["args"] + ["in.md", "out.docx"])
    except b.BuildError as exc:
        return {"result": {"ok": False, "error": exc.what}, "bytes": None}

    def reader(src):
        if ".." in src.replace("\\", "/").split("/") or src.startswith(("/", "\\")):
            raise b.BuildError("image '" + src + "' lies outside the Markdown file's directory; pass --allow-dir for its directory (ADR 0011 §4)")
        if src not in IMAGES:
            raise b.BuildError("image '" + src + "': No such file or directory")
        return src, IMAGES[src]

    result = {"ok": False, "settings": b.settings_json(opts)}
    outcome, data = b.build_text(case["text"], opts, reader)
    result.update(outcome)
    result["ok"] = data is not None
    return {"result": plain(result), "bytes": None if data is None else base64.b64encode(data).decode()}


def js_build_request(cases: list[dict]) -> dict:
    images = {k: base64.b64encode(v).decode() for k, v in IMAGES.items()}
    return {"op": "build", "cases": [dict(c, images=images) for c in cases]}


# --- check: packages written by rule, then damaged -------------------------------


def py_check(data: bytes) -> dict:
    return plain(check_mod.check(io.BytesIO(data)).as_dict())


M16, M32, M64 = 0xFFFF, 0xFFFFFFFF, 0xFFFFFFFFFFFFFFFF


def write_zip(entries: list[dict], *, prefix=b"", comment=b"", count_delta=0, size_delta=0, offset_delta=0, zip64=False, big64=False) -> bytes:
    """A zip archive from explicit fields, so every ADR 0017 rule can be broken on
    purpose. Each entry: name (bytes), data (as stored in the file), crc, size,
    method, flags; optional local_name, local_extra, extra, comment, offset_delta,
    zip64 (sizes and offset moved to a zip64 extra field)."""
    body, central = bytearray(prefix), bytearray()
    for e in entries:
        offset = len(body) - len(prefix)
        local_name = e.get("local_name", e["name"])
        local_extra = e.get("local_extra", b"")
        csize, size = len(e["data"]), e["size"]
        body += struct.pack("<IHHHHHIIIHH", 0x04034B50, 20, e["flags"] & M16, e["method"] & M16, 0, 33, e["crc"] & M32, csize, size & M32,
                            len(local_name), len(local_extra))
        body += local_name + local_extra + e["data"]
        extra, c_csize, c_size, c_offset = e.get("extra", b""), csize, size, offset + e.get("offset_delta", 0)
        if e.get("zip64"):
            extra = struct.pack("<HHQQQ", 1, 24, size, csize, c_offset & M64) + extra
            c_csize = c_size = c_offset = 0xFFFFFFFF
        comment_e = e.get("comment", b"")
        central += struct.pack(
            "<IHHHHHHIIIHHHHHII", 0x02014B50, 20, 20, e["flags"] & M16, e["method"] & M16, 0, 33, e["crc"] & M32, c_csize & M32, c_size & M32,
            (len(e["name"]) + e.get("name_len_delta", 0)) & M16, (len(extra) + e.get("extra_len_delta", 0)) & M16,
            (len(comment_e) + e.get("comment_len_delta", 0)) & M16,
            0, 0, 0o600 << 16, c_offset & M32,
        )
        central += e["name"] + extra + comment_e
    cd_offset = len(body) - len(prefix)
    count = len(entries) + count_delta
    out = body + central
    if zip64:
        record_at = len(out) - len(prefix)
        value = (1 << 53) if big64 else 0
        out += struct.pack("<IQHHIIQQQQ", 0x06064B50, 44, 45, 45, 0, 0, count, (count + value) & M64, (len(central) + size_delta) & M64,
                           (cd_offset + offset_delta) & M64)
        out += struct.pack("<IIQI", 0x07064B50, 0, record_at, 1)
        out += struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, 0xFFFF, 0xFFFF, 0xFFFFFFFF, 0xFFFFFFFF, len(comment)) + comment
    else:
        out += struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, count & 0xFFFF, count & 0xFFFF, (len(central) + size_delta) & 0xFFFFFFFF,
                           (cd_offset + offset_delta) & 0xFFFFFFFF, len(comment)) + comment
    return bytes(out)


def entry(name: str, data: bytes, rng: random.Random, method=None) -> dict:
    method = rng.choice([0, 8]) if method is None else method
    stored = data if method == 0 else _deflate(data, rng)
    name_bytes = name.encode("utf-8")
    return {"name": name_bytes, "data": stored, "crc": zlib.crc32(data), "size": len(data), "method": method, "flags": 0 if name.isascii() else 0x800}


def _deflate(data: bytes, rng: random.Random) -> bytes:
    strategy = rng.choice([zlib.Z_DEFAULT_STRATEGY, zlib.Z_FILTERED, zlib.Z_HUFFMAN_ONLY, zlib.Z_RLE, zlib.Z_FIXED])
    c = zlib.compressobj(rng.randint(0, 9), zlib.DEFLATED, -15, rng.randint(1, 9), strategy)
    return c.compress(data) + c.flush()


def _parts(rng: random.Random) -> list[tuple[str, bytes]]:
    parts = good()
    if rng.random() < 0.5:
        name, data = rng.choice([("word/document.xml", "<w:t>"), ("word/styles.xml", "<w:rFonts")])
        parts[name] = parts[name].replace(data, data + "ก", 1) if rng.random() < 0.3 else parts[name]
    return [(k, v.encode("utf-8") if isinstance(v, str) else v) for k, v in parts.items()]


def structural_package(rng: random.Random) -> bytes:
    """A package that breaks (or, as often, keeps) one or two ADR 0017 rules."""
    entries = [entry(name, data, rng) for name, data in _parts(rng)]
    if rng.random() < 0.3:
        entries.append(entry("word/media/รูป.png", PNG, rng))
    kw: dict = {}
    for _ in range(rng.randint(1, 2)):
        e = rng.choice(entries)
        k = rng.randrange(26)
        if k == 0:
            kw["prefix"] = rng.choice([b"MZ", b"PK\x03\x04" * 3, bytes(100)])
        elif k == 1:
            kw["comment"] = rng.choice([b"x", b"PK\x05\x06" + bytes(18), bytes(300)])
        elif k == 2:
            kw["count_delta"] = rng.choice([-1, 1, 65536])
        elif k == 3:
            kw["size_delta"] = rng.choice([-1, 1, -46])
        elif k == 4:
            kw["offset_delta"] = rng.choice([-1, 1, 1 << 40])
        elif k == 5:
            kw["zip64"] = True
        elif k == 6:
            kw.update(zip64=True, big64=True)
        elif k == 7:
            e["zip64"] = True
        elif k == 8:
            e["comment_len_delta"] = rng.choice([1, 4096])
        elif k == 9:
            e["extra_len_delta"] = rng.choice([1, 3, 4])
        elif k == 10:
            e["extra"] = rng.choice([struct.pack("<HH", 0x5455, 5) + bytes(5), struct.pack("<HH", 1, 8) + bytes(8), struct.pack("<HH", 9, 40)])
        elif k == 11:
            e["local_extra"] = rng.choice([struct.pack("<HH", 0x5455, 5) + bytes(5), bytes(3)])
        elif k == 12:
            e["local_name"] = e["name"][:-1] + b"X"
        elif k == 13:
            e["local_name"] = e["name"] + b"x"
        elif k == 14:
            entries.append(dict(e))
        elif k == 15:
            e["flags"] |= rng.choice([0x1, 0x8, 0x800])
        elif k == 16:
            e["method"] = rng.choice([12, 14, 99, 8 if e["method"] == 0 else 0])
        elif k == 17:
            e["size"] += rng.choice([-1, 1])
        elif k == 18:
            e["crc"] ^= 1
        elif k == 19:
            e["offset_delta"] = rng.choice([-1, 1, 1 << 33])
        elif k == 20:
            e["name"] = e["name"].replace(b"word", b"w\xd3rd")
        elif k == 21:
            e["name"], e["flags"] = e["name"] + b"\xff", e["flags"] | 0x800
        elif k == 22:
            e["name_len_delta"] = rng.choice([-1, 1])
        elif k == 23:
            e["data"] = e["data"] + b"\0"
        elif k == 24:
            entries.remove(e) if len(entries) > 1 else None
        else:
            e["name"] = e["name"].replace(b".xml", b".XML")
    return write_zip(entries, **kw)


def inflate_package(rng: random.Random) -> bytes:
    """One deflated part whose stream is damaged, with the checksum and size taken
    from what zlib makes of it — so only the decoder's own verdict can differ."""
    source = rng.choice([p for _, p in _parts(rng)] + [bytes(rng.randrange(256) for _ in range(rng.randint(0, 400)))])
    stream = bytearray(_deflate(source, rng))
    for _ in range(rng.randint(1, 4)):
        k = rng.randrange(4)
        if k == 0 and stream:
            stream[rng.randrange(len(stream))] ^= 1 << rng.randrange(8)
        elif k == 1 and stream:
            del stream[rng.randrange(len(stream)):]
        elif k == 2:
            stream += bytes(rng.randrange(256) for _ in range(rng.randint(1, 4)))
        elif k == 3 and len(stream) > 3:
            stream[rng.randrange(3)] = rng.randrange(256)
    d = zlib.decompressobj(-15)
    try:
        out = d.decompress(bytes(stream), 1 << 20)
    except zlib.error:
        out = source
    size = len(out) + rng.choice([0, 0, 0, -1, 1])
    part = {"name": b"word/document.xml", "data": bytes(stream), "crc": zlib.crc32(out), "size": max(size, 0), "method": 8, "flags": 0}
    return write_zip([part] + [entry(n, p, rng, method=0) for n, p in _parts(rng) if n != "word/document.xml"])


def damaged_package(rng: random.Random, base: list[bytes]) -> bytes:
    """A real package, damaged the way files get damaged: flipped bits, cut short."""
    data = bytearray(rng.choice(base))
    k = rng.randrange(3)
    if k == 0:
        for _ in range(rng.randint(1, 3)):
            data[rng.randrange(len(data))] ^= 1 << rng.randrange(8)
    elif k == 1:
        del data[rng.randrange(len(data)):]
    else:
        at = rng.randrange(len(data))
        data[at:at] = bytes(rng.randrange(256) for _ in range(rng.randint(1, 8)))
    return bytes(data)


def xml_package(rng: random.Random) -> bytes:
    """A readable package whose XML carries one of the causes, or is broken."""
    parts = dict(_parts(rng))
    name = rng.choice([n for n in parts if n.endswith(".xml")])
    x = parts[name]
    for _ in range(rng.randint(1, 3)):
        x = rng.choice(XML_EDITS)(x)
    parts[name] = x
    return fixture_pack({k: v for k, v in parts.items()})


XML_EDITS = [
    lambda x: x.replace(b"<w:cs/>", b"", 1),
    lambda x: x.replace(b'w:val="15"', b'w:val="14"', 1),
    lambda x: x.replace(b"<w:b/><w:bCs/>", b"<w:bCs/><w:b/>", 1),
    lambda x: x.replace(b"<w:rPr>", b"<w:rPr><w:noProof/>", 1),
    lambda x: x.replace(b"?>", b"?><!DOCTYPE x>", 1),
    lambda x: x.replace(b'<w:t xml:space="preserve">', '<w:t xml:space="preserve">\u200b'.encode(), 1),
    lambda x: x.replace(b"<w:t", b"<w:t\xff", 1),
    lambda x: x.replace(b'encoding="UTF-8"', b'encoding="ISO-8859-1"', 1),
    lambda x: b"\xff\xfe" + x,
    lambda x: b"\xef\xbb\xbf" + x,
    lambda x: x.replace(b"</w:body>", b"", 1),
    lambda x: x.replace(b"<w:t", b"<x:t", 1),
    lambda x: x.replace(b'<w:t xml:space="preserve">', b'<w:t xml:space="preserve">&nbsp;', 1),
    lambda x: x.replace(b'w:bidi="th-TH"', b'w:bidi="ar-SA"', 1),
    lambda x: x.replace(b"TH Sarabun New", b"Symbol", 2),
    lambda x: x.replace(b'<w:t xml:space="preserve">', b'<w:t xml:space="preserve"><![CDATA[&]]>', 1),
    lambda x: x.replace(b"<w:p>", b"<w:p><!-- c --><?pi x?>", 1),
    lambda x: x.replace(b"<w:r>", b"<w:r>&#1;", 1),
    lambda x: x.replace(b"<w:r>", b"<w:r>&#x0E01;", 1),
    lambda x: x.replace(b'xmlns:w="', b'xmlns:q="', 1),
    lambda x: x.replace(b"<w:r>", b"<w:r><w:rPr><w:rFonts w:cs=\"Tahoma\"/></w:rPr>", 1),
    lambda x: x.replace(b"</w:r>", b"</w:r><w:r><w:t>x</w:t></w:r>", 1),
]


XML_ALPHABET = [
    b"<", b">", b"&", b";", b"\"", b"'", b"=", b"/", b"?", b"!", b"[", b"]", b"-", b" ", b"\r", b"\t", b"\n",
    b"#", b"x", b":", b"a", b"1", b"_", b".", b"\xc2\xa0", b"\xe0\xb8\x81", b"\x00", b"\x0b", b"\xef\xbf\xbe",
    b"]]>", b"<!--", b"-->", b"<![CDATA[", b"<?", b"?>", b"&#", b"&#x", b"&amp;", b"&lt", b"xmlns:", b"xml:",
    b"<!DOCTYPE", b"<?xml ", b"version", b"encoding", b"standalone", b"\xed\xa0\x80", b"\xf4\x90\x80\x80",
    b' xmlns:w="u"', b' xmlns=""', b' xmlns:xml="u"', b' xmlns:a=""', b' xmlns:xmlns="u"', b' xmlns:x="http://www.w3.org/XML/1998/namespace"', b' xmlns="http://www.w3.org/2000/xmlns/"',
    b' xmlns:xml="http://www.w3.org/XML/1998/namespace"', b' xml:lang="th"',
    b' xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"', b' a="1"', b' w:val="1"',
    b"&#x10FFFF;", b"&#xD800;", b"&#0;", b"&#65;", b"&#x9;", "ฯ".encode(), "๎".encode(), "·".encode(), "\u0300".encode(),
    "\U00010000".encode(), b"\xef\xbb\xbf", b"\x80", b"\xc0\xaf",
]


def xml_fuzz_package(rng: random.Random) -> bytes:
    """A package whose XML took a few byte-level edits from XML's own alphabet,
    so the two XML readers must agree on what is well-formed."""
    parts = dict(_parts(rng))
    name = rng.choice(["word/document.xml", "word/settings.xml", "word/styles.xml"])
    x = bytearray(parts[name])
    for _ in range(rng.randint(1, 3)):
        at = rng.randrange(len(x) + 1)
        k = rng.randrange(3)
        if k == 0:
            x[at:at] = rng.choice(XML_ALPHABET)
        elif k == 1:
            del x[at : at + rng.randint(1, 6)]
        else:
            x[at : at + 1] = rng.choice(XML_ALPHABET)
    parts[name] = bytes(x)
    return fixture_pack(parts)


# --- check: the rules by name ---------------------------------------------------------
#
# Each difference a campaign of tens of thousands of packages found, as the smallest
# package that shows it. The seeded corpus below reaches these rarely or never, so
# without them a guard could be removed from one implementation and the suite stay green.

_CL_ORDER = [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15]


def _dynamic_block(lit_lengths: dict[int, int], symbols: list[int]) -> bytes:
    """One final dynamic Huffman block (RFC 1951 §3.2.7) whose literal/length code
    has exactly `lit_lengths` — complete, incomplete or over-subscribed — and a
    one-bit distance code, followed by `symbols` in canonical codes."""
    out, acc, n = bytearray(), 0, 0

    def put(value: int, count: int) -> None:  # header fields: least significant bit first
        nonlocal acc, n
        for i in range(count):
            acc |= ((value >> i) & 1) << n
            n += 1
            if n == 8:
                out.append(acc)
                acc = n = 0

    def code(bits: str) -> None:  # Huffman codes: most significant bit first
        for c in bits:
            put(int(c), 1)

    put(1, 1), put(2, 2), put(0, 5), put(0, 5), put(14, 4)  # final, dynamic; 257 literal/length, 1 distance, 18 code-length codes
    cl = {0: "00", 1: "01", 2: "10", 18: "11"}
    for sym in _CL_ORDER[:18]:
        put(2 if sym in cl else 0, 3)
    lengths, i = [lit_lengths.get(s, 0) for s in range(257)] + [1], 0
    while i < len(lengths):
        run = 0
        while lengths[i] == 0 and i + run < len(lengths) and lengths[i + run] == 0 and run < 138:
            run += 1
        if run >= 11:
            code(cl[18]), put(run - 11, 7)
            i += run
        else:
            code(cl[lengths[i]])
            i += 1
    next_code, value = {}, 0
    for length in range(1, max(lit_lengths.values()) + 1):
        next_code[length] = value
        value = (value + sum(1 for n in lit_lengths.values() if n == length)) << 1
    codes = {}
    for sym in sorted(lit_lengths):
        length = lit_lengths[sym]
        codes[sym] = format(next_code[length], f"0{length}b")
        next_code[length] += 1
    for sym in symbols:
        code(codes[sym])
    return bytes(out + (bytes([acc]) if n else b""))


def _with_document_stream(stream: bytes, crc: int, size: int) -> bytes:
    entries = []
    for name, data in _parts(random.Random(0)):
        if name == "word/document.xml":
            entries.append({"name": name.encode(), "data": stream, "crc": crc, "size": size, "method": 8, "flags": 0})
        else:
            entries.append({"name": name.encode(), "data": data, "crc": zlib.crc32(data), "size": len(data), "method": 0, "flags": 0})
    return write_zip(entries)


def _with_document_edit(old: str, new: str) -> bytes:
    parts = good()
    assert parts["word/document.xml"].count(old) == 1
    parts["word/document.xml"] = parts["word/document.xml"].replace(old, new)
    return fixture_pack(parts)


UNREADABLE, NOT_XML = "entry cannot be read (corrupt data or checksum)", "XML is not well-formed"
_A, _END = ord("a"), 256


def named_packages() -> list[tuple[str, bytes, str | None]]:
    """(what the package shows, the package, the first finding's message or None)."""
    root = "<w:document "
    return [
        # ADR 0017 rule 9: zlib's strictness, and exactly the declared size
        ("literal/length code incomplete", _with_document_stream(_dynamic_block({_A: 1, _END: 2}, [_A, _A, _END]), zlib.crc32(b"aa"), 2), UNREADABLE),
        ("literal/length code over-subscribed",
         _with_document_stream(_dynamic_block({_A: 1, _END: 1, _A + 1: 2}, [_A, _A, _END]), zlib.crc32(b"aa"), 2), UNREADABLE),
        ("control: the same code complete decodes", _with_document_stream(_dynamic_block({_A: 1, _END: 1}, [_A, _A, _END]), zlib.crc32(b"aa"), 2),
         NOT_XML),
        ("control: a single one-bit literal/length code, which zlib allows",
         _with_document_stream(_dynamic_block({_END: 1}, [_END]), zlib.crc32(b""), 0), NOT_XML),
        ("inflates short of its declared size, checksum of the padded bytes",
         _with_document_stream(zlib.compress(b"ab")[2:-4], zlib.crc32(b"ab\0"), 3), UNREADABLE),
        # XML parts: what expat accepts, reading with namespaces [S31]
        ("the xml prefix bound to another namespace", _with_document_edit(root, root + 'xmlns:xml="urn:x" '), NOT_XML),
        ("another prefix bound to the xml namespace", _with_document_edit(root, root + 'xmlns:x="http://www.w3.org/XML/1998/namespace" '), NOT_XML),
        ("a prefix bound to the xmlns namespace", _with_document_edit(root, root + 'xmlns:y="http://www.w3.org/2000/xmlns/" '), NOT_XML),
        ("the xmlns prefix declared", _with_document_edit(root, root + 'xmlns:xmlns="urn:x" '), NOT_XML),
        ("control: the xml prefix bound to its own namespace", _with_document_edit(root, root + 'xmlns:xml="http://www.w3.org/XML/1998/namespace" '),
         None),
        ("a name with two colons", _with_document_edit("<w:body>", "<w:body><w:a:b/>"), NOT_XML),
        ("a colon in a processing instruction target", _with_document_edit("<w:body>", "<w:body><?a:b x?>"), NOT_XML),
        ("control: a processing instruction", _with_document_edit("<w:body>", "<w:body><?ab x?>"), None),
        ("a local name starting with -", _with_document_edit("<w:body>", "<w:body><w:-b/>"), NOT_XML),
        ("U+0E2F in a name: fifth-edition ranges allow it, expat does not", _with_document_edit("<w:body>", "<w:body><w:aฯ/>"), NOT_XML),
        ("control: U+0E01 in a name", _with_document_edit("<w:body>", "<w:body><w:aก/>"), None),
        # read without recursion in both: expat's depth, not a stack's
        ("control: elements nested 20,000 deep", _with_document_edit("<w:body>", "<w:body>" + "<w:customXml>" * 20000 + "</w:customXml>" * 20000),
         None),
        ("elements nested 20,000 deep, then malformed",
         _with_document_edit("<w:body>", "<w:body>" + "<w:customXml>" * 20000 + "</w:customXml>" * 20000 + "<bad"), NOT_XML),
        ("-- inside a comment", _with_document_edit("<w:body>", "<w:body><!-- a -- b -->"), NOT_XML),
        ("a comment ending --->", _with_document_edit("<w:body>", "<w:body><!-- a --->"), NOT_XML),
    ]


def package_corpus(seed: int, n: int) -> list[bytes]:
    rng = random.Random(seed)
    base = [p.read_bytes() for p in sorted(GOLDEN.glob("*.docx")) + sorted(FIXTURES.glob("*.docx"))]
    base.append(fixture_pack(good()))
    makers = [structural_package, inflate_package, xml_package, xml_fuzz_package, lambda r: damaged_package(r, base)]
    corpus = list(base) + [b"", b"not a zip", b"PK\x05\x06" + bytes(18)]
    corpus += [makers[i % len(makers)](rng) for i in range(n)]
    return corpus
