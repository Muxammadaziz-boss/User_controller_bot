# client_handlers/__init__.py - v3.0.5 Handler Package
"""
Modular handler architecture
Each module handles a specific category
"""

from .spy import register_spy_handlers
from .system import register_system_handlers
from .files import register_file_handlers

__all__ = [
    'register_spy_handlers',
    'register_system_handlers', 
    'register_file_handlers',
    'register_all_handlers'
]


def register_all_handlers(client, ctx):
    """Register all handler modules"""
    register_spy_handlers(client, ctx)
    register_system_handlers(client, ctx)
    register_file_handlers(client, ctx)
