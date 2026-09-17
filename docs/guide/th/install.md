# ติดตั้งและเริ่มใช้

ทุกแอปใช้ไฟล์เดียวกัน คือ `thai-docx-<เลขรุ่น>.zip` จากหน้า
[Releases](https://github.com/sayam/thai-docx-skill/releases) ข้างในมีโฟลเดอร์เดียวชื่อ
`thai-docx/` หาแอปของเราด้านล่าง ทำตามขั้นตอน แล้วลองขอไฟล์แรก

[หน้าแรกของคู่มือ](../th.md) · [English](../en/install.md)

## ใช้อะไรได้ในแอปไหน

สองแถวแรกบอกว่าผู้ดูแลสกิลทำอะไรในแอปนั้นแล้วบ้าง คือ **ติดตั้งแล้ว** และ **สร้างไฟล์แล้ว** ช่องอื่นในตาราง
และแอปที่ยังไม่ได้ลอง เขียนตามคู่มือของผู้ผลิต ที่อ่านเมื่อวันที่ 17 กันยายน 2569 ถ้าลองแล้วไม่ได้ ช่วย
[แจ้งที่หน้า Issues](https://github.com/sayam/thai-docx-skill/issues)

| | แอป Claude | Claude Code | ChatGPT | Codex | แอป Gemini | เอเจนต์เขียนโค้ด | ไม่มี AI |
|---|---|---|---|---|---|---|---|
| ติดตั้งแล้ว | ลองแล้ว | ลองแล้ว | ยัง | ยัง | ยัง | ยัง | ลองแล้ว |
| สร้างไฟล์แล้ว | ยัง | ลองแล้ว | ยัง | ยัง | ยัง | ยัง | ลองแล้ว |
| สร้างไฟล์ (สถานการณ์ 1–4, 6, 7) | ได้ | ได้ | ได้ | ได้ | ได้ | ได้ | ได้ |
| ถามก่อนสร้าง (5, 11) | ถามเป็นข้อความ | กดเลือก | แล้วแต่แอป | แล้วแต่แอป | แล้วแต่แอป | แล้วแต่แอป | — |
| เก็บโปรไฟล์ (8–12) | แอปไม่เก็บให้: เก็บไฟล์ `.json` เอง | เก็บ | แอปไม่เก็บให้: เก็บไฟล์ `.json` เอง | เก็บ | แอปไม่เก็บให้: เก็บไฟล์ `.json` เอง | เก็บ ยกเว้นเอเจนต์บนคลาวด์ | เก็บ |
| ตรวจไฟล์ (13) | ได้ | ได้ | ได้ | ได้ | ได้ | ได้ | ได้ |
| ได้ไฟล์ที่ไหน | ดาวน์โหลดในแชต | ในโฟลเดอร์ | ดาวน์โหลดในแชต | ในโฟลเดอร์ | ยังไม่ทราบ | ในโฟลเดอร์ | ในโฟลเดอร์ |

"เก็บไฟล์ `.json` เอง" หมายความว่า แอปแชตจะลืมไฟล์เมื่อจบแชต เวลาบันทึกโปรไฟล์ ผู้ช่วยจะให้ไฟล์
`.json` มา ให้เก็บไฟล์นี้ไว้ แล้วแนบมาทุกครั้งที่อยากใช้

## แอป Claude

ใช้กับ Claude บนเว็บ (claude.ai) และแอป Claude บนคอมพิวเตอร์ สกิลที่อัปโหลดจะอยู่กับบัญชี Claude ของเรา
คู่มือของ Claude บอกว่า Cowork และส่วนเสริม Claude ใน Word, Excel, PowerPoint, Outlook ก็ใช้สกิลนี้ได้ด้วย

**ก่อนเริ่ม**

- ใช้ได้ทุกแพ็กเกจ: Free, Pro, Max, Team, Enterprise
- ต้องเปิดการรันโค้ด แพ็กเกจ Free, Pro, Max: ไปที่ **Settings > Capabilities** แล้วเปิด
  **Code execution and file creation** แพ็กเกจ Team เปิดสกิลไว้แล้ว ให้ดูว่าเปิดการรันโค้ดด้วย
  แพ็กเกจ Enterprise ให้ผู้ดูแลองค์กรเปิดการรันโค้ดและสกิลที่ **Organization settings > Skills**

**ติดตั้ง**

1. ดาวน์โหลด `thai-docx-<เลขรุ่น>.zip` ไม่ต้องแตกไฟล์
2. ใน Claude ไปที่ **Customize > Skills**
3. กด **+** แล้วกด **Create skill** แล้วกด **Upload a skill**
4. เลือกไฟล์ zip จะเห็น thai-docx ในรายการสกิล
5. ดูให้แน่ใจว่าสวิตช์ของ thai-docx เปิดอยู่

ลองแล้วเมื่อวันที่ 18 กันยายน 2569 ด้วยไฟล์ `thai-docx-0.1.1.zip` อัปโหลดผ่าน ระบบสแกนความปลอดภัยให้ตอนกดบันทึก
แล้วเห็นสกิลอยู่ในรายการ **Created by you** พร้อมสวิตช์เปิดอยู่ คู่มือของ Claude บอกว่าคำอธิบายสกิลยาวได้ไม่เกิน
200 ตัวอักษร รุ่น 0.1.0 ยาวเกิน รุ่น 0.1.1 เป็นต้นไปไม่เกินแล้ว ถ้าอัปโหลดไม่ผ่าน ช่วย
[แจ้งที่หน้า Issues](https://github.com/sayam/thai-docx-skill/issues) พร้อมข้อความที่ขึ้น

**เริ่มใช้**

เปิดแชตใหม่ แล้วพิมพ์

```text
ช่วยทำไฟล์ Word เรื่องวิธีประหยัดน้ำในบ้านแบบสั้น ๆ
```

Claude จะสร้างไฟล์ให้ กดดาวน์โหลดในแชต

**ข้อควรรู้**

- ถ้าจะใช้ไฟล์ Markdown รูป หรือไฟล์ Word ของเรา ให้แนบในแชต
- คำถามก่อนสร้าง (สถานการณ์ 5) มาเป็นข้อความ ตอบเป็นเลขข้อกับตัวอักษร เช่น `2b 7c`
- อย่าวางใจว่าไฟล์จะอยู่หลังจบแชต เก็บไฟล์โปรไฟล์ `.json` ที่ผู้ช่วยให้มาไว้เอง
- ถ้าอัปโหลดไม่ได้ ผู้ดูแลองค์กรอาจปิดสกิลที่ผู้ใช้สร้างเองไว้
- แพ็กเกจ Team และ Enterprise แบ่งสกิลให้คนอื่นได้ ที่เมนู **⋯ > Share** ของสกิล
- ที่มา: [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude),
  [Create and edit files with Claude](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude)

## Claude Code

**ก่อนเริ่ม**

- เครื่องต้องมี Python 3.11 ขึ้นไป หรือ Node.js 22 ขึ้นไป ดูได้ด้วยคำสั่ง `python3 --version`
  หรือ `node --version` ตัว Claude Code เองไม่ต้องใช้สองอย่างนี้ เครื่องจึงอาจยังไม่มี

**ติดตั้งให้ใช้ได้ทุกโปรเจกต์**

1. ดาวน์โหลด `thai-docx-<เลขรุ่น>.zip`
2. แตกไฟล์ไว้ในโฟลเดอร์สกิลของ Claude Code

   ```sh
   mkdir -p ~/.claude/skills
   unzip thai-docx-0.1.1.zip -d ~/.claude/skills
   ```

   บน Windows ใช้ PowerShell

   ```powershell
   Expand-Archive thai-docx-0.1.1.zip -DestinationPath $HOME\.claude\skills
   ```

3. ตรวจว่ามีไฟล์ `~/.claude/skills/thai-docx/SKILL.md`

ถ้าอยากใช้แค่โปรเจกต์เดียว ให้แตกไฟล์ไว้ในโฟลเดอร์ `.claude/skills` ของโปรเจกต์นั้นแทน

**เริ่มใช้**

1. เปิด Claude Code ในโฟลเดอร์ที่อยากให้ไฟล์ไปอยู่ ถ้าเปิดค้างไว้ก่อนสร้างโฟลเดอร์สกิล ให้ปิดแล้วเปิดใหม่
2. พิมพ์ `/skills` แล้วดูว่ามี thai-docx ในรายการ
3. พิมพ์คำขอ หรือขึ้นต้นด้วย `/thai-docx`

   ```text
   ช่วยทำไฟล์ Word ชื่อ water.docx เรื่องวิธีประหยัดน้ำในบ้านแบบสั้น ๆ
   ```

4. เมื่อ Claude Code ขออนุญาตรัน `python3` หรือ `node` ให้กดอนุญาต ไฟล์จะอยู่ในโฟลเดอร์

**ข้อควรรู้**

- คำถามก่อนสร้าง (สถานการณ์ 5) มาเป็นกล่องให้กดเลือก
- โปรไฟล์เก็บที่ `~/.thai-docx/profiles/` ใช้ได้ทุกโปรเจกต์ ถ้าเปิดโหมด sandbox ไว้
  Claude Code อาจเขียนที่นั่นไม่ได้ ให้พูดว่า "บันทึกไว้ในโปรเจกต์นี้" แทน
- ถ้าเข้าสู่ระบบ Claude Code ด้วยบัญชี Claude สกิลที่อัปโหลดไว้ในแอป Claude อาจมาอยู่ที่นี่ด้วย
- ที่มา: [Claude Code skills](https://code.claude.com/docs/en/skills)

## ChatGPT

วิธีใช้ขึ้นกับแพ็กเกจของเรา

| แพ็กเกจ | ทำอย่างไร |
|---|---|
| Business, Enterprise, Edu, Healthcare | อัปโหลดสกิล (ด้านล่าง) |
| Free, Go, Plus, Pro | ใช้แอป ChatGPT บนคอมพิวเตอร์ หรือ Codex แบบวางโฟลเดอร์ ดู [Codex](#codex) |
| ทุกแพ็กเกจ บนเว็บที่ไม่มีเมนูสกิล | แนบไฟล์ zip พร้อมใบสั่งงาน ตาม [PROMPT.th.md](https://github.com/sayam/thai-docx-skill/blob/main/PROMPT.th.md) |

**อัปโหลดสกิล (Business, Enterprise, Edu, Healthcare)**

1. ดาวน์โหลด `thai-docx-<เลขรุ่น>.zip`
2. ที่แถบด้านข้าง เปิด **Plugins** แล้วไปที่แท็บ **Skills**
3. กด **Create** แล้ว **Upload from your computer** แล้วเลือกไฟล์ zip
4. ChatGPT จะตรวจไฟล์ก่อน ถ้าขึ้นว่า **Needs Review** หรือ **Blocked** ให้ถามผู้ดูแลระบบของที่ทำงาน
   ผู้ดูแลระบบอาจต้องเปิดให้ใช้และอัปโหลดสกิลก่อนด้วย

**เริ่มใช้**

พิมพ์คำขอ

```text
ช่วยทำไฟล์ Word เรื่องวิธีประหยัดน้ำในบ้านแบบสั้น ๆ
```

กดดาวน์โหลดไฟล์ในแชต

**ไม่มีเมนูสกิล: แนบไฟล์พร้อมใบสั่งงาน**

1. แนบไฟล์ `thai-docx-<เลขรุ่น>.zip` ในแชตใหม่
2. คัดลอกใบสั่งงานจาก [PROMPT.th.md](https://github.com/sayam/thai-docx-skill/blob/main/PROMPT.th.md) มาวาง แล้วพิมพ์คำขอของเราต่อท้าย

วิธีนี้ยังไม่ได้ลองกับแอปใด ถ้าลองแล้วได้หรือไม่ได้ ช่วยเล่าที่หน้า
[Issues](https://github.com/sayam/thai-docx-skill/issues) ว่าใช้แอปอะไร และเจออะไร

วิธีนี้ต้องใช้แชตที่รัน Python กับไฟล์ที่แนบได้ ยังไม่ได้ลองใน ChatGPT

**ข้อควรรู้**

- แนบไฟล์ Markdown รูป หรือไฟล์ Word ของเราในแชต
- คำถามก่อนสร้าง (สถานการณ์ 5) มาเป็นข้อความ ตอบเป็นเลขข้อกับตัวอักษร
- อย่าวางใจว่าไฟล์จะอยู่หลังจบแชต เก็บไฟล์โปรไฟล์ `.json` ไว้เอง
- ที่มา: [Skills in ChatGPT](https://help.openai.com/en/articles/20001066-skills-in-chatgpt),
  [Data analysis with ChatGPT](https://help.openai.com/en/articles/8437071-data-analysis-with-chatgpt)

## Codex

ใช้กับ Codex CLI, ส่วนเสริม Codex ในโปรแกรมเขียนโค้ด และแอป ChatGPT บนคอมพิวเตอร์ ในแพ็กเกจที่มี Codex

**ก่อนเริ่ม**

- เครื่องต้องมี Python 3.11 ขึ้นไป หรือ Node.js 22 ขึ้นไป

**ติดตั้ง**

1. ดาวน์โหลด `thai-docx-<เลขรุ่น>.zip`
2. แตกไฟล์ไว้ในโฟลเดอร์สกิล

   ```sh
   mkdir -p ~/.agents/skills
   unzip thai-docx-0.1.1.zip -d ~/.agents/skills
   ```

   ถ้าใช้โปรเจกต์เดียว ให้แตกไว้ในโฟลเดอร์ `.agents/skills` ของโปรเจกต์นั้น
3. ตรวจว่ามีไฟล์ `~/.agents/skills/thai-docx/SKILL.md`

**เริ่มใช้**

1. พิมพ์ `/skills` แล้วดูว่ามี thai-docx ถ้าไม่มี ให้ปิดแล้วเปิด Codex ใหม่
2. พิมพ์คำขอ หรือขึ้นต้นด้วย `$thai-docx`

   ```text
   $thai-docx ช่วยทำไฟล์ Word ชื่อ water.docx เรื่องวิธีประหยัดน้ำในบ้านแบบสั้น ๆ
   ```

3. ไฟล์จะอยู่ในโฟลเดอร์โปรเจกต์

**ข้อควรรู้**

- Codex จะขออนุญาตก่อนเขียนไฟล์นอกโปรเจกต์ การบันทึกโปรไฟล์ไปที่ `~/.thai-docx/profiles/`
  อยู่นอกโปรเจกต์ ให้กดอนุญาต หรือพูดว่า "บันทึกไว้ในโปรเจกต์นี้"
- ที่มา: [Codex skills](https://developers.openai.com/codex/skills),
  [Codex sandboxing](https://learn.chatgpt.com/docs/sandboxing)

## Google Gemini

### แอป Gemini

สกิลใช้ได้ใน Gemini Spark สำหรับ Google AI Pro และ Ultra ที่เป็นบัญชีส่วนตัว

1. เปิด Gemini Spark แล้วไปที่ **Skills** แล้วกด **Upload**
2. เลือกไฟล์ `thai-docx-<เลขรุ่น>.zip`
3. ใน Spark พิมพ์คำขอ หรือพิมพ์ `/` แล้วเลือก thai-docx

ข้อควรรู้

- เงื่อนไขของ Google: เจ้าของบัญชีต้องอายุ 18 ปีขึ้นไป ต้องเปิด Keep Activity และยังไม่เปิดให้ใช้ใน
  เขตเศรษฐกิจยุโรป (EEA) สหราชอาณาจักร สวิตเซอร์แลนด์ และไนจีเรีย
- แอป Gemini รันสคริปต์ `.py` และ `.sh` ของสกิล ส่วน Python ของ thai-docx ใช้ได้ ไฟล์ `.js` ไม่ได้ใช้
  คู่มือของ Google ให้ `SKILL.md` อยู่ในโฟลเดอร์หลักของไฟล์ zip แต่ zip ของ thai-docx มีโฟลเดอร์ซ้อนอยู่
  จึงอาจอัปโหลดไม่ผ่าน ถ้าไม่ผ่าน ให้ zip **ของข้างใน** โฟลเดอร์ `thai-docx` แล้วลองใหม่
- ยังไม่ได้ลอง และคู่มือของ Google ไม่ได้บอกว่าดาวน์โหลดไฟล์ Word ได้หรือไม่ ช่วย
  [แจ้งที่หน้า Issues](https://github.com/sayam/thai-docx-skill/issues) ว่าเจออะไร
- ที่มา: [Skills in Gemini](https://support.google.com/gemini/answer/17094296)

### Antigravity และ Gemini CLI

Google เปลี่ยนจาก Gemini CLI เป็น Antigravity CLI ตั้งแต่มิถุนายน 2569 Gemini CLI ยังใช้ได้กับ
Gemini API key แบบเสียเงิน หรือสิทธิ์ใช้งาน Gemini Code Assist Standard หรือ Enterprise

- **Antigravity:** แตกไฟล์ zip ไว้ในโฟลเดอร์ `.agents/skills` ของโปรเจกต์ ให้ได้
  `.agents/skills/thai-docx/SKILL.md`
- **Gemini CLI:** รันคำสั่ง

  ```sh
  gemini skills install https://github.com/sayam/thai-docx-skill.git --path skills/thai-docx
  ```

  Gemini CLI จะขอความยินยอมทุกครั้งที่เริ่มใช้สกิล ดูรายการสกิลด้วย `/skills list`

ที่มา: [Antigravity skills](https://antigravity.google/docs/skills/),
[Gemini CLI skills](https://geminicli.com/docs/cli/skills/)

## GitHub Copilot

ใช้กับ Copilot agent mode ใน VS Code, Copilot CLI และ Copilot cloud agent

**ติดตั้ง**

- **ให้ตัวเราใช้ได้ทุกโปรเจกต์:** แตกไฟล์ zip ไว้ใน `~/.copilot/skills` ให้ได้
  `~/.copilot/skills/thai-docx/SKILL.md`
- **ให้ใช้ใน repository เดียว:** แตกไว้ใน `.github/skills` ของ repository นั้น แล้ว commit โฟลเดอร์นี้
  Copilot cloud agent ใช้ได้เฉพาะสกิลที่ commit ไว้ใน repository
- **ใช้ GitHub CLI** (รุ่นทดลอง)

  ```sh
  gh skill install sayam/thai-docx-skill thai-docx --scope user
  ```

**เริ่มใช้**

ใน agent mode พิมพ์คำขอ หรือขึ้นต้นด้วย `/thai-docx` เมื่อ Copilot ขออนุญาตรันคำสั่ง ให้กดอนุญาต

**ข้อควรรู้**

- cloud agent ทำงานในสำเนาใหม่ของ repository ทุกครั้ง จึงไม่เก็บโปรไฟล์ ยังไม่ได้ลอง
- ที่มา: [About agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills),
  [Agent skills in VS Code](https://code.visualstudio.com/docs/copilot/customization/agent-skills),
  [gh skill install](https://cli.github.com/manual/gh_skill_install)

## Cursor

**ติดตั้ง**

- แตกไฟล์ zip ไว้ใน `~/.cursor/skills` (ทุกโปรเจกต์) หรือ `.cursor/skills` (โปรเจกต์เดียว)
- Cursor อ่าน `~/.claude/skills` ด้วย ถ้าติดตั้ง thai-docx ให้ Claude Code ไว้แล้ว ก็ใช้ได้เลย

**เริ่มใช้**

ใน Agent พิมพ์คำขอ หรือขึ้นต้นด้วย `/thai-docx` เมื่อขออนุญาตรันคำสั่ง ให้กดอนุญาต

**ข้อควรรู้**

- Cloud Agents และการทำงานผ่าน SSH มองไม่เห็นสกิลที่อยู่แค่ในเครื่องของเรา
- ที่มา: [Cursor skills](https://cursor.com/docs/context/skills)

## เอเจนต์เขียนโค้ดอื่น ๆ

แตกไฟล์ zip ให้โฟลเดอร์ `thai-docx` อยู่ในโฟลเดอร์ตามตาราง หลายแอปอ่าน `~/.agents/skills`
ด้วย ถ้าวางไว้ที่นั่นที่เดียว หลายแอปก็ใช้ร่วมกันได้

| แอป | ให้ตัวเราใช้ | ให้โปรเจกต์เดียวใช้ |
|---|---|---|
| OpenCode | `~/.config/opencode/skills` หรือ `~/.agents/skills` | `.opencode/skills` หรือ `.agents/skills` |
| Goose | `~/.agents/skills` | `.agents/skills` |
| Amp | `~/.config/agents/skills` หรือ `~/.agents/skills` | `.agents/skills` |
| Kiro | `~/.kiro/skills` | `.kiro/skills` |
| Roo Code | `~/.roo/skills` หรือ `~/.agents/skills` | `.roo/skills` หรือ `.agents/skills` |
| Cline | `~/.cline/skills` | `.cline/skills` |
| Junie | `~/.junie/skills` หรือ `~/.agents/skills` | `.junie/skills` หรือ `.agents/skills` |
| Devin Desktop (ชื่อเดิม Windsurf) | `~/.config/devin/skills` หรือ `~/.agents/skills` | `.devin/skills` หรือ `.agents/skills` |
| Mistral Vibe CLI | `~/.vibe/skills` | `.vibe/skills` หรือ `.agents/skills` |

หรือใช้ตัวติดตั้งวางให้ ตัวติดตั้งต้องใช้ Node.js จะถามว่าเราใช้แอปไหนบ้าง และส่งข้อมูลการใช้งานแบบไม่ระบุตัวตน
ถ้าไม่ต้องการ ให้ตั้ง `DISABLE_TELEMETRY=1`

```sh
npx skills add sayam/thai-docx-skill --skill thai-docx -g
```

จากนั้นขอไฟล์ Word ได้เลย หรือพิมพ์ `/thai-docx` ในแอปที่มีคำสั่งขึ้นต้นด้วย `/`

ที่มา: [agentskills.io clients](https://agentskills.io/clients),
[vercel-labs/skills](https://github.com/vercel-labs/skills) และหน้าสกิลของแต่ละแอป:
[OpenCode](https://opencode.ai/docs/skills/),
[Goose](https://goose-docs.ai/docs/guides/context-engineering/using-skills/),
[Amp](https://ampcode.com/docs/customize/skills), [Kiro](https://kiro.dev/docs/skills/),
[Roo Code](https://roocodeinc.github.io/Roo-Code/features/skills),
[Cline](https://docs.cline.bot/features/skills),
[Junie](https://junie.jetbrains.com/docs/agent-skills.html),
[Devin](https://docs.devin.ai/cli/extensibility/skills/overview),
[Mistral Vibe](https://docs.mistral.ai/vibe/code/cli/skills)

## สำหรับนักพัฒนา

สำหรับโปรแกรมที่เราเขียนเอง สกิลจะรันใน container ของผู้ให้บริการ ซึ่งไม่มีอินเทอร์เน็ตและติดตั้งอะไรไม่ได้
thai-docx ไม่ต้องใช้ทั้งสองอย่าง

- **Claude API:** อัปโหลด zip ด้วย `POST /v1/skills` แล้วส่งคำขอโดยใส่สกิลใน `container.skills`
  และเปิดเครื่องมือ code execution container มี Python 3.11 รับไฟล์ Word ด้วย Files API
  ใช้ไม่ได้บน Amazon Bedrock และ Google Vertex AI
  [Skills guide](https://platform.claude.com/docs/en/build-with-claude/skills-guide)
- **Claude Agent SDK:** วางโฟลเดอร์ไว้ใน `~/.claude/skills` หรือ `.claude/skills` และอนุญาตเครื่องมือ
  `Bash`, `Read`, `Write` [Agent SDK skills](https://code.claude.com/docs/en/agent-sdk/skills)
- **OpenAI API:** อัปโหลด zip ด้วย `POST /v1/skills` แล้วเพิ่มเครื่องมือ `shell` ที่ container
  ระบุสกิลนี้ container มี Python 3.11 และ Node.js 22
  [Skills](https://developers.openai.com/api/docs/guides/tools-skills)
- **sandbox JavaScript ที่ไม่มี shell:** โหลด `scripts/thai_docx.js` แล้วเรียก `ThaiDocx.buildDocument`
  [references/sandbox.md](https://github.com/sayam/thai-docx-skill/blob/main/skills/thai-docx/references/sandbox.md)

## ตรวจไฟล์ที่ดาวน์โหลด

ไม่ทำก็ได้ ถ้ามี [GitHub CLI](https://cli.github.com/) ตรวจได้ว่าไฟล์ zip เป็นไฟล์ที่ระบบ release
ของโปรเจกต์สร้างจริง

```sh
gh attestation verify thai-docx-0.1.1.zip --repo sayam/thai-docx-skill
```

ถ้าถูกต้องจะขึ้นว่าตรวจผ่าน ถ้าเป็นไฟล์อื่นจะไม่ผ่าน

## อัปเดตหรือลบสกิล

รุ่นใหม่ไม่ได้วิ่งไปหาสำเนาที่ติดตั้งไว้แล้วเอง ต้องอัปเดตตามวิธีที่ติดตั้งไว้

**ดูว่าใช้รุ่นไหนอยู่**

- เปิดไฟล์ `thai-docx/SKILL.md` แล้วดูบรรทัด `version` ตอนต้นไฟล์ ในแอป Claude ดูได้ที่แท็บ
  **Contents** ของสกิล เป็นไฟล์เดียวกัน มี License, Compatibility, Author และ Version อยู่ด้านบน
  ส่วนแท็บ **Overview** ไม่บอกเลขรุ่น คำอธิบายที่เห็นตรงนั้นคือบรรทัด `description` ใน SKILL.md
  ซึ่งเขียนให้ผู้ช่วยอ่าน ไม่ใช่คำโปรยใต้หัวข้อ About ในหน้า GitHub ของโครงการ
- หรือถามผู้ช่วยว่า *สกิล thai-docx ที่มีอยู่เป็นรุ่นอะไร*
- รุ่นล่าสุดดูได้ที่[หน้า releases](https://github.com/sayam/thai-docx-skill/releases/latest)

**วิธีอัปเดต**

| ติดตั้งไว้แบบไหน | อัปเดตอย่างไร |
|---|---|
| แอป Claude (อัปโหลด) | ไปที่ **Customize > Skills** กดเข้าไปในหน้าของ thai-docx (ไม่ใช่เมนูในรายการ) แล้วกด **⋮ > Replace** เลือกไฟล์ zip ใหม่ ระบบจะสแกนความปลอดภัยอีกครั้ง (**Edit with Claude** ในเมนูเดียวกันคือเปิดแชตให้แก้สกิลด้วย `skill-creator` ไม่ใช่การใส่ไฟล์ zip) |
| โฟลเดอร์ที่แตก zip เอง (Claude Code, Codex, Copilot, Cursor, ไม่มี AI) | ลบโฟลเดอร์ `thai-docx` เก่าก่อน แล้วแตก zip ใหม่ลงที่เดิม ถ้าแตกทับของเก่า ไฟล์ที่รุ่นใหม่ไม่มีแล้วจะค้างอยู่ |
| `gh skill install` | รันคำสั่งเดิมซ้ำ จะได้ release ล่าสุด |
| `npx skills add` | รันคำสั่งเดิมซ้ำ จะได้โค้ดบน `main` |
| clone ของ repository | สั่ง `git pull` ในโฟลเดอร์ที่ clone ไว้ |

**สองเรื่องที่คนมักไม่รู้**

- **สกิลที่อัปโหลดในแอป Claude จะซิงก์ลงเครื่อง** Claude Code และเครื่องมืออื่นที่อ่านโฟลเดอร์สกิลที่ Claude
  ซิงก์ไว้ จะใช้สำเนานั้น อัปเดตในแอปที่เดียวจึงอัปเดตให้ทั้งหมด ไม่ต้องแตก zip ใหม่เอง
- **ถ้าเปิด repo ที่ clone ไว้เป็นโปรเจกต์ เครื่องมือจะอ่านจาก repo นั้นก่อน** ไม่ว่ามันจะเก่าแค่ไหน
  ให้สั่ง `git pull` ในโฟลเดอร์นั้น

**ลบสกิล**

ลบโฟลเดอร์ `thai-docx` หรือในแอป Claude กด **⋮ > Remove** เมนู **⋮** ในรายการสกิลมีแค่ **Turn off**
(ปิดไว้เฉย ๆ ยังไม่ลบ) กับ **Remove** ส่วนเมนูในหน้าของสกิลมีครบกว่า รวมถึง **Download** ที่ขอไฟล์ zip คืนได้
โปรไฟล์ยังอยู่ที่ `~/.thai-docx/profiles/`
จนกว่าจะลบเอง
