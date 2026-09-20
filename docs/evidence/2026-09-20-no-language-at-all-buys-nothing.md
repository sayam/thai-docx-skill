# 2026-09-20 — `<w:cs/>` with no `<w:lang>` at all: measured, and it buys nothing

The probe [ADR 0038](../adr/0038-the-thai-language-is-written-only-when-asked.md) listed under
"Why not the alternatives" as **Drop `w:lang` altogether**, run for the first time. That record
dismissed it on the reasoning that `w:val="en-US"` *"costs nothing in any application tested"*.
The reasoning was right about the conclusion and wrong about the reason, and this is the
measurement that says so.

- **WPS Writer 11.1.0.11723** (flatpak, Kingsoft) and **LibreOffice 26.8** on the maintainer's
  Linux machine, **Word for the web** and **Google Docs** in Chrome on the same machine.
- Three documents, one source (`probe.md`: correctly spelled Thai, SARA AM words, deliberately
  misspelled Thai, correctly spelled English, deliberately misspelled English, and a mixed
  paragraph), opened by eye by the maintainer.
- The three differ in the language elements and in nothing else: arm 2 is arm 1's own bytes with
  every `<w:lang/>` removed and every other entry repacked untouched. `<w:cs/>` (24), the fonts,
  the sizes and `w:themeFontLang w:val="en-US"` are identical in all three; the text is identical
  character for character; `check` reports no finding on any of them.

| arm | every run says |
|---|---|
| 1 `arm-1-default` | `<w:cs/><w:lang w:val="en-US"/>` — what `main` 24a90a5 writes |
| 2 `arm-2-no-lang` | `<w:cs/>` alone — the alternative under test |
| 3 `arm-3-thai-language` | `<w:cs/><w:lang w:val="en-US" w:bidi="th-TH"/>` — `--thai-language` |

## What each application drew

| | arm 1 (default) | arm 2 (no language) | arm 3 (`--thai-language`) |
|---|---|---|---|
| **WPS Writer** — SARA AM | correct | correct | **misplaced** |
| **LibreOffice** — correctly spelled Thai | red underline on every word | **red underline on every word** | none |
| **LibreOffice** — misspelled Thai (ประเทษ จำนวร วัฒนธรม) | underlined, with everything else | underlined, with everything else | **underlined, and nothing else is** |
| **LibreOffice** — status bar | `Hindi` | `Hindi` | `Thai` |
| **Word for the web** — correctly spelled Thai | red underline | **red underline** | none |
| **Word for the web** — status bar | `English (U.S.)` | `English (U.S.)` | `Thai` |
| **Google Docs** | no difference between the three, by eye |
| **misspelled English** (Teh quik brwn) | underlined | underlined | underlined |

## What it settles

**Arm 2 is arm 1 in every application.** Not one thing it was hoped to buy came back: the red
underline in LibreOffice and in Word for the web is exactly as it was. There is no application in
which dropping `<w:lang>` differs from keeping `w:val="en-US"` — so the alternative is not a
trade-off with a price, it is a change with no effect at all, and ADR 0038's decision stands
unchanged.

**The underline was never about `w:val="en-US"`.** The reasoning recorded on 2026-09-20 after the
five-application check — that LibreOffice and Word for the web proof Thai as English *because*
every run says `en-US` — is **wrong**, and this measurement is what retires it. `w:val` is the
Latin language; neither application ever consults it for Thai text. What decides is the
complex-script language, and when the file does not name one the application supplies its own:

- LibreOffice supplied **Hindi** — its own CTL default on this machine — and proofed Thai against
  a Hindi dictionary, which underlines everything.
- Word for the web supplied **English (U.S.)** here, and **Arabic (Saudi Arabia)** in
  `sample-options-word365_windows.docx` on the same account the same day. The fallback is not even
  stable between documents.

**`w:bidi="th-TH"` is the only thing that clears it**, and arm 3 shows it working properly rather
than merely silently: LibreOffice underlines ประเทษ, จำนวร and วัฒนธรม — the three deliberate
misspellings — and nothing else. That is Thai proofing actually running, not proofing switched off.

**So the trade is confirmed, in both directions and with the price now visible on both sides.**
Writing the Thai language buys real Thai proofing in LibreOffice and Word for the web and costs
SARA AM in WPS Writer; not writing it costs Thai proofing in those two — against whatever
dictionary the reader's application guesses — and keeps ำ in its place everywhere. There is no
third option. ADR 0038 leans the default at the page rather than at the proofing, and nothing
measured here disturbs that; `--thai-language` remains the way to ask for the other side.

## Found along the way, and not about language: Word for the web has no TH Sarabun New

In Word for the web the tone marks sit too high above the letter (ป้า ม้า ค้า ค่า) in **all three
arms**, and in `sample-options` and `extra-sample-text-with-thai-language` as well — including text
typed into those documents by hand, while the same text typed into a newly created document there
was drawn correctly. So it followed the document rather than the typing, and it was present with
and without the Thai language.

The variable was the font. **Word for the web's font list has no TH Sarabun New**; it offers
**TH SarabunPSK**. Asked for a font it does not have, it substitutes one whose mark metrics are not
the font's, and the tone marks float. Setting the same text to TH SarabunPSK in the same document
draws them in their place.

It is therefore that application's font list, not anything in the package, and no attribute reaches
it. A document meant to be read or edited in Word for the web is built with
`--font "TH SarabunPSK"`; the skill's default stays TH Sarabun New, which is the font the desktop
Word, LibreOffice and WPS all have here and the one Thai theses are written in. This belongs in
`references/limits.md` beside the other things that application cannot do.

## Files

`.local/work/2026-09-20-lang-probe/` — `probe.md`, `make.py` (builds all three; arm 2 by stripping
arm 1), `READ-ME-FIRST.md` (what was looked at, and the rule the result was read by, written before
the result was known).
