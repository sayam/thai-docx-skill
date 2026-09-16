# Checking an existing .docx: the finding codes

Read this when `thai_docx check` has reported (SKILL.md, Check an existing .docx).

## Codes

Exit 0: no findings. Exit 1: findings. Exit 2: not a readable .docx (or refused as
unsafe). Explain each finding by its code, in the user's language:

| code | what is wrong | what the user sees |
|---|---|---|
| `1` | compatibility mode is not 15 | "Compatibility Mode" in Word's title bar; Thai lines break only at spaces |
| `2` | a run with text is not marked complex script (`<w:cs/>`, `w:bidi="th-TH"`) | red squiggles under Thai words, Latin line breaking |
| `3` | proofing switched off (`<w:noProof/>`) | squiggles gone, but Thai lines no longer break inside words |
| `4` | one word split across two runs with the same formatting | odd gaps or breaks where formatting changed |
| `5` | a Latin property with no complex-script twin (`w:cs` font, `szCs`, `bCs`, `iCs`), or a Symbol-font bullet | Thai in the wrong font or size, bold not bold, broken bullets |
| `invisible` | zero-width or other invisible characters in the text | words that do not wrap, text that searches wrongly |
| `order` | formatting properties in an order the schema does not allow | a setting silently ignored, e.g. bold or size not applied |
| `package`, `doctype`, `size` | the file is damaged, not a Word document, or refused as unsafe (exit 2) | the file may not open at all |

This version reports; it does not repair. If the user wants the document fixed and
has its content, rebuild it from Markdown with this skill.
