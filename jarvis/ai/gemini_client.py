"""
Gemini API client for the Jarvis Telegram bot.
Provides wrappers for code generation and intent classification.
"""

import google.generativeai as genai
from typing import Dict, Any, Optional
import json
import time
import logging
from config import GEMINI_API_KEY
from ai.prompts import SYSTEM_CONSTRAINTS, DEV_REQUEST_PROMPT, INTENT_CLASSIFICATION_PROMPT

# Configure logging
logger = logging.getLogger(__name__)

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
            response = self.model.generate_content(prompt)
            # Try to parse as JSON if possible
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                return {"text": response.text}
                
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