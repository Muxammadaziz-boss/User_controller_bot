# services/ai_service.py - v3.0.5 AI Service
"""
AI helper xizmati:
- AI provider wrapper
- Context management
- Error handling
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AIService:
    """AI helper service - wrapper for ai_helper module"""
    
    def __init__(self, use_openrouter: bool = True, 
                 openrouter_key: str = "", 
                 gemini_key: str = "",
                 model: str = "google/gemini-2.0-flash-exp:free"):
        """
        Args:
            use_openrouter: True for OpenRouter, False for Gemini
            openrouter_key: OpenRouter API key
            gemini_key: Gemini API key
            model: Model name for OpenRouter
        """
        self.use_openrouter = use_openrouter
        self.openrouter_key = openrouter_key
        self.gemini_key = gemini_key
        self.model = model
        self._enabled = False
        self._initialized = False
        self._provider_type = None
    
    def initialize(self) -> bool:
        """AI provider'ni ishga tushirish"""
        try:
            from ai_helper import initialize_ai
            
            if self.use_openrouter and self.openrouter_key:
                success = initialize_ai(
                    use_openrouter=True,
                    openrouter_key=self.openrouter_key,
                    openrouter_model=self.model
                )
                if success:
                    self._provider_type = "OpenRouter"
                    self._initialized = True
                    self._enabled = True
                    logger.info("AI initialized with OpenRouter")
                    return True
            
            # Fallback to Gemini
            if self.gemini_key:
                success = initialize_ai(
                    use_openrouter=False,
                    gemini_key=self.gemini_key
                )
                if success:
                    self._provider_type = "Gemini"
                    self._initialized = True
                    self._enabled = True
                    logger.info("AI initialized with Gemini")
                    return True
            
            logger.warning("No AI API key configured")
            return False
            
        except Exception as e:
            logger.error(f"AI initialization error: {e}")
            return False
    
    async def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        AI bilan suhbat
        
        Args:
            message: Foydalanuvchi xabari
            context: Qo'shimcha kontekst
        
        Returns:
            AI javobi
        """
        if not self._enabled or not self._initialized:
            return "❌ AI yoqilmagan yoki ishga tushmagan"
        
        try:
            from ai_helper import ai_chat
            response = await ai_chat(message, context or {})
            return response
        except Exception as e:
            logger.error(f"AI chat error: {e}")
            return f"❌ AI xatosi: {str(e)}"
    
    async def explain_error(self, error: str) -> str:
        """Xatoni tushuntirish"""
        if not self._enabled:
            return "AI o'chirilgan"
        
        try:
            from ai_helper import ai_explain_error
            return await ai_explain_error(error)
        except Exception as e:
            logger.error(f"AI explain error: {e}")
            return f"Xato: {str(e)}"
    
    def enable(self):
        """AI yoqish"""
        if self._initialized:
            self._enabled = True
            try:
                from ai_helper import enable_ai
                enable_ai()
            except:
                pass
            logger.info("AI enabled")
    
    def disable(self):
        """AI o'chirish"""
        self._enabled = False
        try:
            from ai_helper import disable_ai
            disable_ai()
        except:
            pass
        logger.info("AI disabled")
    
    @property
    def is_enabled(self) -> bool:
        """AI yoqilganmi?"""
        return self._enabled and self._initialized
    
    def get_status(self) -> Dict[str, Any]:
        """AI status"""
        return {
            'enabled': self._enabled,
            'initialized': self._initialized,
            'provider': self._provider_type,
            'model': self.model if self.use_openrouter else 'gemini-1.5-flash'
        }
