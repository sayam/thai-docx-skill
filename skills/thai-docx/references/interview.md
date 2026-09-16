# Grill mode: the questions

Nine fixed questions, each with fixed choices. Do not add, drop, merge or reword a
question or a choice, and do not suggest other values. Ask in the language the grill
command named — `"language": "th"` is the Thai wording, `"en"` the English. Choice **a**
is always the default.

## How to ask

- **Your client has a tool for multiple-choice questions** (in Claude Code,
  `AskUserQuestion`): ask questions 1–4 in one call, then 5–9 in a second call. Each
  question's text is its line below without the choices; each choice is one option, choice
  a first. A choice "อื่น ๆ" / "Other" asks the user to type a value; if the tool adds its
  own free-text option, leave that choice out.
- **Otherwise:** send the message below, all nine questions at once, and let the user
  answer in short form, e.g. `1a 3b 5c` — anything not mentioned keeps a.

Ask once. If an answer is unclear, keep the default and say so when reporting the settings.

## The message

**Thai**

> ก่อนสร้างไฟล์ ขอถามการตั้งค่า 9 ข้อ ตอบสั้น ๆ เช่น `1a 5b` ข้อที่ไม่ตอบใช้ตัวเลือก a
>
> 1. ฟอนต์ — a) TH Sarabun New · b) TH SarabunPSK · c) Sarabun · d) อื่น ๆ: พิมพ์ชื่อฟอนต์
> 2. ขนาดตัวอักษร — a) 16 pt · b) 14 pt · c) 15 pt · d) อื่น ๆ: พิมพ์ขนาด
> 3. กระดาษและขอบ — a) A4 ขอบซ้าย 1.5 นิ้ว ด้านอื่น 1 นิ้ว · b) A4 ขอบ 1 นิ้วทุกด้าน · c) Letter ขอบซ้าย 1.5 นิ้ว ด้านอื่น 1 นิ้ว · d) อื่น ๆ: กระดาษ และขอบ บน ขวา ล่าง ซ้าย เป็นนิ้ว
> 4. การจัดย่อหน้า — a) ชิดซ้าย · b) กระจายแบบไทย
> 5. ย่อหน้าบรรทัดแรกของเนื้อความ — a) ไม่ย่อ · b) 0.5 นิ้ว · c) 1 นิ้ว · d) อื่น ๆ: พิมพ์เป็นนิ้ว
> 6. สารบัญ — a) ไม่ใส่ · b) ใส่
> 7. เลขหน้า — a) ไม่ใส่ · b) ใส่
> 8. เส้นหยักตรวจคำสะกด — a) แสดง · b) ซ่อน (ซ่อนคำที่สะกดผิดจริงด้วย)
> 9. บันทึกการตั้งค่านี้ไว้ใช้ครั้งต่อไป — a) ไม่บันทึก · b) บันทึกเป็นของฉัน: พิมพ์ชื่อ · c) บันทึกไว้ในโปรเจกต์นี้: พิมพ์ชื่อ

**English**

> Before I build the file, nine settings. Answer briefly, e.g. `1a 5b`; anything you skip keeps a.
>
> 1. Font — a) TH Sarabun New · b) TH SarabunPSK · c) Sarabun · d) Other: the font name
> 2. Font size — a) 16 pt · b) 14 pt · c) 15 pt · d) Other: the size
> 3. Paper and margins — a) A4, left 1.5 in, others 1 in · b) A4, 1 in all round · c) Letter, left 1.5 in, others 1 in · d) Other: paper, and margins top, right, bottom, left in inches
> 4. Paragraph alignment — a) Left · b) Thai distributed
> 5. First-line indent of body paragraphs — a) None · b) 0.5 in · c) 1 in · d) Other: inches
> 6. Table of contents — a) No · b) Yes
> 7. Page numbers — a) No · b) Yes
> 8. Spelling squiggles — a) Show · b) Hide (hides real typos too)
> 9. Keep these settings for next time — a) No · b) Yes, as mine: the name · c) Yes, in this project: the name

## From answers to flags

| question | answer | flag |
|---|---|---|
| 1 | b / c / d | `--font "TH SarabunPSK"` / `--font "Sarabun"` / `--font "NAME"` |
| 2 | b / c / d | `--size 14` / `--size 15` / `--size N` |
| 3 | b | `--margins 1,1,1,1` |
| 3 | c | `--paper letter` |
| 3 | d | `--paper a4`, `--paper letter` or `--paper f14`, and `--margins T,R,B,L` |
| 4 | b | `--align thai` |
| 5 | b / c / d | `--indent 0.5` / `--indent 1` / `--indent N` |
| 6 | b | `--toc` |
| 7 | b | `--page-numbers` |
| 8 | b | `--hide-spelling-errors` |
| 9 | b / c | `profile save NAME` with the flags above / the same with `--project` |

Choice a adds no flag. On 9b or 9c, run `thai_docx profile save` with the flags the other
answers map to before the build, and tell the user the name and `--profile NAME`; where no
home directory lasts, give them the saved file. If the build rejects a value (exit 2 naming the flag), tell the user
the accepted range from its message and build with that setting's default.
