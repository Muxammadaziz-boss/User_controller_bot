# ai_helper.py - PRODUCTION READY (No loop conflicts)
"""
AI Helper Module - Fully Async
No more RuntimeError: This event loop is already running
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
        """
        Generate AI response asynchronously
        
        Args:
            prompt: User prompt
            **kwargs: Additional parameters
        
        Returns:
            Generated text or None on error
        """
        raise NotImplementedError("Subclass must implement generate()")


class AnthropicProvider(AsyncAIProvider):
    """Anthropic Claude API - Fully Async"""
    
    async def generate(self, prompt: str, model: str = "claude-sonnet-4-20250514", max_tokens: int = 1000) -> Optional[str]:
        """Generate using Claude API"""
        try:
            import urllib.request
            import urllib.parse
            
            url = "https://api.anthropic.com/v1/messages"
            
            data = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            
            # Run in executor to avoid blocking
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
            if 'content' in result and len(result['content']) > 0:
                return result['content'][0].get('text', '')
            
            return None
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return None


class OpenAIProvider(AsyncAIProvider):
    """OpenAI GPT API - Fully Async"""
    
    async def generate(self, prompt: str, model: str = "gpt-4", max_tokens: int = 1000) -> Optional[str]:
        """Generate using OpenAI API"""
        try:
            import urllib.request
            
            url = "https://api.openai.com/v1/chat/completions"
            
            data = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
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
            
            # Extract text
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            
            return None
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None


class OpenRouterProvider(AsyncAIProvider):
    """OpenRouter API - Fully Async (For free models like Gemini)"""
    
    async def generate(self, prompt: str, model: str = "google/gemini-2.0-flash-exp:free", max_tokens: int = 1000) -> Optional[str]:
        """Generate using OpenRouter API"""
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
    
    async def analyze_text(self, text: str, max_length: int = 500) -> str:
        """
        Analyze and summarize text
        
        Args:
            text: Text to analyze
            max_length: Maximum output length
        
        Returns:
            Summary or error message
        """
        try:
            if not text or len(text) < 10:
                return "❌ Text too short to analyze"
            
            prompt = f"""Analyze and summarize the following text in {max_length} characters or less:

{text[:5000]}

Provide a concise summary."""
            
            result = await self.provider.generate(prompt, max_tokens=max_length)
            
            if result:
                return f"📊 **Analysis:**\n\n{result}"
            else:
                return "❌ AI analysis failed"
                
        except Exception as e:
            logger.error(f"Analyze text error: {e}")
            return f"❌ Error: {str(e)}"
    
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
                return "❌ Empty message"
            
            result = await self.provider.generate(user_message)
            
            if result:
                return result
            else:
                return "❌ Failed to generate response"
                
        except Exception as e:
            logger.error(f"Generate response error: {e}")
            return f"❌ Error: {str(e)}"
    
    async def explain_code(self, code: str) -> str:
        """
        Explain code snippet
        
        Args:
            code: Code to explain
        
        Returns:
            Explanation
        """
        try:
            if not code:
                return "❌ No code provided"
            
            prompt = f"""Explain what this code does in simple terms:

```
{code[:2000]}
```

Provide a clear, concise explanation."""
            
            result = await self.provider.generate(prompt, max_tokens=800)
            
            if result:
                return f"💡 **Code Explanation:**\n\n{result}"
            else:
                return "❌ Failed to explain code"
                
        except Exception as e:
            logger.error(f"Explain code error: {e}")
            return f"❌ Error: {str(e)}"
    
    async def translate_text(self, text: str, target_language: str = "English") -> str:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_language: Target language name
        
        Returns:
            Translated text
        """
        try:
            if not text:
                return "❌ No text to translate"
            
            prompt = f"""Translate the following text to {target_language}. Only provide the translation, no explanations:

{text[:2000]}"""
            
            result = await self.provider.generate(prompt, max_tokens=1000)
            
            if result:
                return f"🌐 **Translation ({target_language}):**\n\n{result}"
            else:
                return "❌ Translation failed"
                
        except Exception as e:
            logger.error(f"Translate error: {e}")
            return f"❌ Error: {str(e)}"


# ==================== GLOBAL INSTANCE ====================
_ai_helper: Optional[AIHelper] = None
_ai_enabled: bool = True  # AI yoqilgan/o'chirilgan holati

def initialize_ai_helper(provider_type: str = "openrouter", api_key: str = None) -> bool:
    """
    Initialize global AI helper
    
    Args:
        provider_type: "anthropic", "openai", or "openrouter"
        api_key: API key for the provider
    
    Returns:
        True if successful
    """
    global _ai_helper
    
    try:
        if not api_key:
            logger.warning("No API key provided")
            return False
        
        if provider_type.lower() == "anthropic":
            provider = AnthropicProvider(api_key)
        elif provider_type.lower() == "openai":
            provider = OpenAIProvider(api_key)
        elif provider_type.lower() == "openrouter":
            provider = OpenRouterProvider(api_key)
        else:
            logger.error(f"Unknown provider: {provider_type}")
            return False
        
        _ai_helper = AIHelper(provider)
        logger.info(f"AI Helper initialized with {provider_type}")
        return True
        
    except Exception as e:
        logger.error(f"Initialize AI helper error: {e}")
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
    logger.info("AI enabled")
    return True

def disable_ai() -> bool:
    """AI ni o'chirish"""
    global _ai_enabled
    _ai_enabled = False
    logger.info("AI disabled")
    return True


# ==================== TELEGRAM HANDLER INTEGRATION ====================
async def handle_ai_request(event, command: str, text: str):
    """
    Handle AI requests from Telegram
    
    Args:
        event: Telegram event
        command: Command type (analyze, explain, translate, chat)
        text: Input text
    
    Usage in handlers.py:
        if data == "ai_analyze":
            await handle_ai_request(event, "analyze", user_text)
    """
    try:
        ai = get_ai_helper()
        
        if not ai:
            await event.reply("❌ AI Helper not initialized!\n\nContact admin to configure API keys.")
            return
        
        # Show processing message
        msg = await event.reply("🤖 **AI Processing...**\n\n⏳ Please wait...")
        
        # Process based on command
        if command == "analyze":
            result = await ai.analyze_text(text)
        elif command == "explain":
            result = await ai.explain_code(text)
        elif command == "translate":
            result = await ai.translate_text(text)
        elif command == "chat":
            result = await ai.generate_response(text)
        else:
            result = "❌ Unknown command"
        
        # Edit message with result
        await event.client.edit_message(event.chat_id, msg.id, result)
        
    except Exception as e:
        logger.error(f"AI request handler error: {e}")
        await event.reply(f"❌ AI Error:\n```\n{str(e)}\n```")


# ==================== USAGE EXAMPLES ====================
"""
# In main.py or bot initialization:
from ai_helper import initialize_ai_helper

# Initialize with your API key
initialize_ai_helper("anthropic", "sk-ant-...")

# In handlers.py:
from ai_helper import get_ai_helper, handle_ai_request

async def some_handler(event):
    ai = get_ai_helper()
    if ai:
        result = await ai.analyze_text("Some text to analyze")
        await event.reply(result)

# Or use the integrated handler:
if event.text.startswith("/ai"):
    text = event.text[4:].strip()
    await handle_ai_request(event, "chat", text)
"""