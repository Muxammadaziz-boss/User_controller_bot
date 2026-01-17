# tools/upload_env.py - Upload .env to server
"""Quick script to upload .env file"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import paramiko

SSH_HOST = "ssh-muxammadaziz.alwaysdata.net"
SSH_USER = "muxammadaziz"
REMOTE_DIR = "/home/muxammadaziz/ghost_server"

password = os.environ.get('ALWAYSDATA_PASSWORD', 'MAZIZ2009')

print("Uploading .env to server...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SSH_HOST, username=SSH_USER, password=password)

sftp = ssh.open_sftp()

local_env = Path(__file__).parent.parent / "server" / ".env"
remote_env = f"{REMOTE_DIR}/.env"

sftp.put(str(local_env), remote_env)
print(f"✅ Uploaded .env to {remote_env}")

# Restart bot
print("Restarting bot...")
stdin, stdout, stderr = ssh.exec_command(f"pkill -f 'python.*bot.py' ; cd {REMOTE_DIR} && nohup python bot.py > bot.log 2>&1 &")
print(stdout.read().decode())

sftp.close()
ssh.close()
print("Done!")
