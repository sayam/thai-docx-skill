# 2026-09-22 — What Word writes when a person types Thai and English: eight rules, read off the file

What this proves: a document typed by hand in Microsoft Word 365 for Windows, covering Thai alone,
English alone, the two mixed three different ways, and digits among Thai, **carries no red underline
anywhere** — and its `word/document.xml` and `word/styles.xml` say exactly how it manages that.
Eight rules were read off it. They are the reference that
[ADR 0039](../adr/0039-complex-script-is-marked-where-it-is.md) copies, and the answer to
`2026-09-22-word-365-windows-on-the-release-bytes.md` §3, where this project's own files underline
correctly spelled English.

This follows the project's own principle for questions of this kind: what a document typed in Word
*visibly* does is the target, and where our output differs the difference has to be justified or
removed.

Environment: Microsoft Word 365 for Windows on the maintainer's Windows machine, which has Thai
among its languages. The maintainer typed five paragraphs from a written script, in TH Sarabun New
at 16 pt, and saved twice: `word-reference.docx` (14,046 bytes, md5 `cfbb3ae772cb`, application
`Microsoft Office Word`), and `word-reference-bold.docx` (14,104 bytes, md5 `1797bd324a5f`) after
making three words bold by selecting each word without its surrounding spaces. Both were read with
a short script that walks the runs and prints each one's text and `w:rPr`; the screenshots the
maintainer took are what establishes there are no underlines. Content typed by the maintainer, not
generated.

## 1. The languages are declared once, at the document, and never on a run

```xml
<!-- styles.xml · docDefaults -->
<w:rPr>
  <w:rFonts w:asciiTheme="minorHAnsi" w:eastAsiaTheme="minorHAnsi"
            w:hAnsiTheme="minorHAnsi" w:cstheme="minorBidi"/>
  <w:kern w:val="2"/><w:sz w:val="24"/><w:szCs w:val="30"/>
  <w:lang w:val="en-US" w:eastAsia="en-US" w:bidi="th-TH"/>
</w:rPr>
```

```xml
<!-- settings.xml -->
<w:themeFontLang w:val="en-US" w:bidi="th-TH"/>
```

**`w:lang` appears on no run at all** — zero occurrences in the whole document. This project writes
it on every run: 75 of them in `sample-basic`.

## 2. `docDefaults` carries no `<w:cs/>`

There is nothing to inherit, so a run that omits the element is not complex script. This is what
makes rule 5 workable.

## 3. Runs are split at script boundaries, and only the complex-script ones are marked

| the paragraph | runs | `<w:cs/>` |
|---|---|---|
| Thai only | 1 | **yes** |
| English only | 1 | **no** |
| `ข้อความผสม Word และ Markdown ในย่อหน้าเดียวกัน` | **5** | 3 Thai yes · 2 Latin no |
| `เอกสารภาษาไทย, Markdown, Office Open XML, การตัดบรรทัด, complex script` | **4** | 2 Thai yes · 2 Latin no |
| `กลุ่มตัวอย่างจำนวน 120 ฉบับ และ 98.3 เปอร์เซ็นต์` | **5** | 3 Thai yes · **2 numeric no** |

This splitting is over and above the splitting that formatting already forces. Nothing in the text
of these paragraphs changes format; the boundaries are script boundaries alone.

**A run that is not complex script says so by omission, never by `<w:cs w:val="0"/>`.** The
negative form does not appear in the file.

## 4. Arabic digits are not complex script

The fifth paragraph contains no Latin letter whatsoever, and Word still splits it into five runs.
`'120 '` and `'98.3 '` carry no `<w:cs/>`. So the test Word applies is the script of the characters,
not "does this run contain letters".

## 5. A space takes the script of what precedes it; punctuation goes to the Latin side

| case | where the character landed |
|---|---|
| space between Thai and Latin (`ข้อความผสม Word`) | with the **preceding** run → `'ข้อความผสม '`, marked |
| space between Latin and Thai (`'Word'` then `' '`) | with the **preceding** run → unmarked |
| space after digits (`120 ฉบับ`) | with the digits → `'120 '`, unmarked |
| comma between Thai and Latin (`เอกสารภาษาไทย, Markdown`) | starts the **following** Latin run → `', Markdown, '` |

The space behaves as a neutral character taking the script of the strong character before it; the
comma behaves as a character that is simply not complex script, so it joins the Latin side whether
it follows Thai or not. **Only these two neutral characters were measured.** Brackets, dashes and
quotation marks were not typed, and this record does not state a rule for them.

## 6. Bold is written on both sides, always

From the second file, where the maintainer made three words bold:

| run | `w:rPr` |
|---|---|
| `'English'`, Latin, bold | `<w:b/><w:bCs/>` — **no `<w:cs/>`** |
| `'ผสม'`, Thai, bold | `<w:b/><w:bCs/><w:cs/>` |
| `'Word'`, Latin, bold | `<w:b/><w:bCs/>` |

**Word writes `w:b` and `w:bCs` together whether or not the run is complex script.** This is what
makes rule 5 safe to adopt: taking `<w:cs/>` off a Latin run does not lose its bold, because `w:b`
governs the Latin side and this project already writes the pair —
`<w:b/><w:bCs/><w:cs/><w:lang w:val="en-US"/>` is what `sample-text`'s bold English run holds today.

Selecting the word without its trailing space is what produced separate runs for the spaces, which
is how rule 5's neutral-character behaviour became visible at all.

## 7. The eight rules, together

1. `docDefaults` carries no `<w:cs/>`, and carries
   `<w:lang w:val="en-US" w:eastAsia="en-US" w:bidi="th-TH"/>`.
2. `settings.xml` carries `<w:themeFontLang w:val="en-US" w:bidi="th-TH"/>`.
3. No `w:lang` on any run.
4. Runs split at every boundary between complex script and not.
5. Complex-script runs carry `<w:cs/>`; the others carry nothing — never `<w:cs w:val="0"/>`.
6. Digits and ASCII punctuation are not complex script.
7. A neutral character takes the script of the strong character before it.
8. `w:b` and `w:bCs` are written together whatever the run's script.

## 8. Three layers between this and what we write

| | Word, typed | this project, today |
|---|---|---|
| `<w:cs/>` in `docDefaults` | **no** | yes |
| `w:lang` on runs (`sample-basic`) | **0** | 75 |
| `<w:cs/>` on runs (`sample-basic`) | **9**, the Thai ones | **75**, all of them |
| runs split by script | **yes** | no — runs hold Thai and Latin together |
| `w:bidi="th-TH"` declared | **yes, at `docDefaults` and `themeFontLang`** | no (ADR 0038 removed it) |

The last row is the one rule that cannot simply be copied, because `w:bidi="th-TH"` is what makes
WPS Writer misplace SARA AM. Where exactly WPS trips over it is measured separately, in
`2026-09-22-where-wps-trips-over-the-thai-language.md`, and that measurement is why ADR 0039 adopts
rules 1 and 3 through 8 and leaves rule 2 unadopted for now.

## 9. Not proved here

- **What Word does with Thai and Latin adjacent with nothing between them.** Every mixed paragraph
  typed here has a space or a comma at the boundary.
- **Neutral characters other than the space and the comma.**
- **Italic.** Inferred from bold, not measured; `w:i`/`w:iCs` were not in either file.
- **Any application other than Word.** These are Word's rules, adopted because ADR 0012 makes Word
  365 for Windows the reference, not because they are the specification's.

The two documents and the reading script are the maintainer's working copy and are not part of the
repository; they are kept at `.local/work/2026-09-22-word-reference/`, and
`python3 read-reference.py word-reference.docx` prints the reading again.
