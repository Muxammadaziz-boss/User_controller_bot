# tools/deploy_server.py - AlwaysData Server Deployment
"""
Deploy server files to AlwaysData via SSH/SFTP
"""

import os
import sys
import getpass
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import paramiko
except ImportError:
    print("❌ paramiko not installed. Run: pip install paramiko")
    sys.exit(1)

# Configuration
SSH_HOST = "ssh-muxammadaziz.alwaysdata.net"
SSH_USER = "muxammadaziz"
REMOTE_DIR = "/home/muxammadaziz/ghost_server"
LOCAL_SERVER_DIR = Path(__file__).parent.parent / "server"


def get_password():
    """Get SSH password from .env or prompt"""
    env_file = Path(__file__).parent.parent / "server" / ".env"
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('SSH_PASSWORD='):
                    return line.split('=', 1)[1].strip()
    
    # Check environment
    pwd = os.environ.get('ALWAYSDATA_PASSWORD', '')
    if pwd:
        return pwd
    
    # Prompt user
    return getpass.getpass(f"🔑 Enter SSH password for {SSH_USER}@{SSH_HOST}: ")


def deploy():
    """Deploy server files"""
    print("=" * 50)
    print("🚀 Ghost Server Deployment")
    print("=" * 50)
    
    password = get_password()
    if not password:
        print("❌ Password required!")
        return False
    
    print(f"\n📡 Connecting to {SSH_HOST}...")
    
    try:
        # SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, password=password)
        
        print("✅ Connected!")
        
        # SFTP
        sftp = ssh.open_sftp()
        
        # 1. Clean remote directory
        print(f"\n🗑️ Cleaning {REMOTE_DIR}...")
        
        try:
            # List and remove all files
            stdin, stdout, stderr = ssh.exec_command(f'rm -rf {REMOTE_DIR}/*')
            stdout.read()
            print("✅ Remote directory cleaned")
        except Exception as e:
            print(f"⚠️ Clean warning: {e}")
        
        # 2. Ensure remote directory exists
        try:
            sftp.mkdir(REMOTE_DIR)
        except:
            pass  # Already exists
        
        # 3. Upload server files
        print(f"\n📤 Uploading files from {LOCAL_SERVER_DIR}...")
        
        if not LOCAL_SERVER_DIR.exists():
            print(f"❌ Local server directory not found: {LOCAL_SERVER_DIR}")
            return False
        
        uploaded = 0
        for local_file in LOCAL_SERVER_DIR.iterdir():
            if local_file.is_file() and not local_file.name.startswith('.'):
                remote_path = f"{REMOTE_DIR}/{local_file.name}"
                print(f"   📄 {local_file.name}")
                sftp.put(str(local_file), remote_path)
                uploaded += 1
        
        print(f"\n✅ Uploaded {uploaded} files")
        
        # 4. Set permissions
        print("\n🔧 Setting permissions...")
        ssh.exec_command(f'chmod +x {REMOTE_DIR}/*.py')
        
        # 5. Create requirements if missing
        stdin, stdout, stderr = ssh.exec_command(f'cat {REMOTE_DIR}/requirements.txt')
        if not stdout.read():
            print("📝 Creating requirements.txt...")
            sftp.putfo(
                __import__('io').BytesIO(b"telethon>=1.28.0\naiosqlite>=0.19.0\naiohttp>=3.8.0\n"),
                f"{REMOTE_DIR}/requirements.txt"
            )
        
        # 6. Install dependencies
        print("\n📦 Installing dependencies...")
        stdin, stdout, stderr = ssh.exec_command(
            f'cd {REMOTE_DIR} && pip install -r requirements.txt --quiet'
        )
        stdout.read()
        
        # Close connections
        sftp.close()
        ssh.close()
        
        print("\n" + "=" * 50)
        print("✅ DEPLOYMENT COMPLETE!")
        print(f"   Remote: {SSH_HOST}:{REMOTE_DIR}")
        print(f"   Files: {uploaded}")
        print("\n💡 To start the bot:")
        print(f"   ssh {SSH_USER}@{SSH_HOST}")
        print(f"   cd {REMOTE_DIR}")
        print(f"   nohup python bot.py &")
        print("=" * 50)
        
        return True
        
    except paramiko.AuthenticationException:
        print("❌ Authentication failed! Check password.")
        return False
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False


def main():
    success = deploy()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
