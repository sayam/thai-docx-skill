# 0028 — Settings live in one registry, grouped by what they need; everything else is derived from it

- Status: accepted
- Decided: 2026-09-16

## Where it came from

The skill grew from one fault — a .docx whose Thai broke — one setting at a time. By v0.1
it had twenty-six, and the maintainer asked for the design to be seen as one picture:
which features depend on which, which stand alone, which mix, and the code and SKILL.md
made smaller to match.

Reading the settings, the region comments, the two modes and the profiles together, two
facts stood out:

- **Each setting was described in nine places kept by hand**, in each of two languages:
  the defaults, the usage line, the parser's list of flags that take a value, its list of
  switches and its per-flag checks, the settings the build reports, the flags a profile
  may hold, the settings table of SKILL.md, the interview, and the settings a test expects.
  Every flag added on 2026-09-16 touched all of them, and the parity run caught an ordering
  slip between two.
- **The settings are not all one kind.** Most set how any document looks. Some only tune a
  structure the Markdown itself declares with region comments — without `<!-- chapters -->`
  or `<!-- appendices -->`, `--chapter-label` changes nothing — and the difference showed
  only as the one "changed nothing" warning ADR 0027 added.

A draft in `.local` proposed a registry of *features* with slots that code plugs into. This
record takes the part that needs no plug-in machinery.

## Decision

**The settings form six layers, by what each needs:**

| layer | what | settings | needs |
|---|---|---|---|
| L0 fidelity core | Markdown to a .docx with Thai set right, the checker, byte stability, both implementations | — | nothing; the invariant every layer keeps |
| L1 page and type | what every document has | `font`, `size`, `paper`, `landscape`, `margins`, `indent`, `line_spacing`, `align`, `hide_spelling_errors` | nothing; each independent |
| L2 page furniture | what the header and footer hold, and how generated numbers are drawn | `page_numbers`, `page_number_on_first`, `header`, `footer`, `thai_digits` | `page_number_on_first` needs `page_numbers` |
| L3 tables | how tables are laid out | `repeat_table_header`, `table_widths`, `table_size` | a table in the document |
| L4 headings | how headings are numbered and listed | `heading_numbers`, `toc`; heading styles from the front matter (0020) | headings in the document |
| L5 thesis structure | parameters of the structure region comments declare (0021) | `chapter_label`, `appendix_label`, `appendix_numbers`, `front_page_numbers`, `chapter_title_on_new_line`, `table_label`, `figure_label` | region comments or captions in the document |
| L6 modes and persistence | how settings are chosen and kept | grill (0026), profiles (0024) | L1–L5 as data |

`thai_digits` reaches across layers (page, list, footnote and caption numbers) and stays in
L2, where the numbers it draws are listed.

**One registry holds every setting**, one entry each, in `settings.py` and its JavaScript
twin: the key, the flag, the kind (a value, a switch, a switch that turns something off, a
value that may be left out, a list), the default, the layer, how a value is read and the
message when it is refused, what it needs, and the name the build reports it under. From
the registry, in both implementations, come: the defaults, the usage line, the parser, the
settings the build reports, and the flags a profile may hold. From it, checked into the
repository with a `--check` that fails when stale, as the JavaScript bundle is: the settings
table the agent reads (`references/settings.md`). A test holds the two registries equal
entry for entry; the parity suite goes on proving the behaviour.

**What a setting needs is data, not code in the flow.** Two kinds:

- *another setting* (`page_number_on_first` needs `page_numbers`): refused before the build,
  with the message the registry gives, as today;
- *a structure in the document* (region comments, captions, tables, headings): the build
  goes on, and one warning per layer names the settings given that changed nothing. `--toc`
  beside a `<!-- toc -->` comment is warned about the same way.

Warnings keep the code `settings` that ADR 0027 introduced.

**The code is arranged along the layers**, each file in both implementations: the registry;
the layout of L5 as pure functions on the parsed document; the body writer; the package's
other parts (styles, numbering, settings, headers and footers); the fidelity reference; and
a build that only runs parse, layout, write, pack, check and report in that order. A split
is a move, not a rewrite: every golden keeps its bytes.

**The core still owns the flow** (0007, 0008). The registry describes settings; it loads no
code, adds no slot a setting plugs into, and reads no file at run time — the JavaScript
sandbox has no file system (0025), so the registry is a literal in each implementation, not
a JSON asset.

Left out on purpose:

- Feature modules or slots that plug into the writer. Every setting still changes the
  package through code the core calls in a fixed order, so byte identity stays provable.
- Heading styles from the front matter in the registry: they are properties of the Markdown,
  checked by their own table (0020), not flags.
- `--allow-dir` and `--profile` in the registry's settings: they say where files are read
  from, not how the document looks, and a profile may never carry them (0025).
- Changing any default, message or golden. This record rearranges; it decides nothing a
  user can see except the new warnings.

## Why

A setting described once cannot disagree with itself. The nine hand-kept copies were
held equal only by tests that noticed after the fact; generating them turns a class of
slips into something that cannot be written. Grouping by what a setting needs makes the
"changed nothing" rule one rule instead of one sentence per flag, and gives the interview,
SKILL.md and the code the same order to follow. Keeping the registry as data about settings
— rather than a plug-in system — keeps the promise of 0008: one flow, two implementations,
the same bytes.

## Expires when

A setting appears that cannot be described as a flag with a value — for example one that
depends on another setting's value, not only on its presence — or the build gains a second
output format whose settings differ.
