"""
Normal chat handlers for the Jarvis Telegram bot.
Handles conversational responses for non-admin users.
"""

from telegram import Update
from telegram.ext import ContextTypes
from ai.gemini_client import gemini_client
from utils.logger import app_logger

async def handle_normal_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle normal chat messages from users.
    
    Args:
        update: Telegram update object
        context: Telegram context object
    """
    user_message = update.message.text
    user_id = update.effective_user.id
    
    app_logger.info(f"Handling normal chat from user {user_id}: {user_message}")
    
    try:
        # Use Gemini to generate a friendly response
        prompt = f"""
        You are Jarvis, a helpful AI assistant. Respond to the user's message in a friendly and informative way.
        User message: {user_message}
        """
        
        response = gemini_client.model.generate_content(prompt)
        
        await update.message.reply_text(response.text)
    except Exception as e:
        app_logger.error(f"Error handling normal chat: {e}")
        await update.message.reply_text("Sorry, I encountered an error while processing your message.")

def reply_to_text(text: str) -> str:
    """
    Simple function to generate a reply to text (used for testing).
    
    Args:
        text: Input text
        
    Returns:
        Generated reply
    """
    # Simple hardcoded response for testing
    return f"I received your message: '{text}'. I'm Jarvis, your AI assistant!"