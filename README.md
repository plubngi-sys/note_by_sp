# Note by SP 🧡

เว็บบันทึกและสรุปบทเรียนรายวัน ธีมครีมส้ม: Dashboard, Calendar, Notes, Subjects, Login, PostgreSQL

## Features
- สมัครสมาชิกและเข้าสู่ระบบด้วย JWT
- เพิ่ม แก้ไข ลบ ค้นหาโน้ต แยกตามรายวิชา
- Dashboard สถิติการจดบันทึกและ streak
- ปฏิทินแสดงวันที่จดโน้ต
- ข้อมูลผู้ใช้แต่ละคนแยกจากกันด้วย user_id

## เริ่มใช้งานบน Windows
1. ติดตั้ง Docker Desktop และเปิดโปรแกรมให้ทำงาน
2. เปิดโปรเจกต์ใน VS Code และเปิด Terminal
3. คัดลอกไฟล์ตัวอย่างเป็นไฟล์ตั้งค่า:

```powershell
Copy-Item .env.example .env
```

4. สุ่ม SECRET_KEY ที่ปลอดภัยด้วย Python (ต้องติดตั้ง Python):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

5. เปิดไฟล์ `.env` และแทน `replace-with-a-long-random-secret-key` ด้วยค่าที่สุ่มได้
6. รัน:

```powershell
docker compose up --build
```

7. เว็บ: http://localhost:5173
8. API docs: http://localhost:8000/docs

## โครงสร้าง
```
backend/app/main.py     FastAPI, authentication, models, endpoints
backend/requirements.txt
frontend/src/App.jsx    Dashboard, Calendar, Notes, Subjects, Login
frontend/src/api.js     Frontend API client
frontend/src/styles.css Cream-orange responsive styling
docker-compose.yml      PostgreSQL + backend + frontend
.env.example            Template for local secret key
```

## ความปลอดภัย
- ห้าม Commit `.env`, token หรือรหัสผ่านจริง (มี `.gitignore`)
- ค่า DB user/password ใน docker-compose เป็น **ค่า development เท่านั้น** ไม่ใช้ Production
- อย่าเปิด PostgreSQL/API สู่สาธารณะโดยไม่ตั้งค่าความปลอดภัย, HTTPS, migration และ backup
- Repository นี้เป็น **Public** ในตอนที่อัปโหลด: source code ทุกไฟล์ที่ commit มองเห็นได้ทั่วไป

## สถานะ
Starter source code; ยังไม่ได้ยืนยันการ build/run Docker บนเครื่องผู้ใช้ และยังไม่มี Rich Text Editor/AI/PDF attachments
