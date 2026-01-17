# services/heartbeat_service.py - v3.0.5 Heartbeat Service
"""
Heartbeat monitoring xizmati:
- Device'larni monitoring qilish
- Offline detection
- Callback system
"""

import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, Any

logger = logging.getLogger(__name__)


class HeartbeatService:
    """Heartbeat monitoring service"""
    
    def __init__(self, device_service, interval: int = 60, timeout: int = 120):
        """
        Args:
            device_service: DeviceService instance
            interval: Check interval in seconds
            timeout: Offline threshold in seconds
        """
        self.device_service = device_service
        self.interval = interval
        self.timeout = timeout
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_device_offline: Optional[Callable] = None
        self.on_device_online: Optional[Callable] = None
    
    def start(self):
        """Monitoring'ni boshlash"""
        if self.running:
            logger.warning("Heartbeat service already running")
            return False
        
        self.running = True
        
        # Try async first, fallback to thread
        try:
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._monitor_async())
            logger.info("Heartbeat service started (async)")
        except RuntimeError:
            # No running loop - use thread
            self._thread = threading.Thread(target=self._monitor_sync, daemon=True)
            self._thread.start()
            logger.info("Heartbeat service started (threaded)")
        
        return True
    
    def stop(self):
        """Monitoring'ni to'xtatish"""
        self.running = False
        
        if self._task:
            self._task.cancel()
            self._task = None
        
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        
        logger.info("Heartbeat service stopped")
    
    async def _monitor_async(self):
        """Async monitoring loop"""
        while self.running:
            try:
                await self._check_devices()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                await asyncio.sleep(5)
    
    def _monitor_sync(self):
        """Sync monitoring loop (for threading)"""
        import time
        while self.running:
            try:
                # Create new event loop for thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._check_devices())
                loop.close()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                time.sleep(5)
    
    async def _check_devices(self):
        """Device'larni tekshirish"""
        try:
            now = datetime.now()
            timeout_delta = timedelta(seconds=self.timeout)
            
            devices = self.device_service.get_all_devices()
            
            for device_id, device in devices.items():
                try:
                    last_seen_str = device.get('last_seen', '')
                    if not last_seen_str:
                        continue
                    
                    # Parse last_seen
                    try:
                        last_seen = datetime.fromisoformat(last_seen_str.replace('Z', '+00:00'))
                        if last_seen.tzinfo:
                            last_seen = last_seen.replace(tzinfo=None)
                    except:
                        continue
                    
                    current_status = device.get('status', 'offline')
                    
                    # Check timeout
                    if (now - last_seen) > timeout_delta:
                        if current_status == 'online':
                            logger.warning(f"Device offline: {device_id}")
                            self.device_service.mark_offline(device_id)
                            
                            # Callback
                            if self.on_device_offline:
                                try:
                                    if asyncio.iscoroutinefunction(self.on_device_offline):
                                        await self.on_device_offline(device_id)
                                    else:
                                        self.on_device_offline(device_id)
                                except Exception as cb_err:
                                    logger.error(f"Offline callback error: {cb_err}")
                    
                except Exception as dev_err:
                    logger.debug(f"Check device error: {device_id} - {dev_err}")
                    continue
                    
        except Exception as e:
            logger.error(f"Check devices error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Service status"""
        return {
            'running': self.running,
            'interval': self.interval,
            'timeout': self.timeout,
            'mode': 'async' if self._task else 'threaded' if self._thread else 'stopped'
        }
