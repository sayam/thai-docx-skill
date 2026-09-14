# thai-docx-skill

An [Agent Skill](https://agentskills.io/specification) that makes Word (.docx)
documents with Thai or mixed Thai–English text render correctly: no spelling
squiggles under every Thai word, Thai lines that wrap inside words, bullets and
bold that work. The agent writes Markdown; one bundled command builds the
document and checks it without changing a character of the content.

**Status: under construction — v0.1.0 is not released.**

## Where things are

- `skills/thai-docx/` — the skill itself; the only part that ships
- `docs/adr/` — the decision records; `docs/adr/README.md` is their index
- `docs/handoff/` — the diagnosis this skill started from, kept verbatim
- `docs/templates/decision.md` — the shape of a new record
- `SOURCES.md` — the sources the records cite, by id
- `tools/` — verifiable-gates; `python3 tools/gates_doctor.py` runs the gates

## Adding a decision

1. Copy `docs/templates/decision.md` to `docs/adr/NNNN-short-slug.md`, taking
   the next number — no gaps, no repeats.
2. Add its row to `docs/adr/README.md`. The doctor is red until you do.
3. Give every outside source it leans on a row in `SOURCES.md` and cite it by
   id, as `[S1]`.
4. A record that replaces an older one says `Supersedes: NNNN`, and the older
   one gets `Superseded by: NNNN` — the doctor reads both sides.

## Commits

Conventional Commits, signed off with `git commit -s`, and no assistant
trailers — see `docs/adr/0013`.

## License

MIT — see `LICENSE`.
