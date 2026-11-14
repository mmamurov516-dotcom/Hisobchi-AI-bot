# 🤖 Gemini AI Bilan Ishlaydigan Aqlli Hisobchi Bot

Ushbu Telegram bot Google Gemini AI (gemini-3.5-flash) modeli asosida ishlaydi. Bot foydalanuvchining oylik daromadlari va kunlik barcha harajatlarini oddiy matn (text) ko'rinishida qabul qilib, barchasini aniq hisoblab boradi.

## 🚀 Asosiy Imkoniyatlari
- **Oylik daromadni kiritish:** Foydalanuvchi "Oyligim 5 million so'm" yoki shunga o'xshash matn yozsa, daromad sifatida qabul qilinadi.
- **Harajatlarni kiritish:** Bir nechta xaridni bitta xabarda yozsa ham (masalan: `1 kg olma uchun 10 ming som, 2 kg banan uchun 20 ming`), Gemini ularni alohida ajratib, narxlarini va kategoriyalarini aniqlab hisobga oladi.
- **Qancha pul qolganini ko'rsatish (Balans):** Daromaddan barcha sarflangan xarajatlar ayrilib, qolgan sof mablag' ko'rsatiladi.
- **Aynan nimaga qancha pul sarflanganini ko'rsatish:** Barcha xaridlar ro'yxati, miqdori va summasi bilan batafsil ro'yxat ko'rinishida taqdim etiladi.
- **1-bosqich:** Faqat matnli (text) xabarlar bilan ishlaydi.
- **Tuzatish / Bekor qilish:** Agar foydalanuvchi xato kiritib qo'ysa, `/bekor` buyrug'i orqali oxirgi yozuvni bekor qilishi mumkin.
- **Tozalash:** `/tozalash` buyrug'i hisobni noldan boshlash imkonini beradi.

## 📂 Loyiha Tuzilishi
- `main.py` — Botni ishga tushiruvchi asosiy fayl.
- `handlers.py` — Telegram xabarlarini qayta ishlovchi va foydalanuvchiga javob beruvchi qism.
- `ai_service.py` — Google Gemini SDK orqali erkin matnni tahlil qilib, JSON shaklda ma'lumotlarni ajratib oluvchi modul.
- `database.py` — SQLite (`aiosqlite`) ma'lumotlar bazasi bilan ishlash moduli.
- `formatters.py` — Chiroyli va o'qishga qulay moliyaviy hisobotlarni formatlash.
- `config.py` — Sozlamalar va `.env` o'quvchi modul.
- `.env` — Bot tokeni va Gemini API kaliti.

## ⚙️ Ishga Tushirish
Botni ishga tushirish uchun:
```bash
python main.py
```
Yoki `run.bat` fayliga 2 marta bosing.
