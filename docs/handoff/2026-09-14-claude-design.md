# Handoff — diagnosis of Thai .docx rendering, Claude Design session, 2026-09-14

> **Historical record, kept verbatim below the line.** It is the source the decision
> records cite as [S2]. It names files — `thai_docx.py`, `tools/build-docx.js`,
> `SKILL.md`, `PROMPT.md` — from that session; they were one use case, were not
> imported into this repository, and are not how this skill is built. The concepts
> it establishes are carried by `docs/adr/0004` (amended by 0038 and 0039) and `0023` (which
> restates 0005).

---

# สรุปแนวทางแก้ปัญหา: .docx ภาษาไทยที่สร้างโดย AI แสดงผลผิดใน Word

เอกสารนี้สรุปกระบวนการวินิจฉัยและแก้ปัญหาที่ใช้จริงในโปรเจกต์นี้ เพื่อส่งต่อให้ทีมจัดทำ
skill มาตรฐานสำหรับ agent ทุกตัว (Claude, ChatGPT, Gemini, DeepSeek, Grok, Kimi)

## อาการตั้งต้น (จากผู้ใช้)

สร้าง .docx ภาษาไทยด้วย AI แล้วเปิดใน Word เจอ 2 อาการพร้อมกัน:
1. คำไทยถูกขีดเส้นหยักแดง (ตรวจสะกดผิด) แทบทุกคำ
2. ช่องไฟและตำแหน่งตัดบรรทัดผิดเพี้ยนไปจากที่ควรเป็น

จุดสังเกตสำคัญที่ผู้ใช้รายงาน: ถ้า copy ข้อความจาก Word แล้ว paste แบบ "Unformatted
Text" ทับตำแหน่งเดิม อาการทั้งสองหายไปทันที — นี่คือเบาะแสหลักที่ใช้ไล่หาสาเหตุ

## วิธีวินิจฉัย: ใช้ "unformatted paste" เป็นเส้นฐาน (baseline)

Paste แบบ unformatted ทำ 2 อย่างที่ต่างจากการสร้างไฟล์แบบ programmatic:
- รวมทุก run ในย่อหน้าเป็น run เดียว (ล้าง formatting ทั้งหมด)
- ให้ Word เขียน run ใหม่ด้วยค่า default ของ Word เอง (ภาษา, proofing, complex-script flag)

เพราะฉะนั้นอาการที่ "หายไปเมื่อ paste unformatted" ทั้งหมด คือค่าที่ไฟล์ต้นทาง
**ตั้งผิดหรือไม่ได้ตั้ง** ในระดับ run/document setting — ไม่ใช่ปัญหาของเนื้อหาหรือฟอนต์
ไล่แก้จากตรงนั้นแทนจะตรงจุดกว่าการลองผิดลองถูก

## รากของปัญหา: OOXML แยก "ภาษาละติน" กับ "ภาษา complex script" เป็นคนละชุด attribute เสมอ

Word/OOXML ปฏิบัติต่อทุก run เป็น 2 ระบบคู่กันตลอด — ฝั่ง Latin (ascii/hAnsi, `sz`,
`w:lang w:val`) กับฝั่ง Complex Script (`w:cs` ใน rFonts, `szCs`, `w:lang w:bidi`)
ไทยอยู่ฝั่งหลังเสมอ ถ้า generator เขียนแต่ฝั่ง Latin (ซึ่งเป็นค่า default ที่ library
ส่วนใหญ่ตั้งมาให้อัตโนมัติ) ตัวอักษรไทยจะถูก "มองเป็น Latin" ทุกจุด

ต้นเหตุที่พบจริง เรียงจากกระทบมากไปน้อย:

### 1) ไม่ประกาศ `compatibilityMode = 15` ใน `settings.xml`

ผลคือ Word เปิดไฟล์ใน **Compatibility Mode** (ยืนยันได้จากแถบชื่อไฟล์) ซึ่งใช้เอ็นจิ้น
จัดหน้าของ Word รุ่นเก่าที่ไม่รองรับการตัดคำไทยกลางคำ ตัดได้แค่ที่ช่องว่าง — อาการที่เห็น
คือบรรทัดสั้น ขอบขวาเป็นตะเข็บ

### 2) ทุก run ขาด `<w:cs/>` (Complex Script Formatting flag)

ถ้าไม่มี flag นี้ต่อ run Word จะตีความ run นั้นเป็นข้อความ Latin แม้ตัวอักษรเป็นไทย
ผลคือใช้ดิกอังกฤษตรวจสะกด (เส้นหยักแดงทุกคำ) และใช้กฎตัดบรรทัดของ Latin

### 3) ปิด proofing (`<w:noProof/>` หรือ "Do not check spelling/grammar") เพื่อไล่เส้นหยัก
   กลับไปปิดตัวตัดคำไทยด้วย เพราะเป็นกลไกเดียวกัน

แนวทางที่ถูก: ไม่ปิด proofing engine แต่ซ่อน "การแสดงผล" เส้นหยักที่ระดับเอกสารด้วย
`<w:hideSpellingErrors/>` และ `<w:hideGrammaticalErrors/>` แทน

### 4) หนึ่งคำไทยถูกผ่าเป็นหลาย run

เกิดเมื่อ generator สร้าง run ใหม่ทุกครั้งที่ parse เจอ markup (`**bold**`, `` `code` ``
ฯลฯ) แล้วรอยตัด run บังเอิญตกกลางคำไทย Word ตัดคำข้าม run ไม่ได้ จึงเห็นช่องไฟ/
การตัดบรรทัดเพี้ยนเฉพาะจุดที่มี inline formatting คาบอยู่ — อาการนี้หายไปตอน paste
unformatted เพราะการ paste รวม run ให้อัตโนมัติ

แก้ที่ตัว generator: หลังแตก inline formatting เป็น token แล้ว ต้อง **merge token ที่
ติดกันและมี attribute เหมือนกัน** กลับเป็น run เดียวก่อนเขียน XML

### 5) ฟอนต์/ขนาดตั้งเฉพาะฝั่ง Latin (`w:ascii`, `w:sz`) แต่ไม่ตั้งฝั่ง complex script
   (`w:cs` ใน rFonts, `w:szCs`) และบุลเลตใช้ฟอนต์ `Symbol` (กลายเป็น → หรือกล่องในคำไทย)

## กระบวนการยืนยันว่าแก้ครบ (ไม่ต้องเปิด Word ด้วยตาเปล่าทุกรอบ)

เกณฑ์ตรวจที่ใช้ได้จริงและตรวจอัตโนมัติได้บางส่วน:
- แถบชื่อไฟล์ไม่มีคำว่า "Compatibility Mode"
- Regex บน `document.xml`: ทุก `<w:r>` ที่มี `<w:t>` ต้องมี `<w:cs/>` ในคู่ `<w:rPr>` เดียวกัน
- `settings.xml` มี `compatSetting name="compatibilityMode" val="15"` และไม่มี
  `<w:noProof/>` อยู่เลย
- นับจำนวนบล็อก (heading/table row/bullet) ที่แปลงได้ เทียบกับจำนวนในไฟล์ต้นฉบับ
  เพื่อยืนยันไม่มีเนื้อหาหาย (สำคัญเมื่อโจทย์คือ "เนื้อหาคงเดิม 100%")

## ข้อจำกัดที่ตั้งใจไม่แก้ (และทำไม)

ผู้ใช้ถามถึงการแทรก ZWSP (U+200B) เพื่อคุมจุดตัดคำเองแบบเป๊ะ — ปฏิเสธแนวทางนี้ไว้ตั้งแต่แรก
เพราะเป็นการแทรกอักขระที่มองไม่เห็นเข้าไปในเนื้อหาจริง ขัดกับเงื่อนไข "เนื้อหาคงเดิม 100%"
ที่งานวิจัย/เอกสารผ่าน proof แล้วต้องคง แนวทางที่เลือกคือแก้ที่ document-setting/run-attribute
ระดับ metadata เท่านั้น ไม่แตะเนื้อหา — เป็นหลักการที่ skill ควรสืบทอดต่อ: **แก้ปัญหาการแสดงผล
ด้วย attribute ของ format ไม่ใช่ด้วยการแก้เนื้อหา**

## สิ่งที่ควรอยู่ใน skill มาตรฐาน (ข้าม engine)

เพราะสาเหตุทั้งหมดเป็นเรื่อง OOXML schema (มาตรฐานเดียวกันไม่ว่าใครสร้างไฟล์) เนื้อหานี้
ไม่ผูกกับ Claude โดยเฉพาะ — พอร์ตไปเป็น instruction ให้ agent อื่นได้ตรง ๆ ถ้าใช้แนวทาง
สร้างไฟล์แบบ raw OOXML (ไม่พึ่ง docx-js/python-docx ที่อาจไม่เปิด option พวกนี้ให้ตั้ง)
สิ่งที่ skill ต้องบังคับคือ 5 attribute/setting ข้างต้น เป็น checklist ที่ตรวจได้จริงจาก
XML string ไม่ใช่คำแนะนำเชิงหลักการเท่านั้น

## สองทางเลือกในการ implement (สำหรับ skill มาตรฐาน)

- **raw OOXML + zip** — ไม่พึ่ง library ควบคุมทุก byte เหมาะกับ environment ที่ไม่มี
  Python (เช่น JS sandbox) implementation อ้างอิง: `tools/build-docx.js`
- **python-docx + helper module บังคับ** — เมื่อ environment มี Python ต้องบังคับ
  agent เรียกผ่าน `thai_docx.py` (`setup_thai_document`, `add_thai_run`,
  `add_thai_bullet_list`) เท่านั้น ห้ามเขียน `doc.add_run(text)` ตรง ๆ กับข้อความไทย
  เหตุผลที่ต้องบังคับ (ไม่ใช่แค่แนะนำ): เป้าหมายคือ **ผลลัพธ์เหมือนกันไม่ว่า model
  ขนาดไหนเป็นคนเขียนโค้ด** (Haiku เท่ากับ Sonnet เท่ากับ GPT/Gemini/DeepSeek/Grok/
  Kimi) — ปล่อยให้ model ต่างขนาดเขียน `w:rPr` เองแต่ละครั้ง มีโอกาสพลาดจุดใดจุดหนึ่ง
  ใน 5 ข้อไม่เท่ากัน โดยเฉพาะ toggle element `<w:cs/>` ที่แยกจาก attribute `w:cs`
  ในกันคนละความหมาย ซึ่งเป็นจุดพลาดบ่อยที่สุดแม้ในโค้ดที่ดูสมบูรณ์ การบังคับผ่าน
  ฟังก์ชันเดียวตัดความแปรผันนี้ทิ้งไปเลย
- module เต็ม: `skills/thai-docx/thai_docx.py`

ทั้งสองทางยึดหลักการเดียวกันคือ 5 root cause ในหัวข้อ "รากของปัญหา" ข้างบน —
ต่างกันแค่ syntax ที่ใช้ตั้งค่า ไม่ต่างกันที่ค่าที่ต้องตั้ง

## ไฟล์ในชุด skill นี้ (สำหรับ publish)

- `SKILL.md` — เนื้อหาเต็ม: อาการ, สาเหตุ 5 ข้อ, ทั้งสอง implementation path,
  เช็กลิสต์ผ่าน/วินิจฉัย — ใช้เป็นต้นฉบับหลักตอนเขียน skill มาตรฐาน
- `PROMPT.md` — คำสั่งพร้อมใช้ ให้ agent อื่นวางเป็น system/user prompt ได้ตรง ๆ
- `thai_docx.py` — helper module python-docx ที่บังคับใช้ตามเหตุผลข้างบน
- `../../tools/build-docx.js` — implementation อ้างอิงฝั่ง raw OOXML (JS)
- `HANDOFF.md` (ไฟล์นี้) — บันทึกกระบวนการวินิจฉัยและเหตุผลเชิงตัดสินใจ
  สำหรับคนที่จะดูแล skill นี้ต่อ ไม่จำเป็นต้อง publish คู่กับ skill
