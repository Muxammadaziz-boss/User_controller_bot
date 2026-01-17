# tests/test_security.py - Security Module Tests
"""
HMAC, Rate Limiter, Checksum tests
"""

import pytest
import time
import tempfile
import os


class TestHMACAuth:
    """HMAC authentication tests"""
    
    def test_sign_creates_signature(self):
        """Imzo yaratilishi kerak"""
        from security import HMACAuth
        
        signature = HMACAuth.sign("test_data", "secret_key")
        
        assert signature is not None
        assert len(signature) == 64  # SHA256 hex length
    
    def test_verify_valid_signature(self):
        """To'g'ri imzo tasdiqlanishi kerak"""
        from security import HMACAuth
        
        data = "test_data"
        secret = "secret_key"
        signature = HMACAuth.sign(data, secret)
        
        assert HMACAuth.verify(data, signature, secret) is True
    
    def test_verify_invalid_signature(self):
        """Noto'g'ri imzo rad etilishi kerak"""
        from security import HMACAuth
        
        assert HMACAuth.verify("data", "wrong_signature", "secret") is False
    
    def test_verify_empty_secret(self):
        """Bo'sh secret False qaytarishi kerak"""
        from security import HMACAuth
        
        assert HMACAuth.verify("data", "signature", "") is False
    
    def test_sign_message_format(self):
        """Message imzolash formati"""
        from security import HMACAuth
        
        signature = HMACAuth.sign_message(
            device_id="DEV-123",
            action="register",
            timestamp="2026-01-15T12:00:00",
            secret="secret"
        )
        
        assert signature is not None
        assert len(signature) == 64


class TestRateLimiter:
    """Rate limiter tests"""
    
    def test_allows_within_limit(self):
        """Limit ichida ruxsat berilishi kerak"""
        from security import RateLimiter
        
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        user_id = 12345
        
        for _ in range(5):
            assert limiter.is_allowed(user_id) is True
    
    def test_blocks_over_limit(self):
        """Limitdan oshganda bloklanishi kerak"""
        from security import RateLimiter
        
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        user_id = 12345
        
        for _ in range(3):
            limiter.is_allowed(user_id)
        
        assert limiter.is_allowed(user_id) is False
    
    def test_different_users_independent(self):
        """Har bir user alohida hisoblanishi kerak"""
        from security import RateLimiter
        
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        limiter.is_allowed(111)
        limiter.is_allowed(111)
        assert limiter.is_allowed(111) is False
        
        # Boshqa user hali limit ichida
        assert limiter.is_allowed(222) is True
    
    def test_get_remaining(self):
        """Qolgan so'rovlar soni"""
        from security import RateLimiter
        
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        user_id = 12345
        
        assert limiter.get_remaining(user_id) == 5
        limiter.is_allowed(user_id)
        assert limiter.get_remaining(user_id) == 4


class TestChecksumVerification:
    """Checksum verification tests"""
    
    def test_calculate_file_hash(self):
        """Fayl hash hisoblash"""
        from security import calculate_file_hash
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name
        
        try:
            hash_result = calculate_file_hash(temp_path)
            assert hash_result is not None
            assert len(hash_result) == 64  # SHA256
        finally:
            os.unlink(temp_path)
    
    def test_verify_correct_checksum(self):
        """To'g'ri checksum tasdiqlash"""
        from security import calculate_file_hash, verify_file_checksum
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content for checksum")
            temp_path = f.name
        
        try:
            expected = calculate_file_hash(temp_path)
            assert verify_file_checksum(temp_path, expected) is True
        finally:
            os.unlink(temp_path)
    
    def test_verify_wrong_checksum(self):
        """Noto'g'ri checksum rad etilishi kerak"""
        from security import verify_file_checksum
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name
        
        try:
            assert verify_file_checksum(temp_path, "wrong_hash") is False
        finally:
            os.unlink(temp_path)
