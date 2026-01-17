# services/device_service.py - v3.0.5 Device Service
"""
Device management xizmati:
- Registration bilan HMAC imzolash
- Device CRUD operatsiyalari
- Status boshqaruvi
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class DeviceService:
    """Device management service - biznes logika"""
    
    def __init__(self, db, hmac_secret: str = ""):
        """
        Args:
            db: Database instance
            hmac_secret: HMAC secret for signature verification
        """
        self.db = db
        self.hmac_secret = hmac_secret
        self._cache = {}  # In-memory cache
    
    def register(self, device_id: str, device_info: Dict[str, Any], 
                 signature: str = "") -> bool:
        """
        Device'ni ro'yxatdan o'tkazish
        
        Args:
            device_id: Unique device ID
            device_info: Device metadata
            signature: HMAC signature (v3.0.5)
        
        Returns:
            True if successful
        """
        try:
            # HMAC tekshirish (agar secret mavjud bo'lsa)
            if self.hmac_secret and signature:
                from security import HMACAuth
                timestamp = device_info.get('timestamp', datetime.now().isoformat())
                if not HMACAuth.verify_message(
                    device_id, 'register', timestamp, signature, self.hmac_secret
                ):
                    logger.warning(f"Invalid signature for device: {device_id}")
                    return False
            
            # Database'ga qo'shish
            success = self.db.add_device(device_id, device_info)
            
            if success:
                # Cache yangilash
                self._cache[device_id] = {
                    'id': device_id,
                    'info': device_info,
                    'status': 'online',
                    'last_seen': datetime.now().isoformat(),
                    'heartbeat_count': 1
                }
                logger.info(f"Device registered: {device_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Register device error: {e}")
            return False
    
    def heartbeat(self, device_id: str, signature: str = "") -> bool:
        """
        Device heartbeat qabul qilish
        
        Args:
            device_id: Device ID
            signature: HMAC signature
        
        Returns:
            True if successful
        """
        try:
            # HMAC tekshirish
            if self.hmac_secret and signature:
                from security import HMACAuth
                timestamp = datetime.now().isoformat()
                if not HMACAuth.verify_message(
                    device_id, 'heartbeat', timestamp, signature, self.hmac_secret
                ):
                    logger.warning(f"Invalid heartbeat signature: {device_id}")
                    return False
            
            # Database yangilash
            success = self.db.update_device_heartbeat(device_id)
            
            if success and device_id in self._cache:
                self._cache[device_id]['last_seen'] = datetime.now().isoformat()
                self._cache[device_id]['status'] = 'online'
                self._cache[device_id]['heartbeat_count'] = \
                    self._cache[device_id].get('heartbeat_count', 0) + 1
            
            return success
            
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            return False
    
    def mark_offline(self, device_id: str) -> bool:
        """Device'ni offline qilish"""
        try:
            success = self.db.mark_device_offline(device_id)
            
            if success and device_id in self._cache:
                self._cache[device_id]['status'] = 'offline'
            
            return success
        except Exception as e:
            logger.error(f"Mark offline error: {e}")
            return False
    
    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Device ma'lumotini olish"""
        if device_id in self._cache:
            return self._cache[device_id]
        
        device = self.db.get_device(device_id)
        if device:
            self._cache[device_id] = device
        return device
    
    def get_all_devices(self) -> Dict[str, Dict[str, Any]]:
        """Barcha device'lar"""
        devices = self.db.get_all_devices()
        result = {}
        for device in devices:
            device_id = device.get('device_id')
            if device_id:
                result[device_id] = device
                self._cache[device_id] = device
        return result
    
    def get_online_devices(self) -> Dict[str, Dict[str, Any]]:
        """Faqat online device'lar"""
        all_devices = self.get_all_devices()
        return {k: v for k, v in all_devices.items() if v.get('status') == 'online'}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Device statistikasi"""
        all_devices = self.get_all_devices()
        online = len([d for d in all_devices.values() if d.get('status') == 'online'])
        total = len(all_devices)
        
        return {
            'total': total,
            'online': online,
            'offline': total - online,
            'online_percent': round((online / total * 100) if total > 0 else 0, 1)
        }
    
    def refresh_cache(self):
        """Cache'ni yangilash"""
        self._cache.clear()
        self.get_all_devices()
