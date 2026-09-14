# 0001 — Record every decision, where it came from, and its sources

- Status: accepted
- Decided: 2026-09-14

## Where it came from

thai-docx-skill was opened on 2026-09-14 as a repository that is not code. Nothing here
can be held to a test suite, so what a reader can be given instead is the
trail: why each thing is the way it is, what prompted it, and what it rests on.

## Decision

Every significant decision is a numbered record in this directory, listed in
`README.md` beside it. Every source a record leans on has a row in
`../../SOURCES.md` and is cited by id.

Left out on purpose: nothing checks that a cited id exists in `SOURCES.md`, or
that a source says what the record claims. That is the reader's judgement.

## Why

An index that is out of date reads as complete while the latest decisions are
missing from it. verifiable-gates checks the index against the records in both
directions — numbering, gaps, and supersessions on both sides [S1] — so that
part does not depend on anyone remembering.

## Expires when

The repository adopts another way of keeping decisions that a tool holds to
the files as closely — then this record is superseded, not deleted.
