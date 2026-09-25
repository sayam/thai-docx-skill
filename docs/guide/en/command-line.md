# Use it without an AI

The skill's program runs by itself in a terminal. You write the Markdown, and one command makes
the Word file. Every command on this page was run as written.

[Guide home](../en.md) · [ภาษาไทย](../th/command-line.md)

## Before you start

1. Check that you have Python 3.11 or newer, or Node.js 22 or newer:

   ```sh
   python3 --version
   node --version
   ```

   On Windows, type `py --version` for Python. If you have neither, install one from
   [python.org](https://www.python.org/downloads/) or [nodejs.org](https://nodejs.org/).
2. Download `thai-docx-<version>.zip` from
   [Releases](https://github.com/sayam/thai-docx-skill/releases) and unzip it in your working
   folder. You get a folder `thai-docx`.

   ```sh
   unzip thai-docx-0.2.0.zip
   ```

Nothing else is installed, and nothing uses the internet.

The commands below use Python. For Node.js, replace `python3 thai-docx/scripts/thai_docx` with
`node thai-docx/scripts/thai_docx.js`; the file you get is the same, byte for byte. On Windows,
replace `python3` with `py`.

## Make your first file

1. Write `report.md` in UTF-8, for example:

   ```markdown
   # รายงานการประชุม

   ประชุมทีมประจำเดือน **กันยายน**

   - สรุปงานที่เสร็จแล้ว
   - งานที่ต้องทำต่อ

   | งาน | ผู้รับผิดชอบ |
   |---|---|
   | ทำเอกสาร | สมชาย |
   ```

2. Build it:

   ```sh
   python3 thai-docx/scripts/thai_docx build report.md report.docx
   ```

3. Read the one line it prints, and the exit code:

   | exit code | the line says | what it means |
   |---|---|---|
   | 0 | `"ok": true` | `report.docx` is made; `"settings"` lists the settings used |
   | 2 | `"error"`, often with `"line"` | the Markdown has something the build does not take, on that line; no file is made |
   | 1 | `"findings"` | a fault in the skill; no file is made. Please [report it](https://github.com/sayam/thai-docx-skill/issues) |

   `"warnings"` never stop the build, but read them: a font with no Thai letters, or a setting
   that changed nothing.

   **Careful:** `build` replaces `report.docx` if it already exists, without asking. Use a new
   name to keep the old file.

## Change the settings

Add flags after the file names:

```sh
python3 thai-docx/scripts/thai_docx build report.md report.docx --font "Sarabun" --size 14 --page-numbers bottom-center --toc
```

Common flags:

| flag | does |
|---|---|
| `--font "Sarabun"`, `--size 14` | font and text size |
| `--paper letter`, `--paper f14`, `--landscape` | paper |
| `--margins 1,1,1,1` | margins in inches: top, right, bottom, left |
| `--indent 0.5`, `--line-spacing 1.5` | first-line indent, line spacing |
| `--align thai` | Thai distributed alignment |
| `--toc`, `--heading-numbers` | table of contents, numbered headings |
| `--page-numbers`, `--page-numbers bottom-center`, `--no-page-number-first` | page numbers |
| `--header "ลับ"`, `--footer "ร่าง"` | text at the top or bottom of each page |
| `--thai-digits` | ๑ ๒ ๓ for the numbers the skill adds; digits you typed stay |
| `--thai-language` | write the Thai language into the document, so Word proofs it as Thai on any machine; WPS Writer then misplaces ำ |
| `--auto-numbering` | Word counts headings, lists and captions and renumbers as you edit (by default the skill writes the numbers in: the same in every application, but they do not renumber) — for a file you will keep editing in Word; other applications draw it differently |
| `--force-cs-whole-doc` | one font throughout in Word, English and code included (Google Docs keeps code blocks monospace) — for a final file that will be read, not edited; Word then underlines correctly spelled English on screen |
| `--hide-spelling-errors` | no squiggles |
| `--table-widths auto`, `--table-size 14`, `--no-repeat-table-header` | tables |
| `--allow-dir ../images` | read images from another folder |

Every flag and its default: [references/settings.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/settings.md).
For a report or thesis (`<!-- chapters -->` and the other markers, `Table:` and `Figure:`
captions, `--chapter-label` and more):
[references/chapters.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/chapters.md).
For heading colors and sizes in the front matter:
[references/heading-styles.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/heading-styles.md).

## Keep settings as a profile

```sh
python3 thai-docx/scripts/thai_docx profile save thesis --size 15 --align thai
python3 thai-docx/scripts/thai_docx build report.md report.docx --profile thesis
python3 thai-docx/scripts/thai_docx build report.md report.docx --profile thesis --size 18
```

A flag after `--profile` wins over the profile. The other profile commands:

| command | does |
|---|---|
| `profile list` | lists your profiles and where they are |
| `profile show thesis` | shows a profile's settings, and every setting a build would use |
| `profile save thesis --size 15 --project` | saves in this folder's `.thai-docx/profiles/`, not your home folder |
| `profile save thesis-v2 --from thesis --default align --size 14` | a new profile from an old one: `align` back to its default, size 14 |
| `profile export thesis thesis.json` | writes the file to send to someone |
| `profile import thesis.json --name school-thesis` | takes a profile someone sent, under a name you choose (add `--project` for this folder only) |
| `build report.md report.docx --profile thesis.json` | uses a profile file straight from its path |
| `build report.md report.docx --profile thesis --default toc` | uses a profile without one of its settings |

```sh
python3 thai-docx/scripts/thai_docx profile list
python3 thai-docx/scripts/thai_docx profile show thesis
python3 thai-docx/scripts/thai_docx profile save thesis-v2 --from thesis --default align --size 14
python3 thai-docx/scripts/thai_docx profile export thesis thesis.json
python3 thai-docx/scripts/thai_docx profile import thesis.json --name school-thesis
```

**Careful:** `profile save` and `profile import` replace a profile of the same name without
asking. When they did, the line they print says `"replaced": true` and has a warning.

Profiles live in `~/.thai-docx/profiles/`, or `.thai-docx/profiles/` in a project; a project
profile wins over one of the same name. A profile is a small JSON file of settings, nothing
else. Details: [references/profiles.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/profiles.md).

## Check a Word file

```sh
python3 thai-docx/scripts/thai_docx check report.docx
```

Exit code 0: no problems. 1: problems, listed under `"findings"` by code. 2: not a Word file it
can read, or refused as unsafe. What each code means:
[references/check.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/check.md).
The check reports. To fix a file you do not have the content for:

```text
python3 thai-docx/scripts/thai_docx repair theirs.docx theirs-fixed.docx
```

It writes a new file — the one you gave is never changed — with these faults gone: the marks
every Thai run needs, proofing switched off, the complex-script twins, properties in the wrong
order, and the compatibility mode when the file declares one. A file that declares no mode is
left so, and the mode stays under `"remaining"`. A word split across two runs and invisible
characters are listed there too, because fixing either would change the text. The report also names the font it wrote where a run named none;
`--font "Sarabun"` chooses it yourself.

Setting the compatibility mode reflows the document, so page breaks can move: look through it
before you send it on. The new file is about the size of the old one. When you have the Markdown, rebuilding fixes
everything, including the faults repair leaves alone.

## Ask the questions yourself

The grill questions are for AI assistants, but you can see them:

```sh
python3 thai-docx/scripts/thai_docx grill --said "thai-docx grill make a report"
```

It prints the questions, their choices and the flags each choice adds. At the command line you
can pass those flags straight to `build`.

## In a web page or a sandbox

`thai-docx/scripts/thai_docx.js` also runs with no Node.js, in a JavaScript sandbox that has
`TextEncoder` and `TextDecoder`: `ThaiDocx.buildDocument(markdown, flags, images)` returns
`{ result, bytes }`, where `bytes` is the Word file, or `null` when the build refused.
See [references/sandbox.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/sandbox.md).
