# tests/conftest.py - Pytest Fixtures
"""
Shared test fixtures
"""

import pytest
import tempfile
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_db():
    """Vaqtinchalik database"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    from database import Database
    db = Database(db_path)
    db.connect()
    
    yield db
    
    db.disconnect()
    try:
        os.unlink(db_path)
        # WAL files
        os.unlink(db_path + '-wal')
        os.unlink(db_path + '-shm')
    except:
        pass


@pytest.fixture
def mock_hmac_secret():
    """Test HMAC secret"""
    return "test_secret_key_12345678901234567890"


@pytest.fixture
def sample_device_info():
    """Sample device info for testing"""
    return {
        'hostname': 'TEST-PC',
        'username': 'testuser',
        'os': 'Windows',
        'os_version': '10.0.19041',
        'local_ip': '192.168.1.100',
        'mac_address': '00:11:22:33:44:55',
        'timestamp': '2026-01-15T12:00:00'
    }


@pytest.fixture
def sample_device_id():
    """Sample device ID"""
    return "DEV-TEST-PC-abc123-1234"
