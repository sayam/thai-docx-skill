# Roadmap

What the project intends to do, and not do, from September 2026 to September 2027. It is a plan,
not a promise; each item becomes a decision record when it is taken up.

## Will do

**Stay correct where users open the files**

- Check every release that changes document bytes in the five office applications of ADR 0012,
  with Word 365 for Windows as the reference.
- Re-check WPS Writer after the fixes of 0.1.0 and record what it still draws its own way.

**Make agents follow the skill more reliably**

- Measure again, on the smallest model, whether agents pass the user's whole message to the grill
  command and add no settings nobody asked for; change the wording the agent reads when it does not.

**Reach more users**

- Try the skill in the applications the user guide lists as "not tried yet" — ChatGPT, Codex, the
  Gemini app, Copilot, Cursor — and mark each as tried or record what fails. The Claude apps were
  tried on 2026-09-18; building a document in them is still to do.
- Keep the release archive installable by the common installers (`npx skills add`, `gh skill install`).
- Submit the skill to curated skill lists by hand (ADR 0014).

**Security and project health**

- Keep code scanning (CodeQL), the dependency check (OSV-Scanner) and OpenSSF Scorecard running
  in CI, and bump every pinned tool by hand.
- Keep the assurance case current, and record a security review done by a person.
- OpenSSF Best Practices: passing (reached 2026-09-18), then silver as far as a one-maintainer
  project can go.

**Markdown and documents** (as users ask)

- More of what theses and official documents need, each as a setting in the registry (ADR 0028) and
  in both implementations.

## Will not do

- Accept input other than Markdown, or run with dependencies at run time (ADR 0007, 0008).
- Reach the network, run other programs, or read settings from environment variables (ADR 0025).
- Change a user's wording to make a build pass (ADR 0023).
- Name or imitate a real institution's template; profiles are for users to make and share.
