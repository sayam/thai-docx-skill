# Checking an existing .docx: the finding codes

Read this when `thai_docx check` has reported (SKILL.md, Check an existing .docx).

## Codes

Exit 0: no findings. Exit 1: findings in the user's file — the answer about their file, not a
defect in this skill. Exit 2: the file could not be read, is not a .docx, or was refused as
unsafe. A path that cannot be read answers with `error`
("cannot read …: No such file or directory") and no findings — that is a name to fix,
not a damaged document. Explain each finding by its code, in the user's language:

| code | what is wrong | what the user sees |
|---|---|---|
| `1` | compatibility mode is not 15 | "Compatibility Mode" in Word's title bar; Thai lines break only at spaces |
| `2` | a run whose text is complex script is not marked so (`<w:cs/>`; `<w:cs w:val="0"/>` says it is not) — deleted text included. A Latin run carrying the mark is not a finding — `--force-cs-whole-doc` writes that on purpose | red squiggles under Thai words, Latin line breaking |
| `3` | proofing switched off (`<w:noProof/>`; one that says `w:val="0"` switches it on, and is not a finding) | squiggles gone, but Thai lines no longer break inside words |
| `4` | one word split across two runs with the same formatting | odd gaps or breaks where formatting changed |
| `5` | a Latin property with no complex-script twin (`w:cs` font, `szCs`, `bCs`, `iCs`) — in a run, a style, a paragraph mark or a numbering level — or a Symbol-font bullet | Thai in the wrong font or size, bold not bold, broken bullets |
| `invisible` | a character a reader cannot see: the zero-width five by name, and any other format character (a soft hyphen, a direction mark) or noncharacter by its code point | words that do not wrap, text that searches wrongly or reads in the wrong direction |
| `order` | formatting properties in an order the schema does not allow: a run's, a paragraph's or its mark's, a section's, a table's, a row's or a cell's, a style's, a numbering level's, the settings' | a setting silently ignored, e.g. bold or size not applied |
| `package`, `doctype`, `size` | the file is damaged, not a Word document, saved as Strict Open XML (ask the user to save it again as Word Document), a part is not UTF-8 (a part in UTF-16 is refused before it is read), or refused as unsafe (exit 2) | the file may not open at all |

`warnings` never fail the check (exit 0 with warnings is a pass): today there is one, a
complex-script font the checker does not know to carry Thai glyphs. Pass it on — the Thai may
show in a substitute.

`counts` says how many run properties carry the Thai complex-script language
(`thai_language_runs`). Its absence is not a finding: the language is `--thai-language`'s to write
(ADR 0038), and a document without it takes the language from the reader's machine.

The check reads every part of the package that holds text a reader sees: the body, the
comments, the footnotes and endnotes, and each header and footer. It finds them as Word does,
by the package's relationships, not by their file names — a first-page header may be
`headerFirst.xml`. A finding names the part it is in, so say which one when the answer is not
the body. Formatting that a tracked change says a style once had is history, and not checked.

This reports. To fix a file whose content the user does not have, `repair` writes a new one
with every finding gone but `4`, `invisible` and a compatibility mode the file never declared, which it reports — [repair.md](repair.md).
When they do have the content, rebuilding from Markdown fixes everything, and is the better
move.
