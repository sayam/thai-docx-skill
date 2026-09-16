# 0029 — Grill from a profile and save as another: the interview is data, read by the script (restated)

- Status: accepted
- Decided: 2026-09-16
- Supersedes: 0026

## Where it came from

With profiles (0024) a user can keep the settings an interview found, but not start the
next interview from them. The maintainer asked for exactly that: "grill-me from thesis,
save to thesis-v1" — ask again, with the thesis profile's answers already in place, and keep
the result under a new name. 0026 made the interview the user's word, read by the script;
this record keeps that and gives the words two more parts. It also moves the nine questions
out of hand-kept prose into the settings registry of 0028, because the questions a start
profile changes must be computed, not written.

## Decision

**The mode is still read, not chosen** — everything 0026 decided about `thai_docx grill
--said "<the user's own message>"` stands: the phrase `thai-docx grill`, in any case, with
`-`, `_` or a space, the first 20,000 characters, and nothing else turning the interview on.

**Three optional parts follow the phrase**, read from the words directly after it, in any
order, each once; the first word that is none of them ends the reading:

| part | English | Thai | takes |
|---|---|---|---|
| start from a profile | `from` | `จาก` | a profile name or path, looked up as `--profile` looks it up |
| save the answers | `save to` | `บันทึกเป็น` | a name, never a path — written to the user's own profiles |
| ask only some questions | `only` | `เฉพาะ` | question keys or numbers, comma-separated: `font`, `size`, `paper`, `align`, `indent`, `toc`, `page-numbers`, `squiggles`, `save` |

A Thai word may be written against its value (`บันทึกเป็นthesis-v1`). A profile that is not
found, a save name that is a path, or a question key that does not exist is an error the
command reports as JSON, naming the word; nothing is asked.

**The command answers with the questions themselves.** In grill mode the JSON carries, in
the language of the message: `start` (the profile's name, where it was found, and its
settings), `save_to`, and `questions` — each with its number, key, text and fixed choices.
Every choice carries:

- `current: true` when the start's settings are what that choice sets — with no start, the
  defaults, so choice a; when no fixed choice matches (a font the list does not have), the
  "other" choice is current;
- `args`: the exact flags that make the choice true *relative to the start* — nothing for
  the current choice, `--default SETTING` for a choice that puts a setting back to its
  default, the setting's own flag otherwise; an "other" choice carries its flag with a
  placeholder (`--font NAME`) for the value the user types.

An unanswered question keeps the current choice. With `save to`, question 9 is not asked.
`next` names the commands to run with the chosen args: `profile save SAVE_TO [--from START]
ARGS` and then `build … --profile SAVE_TO`; without `save to`, `build … [--profile START]
ARGS`.

**`--default SETTING[,SETTING…]`** is new: on `build` with `--profile` and on `profile
save --from`, it drops the named settings from the profile before any flag is applied, so
"no table of contents" can be said to a profile that has one. Without a profile it changes
nothing, since the setting already is its default. An unknown setting is refused with the
list of settings.

**The questions are data, and reach the agent only through the command.** The nine
questions — font; size; paper and margins; alignment; first-line indent; table of contents;
page numbers; spelling squiggles; keeping the answers — live in the registry module beside
the settings, each choice as the settings it sets, in both implementations, held equal by a
test; the flag each choice maps to is computed, not typed. `references/interview.md` says
how to ask and what to run afterwards, and holds no question: an agent that did not run the
command on the user's message has nothing to ask. On 2026-09-16, before this record, Haiku
twice went around the command — once reading the questions straight from that file after
invoking the skill with `grill` itself, once passing the command the user's message with
the phrase cut out, so the command answered `build` (`docs/evidence/2026-09-16-agents-after-the-redesign.md`).
SKILL.md now asks for the message whole, the skill's name included.

**Asking stays as 0026 set it:** the client's question tool when it has one (at most four
questions a call), otherwise one message answered in short form such as `1a 5b`; the agent
asks the questions the JSON lists, in their order, with their letters, and marks the current
choice.

Left out on purpose:

- Asking by group (page and type, furniture, tables, thesis) with "keep as is" per group —
  the grouped interview a draft proposed. The nine flat questions stay; `only` narrows them.
- Letters that move with the start profile (choice a always the current value): fixed
  letters keep a short-form answer meaning the same thing whatever the start.
- The script taking the user's answers and saving the profile itself: the agent still runs
  `profile save`, whose output the user sees; the script only computes what each choice means.
- Question keys in Thai: one set of keys, which the agent can read to the user in either
  language.
- Questions for the thesis settings of layer 5 and the table settings of layer 3: they are
  set by flags or a profile, as before.

## Why

Starting from a profile turns the interview from a one-off into a way of maintaining a
house style. The part that can go wrong is working out what each answer means against the
profile — a "no" that must undo a "yes" — and that is arithmetic on settings, which the
script does the same way in both implementations and a test can hold; an agent asked to do
it in its head would do it differently on each model. Keeping the phrase and adding words
after it keeps 0026's guarantee: nothing but the user's own words starts the interview.

## Expires when

The interview needs a question that is not a choice among settings, or a client passes the
user's answers to the skill without the agent in between.
