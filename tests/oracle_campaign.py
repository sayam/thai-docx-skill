# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""The large oracle campaigns behind tests/test_oracle.py, run by hand:

    python3 tests/oracle_campaign.py core 0 50000
    python3 tests/oracle_campaign.py gfm 0 50000

Prints one JSON line: documents compared, refusals by reason, accepted
divergences by category, and the seeds of anything unexplained. Not collected by
pytest (the name does not start with test_).
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "skills" / "thai-docx" / "scripts"), str(ROOT / "tests")]

import oracle  # noqa: E402
from thai_docx import markdown as md  # noqa: E402

BATCH = 2000


def core(start: int, count: int) -> dict:
    refused, unjustified, unexplained = collections.Counter(), [], []
    for batch_start in range(start, start + count, BATCH):
        seeds = range(batch_start, min(batch_start + BATCH, start + count))
        texts = [oracle.generate_core(s) for s in seeds]
        for seed, text, ref in zip(seeds, texts, oracle.cm_canon_many(texts), strict=True):
            try:
                doc = md.parse(text)
            except md.Unsupported as exc:
                refused[exc.what.split(";")[0][:60]] += 1
                if not any(e[0] == "html_block" for e in ref) and "html" not in repr(ref):
                    unjustified.append(seed)
                continue
            if oracle.ours_canon(doc, core=True) != ref:
                unexplained.append(seed)
    return {"corpus": "core", "reference": "commonmark.js 0.31.2", "seeds": [start, start + count],
            "refused": dict(refused), "unjustified_refusals": unjustified, "unexplained": unexplained}


def gfm(start: int, count: int) -> dict:
    oracle.gfm_task_presence_only[0] = True
    refused, known, unexplained = collections.Counter(), collections.Counter(), []
    for seed in range(start, start + count):
        text = oracle.generate_gfm(seed)
        try:
            doc = md.parse(text)
        except md.Unsupported as exc:
            refused[exc.what.split(";")[0][:60]] += 1
            continue
        ours, ref = oracle.ours_canon(doc), oracle.gfm_canon(text)
        if ours != ref:
            category = oracle.known_divergence(text, ours, ref)
            if category is None:
                unexplained.append(seed)
            else:
                known[category] += 1
    return {"corpus": "gfm", "reference": "cmark-gfm (cmarkgfm 2025.10.22)", "seeds": [start, start + count],
            "refused": dict(refused), "known_divergences": dict(known), "unexplained": unexplained}


if __name__ == "__main__":
    kind, start, count = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    print(json.dumps((core if kind == "core" else gfm)(start, count), ensure_ascii=False))
