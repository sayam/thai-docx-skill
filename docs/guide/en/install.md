# Install and start

Every app takes the same file: `thai-docx-<version>.zip` from the
[Releases](https://github.com/sayam/thai-docx-skill/releases) page. Inside it is one folder,
`thai-docx/`. Find your app below, follow its steps, then try your first request.

[Guide home](../en.md) · [ภาษาไทย](../th/install.md)

## What works where

The **tried** row says whether the maintainer has run thai-docx in that app. Apps not tried yet
are described from their makers' documentation, as read on 17 September 2026; if something there does not work,
please [open an issue](https://github.com/sayam/thai-docx-skill/issues).

| | Claude apps | Claude Code | ChatGPT | Codex | Gemini app | coding agents | no AI |
|---|---|---|---|---|---|---|---|
| tried | yes | yes | not yet | not yet | not yet | not yet | yes |
| make a file (scenarios 1–4, 6, 7) | yes | yes | yes | yes | yes | yes | yes |
| questions first (5, 11) | as a message | click choices | depends on the app | depends on the app | depends on the app | depends on the app | — |
| profiles kept (8–12) | no: keep the `.json` file | yes | no: keep the `.json` file | yes | no: keep the `.json` file | yes, except cloud agents | yes |
| check a file (13) | yes | yes | yes | yes | yes | yes | yes |
| you get the file | download it in the chat | in your folder | download it in the chat | in your folder | not known yet | in your folder | in your folder |

"Keep the `.json` file" means: a chat app forgets files when the chat ends. When you save a
profile, the assistant gives you a `.json` file. Keep it, and attach it when you want to use it.

## Claude apps

Claude on the web (claude.ai) and the Claude desktop app. A skill you upload belongs to your Claude
account; Claude's help pages say Cowork and the Claude add-ins for Word, Excel, PowerPoint and
Outlook use it too.

**Before you start**

- Any plan: Free, Pro, Max, Team or Enterprise.
- Code execution must be on. On Free, Pro and Max: **Settings > Capabilities**, turn on
  **Code execution and file creation**. On Team, skills are on by default; check that code execution
  is on too. On Enterprise, an owner turns on code execution and skills in
  **Organization settings > Skills**.

**Install**

1. Download `thai-docx-<version>.zip`. Do not unzip it.
2. In Claude, go to **Customize > Skills**.
3. Select **+**, then **Create skill**, then **Upload a skill**.
4. Choose the zip file. thai-docx appears in your list of skills.
5. Make sure its switch is on.

Tried on 18 September 2026 with `thai-docx-0.1.1.zip`: the upload was accepted, a security scan
ran on save, and the skill appeared under **Created by you** with its switch on. Claude's help page
gives skill descriptions a limit of 200 characters, which version 0.1.0's exceeded; 0.1.1 and later
fit. If an upload is refused, please
[open an issue](https://github.com/sayam/thai-docx-skill/issues) with the message.

**Start**

Open a new chat and type:

```text
Make a Word file in Thai with a short guide to saving water at home
```

Claude makes the file. Download it from the chat.

**Good to know**

- To use your own Markdown file, images or Word file, attach them to the chat.
- Questions (scenario 5) come as a message. Answer with the numbers and letters, such as `2b 7c`.
- Do not count on files lasting after the chat. Keep any profile `.json` file the assistant gives you.
- If you cannot upload, an owner of your organization may have turned off skills you make yourself.
- On Team and Enterprise, you can share the skill with others: **⋯ > Share** on the skill.
- Sources: [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude),
  [Create and edit files with Claude](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude).

## Claude Code

**Before you start**

- Python 3.11 or newer, or Node.js 22 or newer, on your computer. Check with `python3 --version`
  or `node --version`. Claude Code itself does not need them, so they may be missing.

**Install for all your projects**

1. Download `thai-docx-<version>.zip`.
2. Unzip it into the skills folder of Claude Code:

   ```sh
   mkdir -p ~/.claude/skills
   unzip thai-docx-0.1.1.zip -d ~/.claude/skills
   ```

   On Windows, in PowerShell:

   ```powershell
   Expand-Archive thai-docx-0.1.1.zip -DestinationPath $HOME\.claude\skills
   ```

3. Check that the file `~/.claude/skills/thai-docx/SKILL.md` exists.

To use it in one project only, unzip it into that project's `.claude/skills` folder instead.

**Start**

1. Start Claude Code in the folder you want the file in. If it was already running and the skills
   folder is new, restart it.
2. Type `/skills` and check that thai-docx is in the list.
3. Type a request, or start it with `/thai-docx`:

   ```text
   Make a Word file in Thai called water.docx with a short guide to saving water at home
   ```

4. When Claude Code asks to run `python3` or `node`, allow it. The file appears in your folder.

**Good to know**

- Questions (scenario 5) come as boxes you click.
- Profiles are saved in `~/.thai-docx/profiles/` and work in every project. With the sandbox on,
  Claude Code may not write there; say "save it in this project" instead.
- If you sign in to Claude Code with your Claude account, skills you uploaded to the Claude apps
  can appear here too.
- Source: [Claude Code skills](https://code.claude.com/docs/en/skills).

## ChatGPT

How you use thai-docx depends on your plan.

| your plan | what to do |
|---|---|
| Business, Enterprise, Edu or Healthcare | upload the skill (below) |
| Free, Go, Plus or Pro | use the ChatGPT desktop app or Codex with the folder: see [Codex](#codex) |
| any plan, on the web, where skills are not offered | the prompt in [PROMPT.md](https://github.com/sayam/thai-docx-skill/blob/main/PROMPT.md) |

**Upload the skill (Business, Enterprise, Edu, Healthcare)**

1. Download `thai-docx-<version>.zip`.
2. In the sidebar, open **Plugins**, then the **Skills** tab.
3. Select **Create**, then **Upload from your computer**, and choose the zip file.
4. ChatGPT checks the upload. If it says **Needs Review** or **Blocked**, ask your workspace admin.
   An admin may also need to allow skills and skill uploads for your workspace.

**Start**

Type a request:

```text
Make a Word file in Thai with a short guide to saving water at home
```

Download the file from the chat.

**Without skills: PROMPT.md**

1. Attach `thai-docx-<version>.zip` to a new chat.
2. Paste the text of [PROMPT.md](https://github.com/sayam/thai-docx-skill/blob/main/PROMPT.md)
   below its line, then your request.

This needs a chat that can run Python on the files you attach. It has not been tried in ChatGPT yet.

**Good to know**

- Attach your Markdown file, images or Word file to the chat.
- Questions (scenario 5) come as a message. Answer with the numbers and letters.
- Do not count on files lasting after the chat. Keep any profile `.json` file you are given.
- Sources: [Skills in ChatGPT](https://help.openai.com/en/articles/20001066-skills-in-chatgpt),
  [Data analysis with ChatGPT](https://help.openai.com/en/articles/8437071-data-analysis-with-chatgpt).

## Codex

For the Codex CLI, the Codex IDE extension and the ChatGPT desktop app, on any plan that includes
Codex.

**Before you start**

- Python 3.11 or newer, or Node.js 22 or newer, on your computer.

**Install**

1. Download `thai-docx-<version>.zip`.
2. Unzip it into your skills folder:

   ```sh
   mkdir -p ~/.agents/skills
   unzip thai-docx-0.1.1.zip -d ~/.agents/skills
   ```

   For one project only, unzip it into that project's `.agents/skills` folder.
3. Check that `~/.agents/skills/thai-docx/SKILL.md` exists.

**Start**

1. Type `/skills` and check that thai-docx is listed. If it is not, restart Codex.
2. Type a request, or start it with `$thai-docx`:

   ```text
   $thai-docx Make a Word file in Thai called water.docx with a short guide to saving water at home
   ```

3. The file appears in your project folder.

**Good to know**

- Codex asks before it writes outside your project. Saving a profile to `~/.thai-docx/profiles/`
  is outside it: approve it, or say "save it in this project".
- Source: [Codex skills](https://developers.openai.com/codex/skills),
  [Codex sandboxing](https://learn.chatgpt.com/docs/sandboxing).

## Google Gemini

### Gemini app

Skills work in Gemini Spark, for Google AI Pro and Ultra on a personal account.

1. Open Gemini Spark, then **Skills**, then **Upload**.
2. Choose `thai-docx-<version>.zip`.
3. In Spark, type a request, or type `/` and pick thai-docx.

Good to know:

- Google's rules: the account holder must be 18 or older, Keep Activity must be on, and it is not
  offered in the EEA, the UK, Switzerland or Nigeria.
- The Gemini app runs `.py` and `.sh` scripts from a skill; thai-docx's Python works, its `.js` file
  is not used. Google's page asks for `SKILL.md` in the main folder of the zip, and thai-docx's zip
  has a folder inside it, so the upload may be refused. If it is, zip the **contents** of the
  `thai-docx` folder and try again.
- Not tried yet, and Google's page does not say whether a Word file can be downloaded. Please
  [open an issue](https://github.com/sayam/thai-docx-skill/issues) with what you see.
- Source: [Skills in Gemini](https://support.google.com/gemini/answer/17094296).

### Antigravity and Gemini CLI

Google replaced Gemini CLI with Antigravity CLI in June 2026. Gemini CLI still works with a paid
Gemini API key or a Gemini Code Assist Standard or Enterprise licence.

- **Antigravity:** unzip the zip into your project's `.agents/skills` folder, so you have
  `.agents/skills/thai-docx/SKILL.md`.
- **Gemini CLI:** run

  ```sh
  gemini skills install https://github.com/sayam/thai-docx-skill.git --path skills/thai-docx
  ```

  Gemini CLI asks for your consent each time it starts the skill. `/skills list` shows it.

Sources: [Antigravity skills](https://antigravity.google/docs/skills/),
[Gemini CLI skills](https://geminicli.com/docs/cli/skills/).

## GitHub Copilot

For Copilot agent mode in VS Code, the Copilot CLI and the Copilot cloud agent.

**Install**

- **For you, in every project:** unzip the zip into `~/.copilot/skills`, so you have
  `~/.copilot/skills/thai-docx/SKILL.md`.
- **For one repository:** unzip it into `.github/skills` in the repository, and commit the folder.
  The Copilot cloud agent uses only skills committed to the repository.
- **With the GitHub CLI** (preview):

  ```sh
  gh skill install sayam/thai-docx-skill thai-docx --scope user
  ```

**Start**

In agent mode, type a request, or start it with `/thai-docx`. Allow the terminal command when
Copilot asks.

**Good to know**

- The cloud agent works in a fresh copy of your repository each time, so profiles are not kept.
  Not tried yet.
- Sources: [About agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills),
  [Agent skills in VS Code](https://code.visualstudio.com/docs/copilot/customization/agent-skills),
  [gh skill install](https://cli.github.com/manual/gh_skill_install).

## Cursor

**Install**

- Unzip the zip into `~/.cursor/skills` (every project) or `.cursor/skills` (one project).
- Cursor also reads `~/.claude/skills`: if you installed thai-docx for Claude Code, it is there already.

**Start**

In Agent, type a request, or start it with `/thai-docx`. Allow the terminal command when asked.

**Good to know**

- Cloud Agents and remote (SSH) sessions do not see skills that exist only on your computer.
- Source: [Cursor skills](https://cursor.com/docs/context/skills).

## Other coding agents

Unzip the zip so the folder `thai-docx` sits in one of these folders. Many agents also read
`~/.agents/skills`, which lets several of them share one copy.

| agent | for you | for one project |
|---|---|---|
| OpenCode | `~/.config/opencode/skills` or `~/.agents/skills` | `.opencode/skills` or `.agents/skills` |
| Goose | `~/.agents/skills` | `.agents/skills` |
| Amp | `~/.config/agents/skills` or `~/.agents/skills` | `.agents/skills` |
| Kiro | `~/.kiro/skills` | `.kiro/skills` |
| Roo Code | `~/.roo/skills` or `~/.agents/skills` | `.roo/skills` or `.agents/skills` |
| Cline | `~/.cline/skills` | `.cline/skills` |
| Junie | `~/.junie/skills` or `~/.agents/skills` | `.junie/skills` or `.agents/skills` |
| Devin Desktop (was Windsurf) | `~/.config/devin/skills` or `~/.agents/skills` | `.devin/skills` or `.agents/skills` |
| Mistral Vibe CLI | `~/.vibe/skills` | `.vibe/skills` or `.agents/skills` |

An installer can put it in place for you instead. It needs Node.js, asks which agents you use,
and sends anonymous usage data unless you set `DISABLE_TELEMETRY=1`:

```sh
npx skills add sayam/thai-docx-skill --skill thai-docx -g
```

Then ask for a Word file, or type `/thai-docx` where the agent has slash commands.

Sources: [agentskills.io clients](https://agentskills.io/clients),
[vercel-labs/skills](https://github.com/vercel-labs/skills), and each agent's skills page:
[OpenCode](https://opencode.ai/docs/skills/),
[Goose](https://goose-docs.ai/docs/guides/context-engineering/using-skills/),
[Amp](https://ampcode.com/docs/customize/skills), [Kiro](https://kiro.dev/docs/skills/),
[Roo Code](https://roocodeinc.github.io/Roo-Code/features/skills),
[Cline](https://docs.cline.bot/features/skills),
[Junie](https://junie.jetbrains.com/docs/agent-skills.html),
[Devin](https://docs.devin.ai/cli/extensibility/skills/overview),
[Mistral Vibe](https://docs.mistral.ai/vibe/code/cli/skills).

## For developers

For your own program. The skill runs in the provider's code container, which has no network and
installs nothing: thai-docx needs neither.

- **Claude API:** upload the zip with `POST /v1/skills`, then send requests with the skill in
  `container.skills` and the code execution tool on. The container has Python 3.11. Get the Word
  file with the Files API. Not on Amazon Bedrock or Google Vertex AI.
  [Skills guide](https://platform.claude.com/docs/en/build-with-claude/skills-guide)
- **Claude Agent SDK:** put the folder in `~/.claude/skills` or `.claude/skills`, and allow the
  `Bash`, `Read` and `Write` tools. [Agent SDK skills](https://code.claude.com/docs/en/agent-sdk/skills)
- **OpenAI API:** upload the zip with `POST /v1/skills` and add a `shell` tool whose container lists
  the skill. The container has Python 3.11 and Node.js 22.
  [Skills](https://developers.openai.com/api/docs/guides/tools-skills)
- **A JavaScript sandbox with no shell:** load `scripts/thai_docx.js` and call
  `ThaiDocx.buildDocument`. [references/sandbox.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/sandbox.md)

## Check the download

Optional. If you have the [GitHub CLI](https://cli.github.com/), check that the zip is the one the
project's release workflow built:

```sh
gh attestation verify thai-docx-0.1.1.zip --repo sayam/thai-docx-skill
```

It says the verification succeeded, or fails for any other file.

## Update or remove

- **Update:** delete the old `thai-docx` folder, then unzip the new zip the same way. In the Claude
  apps or ChatGPT, replace the skill there with the new zip.
- **Which version you have:** `version` near the top of `thai-docx/SKILL.md`.
- **Remove:** delete the `thai-docx` folder, or the skill in the app. Your profiles stay in
  `~/.thai-docx/profiles/` until you delete them.
