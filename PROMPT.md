# thai-docx for chat apps without skills

[ภาษาไทย: อธิบายทีละขั้น](PROMPT.th.md)

For an AI chat app that does not load Agent Skills but can run Python on files you
upload. Upload `thai-docx-<version>.zip` from this repository's releases — the file under
**Assets**, not *Source code*, and not unzipped — then paste everything below the line as your
first message, followed by your request.

The document comes out byte for byte the same as the skill makes it, because the
same program makes it. An app that cannot run Python on an uploaded file cannot use
this; ask it for Markdown instead and build the file yourself with
`python3 thai-docx/scripts/thai_docx build doc.md doc.docx`.

This route has not been tried in any app yet. If you try it, please say in an
[issue](https://github.com/sayam/thai-docx-skill/issues) which app you used and what happened.

If something goes wrong:

| what you see | what to do |
|---|---|
| the app cannot take a zip file | it cannot use this; try an app with skills, or build the file yourself: [without AI](https://github.com/sayam/thai-docx-skill/blob/main/docs/guide/en/command-line.md) |
| the app cannot run Python, or has none | turn code execution on in its settings; if it has none, ask it for the content as Markdown and build the file yourself as above |
| the app says its Python is too old | the program needs Python 3.11 or later; this app cannot use it |
| the app writes its own code to make the Word file | say "use the program in thai-docx, as my first message says" |
| every Thai word in the file has a red squiggle | the app did not use the program; say so as above, and ask for the file again |
| the app reports an **error on line …** | that line holds something the program does not take; ask the app to change that line without changing its meaning |
| the app asks about fonts though you did not write `thai-docx grill` | say "use the defaults for now" |

Never attach anybody's real document to an issue.

---

You have `thai-docx-<version>.zip`, uploaded with this message. It holds a program that
builds Word documents with Thai text correctly. For any Word (.docx) file I ask for that
contains Thai, follow these rules instead of writing document code of your own.

1. Unzip the archive once. Read `thai-docx/SKILL.md` and follow it. It is written for
   agents; in it, `<skill>` is the `thai-docx` folder you unzipped.
2. Write the content as a Markdown file, then run
   `python3 <skill>/scripts/thai_docx build doc.md doc.docx` and read the JSON it prints.
   Do not use python-docx or any other library, and do not read the program's source.
3. Do not add spaces between Thai words or zero-width characters, and never change my
   wording to get a build through.
4. Give me the .docx as a file, and tell me in two or three lines, in my language, the
   settings it used and that any of them can be changed.
5. Do not ask me about fonts or layout unless my message says `thai-docx grill`.
