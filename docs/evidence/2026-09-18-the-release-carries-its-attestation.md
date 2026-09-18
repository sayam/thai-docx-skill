# 2026-09-18 — the release carries its own attestation

`gh attestation verify thai-docx-0.1.1.zip --repo sayam/thai-docx-skill` already passed, because
GitHub keeps the attestation in its own store. Two things were wrong with leaving it there:

1. A reader who does not use `gh`, or is not signed in to GitHub, has no file to check. The proof
   existed but did not travel with the archive.
2. OpenSSF Scorecard reads a release's **assets** and nothing else, which is why Signed-Releases
   scored 0 while the archive was, in fact, attested.

## What the probe actually accepts

Read from the source of Scorecard v5.5.0, not from its documentation:

| probe | accepts | worth |
|---|---|---|
| `releasesHaveProvenance` | an asset whose name ends `.intoto.jsonl` — that suffix and no other | 10 per release |
| `releasesAreSigned` | `.asc`, `.minisig`, `.sig`, `.sign`, `.sigstore`, `.sigstore.json` | 8 per release |
| `signed_releases` evaluation | takes the last five releases, sums the points, divides by the number examined, floors | — |

So the file's **name** decides the score, and every recent release counts.

## The change

`actions/attest-build-provenance` already wrote the bundle; the workflow threw the path away. It now
takes `steps.attest.outputs.bundle-path`, copies it beside the archive as
`thai-docx-<version>.intoto.jsonl`, checks it parses as one JSON object per line, and attaches it
with the zip.

The verification step gained the offline half, which is the half a reader can repeat:

```sh
gh attestation verify "$ZIP" --bundle "$BUNDLE" \
  --repo "$GITHUB_REPOSITORY" \
  --signer-workflow "$GITHUB_REPOSITORY/.github/workflows/release.yml"
```

and a second tamper check against the attached bundle, so a bundle that would verify a corrupted
archive stops the release. The workflow now proves both directions twice: online, that GitHub holds
the attestation; offline, that the **file about to be attached** works and rejects a changed
archive.

`gates.yaml` says so in `release-carries-only-the-skill`, whose title now names the attestation and
both verifications. `.github/SECURITY.md` and both install guides give the offline command.

## What it is worth

Signed-Releases 0 → 10 is **+0.75** on the Scorecard total (weight 8 of 105). Because the check
averages over the last five releases, a release built before this change scores 0 in that window:
with v0.1.0 and v0.1.1 as they are, the next release gives `floor((10 + 0 + 0) / 3) = 3`. The
release workflow takes a tag as a `workflow_dispatch` input and rebuilds from it, so re-running it
for the two existing tags attaches the asset to them as well, without rewriting a tag, a commit or
the archive's bytes — the archive is built from the tag and is byte-identical, as the release
evidence records.

The score is not the reason to do it. The reason is that a person who downloads the zip can now
check it without a GitHub account, and the file that proves the archive travels with the archive.

## The two existing tags, re-run the same day

The workflow was dispatched for both tags after the change landed.

**v0.1.1 — attached.** [Run 35343227900](https://github.com/sayam/thai-docx-skill/actions/runs/35343227900)
rebuilt the archive from the tag, attested it, verified it both ways and uploaded both files. The
release now carries `thai-docx-0.1.1.zip` and `thai-docx-0.1.1.intoto.jsonl`. Downloaded and checked
from a clean directory, with the workflow named:

```
$ gh attestation verify thai-docx-0.1.1.zip --bundle thai-docx-0.1.1.intoto.jsonl \
    --repo sayam/thai-docx-skill \
    --signer-workflow sayam/thai-docx-skill/.github/workflows/release.yml
$ echo $?
0
$ sha256sum thai-docx-0.1.1.zip
65d5c618bee6412c5b3fdddfa7605070e52231e2224d9b2311034368206e229e
```

and a byte appended to the archive makes the same command fail:
`Error: verifying with issuer "sigstore.dev"`.

**v0.1.0 — refused, by a check working as intended.**
[Run 35343232883](https://github.com/sayam/thai-docx-skill/actions/runs/35343232883) stopped in
`release-check`, at the OSV-Scanner step:

```
Total 1 package affected by 1 known vulnerability (0 Critical, 0 High, 1 Medium, 0 Low)
| https://osv.dev/PYSEC-2026-1845 | 6.8 | PyPI | pytest | 8.4.2 | 9.0.3 | requirements/dev.txt |
```

The v0.1.0 tag pins `pytest==8.4.2`; `main` and v0.1.1 pin `9.1.1`, so only the old tag is affected,
and only its development dependency — nothing the skill ships and nothing a user runs. The workflow
says "no release while a development dependency has a known vulnerability" (CONTRIBUTING,
*Dependencies*), and it held, on a tag cut before the advisory existed.

That is the right outcome and it is left as it is. Attaching the asset to v0.1.0 would mean either
skipping the dependency check for one run, or moving the tag to a commit with a newer pin — the
first weakens the check that just did its job, the second rewrites a published release. Neither is
worth an asset on a superseded version.

## What it means for the score

Scorecard averages over the last five releases, so with v0.1.1 carrying provenance and v0.1.0 not,
`signed_releases` lands at `floor((10 + 0) / 2) = 5`, not 10. The next release takes it to
`floor((10 + 10 + 0) / 3) = 6`, and v0.1.0 falls out of the window once five newer releases exist.

## Not done

- No asset on v0.1.0, for the reason above.
- No `.sigstore.json` and no detached signature: `releasesAreSigned` would add 8 more, but it would
  mean a second signing path to keep correct, and the provenance bundle already carries the
  signature that matters.
