# Fix a problem

Every limit in one place — what the skill promises, what you must do after opening the file,
what does not renumber itself, and where the five applications differ:
`skills/thai-docx/references/limits.md`.

Find what you see in the left column.

[Guide home](../en.md) · [ภาษาไทย](../th/troubleshooting.md)

## Installing

| you see | why | what to do |
|---|---|---|
| the app does not list thai-docx | the folder is in the wrong place, or one level too deep | the path must end `skills/thai-docx/SKILL.md`, not `skills/thai-docx/thai-docx/SKILL.md`; then restart the app |
| the Claude app refuses the upload | code execution is off, your organization turned off skills you make, or it is version 0.1.0, whose description is longer than the app accepts | turn on **Code execution and file creation**, ask an owner, or download a version newer than 0.1.0 ([Claude apps](install.md#claude-apps)); otherwise [open an issue](https://github.com/sayam/thai-docx-skill/issues) with the message |
| the Gemini app refuses the upload | Google asks for `SKILL.md` in the zip's main folder | zip the contents of the `thai-docx` folder and upload that ([Gemini app](install.md#gemini-app)) |
| ChatGPT says **Needs Review** or **Blocked** | your workspace checks uploaded skills | ask your workspace admin |
| the assistant says Python or Node.js is missing, or the build fails with a Python error | the computer has neither, or Python is older than 3.11 | install Python 3.11+ or Node.js 22+ |
| the assistant writes a Word file its own way, without the skill | it did not pick the skill | start your message with `/thai-docx` (Claude Code, Copilot, Cursor), `$thai-docx` (Codex) or "Use the thai-docx skill" |

## Making a file

| you see | why | what to do |
|---|---|---|
| a **warning** | the file is made, but something needs a look: a font with no Thai letters, or a setting that changed nothing | read it and change the request if needed |
| an **error on line …** | that line of the Markdown has something the skill does not take, such as an HTML tag; no file is made | fix that line and ask again |
| **findings** | a fault in the skill itself; no file is made | please report it on [Issues](https://github.com/sayam/thai-docx-skill/issues) |
| an image is refused | it is not PNG or JPEG, it is on the internet, or it is outside the Markdown file's folder | use a PNG or JPEG in that folder, or say which folder it is in |
| a setting you asked for is not in the reply | the assistant missed it | ask again for that setting |
| the assistant asked questions you did not want | your message contains `thai-docx grill` — wherever it stands, even in "don't use thai-docx grill" | send it again without those words |
| the assistant did not ask questions | your message did not contain `thai-docx grill` (between `thai` and `docx` a hyphen, an underscore or a space; before `grill`, a space) | send it again with those words |
| `'' is not a question` | a space after a comma in `only size, toc` | write `only size,toc` |
| a saved profile is not found in a chat app | chat apps forget files when the chat ends | attach the profile's `.json` file |
| saving a profile needs approval, or fails | the app does not let the assistant write outside your project | approve it, or say "save it in this project" |

## Opening the file

| you see | why | what to do |
|---|---|---|
| Thai text in an odd font | the computer does not have the font in the file | install that font, or ask for a font you have |
| the table of contents or lists have no page numbers | the fields have not been updated | Word: Ctrl+A, then F9; LibreOffice: Ctrl+Shift+F9; WPS: **References > Update** |
| in WPS Writer, บทที่ or ภาคผนวก numbers look garbled | seen once on 19 September 2026; it did not happen again on 23 September 2026, and the cause is not known | please [open an issue](https://github.com/sayam/thai-docx-skill/issues) with a screenshot; meanwhile open the file in Word |
| in WPS Writer, ำ sits over the wrong letter | the file was made with `--thai-language`, and WPS mishandles the Thai language mark it writes | make it again without that flag — then Word takes the language from the machine, which every machine that types Thai has (LibreOffice uses its own setting instead; see below) |
| squiggles under Thai words in a file **this skill made**, on somebody else's computer | that computer has no Thai among its languages, so Word proofs the Thai as another language | make it again with `--thai-language` ("guarantee Thai on any machine"); ำ will then sit wrongly in WPS Writer |
| in LibreOffice Writer, every Thai word is underlined (the status bar shows Hindi or another language) | LibreOffice does not take the language from the computer; it uses its own default for complex text layout, which on the English installation read was Hindi | Tools → Options → Languages and Locales → General: set the default for complex text layout to Thai. Whether making the file with `--thai-language` fixes it there has not been measured |
| in Word, a red underline under code | code is not a word in any language; the underline does not print | nothing to fix; to hide it on screen, ask to hide the spelling squiggles (`--hide-spelling-errors`) |
| in Google Docs, the table of contents has another font | Google Docs turns it into its own object | nothing to fix in the file; Word shows it as made |
| in Google Docs, the list of tables and the list of figures became heading lists like the contents | the lists were updated there; Google Docs has no list of tables or figures of its own, so it rewrites all three from headings | **do not ask Google Docs to update the lists** — the entries are already in the file, so read them as they came. If they are already overwritten, download the document again and update in Word, LibreOffice or WPS |
| in Word for the web, the tone marks float above the letter | Word for the web has no TH Sarabun New, and the font it substitutes places the marks wrongly | for a document to be read or edited there, make it again with `--font "TH SarabunPSK"` ("use TH SarabunPSK"), which is in its font list |
| squiggles under Thai words in a file made elsewhere | the file does not mark Thai as Thai | check it ([scenario 13](scenarios.md#scenario-13-check-a-word-file-you-already-have)) and make it again with the skill |

Still stuck? [Open an issue](https://github.com/sayam/thai-docx-skill/issues) with what you typed,
the app, and what you saw. Do not attach a real person's document; make a short example instead.
