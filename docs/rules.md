# กฎเหล็ก — thai-docx-skill

ใช้เป็นตัวกรองตัดสินใจ ไม่ใช่วิสัยทัศน์
ชนกฎ = ไม่ทำ แล้วเขียนเหตุผลที่ไม่ได้ทำ

ฉบับภาษาไทยข้างล่างนี้คือฉบับจริง คำแปลภาษาอังกฤษท้ายหน้ามีไว้อ้างอิง
เมื่อสองฉบับต่างกัน ให้ถือตามภาษาไทย

## 0. ขอบเขตปัญหาที่รับผิดชอบ

เราแก้ไฟล์ `.docx` ที่มีข้อความไทย ซึ่งโปรแกรมหรือเอเจนต์สร้างแล้วทำไทยเป็นสคริปต์ละติน
จนเกิดอาการที่ประกาศไว้: เส้นแดงใต้คำ ตัดบรรทัดเฉพาะที่วรรค ตัวหนาไม่หนา
จุดหัวข้อไม่ขึ้น และ Word เปิดแล้วบันทึกแล้วยังไม่แก้

นอกนี้ไม่ใช่งานของ skill นี้ เว้นแต่เป็นรูที่ผลงานเราเปิดเอง

## 1. ไฟล์ที่ออกจาก skill ต้องใช้ต่อได้ทันที

**ผ่าน** เมื่อครบทุกข้อนี้พร้อมกัน

- Word 365 for Windows (แอปอ้างอิง) ผ่านทั้งสัญญาด้านล่าง ไม่มีข้อยกเว้น
- อีก 4 แอปในชุดออราเคิลถูกตรวจด้วยชุด fixture ชุดเดียวกัน
- ถ้าแอปอื่นเพี้ยน ต้องเป็นข้อจำกัดที่รู้จักแล้วในบันทึก ไม่ใช่ของใหม่ในรีลีสนี้
- ผู้ใช้เปิดแล้วอ่าน พิมพ์ต่อ จัดหน้า และบันทึกได้ โดยไม่ต้องซ่อมไฟล์ก่อนใช้
- ไม่มีกล่อง Repair

**ไม่ผ่าน** เมื่อผู้ใช้ต้องเปิดแล้วแก้ก่อนใช้ หรือต้องรู้วิธีพิเศษของ skill นี้ถึงจะใช้ไฟล์ได้
นอก 5 แอปด้านล่างอยู่นอกสัญญา ห้ามเขียนว่าใช้ได้ถ้ายังไม่ได้วัด

## 2. เข้ามาซ่อม ไม่ได้เข้ามาตั้งระบบใหม่

### 2.1 ไม่สร้างปัญหาใหม่

ฟีเจอร์ ธง ค่าเริ่มต้น หรือวิธีแพ็กไฟล์ ต้องไม่ทำให้เกิดอาการใหม่ในแอปที่ทดสอบ
และต้องไม่ทำให้คนเอาไฟล์ไปเปิดในท่ออื่นพัง

### 2.2 ไม่สร้างมาตรฐานเอกสารใหม่ และไม่บังคับวิธีทำงานใหม่ในแอปเหล่านั้น

ผู้ใช้ยังเขียนไทยแบบเดิม เปิดไฟล์แบบเดิม ใช้สไตล์ของแอปแบบเดิม
ที่เพิ่มได้มีแค่ทางเข้าสร้างไฟล์ให้ถูกตั้งแต่ต้น หรือทางเข้าขอสำเนาที่ทำเครื่องหมายไทยให้ถูก
ห้ามกำหนดว่าเอกสารราชการ วิทยานิพนธ์ หรือองค์กรต้องหน้าตาแบบนี้
ห้ามเลียนแบบเทมเพลตสถาบันจริง

### 2.3 ไม่แทนที่แอปเหล่านั้น

skill ไม่ใช่ Word ไม่ใช่ตัวเรียงพิมพ์ทั่วไป ไม่ใช่ระบบแม่แบบองค์กร
สิ่งที่แอปทำได้อยู่แล้ว ให้แอปทำ

## 3. จบปัญหาที่รับผิดชอบ และปิดรูที่ตัวเองเปิด

สร้างให้ถูกตั้งแต่ต้น ตรวจก่อนเขียนไฟล์
ข้อความในไฟล์ต้องตรงกับต้นทางทีละตัวอักษร
ซ่อมด้วย attribute ไม่แก้คำ ไม่ลบอักขระล่องหน ไม่จัดคำใหม่เพื่อให้ผ่าน
วิธีปิดรูต้องไม่ชนข้อ 2
ถ้าปิดรูแล้วต้องเปลี่ยนข้อความผู้ใช้ หรือต้องให้ผู้ใช้ทำงานในแอปคนละแบบ — ไม่ทำ แล้วบอกเหตุผล

`repair` ไม่ทับต้นฉบับ เขียนเป็นไฟล์ใหม่เมื่อผู้ใช้ขอเท่านั้น

- IN ไม่ถูกเขียน
- ข้อความ OUT เท่าข้อความ IN ทีละตัวอักษร ไม่เช่นนั้นไม่เขียนไฟล์
- ส่วนที่ไม่เกี่ยวกับอาการไทยผ่านไปตามเดิม
- OUT ต้องผ่าน: เปิดได้ ไม่มีกล่อง Repair · ห้าสาเหตุที่ประกาศในข้อ 0 ถูกล้างในแอปอ้างอิง ·
  ข้อความเท่า IN ทีละตัวอักษร
  ส่วนที่ไม่เกี่ยวกับอาการไทยผ่านไปตามเดิม รวมถึงข้อบกพร่องของต้นฉบับที่เราไม่ได้ทำให้เกิด
  และแก้ไม่ได้โดยไม่แตะเนื้อหา
- รายงานว่าแก้ finding ไหน และไม่แก้ finding ไหน

## 4. สงสัยแล้วไม่เขียนไฟล์

แพ็กเกจตรวจไม่ผ่าน ข้อความไม่ตรงต้นทาง Markdown นอกภาษาที่รับ
ธงหรือโปรไฟล์ไม่ผ่านสคีมา ซ่อมไม่ได้โดยไม่แตะข้อความ
หยุด ชี้บรรทัดหรือสาเหตุ ไม่ส่งไฟล์ครึ่ง ๆ กลาง ๆ

## 5. ซับซ้อนจนตัดสินใจไม่ได้ ให้ย้อน 0 → 1 → 2 → 3 → 4

ถ้ายังชนกันอยู่ ให้เลือกฝั่งที่ใช้ต่อได้ในแอปอ้างอิง และไม่แตะข้อความผู้ใช้
แล้วบันทึกว่าไม่ทำอะไร เพราะอะไร

## 6. ไม่มีสูตรเดียวที่ใช้ได้ทุกงาน

ข้อจำกัด เหตุที่ทำ เหตุที่ไม่ทำ แอปที่ทดสอบ แอปที่ไม่รับรอง
และความต่างที่พบ ต้องเขียนไว้ตรง ๆ ในที่ที่ผู้ใช้เจอ
ห้ามปิดด้วยคำว่า "รองรับทั่วไป" ถ้ายังไม่ได้วัด

---

# สัญญาความเข้ากันได้

ชุดออราเคิล ตรวจก่อนทุกแท็กที่เปลี่ยนไบต์เอกสาร

| บทบาท | แอป | สิทธิ์ยกเว้น |
|---|---|---|
| อ้างอิง | Word 365 for Windows | ไม่มี |
| ออราเคิล | Word for Mac | มีได้ ถ้าบันทึกแล้ว |
| ออราเคิล | LibreOffice Writer | มีได้ ถ้าบันทึกแล้ว |
| ออราเคิล | Google Docs | มีได้ ถ้าบันทึกแล้ว |
| ออราเคิล | WPS Writer | มีได้ ถ้าบันทึกแล้ว |

CI เป็นพร็อกซี (XML / fidelity / schema) ไม่ใช่หลักฐานว่าไฟล์ดูถูก
แอปอ้างอิงผ่านทุกข้อจึงจะปล่อยรีลีสได้
แอปอื่นเพี้ยนได้เฉพาะข้อจำกัดที่รู้จักแล้วของแอปและเวอร์ชันนั้น

## สัญญาที่แอปอ้างอิงต้องผ่านทุกข้อ

- เปิดได้ ไม่มีกล่อง Repair
- ไม่ขึ้น Compatibility Mode ที่แถบชื่อ
- แถบสถานะเป็นไทย
- ไม่มีเส้นแดงใต้คำที่สะกดถูก
- ตัวหนา / ตัวเอียง บนไทยเห็นจริง
- จุดหัวข้อเห็น
- บรรทัดไทยหักในคำได้ ไม่หักเฉพาะที่วรรค
- ฟอนต์ที่ไฟล์ระบุถูกใช้
- ตาราง ลิงก์ หัวข้อ เชิงอรรถ รูป ครบและอยู่ในหน้า
- กล่องงาน □ ■ เห็นเป็นสัญลักษณ์

อีก 4 แอปใช้รายการเดียวกันเป็นเกณฑ์ตั้งต้น
ข้อที่แอปนั้นไม่มีกลไกนั้นอยู่เลย — เช่น Compatibility Mode, แถบสถานะภาษา, การตรวจคำสะกด
ใน Google Docs — ทำเครื่องหมาย — ไม่นับว่าตก
ข้อที่ตกได้มีเฉพาะรายการที่บันทึกเป็นข้อจำกัดของแอปนั้น

## ความเพี้ยนที่ยอมรับได้ ต้องครบทุกข้อ

- แอปอ้างอิงไม่เพี้ยนข้อนั้น
- สาเหตุอยู่ที่แอปนั้น แก้ด้วย attribute ที่เราเขียนได้ไม่สำเร็จ
- เอกสารยังใช้ต่อได้: อ่าน พิมพ์ต่อ บันทึกได้
- ข้อความไม่เพี้ยน และผู้ใช้ไม่ต้องทำงานคนละแบบในแอปนั้น
- มีบันทึกใน `docs/evidence/` ของรีลีส: แอป เวอร์ชัน fixture อาการ
  แอปอ้างอิงผ่านหรือไม่ แก้ด้วย attribute ได้หรือไม่ เหตุที่ไม่แก้
  ผลกระทบต่อการใช้ต่อ วันตรวจ รีลีส
- ของใหม่ในรีลีสนี้ยังไม่นับว่า "ยอมรับแล้ว" จนกว่าจะเขียนลงบันทึกก่อนแท็ก

## ความเพี้ยนที่ยอมรับไม่ได้ แม้จะอยากบันทึก

- แอปอ้างอิงไม่ผ่าน
- มีกล่อง Repair ในแอปใดในชุด
- ข้อความไม่ครบ หรือตัวอักษรไม่เท่าต้นทาง
- กลับไปเป็นสาเหตุที่ประกาศในขอบเขตปัญหา
- ข้อที่แอปนั้นเคยผ่านแล้วกลับพังในรีลีสนี้
- ของใหม่ที่เพิ่งพังแล้วยังไม่มีบันทึก
- แก้ด้วยการเปลี่ยนข้อความผู้ใช้เพื่อให้อีกแอปสวย

**ข้อจำกัดที่รู้จักไม่ใช่บัตรผ่านของรีเกรสชัน**

## ข้อจำกัดที่ต้องพูดออก

- สัญญานี้มีแค่ 5 แอปด้านบน
- ฟอนต์ที่ไฟล์ระบุต้องมีในเครื่องผู้ใช้ ไม่อยู่ในสัญญาเรนเดอร์
- `repair` วัดด้วยสัญญาของตัวเอง: ล้างห้าสาเหตุ ไม่แตะข้อความ ไม่ทับต้นฉบับ
  ไม่รับประกันการจัดหน้าของเอกสารที่คนอื่นสร้าง
- ความต่างที่ยอมรับแล้วอาจเปลี่ยนเมื่ออีกฝ่ายอัปเดต ต้องวัดใหม่เมื่อไบต์เอกสารเปลี่ยน
- พร็อกซีใน CI ผ่าน ไม่เท่ากับออราเคิลผ่าน

## คำถามเดียวต่อกฎ เมื่อจะเพิ่มฟีเจอร์

| กฎ | คำถาม |
|---|---|
| 0 | นี่คืออาการที่ประกาศ หรือเป็นงานใหม่ที่แอบป้ายว่าแก้ไทย |
| 1 | เปิดในแอปอ้างอิงแล้วใช้ต่อได้โดยไม่ซ่อมหรือไม่ อีก 4 แอปไม่แย่กว่าบันทึกหรือไม่ |
| 2.1 | ปิดรูนี้แล้วไปเปิดรูใหม่ในแอปไหน หรือในท่อต่อไฟล์ |
| 2.2 | ผู้ใช้ต้องเรียนวิธีจัดหน้าแบบใหม่หรือไม่ |
| 2.3 | เรากำลังทำหน้าที่ของ Word อยู่หรือไม่ |
| 3 | เราแตะตัวอักษรผู้ใช้หรือไม่ ถ้าเป็น repair เราทับต้นฉบับหรือไม่ |
| 4 | กรณีพังแล้วเรายังเขียนไฟล์อยู่หรือไม่ |
| 6 | ข้อจำกัดถูกเขียนไว้ในที่ที่ผู้ใช้เจอหรือไม่ |

---

# ร่องรอย — กฎข้อไหนถูกใช้ที่ไหน

กฎเป็นข้อความที่ใช้ตัดสิน บันทึกการตัดสินใจคือร่องรอยว่ากฎถูกใช้กับเรื่องจริงอย่างไร
และบันทึกใน `docs/evidence/` คือสิ่งที่เห็นกับตา บันทึกไม่ได้อยู่เหนือกฎ และกฎไม่ได้แทนบันทึก

อ้างได้เฉพาะบันทึกที่ยังมีผล เมื่อบันทึกถูกแทนที่ ต้องย้ายมาอ้างฉบับที่แทน

| กฎ | บันทึกการตัดสินใจ | สิ่งที่เห็นกับตา |
|---|---|---|
| 0 ขอบเขต | [0038 ทุก run บอกว่าเป็น complex script ส่วนภาษาไทยเขียนเมื่อสั่ง](adr/0038-the-thai-language-is-written-only-when-asked.md) · [0004 ไทยเป็นสคริปต์ซับซ้อน ห้าสาเหตุ](adr/0004-thai-is-complex-script-five-causes.md) · [0006 ใช้เมื่อเอกสารมีไทย](adr/0006-use-the-skill-when-the-document-contains-thai.md) | [ตัวตรวจแดงกับข้อบกพร่องที่ปลูกไว้](evidence/2026-09-15-checker-red-evidence.md) |
| 1 ใช้ต่อได้ทันที | [0012 พร็อกซีคือ XML ออราเคิลคือห้าแอป](adr/0012-xml-checks-are-the-proxy-office-apps-the-oracle.md) · [0027 เอกสารที่สร้างเองพกสิ่งที่แอปจะเติมให้](adr/0027-lists-carry-entries-and-runs-name-their-font.md) | [ห้าแอป](evidence/2026-09-16-office-check-five-applications.md) · [Word for macOS](evidence/2026-09-17-word-for-macos.md) · [WPS Writer](evidence/2026-09-19-wps-writer.md) · [สระอำกับภาษาไทย](evidence/2026-09-20-sara-am-and-the-thai-language.md) · [Word ไม่ repair สิ่งที่เปิด](evidence/2026-09-18-word-does-not-repair-what-it-opens.md) |
| 2.1 ไม่สร้างปัญหาใหม่ | [0033 กล่องงานเป็นอักษรในฟอนต์ข้อความ](adr/0033-the-task-box-is-a-square-in-a-text-font.md) · [0027](adr/0027-lists-carry-entries-and-runs-name-their-font.md) | [กล่องที่ทุกเครื่องวาดได้](evidence/2026-09-19-a-box-every-reader-can-draw.md) · [ข้อบกพร่องที่ปลูกใน ADR 0027](evidence/2026-09-16-adr-0027-mutations.md) |
| 2.2 ไม่สร้างมาตรฐานใหม่ | [0021 ภูมิภาค ชื่อตาราง และสารบัญ](adr/0021-regions-sections-captions-and-lists.md) · [0024 โปรไฟล์เป็นข้อมูล](adr/0024-profiles-are-data-saved-and-shared.md) · [0036 build เขียนเลขเอง เว้นแต่สั่ง `--auto-numbering`](adr/0036-who-counts-is-one-switch.md) | [โปรไฟล์เป็นข้อมูล](evidence/2026-09-16-profiles-are-data.md) |
| 2.3 ไม่แทนที่แอป | [0007 Markdown อย่างเดียว คำสั่งเดียว](adr/0007-markdown-in-one-command-builds-and-checks.md) · [0036](adr/0036-who-counts-is-one-switch.md) | [หัวข้อภาษาอังกฤษก็คือหัวข้อ](evidence/2026-09-19-an-english-heading-is-a-heading.md) |
| 3 ไม่แตะข้อความ | [0023 ซ่อมด้วย attribute ไม่แก้เนื้อหา](adr/0023-fidelity-transformations-restated-again.md) · [0037 repair คืนเลขรันของเอกสาร ถามก่อนว่าเป็นเลขแบบไหน](adr/0037-repair-renumbers-what-the-build-would-have-written.md) · [0034 สองอักขระที่ดูเหมือนตัวเดียว](adr/0034-two-characters-that-look-like-one.md) | [goldens และข้อบกพร่องที่ปลูกไว้](evidence/2026-09-15-build-goldens-and-mutations.md) · [repair คืนลำดับ property](evidence/2026-09-19-repair-puts-the-properties-back-in-order.md) · [สองอักขระที่ดูเหมือนตัวเดียว](evidence/2026-09-19-two-characters-that-look-like-one.md) |
| 4 สงสัยแล้วไม่เขียนไฟล์ | [0022 Markdown ที่รับ และสิ่งที่หยุด build](adr/0022-markdown-accepted-restated.md) · [0017 อ่านไฟล์ตามกฎที่ประกาศ](adr/0017-files-read-by-stated-rules.md) | [ภาพต้องทั้งภาพ ไม่งั้นถูกปฏิเสธ](evidence/2026-09-18-an-image-is-whole-or-it-is-refused.md) · [build บอกสิ่งที่ไม่ได้เขียน](evidence/2026-09-18-the-build-names-what-it-did-not-write.md) |
| 5 ย้อนลำดับกฎ | [0001 บันทึกทุกการตัดสินใจและที่มา](adr/0001-record-decisions-and-their-sources.md) | [หน้าที่ยังใช้อยู่ต้องชี้บันทึกที่ยังมีผล](evidence/2026-09-18-records-point-at-the-record-in-force.md) |
| 6 ไม่มีสูตรเดียว | [0012](adr/0012-xml-checks-are-the-proxy-office-apps-the-oracle.md) · [0036](adr/0036-who-counts-is-one-switch.md) | `references/limits.md` (ข้อกำหนดการนำไปใช้ รวมไว้หน้าเดียว) บันทึกข้อจำกัดของรีลีสใน [`docs/evidence/`](evidence/) และ `references/numbering.md`, `references/chapters.md` กับคู่มือทั้งสองภาษา |

---

# Reference translation

**The Thai above governs.** This is here so a reader who has no Thai can follow the same filter;
where the two differ, the Thai is the rule. The table just above this translation
(ร่องรอย) maps each rule to the decision records that applied it and to what was seen in
`docs/evidence/`: a record is a trace of a rule in use, never a rule of its own, and only a record
the index still marks accepted may be cited.

## Iron rules

A filter for decisions, not a vision. **Against a rule = do not do it, and write down why not.**

**0. The problem we answer for.** We fix `.docx` files holding Thai that a program or an agent
wrote as Latin script, with the declared symptoms: a red line under every word, lines that break
only at spaces, bold that is not bold, bullets that do not appear, and Word opening and saving
without fixing any of it. Nothing else is this skill's work — except a hole our own work opened.

**1. What leaves the skill must be usable straight away.** It passes when all of these hold at
once: Word 365 for Windows (the reference) passes the whole contract with no exception; the other
four oracle applications are checked with the same fixtures; a deviation in another application is
a limitation already in the record, not something new in this release; the user can open, read,
type on, lay out and save without repairing the file first; and there is no Repair dialog. It
fails when the user must open and fix the file before using it, or must know a way of working
peculiar to this skill. Beyond the five applications there is no contract: never write that
something works before it has been measured.

**2. We came to repair, not to set up a new system.**

- **2.1 Create no new problem.** No feature, flag, default or packing method may cause a new
  symptom in the applications tested, or break someone's other pipeline.
- **2.2 Introduce no new document standard and no new way of working in those applications.**
  The user still writes Thai as before, opens files as before, uses the application's own styles
  as before. All we may add is a way in — to create the file right from the start, or to ask for
  a copy marked as Thai. Never rule that an official letter, a thesis or a company document must
  look a certain way. Never imitate a real institution's template.
- **2.3 Do not stand in for those applications.** The skill is not Word, not a general
  typesetter, not a corporate template system. What the application already does, let it do.

**3. Finish the problem we answer for, and close the holes we open ourselves.** Build it right
from the start and check before writing the file. The text in the file matches the source
character for character. Repair with attributes: do not change words, do not delete invisible
characters, do not rearrange words to make something pass. A way of closing a hole must not break
rule 2. If closing it would mean changing the user's text, or making the user work differently in
their application — do not do it, and say why.

`repair` never overwrites the original; it writes a new file, and only when the user asks. IN is
not written. OUT's text equals IN's character for character, or no file is written. OUT must:
open with no Repair dialog; have the five declared causes cleared in the reference application;
and hold text equal to IN. What has nothing to do with the Thai symptoms passes through as it
was — including faults of the original that we did not cause and cannot fix without touching
content. Report which findings were repaired and which were not.

**4. In doubt, write no file.** The package fails the check; the text does not match the source;
the Markdown is outside the language accepted; a flag or profile fails the schema; it cannot be
repaired without touching text — stop, name the line or the cause, and hand over nothing
half-made.

**5. Too complex to decide: go back through 0 → 1 → 2 → 3 → 4.** If they still collide, choose the
side that is usable in the reference application and does not touch the user's text, then record
what was not done and why.

**6. Nothing fits every job.** Limitations, reasons for doing and for not doing, which
applications were tested, which are not covered, and the differences found, are written plainly
where the user meets them. Never paper over with "works everywhere" before it has been measured.

## The compatibility contract

The oracle set is checked before every tag that changes a document's bytes.

| role | application | may deviate |
|---|---|---|
| reference | Word 365 for Windows | never |
| oracle | Word for Mac | only if recorded |
| oracle | LibreOffice Writer | only if recorded |
| oracle | Google Docs | only if recorded |
| oracle | WPS Writer | only if recorded |

CI is a proxy (XML, fidelity, schema), not evidence that the file looks right. A release goes out
only when the reference application passes every item. Another application may deviate only in a
known limitation of that application and that version.

**Every item the reference application must pass:** opens with no Repair dialog; no Compatibility
Mode in the title bar; the status bar says Thai; no red line under correctly spelled words; bold
and italic show on Thai; bullets show; Thai lines break inside words, not only at spaces; the font
the file names is used; tables, links, headings, footnotes and images are complete and within the
page; the task boxes □ and ■ show as symbols.

The other four start from the same list. An item for which an application has no such mechanism —
Compatibility Mode, a language status bar, spell checking in Google Docs — is marked "—" and does
not count as a failure. Only items recorded as that application's limitation may fail.

**A deviation is acceptable only when all of these hold:** the reference application does not have
it; the cause is in that application and our attributes cannot reach it; the document is still
usable — read, typed on, saved; the text is not altered and the user need not work differently
there; and a record in `docs/evidence/` for the release carries the application, its version, the
fixture, the symptom, whether the reference passed, whether an attribute could fix it, why it was
not fixed, what it costs the reader, the date and the release. Something new in this release does
not count as accepted until it is written down before the tag.

**A deviation is unacceptable, however much we would like to record it,** when: the reference
application fails; any application in the set shows a Repair dialog; text is missing or differs
from the source; a declared cause has come back; an item that application used to pass now fails;
something newly broken has no record yet; or the fix would change the user's text to make another
application look better. **A known limitation is not a pass for a regression.**

**Limitations that must be said out loud:** this contract covers only the five applications above;
the font a file names must exist on the reader's machine, and is outside the rendering contract;
`repair` is measured by its own contract — clear the five causes, touch no text, overwrite no
original — and promises nothing about the layout of a document someone else made; an accepted
difference may change when the other side updates, so it is measured again whenever a document's
bytes change; and a proxy passing in CI is not the oracle passing.
