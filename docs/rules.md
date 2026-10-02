# กฎเหล็ก — thai-docx-skill

กฎชุดนี้ใช้คัดกรองการตัดสินใจ ไม่ใช่ถ้อยแถลงวิสัยทัศน์
สิ่งใดขัดกับกฎ ให้ไม่ทำ และเขียนเหตุผลที่ไม่ทำไว้

ฉบับภาษาไทยข้างล่างนี้คือฉบับจริง คำแปลภาษาอังกฤษท้ายหน้ามีไว้อ้างอิง
เมื่อสองฉบับต่างกัน ให้ถือตามภาษาไทย

## 0. ขอบเขตปัญหาที่รับผิดชอบ

เราแก้ไฟล์ `.docx` ที่มีข้อความภาษาไทย ซึ่งโปรแกรมหรือเอเจนต์สร้างขึ้น แต่ระบุข้อความไทยในไฟล์ว่าเป็นอักษรแบบละติน (Latin script)
จนเกิดอาการที่ประกาศไว้ ได้แก่ มีเส้นแดงใต้คำ ขึ้นบรรทัดใหม่ได้เฉพาะตรงช่องว่าง ตัวหนาไม่แสดงเป็นตัวหนา
สัญลักษณ์หน้ารายการ (bullet) ไม่แสดง และเปิดแล้วบันทึกซ้ำใน Word อาการก็ยังไม่หาย

เรื่องอื่นนอกจากนี้ไม่ใช่งานของ skill นี้ เว้นแต่เป็นปัญหาที่ผลงานของเราเองก่อขึ้น

## 1. ไฟล์ที่ skill สร้างต้องใช้งานต่อได้ทันที

**ถือว่าผ่าน** เมื่อเป็นจริงครบทุกข้อต่อไปนี้พร้อมกัน

- Word 365 for Windows (แอปอ้างอิง) ผ่านทุกข้อของสัญญาความเข้ากันได้ด้านล่าง โดยไม่มีข้อยกเว้น
- แอปตรวจเทียบ (oracle) อีก 4 แอป ได้รับการตรวจด้วยไฟล์ทดสอบ (fixture) ชุดเดียวกัน
- ถ้าแอปอื่นแสดงผลเพี้ยน ความเพี้ยนนั้นต้องเป็นข้อจำกัดที่รู้จักและบันทึกไว้แล้ว ไม่ใช่ปัญหาใหม่ที่เกิดในรุ่นนี้
- ผู้ใช้เปิดไฟล์แล้วอ่าน พิมพ์ต่อ จัดหน้า และบันทึกได้ โดยไม่ต้องซ่อมไฟล์ก่อนใช้
- ไม่มีกล่องข้อความ Repair (ให้ซ่อมไฟล์) ขึ้นมา

**ถือว่าไม่ผ่าน** เมื่อผู้ใช้ต้องเปิดไฟล์แล้วแก้ไขก่อนใช้ หรือต้องรู้วิธีการเฉพาะของ skill นี้จึงจะใช้ไฟล์ได้
แอปอื่นนอกเหนือจาก 5 แอปในตารางด้านล่างไม่อยู่ในสัญญา ห้ามเขียนว่าใช้ได้หากยังไม่ได้ทดสอบวัดผลจริง

## 2. เรามาเพื่อซ่อม ไม่ได้มาเพื่อวางระบบใหม่

### 2.1 ไม่สร้างปัญหาใหม่

ฟีเจอร์ ตัวเลือกคำสั่ง (flag) ค่าเริ่มต้น หรือวิธีจัดแพ็กเกจไฟล์ ต้องไม่ทำให้เกิดอาการใหม่ในแอปที่ทดสอบ
และต้องไม่ทำให้ขั้นตอนหรือเครื่องมืออื่นที่ผู้ใช้นำไฟล์ไปใช้ต่อทำงานผิดพลาด

### 2.2 ไม่สร้างมาตรฐานเอกสารใหม่ และไม่บังคับวิธีทำงานใหม่ในแอปเหล่านั้น

ผู้ใช้ยังเขียนภาษาไทย เปิดไฟล์ และใช้สไตล์ของแอปแบบเดิม
สิ่งที่เราเพิ่มได้มีเพียงช่องทางสร้างไฟล์ให้ถูกต้องตั้งแต่แรก หรือช่องทางขอสำเนาไฟล์ที่ระบุภาษาไทยไว้ถูกต้อง
ห้ามกำหนดว่าเอกสารราชการ วิทยานิพนธ์ หรือเอกสารขององค์กรต้องมีรูปแบบอย่างใดอย่างหนึ่ง
และห้ามเลียนแบบแม่แบบ (template) ของสถาบันที่มีอยู่จริง

### 2.3 ไม่ทำหน้าที่แทนแอปเหล่านั้น

skill นี้ไม่ใช่ Word ไม่ใช่โปรแกรมจัดเรียงพิมพ์ทั่วไป และไม่ใช่ระบบแม่แบบขององค์กร
สิ่งใดที่แอปทำได้อยู่แล้ว ให้แอปเป็นผู้ทำ

## 3. แก้ปัญหาที่รับผิดชอบให้จบ และแก้ปัญหาที่เราก่อขึ้นเอง

สร้างไฟล์ให้ถูกต้องตั้งแต่แรก และตรวจก่อนเขียนไฟล์
ข้อความในไฟล์ต้องตรงกับต้นฉบับทุกตัวอักษร
ซ่อมด้วยการแก้ค่าคุณสมบัติ (attribute) ในไฟล์ ไม่แก้ถ้อยคำ ไม่ลบอักขระที่มองไม่เห็น และไม่เรียงคำใหม่เพื่อให้ผ่านการตรวจ
วิธีแก้ปัญหาต้องไม่ขัดกับข้อ 2
ถ้าการแก้ปัญหาต้องเปลี่ยนข้อความของผู้ใช้ หรือต้องให้ผู้ใช้ทำงานในแอปด้วยวิธีที่ต่างไปจากเดิม ให้ไม่ทำ และแจ้งเหตุผล

คำสั่ง `repair` ไม่เขียนทับต้นฉบับ แต่เขียนเป็นไฟล์ใหม่ และทำเมื่อผู้ใช้ขอเท่านั้น

- ไม่มีการเขียนใด ๆ ลงไฟล์ต้นฉบับ (IN)
- ข้อความในไฟล์ผลลัพธ์ (OUT) ต้องตรงกับข้อความใน IN ทุกตัวอักษร มิฉะนั้นจะไม่เขียนไฟล์
- ส่วนที่ไม่เกี่ยวกับอาการของภาษาไทยต้องคงไว้ตามเดิม
- OUT ต้องผ่านเกณฑ์ต่อไปนี้: เปิดได้โดยไม่มีกล่องข้อความ Repair · สาเหตุทั้งห้าที่ประกาศไว้ในข้อ 0 หมดไปเมื่อเปิดในแอปอ้างอิง ·
  ข้อความตรงกับ IN ทุกตัวอักษร
  ส่วนที่ไม่เกี่ยวกับอาการของภาษาไทยคงไว้ตามเดิม รวมถึงข้อบกพร่องของต้นฉบับที่เราไม่ได้ทำให้เกิด
  และแก้ไม่ได้หากไม่แตะเนื้อหา
- รายงานว่าแก้ข้อที่ตรวจพบ (finding) ข้อใดแล้ว และข้อใดไม่ได้แก้

## 4. หากไม่แน่ใจ ให้ไม่เขียนไฟล์

กรณีเหล่านี้ ได้แก่ ไฟล์ที่ได้ (แพ็กเกจ) ไม่ผ่านการตรวจ ข้อความไม่ตรงกับต้นฉบับ Markdown ใช้รูปแบบนอกเหนือจากที่รองรับ
ตัวเลือกคำสั่งหรือโปรไฟล์ไม่ผ่านการตรวจตามสคีมา หรือซ่อมไม่ได้หากไม่แตะข้อความ
ให้หยุด ระบุบรรทัดหรือสาเหตุ และไม่ส่งไฟล์ที่ทำไม่เสร็จออกไป

## 5. หากซับซ้อนจนตัดสินใจไม่ได้ ให้ไล่ทบทวนกฎตามลำดับ 0 → 1 → 2 → 3 → 4

ถ้ากฎยังขัดกันอยู่ ให้เลือกทางที่ใช้งานต่อได้ในแอปอ้างอิงและไม่แตะข้อความของผู้ใช้
แล้วบันทึกว่าไม่ได้ทำอะไร และเพราะเหตุใด

## 6. ไม่มีสูตรเดียวที่ใช้ได้กับทุกงาน

ข้อจำกัด เหตุผลที่ทำ เหตุผลที่ไม่ทำ แอปที่ทดสอบแล้ว แอปที่ไม่รับรอง
และความแตกต่างที่พบ ต้องเขียนไว้อย่างตรงไปตรงมาในตำแหน่งที่ผู้ใช้จะพบ
ห้ามสรุปรวบยอดด้วยคำว่า "รองรับทั่วไป" หากยังไม่ได้ทดสอบวัดผลจริง

---

# สัญญาความเข้ากันได้

ก่อนติดแท็กรุ่นใดก็ตามที่ทำให้ไบต์ของเอกสารที่สร้างเปลี่ยนไป ต้องตรวจในแอปชุดตรวจเทียบ (oracle) ทั้งชุด

| บทบาท | แอป | แสดงผลต่างได้หรือไม่ |
|---|---|---|
| อ้างอิง | Word 365 for Windows | ไม่ได้ |
| ตรวจเทียบ | Word for Mac | ได้ เมื่อบันทึกไว้แล้ว |
| ตรวจเทียบ | LibreOffice Writer | ได้ เมื่อบันทึกไว้แล้ว |
| ตรวจเทียบ | Google Docs | ได้ เมื่อบันทึกไว้แล้ว |
| ตรวจเทียบ | WPS Writer | ได้ เมื่อบันทึกไว้แล้ว |

การตรวจใน CI (XML ความตรงของข้อความ และสคีมา) เป็นเพียงการตรวจแทน ไม่ใช่หลักฐานว่าไฟล์แสดงผลถูกต้อง
จะออกรุ่นได้ก็ต่อเมื่อแอปอ้างอิงผ่านทุกข้อ
แอปอื่นแสดงผลเพี้ยนได้เฉพาะในข้อจำกัดที่รู้จักแล้วของแอปนั้นและเวอร์ชันนั้น

## สัญญาที่แอปอ้างอิงต้องผ่านทุกข้อ

- เปิดได้โดยไม่มีกล่องข้อความ Repair
- แถบชื่อไม่แสดง Compatibility Mode
- แถบสถานะแสดงภาษาเป็นไทย
- ไม่มีเส้นแดงใต้คำที่สะกดถูก
- ตัวหนาและตัวเอียงบนข้อความไทยแสดงผลจริง
- สัญลักษณ์หน้ารายการ (bullet) แสดง
- บรรทัดภาษาไทยตัดคำขึ้นบรรทัดใหม่ภายในคำได้ ไม่ใช่ตัดเฉพาะที่ช่องว่าง
- แอปใช้ฟอนต์ตามที่ไฟล์ระบุ
- ตาราง ลิงก์ หัวข้อ เชิงอรรถ และรูปภาพ ครบถ้วนและอยู่ภายในหน้า
- กล่องรายการงาน □ ■ แสดงเป็นสัญลักษณ์

อีก 4 แอปใช้รายการเดียวกันนี้เป็นเกณฑ์ตั้งต้น
ข้อใดที่แอปนั้นไม่มีกลไกดังกล่าวเลย เช่น Compatibility Mode แถบสถานะแสดงภาษา หรือการตรวจตัวสะกด
ใน Google Docs ให้ใส่เครื่องหมาย — และไม่นับว่าไม่ผ่าน
ข้อที่ไม่ผ่านได้ มีเฉพาะข้อที่บันทึกไว้เป็นข้อจำกัดของแอปนั้น

## ความเพี้ยนที่ยอมรับได้ ต้องเป็นจริงครบทุกข้อ

- แอปอ้างอิงไม่เพี้ยนในข้อนั้น
- สาเหตุอยู่ที่ตัวแอปนั้นเอง และ attribute ที่เราเขียนลงไฟล์แก้ไม่ได้
- เอกสารยังใช้งานต่อได้ คือ อ่าน พิมพ์ต่อ และบันทึกได้
- ข้อความไม่เพี้ยน และผู้ใช้ไม่ต้องทำงานด้วยวิธีที่ต่างไปในแอปนั้น
- มีบันทึกใน `docs/evidence/` ของรุ่นนั้น ระบุ แอป เวอร์ชัน fixture อาการ
  แอปอ้างอิงผ่านหรือไม่ แก้ด้วย attribute ได้หรือไม่ เหตุผลที่ไม่แก้
  ผลกระทบต่อการใช้งานต่อ วันที่ตรวจ และรุ่น
- ความเพี้ยนใหม่ที่เกิดในรุ่นนี้ ยังไม่นับว่า "ยอมรับแล้ว" จนกว่าจะบันทึกไว้ก่อนติดแท็กรุ่น

## ความเพี้ยนที่ยอมรับไม่ได้ แม้เราอยากจะบันทึกไว้ก็ตาม

- แอปอ้างอิงไม่ผ่าน
- มีกล่องข้อความ Repair ขึ้นในแอปใดก็ตามในชุด
- ข้อความไม่ครบ หรือตัวอักษรไม่ตรงกับต้นฉบับ
- สาเหตุที่ประกาศไว้ในขอบเขตปัญหา (ข้อ 0) กลับมาเกิดอีก
- ข้อที่แอปนั้นเคยผ่านแล้ว กลับไม่ผ่านในรุ่นนี้
- ปัญหาใหม่ที่เพิ่งเกิดแต่ยังไม่มีบันทึก
- แก้ไขด้วยการเปลี่ยนข้อความของผู้ใช้ เพื่อให้แอปอื่นแสดงผลสวยงาม

**ข้อจำกัดที่รู้จักแล้ว ใช้เป็นเหตุให้ผ่านไม่ได้ เมื่อข้อที่เคยผ่านกลับไม่ผ่าน (regression)**

## ข้อจำกัดที่ต้องประกาศให้ชัด

- สัญญานี้ครอบคลุมเพียง 5 แอปข้างต้น
- ฟอนต์ที่ไฟล์ระบุต้องติดตั้งอยู่ในเครื่องของผู้ใช้ และไม่อยู่ในสัญญาด้านการแสดงผล
- `repair` วัดผลด้วยสัญญาของตัวเอง คือ ขจัดสาเหตุทั้งห้า ไม่แตะข้อความ และไม่เขียนทับต้นฉบับ
  โดยไม่รับประกันการจัดหน้าของเอกสารที่ผู้อื่นสร้าง
- ความแตกต่างที่ยอมรับแล้วอาจเปลี่ยนไปเมื่ออีกฝ่ายอัปเดตแอป จึงต้องวัดผลใหม่ทุกครั้งที่ไบต์ของเอกสารเปลี่ยน
- การตรวจแทนใน CI ผ่าน ไม่ได้แปลว่าผ่านการตรวจในแอปชุดตรวจเทียบ

## คำถามประจำกฎแต่ละข้อ เมื่อจะเพิ่มฟีเจอร์

| กฎ | คำถาม |
|---|---|
| 0 | นี่คืออาการที่ประกาศไว้ หรือเป็นงานใหม่ที่แอบอ้างว่าเป็นการแก้ปัญหาภาษาไทย |
| 1 | เปิดในแอปอ้างอิงแล้วใช้งานต่อได้โดยไม่ต้องซ่อมหรือไม่ และอีก 4 แอปแย่ไม่เกินกว่าที่บันทึกไว้หรือไม่ |
| 2.1 | แก้ปัญหานี้แล้ว ไปก่อปัญหาใหม่ในแอปใด หรือในขั้นตอนที่นำไฟล์ไปใช้ต่อหรือไม่ |
| 2.2 | ผู้ใช้ต้องเรียนรู้วิธีจัดหน้าแบบใหม่หรือไม่ |
| 2.3 | เรากำลังทำหน้าที่แทน Word อยู่หรือไม่ |
| 3 | เราแตะตัวอักษรของผู้ใช้หรือไม่ และถ้าเป็น `repair` เราเขียนทับต้นฉบับหรือไม่ |
| 4 | เมื่อเกิดความผิดพลาด เรายังเขียนไฟล์ออกไปอยู่หรือไม่ |
| 6 | ข้อจำกัดถูกเขียนไว้ในตำแหน่งที่ผู้ใช้จะพบหรือไม่ |

---

# ร่องรอย — กฎข้อไหนถูกใช้ที่ไหน

กฎคือข้อความที่ใช้ตัดสิน บันทึกการตัดสินใจ (ADR) คือร่องรอยว่ากฎถูกนำไปใช้กับเรื่องจริงอย่างไร
และบันทึกใน `docs/evidence/` คือสิ่งที่ตรวจเห็นจริง บันทึกไม่ได้อยู่เหนือกฎ และกฎก็ไม่ได้ใช้แทนบันทึก

อ้างอิงได้เฉพาะบันทึกที่ยังมีผลอยู่ เมื่อบันทึกใดถูกแทนที่ ต้องเปลี่ยนไปอ้างฉบับที่มาแทน

| กฎ | บันทึกการตัดสินใจ | สิ่งที่ตรวจเห็นจริง |
|---|---|---|
| 0 ขอบเขต | [0039 ทำเครื่องหมาย complex script ตรงที่ข้อความเป็น complex script](adr/0039-complex-script-is-marked-where-it-is.md) · [0038 ภาษาไทยเขียนเมื่อสั่งเท่านั้น](adr/0038-the-thai-language-is-written-only-when-asked.md) · [0004 ไทยเป็นสคริปต์ซับซ้อน ห้าสาเหตุ](adr/0004-thai-is-complex-script-five-causes.md) · [0006 ใช้เมื่อเอกสารมีไทย](adr/0006-use-the-skill-when-the-document-contains-thai.md) | [ตัวตรวจแดงกับข้อบกพร่องที่ปลูกไว้](evidence/2026-09-15-checker-red-evidence.md) · [ทำเครื่องหมายเฉพาะที่เป็น complex script](evidence/2026-09-22-marking-only-what-is-complex-script.md) · [Word เขียนอะไรเมื่อคนพิมพ์](evidence/2026-09-22-what-word-writes-when-a-person-types.md) |
| 1 ใช้ต่อได้ทันที | [0012 การตรวจ XML ใน CI เป็นการตรวจแทน ห้าแอปเป็นชุดตรวจเทียบ](adr/0012-xml-checks-are-the-proxy-office-apps-the-oracle.md) · [0027 เอกสารที่สร้างเองพกสิ่งที่แอปจะเติมให้](adr/0027-lists-carry-entries-and-runs-name-their-font.md) | [ห้าแอป](evidence/2026-09-16-office-check-five-applications.md) · [Word for macOS](evidence/2026-09-17-word-for-macos.md) · [WPS Writer](evidence/2026-09-19-wps-writer.md) · [สระอำกับภาษาไทย](evidence/2026-09-20-sara-am-and-the-thai-language.md) · [Word 365 Windows บนไบต์รีลีส](evidence/2026-09-22-word-365-windows-on-the-release-bytes.md) · [Word ไม่ repair สิ่งที่เปิด](evidence/2026-09-18-word-does-not-repair-what-it-opens.md) · [v0.2.0: อ่านแล้วในแอปไหน และยังไม่ได้อ่าน](evidence/2026-09-24-what-v0.2.0-was-read-in.md) · [v0.3.0: อ่านครบห้าแอป](evidence/2026-09-27-what-v0.3.0-was-read-in.md) |
| 2.1 ไม่สร้างปัญหาใหม่ | [0033 กล่องงานเป็นอักษรในฟอนต์ข้อความ](adr/0033-the-task-box-is-a-square-in-a-text-font.md) · [0027](adr/0027-lists-carry-entries-and-runs-name-their-font.md) | [กล่องที่ทุกเครื่องวาดได้](evidence/2026-09-19-a-box-every-reader-can-draw.md) · [ข้อบกพร่องที่ปลูกใน ADR 0027](evidence/2026-09-16-adr-0027-mutations.md) |
| 2.2 ไม่สร้างมาตรฐานใหม่ | [0021 ภูมิภาค ชื่อตาราง และสารบัญ](adr/0021-regions-sections-captions-and-lists.md) · [0024 โปรไฟล์เป็นข้อมูล](adr/0024-profiles-are-data-saved-and-shared.md) · [0036 build เขียนเลขเอง เว้นแต่สั่ง `--auto-numbering`](adr/0036-who-counts-is-one-switch.md) | [โปรไฟล์เป็นข้อมูล](evidence/2026-09-16-profiles-are-data.md) |
| 2.3 ไม่แทนที่แอป | [0007 Markdown อย่างเดียว คำสั่งเดียว](adr/0007-markdown-in-one-command-builds-and-checks.md) · [0036](adr/0036-who-counts-is-one-switch.md) | [หัวข้อภาษาอังกฤษก็คือหัวข้อ](evidence/2026-09-19-an-english-heading-is-a-heading.md) |
| 3 ไม่แตะข้อความ | [0023 ซ่อมด้วย attribute ไม่แก้เนื้อหา](adr/0023-fidelity-transformations-restated-again.md) · [0037 repair ใส่เลขลำดับแบบที่ build จะเขียน โดยถามก่อนว่าเอกสารใช้เลขแบบไหน](adr/0037-repair-renumbers-what-the-build-would-have-written.md) · [0034 สองอักขระที่ดูเหมือนตัวเดียว](adr/0034-two-characters-that-look-like-one.md) | [goldens และข้อบกพร่องที่ปลูกไว้](evidence/2026-09-15-build-goldens-and-mutations.md) · [repair คืนลำดับ property](evidence/2026-09-19-repair-puts-the-properties-back-in-order.md) · [สองอักขระที่ดูเหมือนตัวเดียว](evidence/2026-09-19-two-characters-that-look-like-one.md) |
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
wrote with the Thai marked as Latin script, with the declared symptoms: a red line under every word, lines that break
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
  symptom in the applications tested, or break the tools or steps someone takes the file on to.
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

`repair` never overwrites the original; it writes a new file, and only when the user asks. Nothing is
written to IN, the original. OUT's text equals IN's character for character, or no file is written. OUT must:
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

The checks in CI (XML, text fidelity, schema) are a proxy, not evidence that the file looks right. A release goes out
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
application look better. **A known limitation is no pass for a regression — an item that passed before and fails now.**

**Limitations that must be said out loud:** this contract covers only the five applications above;
the font a file names must exist on the reader's machine, and is outside the rendering contract;
`repair` is measured by its own contract — clear the five causes, touch no text, overwrite no
original — and promises nothing about the layout of a document someone else made; an accepted
difference may change when the other side updates, so it is measured again whenever a document's
bytes change; and the proxy passing in CI is not the oracle applications passing.

## One question per rule, when a feature is added

| rule | question |
|---|---|
| 0 | Is this a declared symptom, or new work passed off as fixing Thai? |
| 1 | Is it usable in the reference application without a repair, and are the other four no worse than recorded? |
| 2.1 | Does fixing this cause a new problem in any application, or in a step the file is taken on to? |
| 2.2 | Must the user learn a new way of laying out pages? |
| 2.3 | Are we doing Word's job? |
| 3 | Do we touch the user's characters, and, for `repair`, do we overwrite the original? |
| 4 | When something goes wrong, do we still write a file? |
| 6 | Is the limitation written where the user will find it? |
