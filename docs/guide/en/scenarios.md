# Scenarios

Each scenario is one job, with what to type and what you get. What you type is the same in every
app; where an app differs, the scenario says so. Install the skill first:
[Install and start](install.md).

[Guide home](../en.md) · [ภาษาไทย](../th/scenarios.md)

In a chat app (Claude on the web, ChatGPT, Gemini), "put the file in your folder" means
**attach it to the chat**, and you **download** the Word file from the chat.

---

## Scenario 1: the simplest request

**Use it when** you want a document quickly and do not mind the layout yet.

1. Say what the document is about.

   ```text
   Make a Word file in Thai that sums up how to apply for a passport, with a heading, a bullet list of the documents you need, and a table of fees
   ```

2. The assistant writes the content and makes the file at once, without asking you anything.
3. It tells you the file name and the settings, for example:

   > Made `passport.docx` — TH Sarabun New 16 pt, A4 paper, left margin 1.5 in, other margins
   > 1 in. Any of these can be changed.

The defaults, when you ask for nothing else:

| what | default |
|---|---|
| font | TH Sarabun New, 16 pt |
| paper | A4, portrait |
| margins | left 1.5 in, the others 1 in |
| line spacing | single |
| alignment | left |
| table of contents, page numbers | none |

## Scenario 2: you already have a Markdown file

**Use it when** you wrote the content yourself and want it as a Word file.

1. Put the file, for example `report.md`, in your folder.
2. Type:

   ```text
   Turn report.md into a Word file called report.docx
   ```

3. The assistant uses your file exactly as written and makes `report.docx`.

What Markdown can hold:

```markdown
# Main heading

## Sub-heading

Plain text, **bold**, *italic*, ~~struck out~~, `code`, <u>underlined</u>, H<sub>2</sub>O, x<sup>2</sup>,
<kbd>Ctrl</kbd>, a [link](https://example.com), and a line break<br>here

- a bullet
  - a bullet inside it

1. a numbered item

- [x] a ticked task
- [ ] an open task

| item | price |
|---|--:|
| pen | 10 |

> a quotation

~~~
code, as written
~~~

---

A footnote.[^1]

[^1]: The footnote text.

![chart](chart.png)
```

Good to know:

- Images must be PNG or JPEG. Put them in the same folder as the Markdown file, or a folder inside
  it. For images in another folder, say where they are.
- Write Thai the normal way. **Do not put spaces between Thai words.** You may break a line in the
  middle of a Thai sentence; the words are joined again.
- `title:` and `author:` lines at the very top, between `---` lines, become the file's properties.
- Math such as `$x^2$` stays as plain text, with a warning.
- Other HTML tags are not allowed. If the file has one, the assistant tells you **the line** and
  nothing is made. Fix that line and ask again.
- Full list: [references/markdown.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/markdown.md)

## Scenario 3: change the settings

**Use it when** you have the file but want another font, size, paper or page numbers.

1. In the same chat, say what to change.

   ```text
   Use the font Sarabun at size 14 and put page numbers at the bottom center
   ```

2. The assistant makes the file again, changing only what you asked for.
3. Check the settings in its reply.

What you can ask for:

| you want | say |
|---|---|
| another font | "use the font Sarabun" |
| another text size | "size 14" |
| Letter or F14 paper | "use F14 paper" |
| landscape pages | "make it landscape" |
| other margins | "1 inch margins all round" |
| a first-line indent | "indent the first line 0.5 inch" (body paragraphs only) |
| more space between lines | "line spacing 1.5" (code and footnotes stay single) |
| Thai text spread to fill each line | "Thai distributed alignment" (a paragraph with no Thai stays left) |
| a table of contents | "add a table of contents" |
| numbered headings (1., 1.1, 1.1.1) | "number the headings" |
| page numbers | "add page numbers" (top right), "page numbers at the top center" or "at the bottom center" |
| no page number on the first page | "no page number on the first page" |
| text at the top or bottom of each page | "header text: Confidential", "footer text: Draft" |
| Thai digits (๑ ๒ ๓) | "use Thai digits" (the numbers the skill adds: pages, headings, lists, captions, footnotes; digits you typed stay) |
| no spelling squiggles | "hide the spelling squiggles" (real typos are hidden too) |
| table header row only on the first page | "do not repeat the table header row" |
| wider columns for longer text | "fit the table columns to the text" |
| smaller text in tables | "table text size 14" |

Every setting: [references/settings.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/settings.md).
Ask for something the document has nothing for, such as a table setting with no table, and the
assistant tells you it "changed nothing".

## Scenario 4: give the settings in your first message

**Use it when** you already know what you want.

1. Put the settings in your request.

   ```text
   Turn input.md into a Word file called output.docx with text size 14, Letter paper, 1 inch margins on every side, a 0.5 inch first-line indent and line spacing 1.5
   ```

2. The assistant makes the file at once and lists the settings it used.
3. **Check that each setting you asked for is in the list.** If one is missing, ask again.

## Scenario 5: have the assistant ask you first

**Use it when** you are not sure what to choose and want to pick from choices (grill mode).

1. Put **`thai-docx grill`** in your message, with the hyphen. The start of the message is easiest.
   Without those words, the assistant does not ask.

   ```text
   thai-docx grill Make a Word file in Thai with the schedule of our monthly team meeting
   ```

2. The assistant asks nine questions, each with two to four choices (a to d): font, text size, paper and
   margins, alignment, first-line indent, table of contents, page numbers, spelling squiggles, and
   whether to save the answers as a profile.
3. Answer.
   - In Claude Code, click your choices.
   - In other apps, reply with the question numbers and letters. A question you skip keeps its
     current choice.

   ```text
   4b 7b, keep the rest
   ```

4. The assistant makes the file with your answers.

If you typed `thai-docx grill` and the assistant still made the file without asking, send the same
message again.

## Scenario 6: style the headings

**Use it when** you want headings with their own color, size or position.

1. Describe the headings.

   ```text
   Turn notice.md into a Word file; make the top-level heading dark blue, centered and 22 pt, and give the second-level headings a double underline
   ```

2. The assistant writes heading settings at the very top of the Markdown file:

   ```markdown
   ---
   heading-1: font-size: 22pt; color: #1F4E79; text-align: center
   heading-2: text-decoration: underline double
   ---
   ```

3. Heading numbers, such as "บทที่ 1" or "1.1", take the same font, size and color as their heading.

You can also ask for a font, bold or italic, a strike-through or a dotted, dashed or wavy
underline, justified or Thai distributed alignment, a left margin or hanging indent, space above or
below, line spacing, or a new page before each heading:
[references/heading-styles.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/heading-styles.md).

## Scenario 7: a report or a thesis

**Use it when** the document has a cover, front pages, chapters, tables, figures and appendices.

1. List what the document needs.

   ```text
   Turn draft.md into a Word thesis called thesis.docx with a cover page, an abstract, a table of contents, a list of tables, numbered chapters, table captions like ตารางที่ 1-1, appendices lettered ก ข ค, and page numbers. Do not change the text
   ```

2. The assistant adds **markers** to the Markdown file. They do not show in Word.

   | marker | what it does |
   |---|---|
   | `<!-- front -->` | front pages, such as the abstract (page numbers ก ข ค) |
   | `<!-- chapters -->` | chapters: each `#` heading becomes "บทที่ 1", "บทที่ 2" |
   | `<!-- back -->` | back pages, such as the bibliography |
   | `<!-- appendices -->` | appendices: each `#` heading becomes "ภาคผนวก ก", "ภาคผนวก ข" |
   | `<!-- toc -->` | the table of contents goes here |
   | `<!-- list-of-tables -->` | the list of tables goes here |
   | `<!-- list-of-figures -->` | the list of figures goes here |

3. A table caption is a line `Table: caption` just **before** the table. A figure caption is a line
   `Figure: caption` just **after** the image. Leave a blank line between them. In Word they read
   "ตารางที่ 1-1 caption" and "รูปที่ 1-1 caption".
4. The lists show their entries at once; their page numbers come when the fields are updated.
   Word on a computer offers to update them when the file opens (or press Ctrl+A, then F9).
   LibreOffice: Ctrl+Shift+F9. WPS: **References > Update**.

More you can ask for:

| you want | say |
|---|---|
| numbered sections: 1.1 in chapters, ก.1 in appendices | "number the headings" |
| another word for บทที่ | "chapter label บท" |
| another word for ตารางที่ or รูปที่ | "table label ตาราง", "figure label ภาพที่" |
| front pages numbered i ii iii, I II III or 1 2 3 | "number the front pages in lower-case Roman numerals" |
| another word for ภาคผนวก | "appendix label Appendix" |
| appendices A B C, 1 2 3 or I II III | "letter the appendices A B C" |
| no page number on the first page of each part | "no page number on the first page" |
| บทที่ 1 on one line, the title under it | "put the chapter title on a new line" |

Good to know:

- What comes before the first marker is the cover. Every `#` heading starts a new page.
- The markers go in this order, each at most once: front, chapters, back, appendices, and back
  again. Out of order,
  the build stops and names the line.
- Front pages are numbered ก ข ค only when you ask for page numbers.
- Outside a chapter, captions read "ตารางที่ 1".
- `<!-- toc -->` already places a table of contents; asking for a table of contents too gives a
  second one.

Full rules: [references/chapters.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/chapters.md).

## Scenario 8: save your settings as a profile

**Use it when** you like your settings and want to use them again without repeating them.

**Way 1: when you answer the grill questions.** The last question asks whether to save. Answer b
(for all your projects) or c (this project only), and give a name.

```text
1c 9b name it myreport
```

**Way 2: say it.**

```text
Save these settings as a profile called thesis: size 15, Thai distributed alignment, page numbers at the bottom center
```

Where the profile goes:

- **On your computer** (Claude Code, Codex, Copilot, Cursor and other coding agents):
  `~/.thai-docx/profiles/NAME.json`, for all your projects. Say "save it in this project" to keep it
  in the project's `.thai-docx/profiles/` instead.
- **In a chat app** (Claude on the web, ChatGPT, Gemini): you get a `.json` file. **Keep it**, and
  attach it next time.

A profile name uses letters, digits, `-` or `_`, with no spaces.

Good to know:

- Saving under a name you already use replaces that profile. To keep the old one, give the new
  profile another name.

## Scenario 9: use a saved profile

1. Name the profile in your request. In a chat app, attach its `.json` file too.

   ```text
   Turn chapter2.md into a Word file using the profile thesis
   ```

2. The assistant makes the file with the profile and tells you which one it used.
3. To change something for this file only, add it. What you add wins over the profile.

   ```text
   Use the profile thesis, but size 18 this time
   ```

Or take something out, for this file only:

```text
Use the profile thesis, but without the table of contents
```

A profile file can also be used straight from its path, such as `profiles/thesis.json`, without
importing it.

To see your profiles and their settings:

```text
Which thai-docx profiles do I have, and what is in thesis?
```

## Scenario 10: share a profile

**Send yours**

1. Type:

   ```text
   Export the profile thesis as a file
   ```

2. You get `thesis.json`. Send it by email, chat or a shared drive.

**Use one you received**

1. Put the `.json` file in your folder.
2. Type:

   ```text
   Import the profile from thesis.json
   ```

3. To give it another name, say "import it as school-thesis".

The skill checks the file first. A profile may hold settings and nothing else; anything more is
refused. Say "import it into this project" to keep it in the project only; a project profile wins
over one of the same name in your home folder.

## Scenario 11: edit a profile with questions

**Use it when** you want to adjust a profile and save the result under a new name. The old one
stays as it is.

1. Type `thai-docx grill from` the old name `save to` the new name.

   ```text
   thai-docx grill from thesis save to thesis-v2 Turn input.md into a Word file called output.docx
   ```

   Thai words work too:

   ```text
   thai-docx grill จาก thesis บันทึกเป็น thesis-v2
   ```

2. The assistant asks the questions of scenario 5 (without the save question), with the old
   profile's choices marked "(current)".
3. Answer only what you want to change.

   ```text
   2b 6a, keep the rest
   ```

4. The assistant saves `thesis-v2` and makes the file with it.

To be asked only some questions, add `only` and their names, separated by commas with no spaces:

```text
thai-docx grill from thesis save to thesis-v3 only size,toc
```

Question names: `font`, `size`, `paper`, `align`, `indent`, `toc`, `page-numbers`, `squiggles`,
`save`, or the numbers 1 to 9.

Good to know:

- `from`, `save to` and `only` come **straight after `thai-docx grill`**.
- If no profile has that name, the assistant says it was not found.

## Scenario 12: edit a profile in one sentence

**Use it when** you know exactly what should change.

```text
Make a profile thesis-v2 from the profile thesis, but with size 14 and no table of contents
```

The new profile matches the old one except for what you said. "No table of contents" or "no page
numbers" puts that setting back to its default.

## Scenario 13: check a Word file you already have

**Use it when** a Thai Word file from somewhere else has squiggles, odd line breaks or bold that
does not work.

1. Put the file in your folder.
2. Type:

   ```text
   Check report.docx and tell me why every Thai word has a red squiggle
   ```

3. The assistant explains each problem and what it does to the file.

The skill can repair four of the seven faults with `repair` at the command line, including the
marks every Thai run needs; a split word, invisible characters and misordered properties are
reported instead. The repaired file is bigger. If you have the content, making a new file with
scenario 1 or 2 fixes everything and keeps it small.
