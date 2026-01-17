# tools/ghost_hunter.py - Find Old Ghost Installations
"""
Scan local machine for old Ghost/RAT leftovers
"""

import os
import sys
import io

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import winreg
from pathlib import Path
from datetime import datetime


def search_registry():
    """Search registry for Ghost entries"""
    findings = []
    
    # Keys to check
    keys_to_check = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    ]
    
    suspicious_names = [
        'SystemService', 'WindowsUpdate', 'svchost', 'system', 
        'ghost', 'remote', 'client', 'helper', 'service'
    ]
    
    for hive, key_path in keys_to_check:
        try:
            key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ)
            
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    
                    # Check if suspicious
                    for sus in suspicious_names:
                        if sus.lower() in name.lower() or sus.lower() in value.lower():
                            hive_name = "HKCU" if hive == winreg.HKEY_CURRENT_USER else "HKLM"
                            findings.append({
                                'type': 'registry',
                                'location': f"{hive_name}\\{key_path}",
                                'name': name,
                                'value': value
                            })
                            break
                    
                    i += 1
                except OSError:
                    break
            
            winreg.CloseKey(key)
            
        except Exception as e:
            pass
    
    return findings


def search_files():
    """Search for Ghost files in common locations"""
    findings = []
    
    # Locations to check
    search_paths = [
        Path(os.environ.get('APPDATA', '')) / 'Microsoft' / 'Crypto' / 'system',
        Path(os.environ.get('APPDATA', '')) / 'Microsoft' / 'Windows',
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Temp',
        Path(os.environ.get('TEMP', '')),
        Path.home() / 'AppData' / 'Local' / 'Microsoft',
        Path(os.environ.get('PROGRAMDATA', '')) / 'Microsoft',
    ]
    
    # Files to look for
    suspicious_files = [
        'session.session', 'session.session-journal',
        'net.dat', 'version.txt', 'config.dat',
        'system.exe', 'svchost.exe', 'helper.exe',
        'ghost*.exe', '*.session'
    ]
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
        
        try:
            for pattern in suspicious_files:
                if '*' in pattern:
                    for file in search_path.glob(pattern):
                        findings.append({
                            'type': 'file',
                            'location': str(file),
                            'size': file.stat().st_size if file.exists() else 0,
                            'modified': datetime.fromtimestamp(file.stat().st_mtime).isoformat() if file.exists() else ''
                        })
                else:
                    file = search_path / pattern
                    if file.exists():
                        findings.append({
                            'type': 'file',
                            'location': str(file),
                            'size': file.stat().st_size,
                            'modified': datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                        })
        except Exception as e:
            pass
    
    return findings


def search_tasks():
    """Search scheduled tasks"""
    findings = []
    
    try:
        import subprocess
        result = subprocess.run(
            ['schtasks', '/query', '/fo', 'csv'],
            capture_output=True,
            text=True,
            creationflags=0x08000000  # CREATE_NO_WINDOW
        )
        
        suspicious = ['SystemService', 'WindowsUpdate', 'ghost', 'helper', 'client']
        
        for line in result.stdout.split('\n'):
            for sus in suspicious:
                if sus.lower() in line.lower():
                    findings.append({
                        'type': 'task',
                        'location': 'Task Scheduler',
                        'name': line.split(',')[0].strip('"') if ',' in line else line
                    })
                    break
                    
    except Exception as e:
        pass
    
    return findings


def search_processes():
    """Search running processes"""
    findings = []
    
    try:
        import psutil
        
        suspicious = ['system.exe', 'svchost32.exe', 'ghost', 'helper.exe']
        
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                name = proc.info['name'].lower()
                exe = proc.info.get('exe', '') or ''
                
                for sus in suspicious:
                    if sus.lower() in name or sus.lower() in exe.lower():
                        # Skip real system processes
                        if 'windows\\system32' in exe.lower():
                            continue
                        
                        findings.append({
                            'type': 'process',
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'exe': exe
                        })
                        break
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
    except ImportError:
        print("⚠️ psutil not available - process scan skipped")
    
    return findings


def main():
    print("=" * 60)
    print("🔍 GHOST HUNTER - Local Installation Scanner")
    print("=" * 60)
    print()
    
    all_findings = []
    
    # 1. Registry scan
    print("📋 Scanning registry...")
    registry_findings = search_registry()
    all_findings.extend(registry_findings)
    print(f"   Found: {len(registry_findings)} entries")
    
    # 2. File scan
    print("📁 Scanning files...")
    file_findings = search_files()
    all_findings.extend(file_findings)
    print(f"   Found: {len(file_findings)} files")
    
    # 3. Task scan
    print("📅 Scanning scheduled tasks...")
    task_findings = search_tasks()
    all_findings.extend(task_findings)
    print(f"   Found: {len(task_findings)} tasks")
    
    # 4. Process scan
    print("⚙️ Scanning processes...")
    process_findings = search_processes()
    all_findings.extend(process_findings)
    print(f"   Found: {len(process_findings)} processes")
    
    # Report
    print()
    print("=" * 60)
    
    if not all_findings:
        print("✅ NO GHOST LEFTOVERS FOUND!")
        print("   Your system is clean.")
    else:
        print(f"⚠️ FOUND {len(all_findings)} POTENTIAL LEFTOVERS:")
        print()
        
        for i, finding in enumerate(all_findings, 1):
            print(f"  {i}. [{finding['type'].upper()}]")
            
            if finding['type'] == 'registry':
                print(f"     📍 {finding['location']}")
                print(f"     📛 Name: {finding['name']}")
                print(f"     📄 Value: {finding['value'][:80]}...")
                
            elif finding['type'] == 'file':
                print(f"     📍 {finding['location']}")
                print(f"     📊 Size: {finding['size']} bytes")
                print(f"     📅 Modified: {finding['modified']}")
                
            elif finding['type'] == 'task':
                print(f"     📍 {finding['location']}")
                print(f"     📛 Task: {finding['name']}")
                
            elif finding['type'] == 'process':
                print(f"     🔢 PID: {finding['pid']}")
                print(f"     📛 Name: {finding['name']}")
                print(f"     📍 EXE: {finding['exe']}")
            
            print()
        
        print("💡 To clean up:")
        print("   - Registry: Use regedit or run 'reg delete' commands")
        print("   - Files: Delete the listed files manually")
        print("   - Tasks: Use Task Scheduler to remove")
        print("   - Processes: Use Task Manager to end them")
    
    print("=" * 60)
    
    return all_findings


if __name__ == "__main__":
    findings = main()
    sys.exit(0 if not findings else 1)
