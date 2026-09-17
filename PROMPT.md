# thai-docx for chat apps without skills

[ภาษาไทย: อธิบายทีละขั้น](PROMPT.th.md)

For an AI chat app that does not load Agent Skills but can run Python on files you
upload. Upload `thai-docx-<version>.zip` from this repository's releases, then paste
everything below the line as your first message, followed by your request.

The document comes out byte for byte the same as the skill makes it, because the
same program makes it. An app that cannot run Python on an uploaded file cannot use
this; ask it for Markdown instead and build the file yourself with
`python3 thai-docx/scripts/thai_docx build doc.md doc.docx`.

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
