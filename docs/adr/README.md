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
| 0009 | [Two modes: build at once with announced defaults, or interview first](0009-build-with-announced-defaults-or-grill-first.md) | 2026-09-15 | superseded by 0019 |
| 0010 | [What Markdown v0.1 accepts, and what stops the build](0010-markdown-accepted-in-v0-1.md) | 2026-09-15 | superseded by 0022 |
| 0011 | [Bundled scripts run with the agent's rights: eight limits](0011-scripts-run-with-the-agents-rights.md) | 2026-09-15 | superseded by 0025 |
| 0012 | [XML checks are the proxy; five office applications are the release oracle](0012-xml-checks-are-the-proxy-office-apps-the-oracle.md) | 2026-09-15 | accepted |
| 0013 | [Commits are Conventional, signed off, and carry no assistant trailers](0013-commits-conventional-signed-no-assistant-trailers.md) | 2026-09-15 | accepted |
| 0014 | [Distribution: the Agent Skills specification, SkillsMP indexing, curated lists by hand](0014-distribution-spec-skillsmp-curated-lists.md) | 2026-09-15 | accepted |
| 0015 | [The parser is held to two reference implementations, under one character model](0015-parser-held-to-two-reference-implementations.md) | 2026-09-15 | accepted |
| 0016 | [Fix rendering with format attributes, never by changing content (restated)](0016-fidelity-transformations-restated.md) | 2026-09-15 | superseded by 0023 |
| 0017 | [The checker and the build read files by stated rules, not by a library's habits](0017-files-read-by-stated-rules.md) | 2026-09-15 | accepted |
| 0018 | [Users download the skill alone; contributors carry the gates and are held to them at merge](0018-users-get-the-skill-contributors-get-the-gates.md) | 2026-09-15 | accepted |
| 0019 | [Two modes: build at once with announced defaults, or nine questions as choices first (restated)](0019-grill-asks-eight-questions-as-choices.md) | 2026-09-15 | superseded by 0026 |
| 0020 | [Heading styles come from the front matter, as CSS-like declarations](0020-heading-styles-from-front-matter.md) | 2026-09-15 | accepted |
| 0021 | [Reports and theses: regions, a section per chapter, numbered captions and lists](0021-regions-sections-captions-and-lists.md) | 2026-09-16 | accepted |
| 0022 | [What Markdown v0.1 accepts, and what stops the build (restated)](0022-markdown-accepted-restated.md) | 2026-09-16 | accepted |
| 0023 | [Fix rendering with format attributes, never by changing content (restated with captions)](0023-fidelity-transformations-restated-again.md) | 2026-09-16 | accepted |
| 0024 | [Profiles are data: settings a user saves, exports and imports](0024-profiles-are-data-saved-and-shared.md) | 2026-09-16 | accepted |
| 0025 | [Bundled scripts run with the agent's rights: the limits, restated for profiles](0025-script-limits-restated-for-profiles.md) | 2026-09-16 | accepted |
| 0026 | [Two modes, and the script decides which: grill is the user's word, read (restated)](0026-grill-is-the-users-word-read-by-the-script.md) | 2026-09-16 | superseded by 0029 |
| 0027 | [Generated matter carries what an application would otherwise supply: list entries, and a font on every run](0027-lists-carry-entries-and-runs-name-their-font.md) | 2026-09-16 | accepted |
| 0028 | [Settings live in one registry, grouped by what they need; everything else is derived from it](0028-settings-in-one-registry-grouped-by-what-they-need.md) | 2026-09-16 | accepted |
| 0029 | [Grill from a profile and save as another: the interview is data, read by the script (restated)](0029-grill-from-a-profile-save-as-another.md) | 2026-09-16 | accepted |
