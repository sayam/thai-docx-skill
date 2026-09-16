# 0024 — Profiles are data: settings a user saves, exports and imports

- Status: accepted
- Decided: 2026-09-16

## Where it came from

With the settings grown to twenty-five flags, the maintainer asked that a user who has
found the ones their work needs — by grill mode or by trying — be able to keep them, and
to hand them to someone else: "บางคนสร้าง/grill ไว้ตรงกับงานแล้ว อยากจะแบ่งปันให้คนอื่นใช้".
Exporting and importing a profile also settles what a contributor can add: a profile
travels by any channel, so the skill does not have to be the only place profiles live.

A longer design exists in `.local` for a feature registry that would generate the schema,
the questions and the documentation (a draft in `.local`, now numbered 0026). This record takes the half that does not
need it; the registry comes later and changes how a profile is validated, not what it is.

## Decision

**A profile is a JSON file of settings, and nothing else.** Its keys are `schema` (1),
`id`, `title` and `description` (`th`, `en`), `version`, `source`, `maintainer`, and
`settings`. Settings are the build's own names — `size`, `align`, `margins`,
`page_numbers`, … — and a profile may hold any subset; what is absent stays at the
default. No code, no conditions, no reference to another profile.

**It is checked as a command line is.** Each setting is written out as the flag that sets
it and read by the build's own parser, so a profile can hold nothing a command line could
not, and a value outside a flag's range is refused with that flag's own message, naming the
file. A profile larger than 64 KiB, or not JSON, or holding an unknown key, is refused.

**Precedence:** the defaults, then the profile, then the flags typed after it —
`--profile thesis --size 18` is the profile with 18-point text.

**Where a name is found**, first match wins: a path (it holds `/` or ends `.json`), then
`./.thai-docx/profiles/<name>.json`, then `~/.thai-docx/profiles/<name>.json`, then
`<skill>/profiles/<name>.json`. A name is a name, never a path: no separator, no leading
dot, at most 64 characters.

**The commands**, each printing one JSON line as `build` does:

- `profile list` — every profile found, where, and which one a build would use;
- `profile show NAME` — its settings, the settings a build would resolve, and the sha256;
- `profile save NAME [--from NAME] [--project] [flags]` — the flags as a profile, written
  to the user's own directory, or the project's with `--project`; only what differs from
  the defaults is written;
- `profile export NAME [OUT.json]` — the file to send, with the sentence that says how the
  other side takes it;
- `profile import FILE.json [--name NAME] [--project]` — someone else's file, checked
  before it is written, `"replaced"` saying whether it took the place of one.

**One written form:** UTF-8 JSON, keys sorted, two-space indent, no escaped non-ASCII, one
trailing newline, integers and floats as Python writes them — the same bytes from both
implementations, so a shared profile has one sha256 wherever it is written. The build
reports the profile it used, where it came from, and that sha256.

**Grill mode** gains a ninth question: keep these settings, as mine or in this project,
under a name (ADR 0026). Where no home directory lasts — a chat app's container — the agent
gives the user the saved file and says to attach it next time.

Left out on purpose:

- A `default` profile every build uses: nothing is a profile until the user asks, so a
  document built today keeps its bytes tomorrow.
- Profiles that extend other profiles: `save --from` copies instead.
- A profile in the front matter of a Markdown file: the file would then carry settings the
  text does not show, and two places would decide one build.
- Templates — fixed layouts with named fields, such as a government letter's blocks. They
  need more than settings.

## Why

Data can be read by anyone who knows the document it describes, cannot run, and gives the
same file from either implementation — so 0007's promise (any model, the same file) holds
per profile. Checking a profile by writing it out as flags means one set of rules, not two:
a setting a flag refuses is refused in a profile, with the same words, on the day the flag
gains a range. Export and import are a file and a command because that is what every
channel carries — mail, chat, a repository — and it needs no account anywhere.

## Expires when

A setting needs a value that depends on the document, profiles need to be listed or fetched
from somewhere central, or the registry of draft 0026 lands and takes over validation.
