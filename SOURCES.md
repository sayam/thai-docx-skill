# Sources

Everything a record leans on from outside this repository: a document, a
standard, a paper, a conversation, an incident. A record cites a source by its
id (`[S1]`). An id is never reused — a source that no longer applies is struck
through, not deleted, so an old record still resolves to what it meant.

Prefer a DOI or a pinned version over a bare link: a page that changes under a
citation makes the record say something it did not.

| id | source | where | accessed | cited by |
|---|---|---|---|---|
| S1 | verifiable-gates 0.10.0 — the ADR index check (`adr-index-complete`) and the practice that a gate is proved in both directions | doi:10.5281/zenodo.22103110 · https://pypi.org/project/verifiable-gates/0.10.0/ | 2026-09-14 | 0001, 0002, 0012 |
| S2 | Diagnosis of Thai .docx rendering, Claude Design session, 2026-09-14 — handoff kept verbatim | `docs/handoff/2026-09-14-claude-design.md` | 2026-09-14 | 0004, 0005, 0006, 0009, 0014, 0016, 0019, 0023 |
| S3 | Agent Skills specification | https://agentskills.io/specification | 2026-09-14 | 0002, 0003, 0006, 0007, 0011, 0014, 0018 |
| S4 | skills-ref 0.1.1 — reference validator for Agent Skills; installs the `agentskills` command ("demonstration purposes only") | https://pypi.org/project/skills-ref/0.1.1/ | 2026-09-14 | 0014 |
| S5 | SkillsMP FAQ — "How do I submit my skill?" (auto-indexing, daily sync, topics) | https://skillsmp.com/docs/faq | 2026-09-14 | 0002, 0011, 0014 |
| S6 | Awesome Claude Skills (awesome-skills.com), curated by Ocean Path Ventures — no submission form on the site | https://awesome-skills.com | 2026-09-14 | 0002, 0014 |
| S7 | ECMA-376 Office Open XML File Formats, 5th edition, Part 1 (WordprocessingML) | https://ecma-international.org/publications-and-standards/standards/ecma-376/ | 2026-09-15 | 0004, 0021 |
| S8 | CommonMark Spec 0.31.2 — soft line breaks; Unicode punctuation (P and S categories) | https://spec.commonmark.org/0.31.2/ | 2026-09-15 | 0005, 0010, 0015, 0016, 0020, 0022, 0023 |
| S9 | GitHub Flavored Markdown Spec, version 0.29-gfm (2019-04-06) | https://github.github.com/gfm/ | 2026-09-15 | 0010, 0015, 0022 |
| S10 | GitHub Docs — basic writing and formatting syntax, footnotes | https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax | 2026-09-15 | 0010, 0022 |
| S11 | Claude Help Center — create and edit files with Claude (code execution, network egress settings) | https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude | 2026-09-14 | 0008 |
| S12 | Claude Platform docs — code execution tool (Python 3.11, no network, no runtime installs) | https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool | 2026-09-14 | 0008, 0010, 0022 |
| S13 | Claude Code docs — setup (system requirements, native installer) | https://code.claude.com/docs/en/setup | 2026-09-14 | 0008 |
| S14 | OpenAI — build skills for Codex (skill discovery); openai/codex distribution | https://learn.chatgpt.com/docs/build-skills · https://github.com/openai/codex | 2026-09-14 | 0008 |
| S15 | Gemini CLI docs — Agent Skills | https://geminicli.com/docs/cli/skills/ | 2026-09-14 | 0008 |
| S16 | Gemini Apps Help — skills (uploads; `.py` and `.sh` scripts only; no external requests) | https://support.google.com/gemini/answer/17094296 | 2026-09-14 | 0008, 0010, 0022 |
| S17 | Third-party copy of the Claude Design system prompt (`run_script`: async JavaScript) — **not confirmed by Anthropic** | https://gist.github.com/hqman/f46d5479a5b663c282c94faa8be866de | 2026-09-14 | 0008 |
| S18 | anthropics/skills — the `docx` skill (docx via npm, Python checking scripts) | https://github.com/anthropics/skills/blob/main/skills/docx/SKILL.md | 2026-09-14 | 0006, 0008 |
| S19 | Regulation (EU) 2016/679 (GDPR), Article 5(1)(c) — data minimisation | https://eur-lex.europa.eu/eli/reg/2016/679/oj | 2026-09-15 | 0011 |
| S20 | Personal Data Protection Act B.E. 2562 (2019), Thailand — Government Gazette No. 136 Chapter 69 Gor, 27 May 2019 | https://mdes.go.th/law/detail/3577-Personal-Data-Protection-Act-B-E--2562--2019- | 2026-09-15 | 0011 |
| S21 | verifiable-gates 0.10.0 — `conventional-commits` rule and `tools/lint_commits.py` | `tools/lint_commits.py` · https://pypi.org/project/verifiable-gates/0.10.0/ | 2026-09-15 | 0013 |
| S22 | The MIT License | https://opensource.org/license/mit | 2026-09-15 | 0003 |
| S23 | Developer Certificate of Origin 1.1 | https://developercertificate.org/ | 2026-09-15 | 0013 |
| S24 | commonmark.js 0.31.2 — the CommonMark reference implementation (BSD-2-Clause) | npm `commonmark@0.31.2`, integrity sha512-2fRLTyb9r/2835k5cwcAwOj0DEc44FARnMp5veGsJ+mEAZdi52sNopLu07ZyElQUz058H43whzlERDIaaSw4rg== · https://github.com/commonmark/commonmark.js | 2026-09-15 | 0015 |
| S25 | cmark-gfm, GitHub's Markdown renderer, as packaged by cmarkgfm 2025.10.22 | https://pypi.org/project/cmarkgfm/2025.10.22/ · https://github.com/github/cmark-gfm | 2026-09-15 | 0015 |
| S26 | CPython `html.entities.html5` — the HTML5 named character references (Python 3.13) | https://docs.python.org/3.13/library/html.entities.html | 2026-09-15 | 0015 |
| S27 | PKWARE .ZIP File Format Specification (APPNOTE.TXT) 6.3.10 — end of central directory records §4.3.14–4.3.16, zip64 extra field §4.5.3 | https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT | 2026-09-15 | 0017 |
| S28 | RFC 1951 — DEFLATE Compressed Data Format Specification version 1.3 | https://www.rfc-editor.org/rfc/rfc1951 | 2026-09-15 | 0017 |
| S29 | zlib `inftrees.c` — "check for an over-subscribed or incomplete set of lengths" | https://github.com/madler/zlib/blob/master/inftrees.c | 2026-09-15 | 0017 |
| S30 | Python 3.11 documentation — `pathlib.Path.resolve()`: "If an infinite loop is encountered along the resolution path, RuntimeError is raised." | https://docs.python.org/3.11/library/pathlib.html | 2026-09-15 | 0017 |
| S31 | Expat, the XML parser behind `xml.etree.ElementTree` — behaviour measured, not transcribed (`tools/measure_xml_names.py`) | https://github.com/libexpat/libexpat · https://docs.python.org/3/library/pyexpat.html | 2026-09-15 | 0017 |
| S32 | GitHub Docs — About forks: "Forks are repositories that start as copies of another repository, called the upstream repository." | https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-forks | 2026-09-15 | 0018 |
| S33 | Git documentation — gitattributes, `export-ignore`: "Files and directories with the attribute export-ignore won't be added to archive files." | https://git-scm.com/docs/gitattributes#_export_ignore | 2026-09-15 | 0018 |
| S34 | GitHub Docs — Downloading source code archives: snapshots "are generated by the git archive command" | https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives | 2026-09-15 | 0018 |
| S35 | GitHub Docs — About protected branches: required status checks "must have a successful, skipped, or neutral status"; required reviews; applying the rules to administrators | https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches | 2026-09-15 | 0018 |
| S36 | GitHub Docs — About code owners: owners are requested for review; "Require review from Code Owners"; the CODEOWNERS file "must be on the base branch of the pull request" | https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners | 2026-09-15 | 0018 |
| S37 | GitHub Docs — Approving a pull request with required reviews: "Pull request authors cannot approve their own pull requests." | https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/approving-a-pull-request-with-required-reviews | 2026-09-15 | 0018 |
| S38 | CSS 2.1, Full property table — the value grammars of `font-family`, `font-size`, `color`, `font-weight`, `font-style`, `text-align`, `margin-*`, `text-indent`, `line-height`, `page-break-before` | https://www.w3.org/TR/CSS21/propidx.html | 2026-09-15 | 0020 |
| S39 | CSS Text Decoration Module Level 3, W3C Candidate Recommendation Draft 2022-05-05 — `text-decoration: <'text-decoration-line'> \|\| <'text-decoration-style'> \|\| <'text-decoration-color'>`; styles `solid \| double \| dotted \| dashed \| wavy` | https://www.w3.org/TR/css-text-decor-3/ | 2026-09-15 | 0020 |
| S40 | Pandoc User's Guide — `table_captions`: "A caption is a paragraph beginning with the string `Table:` (or `table:` or just `:`), which will be stripped off. It may appear either before or after the table."; `implicit_figures`: an image alone in a paragraph takes its alt text as the caption | https://pandoc.org/MANUAL.html | 2026-09-16 | 0021 |
