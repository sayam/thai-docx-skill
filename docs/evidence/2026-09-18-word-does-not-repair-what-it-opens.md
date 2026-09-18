# 2026-09-18 — Word does not repair a Thai file it did not type

A working assumption behind this project's scope was that **Word writes Thai correctly**, so a
person editing in Word has no use for this skill. Half of that assumption is now measured, and it is
false: when Word saves a document another program wrote, it does not add the complex-script marks,
and it stamps the runs with the wrong language.

The occasion was OpenAI's ChatGPT add-in, which became available for Word alongside Excel and
PowerPoint in September 2026. It runs as a pane inside Word and edits the open document, so it was
worth asking whether an assistant working inside Word produces correct Thai — and, if a user opens a
broken file there, whether Word heals it.

## Method

The input is `B-known-bad-docxjs.docx`, built with docx-js 9.7.1 on 2026-09-18: a Thai heading, a
Thai paragraph with a bold run, one bullet. Five runs of Thai text, none with `<w:cs/>`.

```
sha256 520b0b605f64ad400744e8e6230ead718989f0209f1630c5eed511e2bad41b9a
check  → ok: false, 5 × code 2
```

Three rounds, all in Word for the web with the file in cloud storage, on Word for Microsoft 365
version 2608 (build 16.0.20326.20072), Current Channel:

| round | what was done |
|---|---|
| **control** | opened, nothing changed, downloaded again |
| **A** | one `.` typed at the end of two paragraphs, waited for *Saved*, downloaded |
| **B** | a fresh copy; the ChatGPT pane asked to indent the first line after the heading by 0.5 inch |

## Results

**Control — Word writes nothing until something changes.** The downloaded file was byte-identical,
sha256 `520b0b60…41b9a`. Opening and closing a document is not a save, so "open it in Word and save
it" is not a repair that happens by itself.

**A — Word rewrote the document and made it worse.**

| | before | after (sha256 `4d403cf5…6fa6d`) |
|---|---|---|
| bytes | 8 797 | 6 795 |
| runs / paragraphs | 5 / 7 | 6 / 3 |
| findings | 5 × code 2 | **5 × code 2 + 1 × code 4** |
| every run's `rPr` | absent, or `<w:b/><w:bCs/>` on the bold run | **`<w:lang w:val="en-US"/>` on every run** |
| `<w:cs/>` | none | **still none** |

The heading's run, after the save:

```xml
<w:r w:rsidRPr="6548ED05" w:rsidR="6548ED05">
  <w:rPr><w:lang w:val="en-US"/></w:rPr>
  <w:t>รายงานการประชุม</w:t>
</w:r>
```

Before the edit the runs said nothing about language. Afterwards they assert the wrong one. The
mechanism is visible on screen: the status bar read "English (U.S.)" throughout, so the proofing
language at the insertion point is what Word stamped on the runs it rewrote. Word does not re-detect
the script of text it did not watch being typed. It also split a word across two runs with identical
formatting — the new code 4.

One thing it did right: `<w:bCs>` stayed beside `<w:b>`. Word's writer knows about complex-script
twins. It simply had no reason to believe this text was complex script.

**B — the add-in behaves the same.** The instruction was formatting only, and the pane obeyed
exactly: it added `<w:ind w:firstLine="720"/>` to that one paragraph and changed not a character of
text. The file (sha256 `8575dbab…9da7e1`, 8 220 bytes, 5 runs) still checks as

```
ok: false, 5 × code 2
```

with `<w:lang w:val="en-US"/>` on every run and `<w:cs/>` on none. The code 4 from round A did not
appear — the split runs were merged back — so the add-in's edit is tidier than the keystroke was,
and no more correct.

## What this establishes

- A Thai `.docx` that arrives from another program is **not** healed by opening it in Word, by
  saving it there, or by editing it through an assistant that works inside Word.
- Word writing a file it did not originate **adds a wrong language mark** rather than the missing
  complex-script one.
- This is the case `repair` is planned for in v0.2, and it is now measured rather than assumed.

## What it does not establish

The other half of the assumption — Thai typed directly into Word with the Thai input language
active — was not tested here and is not contradicted by anything above. Every Word-authored sample
this project holds carries correct marks, which is consistent with Word marking what it watches
being typed. Any claim in the README or the guides about "Word gets Thai right" must be limited to
that case.

Nothing about the tenant, the account or its configuration is part of this record; the add-in's
availability is not the finding, its output is.
