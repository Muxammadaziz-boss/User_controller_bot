# url_player.py - FIXED ASYNC VERSION
import asyncio
import logging
import webbrowser
import subprocess

try:
    import pyautogui
except ImportError:
    pyautogui = None

logger = logging.getLogger(__name__)

async def open_url_fullscreen(url):
    """
    URL ni to'liq ekran rejimida ochish (Non-blocking)
    """
    try:
        # Brauzerni ochish (Blocking emas)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, webbrowser.open, url)
        logger.info(f"URL opened: {url}")
        
        # Async kutish (Botni qotirmaydi)
        await asyncio.sleep(3)
        
        if not pyautogui:
            logger.warning("PyAutoGUI not available")
            return True
        
        try:
            # F11 bosish (Fullscreen)
            # PyAutoGUI main thread'da ishlashi kerak, lekin tez bo'lgani uchun OK
            pyautogui.press('f11')
            logger.info("Fullscreen activated (F11)")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"F11 error: {e}")
        
        try:
            # Video saytlar uchun Space bosish (Play)
            if any(site in url.lower() for site in ['youtube', 'vimeo', 'dailymotion', 'video']):
                await asyncio.sleep(1)
                pyautogui.press('space')
                logger.info("Video played (Space)")
        except Exception as e:
            logger.error(f"Play error: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"URL open error: {e}")
        return False

async def open_url_in_chrome_fullscreen(url):
    """
    Chrome Kiosk rejimida ochish (Async Subprocess)
    """
    try:
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        
        chrome_path = None
        
        # Chrome qidirish (Async)
        try:
            proc = await asyncio.create_subprocess_exec(
                "where", "chrome.exe",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            await proc.communicate()
            if proc.returncode == 0:
                # Agar path'da bo'lsa
                chrome_path = "chrome.exe"
        except:
            pass

        if not chrome_path:
            # Path'da yo'q bo'lsa, papkalarni tekshirish
            for path in chrome_paths:
                import os
                if os.path.exists(path):
                    chrome_path = path
                    break
        
        if not chrome_path:
            logger.warning("Chrome not found, using default browser")
            return await open_url_fullscreen(url)
        
        # Chrome ni Kiosk rejimida ochish
        logger.info(f"Opening Chrome Kiosk: {url}")
        creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        
        subprocess.Popen(
            [
                chrome_path,
                "--kiosk",
                "--autoplay-policy=no-user-gesture-required",
                "--new-window",
                url
            ],
            creationflags=creationflags,
            shell=False
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Chrome kiosk error: {e}")
        return await open_url_fullscreen(url)

async def play_url(url):
    """Main entry point"""
    return await open_url_in_chrome_fullscreen(url)