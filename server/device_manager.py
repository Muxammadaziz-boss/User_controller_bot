# device_manager.py - ASYNC DEVICE MANAGEMENT (v3.0.5 Production)
"""
🚀 Production-Grade Async Device Manager
- Async database operations
- Async heartbeat monitoring
- In-memory caching with DB sync
"""

import uuid
import socket
import getpass
import platform
import hashlib
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable

logger = logging.getLogger(__name__)


# ==================== DEVICE ID GENERATION ====================
def generate_device_id() -> str:
    """Generate unique device ID"""
    try:
        hostname = socket.gethostname()[:15]
        mac = uuid.getnode()
        mac_hex = '{:012x}'.format(mac)
        mac_hash = hashlib.md5(mac_hex.encode()).hexdigest()[:6]
        random_suffix = hashlib.md5(str(time.time()).encode()).hexdigest()[:4]
        return f"DEV-{hostname}-{mac_hash}-{random_suffix}"
    except Exception as e:
        logger.error(f"Generate device ID error: {e}")
        return f"DEV-UNKNOWN-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"


def get_device_info() -> Dict[str, Any]:
    """Get comprehensive device information"""
    try:
        info = {
            'hostname': socket.gethostname(),
            'username': getpass.getuser(),
            'os': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'machine': platform.machine(),
            'processor': platform.processor()[:50] if platform.processor() else 'Unknown',
        }
        
        # Local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info['local_ip'] = s.getsockname()[0]
            s.close()
        except:
            info['local_ip'] = "Unknown"
        
        # MAC address
        try:
            mac = uuid.getnode()
            info['mac_address'] = ':'.join(['{:02x}'.format((mac >> i) & 0xff) 
                                            for i in range(0, 48, 8)][::-1])
        except:
            info['mac_address'] = "Unknown"
        
        # System resources (if psutil available)
        try:
            import psutil
            info['cpu_count'] = psutil.cpu_count(logical=False)
            info['cpu_cores'] = psutil.cpu_count(logical=True)
            freq = psutil.cpu_freq()
            info['cpu_freq'] = f"{freq.current:.0f} MHz" if freq else "Unknown"
            
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


def get_device_fingerprint() -> Optional[str]:
    """Generate unique device fingerprint"""
    try:
        components = [
            socket.gethostname(),
            platform.machine(),
            str(uuid.getnode()),
            platform.processor() or ''
        ]
        combined = '|'.join(components)
        return hashlib.sha256(combined.encode()).hexdigest()
    except Exception as e:
        logger.error(f"Device fingerprint error: {e}")
        return None


# ==================== ASYNC DEVICE REGISTRY ====================
class AsyncDeviceRegistry:
    """
    Async Device Registry with caching
    All database operations are non-blocking
    """
    
    def __init__(self, db):
        """
        Args:
            db: AsyncDatabase instance
        """
        self.db = db
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._loaded = False
    
    async def load(self):
        """Load devices from database into cache"""
        try:
            devices_list = await self.db.get_all_devices()
            
            for device in devices_list:
                device_id = device['device_id']
                self._cache[device_id] = {
                    'id': device_id,
                    'info': device.get('metadata', device.get('info', {})),
                    'first_seen': device['first_seen'],
                    'last_seen': device['last_seen'],
                    'status': device['status'],
                    'heartbeat_count': device['heartbeat_count'],
                    'total_uptime': device.get('total_uptime', 0)
                }
            
            self._loaded = True
            logger.info(f"Loaded {len(self._cache)} devices from database")
            
        except Exception as e:
            logger.error(f"Load registry error: {e}")
            self._cache = {}
    
    async def register(self, device_id: str = None, 
                       device_info: Dict[str, Any] = None) -> Optional[str]:
        """Register or update device - async"""
        try:
            if not device_id:
                device_id = generate_device_id()
            
            if not device_info:
                device_info = get_device_info()
            
            now = datetime.now().isoformat()
            
            # Database upsert
            await self.db.add_device(device_id, device_info)
            
            # Update cache
            if device_id in self._cache:
                self._cache[device_id]['last_seen'] = now
                self._cache[device_id]['info'] = device_info
                self._cache[device_id]['heartbeat_count'] += 1
                self._cache[device_id]['status'] = 'online'
                logger.info(f"Device updated: {device_id}")
            else:
                self._cache[device_id] = {
                    'id': device_id,
                    'info': device_info,
                    'first_seen': now,
                    'last_seen': now,
                    'status': 'online',
                    'heartbeat_count': 1,
                    'total_uptime': 0
                }
                logger.info(f"Device registered: {device_id}")
            
            return device_id
            
        except Exception as e:
            logger.error(f"Register device error: {e}")
            return None
    
    async def heartbeat(self, device_id: str) -> bool:
        """Process device heartbeat - async"""
        try:
            # Update database
            success = await self.db.update_heartbeat(device_id)
            
            if success and device_id in self._cache:
                now = datetime.now().isoformat()
                self._cache[device_id]['last_seen'] = now
                self._cache[device_id]['status'] = 'online'
                self._cache[device_id]['heartbeat_count'] += 1
                return True
            elif not success:
                # Device not in DB - needs re-registration
                logger.warning(f"Heartbeat for unknown device: {device_id}")
                return False
            
            return success
            
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            return False
    
    async def mark_offline(self, device_id: str) -> bool:
        """Mark device as offline - async"""
        try:
            await self.db.mark_offline(device_id)
            
            if device_id in self._cache:
                self._cache[device_id]['status'] = 'offline'
            
            return True
            
        except Exception as e:
            logger.error(f"Mark offline error: {e}")
            return False
    
    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device from cache (sync - fast)"""
        return self._cache.get(device_id)
    
    def get_all_devices(self) -> Dict[str, Dict[str, Any]]:
        """Get all devices from cache (sync - fast)"""
        return self._cache.copy()
    
    def get_online_devices(self) -> Dict[str, Dict[str, Any]]:
        """Get online devices from cache"""
        return {k: v for k, v in self._cache.items() 
                if v.get('status') == 'online'}
    
    def get_offline_devices(self) -> Dict[str, Dict[str, Any]]:
        """Get offline devices from cache"""
        return {k: v for k, v in self._cache.items() 
                if v.get('status') == 'offline'}
    
    async def remove_device(self, device_id: str) -> bool:
        """Remove device"""
        try:
            if device_id in self._cache:
                del self._cache[device_id]
            return True
        except Exception as e:
            logger.error(f"Remove device error: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get device statistics (sync - from cache)"""
        try:
            total = len(self._cache)
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
            return {'total': 0, 'online': 0, 'offline': 0, 'online_percent': 0}
    
    async def refresh(self):
        """Refresh cache from database"""
        await self.load()


# ==================== ASYNC HEARTBEAT MANAGER ====================
class AsyncHeartbeatManager:
    """
    Async Heartbeat Monitoring
    Uses asyncio instead of threading
    """
    
    def __init__(self, registry: AsyncDeviceRegistry, 
                 interval: int = 60, timeout: int = 120):
        """
        Args:
            registry: AsyncDeviceRegistry instance
            interval: Check interval in seconds
            timeout: Offline threshold in seconds
        """
        self.registry = registry
        self.interval = interval
        self.timeout = timeout
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.on_device_offline: Optional[Callable] = None
        self.on_device_online: Optional[Callable] = None
    
    def start(self):
        """Start heartbeat monitoring"""
        if self.running:
            logger.warning("Heartbeat manager already running")
            return False
        
        self.running = True
        self._task = asyncio.create_task(self._monitor())
        logger.info(f"Heartbeat manager started (interval={self.interval}s, timeout={self.timeout}s)")
        return True
    
    def stop(self):
        """Stop heartbeat monitoring"""
        self.running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Heartbeat manager stopped")
    
    async def _monitor(self):
        """Async monitoring loop"""
        while self.running:
            try:
                await self._check_devices()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                await asyncio.sleep(5)
    
    async def _check_devices(self):
        """Check all devices for timeout"""
        try:
            now = datetime.now()
            timeout_delta = timedelta(seconds=self.timeout)
            
            devices = self.registry.get_all_devices()
            
            for device_id, device in devices.items():
                try:
                    last_seen_str = device.get('last_seen', '')
                    if not last_seen_str:
                        continue
                    
                    # Parse last_seen timestamp
                    try:
                        last_seen = datetime.fromisoformat(
                            last_seen_str.replace('Z', '+00:00')
                        )
                        if last_seen.tzinfo:
                            last_seen = last_seen.replace(tzinfo=None)
                    except:
                        continue
                    
                    current_status = device.get('status', 'offline')
                    
                    # Check if timed out
                    if (now - last_seen) > timeout_delta:
                        if current_status == 'online':
                            logger.warning(f"Device timeout: {device_id}")
                            await self.registry.mark_offline(device_id)
                            
                            # Fire callback
                            if self.on_device_offline:
                                try:
                                    if asyncio.iscoroutinefunction(self.on_device_offline):
                                        await self.on_device_offline(device_id)
                                    else:
                                        self.on_device_offline(device_id)
                                except Exception as cb_err:
                                    logger.error(f"Offline callback error: {cb_err}")
                    
                except Exception as dev_err:
                    logger.debug(f"Check device error: {device_id} - {dev_err}")
                    
        except Exception as e:
            logger.error(f"Check devices error: {e}")


# ==================== HELPERS ====================
def format_device_info(device_data: Dict[str, Any]) -> str:
    """Format device info for Telegram message"""
    try:
        info = device_data.get('info', {})
        device_id = device_data.get('id', device_data.get('device_id', 'Unknown'))
        
        text = f"🖥️ **{device_id}**\n\n"
        text += f"👤 User: `{info.get('username', 'Unknown')}`\n"
        text += f"💻 Host: `{info.get('hostname', 'Unknown')}`\n"
        text += f"🖥️ OS: `{info.get('os', 'Unknown')} {info.get('os_release', '')}`\n"
        text += f"🌐 IP: `{info.get('local_ip', 'Unknown')}`\n"
        text += f"📡 MAC: `{info.get('mac_address', 'Unknown')}`\n"
        
        if 'cpu_count' in info:
            text += f"\n💾 **System:**\n"
            text += f"📲 CPU: {info.get('cpu_cores', '?')} cores @ {info.get('cpu_freq', 'Unknown')}\n"
            text += f"🧠 RAM: {info.get('ram_available_gb', '?')}/{info.get('ram_total_gb', '?')} GB\n"
            text += f"💿 Disk: {info.get('disk_free_gb', '?')}/{info.get('disk_total_gb', '?')} GB\n"
        
        text += f"\n⏱️ **Status:**\n"
        text += f"📊 Status: `{device_data.get('status', 'Unknown')}`\n"
        text += f"👁️ First: `{device_data.get('first_seen', 'Unknown')[:19]}`\n"
        text += f"💓 Last: `{device_data.get('last_seen', 'Unknown')[:19]}`\n"
        text += f"🔄 Heartbeats: `{device_data.get('heartbeat_count', 0)}`\n"
        
        return text
        
    except Exception as e:
        logger.error(f"Format device info error: {e}")
        return f"❌ Error: {str(e)}"


# ==================== BACKWARD COMPATIBILITY ====================
DeviceRegistry = AsyncDeviceRegistry
HeartbeatManager = AsyncHeartbeatManager