# 0036 — The build writes every number, unless `--auto-numbering` asks the application to count (restated)

- Status: accepted
- Decided: 2026-09-19
- Supersedes: 0035
- Extends: [0027](0027-lists-carry-entries-and-runs-name-their-font.md) (generated matter carries
  what an application would otherwise supply), [0021](0021-regions-sections-captions-and-lists.md)
  (regions, captions and the three lists), [0012](0012-xml-checks-are-the-proxy-office-apps-the-oracle.md)
  (five applications, Word 365 for Windows the reference), [0028](0028-settings-in-one-registry-grouped-by-what-they-need.md)
  (a setting is one registry entry)

## Where it came from

[ADR 0035](0035-numbers-the-build-writes.md) wrote a document's numbers as text whenever it asked
for Thai digits or held regions, and left every other document to the application. It chose per
document, by a rule the user never saw.

On 2026-09-19 the maintainer opened `sample-options` — a thesis, in Thai digits — in Word 365 for
Windows, the reference application, as the first of the five before v0.2.0
([record](../evidence/2026-09-19-the-look-passes-the-edit-does-not.md)). Every item of the
checklist held: `บทที่ ๑`, `๑.๓.๒`, `ตารางที่ ๑-๑`, `รูปที่ ๒-๑`, `ตารางที่ A-๑`, the three lists
filled in with their page numbers, □ and ■, no squiggle under ordinary Thai, no Compatibility Mode. The verdict, in
the maintainer's words: *the look passes; the action fails.* A heading inserted in Word does not
renumber the ones after it, and Word is the application that does that best — in Arabic digits
and in Thai.

Two things followed from the same conversation:

- **Both documents are wanted, and they are different documents.** Most files this skill builds
  are asked of an assistant, read, and have a few words changed; their numbers are never touched
  again. Those must look the same wherever they are opened. A smaller number are taken into Word
  and worked on for weeks; those must renumber.
- **Which one a user gets must be the user's word, not a rule about Thai digits.** A report in
  Arabic digits deserves the same five-application guarantee as a thesis, and a thesis in Thai
  digits deserves Word's renumbering when its author asks for it. ADR 0035's rule gave neither.

## Decision

**One switch, for the whole document: `--auto-numbering`.**

| | without it — the default | with `--auto-numbering` |
|---|---|---|
| who counts | the build: every number is text | the application: numbering levels and fields |
| a heading's number | a run in the heading's paragraph | a multilevel list tied to the heading styles |
| an ordered list's marker | `๑.` and a tab, with the hanging indent | a numbering level |
| a caption's number | text beside its label | `STYLEREF 1 \s`, `-`, `SEQ <the label> \* ARABIC \s 1` |
| with `--thai-digits` | ๑ ๒ ๓ written | `thaiNumbers`, `SEQ … \* ThaiArabic` |
| in the five applications | the same in all five | right in Word; the others as recorded below |
| a reader inserts a chapter | renumbers by hand, or changes the Markdown and builds again | Word renumbers |

**The default is the written number**, in every document — Thai digits or Arabic, regions or none
— because it is the one that holds in all five applications, and rule 1 asks that a file be usable
as it leaves the skill, wherever it is opened.

**It stays one answer for the whole document, never a number here and a field there.** A document
that renumbers its headings but not its captions goes wrong silently the first time a reader
inserts a chapter — `ตารางที่ 1-1` sitting in chapter 2, with nothing to say so. That was ADR
0035's and it stands.

**What the build cannot know stays a field or a format in both**, because only a laid-out page has
it: page numbers (`PAGE`, `w:pgNumType`), footnote marks, and the page numbers a table of contents
shows after an application updates it. **A bullet stays a numbering level in both**: `•` is a
literal `w:lvlText`, and every application drew it.

**The three lists stay `TOC` fields that collect a style, in both.** A list of tables collects the
paragraphs in `Table Caption` with `\t`, not the `SEQ` fields with `\c`, so the same list works
whether the caption's number is text or a field, and LibreOffice reads it as its own
index-by-style.

**With `--auto-numbering` the result of every field is still written in**, so an application that
never updates fields shows `ตารางที่ ๑-๑` and not an empty caption (ADR 0027).

**A caption's counter is named after its label, and the label is written into the package.** Word
names the counter of a caption it inserts after the label chosen in its dialog, and keeps a label
the user makes in their own profile rather than in the file. A document that counted `SEQ Figure`
while Word counted `SEQ รูปที่` therefore handed a reader who inserted a figure a second count
starting at 1 beside the first (seen in Word 365 for Windows and Word on the web, 2026-09-20). So
the build names the counter after the label, and `word/settings.xml` carries a `<w:caption>` for
each label the document uses — its number format, its chapter number, and the side of the table or
figure it belongs on. In a document whose numbers are the build's own there is no such label: a
caption inserted there would count on its own beside numbers that are text, which is the
half-numbered document this record refuses.

**The name says what the user gets.** "Automatic numbering" is Word's own term for it. The two
documents are not called "ready to use" and "to edit": a file with written numbers can be edited
too, and a name that suggests otherwise would send people to the wrong one.

**The flag is said to have changed nothing** when the document holds no numbered heading, no
ordered list and no caption (ADR 0028) — then there is nothing to count, and no byte differs.

**The five-application contract of ADR 0012 covers the default**, the document the skill hands
over ready to use. A document built with `--auto-numbering` is made for Word: it is opened in the
reference application, and what the other four draw with it is recorded below and in
`references/numbering.md` rather than held to the contract. The release oracle says the same — the
`sample-auto` variant is built for Word 365 for Windows alone.

## What `--auto-numbering` draws outside Word, as measured

Only what has been seen is written here; `references/numbering.md` carries the same table for the
user, and is where a new measurement goes.

| application | what was seen | record |
|---|---|---|
| Word 365 for Windows, Word on the web | correct, Arabic and Thai digits | [2026-09-16](../evidence/2026-09-16-office-check-five-applications.md) |
| Word for macOS | correct; the number takes its heading's size | [2026-09-17](../evidence/2026-09-17-word-for-macos.md) |
| Google Docs | headings and captions numbered by chapter, correct; renumbering on edit not measured | [2026-09-16](../evidence/2026-09-16-office-check-five-applications.md) |
| LibreOffice Writer | `thaiNumbers` drawn as 1, 2, 3; `STYLEREF 1 \s` answers the chapter's *title* (`ตารางที่ บทนำ-ก`); `SEQ \* ThaiArabic` a Thai letter, its restart ignored. In Arabic digits with no regions, correct | ADR 0035, measured 2026-09-19 with LibreOffice 26.8 |
| WPS Writer | the Thai of a chapter label drawn as Latin letters (`ÓõõõyA`); with `--thai-digits` the value 1 drawn as ๕ | [2026-09-16](../evidence/2026-09-16-office-check-five-applications.md), [2026-09-19](../evidence/2026-09-19-wps-writer.md) |

These are those applications' own, in the file's numbering path; there is no attribute to change.
A user who needs one of them to draw the numbers right leaves the flag off.

## Why

- **Rule 1**: a file is usable as it leaves the skill. For most users that means *wherever it is
  opened*, which only a written number gives; for the user who goes on working in Word it means
  *numbers that follow the edit*, which only Word's numbering gives. One document cannot be both,
  so the user says which.
- **Rule 2.3**: what the application does already, the application does. Renumbering is Word's
  work; the build does not imitate it, it hands it over when asked.
- **Rule 6**: there is no one recipe. The limits of each choice are written where the user meets
  them — the settings reference, `references/numbering.md`, both guides — and not closed with
  "supported".
- **A default the user can see beats a rule the user cannot.** ADR 0035 decided by whether the
  document had Thai digits or regions. Nobody asking for a report could have known their list
  would renumber and their colleague's thesis would not.

## Why not the alternatives

**Make automatic numbering the default, Word being the reference.** The reference application is
the one that must pass every item; it is not the only one a file is opened in. A default that
hands a LibreOffice reader `ตารางที่ บทนำ-ก` without anyone having asked for anything is ADR
0035's first finding, and it has not changed.

**Keep ADR 0035's rule and add the switch on top.** Then there are three behaviours and the
default still depends on something the user did not say. The rule that survives is shorter than
the one it replaces: *the build writes the numbers unless you ask the application to.*

**`--build ready-to-use|to-edit`.** Both files can be edited. The difference is who counts, and
the flag is named for that.

**A switch per kind of number.** That is the half-renumbered document this record and the last one
both refuse.

## What it costs

**The bytes of a document with no Thai digits and no regions change**: its ordered lists and
captions become text. `sample-default` and `sample-all-flags` are regenerated; the three thesis
goldens do not move a byte, so what the maintainer saw in Word on 2026-09-19 still stands for
them. `sample.md` built with `--auto-numbering` is byte for byte the `sample-default` of before
this record (`50776ea25c45…`), which is how the old path is known to be whole.

**The oracle set gains a variant**, `sample-auto`: the thesis with `--heading-numbers
--thai-digits --auto-numbering`, held as a golden. Its checklist asks what no other variant can:
that a heading, a list item and a caption inserted in the application renumber what follows. The
reference application must pass it; the other four are recorded.

**The guides and `references/chapters.md`** said a thesis never renumbers. They now say it does
not unless asked, and send the reader to `references/numbering.md`.

## Expires when

LibreOffice and WPS draw `thaiNumbers`, `STYLEREF 1 \s` and `SEQ \* ThaiArabic \s` as Word does —
then the two documents look alike everywhere, and the default can be the one that renumbers.
