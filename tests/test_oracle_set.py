# SPDX-FileCopyrightText: 2026 Sayam Sriphua
# SPDX-License-Identifier: MIT
"""tools/oracle_set.py: the documents a release is opened in (ADR 0012) — one per
application, the same bytes as the goldens, and a checklist that names them all."""

from __future__ import annotations

import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import oracle_set  # noqa: E402


def test_every_variant_for_every_application_is_its_golden(tmp_path):
    results = oracle_set.write(tmp_path)
    assert len(results) == len(oracle_set.VARIANTS) * len(oracle_set.APPLICATIONS) == 20
    names = sorted(p.name for p in tmp_path.glob("*.docx"))
    assert names == sorted(f"{v}-{a}.docx" for v in oracle_set.VARIANTS for a in oracle_set.APPLICATIONS)
    checklist = (tmp_path / "CHECKLIST.md").read_text(encoding="utf-8")
    for variant, (_source, _flags, golden, _about) in oracle_set.VARIANTS.items():
        golden_bytes = (ROOT / "tests" / "golden" / f"{golden}.docx").read_bytes()
        for application in oracle_set.APPLICATIONS:
            assert (tmp_path / f"{variant}-{application}.docx").read_bytes() == golden_bytes, (variant, application)
        assert f"## {variant}" in checklist and hashlib.sha256(golden_bytes).hexdigest() in checklist
    for r in results:
        assert r["ok"] and r["findings"] == []
        # the sample's literal LaTeX warns; sample-layout's --toc beside the thesis's own
        # <!-- toc --> writes a second table of contents, and says so (ADR 0028)
        said = [w["message"] for w in r["warnings"]]
        if r["variant"] == "sample-basic":
            assert said and all("LaTeX" in m for m in said)
        elif r["variant"] == "sample-layout":
            assert said == ["--toc: the document places a table of contents with <!-- toc --> as well, so it now has two"]
        else:
            assert said == []
    assert all(a in checklist for a in oracle_set.APPLICATIONS)
