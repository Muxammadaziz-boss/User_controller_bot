# Ghost Control v3.0.6

**Chiqarilgan sana:** 2026-01-17

## 🆕 v3.0.6 O'zgarishlari

### 🔄 Yangi Arxitektura

v3.0.6 da arxitektura tubdan o'zgartirildi:

| Oldingi (v3.0.5) | Yangi (v3.0.6) |
|------------------|----------------|
| Client → **ADMIN_ID** ga xabar yuboradi | Client → **SERVER BOT** ga xabar yuboradi |
| Server bot client xabarlarini ko'rmaydi | Server bot **/ghost_register** buyruqlarini qabul qiladi |
| Qurilmalar ro'yxatga olinmaydi | Qurilmalar avtomatik ro'yxatga olinadi |

### 📊 Arxitektura Diagrammasi

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   CLIENT    │ ───► │  SERVER BOT │ ◄─── │    ADMIN    │
│  (User PC)  │      │ (AlwaysData)│      │ (Telegram)  │
└─────────────┘      └─────────────┘      └─────────────┘
     │                     │                     │
     │ /ghost_register     │                     │
     │ /ghost_heartbeat    │                     │
     │ /ghost_response     │                     │
     └─────────────────────┼─────────────────────┘
                           │
                      BOT boshqaradi
```

### 🛠️ Texnik O'zgarishlar

1. **config.py**
   - `SERVER_BOT_ID` qo'shildi (Bot token dagi ID)
   - Versiya 3.0.6 ga yangilandi

2. **main.py**
   - `SERVER_BOT_ID` import qilindi
   - Barcha xabarlar botga yuboriladi

3. **utils.py**
   - `register_device()` - `/ghost_register` ni SERVER_BOT_ID ga yuboradi
   - `heartbeat_loop()` - `/ghost_heartbeat` ni SERVER_BOT_ID ga yuboradi

4. **server/bot.py**
   - Versiya 3.0.6 ga yangilandi
   - Client xabarlarini qabul qiladi va qayta ishlaydi

### 🚀 O'rnatish

#### Client (Windows)
1. `v3.0.6/system/system.exe` ni yuklab olish
2. `.env` faylni sozlash (agar kerak bo'lsa)
3. EXE ni ishga tushirish

#### Server (AlwaysData/VPS)
1. `v3.0.6/server/` papkasini serverga yuklash
2. `.env` faylni sozlash
3. `python3 bot.py` ni ishga tushirish

### 📁 Fayl Strukturasi

```
v3.0.6/
├── system/
│   └── system.exe          # Tayyor EXE fayl
├── server/
│   ├── bot.py              # Server bot
│   ├── config.py           # Server konfiguratsiyasi
│   ├── database.py         # Asinxron database
│   ├── device_manager.py   # Qurilma boshqaruvchisi
│   └── ...
├── main.py                 # Client asosiy fayl
├── config.py               # Client konfiguratsiyasi
├── utils.py                # Utility funksiyalar
├── handlers.py             # Telegram handlers
└── README.md               # Hujjat
```

### ⚠️ Muhim Eslatmalar

- `.env` faylni GitHub ga **YUKLAMANG**
- API kalitlarni maxfiy saqlang
- EXE fayl faqat Windows da ishlaydi

---

**Muallif:** @Muxammadaziz_boss  
**Versiya:** 3.0.6  
**Litsenziya:** Shaxsiy foydalanish uchun
