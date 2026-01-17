# tests/test_device_service.py - Device Service Tests
"""
Device service unit tests
"""

import pytest


class TestDeviceService:
    """Device service tests"""
    
    def test_create_device_service(self, temp_db, mock_hmac_secret):
        """Service yaratish"""
        from services import DeviceService
        
        service = DeviceService(temp_db, hmac_secret=mock_hmac_secret)
        
        assert service is not None
        assert service.hmac_secret == mock_hmac_secret
    
    def test_register_device(self, temp_db, mock_hmac_secret, sample_device_info, sample_device_id):
        """Device ro'yxatdan o'tkazish"""
        from services import DeviceService
        
        service = DeviceService(temp_db, hmac_secret="")
        
        result = service.register(sample_device_id, sample_device_info)
        
        assert result is True
    
    def test_register_updates_cache(self, temp_db, sample_device_info, sample_device_id):
        """Register cache'ni yangilashi kerak"""
        from services import DeviceService
        
        service = DeviceService(temp_db)
        service.register(sample_device_id, sample_device_info)
        
        assert sample_device_id in service._cache
    
    def test_heartbeat(self, temp_db, sample_device_info, sample_device_id):
        """Heartbeat qabul qilish"""
        from services import DeviceService
        
        service = DeviceService(temp_db)
        service.register(sample_device_id, sample_device_info)
        
        result = service.heartbeat(sample_device_id)
        
        assert result is True
    
    def test_mark_offline(self, temp_db, sample_device_info, sample_device_id):
        """Device'ni offline qilish"""
        from services import DeviceService
        
        service = DeviceService(temp_db)
        service.register(sample_device_id, sample_device_info)
        
        result = service.mark_offline(sample_device_id)
        
        assert result is True
        
        device = service.get_device(sample_device_id)
        assert device['status'] == 'offline'
    
    def test_get_statistics(self, temp_db, sample_device_info):
        """Statistika olish"""
        from services import DeviceService
        
        service = DeviceService(temp_db)
        service.register("DEV-1", sample_device_info)
        service.register("DEV-2", sample_device_info)
        
        stats = service.get_statistics()
        
        assert stats['total'] == 2
        assert stats['online'] == 2
        assert stats['offline'] == 0
    
    def test_refresh_cache(self, temp_db, sample_device_info):
        """Cache yangilash"""
        from services import DeviceService
        
        service = DeviceService(temp_db)
        service.register("DEV-1", sample_device_info)
        
        service._cache.clear()
        assert len(service._cache) == 0
        
        service.refresh_cache()
        
        assert len(service._cache) == 1
