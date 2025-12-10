"""
Admin interpreter for the Jarvis Telegram bot.
Determines if admin messages are instructions or normal chat.
"""

from typing import Dict, Any, Optional
from ai.gemini_client import gemini_client
from utils.logger import app_logger

async def classify_admin_message(message_text: str) -> Dict[str, Any]:
    """
    Classify an admin message as either a dev instruction or normal chat.
    
    Args:
        message_text: The text of the message to classify
        
    Returns:
        Dictionary with classification result
    """
    app_logger.info(f"Classifying admin message: {message_text[:50]}...")
    
    try:
        result = gemini_client.classify_intent(message_text)
        app_logger.info(f"Classification result: {result}")
        return result
    except Exception as e:
        app_logger.error(f"Error classifying admin message: {e}")
        # Default to normal chat if classification fails
        return {
            "type": "NORMAL_CHAT",
            "targets": [],
            "summary": ""
        }

def is_dev_instruction(classification: Dict[str, Any]) -> bool:
    """
    Check if a classification result indicates a dev instruction.
    
    Args:
        classification: Classification result
        
    Returns:
        True if it's a dev instruction, False otherwise
    """
    return classification.get("type") == "DEV_INSTRUCTION"