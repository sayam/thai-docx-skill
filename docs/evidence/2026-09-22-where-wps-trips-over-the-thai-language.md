# 2026-09-22 — Where WPS Writer trips over the Thai language: `docDefaults` yes, `themeFontLang` no

What this proves: five documents differing only in where `w:bidi="th-TH"` is written were opened in
WPS Writer, one at a time. **`w:bidi="th-TH"` in `docDefaults` misplaces SARA AM exactly as it does
on a run; `<w:themeFontLang w:bidi="th-TH"/>` in `settings.xml` does not.** Both controls behaved,
so the three arms between them are trustworthy. This is finer than the bisect of
`2026-09-20-sara-am-and-the-thai-language.md`, which measured the attribute only on runs, and it
refines — does not overturn —
[ADR 0038](../adr/0038-the-thai-language-is-written-only-when-asked.md).

Why it was asked: `2026-09-22-what-word-writes-when-a-person-types.md` found that Word itself
declares `w:bidi="th-TH"`, once at the document, in both `docDefaults` and `themeFontLang` — and
produces a file with no underline anywhere. Before
[ADR 0039](../adr/0039-complex-script-is-marked-where-it-is.md) could copy Word's rules it had to
know which of them WPS Writer will tolerate.

Environment: **WPS Writer 11.1.0.11723** (flatpak, Kingsoft) on the maintainer's Linux machine, and
**Word 365 for Windows** on the Windows machine, both as in the 2026-09-20 record. WPS Writer has no
headless conversion, so every arm was opened and read by eye by the maintainer, **one arm at a
time**, and reported before the next was opened. 27 screenshots from WPS Writer and 23 from Word,
seven of them of arm 3. Content synthetic (ADR 0025 §10).

The five files were made by a script that edits the XML of `sample-text-word365_windows.docx`,
built from `main`, changing nothing else; arm 5 is `extra-sample-text-with-thai-language.docx`,
the file this project already builds with `--thai-language`. The script asserts that
`settings.xml` ends with exactly one `<w:themeFontLang>` element, because the build already writes
one and an earlier version of the probe silently produced two.

## The five arms

| arm | `docDefaults` | `themeFontLang` | `w:bidi` on runs | SARA AM in WPS |
|---|---|---|---|---|
| **1** baseline | — | — | — | ✅ **correct** — the negative control |
| **2** | **yes** | — | — | ❌ **wrong** |
| **3** | — | **yes** | — | ✅ **correct** |
| **4** both | **yes** | **yes** | — | ❌ **wrong** |
| **5** control | yes | yes | **all 498** | ❌ **wrong** — the positive control |

Arm 1 is byte-equivalent to what `main` builds and had to come out right; arm 5 is the file already
known to come out wrong. **Both did**, which is the condition this project sets before believing a
probe at all. Had either control misbehaved the whole set would have been discarded.

## The symptom

In the failing arms SARA AM loses its tail, leaving only the nikhahit over the letter, and the
words run together:

| should read | arm 2 · arm 4 · arm 5 show |
|---|---|
| `ทำให้โปรแกรมตรวจคำสะกด` | `ทํให้โปรแกรมตรวจคํสะกด` |
| `ถูกกำหนดเป็นภาษาละติน` | `ถูกกํหนดเป็นภาษาละติน` |
| `คำสำคัญ:` | `คํสํคัญ:` |
| `สังเคราะห์จำนวน` | `สังเคราะห์จํนวน` |
| `โปรแกรมสำนักงาน` | `โปรแกรมสํนักงาน` |
| `เฉพาะตำแหน่ง` | `เฉพาะตํแหน่ง` |

The spaces between sentences go too: `ทุกคำ การตัดบรรทัด` becomes `ทุกคํการตัดบรรทัด`.

Arms 1 and 3 show none of it. `กำหนด`, `ทำให้`, `คำสำคัญ`, `จำนวน`, `ตำแหน่ง`, `สำนักงาน` are all
correct, and the spacing is ordinary. Arm 3 is indistinguishable from arm 1 by eye.

## What it refines in ADR 0038

ADR 0038 says WPS Writer trips over the attribute *"on a run, in a style, or in the document's
defaults"*. Arm 2 confirms the last of those directly — `docDefaults` alone, no run touched, and
the symptom is identical to arm 5's. **What is new is that `themeFontLang` is outside that set.**
The line does not fall between "on runs" and "at the document"; it falls between two places at the
document, one of which WPS reads and one of which it apparently does not.

ADR 0038's decision is unchanged. Its default — write `w:bidi="th-TH"` only under `--thai-language`
— still holds, and `docDefaults` remains closed to the attribute.

## Arm 3 in Word 365 for Windows

Opened to check that the safe arm costs nothing in the reference application. Seven screenshots:

| checked | result |
|---|---|
| SARA AM | ✅ `กำหนด` `ทำให้` `คำสำคัญ` `จำนวน` `สำนักงาน` |
| red underline under Thai | ✅ none |
| status bar | Thai |
| contents and page numbers | ✅ `ก ข ค ง ฉ ช`, then `1 1 1 2`; section break outside the field |
| `□` `■` | ✅ squares |
| tables, links, headings | ✅ |
| **red underline under English** | ❌ still there — **as expected**, arm 3 does not touch `<w:cs/>` |

`<w:themeFontLang w:bidi="th-TH"/>` is therefore safe in both applications, and on its own fixes
nothing about English. The English underline needs the `<w:cs/>` change, which is ADR 0039.

## What this decides, and what it leaves open

**Decided:** ADR 0039 may copy Word's run splitting, its `<w:cs/>` rule, its silence about `w:lang`
on runs, and its empty `docDefaults` — none of those involve `w:bidi`. It may **not** copy
`w:bidi="th-TH"` into `docDefaults`.

**Left open, deliberately:** whether to write `<w:themeFontLang w:bidi="th-TH"/>`. It is safe, but
safe is not a reason. Its only possible benefit is on a machine whose complex-script language is
not Thai — the case ADR 0038 knowingly traded away — and **nobody has such a machine to test on**.
An untested benefit is not a benefit, so ADR 0039 does not write it, and the question stays where
ADR 0038 left it.

**Not measured:** arms 2, 3 and 4 in LibreOffice Writer, Google Docs and Word for the web. Only
arms 1 and 3 were opened in Word at all.

The five documents, the script that builds them and the screenshots are the maintainer's working
copy and are not part of the repository; they are kept at `.local/work/2026-09-22-wps-bidi-probe/`,
with the arm-by-arm reading in `RESULTS.md`.
