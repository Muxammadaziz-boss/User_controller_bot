# security.py - v3.0.5 Security Module
"""
Xavfsizlik moduli:
- HMAC-SHA256 imzolash (device auth)
- Rate limiting
- Checksum verification
- Admin authentication
"""

import hmac
import hashlib
import time
import logging
from functools import wraps
from collections import defaultdict
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)


# ==================== HMAC AUTHENTICATION ====================
class HMACAuth:
    """
    Device registration va heartbeat xabarlari uchun HMAC-SHA256 imzolash.
    Server va client o'rtasida shared secret orqali validate qiladi.
    """
    
    @staticmethod
    def sign(data: str, secret: str) -> str:
        """
        Ma'lumotni imzolash
        
        Args:
            data: Imzolanadigan string (JSON yoki oddiy text)
            secret: Shared secret key
        
        Returns:
            HMAC-SHA256 signature (hex)
        """
        if not secret:
            logger.warning("HMAC secret bo'sh - imzo yaratilmadi")
            return ""
        return hmac.new(
            secret.encode('utf-8'), 
            data.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verify(data: str, signature: str, secret: str) -> bool:
        """
        Imzoni tekshirish
        
        Args:
            data: Original string
            signature: Tekshiriladigan imzo
            secret: Shared secret key
        
        Returns:
            True agar imzo to'g'ri bo'lsa
        """
        if not secret or not signature:
            return False
        expected = HMACAuth.sign(data, secret)
        return hmac.compare_digest(expected, signature)
    
    @staticmethod
    def sign_message(device_id: str, action: str, timestamp: str, secret: str) -> str:
        """
        Device xabari uchun standart imzo yaratish
        
        Args:
            device_id: Qurilma ID
            action: Harakat turi (register, heartbeat, command)
            timestamp: ISO formatdagi vaqt
            secret: HMAC secret
        
        Returns:
            Signature
        """
        message = f"{device_id}|{action}|{timestamp}"
        return HMACAuth.sign(message, secret)
    
    @staticmethod
    def verify_message(device_id: str, action: str, timestamp: str, 
                       signature: str, secret: str, max_age_seconds: int = 300) -> bool:
        """
        Device xabarini tekshirish (replay attack himoyasi bilan)
        
        Args:
            device_id: Qurilma ID
            action: Harakat turi
            timestamp: ISO formatdagi vaqt
            signature: Tekshiriladigan imzo
            secret: HMAC secret
            max_age_seconds: Maksimal xabar yoshi (default 5 daqiqa)
        
        Returns:
            True agar xabar to'g'ri va yangi bo'lsa
        """
        # Imzoni tekshirish
        message = f"{device_id}|{action}|{timestamp}"
        if not HMACAuth.verify(message, signature, secret):
            logger.warning(f"Noto'g'ri imzo: device={device_id}, action={action}")
            return False
        
        # Vaqtni tekshirish (replay attack himoyasi)
        try:
            from datetime import datetime
            msg_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.now(msg_time.tzinfo) if msg_time.tzinfo else datetime.now()
            age = abs((now - msg_time).total_seconds())
            
            if age > max_age_seconds:
                logger.warning(f"Eskirgan xabar: device={device_id}, age={age}s")
                return False
        except Exception as e:
            logger.error(f"Vaqt tekshirish xatosi: {e}")
            return False
        
        return True


# ==================== RATE LIMITING ====================
class RateLimiter:
    """
    Admin endpoint'lar uchun rate limiting.
    Brute-force va spam hujumlardan himoya.
    """
    
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        """
        Args:
            max_requests: Window ichida maksimal so'rovlar soni
            window_seconds: Sliding window davomiyligi
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)  # user_id -> [timestamps]
        self._cleanup_counter = 0
    
    def is_allowed(self, user_id: int) -> bool:
        """
        So'rov ruxsat berilganligini tekshirish
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            True agar ruxsat berilsa
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # Eski so'rovlarni tozalash
        self.requests[user_id] = [
            t for t in self.requests[user_id] 
            if t > window_start
        ]
        
        # Limitni tekshirish
        if len(self.requests[user_id]) >= self.max_requests:
            logger.warning(f"Rate limit oshdi: user={user_id}")
            return False
        
        # Yangi so'rovni qo'shish
        self.requests[user_id].append(now)
        
        # Periodic cleanup
        self._cleanup_counter += 1
        if self._cleanup_counter >= 100:
            self._cleanup()
            self._cleanup_counter = 0
        
        return True
    
    def _cleanup(self):
        """Eskirgan yozuvlarni tozalash"""
        now = time.time()
        window_start = now - self.window_seconds
        
        empty_users = []
        for user_id, timestamps in self.requests.items():
            self.requests[user_id] = [t for t in timestamps if t > window_start]
            if not self.requests[user_id]:
                empty_users.append(user_id)
        
        for user_id in empty_users:
            del self.requests[user_id]
    
    def get_remaining(self, user_id: int) -> int:
        """Qolgan so'rovlar sonini olish"""
        now = time.time()
        window_start = now - self.window_seconds
        
        recent = [t for t in self.requests.get(user_id, []) if t > window_start]
        return max(0, self.max_requests - len(recent))
    
    def get_reset_time(self, user_id: int) -> float:
        """Limit reset bo'lish vaqtini olish (sekundlarda)"""
        if user_id not in self.requests or not self.requests[user_id]:
            return 0
        
        oldest = min(self.requests[user_id])
        reset_at = oldest + self.window_seconds
        return max(0, reset_at - time.time())


def rate_limit(limiter: RateLimiter):
    """
    Rate limiting decorator for async handlers
    
    Usage:
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        @rate_limit(limiter)
        async def my_handler(event):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(event, *args, **kwargs):
            user_id = event.sender_id
            
            if not limiter.is_allowed(user_id):
                reset_time = limiter.get_reset_time(user_id)
                await event.answer(
                    f"⚠️ Juda ko'p so'rov! {reset_time:.0f}s kutib turing.",
                    alert=True
                )
                return None
            
            return await func(event, *args, **kwargs)
        return wrapper
    return decorator


# ==================== CHECKSUM VERIFICATION ====================
def calculate_file_hash(filepath: str, algorithm: str = 'sha256') -> Optional[str]:
    """
    Fayl hashini hisoblash
    
    Args:
        filepath: Fayl yo'li
        algorithm: Hash algoritmi (sha256, md5, sha1)
    
    Returns:
        Hash string yoki None
    """
    try:
        hash_func = getattr(hashlib, algorithm)()
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Hash hisoblash xatosi: {filepath} - {e}")
        return None


def verify_file_checksum(filepath: str, expected_hash: str, 
                          algorithm: str = 'sha256') -> bool:
    """
    Fayl checksumini tekshirish
    
    Args:
        filepath: Fayl yo'li
        expected_hash: Kutilayotgan hash
        algorithm: Hash algoritmi
    
    Returns:
        True agar hash mos kelsa
    """
    actual_hash = calculate_file_hash(filepath, algorithm)
    
    if not actual_hash:
        return False
    
    if not hmac.compare_digest(actual_hash.lower(), expected_hash.lower()):
        logger.error(f"Hash mos kelmadi: {filepath}")
        logger.error(f"  Kutilgan: {expected_hash}")
        logger.error(f"  Haqiqiy:  {actual_hash}")
        return False
    
    logger.info(f"Hash tasdiqlandi: {filepath}")
    return True


# ==================== ADMIN VERIFICATION ====================
def admin_only(admin_id: int):
    """
    Faqat admin uchun decorator
    
    Usage:
        @admin_only(ADMIN_ID)
        async def admin_handler(event):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(event, *args, **kwargs):
            if event.sender_id != admin_id:
                logger.warning(f"Ruxsatsiz kirish urinishi: {event.sender_id}")
                return None
            return await func(event, *args, **kwargs)
        return wrapper
    return decorator


# ==================== GLOBAL INSTANCES ====================
# Default rate limiter (30 requests per minute)
default_limiter = RateLimiter(max_requests=30, window_seconds=60)

# Strict rate limiter for sensitive operations (5 per minute)
strict_limiter = RateLimiter(max_requests=5, window_seconds=60)


# ==================== EXPORTS ====================
__all__ = [
    'HMACAuth',
    'RateLimiter',
    'rate_limit',
    'calculate_file_hash',
    'verify_file_checksum',
    'admin_only',
    'default_limiter',
    'strict_limiter',
]
