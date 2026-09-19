# 2026-09-19 — Word 365 for Windows: the look passes, the edit does not — and the switch that followed

The first application of the five-application check before v0.2.0, and what it led to
([ADR 0036](../adr/0036-who-counts-is-one-switch.md)).

## 1. What the maintainer saw

- **Word 365 for Windows** (Microsoft 365 desktop, on Windows 10 in a QEMU/KVM guest), TH Sarabun
  New installed.
- `sample-options-word365_windows.docx`, byte-identical to `tests/golden/thesis-options.docx`
  (`66a42f822760…`), built from `main` **1edefc4**: the thesis with `--heading-numbers --thai-digits`
  and the paragraph, page and table options. Thirteen screenshots, pages 1 to 24 of 26, the
  navigation pane open.

Held, by eye:

| looked at | seen |
|---|---|
| title bar, status bar | no "Compatibility Mode"; the status bar reads Thai |
| squiggles | ordinary Thai words carry none; Word's own dictionary underlines `ฟอนต์`, part of `วิทยาศาสตรมหาบัณฑิต` and the English words, as it does in any document marked Thai |
| cover, บทคัดย่อ, Abstract | centred headings at 20 pt, body distributed, first line indented, 1.5 spacing; header and footer text on every page |
| front page numbers | `ii` at the top centre; the contents list the front pages as `i`, `iii`, `iv`, `v`, `vii`, `viii` |
| สารบัญ | filled, with page numbers: `บทที่ ๑ บทนำ … ๑`, `๑.๑ …`, `๑.๓.๑ …` |
| สารบัญตาราง, สารบัญภาพ | filled, with page numbers: `ตารางที่ ๑-๑ …`, `ตารางที่ A-๑ …`, `รูปที่ ๒-๑ …`, `รูปที่ B-๑ …` |
| chapter and headings | `บทที่ ๑ บทนำ` centred; `๑.๑` blue at its heading's size; `๑.๓.๒` italic |
| captions | `ตารางที่ ๑-๑`, `ตารางที่ ๒-๑`, `รูปที่ ๒-๑`, `ตารางที่ B-๑`, label and number bold |
| task list | `■` and `□` drawn |
| tables | borders, cell margins, header row bold, columns sized by their text |
| navigation pane | every heading, with its number, at its level |

**Nothing looked wrong.** The maintainer's verdict: *content, look and correctness are complete —
but the automatic numbering of Heading 1 and the levels under it does not work.* A heading typed
into the document takes no number and moves no other. That is what ADR 0035 chose for a thesis in
Thai digits, and the guides say so; seeing it in the reference application is what made it a
question again.

The maintainer's reading of it, which ADR 0036 records as the decision:

- a file whose numbers are the build's own text is the file that holds in all five applications,
  and that is what most users need — they ask an assistant for a document and change a few words;
- a file Word numbers is the one a person who goes on working in Word needs, in Arabic digits and
  in Thai, and the skill did not offer it for a thesis at all;
- the second must be asked for by name, and its limits in the other applications written where
  the user meets them.

**Not seen in this sitting:** `sample-basic`, `sample-text` and `sample-layout` in Word 365 for
Windows; any file in the other four applications. The checklist stays open for them.

## 2. What changed in the bytes

| golden | before | after | why |
|---|---|---|---|
| `thesis-text` | `b860e1ffe0c0…` | the same | already written numbers |
| `thesis-options` | `66a42f822760…` | the same | already written numbers — what section 1 saw still stands |
| `thesis-layout` | `f68752995e1d…` | the same | already written numbers |
| `sample-default` | `50776ea25c45…` | `93c2f0affc28…` | ordered lists and the `SEQ` caption became text: the default now holds for every document |
| `sample-all-flags` | `65cf972b62a1…` | `ad0bde01c781…` | the same |
| `thesis-auto` | — | `f9b0d475072b…` | new: the thesis with `--heading-numbers --thai-digits --auto-numbering --page-numbers bottom-center` |

**The application's own numbering is the path that was there before, whole**: `sample.md` built
with `--auto-numbering` is `50776ea25c45…`, the `sample-default` of before this change, byte for
byte. A test holds that hash.

`thesis-auto.docx` carries `thaiNumbers` on every level of the heading and ordered lists,
`บทที่ %1` and `ภาคผนวก %1` as level text, nine `STYLEREF 1 \s`, five `SEQ Table \* ThaiArabic \s 1`
and four `SEQ Figure \* ThaiArabic \s 1`, each with its result written in, and the three lists as
`TOC … \t "Table Caption,1"` — the same lists the written-number documents carry.

Python and JavaScript give the same bytes for it, as for every golden (`tests/test_js_parity.py`).

**A flag that reaches nothing changes no byte.** With no ordered list the package no longer
carries the ordered lists' numbering definition, so `--auto-numbering` on a document with nothing
to count is byte for byte the document without it, and the build says the flag changed nothing.

## 3. Planted defects

Each planted in `writer.py`, the suite run, the file restored.

| planted | red |
|---|---|
| the switch ignored (`numbers_are_text` always true) | the `thesis-auto` golden; `…a_number_is_the_build_s_unless_the_application_is_asked_to_count`; `…asked_to_count_a_caption…`; `…asked_to_count_the_sample_is_byte_for_byte…`; `…thai_digits_format_the_numbers…`; `…front_matter_heading_styles…`; `…said_to_have_changed_nothing_exactly_when_it_changed_no_byte` |
| the caption's restart at each chapter dropped (`\s 1`) | the `thesis-auto` golden; `…asked_to_count_a_caption…` |
| Thai digits forgotten in the caption's `SEQ` | the `thesis-auto` golden; `…asked_to_count_a_caption…` |

## 4. Not proved here

- **`sample-auto` has not been opened in any application.** That Word renumbers an inserted
  heading, list item and caption in this file — the whole point of the flag — is what its
  checklist asks, and it is unticked. What `references/numbering.md` says of Word with
  `--auto-numbering` rests on the checks of [2026-09-16](2026-09-16-office-check-five-applications.md)
  and [2026-09-17](2026-09-17-word-for-macos.md), which opened files numbered the same way and
  did not edit them.
- What Google Docs and WPS Writer do with `STYLEREF` and a restarting `SEQ` after their fields are
  updated. The table marks those cells not measured.
