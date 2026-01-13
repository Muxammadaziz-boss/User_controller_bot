# bot.py - v3.0.3 SERVER BOT (PART 1/2)
"""
Central server bot:
- Device management
- AI assistant (OpenRouter)
- Status monitoring
- Command routing
- 24/7 operation
"""

import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.custom import Button

import config
from config import (
    API_ID, API_HASH, BOT_TOKEN, ADMIN_ID,
    USE_OPENROUTER, OPENROUTER_API_KEY, OPENROUTER_MODEL, GEMINI_API_KEY
)

from database import Database
from device_manager import DeviceRegistry, HeartbeatManager
from ai_helper import (
    initialize_ai_helper, get_ai_helper,
    is_ai_enabled, enable_ai, disable_ai
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== GLOBAL STATE ====================
db = None
device_registry = None
heartbeat_manager = None
client = None
user_state = {}

# ==================== INITIALIZATION ====================
async def initialize():
    """Bot'ni ishga tushirish"""
    global db, device_registry, heartbeat_manager
    
    try:
        # Database
        logger.info("Initializing database...")
        db = Database("server_bot.db")
        db.connect()
        
        # Device registry
        logger.info("Initializing device registry...")
        device_registry = DeviceRegistry(db)
        
        # Heartbeat manager
        logger.info("Starting heartbeat manager...")
        heartbeat_manager = HeartbeatManager(device_registry, interval=60)
        heartbeat_manager.on_device_offline = on_device_offline
        heartbeat_manager.start()
        
        # AI (OpenRouter)
        logger.info("Initializing AI...")
        
        if USE_OPENROUTER and OPENROUTER_API_KEY and OPENROUTER_API_KEY != "YOUR_KEY":
            success = initialize_ai_helper(
                provider_type="openrouter",
                api_key=OPENROUTER_API_KEY
            )
            if success:
                logger.info("✅ OpenRouter AI initialized")
                enable_ai()
            else:
                logger.warning("⚠️ OpenRouter failed, trying Gemini...")
                # Fallback to Gemini
                success = initialize_ai_helper(
                    provider_type="anthropic",
                    api_key=GEMINI_API_KEY
                )
                if success:
                    logger.info("✅ Gemini AI initialized (backup)")
                    enable_ai()
                else:
                    logger.error("❌ All AI failed")
                    disable_ai()
        elif GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_API_KEY":
            success = initialize_ai_helper(
                provider_type="anthropic",
                api_key=GEMINI_API_KEY
            )
            if success:
                logger.info("✅ Gemini AI initialized")
                enable_ai()
            else:
                logger.warning("⚠️ AI initialization failed")
                disable_ai()
        else:
            logger.warning("⚠️ No AI API key configured")
            disable_ai()
        
        logger.info("✅ Server bot initialized")
        return True
        
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        return False

# ==================== CALLBACKS ====================
async def on_device_offline(device_id):
    """Device offline bo'lganda"""
    try:
        device = device_registry.get_device(device_id)
        if device:
            message = (
                f"🔴 **Device Offline**\n\n"
                f"📱 Device: `{device_id}`\n"
                f"💻 Hostname: `{device['info'].get('hostname', 'Unknown')}`\n"
                f"👤 User: `{device['info'].get('username', 'Unknown')}`\n"
                f"🕐 Last seen: `{device['last_seen']}`"
            )
            await client.send_message(ADMIN_ID, message)
            
            # Log to database
            db.log_activity(device_id, "device_offline", "Device went offline", "info")
            
    except Exception as e:
        logger.error(f"On device offline error: {e}")

# ==================== MESSAGE HANDLER ====================
@events.register(events.NewMessage(chats=ADMIN_ID))
async def message_handler(event):
    """Text xabarlarni handle qilish"""
    global user_state
    
    try:
        # ⚠️ Bot o'z xabarlariga javob bermasligi kerak!
        if event.out:
            return
        
        # Command xabarlarga javob berma (ular alohida handler'da)
        message = event.raw_text.strip()
        if message.startswith('/'):
            return
        
        # Check user state
        current_state = user_state.get(ADMIN_ID, "idle")
        
        # Agar tugma aktiv bo'lsa - AI silent
        if current_state != "idle":
            logger.info(f"AI silent mode - state: {current_state}")
            return
        
        # AI enabled va text message
        if is_ai_enabled() and message:
            # Oddiy suhbat - AI Helper bilan
            ai = get_ai_helper()
            if ai:
                response = await ai.generate_response(message)
                await event.reply(response)
                
    except Exception as e:
        logger.error(f"Message handler error: {e}")
        await event.reply(f"❌ Error: {str(e)}")

async def handle_ai_command(event, parsed_command):
    """AI command'ni bajarish"""
    try:
        action = parsed_command.get('action')
        target = parsed_command.get('target')
        
        if action == 'screenshot':
            if target == 'all':
                await event.reply("📸 Sending screenshot command to all devices...")
            elif target.startswith('#'):
                device_num = int(target[1:])
                await event.reply(f"📸 Sending screenshot command to device #{device_num}...")
        
        elif action == 'info':
            if target.startswith('#'):
                device_num = int(target[1:])
                devices = list(device_registry.get_all_devices().values())
                if 0 < device_num <= len(devices):
                    device = devices[device_num - 1]
                    from device_manager import format_device_info
                    info = format_device_info(device)
                    await event.reply(info)
                else:
                    await event.reply(f"❌ Device #{device_num} not found")
        
        elif action == 'devices':
            await show_devices(event)
        
        else:
            await event.reply(f"🤖 Command recognized: {action}\nBut not implemented yet!")
            
    except Exception as e:
        logger.error(f"Handle AI command error: {e}")
        await event.reply(f"❌ Command error: {str(e)}")

# ==================== CALLBACK HANDLER ====================
@events.register(events.CallbackQuery())
async def callback_handler(event):
    """Tugma callback'larni handle qilish"""
    global user_state
    
    try:
        data = event.data.decode()
        
        # State tracking
        if data == "back_to_main":
            user_state[ADMIN_ID] = "idle"
            await show_main_menu(event)
        
        elif data == "devices":
            await show_devices(event)
        
        elif data == "stats":
            await show_statistics(event)
        
        elif data == "ai_settings":
            await show_ai_settings(event)
        
        elif data == "ai_enable":
            enable_ai()
            await event.answer("✅ AI enabled")
            await show_ai_settings(event)
        
        elif data == "ai_disable":
            disable_ai()
            await event.answer("⚠️ AI disabled")
            await show_ai_settings(event)
        
        elif data.startswith("device_"):
            device_id = data.replace("device_", "")
            await show_device_details(event, device_id)
        
        else:
            # Mark state as active
            if data.startswith("cmd_") or data.startswith("ps_"):
                user_state[ADMIN_ID] = f"waiting_for_{data}"
            
    except Exception as e:
        logger.error(f"Callback handler error: {e}")
        await event.answer(f"❌ Error: {str(e)}")

# ==================== UI FUNCTIONS ====================
async def show_main_menu(event):
    """Asosiy menyu"""
    try:
        stats = device_registry.get_statistics()
        
        message = (
            f"🤖 **Server Bot Dashboard**\n\n"
            f"📊 **Status:**\n"
            f"🟢 Online: {stats['online']}\n"
            f"🔴 Offline: {stats['offline']}\n"
            f"📱 Total: {stats['total']}\n"
            f"📈 Uptime: {stats['online_percent']}%\n\n"
            f"🤖 AI: {'✅ Enabled' if is_ai_enabled() else '❌ Disabled'}\n\n"
            f"💬 Type anything to chat with AI\n"
            f"💡 /devices - Device list\n"
            f"💡 /stats - Statistics\n"
            f"💡 /ai - AI settings"
        )
        
        buttons = [
            [Button.inline("📱 Devices", b"devices"),
             Button.inline("📊 Statistics", b"stats")],
            [Button.inline("🤖 AI Settings", b"ai_settings"),
             Button.inline("🔄 Refresh", b"back_to_main")]
        ]
        
        await event.edit(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Show main menu error: {e}")

async def show_devices(event):
    """Device ro'yxati"""
    try:
        devices = device_registry.get_all_devices()
        
        if not devices:
            await event.edit("📱 **Devices**\n\n❌ No devices registered",
                           buttons=[[Button.inline("🔙 Back", b"back_to_main")]])
            return
        
        message = f"📱 **Devices ({len(devices)})**\n\n"
        
        buttons = []
        for i, (device_id, device) in enumerate(devices.items(), 1):
            status_emoji = "🟢" if device['status'] == 'online' else "🔴"
            info = device['info']
            
            button_text = f"{status_emoji} {info.get('hostname', 'Unknown')} ({info.get('username', 'User')})"
            buttons.append([Button.inline(button_text, f"device_{device_id}".encode())])
        
        buttons.append([Button.inline("🔙 Back", b"back_to_main")])
        
        await event.edit(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Show devices error: {e}")

async def show_device_details(event, device_id):
    """Device batafsil ma'lumot"""
    try:
        device = device_registry.get_device(device_id)
        
        if not device:
            await event.answer("❌ Device not found")
            return
        
        from device_manager import format_device_info
        message = format_device_info(device)
        
        buttons = [
            [Button.inline("📸 Screenshot", f"cmd_screenshot_{device_id}".encode())],
            [Button.inline("🔙 Back", b"devices")]
        ]
        
        await event.edit(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Show device details error: {e}")

async def show_statistics(event):
    """Statistika"""
    try:
        dashboard = db.get_dashboard_stats()
        
        message = (
            f"📊 **Statistics**\n\n"
            f"📱 Total Devices: `{dashboard.get('total_devices', 0)}`\n"
            f"🟢 Online: `{dashboard.get('online_devices', 0)}`\n"
            f"💓 Total Heartbeats: `{dashboard.get('total_heartbeats', 0)}`\n"
            f"⚡ Total Commands: `{dashboard.get('total_commands', 0)}`\n"
            f"❌ Total Errors: `{dashboard.get('total_errors', 0)}`\n\n"
        )
        
        if 'most_active_device' in dashboard:
            device = dashboard['most_active_device']
            message += (
                f"🏆 **Most Active:**\n"
                f"`{device['hostname']}` - {device['heartbeats']} heartbeats"
            )
        
        buttons = [[Button.inline("🔙 Back", b"back_to_main")]]
        
        await event.edit(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Show statistics error: {e}")

async def show_ai_settings(event):
    """AI sozlamalari"""
    try:
        ai_enabled = is_ai_enabled()
        
        ai = get_ai_helper()
        ai_type = type(ai.provider).__name__ if ai else "None"
        
        if ai_type == 'OpenRouterProvider':
            ai_model = "OpenRouter (Gemini 2.0 Free)"
        elif ai_type == 'AnthropicProvider':
            ai_model = "Anthropic Claude"
        else:
            ai_model = "Not initialized"
        
        message = (
            f"🤖 **AI Settings**\n\n"
            f"Status: {'✅ Enabled' if ai_enabled else '❌ Disabled'}\n"
            f"Model: {ai_model}\n\n"
            f"**Features:**\n"
            f"• Natural conversation\n"
            f"• Error explanation\n"
            f"• Device analysis\n"
            f"• Smart suggestions\n"
            f"• Command parsing\n\n"
            f"{'💬 Send any message to chat' if ai_enabled else '⚠️ Enable AI to start chatting'}"
        )
        
        buttons = [
            [Button.inline("✅ Enable AI" if not ai_enabled else "❌ Disable AI",
                          b"ai_enable" if not ai_enabled else b"ai_disable")],
            [Button.inline("🔙 Back", b"back_to_main")]
        ]
        
        await event.edit(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Show AI settings error: {e}")

# ==================== COMMANDS ====================
@events.register(events.NewMessage(pattern='/start', chats=ADMIN_ID))
async def start_handler(event):
    """Start command"""
    await show_main_menu(event)

@events.register(events.NewMessage(pattern='/devices', chats=ADMIN_ID))
async def devices_command(event):
    """Devices command"""
    await show_devices(event)

@events.register(events.NewMessage(pattern='/stats', chats=ADMIN_ID))
async def stats_command(event):
    """Stats command"""
    await show_statistics(event)

@events.register(events.NewMessage(pattern='/ai', chats=ADMIN_ID))
async def ai_command(event):
    """AI command"""
    await show_ai_settings(event)

# ==================== MAIN ====================
async def main():
    """Main function"""
    global client
    
    try:
        logger.info("Starting Server Bot...")
        
        # Initialize
        success = await initialize()
        if not success:
            logger.error("Initialization failed!")
            return
        
        # Telegram client
        client = TelegramClient('server_bot', API_ID, API_HASH)
        await client.start(bot_token=BOT_TOKEN)
        
        # Register handlers
        client.add_event_handler(start_handler)
        client.add_event_handler(devices_command)
        client.add_event_handler(stats_command)
        client.add_event_handler(ai_command)
        client.add_event_handler(message_handler)
        client.add_event_handler(callback_handler)
        
        # Notify admin
        ai_status = "✅ AI enabled (OpenRouter)" if is_ai_enabled() else "⚠️ AI disabled"
        
        await client.send_message(
            ADMIN_ID,
            "🤖 **Server Bot Started**\n\n"
            "✅ Database connected\n"
            "✅ Device registry active\n"
            "✅ Heartbeat manager running\n"
            f"{ai_status}\n\n"
            "💬 Send /start to open dashboard"
        )
        
        logger.info("✅ Server Bot is running (24/7)")
        
        # Run forever
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("Server Bot stopped by user")
    except Exception as e:
        logger.error(f"Server Bot error: {e}")
    finally:
        # Cleanup
        if heartbeat_manager:
            heartbeat_manager.stop()
        if db:
            db.disconnect()
        logger.info("Server Bot shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())