# 0033 — The task-list box is a square in a text font, not a symbol only Windows has

- Status: accepted
- Decided: 2026-09-19
- Supersedes: nothing; it corrects a choice ADR 0022 left unexamined

## Where it came from

The WPS Writer re-check of 2026-09-19 found the task-list boxes missing — not drawn wrongly,
drawn as nothing ([record](../evidence/2026-09-19-wps-writer.md)). The reason was in the file:

```xml
<w:rFonts w:ascii="Segoe UI Symbol" w:hAnsi="Segoe UI Symbol" w:cs="Segoe UI Symbol"/>
<w:t xml:space="preserve">☐ </w:t>
```

Segoe UI Symbol is a Microsoft font. The machine had no font that carries U+2610 and U+2611 under
that name, so nothing was drawn — in WPS, and in every other reader on that machine. Item 9 of
ADR 0012's list, "☐ and ☑ show as symbols", was passing only because it had only ever been looked
at on Windows.

Measured on 2026-09-19, with `fc-list`, over the fonts a document is likely to meet:

| character | Arial | Calibri | Times New Roman | Liberation Sans | DejaVu Sans | TH Sarabun New |
|---|---|---|---|---|---|---|
| ☐ U+2610, ☑ U+2611 | — | — | — | — | yes | — |
| □ U+25A1 | yes | yes | yes | yes | yes | — |
| ■ U+25A0 | yes | — | yes | yes | yes | — |

Every local font that carries ☐ is a symbol font: DejaVu Sans, Noto Sans Symbols 2, Quivira,
Source Code Pro, and Microsoft's two Segoe faces. **No font that carries them is present on
Windows, macOS and Linux alike**, so no choice of font name can make ☐ appear everywhere.

Confirmed the other way round on the same day: with Segoe UI Symbol installed on that Linux
machine, the old file's boxes appear. The font was the whole of it — and the remedy that fact
suggests, *every reader installs a Microsoft font*, is not one a document can ask for.

## Decision

- **The box is `□` (U+25A1) and, when checked, `■` (U+25A0)** — a white square and a black one.
- **The run names Arial.** Arial is on Windows and on macOS; on Linux, fontconfig answers a request
  for Arial with Liberation Sans, which is metric-compatible and carries both squares. The
  document's own Thai font carries neither square, so a font must be named.
- The box is **the skill's rendering of `- [ ]`**, like a bullet — not the user's text. Choosing its
  glyph is a formatting decision and ADR 0023 does not reach it. The Markdown still says `- [ ]`
  and `- [x]`, and `plain_text` reports what the document will show.

## Why not the alternatives

**Keep ☐ and name a different font.** There is none to name: the table above is the whole of it.
Naming DejaVu Sans would trade Windows for Linux, and Word 365 for Windows is this project's
reference (ADR 0012).

**Name no font and let the reader substitute.** Word does substitute for a missing glyph, and
probably LibreOffice too; WPS drew nothing when told a font it did not have, and nobody knows what
it does when told a font that exists but lacks the glyph. That is exactly the kind of hope this
project refuses: the premise of the whole skill is to *say it in the file* rather than let each
reader guess. A named font that carries the glyph is a statement; an omission is a wish.

**A tick inside a box.** `☑`'s shape has no widely available equivalent: `▣`, `☒` and `✓` are all
symbol-font characters too. A filled square is less pretty than a tick and is legible everywhere,
which is the trade this record makes.

## What it costs

The bytes of every document with a task list change, so the goldens and the release oracle were
regenerated. ADR 0012 asks for the five office applications to be looked at again before the next
release, and this change is the reason.

## Expires when

A box-drawing character with a tick becomes common in ordinary text fonts, or the project stops
naming fonts for individual runs.
