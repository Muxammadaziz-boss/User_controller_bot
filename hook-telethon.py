# hook-telethon.py - PyInstaller hook for Telethon
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = collect_all('telethon')
hiddenimports += collect_submodules('telethon')

# Qo'shimcha kerakli modullar
hiddenimports += [
    'telethon.sync',
    'telethon.tl',
    'telethon.tl.types',
    'telethon.tl.functions',
    'telethon.crypto',
    'telethon.network',
    'telethon.sessions',
    'telethon.extensions',
    'telethon.client',
    'telethon.events',
    'telethon.errors',
    'cryptography',
    'cryptography.hazmat',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.ciphers',
    'cryptography.hazmat.backends',
]
