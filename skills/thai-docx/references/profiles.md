# Profiles: settings a user keeps, shares and uses again

Read this when the user asks to save settings, to use saved settings, or to take someone
else's (SKILL.md, Profiles). A profile holds settings and nothing else; it can hold nothing
a flag could not.

## The commands

```sh
thai_docx profile list                       # every profile found, and which one wins
thai_docx profile show NAME                  # its settings, and the settings a build resolves
thai_docx profile save NAME [flags]          # the flags as a profile of the user's own
thai_docx profile save NAME --from OTHER [flags]   # start from another profile
thai_docx profile save NAME --from OTHER --default toc,size   # …with those settings back to their defaults
thai_docx profile save NAME [flags] --project      # for this project, not the user
thai_docx profile export NAME [OUT.json]     # the file to send to someone
thai_docx profile import FILE.json [--name NAME] [--project]
thai_docx build IN.md OUT.docx --profile NAME|PATH [flags]
```

Each prints one JSON line, as `build` does: `"ok"`, the `"path"` written or read, the
`"settings"`, and `"sha256"` — the same profile gives the same sha256 in both runtimes.

## What to tell the user

- **Saving:** say the name, where it was written, and that `--profile NAME` uses it. When
  `"replaced"` is true (`save` or `import`), pass on its warning: it replaced the profile of that
  name.
- **Sharing:** `profile export` writes one JSON file; the user sends it by any means. The
  other person runs `profile import FILE.json`. `"share"` in the output is that sentence.
- **Building:** a build that used a profile reports it under `"profile"`; say the name, and
  read the settings from `"settings"` as always.
- **No home directory** (a chat app's container): the saved file is at the `"path"` printed
  — give it to the user to keep, and say to attach it next time.

## The rules

- **Where a name is found**, first wins: a path (it has `/` or ends `.json`), then
  `./.thai-docx/profiles/`, then `~/.thai-docx/profiles/`, then the skill's own.
- **`save` and `import` write** to `~/.thai-docx/profiles/` — with `--project`, to
  `./.thai-docx/profiles/`. Nowhere else; a name is a name, never a path.
- **Precedence:** the defaults, then the profile, then the flags typed after it. A flag can
  only add to a profile; `--default SETTING[,SETTING]` after `--profile` or `--from` takes
  settings out of it first, back to their defaults.
- **A profile is refused** when it holds a key or a value the build would refuse, naming the
  file and the key. The message is the flag's own, so fix the setting it names.
- **Settings** are the build's own names (`size`, `align`, `page_numbers`, `margins`, …);
  `profile save` writes only what differs from the defaults.
