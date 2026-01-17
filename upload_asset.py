import urllib.request
import json

GITHUB_TOKEN = "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"
REPO = "Muxammadaziz-boss/User_controller_bot"
TAG = "v3.0.4"
FILE_PATH = "system/system.exe"

# Get release info
url = f"https://api.github.com/repos/{REPO}/releases/tags/{TAG}"
req = urllib.request.Request(url, headers={
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
})
response = urllib.request.urlopen(req)
release = json.loads(response.read())

print(f"Release ID: {release['id']}")
upload_url = release['upload_url'].replace('{?name,label}', f'?name=system.exe')
print(f"Upload URL: {upload_url}")

# Upload file
with open(FILE_PATH, 'rb') as f:
    file_data = f.read()
    print(f"File size: {len(file_data) / 1024 / 1024:.1f} MB")

upload_req = urllib.request.Request(upload_url, data=file_data, method='POST', headers={
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/octet-stream"
})

try:
    upload_response = urllib.request.urlopen(upload_req)
    result = json.loads(upload_response.read())
    print(f"✅ Uploaded: {result['name']}")
    print(f"Download URL: {result['browser_download_url']}")
except urllib.error.HTTPError as e:
    print(f"❌ Error {e.code}: {e.read().decode()}")
