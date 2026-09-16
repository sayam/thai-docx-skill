# Heading styles: the properties

Read this when the user asks for a heading look (SKILL.md, Heading styles). Each
`heading-1` … `heading-6` line in the front matter holds declarations from this table,
separated by `;`, as in a CSS rule.

## Properties

| property | values |
|---|---|
| `font-family` | a font name |
| `font-size` | `1pt`–`400pt` |
| `color` | `#RRGGBB` |
| `font-weight` | `bold`, `normal` |
| `font-style` | `italic`, `normal` |
| `text-decoration` | `none`; `underline` (`solid`, `double`, `dotted`, `dashed`, `wavy`, `thick`), `line-through` |
| `text-align` | `left`, `center`, `right`, `justify`, `thai-distribute` |
| `margin-left`, `margin-top`, `margin-bottom` | a length: `0.5in`, `1.27cm`, `12pt`, `0` |
| `text-indent` | a length; negative hangs |
| `line-height` | `1`–`3` |
| `page-break-before` | `always`, `auto` |

Lower case, at most 10in. Anything else stops the build (exit 2) with the front matter
line: fix that declaration. Unset properties keep the built-in heading look.
