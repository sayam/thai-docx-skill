# 0003 — License everything under MIT, and ship the notice inside the skill

- Status: accepted
- Decided: 2026-09-15

## Where it came from

The repository is public (0002), and the skill is meant to be bundled by any
agent product or user. It needed a licence before its first commit.

## Decision

- The whole repository is MIT-licensed: `LICENSE` at the root.
- The skill directory carries an identical copy, `skills/thai-docx/LICENSE.txt`,
  and its front matter says `license: MIT` [S3].

Left out on purpose: Apache-2.0. Its patent grant was weighed and is not needed
for a skill that implements a published file format.

## Why

MIT is the shortest permissive licence, and its one condition is that the
notice travels with every copy [S22]. The skill directory is what gets copied
into clients on its own (0002), so the notice has to live inside it as well as
at the root.

## Expires when

The skill bundles third-party code under a licence MIT cannot carry, or a
contributor needs an explicit patent grant.
