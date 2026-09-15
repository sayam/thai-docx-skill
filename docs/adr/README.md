# Decision records

One row per record, in number order. `python tools/gates_doctor.py` holds this
index to the files beside it: a record missing from here, a row pointing at a
file that is gone, a repeated number or a gap in the numbering is red.

| id | decision | decided | status |
|---|---|---|---|
| 0001 | [Record every decision, where it came from, and its sources](0001-record-decisions-and-their-sources.md) | 2026-09-14 | accepted |
| 0002 | [One public repository per skill, with the skill in `skills/thai-docx/`](0002-one-public-repository-per-skill.md) | 2026-09-15 | accepted |
| 0003 | [License everything under MIT, and ship the notice inside the skill](0003-license-under-mit.md) | 2026-09-15 | accepted |
| 0004 | [Thai in .docx is complex script: five causes every output must avoid](0004-thai-is-complex-script-five-causes.md) | 2026-09-15 | accepted |
| 0005 | [Fix rendering with format attributes, never by changing content](0005-fix-rendering-with-attributes-never-content.md) | 2026-09-15 | superseded by 0016 |
| 0006 | [Use the skill whenever the document will contain Thai, and only then](0006-use-the-skill-when-the-document-contains-thai.md) | 2026-09-15 | accepted |
| 0007 | [Markdown is the only input, and one command builds and checks](0007-markdown-in-one-command-builds-and-checks.md) | 2026-09-15 | accepted |
| 0008 | [Two zero-dependency implementations with byte-identical output](0008-two-zero-dependency-implementations-byte-identical.md) | 2026-09-15 | accepted |
| 0009 | [Two modes: build at once with announced defaults, or interview first](0009-build-with-announced-defaults-or-grill-first.md) | 2026-09-15 | accepted |
| 0010 | [What Markdown v0.1 accepts, and what stops the build](0010-markdown-accepted-in-v0-1.md) | 2026-09-15 | accepted |
| 0011 | [Bundled scripts run with the agent's rights: eight limits](0011-scripts-run-with-the-agents-rights.md) | 2026-09-15 | accepted |
| 0012 | [XML checks are the proxy; five office applications are the release oracle](0012-xml-checks-are-the-proxy-office-apps-the-oracle.md) | 2026-09-15 | accepted |
| 0013 | [Commits are Conventional, signed off, and carry no assistant trailers](0013-commits-conventional-signed-no-assistant-trailers.md) | 2026-09-15 | accepted |
| 0014 | [Distribution: the Agent Skills specification, SkillsMP indexing, curated lists by hand](0014-distribution-spec-skillsmp-curated-lists.md) | 2026-09-15 | accepted |
| 0015 | [The parser is held to two reference implementations, under one character model](0015-parser-held-to-two-reference-implementations.md) | 2026-09-15 | accepted |
| 0016 | [Fix rendering with format attributes, never by changing content (restated)](0016-fidelity-transformations-restated.md) | 2026-09-15 | accepted |
