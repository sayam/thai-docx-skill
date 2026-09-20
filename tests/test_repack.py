# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""Writing a package back the way it came, so a repair can change one part and leave
everything else exactly as the user handed it over (ADR 0037; gate
`repack-keeps-what-it-did-not-write`).
"""

from __future__ import annotations

import base64
import io
import pathlib
import zipfile

import pytest

from parity import run_js
from thai_docx import package as pk

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGES = sorted((ROOT / "tests" / "golden").glob("*.docx")) + sorted((ROOT / "tests" / "fixtures").glob("*.docx"))


def read_all(b: bytes) -> dict[str, bytes]:
    return {e.name: pk.read(b, e) for e in pk.entries(b)}


@pytest.mark.parametrize("path", PACKAGES, ids=lambda p: p.name)
def test_a_package_written_back_unchanged_is_the_same_bytes(path):
    """The strongest form of "everything untouched comes through byte for byte": change
    nothing, and the file that comes out is the file that went in — for this project's own
    output and for the two packages other generators wrote."""
    b = path.read_bytes()
    assert pk.repack(b, pk.entries(b), {}) == b


def test_a_rewritten_part_is_compressed_and_the_rest_keeps_its_own_bytes():
    """What a repair does: one part rewritten and compressed by this project's own deflate,
    every other entry's compressed bytes copied without being touched."""
    src = ROOT / "tests" / "fixtures" / "legacy-python-docx-default.docx"
    b = src.read_bytes()
    before = pk.entries(b)
    new_xml = pk.read(b, next(e for e in before if e.name == "word/document.xml")).replace(b"<w:p>", b"<w:p >")
    out = pk.repack(b, before, {"word/document.xml": new_xml})

    after = {e.name: e for e in pk.entries(out)}
    assert list(after) == [e.name for e in before], "the order of the entries is the order it was"
    rewritten = after["word/document.xml"]
    assert rewritten.method == 8 and rewritten.file_size == len(new_xml)
    assert rewritten.compress_size < rewritten.file_size
    assert pk.read(out, rewritten) == new_xml
    for e in before:
        if e.name != "word/document.xml":
            # not merely equal content: the very bytes, still compressed as they were
            assert pk.raw(out, after[e.name]) == pk.raw(b, e), e.name
            assert (after[e.name].method, after[e.name].crc, after[e.name].mod) == (e.method, e.crc, e.mod)
    # and the result is a package another reader opens, holding what the original held
    with zipfile.ZipFile(io.BytesIO(out)) as z:
        assert z.namelist() == zipfile.ZipFile(src).namelist()
        assert z.read("word/document.xml") == new_xml
        assert z.testzip() is None


def test_storing_everything_is_what_repair_must_not_do():
    """Why repack exists at all: the builder's packer stores every entry, which is right for
    a file made from nothing and would hand a user's own document back many times larger."""
    b = (ROOT / "tests" / "fixtures" / "legacy-python-docx-default.docx").read_bytes()
    ents = pk.entries(b)
    stored = pk.pack([(e.name, pk.read(b, e)) for e in ents])
    kept = pk.repack(b, ents, {})
    assert len(stored) > 20 * len(kept)
    assert len(kept) == len(b)
    # and with the largest part rewritten, the file stays about the size it was
    styles = next(e for e in ents if e.name == "word/styles.xml")
    again = pk.repack(b, ents, {"word/styles.xml": pk.read(b, styles)})
    assert len(again) < 1.3 * len(b), (len(again), len(b))


def test_repacking_a_repacked_package_changes_nothing():
    b = (ROOT / "tests" / "golden" / "sample-default.docx").read_bytes()
    once = pk.repack(b, pk.entries(b), {"word/document.xml": b"<x/>"})
    twice = pk.repack(once, pk.entries(once), {})
    assert twice == once


def test_a_name_the_package_does_not_hold_is_refused():
    """A typo would otherwise leave the file unchanged and say nothing."""
    b = (ROOT / "tests" / "golden" / "sample-default.docx").read_bytes()
    with pytest.raises(pk.PackageError) as exc:
        pk.repack(b, pk.entries(b), {"word/documnet.xml": b"<x/>"})
    assert "no entry named 'word/documnet.xml'" in str(exc.value)


@pytest.mark.parametrize("path", PACKAGES, ids=lambda p: p.name)
def test_both_implementations_write_the_same_package(path):
    """ADR 0008 holds here as everywhere: the same input, the same bytes."""
    b = path.read_bytes()
    replace = {"word/document.xml": b"<w:document/>"} if "word/document.xml" in read_all(b) else {}
    mine = pk.repack(b, pk.entries(b), replace)
    theirs = run_js({"op": "repack", "cases": [{
        "package": base64.b64encode(b).decode(),
        "replace": {k: base64.b64encode(v).decode() for k, v in replace.items()},
    }]})[0]
    assert "crash" not in theirs, theirs
    assert base64.b64decode(theirs["bytes"]) == mine
