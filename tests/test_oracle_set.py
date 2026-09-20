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
    # the five applications open the documents the skill hands over ready to use; the variant
    # built with --auto-numbering is made for Word and is opened there alone (ADR 0036)
    assert sum(len(v[-1]) for v in oracle_set.VARIANTS.values()) == len(results) == 4 * 5 + 1
    assert oracle_set.VARIANTS["sample-auto"][-1] == oracle_set.WORD == ("word365_windows",)
    names = sorted(p.name for p in tmp_path.glob("*.docx"))
    assert names == sorted(f"{v}-{a}.docx" for v, spec in oracle_set.VARIANTS.items() for a in spec[-1])
    checklist = (tmp_path / "CHECKLIST.md").read_text(encoding="utf-8")
    for variant, (_source, _flags, golden, _about, applications) in oracle_set.VARIANTS.items():
        golden_bytes = (ROOT / "tests" / "golden" / f"{golden}.docx").read_bytes()
        for application in applications:
            assert (tmp_path / f"{variant}-{application}.docx").read_bytes() == golden_bytes, (variant, application)
        assert f"## {variant}" in checklist and hashlib.sha256(golden_bytes).hexdigest() in checklist
    for r in results:
        assert r["ok"] and r["findings"] == []
        # the sample's literal LaTeX warns; sample-layout's --toc beside the thesis's own
        # <!-- toc --> writes a second table of contents, and says so (ADR 0028)
        said = [w["message"] for w in r["warnings"]]
        if r["variant"] == "sample-basic":
            # the fixture goes from level 2 to level 5 on purpose, to exercise both in one file;
            # the build says so, and the bytes are the goldens', so the fixture stays as it is
            assert said and all("LaTeX" in m or "a heading of level 5 follows one of level 2" in m for m in said)
            assert sum("heading of level" in m for m in said) == 1
        elif r["variant"] == "sample-layout":
            assert said == ["--toc: the document places a table of contents with <!-- toc --> as well, so it now has two"]
        else:
            assert said == []
    assert all(a in checklist for a in oracle_set.APPLICATIONS)
