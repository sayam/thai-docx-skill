# Governance

thai-docx-skill is a small project with one maintainer. This page says who decides, how a
decision is made and recorded, who does what, and what happens if the maintainer stops.

## How decisions are made

- **The maintainer decides.** Anyone may propose a change in an issue or a pull request; the
  maintainer accepts or declines it, and says why in the thread.
- **[`docs/rules.md`](docs/rules.md) is the filter every decision passes through**: the scope this
  skill answers for, what an output must be, what it must never introduce, and the compatibility
  contract. A proposal against a rule is declined, with the reason written down. The Thai in that
  file is the rule; the English below it is a translation for reference. A decision record shows
  how a rule was applied and never stands above one.
- **A design decision is written down before it is built**, as a record in
  [`docs/adr/`](docs/adr/README.md): where it came from, the decision, why, what it leaves out, and
  when it expires. A record is never edited into another decision; a new record supersedes it.
- **Every change reaches `main` through a pull request** that passes the required checks —
  `scans`, `commits`, `tests`, `lint`, `deps`, and CodeQL's code-scanning results — for everyone,
  the maintainer included
  ([ADR 0018](docs/adr/0018-users-get-the-skill-contributors-get-the-gates.md)).
- **Rendering questions are settled in Word 365 for Windows**, the reference application; other
  applications' differences are recorded in `docs/evidence/`, not fixed by changing bytes.

## Roles

| role | who | responsibilities |
|---|---|---|
| maintainer | Sayam Sriphua ([@sayam](https://github.com/sayam)) | reviews and merges pull requests; owns the repository settings, rulesets and code owners; writes and accepts decision records; cuts releases and checks them in the office applications (ADR 0012); answers security reports as [SECURITY.md](.github/SECURITY.md) says; enforces the [code of conduct](CODE_OF_CONDUCT.md) |
| code owner | the maintainer (`.github/CODEOWNERS`) | approves any contributor change, and every change to the workflows, the gate registry, the tools and the decision records |
| contributor | anyone | opens issues and pull requests that follow [CONTRIBUTING.md](.github/CONTRIBUTING.md) |
| security reporter | anyone | reports privately through GitHub; credited unless they ask not to be |

## Access

Who holds access to the project's sensitive resources today:

| resource | who |
|---|---|
| GitHub repository: admin, rulesets, merge, releases, security advisories and private reports | Sayam Sriphua (@sayam) |
| Zenodo record of the releases (DOI) | Sayam Sriphua |
| bestpractices.dev project entry | Sayam Sriphua |
| OpenSSF Scorecard results | published by the `scorecard` workflow; no personal access |

The project keeps no long-lived secrets (see [SECURITY.md](.github/SECURITY.md#secrets-and-credentials)).

How access is granted:

- Write, merge, release or admin rights are granted only by the maintainer, and only to a person
  with a sustained record of reviewed contributions to this project whose identity the maintainer
  has confirmed.
- Two-factor authentication is required on any account that holds such rights.
- Every grant, and its reason, is added to the table above in a pull request before it takes effect;
  rights are removed when they are no longer used, or at once if an account may be compromised.

## Continuity

The project has one maintainer, so its bus factor is 1. No second person holds admin or release
rights today, and nobody could merge or release within a week if the maintainer stopped. What
exists so that someone else can continue:

- everything is public and forkable: the full history, the tests, the gates, the decision records
  and the evidence behind each gate;
- a release is built by a workflow from a tag, not on anyone's machine, and each release archive
  is attested; from the first release archived there, each release also has a DOI on Zenodo;
- the licence (MIT) lets anyone continue the work under another name.

When a second maintainer joins, this page will name them, and they will receive admin rights and
the ability to publish releases.

## Changing this document

Like any other change: a pull request, accepted by the maintainer.
