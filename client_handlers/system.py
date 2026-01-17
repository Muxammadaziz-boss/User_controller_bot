# client_handlers/system.py - v3.0.5 SYSTEM HANDLERS
"""
💻 System Control Handlers (Non-Blocking)
- Shell commands (CMD/PowerShell)
- System info
- Process management
- Power control
"""

import asyncio
import logging
import time
from typing import Optional

from telethon import events
from telethon.tl.custom import Button

logger = logging.getLogger(__name__)


def register_system_handlers(client, ctx):
    """Register system-related handlers"""
    
    admin_id = ctx.admin_id
    
    # ==================== SHELL COMMANDS ====================
    @client.on(events.CallbackQuery(data=b"cmd_prompt"))
    async def cmd_prompt_handler(event):
        """Prompt for CMD command"""
        if event.sender_id != admin_id:
            return
        
        ctx.user_state['waiting_for'] = 'cmd_command'
        
        await event.edit(
            "⚡ **CMD Buyruq Kiritish**\n\n"
            "Buyruqni yuboring:\n"
            "Masalan: `dir`, `ipconfig`, `tasklist`",
            buttons=[[Button.inline("❌ Bekor", b"back_to_main")]]
        )
    
    @client.on(events.CallbackQuery(data=b"ps_prompt"))
    async def ps_prompt_handler(event):
        """Prompt for PowerShell command"""
        if event.sender_id != admin_id:
            return
        
        ctx.user_state['waiting_for'] = 'ps_command'
        
        await event.edit(
            "🔷 **PowerShell Buyruq Kiritish**\n\n"
            "Buyruqni yuboring:\n"
            "Masalan: `Get-Process`, `Get-Service`",
            buttons=[[Button.inline("❌ Bekor", b"back_to_main")]]
        )
    
    # Handle text input for commands
    @client.on(events.NewMessage(chats=admin_id))
    async def command_input_handler(event):
        """Handle command text input"""
        if event.out:
            return
        
        waiting_for = ctx.user_state.get('waiting_for')
        
        if waiting_for == 'cmd_command':
            ctx.user_state['waiting_for'] = None
            
            cmd = event.raw_text.strip()
            await event.respond(f"⚡ CMD: `{cmd}`\n⏳ Bajarilmoqda...")
            
            from utils import run_command_async
            returncode, stdout, stderr = await run_command_async(cmd)
            
            output = stdout or stderr or "(bo'sh natija)"
            if len(output) > 3500:
                output = output[:3500] + "\n...(qisqartirildi)"
            
            await event.respond(
                f"⚡ **CMD Natijasi**\n"
                f"📋 Buyruq: `{cmd}`\n"
                f"📤 Exit code: `{returncode}`\n\n"
                f"```\n{output}\n```"
            )
        
        elif waiting_for == 'ps_command':
            ctx.user_state['waiting_for'] = None
            
            cmd = f"powershell -Command \"{event.raw_text.strip()}\""
            await event.respond(f"🔷 PowerShell: ⏳ Bajarilmoqda...")
            
            from utils import run_command_async
            returncode, stdout, stderr = await run_command_async(cmd, timeout=60)
            
            output = stdout or stderr or "(bo'sh natija)"
            if len(output) > 3500:
                output = output[:3500] + "\n...(qisqartirildi)"
            
            await event.respond(
                f"🔷 **PowerShell Natijasi**\n\n"
                f"```\n{output}\n```"
            )
    
    # ==================== SYSTEM INFO ====================
    @client.on(events.CallbackQuery(data=b"system_info"))
    async def system_info_handler(event):
        """Show system information"""
        if event.sender_id != admin_id:
            return
        
        await event.answer("💻 Ma'lumot olinmoqda...")
        
        from utils import get_system_info
        info = await get_system_info()
        
        if 'error' in info:
            await client.send_message(event.chat_id, f"❌ {info['error']}")
            return
        
        message = (
            f"💻 **Tizim Ma'lumoti**\n\n"
            f"🖥 **Asosiy:**\n"
            f"👤 User: `{info.get('username', 'N/A')}`\n"
            f"💻 Host: `{info.get('hostname', 'N/A')}`\n"
            f"🖥 OS: `{info.get('os', 'N/A')}`\n"
            f"🌐 IP: `{info.get('local_ip', 'N/A')}`\n\n"
        )
        
        if 'cpu_percent' in info:
            message += (
                f"📊 **Resurslar:**\n"
                f"🔲 CPU: `{info['cpu_cores']} cores @ {info['cpu_percent']}%`\n"
                f"🧠 RAM: `{info['ram_used']} / {info['ram_total']} ({info['ram_percent']}%)`\n"
                f"💿 Disk: `{info['disk_free']} free / {info['disk_total']} ({info['disk_percent']}%)`\n\n"
                f"🕐 Boot: `{info.get('boot_time', 'N/A')}`"
            )
        
        await client.send_message(
            event.chat_id, message,
            buttons=[[Button.inline("🔙 Ortga", b"back_to_main")]]
        )
    
    @client.on(events.CallbackQuery(data=b"broadcast_sysinfo"))
    async def broadcast_sysinfo_handler(event):
        """Broadcast system info"""
        if event.sender_id != admin_id:
            return
        
        event._chat_id = admin_id
        await system_info_handler(event)
    
    # ==================== PROCESS MANAGEMENT ====================
    @client.on(events.CallbackQuery(data=b"process_list"))
    async def process_list_handler(event):
        """Show top processes"""
        if event.sender_id != admin_id:
            return
        
        await event.answer("📋 Jarayonlar...")
        
        from utils import get_processes
        procs = await get_processes(top=15)
        
        if not procs or 'error' in procs[0]:
            await client.send_message(
                event.chat_id,
                "❌ Jarayonlarni olishda xatolik"
            )
            return
        
        message = "📋 **Top Jarayonlar (CPU)**\n\n"
        for p in procs:
            message += f"`{p['pid']:>5}` | {p['name']:<25} | CPU: {p['cpu']:.1f}%\n"
        
        await client.send_message(
            event.chat_id, message,
            buttons=[
                [Button.inline("🔪 O'chirish", b"process_kill_prompt")],
                [Button.inline("🔙 Ortga", b"back_to_main")]
            ]
        )
    
    @client.on(events.CallbackQuery(data=b"broadcast_processes"))
    async def broadcast_processes_handler(event):
        """Broadcast process list"""
        if event.sender_id != admin_id:
            return
        event._chat_id = admin_id
        await process_list_handler(event)
    
    @client.on(events.CallbackQuery(data=b"process_kill_prompt"))
    async def process_kill_prompt_handler(event):
        """Prompt for PID to kill"""
        if event.sender_id != admin_id:
            return
        
        ctx.user_state['waiting_for'] = 'kill_pid'
        
        await event.edit(
            "🔪 **Jarayonni O'chirish**\n\n"
            "PID raqamini yuboring:",
            buttons=[[Button.inline("❌ Bekor", b"back_to_main")]]
        )
    
    # ==================== POWER CONTROL ====================
    @client.on(events.CallbackQuery(data=b"shutdown_prompt"))
    async def shutdown_prompt_handler(event):
        """Confirm shutdown"""
        if event.sender_id != admin_id:
            return
        
        await event.edit(
            "🔌 **Kompyuterni O'chirish**\n\n"
            "⚠️ Ishonchingiz komilmi?",
            buttons=[
                [Button.inline("✅ Ha, O'chir", b"shutdown_confirm")],
                [Button.inline("❌ Yo'q", b"back_to_main")]
            ]
        )
    
    @client.on(events.CallbackQuery(data=b"shutdown_confirm"))
    async def shutdown_confirm_handler(event):
        """Execute shutdown"""
        if event.sender_id != admin_id:
            return
        
        await event.answer("🔌 O'chirilmoqda...")
        await client.send_message(event.chat_id, "🔌 Kompyuter o'chirilmoqda...")
        
        from utils import run_command_async
        await run_command_async("shutdown /s /t 5")
    
    @client.on(events.CallbackQuery(data=b"restart_prompt"))
    async def restart_prompt_handler(event):
        """Confirm restart"""
        if event.sender_id != admin_id:
            return
        
        await event.edit(
            "🔄 **Qayta Yuklash**\n\n"
            "⚠️ Ishonchingiz komilmi?",
            buttons=[
                [Button.inline("✅ Ha, Qayta yukla", b"restart_confirm")],
                [Button.inline("❌ Yo'q", b"back_to_main")]
            ]
        )
    
    @client.on(events.CallbackQuery(data=b"restart_confirm"))
    async def restart_confirm_handler(event):
        """Execute restart"""
        if event.sender_id != admin_id:
            return
        
        await event.answer("🔄 Qayta yuklanmoqda...")
        await client.send_message(event.chat_id, "🔄 Kompyuter qayta yuklanmoqda...")
        
        from utils import run_command_async
        await run_command_async("shutdown /r /t 5")
    
    @client.on(events.CallbackQuery(data=b"shutdown_cancel"))
    async def shutdown_cancel_handler(event):
        """Cancel shutdown"""
        if event.sender_id != admin_id:
            return
        
        from utils import run_command_async
        await run_command_async("shutdown /a")
        await event.answer("❌ O'chirish bekor qilindi")
    
    @client.on(events.CallbackQuery(data=b"lock_screen"))
    async def lock_screen_handler(event):
        """Lock screen"""
        if event.sender_id != admin_id:
            return
        
        import ctypes
        await asyncio.get_event_loop().run_in_executor(
            None, ctypes.windll.user32.LockWorkStation
        )
        await event.answer("🔒 Ekran qulflandi")
    
    logger.info("System handlers registered")
