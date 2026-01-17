# handlers/__init__.py - v3.0.5 Handler Registration
"""
Telegram handlers:
- Admin handlers
- Callback handlers
- Device handlers
"""

from .admin_handlers import register_admin_handlers
from .callback_handlers import register_callback_handlers

def register_all_handlers(client, services):
    """
    Barcha handlerlarni ro'yxatdan o'tkazish
    
    Args:
        client: TelegramClient
        services: Dict with DeviceService, AIService, etc.
    """
    register_admin_handlers(client, services)
    register_callback_handlers(client, services)

__all__ = ['register_all_handlers', 'register_admin_handlers', 'register_callback_handlers']
