"""
Health check handler for the Jarvis Telegram bot.
"""

from telegram import Update
from telegram.ext import ContextTypes
from utils.logger import app_logger

async def handle_health_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle health check requests.
    
    Args:
        update: Telegram update object
        context: Telegram context object
    """
    app_logger.info("Health check requested")
    await update.message.reply_text("Jarvis bot is running and healthy!")