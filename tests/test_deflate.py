# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""A deflate of this project's own: it inflates back with every reader, and both
implementations write the same bytes (gate `deflate-is-defined-not-borrowed`).
"""

from __future__ import annotations

import base64
import pathlib
import random
import zipfile
import zlib

import pytest

from parity import run_js
from thai_docx import deflate as df

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def _styles() -> bytes:
    with zipfile.ZipFile(FIXTURES / "legacy-python-docx-default.docx") as z:
        return z.read("word/styles.xml")


def _random(n: int, seed: int = 7) -> bytes:
    rng = random.Random(seed)
    return bytes(rng.randrange(256) for _ in range(n))


CASES = {
    "nothing": b"",
    "one byte": b"a",
    "shorter than the shortest match": b"ab",
    "one repeated pair": b"ab" * 5000,
    "every byte, twenty times": bytes(range(256)) * 20,
    "a run longer than the longest match": b"\x00" * 100000,
    "this project's own source": (ROOT / "skills" / "thai-docx" / "scripts" / "thai_docx" / "check.py").read_bytes(),
    "a styles part from another program": _styles(),
    "bytes with no pattern in them": _random(5000),
    "a match that reaches the end": b"abcdefgh" + b"x" * 100 + b"abcdefgh",
}


@pytest.mark.parametrize("name", list(CASES), ids=list(CASES))
def test_zlib_inflates_what_this_deflates(name):
    """The reader that matters is the one in Word; zlib is the one this can test against."""
    data = CASES[name]
    assert zlib.decompress(df.deflate(data), -15) == data


@pytest.mark.parametrize("name", list(CASES), ids=list(CASES))
def test_both_implementations_compress_to_the_same_bytes(name):
    data = CASES[name]
    mine = df.deflate(data)
    theirs = run_js({"op": "deflate", "cases": [base64.b64encode(data).decode()]})[0]
    assert "crash" not in theirs, theirs
    assert base64.b64decode(theirs["bytes"]) == mine


def test_the_skills_own_reader_inflates_it_too():
    """The JavaScript implementation reads packages with its own inflate; what this writes
    has to pass through it as well, or a file repaired by one could not be read by the other."""
    data = _styles()
    out = run_js({"op": "roundtrip", "cases": [base64.b64encode(data).decode()]})[0]
    assert "crash" not in out, out
    assert base64.b64decode(out["bytes"]) == data


def test_it_is_worth_doing_at_all():
    """Not the smallest — defined. Within half again of zlib on the part that mattered."""
    data = _styles()
    mine, theirs = len(df.deflate(data)), len(zlib.compress(data, 6)) - 6
    assert mine < len(data) // 20, (mine, len(data))
    assert mine < theirs * 1.5, (mine, theirs)


def test_bytes_with_no_pattern_are_not_made_much_worse():
    """Nothing compresses random bytes; a compressor that doubles them would be a bug. The
    packer stores a part when compressing it does not make it smaller."""
    data = _random(5000)
    assert len(df.deflate(data)) < len(data) * 1.1
