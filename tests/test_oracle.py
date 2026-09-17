# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""The parser held to two reference implementations over generated documents
(ADR 0015): commonmark.js on CommonMark-only text, cmark-gfm on GFM text.

Every document is generated from a fixed seed, so a failure names a seed that
reproduces it. A mismatch passes only when known_divergence() names it; a
refusal passes only when the reference shows the raw HTML the build refuses.
The large campaigns behind these samples are recorded in docs/evidence/.
"""

from __future__ import annotations

import os
import shutil

import pytest

import oracle
from thai_docx import markdown as md

CORE_DOCS = 1500
GFM_DOCS = 1500


def _need_node():
    if shutil.which("node") and (oracle.CM_CANON.parent / "node_modules" / "commonmark").exists():
        return
    if os.environ.get("CI"):
        pytest.fail("Node.js and `npm ci` in tests/js are required in CI")
    pytest.skip("Node.js or tests/js/node_modules missing (run `npm ci` in tests/js)")


def test_core_dialect_matches_commonmark_js():
    _need_node()
    texts = [oracle.generate_core(seed) for seed in range(CORE_DOCS)]
    refs = oracle.cm_canon_many(texts)
    unexplained, unjustified = [], []
    for seed, (text, ref) in enumerate(zip(texts, refs, strict=True)):
        assert not isinstance(ref, dict), f"seed {seed}: commonmark.js failed: {ref}"
        try:
            doc = md.parse(text)
        except md.Unsupported:
            if not any(entry[0] == "html_block" for entry in ref) and "html" not in repr(ref):
                unjustified.append(seed)
            continue
        if oracle.ours_canon(doc, core=True) != ref:
            unexplained.append(seed)
    assert unjustified == [], f"refused documents the reference read without raw HTML: seeds {unjustified[:10]}"
    assert unexplained == [], f"differs from commonmark.js: seeds {unexplained[:10]}"


def test_gfm_dialect_matches_cmark_gfm():
    oracle.gfm_task_presence_only[0] = True
    try:
        unexplained = []
        for seed in range(GFM_DOCS):
            text = oracle.generate_gfm(seed)
            try:
                doc = md.parse(text)
            except md.Unsupported:
                continue
            ours, ref = oracle.ours_canon(doc), oracle.gfm_canon(text)
            if ours != ref and oracle.known_divergence(text, ours, ref) is None:
                unexplained.append(seed)
        assert unexplained == [], f"differs from cmark-gfm outside the named divergences: seeds {unexplained[:10]}"
    finally:
        oracle.gfm_task_presence_only[0] = False


@pytest.mark.parametrize("text,checked", [("- [ ] a", False), ("- [x] a", True), ("- [X] a", True), ("- [ ] a [x]", False)])
def test_task_checked_state(text, checked):
    # cmark-gfm marks "- [ ] a [x]" checked; the oracle compares presence only, so
    # the checked state is held here
    assert md.parse(text).blocks[0]["items"][0][0]["inlines"][0] == {"t": "task", "checked": checked}
