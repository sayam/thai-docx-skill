# 2026-09-19 — a box every reader can draw

The WPS re-check earlier today found the task-list boxes missing on Linux — drawn as nothing, in
every reader on that machine, because the file asked for **Segoe UI Symbol**
([record](2026-09-19-wps-writer.md)). This is the fix, and the measurement it rests on.

## What was measured

`fc-list ":charset=<codepoint>:family=<name>"`, on 2026-09-19, over the fonts a document is likely
to meet:

| character | Arial | Calibri | Times New Roman | Liberation Sans | DejaVu Sans | TH Sarabun New |
|---|---|---|---|---|---|---|
| ☐ U+2610 · ☑ U+2611 | — | — | — | — | yes | — |
| ☒ U+2612 · ✓ U+2713 · ▣ U+25A3 | — | — | — | — | yes | — |
| **□ U+25A1** | **yes** | yes | yes | yes | yes | — |
| **■ U+25A0** | **yes** | — | yes | yes | yes | — |
| × U+00D7 | yes | yes | yes | yes | yes | — |

Every family on this machine that carries ☐ is a symbol font — DejaVu Sans, DejaVu Sans Mono, Noto
Sans Symbols 2, Quivira, Source Code Pro, Segoe UI Symbol, Segoe UI Emoji. **None of them is
present on Windows, macOS and Linux alike.** So no font name could have made ☐ appear everywhere;
the characters had to change.

The document's own Thai font carries no square either, so a font must be named for that run
whatever the character is.

## The cause, proved rather than inferred

After the fix was written, the maintainer installed **Segoe UI Symbol** on the same Linux machine
and opened the **old** file again in WPS. The boxes appeared — ☐ and ☑, correctly drawn.

That closes the diagnosis: nothing was wrong with WPS and nothing was wrong with the file's
structure. The file asked for a font the machine did not have, and no reader invents a glyph it was
not given. It also shows what the "fix" would otherwise be — *ask every reader of the document to
install a Microsoft font* — which is not a thing a person who receives a thesis will do, or will
know how to do, since nothing on screen says which font is missing.

## What changed

```xml
<w:rFonts w:ascii="Segoe UI Symbol" …/><w:t xml:space="preserve">☐ </w:t>
→
<w:rFonts w:ascii="Arial" …/><w:t xml:space="preserve">□ </w:t>
```

`□` (U+25A1) unchecked, `■` (U+25A0) checked, in **Arial** — on Windows and macOS by name, and on
Linux through fontconfig, which answers a request for Arial with Liberation Sans, metric-compatible
and carrying both squares. Verified here: `fc-match Arial` resolves, and both squares are in
Liberation Sans as well.

The same two characters are what `plain_text` reports, in both implementations, so what the
document shows and what the skill says it shows stay one thing.

## Why the box may change at all

The box is the skill's rendering of `- [ ]`, the way `•` is its rendering of `-`. It is not the
user's text: the Markdown still reads `- [ ]` and `- [x]`, and nothing the author typed moved. ADR
0023 governs the text and does not reach a marker the build draws — which is why this is a
formatting decision recorded in [ADR 0033](../adr/0033-the-task-box-is-a-square-in-a-text-font.md)
rather than a refusal.

## What it costs

**The bytes of every document with a task list change.** The five goldens were regenerated:

| golden | bytes | sha256 |
|---|---|---|
| `sample-default` | 32,883 | `50776ea25c45…` |
| `sample-all-flags` | 36,646 | `71d0a05f3367…` |
| `thesis-text` | 192,561 | `10afc0c4b771…` |
| `thesis-options` | 207,614 | `f97504a7929c…` |
| `thesis-layout` | 197,094 | `9faec5daf98f…` |

ADR 0012 asks for the five office applications to be looked at again when a release changes document
bytes. **This change is the reason the next release needs that**, and the checklist item now reads
"□ and ■ show as squares, not as blank space" so the next check tests the thing that failed.

299 tests pass, including the parity of both implementations on the new bytes.

## What was not done, and why

**Keeping ☐ and naming another font.** There is none: the table above is the whole search. DejaVu
Sans would trade Windows for Linux, and Word 365 for Windows is the reference.

**Naming no font and letting each reader substitute.** Word substitutes for a missing glyph;
LibreOffice probably does; WPS drew nothing when told a font it did not have, and nobody has
measured what it does when told a font that exists but lacks the glyph. The premise of this whole
project is to say a thing in the file rather than let a reader guess it — a named font that carries
the glyph is a statement, an omission is a wish.

**A tick inside a box.** `▣`, `☒` and `✓` are symbol-font characters too. A filled square is
plainer than a tick and is drawn everywhere, which is the trade this makes.
