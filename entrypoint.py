# entrypoint.py - v3.0.5 Server Entry Point
"""
Minimal startup script:
- TelegramClient initialization
- Services setup
- Handler registration
- Main loop
"""

import asyncio
import logging
import sys

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('server_bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point"""
    from telethon import TelegramClient
    
    # Import after logging setup
    from config import (
        API_ID, API_HASH, BOT_TOKEN, ADMIN_ID,
        USE_OPENROUTER, OPENROUTER_API_KEY, OPENROUTER_MODEL,
        GEMINI_API_KEY, HMAC_SECRET, CURRENT_VERSION
    )
    from database import Database
    from services import DeviceService, HeartbeatService, AIService
    
    logger.info(f"Starting Server Bot v{CURRENT_VERSION}...")
    
    # ==================== DATABASE ====================
    logger.info("Initializing database...")
    db = Database("server_bot.db")
    if not db.connect():
        logger.error("Database connection failed!")
        return
    
    # ==================== SERVICES ====================
    logger.info("Initializing services...")
    
    # Device Service
    device_service = DeviceService(db, hmac_secret=HMAC_SECRET)
    
    # Heartbeat Service
    heartbeat_service = HeartbeatService(device_service, interval=60, timeout=120)
    
    # AI Service
    ai_service = AIService(
        use_openrouter=USE_OPENROUTER,
        openrouter_key=OPENROUTER_API_KEY,
        gemini_key=GEMINI_API_KEY,
        model=OPENROUTER_MODEL
    )
    ai_service.initialize()
    
    # Services dict for handlers
    services = {
        'db': db,
        'device_service': device_service,
        'heartbeat_service': heartbeat_service,
        'ai_service': ai_service,
        'admin_id': ADMIN_ID
    }
    
    # ==================== TELEGRAM CLIENT ====================
    logger.info("Starting Telegram client...")
    client = TelegramClient('server_bot', API_ID, API_HASH)
    
    try:
        await client.start(bot_token=BOT_TOKEN)
        
        # ==================== HANDLERS ====================
        logger.info("Registering handlers...")
        
        # New modular handlers
        try:
            from handlers import register_all_handlers
            register_all_handlers(client, services)
            logger.info("Modular handlers registered")
        except ImportError:
            # Fallback to original handlers.py
            logger.warning("Modular handlers not found, using original handlers.py")
            from handlers import register_handlers
            register_handlers(client)
        
        # ==================== HEARTBEAT ====================
        logger.info("Starting heartbeat service...")
        heartbeat_service.start()
        
        # Offline callback
        async def on_device_offline(device_id):
            try:
                device = device_service.get_device(device_id)
                if device:
                    info = device.get('info', {})
                    message = (
                        f"🔴 **Device Offline**\n\n"
                        f"📱 Device: `{device_id}`\n"
                        f"💻 Hostname: `{info.get('hostname', 'Unknown')}`\n"
                        f"👤 User: `{info.get('username', 'Unknown')}`"
                    )
                    await client.send_message(ADMIN_ID, message)
            except Exception as e:
                logger.error(f"Offline notification error: {e}")
        
        heartbeat_service.on_device_offline = on_device_offline
        
        # ==================== STARTUP MESSAGE ====================
        ai_status = "✅ AI enabled" if ai_service.is_enabled else "⚠️ AI disabled"
        
        await client.send_message(
            ADMIN_ID,
            f"🤖 **Server Bot v{CURRENT_VERSION} Started**\n\n"
            "✅ Database connected (WAL mode)\n"
            "✅ Device registry active\n"
            "✅ Heartbeat service running\n"
            "✅ Security module loaded\n"
            f"{ai_status}\n\n"
            "💬 Send /start to open dashboard"
        )
        
        logger.info(f"✅ Server Bot v{CURRENT_VERSION} is running")
        
        # ==================== RUN FOREVER ====================
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("Server Bot stopped by user")
    except Exception as e:
        logger.error(f"Server Bot error: {e}", exc_info=True)
    finally:
        # Cleanup
        heartbeat_service.stop()
        db.disconnect()
        logger.info("Server Bot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server Bot stopped")
