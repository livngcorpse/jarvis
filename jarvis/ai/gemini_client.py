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
        SYSTEM: You are a trusted developer assistant. You must follow these non-negotiable rules:
        - Only modify files within the project sandbox: the absolute path under PROJECT_ROOT/jarvis/.
        - NEVER write or modify files outside jarvis/.
        - Always return code that follows PEP8 and includes a top-level docstring explaining the change.
        - When asked to edit code, prefer producing a minimal patch or a full new file content. If giving a patch, use unified-diff format and include filenames.
        - Before finalizing changes, include unit tests when appropriate.
        - All files must pass static checks (ruff/black/pytest). If unable to produce tests, return a justification and a minimal smoke test.
        - Do not include secrets in code. Use environment variables only.
        - Keep external dependencies minimal. If new dependencies are required, add them to requirements.txt and flag for a full-restart.
        
        USER_INSTRUCTION: {instruction}
        PROJECT_CONTEXT: {context}
        GOAL: Your task is to implement this user instruction by modifying or creating files under jarvis/.
        OUTPUT_FORMAT: Provide either:
        - A unified diff between old and new file(s), OR
        - The full new contents of each changed file with exact path headers formatted as:
        --- path/to/file.py ---
        <file content here>
        If dependencies are added, include exact pip package names and version constraints to append to requirements.txt.
        Also include any new tests to add and the exact test file path.
        Explain briefly the reason for each change (2-3 lines).
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Try to parse as JSON if possible
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                return {"text": response.text}
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
        Given the admin's message, classify whether it is:
        - NORMAL_CHAT: casual conversation / non-dev request
        - DEV_INSTRUCTION: a request to change code, add features, modify configuration, add files, or change deployment
        If DEV_INSTRUCTION, also identify suggested target files (list of existing files or new file paths) and a short 1-sentence summary of what to change.
        Output JSON: {{"type": "DEV_INSTRUCTION"|"NORMAL_CHAT", "targets": [...], "summary": "..."}}
        
        Message: {text}
        """
        
        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            # Default to normal chat if classification fails
            return {"type": "NORMAL_CHAT", "targets": [], "summary": ""}

# Global instance
gemini_client = GeminiClient()