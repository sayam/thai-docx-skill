# 0020 — Heading styles come from the front matter, as CSS-like declarations

- Status: accepted
- Decided: 2026-09-15

## Where it came from

With heading numbers in place, the maintainer asked for Heading 1–6 to take their own
font, size, colour, weight, style, underline and indent, "like CSS", and did not know
how a Markdown file could say so. Markdown has no syntax for it: CommonMark reads
`# Title {color=red}` as a heading whose text ends in braces [S8], and raw HTML such as
`<h1 style="…">` is outside what 0010 accepts. Three places were weighed: the front
matter, a separate CSS file named by a flag, and attributes on each heading. The
maintainer chose the front matter first.

0010 said the front matter gives `title` and `author` and nothing else is used; this
record adds the heading keys to that rule and changes nothing else in 0010.

## Decision

**Where.** The front matter keys `heading-1` … `heading-6`, one line each, style every
heading of that level. The value is a list of declarations, `name: value`, separated by
`;` as in a CSS rule; a `;` inside double quotes belongs to the value. The properties go
into Word's Heading 1–6 styles, not onto each paragraph, so the table of contents,
`--heading-numbers` and restyling in Word keep working.

```markdown
---
heading-1: font-size: 20pt; color: #1F4E79; text-align: center; page-break-before: always
heading-2: font-family: "TH SarabunPSK"; text-decoration: underline double
---
```

**What.** The property names and keywords are CSS's [S38, S39], lower case, with the
values Word can hold:

| property | values | Word |
|---|---|---|
| `font-family` | one font name, quoted or not, 1–64 characters | `w:rFonts` (all four) |
| `font-size` | `1pt` to `400pt` | `w:sz`, `w:szCs` |
| `color` | `#RRGGBB` | `w:color` |
| `font-weight` | `bold`, `normal` | `w:b`, `w:bCs` |
| `font-style` | `italic`, `normal` | `w:i`, `w:iCs` |
| `text-decoration` | `none`, or `underline` and `line-through` in any order, the underline `solid`, `double`, `dotted`, `dashed`, `wavy` or `thick` | `w:u`, `w:strike` |
| `text-align` | `left`, `center`, `right`, `justify`, `thai-distribute` | `w:jc` |
| `margin-left` | a length ≥ 0 | `w:ind w:left` |
| `text-indent` | a length; negative hangs | `w:ind w:firstLine` / `w:hanging` |
| `margin-top`, `margin-bottom` | a length ≥ 0 | `w:spacing w:before` / `w:after` |
| `line-height` | a number from 1 to 3 | `w:spacing w:line` |
| `page-break-before` | `always`, `auto` | `w:pageBreakBefore` |

A length is a number with `in`, `cm` or `pt`, or `0`, at most 10 in. `thick` and
`thai-distribute` are Word's, not CSS's. A property not given keeps the built-in look
that `--font`, `--size` and 0026 give that level.

**Refusals and warnings.** An unknown property, a value outside the table, a pair with
no `:` or an unclosed quote stops the build with the front matter line, as 0010 does for
the body. A key that looks meant as a heading style but is not one — `heading1`, `h2`,
`heading-7` — is a warning, since other front matter keys are ignored silently. A font
with no Thai glyphs is the checker's warning, as for `--font`.

Left out on purpose:

- Styles on one heading only (`{…}` attributes): not CommonMark, and headings of one
  level that look different defeat the styles the table of contents is built from.
- A separate `--style file.css`: a file read by 0011 and 0017's rules and a CSS reader in
  both implementations; the declarations here are its body when it comes.
- Styles for paragraphs, lists, tables and code: headings first.
- Font lists with fallbacks, `rgb()` and named colours, `em` and percentages, `bolder` and
  numeric weights: each needs a meaning Word has no field for, or a choice this record
  would have to make for the user.

## Why

Word styles are per level, as CSS rules for `h1` … `h6` are, and the front matter is the
one place in a Markdown file that holds settings without entering the text — 0016 stays
whole, and the fidelity check needs no change. CSS names are the ones an agent and a user
already know, so SKILL.md needs a table, not a new language. Both implementations read
the same declarations with the same rules and give the same bytes (0008); a document
without the keys keeps its bytes.

## Expires when

Users need styles beyond headings, the same styles across many documents (the
`--style` file), or a heading that differs from the rest of its level.
