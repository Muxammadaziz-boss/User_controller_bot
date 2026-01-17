# tests/test_database.py - Database Tests
"""
Database unit tests with mocked SQLite
"""

import pytest


class TestDatabaseConnection:
    """Database connection tests"""
    
    def test_connect_creates_tables(self, temp_db):
        """Connect tablelar yaratishi kerak"""
        assert temp_db.conn is not None
        
        # Check tables exist
        temp_db.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in temp_db.cursor.fetchall()]
        
        assert 'devices' in tables
        assert 'activity_logs' in tables
        assert 'commands_history' in tables
        assert 'schema_version' in tables
    
    def test_wal_mode_enabled(self, temp_db):
        """WAL mode yoqilgan bo'lishi kerak"""
        temp_db.cursor.execute("PRAGMA journal_mode")
        result = temp_db.cursor.fetchone()[0]
        assert result.lower() == 'wal'


class TestDeviceOperations:
    """Device CRUD tests"""
    
    def test_add_device(self, temp_db, sample_device_info, sample_device_id):
        """Device qo'shish"""
        result = temp_db.add_device(sample_device_id, sample_device_info)
        assert result is True
    
    def test_get_device(self, temp_db, sample_device_info, sample_device_id):
        """Device olish"""
        temp_db.add_device(sample_device_id, sample_device_info)
        
        device = temp_db.get_device(sample_device_id)
        
        assert device is not None
        assert device['device_id'] == sample_device_id
        assert device['hostname'] == sample_device_info['hostname']
    
    def test_get_nonexistent_device(self, temp_db):
        """Mavjud bo'lmagan device None qaytarishi kerak"""
        device = temp_db.get_device("NONEXISTENT-ID")
        assert device is None
    
    def test_update_device_heartbeat(self, temp_db, sample_device_info, sample_device_id):
        """Heartbeat yangilash"""
        temp_db.add_device(sample_device_id, sample_device_info)
        
        result = temp_db.update_device_heartbeat(sample_device_id)
        
        assert result is True
        
        device = temp_db.get_device(sample_device_id)
        assert device['status'] == 'online'
    
    def test_mark_device_offline(self, temp_db, sample_device_info, sample_device_id):
        """Device offline qilish"""
        temp_db.add_device(sample_device_id, sample_device_info)
        
        result = temp_db.mark_device_offline(sample_device_id)
        
        assert result is True
        
        device = temp_db.get_device(sample_device_id)
        assert device['status'] == 'offline'
    
    def test_get_all_devices(self, temp_db, sample_device_info):
        """Barcha device'larni olish"""
        temp_db.add_device("DEV-1", sample_device_info)
        temp_db.add_device("DEV-2", sample_device_info)
        
        devices = temp_db.get_all_devices()
        
        assert len(devices) == 2


class TestActivityLogs:
    """Activity log tests"""
    
    def test_log_activity(self, temp_db, sample_device_id):
        """Activity log qo'shish"""
        result = temp_db.log_activity(
            sample_device_id, 
            "screenshot", 
            "Screenshot taken", 
            "success"
        )
        assert result is True
    
    def test_get_activity_logs(self, temp_db, sample_device_id):
        """Activity loglarni olish"""
        temp_db.log_activity(sample_device_id, "test_action", "details", "success")
        
        logs = temp_db.get_activity_logs(device_id=sample_device_id)
        
        assert len(logs) >= 1
        assert logs[0]['action'] == "test_action"


class TestDashboardStats:
    """Dashboard statistics tests"""
    
    def test_get_dashboard_stats_empty(self, temp_db):
        """Bo'sh database stats"""
        stats = temp_db.get_dashboard_stats()
        
        assert stats['total_devices'] == 0
        assert stats['online_devices'] == 0
    
    def test_get_dashboard_stats_with_data(self, temp_db, sample_device_info):
        """Ma'lumotli database stats"""
        temp_db.add_device("DEV-1", sample_device_info)
        temp_db.add_device("DEV-2", sample_device_info)
        
        stats = temp_db.get_dashboard_stats()
        
        assert stats['total_devices'] == 2
        assert stats['online_devices'] == 2
