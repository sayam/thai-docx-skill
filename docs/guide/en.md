# thai-docx step by step

This guide shows how to use thai-docx, from asking for a simple Word file to editing a set
of settings you saved earlier. Jump to the scenario you need.

[ภาษาไทย](th.md)

## What thai-docx is

thai-docx is a **skill**: extra know-how you install into an AI assistant such as Claude.
When you ask the assistant for a Word file that contains Thai, it uses the skill to make the
file.

Word files with Thai made by ordinary tools often go wrong:

- a red squiggly line under every Thai word
- lines that break in odd places
- bold that is not bold, and bullets that do not show

thai-docx avoids all of these, and it **never changes a single character of your text**.

Words used in this guide:

| word | meaning |
|---|---|
| Markdown | plain text with a few symbols for formatting, such as `#` for a heading and `**word**` for bold |
| setting | something that controls how the file looks: font, text size, paper, page numbers |
| profile | a saved set of settings you can use again, like a recipe you wrote down |
| grill | a mode where the assistant asks you about the settings before it makes the file |
| field | a part of a Word file that Word works out itself, such as the page numbers in a table of contents |

## Before you start: install the skill

Download `thai-docx-<version>.zip` from the
[Releases](https://github.com/sayam/thai-docx-skill/releases) page, then:

- **Claude Code** (the app on your computer): unzip it into `~/.claude/skills/`, so you
  get `~/.claude/skills/thai-docx/`. To use it in one project only, unzip it into that
  project's `.claude/skills/` instead.
- **Claude on the web or in the app**: upload the zip on the settings page that takes skills.
- **Another chat app that has no skills but can run Python**: follow
  [PROMPT.md](https://github.com/sayam/thai-docx-skill/blob/main/PROMPT.md).

The computer running the skill needs Python 3.11 or newer, or Node.js. The skill needs no
internet connection and nothing else installed.

The computer that opens the file should have the font **TH Sarabun New**. If it does not,
ask for another font that has Thai letters, such as Sarabun (see scenario 3).

---

## Scenario 1: the simplest request

**Use it when** you want a document quickly and do not care about the layout yet.

1. Tell the assistant what the document is about.

   ```text
   Make a Word file in Thai that sums up how to apply for a Thai passport, with a heading, a bullet list of documents you need, and a table of fees
   ```

2. The assistant writes the content and makes the file **right away, without asking you
   anything first**.
3. It tells you the file name and the settings it used, for example:

   > Made `passport.docx` — TH Sarabun New 16 pt, A4 paper, left margin 1.5 in, other
   > margins 1 in. Any of these can be changed.

4. Open the file in Word.

The default settings, used when you ask for nothing else:

| what | default |
|---|---|
| font | TH Sarabun New, 16 pt |
| paper | A4, portrait |
| margins | left 1.5 in, the others 1 in |
| line spacing | single (1) |
| paragraph alignment | left |
| table of contents, page numbers | none |

## Scenario 2: you already have a Markdown file

**Use it when** you wrote the content yourself and want it as a Word file.

1. Put the file, for example `report.md`, in the folder the assistant works in (or upload it
   in the chat).
2. Type:

   ```text
   Turn report.md into a Word file called report.docx
   ```

3. The assistant uses your file **exactly as written** and makes `report.docx`.

What you can write in Markdown:

```markdown
# Main heading

## Sub-heading

Plain text, **bold**, *italic*

- first item
- second item

| item | price |
|---|---|
| pen | 10 |

![chart](chart.png)
```

Good to know:

- Images must be PNG or JPEG files in the same folder as the Markdown file, or a folder
  inside it.
- Write Thai the normal way. **Do not put spaces between Thai words.** You may start a new
  line in the middle of a Thai sentence; the words are joined back together.
- If the skill finds something it cannot read, such as an unusual HTML tag, it tells you
  **which line** it is on. Fix that line and ask again.

## Scenario 3: you have the file and want different settings

**Use it when** the file is made but you want another font, size or page numbers.

1. In the same chat, say what you want to change.

   ```text
   Use the font Sarabun at size 14 and put page numbers at the bottom center
   ```

2. The assistant makes the file again, changing only what you asked for.
3. It tells you the new settings. Check that they match your request.

Things you can ask to change:

| you want | say |
|---|---|
| another font | "use the font Sarabun" |
| smaller text | "size 14" |
| Letter or F14 paper | "use F14 paper" |
| landscape pages | "make it landscape" |
| 1 inch margins on every side | "1 inch margins all round" |
| an indent on the first line of each paragraph | "indent the first line 0.5 inch" |
| more space between lines | "line spacing 1.5" |
| Thai text spread to fill each line | "Thai distributed alignment" |
| a table of contents | "add a table of contents" |
| page numbers | "add page numbers" (top right) or "page numbers at the bottom center" |
| no number on the first page | "no page number on the first page" |
| Thai digits | "use Thai digits" (only for page, list and footnote numbers — digits in your text stay as written) |
| text at the top or bottom of each page | "header text: Confidential" |
| hide the spelling squiggles | "hide the spelling squiggles" (real typos are hidden too) |

Every setting: [references/settings.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/settings.md)

## Scenario 4: give the settings in your first message

**Use it when** you already know what you want.

1. Put the settings in your request.

   ```text
   Turn input.md into a Word file called output.docx with text size 14, Letter paper, 1 inch margins on every side, a 0.5 inch first-line indent and line spacing 1.5
   ```

2. The assistant makes the file right away and tells you the settings it used.
3. **Check that every setting you asked for is in its reply.** If one is missing, ask again.

## Scenario 5: have the assistant ask you first (grill mode)

**Use it when** you are not sure what settings to choose and would like to pick from choices.

1. Put the words **`thai-docx grill`** in your message. Without them the assistant does not
   ask.

   ```text
   thai-docx grill Make a Word file with the schedule for our monthly team meeting, in Thai
   ```

2. The assistant asks nine questions, each with choices a, b, c or d:
   - font
   - text size
   - paper and margins
   - paragraph alignment
   - first-line indent
   - table of contents
   - page numbers
   - spelling squiggles
   - whether to save these settings for next time
3. If the questions come as boxes you can click (as in Claude Code), click your choices. If
   they come as a message, answer with the question number and letter. Any question you skip
   keeps its current choice.

   ```text
   4b 7b, keep the rest
   ```

4. The assistant makes the file with your answers.

Good to know:

- Without `thai-docx grill` in your message, the assistant **does not ask** and makes the file
  at once.
- If it makes the file without asking even though you typed `thai-docx grill`, send the same
  message again.

## Scenario 6: nicer headings

**Use it when** you want headings with a color, a size or a position of their own.

1. Describe the headings you want.

   ```text
   Turn notice.md into a Word file; make the top-level heading dark blue, centered and 22 pt, and give the second-level headings a double underline
   ```

2. The assistant adds heading settings at the very top of the Markdown file, like this:

   ```markdown
   ---
   heading-1: font-size: 22pt; color: #1F4E79; text-align: center
   heading-2: text-decoration: underline double
   ---
   ```

3. Heading numbers such as "บทที่ 1" or "1.1" get the same size, font and color as their
   heading.

## Scenario 7: a report or a thesis

**Use it when** your document has a cover, an abstract, a table of contents, chapters,
tables, figures and appendices.

1. List everything the document needs.

   ```text
   Turn draft.md into a Word thesis called thesis.docx with a cover page, an abstract, a table of contents, a list of tables, numbered chapters, table captions like ตารางที่ 1-1, appendices lettered ก ข ค, and page numbers. Do not change the text
   ```

2. The assistant adds **section markers** to the Markdown file. They do not show in the Word
   file.

   | marker | what it does |
   |---|---|
   | `<!-- front -->` | front pages, such as the abstract and contents (numbered ก ข ค) |
   | `<!-- chapters -->` | the chapters: each `#` heading becomes "บทที่ 1", "บทที่ 2" |
   | `<!-- back -->` | back pages, such as the bibliography |
   | `<!-- appendices -->` | appendices: each `#` heading becomes "ภาคผนวก ก", "ภาคผนวก ข" |
   | `<!-- toc -->` | the table of contents goes here |
   | `<!-- list-of-tables -->` | the list of tables goes here |
   | `<!-- list-of-figures -->` | the list of figures goes here |

3. A table caption is a paragraph `Table: caption text` **before the table**; a figure
   caption is a paragraph `Figure: caption text` **after the image**. Leave one blank line
   between the caption and the table or image. In Word they read "ตารางที่ 1-1 caption text"
   and "รูปที่ 1-1 caption text".
4. When you open the file, update the fields to get the page numbers in the lists (in Word:
   Ctrl+A, then F9).

Good to know:

- The lists already hold their entries when the file opens; only their **page numbers** wait
  for the field update.
- If you ask for something the document has nothing for — for example a different word for
  "บทที่" when there is no `<!-- chapters -->` marker — the skill warns that the setting
  "changed nothing".

## Scenario 8: save your settings as a profile

**Use it when** you have settings you like and want to use them again without repeating them.

**Way 1: while answering grill questions.** The last question asks whether to save. Answer b
and give a name.

```text
1c 9b name it myreport
```

**Way 2: just say it.**

```text
Save these settings as a profile called thesis: size 15, Thai distributed alignment, page numbers at the bottom center
```

The assistant tells you the profile's name and where it was saved.

- **Claude Code**: in `~/.thai-docx/profiles/NAME.json`, for all your projects. Say "save it
  in this project" to keep it in the project's `.thai-docx/profiles/` instead.
- **Claude on the web or in the app**: the assistant gives you a `.json` file. **Keep that
  file yourself** and attach it next time.

A profile name may use English letters, digits, `-` and `_`, with no spaces.

## Scenario 9: use a saved profile

1. Name the profile in your request.

   ```text
   Turn chapter2.md into a Word file using the profile thesis
   ```

2. The assistant makes the file with the profile's settings and tells you which profile it
   used.
3. To change something for this file only, add it. What you add wins over the profile.

   ```text
   Use the profile thesis, but size 18 this time
   ```

To see which profiles you have:

```text
Which thai-docx profiles do I have?
```

## Scenario 10: share a profile, or use someone else's

**Send one to a friend**

1. Type:

   ```text
   Export the profile thesis as a file
   ```

2. You get `thesis.json`. Send it any way you like: email, chat, a shared drive.

**Use one a friend sent you**

1. Put the `.json` file in the folder the assistant works in, or attach it in the chat.
2. Type:

   ```text
   Import the profile from thesis.json
   ```

3. To give it a different name, say so: "import it as school-thesis".

The skill always checks the file first. A profile may hold settings and nothing else; a file
with anything more is refused.

## Scenario 11: edit a profile by answering questions

**Use it when** you have a profile and want to adjust a few things, saving the result under a
new name (the old profile stays as it is).

1. Type `thai-docx grill from` the old profile's name, `save to` the new name.

   ```text
   thai-docx grill from thesis save to thesis-v2 Turn input.md into a Word file called output.docx
   ```

   Thai words work too:

   ```text
   thai-docx grill จาก thesis บันทึกเป็น thesis-v2
   ```

2. The assistant asks the questions as in scenario 5, but **the choices your old profile
   already has are marked "(current)"**.
3. Answer only what you want to change. Anything you skip stays as in the old profile.

   ```text
   2b 6a, keep the rest
   ```

4. The assistant saves the new profile `thesis-v2` and makes the file with it.

To be asked only some questions, add `only` and the question names, separated by commas:

```text
thai-docx grill from thesis save to thesis-v3 only size,toc
```

Question names: `font`, `size`, `paper` (paper and margins), `align` (alignment), `indent`
(first-line indent), `toc` (table of contents), `page-numbers`, `squiggles`, `save`. You can
use the question numbers 1 to 9 instead.

Good to know:

- `from`, `save to` and `only` must come **straight after `thai-docx grill`**.
- If there is no profile with the name you gave, the assistant says it was not found. Check
  the name.

## Scenario 12: edit a profile by saying what to change

**Use it when** you know exactly what should change.

```text
Make a profile thesis-v2 from the profile thesis, but with size 14 and no table of contents
```

The assistant saves a new profile that matches the old one except for what you said.

You can **take things out**, such as "no table of contents" or "no page numbers": the skill
puts that setting back to its default (the assistant uses `--default` for you).

## Scenario 13: check a Thai Word file you already have

**Use it when** a Word file from somewhere else has squiggles, odd line breaks or bold that
does not work.

1. Put the file in the folder the assistant works in, or attach it.
2. Type:

   ```text
   Check report.docx and tell me why every Thai word has a red squiggle
   ```

3. The assistant explains each problem it found and what it causes in the file.

Good to know: the skill **only checks; it does not repair** the file. If you have the
content, make a new file with scenario 1 or 2.

---

## When something goes wrong

| you see | it means | what to do |
|---|---|---|
| the assistant mentions a **warning** | the file was made, but there is something to know, such as a font without Thai letters or a setting that had no effect | read the warning and fix it if needed |
| the assistant mentions an **error on line …** | the skill could not read that line of the Markdown; no file was made | fix that line, for example remove the HTML tag, and ask again |
| the assistant mentions **findings** | a fault in the skill itself; no file was made | report it on the [Issues](https://github.com/sayam/thai-docx-skill/issues) page |
| Thai text in Word looks like a strange font | the computer does not have the font set in the file | install that font, or ask for another one (scenario 3) |
| the table of contents has no page numbers | the fields have not been updated | in Word press Ctrl+A, then F9 |
| the assistant did not ask questions though you wanted it to | your message did not contain `thai-docx grill` | send it again with those words |
