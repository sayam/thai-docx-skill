# No shell: a JavaScript sandbox

Read this when there is no shell to run the command in (SKILL.md, Build a document).

Evaluate `<skill>/scripts/thai_docx.js` as a plain script — it needs no modules, only
`TextEncoder` and `TextDecoder` — and it defines `ThaiDocx`.

```js
const { result, bytes } = ThaiDocx.buildDocument(markdown, ["--toc"], { "chart.png": pngBytes });
// result is the JSON the command prints; bytes is a Uint8Array .docx, or null when refused
const report = ThaiDocx.checkDocument(docxBytes);
```

Image keys are the paths exactly as the Markdown writes them. Offer `bytes` to the
user as `report.docx`.
