# device_manager.py - DEVICE ID & MANAGEMENT (v3.0.2)
"""
Device management system:
- Unique device ID generation
- Device registration
- Status tracking
- Heartbeat system
"""

import uuid
import socket
import getpass
import platform
import hashlib
import time
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ==================== DEVICE ID GENERATION ====================
def generate_device_id():
    """
    Unique device ID yaratish
    
    Format: DEV-{hostname}-{mac_hash}-{random}
    """
    try:
        hostname = socket.gethostname()[:15]
        mac = uuid.getnode()
        mac_hex = '{:012x}'.format(mac)
        mac_hash = hashlib.md5(mac_hex.encode()).hexdigest()[:6]
        random_suffix = hashlib.md5(str(time.time()).encode()).hexdigest()[:4]
        device_id = f"DEV-{hostname}-{mac_hash}-{random_suffix}"
        return device_id
    except Exception as e:
        logger.error(f"Generate device ID error: {e}")
        return f"DEV-UNKNOWN-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"

def get_device_info():
    """Device haqida to'liq ma'lumot"""
    try:
        info = {
            'hostname': socket.gethostname(),
            'username': getpass.getuser(),
            'os': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'machine': platform.machine(),
            'processor': platform.processor(),
        }
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info['local_ip'] = s.getsockname()[0]
            s.close()
        except:
            info['local_ip'] = "Unknown"
        
        try:
            mac = uuid.getnode()
            info['mac_address'] = ':'.join(['{:02x}'.format((mac >> i) & 0xff) for i in range(0, 48, 8)][::-1])
        except:
            info['mac_address'] = "Unknown"
        
        try:
            import psutil
            info['cpu_count'] = psutil.cpu_count(logical=False)
            info['cpu_cores'] = psutil.cpu_count(logical=True)
            info['cpu_freq'] = f"{psutil.cpu_freq().current:.0f} MHz" if psutil.cpu_freq() else "Unknown"
            
            ram = psutil.virtual_memory()
            info['ram_total_gb'] = round(ram.total / (1024**3), 2)
            info['ram_available_gb'] = round(ram.available / (1024**3), 2)
            
            disk = psutil.disk_usage('/')
            info['disk_total_gb'] = round(disk.total / (1024**3), 2)
            info['disk_free_gb'] = round(disk.free / (1024**3), 2)
        except ImportError:
            pass
        
        return info
    except Exception as e:
        logger.error(f"Get device info error: {e}")
        return {'error': str(e)}

def get_device_fingerprint():
    """Device fingerprint"""
    try:
        components = [
            socket.gethostname(),
            platform.machine(),
            str(uuid.getnode()),
            platform.processor()
        ]
        combined = '|'.join(components)
        fingerprint = hashlib.sha256(combined.encode()).hexdigest()
        return fingerprint
    except Exception as e:
        logger.error(f"Device fingerprint error: {e}")
        return None

# ==================== DEVICE REGISTRATION ====================
class DeviceRegistry:
    """Device registration va tracking"""
    
    def __init__(self, db):
        self.db = db
        self.devices = {}
        self.load()
    
    def load(self):
        """Registry'ni database'dan yuklash"""
        try:
            devices_list = self.db.get_all_devices()
            for device in devices_list:
                self.devices[device['device_id']] = {
                    'id': device['device_id'],
                    'info': device.get('metadata', {}),
                    'first_seen': device['first_seen'],
                    'last_seen': device['last_seen'],
                    'status': device['status'],
                    'heartbeat_count': device['heartbeat_count'],
                    'total_uptime': device['total_uptime']
                }
            logger.info(f"Loaded {len(self.devices)} devices from database")
        except Exception as e:
            logger.error(f"Load registry error: {e}")
            self.devices = {}
    
    def save(self):
        """Registry'ni database'ga saqlash"""
        pass
    
    def register(self, device_id=None, device_info=None):
        """Device'ni ro'yxatdan o'tkazish"""
        try:
            if not device_id:
                device_id = generate_device_id()
            
            if not device_info:
                device_info = get_device_info()
            
            now = datetime.now().isoformat()
            
            if device_id in self.devices:
                self.devices[device_id]['last_seen'] = now
                self.devices[device_id]['info'] = device_info
                self.devices[device_id]['heartbeat_count'] += 1
                self.db.update_device_heartbeat(device_id)
                logger.info(f"Device updated: {device_id}")
            else:
                self.devices[device_id] = {
                    'id': device_id,
                    'info': device_info,
                    'first_seen': now,
                    'last_seen': now,
                    'status': 'online',
                    'heartbeat_count': 1,
                    'total_uptime': 0
                }
                self.db.add_device(device_id, device_info)
                logger.info(f"Device registered: {device_id}")
            
            return device_id
        except Exception as e:
            logger.error(f"Register device error: {e}")
            return None
    
    def heartbeat(self, device_id):
        """Device heartbeat"""
        try:
            if device_id in self.devices:
                now = datetime.now().isoformat()
                self.devices[device_id]['last_seen'] = now
                self.devices[device_id]['status'] = 'online'
                self.devices[device_id]['heartbeat_count'] += 1
                self.db.update_device_heartbeat(device_id)
                return True
            return False
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            return False
    
    def mark_offline(self, device_id):
        """Device'ni offline deb belgilash"""
        try:
            if device_id in self.devices:
                self.devices[device_id]['status'] = 'offline'
                self.db.mark_device_offline(device_id)
                return True
            return False
        except Exception as e:
            logger.error(f"Mark offline error: {e}")
            return False
    
    def get_device(self, device_id):
        """Device ma'lumotini olish"""
        return self.devices.get(device_id)
    
    def get_all_devices(self):
        """Barcha device'lar"""
        return self.devices
    
    def get_online_devices(self):
        """Online device'lar"""
        return {k: v for k, v in self.devices.items() if v.get('status') == 'online'}
    
    def get_offline_devices(self):
        """Offline device'lar"""
        return {k: v for k, v in self.devices.items() if v.get('status') == 'offline'}
    
    def remove_device(self, device_id):
        """Device'ni o'chirish"""
        try:
            if device_id in self.devices:
                del self.devices[device_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Remove device error: {e}")
            return False
    
    def get_statistics(self):
        """Statistika"""
        try:
            total = len(self.devices)
            online = len(self.get_online_devices())
            offline = total - online
            
            return {
                'total': total,
                'online': online,
                'offline': offline,
                'online_percent': round((online / total * 100) if total > 0 else 0, 1)
            }
        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return {'error': str(e)}

# ==================== HEARTBEAT SYSTEM ====================
class HeartbeatManager:
    """Heartbeat monitoring"""
    
    def __init__(self, registry, interval=60):
        self.registry = registry
        self.interval = interval
        self.running = False
        self.thread = None
    
    def start(self):
        """Heartbeat monitoring'ni boshlash"""
        if self.running:
            return False
        
        import threading
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()
        
        logger.info("Heartbeat monitoring started")
        return True
    
    def stop(self):
        """Monitoring'ni to'xtatish"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Heartbeat monitoring stopped")
    
    def _monitor(self):
        """Monitoring loop"""
        while self.running:
            try:
                self._check_devices()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
    
    def _check_devices(self):
        """Device'larni tekshirish"""
        try:
            from datetime import timedelta
            
            now = datetime.now()
            timeout = timedelta(seconds=self.interval * 2)
            
            for device_id, device in self.registry.get_all_devices().items():
                try:
                    last_seen = datetime.fromisoformat(device['last_seen'])
                    
                    if (now - last_seen) > timeout:
                        if device['status'] == 'online':
                            logger.warning(f"Device offline: {device_id}")
                            self.registry.mark_offline(device_id)
                            
                            if hasattr(self, 'on_device_offline'):
                                self.on_device_offline(device_id)
                except:
                    continue
        except Exception as e:
            logger.error(f"Check devices error: {e}")

# ==================== HELPERS ====================
def format_device_info(device_data):
    """Device ma'lumotini formatli string'ga"""
    try:
        info = device_data.get('info', {})
        
        text = f"🖥️ **{device_data['id']}**\n\n"
        text += f"👤 User: `{info.get('username', 'Unknown')}`\n"
        text += f"💻 Host: `{info.get('hostname', 'Unknown')}`\n"
        text += f"🖥️ OS: `{info.get('os', 'Unknown')} {info.get('os_release', '')}`\n"
        text += f"🌐 IP: `{info.get('local_ip', 'Unknown')}`\n"
        text += f"📡 MAC: `{info.get('mac_address', 'Unknown')}`\n"
        
        if 'cpu_count' in info:
            text += f"\n💾 **System:**\n"
            text += f"📲 CPU: {info['cpu_cores']} cores @ {info.get('cpu_freq', 'Unknown')}\n"
            text += f"🧠 RAM: {info.get('ram_available_gb', '?')}/{info.get('ram_total_gb', '?')} GB\n"
            text += f"💿 Disk: {info.get('disk_free_gb', '?')}/{info.get('disk_total_gb', '?')} GB\n"
        
        text += f"\n⏱️ **Status:**\n"
        text += f"📊 Status: `{device_data.get('status', 'Unknown')}`\n"
        text += f"👁️ First seen: `{device_data.get('first_seen', 'Unknown')}`\n"
        text += f"💓 Last seen: `{device_data.get('last_seen', 'Unknown')}`\n"
        text += f"🔄 Heartbeats: `{device_data.get('heartbeat_count', 0)}`\n"
        
        return text
    except Exception as e:
        logger.error(f"Format device info error: {e}")
        return f"❌ Error: {str(e)}"