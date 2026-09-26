# Security policy

## Reporting a vulnerability

Use GitHub's private vulnerability reporting for this repository:
**Security → Report a vulnerability** on
<https://github.com/sayam/thai-docx-skill/security/advisories/new>. It is the only
channel; no address is published here.

## What to expect

- Acknowledgement within **3 days** of the report.
- An assessment — confirmed, not reproducible, or out of scope — within **14 days**.
- A fix or a mitigation before disclosure, and coordinated disclosure no later than
  **90 days** after the report unless we agree otherwise with you.
- Credit in the release notes and the advisory, if you want it.

## Security contact

Sayam Sriphua ([@sayam](https://github.com/sayam)), the maintainer, receives every private report.

## Supported versions

Only the latest release is supported, until the next release is published. Support means bug and
security fixes, released as a new version; fixes are not back-ported to older versions, so a release
stops receiving security updates when the next one comes out. Download a tagged release archive
rather than using `main`.

## How fixed vulnerabilities are published

Each confirmed vulnerability is published as a GitHub Security Advisory on this repository, naming
the affected and the fixed versions and crediting the reporter, and is listed under `### Security`
in `CHANGELOG.md` for the release that fixes it. If a vulnerability in a component the project uses
is found not to affect thai-docx, an OpenVEX statement saying so is published in the repository.

## Verify a release

Each release archive is built from its tag by the `release` workflow and carries a signed
build-provenance attestation (Sigstore, with GitHub's OIDC identity — no signing key is stored
anywhere). Check a download before you install it:

```sh
gh attestation verify thai-docx-<version>.zip --repo sayam/thai-docx-skill \
  --signer-workflow sayam/thai-docx-skill/.github/workflows/release.yml --source-ref refs/tags/v<version>
```

It fails for any file the workflow did not build, and for one it built from any other ref. The identity to expect: certificate issuer
`https://token.actions.githubusercontent.com`, signer workflow
`sayam/thai-docx-skill/.github/workflows/release.yml`, source ref `refs/tags/v<version>`.

That command asks GitHub for the attestation, so it needs `gh auth login`. A release that also
carries `thai-docx-<version>.intoto.jsonl` can be checked against that file instead, with no
account and no network:

```sh
gh attestation verify thai-docx-<version>.zip --bundle thai-docx-<version>.intoto.jsonl \
  --repo sayam/thai-docx-skill \
  --signer-workflow sayam/thai-docx-skill/.github/workflows/release.yml --source-ref refs/tags/v<version>
```

The release workflow verifies both ways itself, against the very file it is about to attach, and
attaches nothing if either check passes for a tampered archive.

You can also rebuild the archive and compare. From a clone at the tag, on a checkout without
line-ending conversion:

```sh
git checkout v<version>
python3 tools/package_skill.py thai-docx-<version>.zip
sha256sum thai-docx-<version>.zip
```

The SHA-256 equals that of the attached archive: entries are stored, in path order, with fixed dates
and modes.

## Secrets and credentials

- The project keeps no long-lived secrets. CI uses only the per-job `GITHUB_TOKEN`, with the
  permissions each workflow declares, and GitHub's OIDC identity for signing.
- Repository and environment secrets are not used; adding one requires changing this policy first,
  in a pull request.
- Accounts with write access use two-factor authentication.
- Secret scanning with push protection is enabled on the repository.
- A leaked credential is revoked and rotated at once, and the incident is recorded in an advisory
  or an issue.

## Scope

- The skill: `skills/thai-docx/` — the Python package, the JavaScript file, and the
  instructions in `SKILL.md` an agent follows.
- This repository's workflows and release process.

What the scripts are designed never to do is written down in `docs/adr/0040`: no network;
no subprocesses, `eval` or code loaded from outside the skill; no environment variable read
beyond the platform's own lookup of the home directory; writing only the output path, the one profile file `profile save` or `import` names in the
profile directories, and the path `profile export` is given (or `./NAME.json` when it is given none); reading images only from the
Markdown file's directory or one named with `--allow-dir`; profiles only as checked JSON of
at most 64 KiB; DOCTYPE and oversized packages refused. A way to make them do any of it is
in scope, and so is a profile file that makes a build do what its flags could not.

The bundled verifiable-gates tools under `tools/` are reported upstream:
<https://github.com/sayam/verifiable-gates/security>.
