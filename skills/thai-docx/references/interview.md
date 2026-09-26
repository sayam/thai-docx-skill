# Grill mode: asking the questions

Read this only after `thai_docx grill --said "<the user's message>"` answered
`"mode": "grill"` (SKILL.md, Grill mode). The questions are not in this file: they are in
that JSON, under `"questions"`, and there is nothing to ask without it. If you have not run
the command on the user's own message, run it now.

## What the JSON gives

- `"language"`: ask in Thai (`th`) or English (`en`); the texts are already in it. It is the
  language most of the user's words are in, the phrase aside.
- `"warnings"`, when there are any: pass them on before asking — one says a `from` or `save to`
  later in the message was not read, since those are read only directly after the phrase.
- `"start"`: the profile the user asked to start from, or `null` for the defaults.
- `"save_to"`: the name the answers will be saved under, or `null`.
- `"questions"`: in order, each with `number`, `key`, `text` and `choices`. Each choice has
  a `letter`, a `label`, `current` (what holds now), and `args` (the flags that make the
  choice true). An `"other": true` choice asks the user to type a value; a `save` choice
  says where to keep the answers.
- `"next"`: what to run once the user has answered.

Ask exactly those questions, with those labels and letters: do not add, drop, merge or
reword a question or a choice, and do not suggest other values. Mark the current choice —
"(ตอนนี้)" in Thai, "(current)" in English.

## How to ask

- **Your client has a tool for multiple-choice questions** (in Claude Code,
  `AskUserQuestion`): ask at most four questions per call, in order. Each question's text
  is its `text`; each choice is one option, labelled as given, the current one marked. For an
  "other" choice the user types the value; if the tool adds its own free-text option, leave
  that choice out.
- **Otherwise:** one message with every question as `N. text — a) label · b) label …`,
  and let the user answer in short form, e.g. `1b 3c 2d=18 9b=my-thesis` — a value or a name
  after `=`; anything not mentioned keeps its current choice. Say so in the first line.

Ask once, and stop there: save nothing and build nothing until the user has answered — a
start profile is not an answer. If an answer is unclear, keep the current choice and say so
when reporting.

## After the answers

Do all of this in the reply that receives the answers; do not only say what you will do.

1. Collect the `args` of every chosen choice, in question order. For an "other" choice, put
   the user's value where the placeholder is (`NAME`, `N`, `PAPER`, `T,R,B,L`).
2. Run what `"next"` says, with those args in place of `ARGS`: `profile save` then the build
   with `--profile`, or the build with the args. A choice whose args are empty needs nothing.
3. If a command rejects a value (exit 2 naming the flag), tell the user the accepted range
   from its message and use the current choice instead.
4. Report as SKILL.md says; after a save, the profile's name and `--profile NAME`. Where no
   home directory lasts, give the user the saved file.

The questions' keys, for when the user names only some of them: `font`, `size`, `paper`,
`align`, `indent`, `toc`, `page-numbers`, `squiggles`, `save`.
