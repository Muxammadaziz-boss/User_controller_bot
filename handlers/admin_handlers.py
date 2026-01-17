# handlers/admin_handlers.py - v3.0.5 Admin Handlers
"""
Admin command handlers:
- /start, /devices, /stats, /ai
- Message handling
- AI integration
"""

import logging
from telethon import events
from telethon.tl.custom import Button

logger = logging.getLogger(__name__)


def register_admin_handlers(client, services):
    """
    Admin handlerlarni ro'yxatdan o'tkazish
    
    Args:
        client: TelegramClient
        services: Dict - {'db', 'device_service', 'ai_service', 'admin_id'}
    """
    admin_id = services.get('admin_id')
    device_service = services.get('device_service')
    ai_service = services.get('ai_service')
    
    # Rate limiter
    try:
        from security import default_limiter, rate_limit
    except ImportError:
        default_limiter = None
        rate_limit = None
    
    def is_admin(event):
        return event.sender_id == admin_id
    
    @client.on(events.NewMessage(pattern='/start', incoming=True))
    async def start_handler(event):
        """Start command - asosiy menyu"""
        if not is_admin(event):
            return
        
        # Rate limiting
        if default_limiter and not default_limiter.is_allowed(event.sender_id):
            await event.respond("⚠️ Juda ko'p so'rov! Biroz kuting.")
            return
        
        try:
            from panels import admin_panel
            await event.respond("👋 **Boshqaruv Paneli v3.0.5**", buttons=admin_panel)
        except Exception as e:
            logger.error(f"Start handler error: {e}")
            await event.respond(f"❌ Xato: {e}")
    
    @client.on(events.NewMessage(pattern='/devices', incoming=True))
    async def devices_handler(event):
        """Devices command"""
        if not is_admin(event):
            return
        
        try:
            if device_service:
                devices = device_service.get_all_devices()
                stats = device_service.get_statistics()
                
                message = (
                    f"📱 **Qurilmalar ({stats['total']})**\n\n"
                    f"🟢 Online: {stats['online']}\n"
                    f"🔴 Offline: {stats['offline']}\n"
                    f"📈 Onlayn: {stats['online_percent']}%"
                )
                
                buttons = []
                for device_id, device in list(devices.items())[:10]:
                    status = "🟢" if device.get('status') == 'online' else "🔴"
                    info = device.get('info', {}) if isinstance(device.get('info'), dict) else device.get('metadata', {})
                    hostname = info.get('hostname', 'Unknown')[:15]
                    buttons.append([Button.inline(f"{status} {hostname}", f"device_{device_id}".encode())])
                
                buttons.append([Button.inline("🔙 Ortga", b"back_to_main")])
                
                await event.respond(message, buttons=buttons)
            else:
                await event.respond("❌ Device service mavjud emas")
                
        except Exception as e:
            logger.error(f"Devices handler error: {e}")
            await event.respond(f"❌ Xato: {e}")
    
    @client.on(events.NewMessage(pattern='/stats', incoming=True))
    async def stats_handler(event):
        """Stats command"""
        if not is_admin(event):
            return
        
        try:
            db = services.get('db')
            if db:
                dashboard = db.get_dashboard_stats()
                
                message = (
                    f"📊 **Statistika**\n\n"
                    f"📱 Jami qurilmalar: `{dashboard.get('total_devices', 0)}`\n"
                    f"🟢 Online: `{dashboard.get('online_devices', 0)}`\n"
                    f"💓 Heartbeats: `{dashboard.get('total_heartbeats', 0)}`\n"
                    f"⚡ Buyruqlar: `{dashboard.get('total_commands', 0)}`\n"
                    f"❌ Xatolar: `{dashboard.get('total_errors', 0)}`"
                )
                
                await event.respond(message)
            else:
                await event.respond("❌ Database mavjud emas")
                
        except Exception as e:
            logger.error(f"Stats handler error: {e}")
            await event.respond(f"❌ Xato: {e}")
    
    @client.on(events.NewMessage(pattern='/ai', incoming=True))
    async def ai_handler(event):
        """AI settings command"""
        if not is_admin(event):
            return
        
        try:
            if ai_service:
                status = ai_service.get_status()
                
                status_text = "Yoqilgan" if status['enabled'] else "O'chirilgan"
                status_emoji = "✅" if status['enabled'] else "❌"
                
                message = (
                    f"🤖 **AI Sozlamalari**\n\n"
                    f"Holat: {status_emoji} {status_text}\n"
                    f"Provider: {status['provider'] or 'N/A'}\n"
                    f"Model: {status['model']}"
                )
                
                from panels import ai_settings_panel
                await event.respond(message, buttons=ai_settings_panel)
            else:
                await event.respond("❌ AI service mavjud emas")
                
        except Exception as e:
            logger.error(f"AI handler error: {e}")
            await event.respond(f"❌ Xato: {e}")
    
    @client.on(events.NewMessage(incoming=True))
    async def message_handler(event):
        """General message handler - AI chat"""
        if not is_admin(event):
            return
        
        # Skip commands
        if event.text and event.text.startswith('/'):
            return
        
        try:
            if ai_service and ai_service.is_enabled and event.text:
                # Context
                context = {}
                if device_service:
                    context['devices'] = device_service.get_statistics()
                
                response = await ai_service.chat(event.text, context)
                await event.respond(response)
                
        except Exception as e:
            logger.error(f"Message handler error: {e}")
    
    logger.info("Admin handlers registered")
