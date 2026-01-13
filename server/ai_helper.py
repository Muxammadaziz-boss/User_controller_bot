# ai_helper.py - v3.0.4 PRODUCTION READY
"""
AI Helper Module - Fully Async
Improved error handling, Gemini support, and fallback

v3.0.4 FIXES:
- Added GeminiProvider (Google Generative AI)
- Better error messages (O'zbek tilida)
- Improved retry mechanism
"""

import asyncio
import logging
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ==================== ASYNC AI PROVIDER ====================
class AsyncAIProvider:
    """Base class for AI providers - fully async"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def generate(self, prompt: str, **kwargs) -> Optional[str]:
        """Generate AI response asynchronously"""
        raise NotImplementedError("Subclass must implement generate()")


class GeminiProvider(AsyncAIProvider):
    """Google Gemini API - Fully Async"""
    
    async def generate(self, prompt: str, model: str = "gemini-1.5-flash", max_tokens: int = 1000) -> Optional[str]:
        """Generate using Google Gemini API"""
        try:
            import urllib.request
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            
            data = {
                "contents": [
                    {"parts": [{"text": prompt}]}
                ],
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": 0.7
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            loop = asyncio.get_event_loop()
            
            def fetch():
                request = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode('utf-8'),
                    headers=headers,
                    method='POST'
                )
                response = urllib.request.urlopen(request, timeout=30)
                return json.loads(response.read().decode())
            
            result = await loop.run_in_executor(None, fetch)
            
            # Extract text from response
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if len(parts) > 0:
                        return parts[0].get('text', '')
            
            logger.error(f"Gemini unexpected response: {result}")
            return None
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='ignore')
            logger.error(f"Gemini HTTP error {e.code}: {error_body}")
            return None
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None


class OpenRouterProvider(AsyncAIProvider):
    """OpenRouter API - Fully Async (For free models like Gemini)"""
    
    # Bepul modellar ro'yxati (fallback uchun)
    FREE_MODELS = [
        "google/gemini-2.0-flash-exp:free",
        "google/gemini-2.5-flash-preview-05-20",
        "meta-llama/llama-3.2-3b-instruct:free",
        "mistralai/mistral-7b-instruct:free"
    ]
    
    async def generate(self, prompt: str, model: str = None, max_tokens: int = 1000) -> Optional[str]:
        """Generate using OpenRouter API with fallback models"""
        
        # Default model
        if not model:
            model = self.FREE_MODELS[0]
        
        # Try each model until one works
        models_to_try = [model] + [m for m in self.FREE_MODELS if m != model]
        
        for try_model in models_to_try:
            result = await self._try_generate(prompt, try_model, max_tokens)
            if result:
                return result
            logger.warning(f"Model {try_model} muvaffaqiyatsiz, keyingisini sinab ko'rmoqda...")
        
        return None
    
    async def _try_generate(self, prompt: str, model: str, max_tokens: int) -> Optional[str]:
        """Try to generate with a specific model"""
        try:
            import urllib.request
            
            url = "https://openrouter.ai/api/v1/chat/completions"
            
            data = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/ghost-control",
                "X-Title": "Ghost Control Bot"
            }
            
            loop = asyncio.get_event_loop()
            
            def fetch():
                request = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode('utf-8'),
                    headers=headers,
                    method='POST'
                )
                response = urllib.request.urlopen(request, timeout=60)
                return json.loads(response.read().decode())
            
            result = await loop.run_in_executor(None, fetch)
            
            # Extract text
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            
            # Xato xabarini tekshirish
            if 'error' in result:
                logger.error(f"OpenRouter error: {result['error']}")
                return None
            
            return None
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='ignore')
            logger.error(f"OpenRouter HTTP error {e.code}: {error_body}")
            return None
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            return None


# ==================== AI HELPER CLASS ====================
class AIHelper:
    """
    Main AI Helper - 100% Async
    No loop conflicts, no blocking operations
    """
    
    def __init__(self, provider: AsyncAIProvider):
        self.provider = provider
    
    async def generate_response(self, user_message: str) -> str:
        """
        Generate conversational response
        
        Args:
            user_message: User's message
        
        Returns:
            AI response
        """
        try:
            if not user_message:
                return "❌ Bo'sh xabar"
            
            if not self.provider:
                return "❌ AI sozlanmagan. Admin bilan bog'laning."
            
            result = await self.provider.generate(user_message)
            
            if result:
                return result
            else:
                return "❌ AI javob bera olmadi. Iltimos keyinroq urinib ko'ring yoki /ai orqali AI holatini tekshiring."
                
        except Exception as e:
            logger.error(f"Generate response error: {e}")
            return f"❌ AI xatosi: {str(e)}"
    
    async def analyze_text(self, text: str, max_length: int = 500) -> str:
        """Analyze and summarize text"""
        try:
            if not text or len(text) < 10:
                return "❌ Matn tahlil qilish uchun juda qisqa"
            
            prompt = f"""Quyidagi matnni tahlil qiling va {max_length} belgidan kam qilib xulosa bering:

{text[:5000]}

Qisqacha xulosa yozing."""
            
            result = await self.provider.generate(prompt, max_tokens=max_length)
            
            if result:
                return f"📊 **Tahlil:**\n\n{result}"
            else:
                return "❌ AI tahlil qila olmadi"
                
        except Exception as e:
            logger.error(f"Analyze text error: {e}")
            return f"❌ Xato: {str(e)}"
    
    async def explain_error(self, error_text: str) -> str:
        """Explain an error message"""
        try:
            prompt = f"""Quyidagi xato xabarini oddiy tilda tushuntiring va yechimini taklif qiling:

Xato: {error_text}

O'zbek tilida javob bering."""
            
            result = await self.provider.generate(prompt, max_tokens=500)
            
            if result:
                return f"🔍 **Xato tushuntirmasi:**\n\n{result}"
            else:
                return "❌ Xatoni tushuntira olmadim"
                
        except Exception as e:
            logger.error(f"Explain error error: {e}")
            return f"❌ Xato: {str(e)}"


# ==================== GLOBAL INSTANCE ====================
_ai_helper: Optional[AIHelper] = None
_ai_enabled: bool = True

def initialize_ai_helper(provider_type: str = "openrouter", api_key: str = None) -> bool:
    """
    Initialize global AI helper
    
    Args:
        provider_type: "gemini" or "openrouter"
        api_key: API key for the provider
    
    Returns:
        True if successful
    """
    global _ai_helper
    
    try:
        if not api_key:
            logger.warning("API kalit berilmadi")
            return False
        
        if provider_type.lower() == "gemini":
            provider = GeminiProvider(api_key)
        elif provider_type.lower() == "openrouter":
            provider = OpenRouterProvider(api_key)
        else:
            logger.error(f"Noma'lum provider: {provider_type}")
            return False
        
        _ai_helper = AIHelper(provider)
        logger.info(f"AI Helper {provider_type} bilan ishga tushirildi")
        return True
        
    except Exception as e:
        logger.error(f"AI helper ishga tushirish xatosi: {e}")
        return False

def get_ai_helper() -> Optional[AIHelper]:
    """Get global AI helper instance"""
    return _ai_helper

def is_ai_enabled() -> bool:
    """AI yoqilganligini tekshirish"""
    return _ai_enabled and _ai_helper is not None

def enable_ai() -> bool:
    """AI ni yoqish"""
    global _ai_enabled
    _ai_enabled = True
    logger.info("AI yoqildi")
    return True

def disable_ai() -> bool:
    """AI ni o'chirish"""
    global _ai_enabled
    _ai_enabled = False
    logger.info("AI o'chirildi")
    return True