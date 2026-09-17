# thai-docx user guide

thai-docx makes Word (.docx) files with Thai text that look right: no red squiggles under every
Thai word, lines that break in the right places, and bold and bullets that work. It never changes
a character of your text.

[ภาษาไทย](th.md)

## Start here

1. **Install the skill in the app you use.** Follow the steps for your app in
   [Install and start](en/install.md).
2. **Ask for a Word file.** Type a request such as:

   ```text
   Make a Word file in Thai that sums up our team meeting, with a heading and a bullet list
   ```

   You get the file, and a short note on the settings it used.
3. **Change what you want.** Say "use size 14" or "add page numbers", and you get the file again.

No AI app? Build files yourself with one command: [Use it without an AI](en/command-line.md).

## Pick your app

| you use | go to |
|---|---|
| Claude on the web or the Claude desktop app | [Claude apps](en/install.md#claude-apps) |
| Claude Code | [Claude Code](en/install.md#claude-code) |
| ChatGPT | [ChatGPT](en/install.md#chatgpt) |
| Codex | [Codex](en/install.md#codex) |
| Gemini, Antigravity or Gemini CLI | [Google Gemini](en/install.md#google-gemini) |
| GitHub Copilot in VS Code, Copilot CLI or the Copilot cloud agent | [GitHub Copilot](en/install.md#github-copilot) |
| Cursor | [Cursor](en/install.md#cursor) |
| OpenCode, Goose, Amp, Kiro, Roo Code, Cline, Junie, Devin or Mistral Vibe, or an installer for several agents | [Other coding agents](en/install.md#other-coding-agents) |
| your own program on the Claude API or the OpenAI API | [For developers](en/install.md#for-developers) |
| a terminal, with no AI | [Use it without an AI](en/command-line.md) |

## Find what you want to do

| I want to | scenario |
|---|---|
| get a Word file quickly | [1. The simplest request](en/scenarios.md#scenario-1-the-simplest-request) |
| turn my own Markdown file into Word | [2. You already have a Markdown file](en/scenarios.md#scenario-2-you-already-have-a-markdown-file) |
| change the font, size, paper or page numbers | [3. Change the settings](en/scenarios.md#scenario-3-change-the-settings) |
| give every setting in one message | [4. Give the settings in your first message](en/scenarios.md#scenario-4-give-the-settings-in-your-first-message) |
| choose settings from a list of questions | [5. Have the assistant ask you first](en/scenarios.md#scenario-5-have-the-assistant-ask-you-first) |
| give headings a color, size or position | [6. Style the headings](en/scenarios.md#scenario-6-style-the-headings) |
| make a report or a thesis | [7. A report or a thesis](en/scenarios.md#scenario-7-a-report-or-a-thesis) |
| keep my settings for next time | [8. Save your settings as a profile](en/scenarios.md#scenario-8-save-your-settings-as-a-profile) |
| use settings I saved | [9. Use a saved profile](en/scenarios.md#scenario-9-use-a-saved-profile) |
| give my settings to a friend, or use theirs | [10. Share a profile](en/scenarios.md#scenario-10-share-a-profile) |
| change a saved profile by answering questions | [11. Edit a profile with questions](en/scenarios.md#scenario-11-edit-a-profile-with-questions) |
| change a saved profile in one sentence | [12. Edit a profile in one sentence](en/scenarios.md#scenario-12-edit-a-profile-in-one-sentence) |
| find out why a Thai Word file looks wrong | [13. Check a Word file you already have](en/scenarios.md#scenario-13-check-a-word-file-you-already-have) |

Something went wrong? See [Fix a problem](en/troubleshooting.md).

## What you need

- **To make files:** Python 3.11 or newer, or Node.js 22 or newer, on the computer or in the app
  that runs the skill. Chat apps with code execution run Python, though their version is not
  published. The skill needs no internet connection and installs nothing.
- **To open files:** Word, LibreOffice, Google Docs or WPS, and the font the file uses.
  The default font is **TH Sarabun New**. If you do not have it, ask for a Thai font you have, or
  install Sarabun free from Google Fonts and ask for it.

## Words in this guide

| word | meaning |
|---|---|
| skill | a folder of instructions and programs that an AI app loads, so it knows how to do a job |
| assistant | the AI app you type to, such as Claude or ChatGPT |
| your folder | the folder the assistant works in; in a chat app, the chat itself |
| Markdown | plain text with a few marks for formatting: `#` for a heading, `**word**` for bold |
| setting | something that controls how the file looks: font, size, paper, page numbers |
| profile | a saved set of settings you can use again |
| grill | a mode where the assistant asks you about the settings before it makes the file |
| field | a part of a Word file that Word works out itself, such as the page numbers in a table of contents |
