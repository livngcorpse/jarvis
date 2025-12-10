"""
Gemini API client for the Jarvis Telegram bot.
Provides wrappers for code generation and intent classification.
"""

import google.generativeai as genai
from typing import Dict, Any, Optional
import json
import time
import logging
import threading
from config import GEMINI_API_KEY
from ai.prompts import SYSTEM_CONSTRAINTS, DEV_REQUEST_PROMPT, INTENT_CLASSIFICATION_PROMPT

# Configure logging
logger = logging.getLogger(__name__)

# Rate limiting variables
_rate_limit_lock = threading.Lock()
_last_call_time = 0
_min_call_interval = 1.0  # Minimum interval between calls in seconds

# Configure the Gemini API client
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class GeminiClient:
    """A client for interacting with the Gemini API."""
    
    def __init__(self):
        """Initialize the Gemini client."""
        self.model = None
        if GEMINI_API_KEY:
            self.model = genai.GenerativeModel('gemini-pro')
    
    def _rate_limit(self):
        """
        Enforce rate limiting between API calls.
        """
        global _last_call_time
        with _rate_limit_lock:
            current_time = time.time()
            time_since_last_call = current_time - _last_call_time
            if time_since_last_call < _min_call_interval:
                sleep_time = _min_call_interval - time_since_last_call
                time.sleep(sleep_time)
            _last_call_time = time.time()
    
    def _retry_with_backoff(self, func, max_retries=3, base_delay=1):
        """
        Retry a function with exponential backoff.
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds
            
        Returns:
            Result of the function call
        """
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
    
    def generate_code_update(self, context: str, instruction: str) -> Dict[str, Any]:
        """
        Generate code updates based on context and instruction.
        
        Args:
            context: Current project context
            instruction: Admin instruction to implement
            
        Returns:
            Dictionary with generated code updates
        """
        if not self.model:
            raise ValueError("Gemini API key not configured")
            
        prompt = f"""
        {SYSTEM_CONSTRAINTS}
        
        {DEV_REQUEST_PROMPT.format(admin_text=instruction, project_context=context)}
        """
        
        def _call_api():
            self._rate_limit()  # Enforce rate limiting
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
                
        try:
            return self._retry_with_backoff(_call_api)
        except Exception as e:
            logger.error(f"Error generating code update: {e}")
            raise
    
    def classify_intent(self, text: str) -> Dict[str, Any]:
        """
        Classify whether a message is normal chat or a dev instruction.
        
        Args:
            text: The text to classify
            
        Returns:
            Dictionary with classification result
        """
        if not self.model:
            raise ValueError("Gemini API key not configured")
            
        prompt = f"""
        {SYSTEM_CONSTRAINTS}
        
        {INTENT_CLASSIFICATION_PROMPT}
        
        Message: {text}
        """
        
        def _call_api():
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
            
        try:
            return self._retry_with_backoff(_call_api)
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            # Default to normal chat if classification fails
            return {"type": "NORMAL_CHAT", "targets": [], "summary": ""}

# Global instance
gemini_client = GeminiClient()