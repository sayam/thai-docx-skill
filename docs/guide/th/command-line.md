# ใช้โดยไม่มี AI

โปรแกรมของสกิลรันเองได้ในหน้าจอคำสั่ง (terminal) เราเขียน Markdown เอง แล้วใช้คำสั่งเดียวสร้างไฟล์ Word
ทุกคำสั่งในหน้านี้ลองรันตามที่เขียนไว้แล้ว

[หน้าแรกของคู่มือ](../th.md) · [English](../en/command-line.md)

## ก่อนเริ่ม

1. ตรวจว่าเครื่องมี Python 3.11 ขึ้นไป หรือ Node.js 22 ขึ้นไป

   ```sh
   python3 --version
   node --version
   ```

   บน Windows ใช้ `py --version` สำหรับ Python ถ้าไม่มีทั้งสองอย่าง ติดตั้งได้จาก
   [python.org](https://www.python.org/downloads/) หรือ [nodejs.org](https://nodejs.org/)
2. ดาวน์โหลด `thai-docx-<เลขรุ่น>.zip` จาก
   [Releases](https://github.com/sayam/thai-docx-skill/releases) แล้วแตกไฟล์ในโฟลเดอร์ที่ทำงาน
   จะได้โฟลเดอร์ `thai-docx`

   ```sh
   unzip thai-docx-0.1.1.zip
   ```

ไม่ต้องติดตั้งอะไรเพิ่ม และไม่ใช้อินเทอร์เน็ต

คำสั่งด้านล่างใช้ Python ถ้าใช้ Node.js ให้เปลี่ยน `python3 thai-docx/scripts/thai_docx` เป็น
`node thai-docx/scripts/thai_docx.js` ได้ไฟล์เหมือนกันทุกไบต์ บน Windows ให้เปลี่ยน `python3` เป็น `py`

## สร้างไฟล์แรก

1. เขียนไฟล์ `report.md` แบบ UTF-8 เช่น

   ```markdown
   # รายงานการประชุม

   ประชุมทีมประจำเดือน **กันยายน**

   - สรุปงานที่เสร็จแล้ว
   - งานที่ต้องทำต่อ

   | งาน | ผู้รับผิดชอบ |
   |---|---|
   | ทำเอกสาร | สมชาย |
   ```

2. สร้างไฟล์

   ```sh
   python3 thai-docx/scripts/thai_docx build report.md report.docx
   ```

3. อ่านข้อความหนึ่งบรรทัดที่พิมพ์ออกมา และรหัสจบการทำงาน (exit code)

   | exit code | ข้อความมี | ความหมาย |
   |---|---|---|
   | 0 | `"ok": true` | ได้ `report.docx` แล้ว `"settings"` บอกการตั้งค่าที่ใช้ |
   | 2 | `"error"` มักมี `"line"` | Markdown บรรทัดนั้นมีสิ่งที่สกิลไม่รับ ยังไม่สร้างไฟล์ |
   | 1 | `"findings"` | ข้อบกพร่องของสกิลเอง ยังไม่สร้างไฟล์ ช่วย[แจ้งที่หน้า Issues](https://github.com/sayam/thai-docx-skill/issues) |

   `"warnings"` (คำเตือน) ไม่หยุดการสร้างไฟล์ แต่ควรอ่าน เช่น ฟอนต์ไม่มีตัวอักษรไทย
   หรือการตั้งค่าที่ไม่มีผล

   **ระวัง:** `build` เขียนทับ `report.docx` ที่มีอยู่แล้วโดยไม่ถาม ถ้าอยากเก็บไฟล์เดิม ให้ใช้ชื่อใหม่

## เปลี่ยนการตั้งค่า

ใส่ตัวเลือก (flag) ต่อท้ายชื่อไฟล์

```sh
python3 thai-docx/scripts/thai_docx build report.md report.docx --font "Sarabun" --size 14 --page-numbers bottom-center --toc
```

ตัวเลือกที่ใช้บ่อย

| ตัวเลือก | ทำอะไร |
|---|---|
| `--font "Sarabun"`, `--size 14` | ฟอนต์และขนาดตัวอักษร |
| `--paper letter`, `--paper f14`, `--landscape` | กระดาษ |
| `--margins 1,1,1,1` | ขอบกระดาษเป็นนิ้ว: บน ขวา ล่าง ซ้าย |
| `--indent 0.5`, `--line-spacing 1.5` | ย่อหน้าบรรทัดแรก ระยะบรรทัด |
| `--align thai` | จัดกระจายแบบไทย |
| `--toc`, `--heading-numbers` | สารบัญ เลขหัวข้อ |
| `--page-numbers`, `--page-numbers bottom-center`, `--no-page-number-first` | เลขหน้า |
| `--header "ลับ"`, `--footer "ร่าง"` | ข้อความหัวกระดาษและท้ายกระดาษ |
| `--thai-digits` | เลขไทย ๑ ๒ ๓ ในเลขที่สกิลใส่ให้ ตัวเลขที่เราพิมพ์ไม่เปลี่ยน |
| `--hide-spelling-errors` | ซ่อนเส้นหยัก |
| `--table-widths auto`, `--table-size 14`, `--no-repeat-table-header` | ตาราง |
| `--allow-dir ../images` | อ่านรูปจากโฟลเดอร์อื่น |

ตัวเลือกทั้งหมดและค่าเริ่มต้น: [references/settings.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/settings.md)
รายงานหรือวิทยานิพนธ์ (ป้าย `<!-- chapters -->` และป้ายอื่น ชื่อตาราง `Table:` ชื่อรูป `Figure:`
`--chapter-label` และอื่น ๆ):
[references/chapters.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/chapters.md)
สีและขนาดหัวข้อที่ส่วนบนของไฟล์:
[references/heading-styles.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/heading-styles.md)

## เก็บการตั้งค่าเป็นโปรไฟล์

```sh
python3 thai-docx/scripts/thai_docx profile save thesis --size 15 --align thai
python3 thai-docx/scripts/thai_docx build report.md report.docx --profile thesis
python3 thai-docx/scripts/thai_docx build report.md report.docx --profile thesis --size 18
```

ตัวเลือกที่ใส่หลัง `--profile` ชนะโปรไฟล์ คำสั่งอื่นของโปรไฟล์

| คำสั่ง | ทำอะไร |
|---|---|
| `profile list` | แสดงโปรไฟล์ทั้งหมด และอยู่ที่ไหน |
| `profile show thesis` | แสดงการตั้งค่าในโปรไฟล์ และการตั้งค่าทั้งหมดที่จะใช้ตอนสร้างไฟล์ |
| `profile save thesis --size 15 --project` | บันทึกใน `.thai-docx/profiles/` ของโฟลเดอร์นี้ ไม่ใช่โฟลเดอร์บ้าน |
| `profile save thesis-v2 --from thesis --default align --size 14` | สร้างโปรไฟล์ใหม่จากของเดิม: `align` กลับเป็นค่าเริ่มต้น ขนาด 14 |
| `profile export thesis thesis.json` | เขียนไฟล์ไว้ส่งให้คนอื่น |
| `profile import thesis.json --name school-thesis` | รับโปรไฟล์ที่คนอื่นส่งมา ตั้งชื่อเอง (เพิ่ม `--project` ถ้าใช้เฉพาะโฟลเดอร์นี้) |
| `build report.md report.docx --profile thesis.json` | ใช้ไฟล์โปรไฟล์จากที่อยู่ของไฟล์ได้เลย |
| `build report.md report.docx --profile thesis --default toc` | ใช้โปรไฟล์ แต่ตัดการตั้งค่าหนึ่งออก |

```sh
python3 thai-docx/scripts/thai_docx profile list
python3 thai-docx/scripts/thai_docx profile show thesis
python3 thai-docx/scripts/thai_docx profile save thesis-v2 --from thesis --default align --size 14
python3 thai-docx/scripts/thai_docx profile export thesis thesis.json
python3 thai-docx/scripts/thai_docx profile import thesis.json --name school-thesis
```

**ระวัง:** `profile save` และ `profile import` เขียนทับโปรไฟล์ชื่อเดียวกันโดยไม่ถาม
ถ้าเขียนทับ บรรทัดที่พิมพ์ออกมาจะมี `"replaced": true` และคำเตือน

โปรไฟล์อยู่ที่ `~/.thai-docx/profiles/` หรือ `.thai-docx/profiles/` ในโปรเจกต์ โปรไฟล์ของโปรเจกต์ชนะโปรไฟล์ชื่อเดียวกัน
เป็นไฟล์ JSON เล็ก ๆ ที่มีแค่การตั้งค่า
รายละเอียด: [references/profiles.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/profiles.md)

## ตรวจไฟล์ Word

```sh
python3 thai-docx/scripts/thai_docx check report.docx
```

exit code 0: ไม่มีปัญหา 1: มีปัญหา อยู่ใน `"findings"` เป็นรหัส 2: ไม่ใช่ไฟล์ Word ที่อ่านได้ หรือไม่ปลอดภัย
ความหมายของแต่ละรหัส:
[references/check.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/check.md)
คำสั่งนี้รายงานอย่างเดียว ถ้าอยากซ่อมไฟล์ที่ไม่มีเนื้อหาต้นฉบับแล้ว

```text
python3 thai-docx/scripts/thai_docx repair theirs.docx theirs-fixed.docx
```

จะได้ไฟล์ใหม่ ไฟล์เดิมไม่ถูกแตะ แก้ได้ห้าในเจ็ดข้อ คือโหมดความเข้ากันได้ เครื่องหมายที่ทุกช่วงข้อความไทยต้องมี
การปิดการตรวจคำสะกด คุณสมบัติคู่ของ complex script และลำดับคุณสมบัติที่ผิด ส่วนคำที่ถูกแยกเป็นสองช่วง
กับอักขระที่มองไม่เห็น จะแจ้งไว้ใน `"remaining"` แทน เพราะการแก้สองข้อนั้นต้องแตะข้อความ
รายงานจะบอกด้วยว่าเขียนฟอนต์อะไรลงไปในที่ที่ไม่ได้ระบุไว้ ถ้าอยากเลือกเอง ใช้ `--font "Sarabun"`

ไฟล์ใหม่จะมีขนาดใกล้เคียงไฟล์เดิม ถ้ามีไฟล์ Markdown ต้นฉบับ การสร้างใหม่แก้ได้ครบกว่า
รวมถึงสามข้อที่ repair ไม่แตะ

## ดูคำถาม grill เอง

คำถาม grill มีไว้ให้ผู้ช่วย AI ใช้ แต่เราดูเองได้

```sh
python3 thai-docx/scripts/thai_docx grill --said "thai-docx grill ช่วยทำรายงาน"
```

จะได้คำถาม ตัวเลือก และ flag ของแต่ละตัวเลือก ในหน้าจอคำสั่ง ใส่ flag เหล่านั้นให้ `build` ได้เลย

## ในหน้าเว็บหรือ sandbox

`thai-docx/scripts/thai_docx.js` รันได้แม้ไม่มี Node.js ใน sandbox JavaScript ที่มี `TextEncoder` และ `TextDecoder`
`ThaiDocx.buildDocument(markdown, flags, images)` คืน `{ result, bytes }` โดย `bytes` คือไฟล์ Word
หรือเป็น `null` ถ้าสร้างไม่ได้
ดู [references/sandbox.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/sandbox.md)
