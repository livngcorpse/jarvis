"""
Dispatcher for the Jarvis Telegram bot.
Sets up handlers and routes Telegram updates.
"""

from telegram.ext import Application, MessageHandler, filters
from bot.message_router import route_message
from bot.handlers.health import handle_health_check
from utils.logger import app_logger

def setup_dispatcher(application: Application) -> None:
    """
    Set up the dispatcher with handlers.
    
    Args:
        application: Telegram Application instance
    """
    app_logger.info("Setting up dispatcher")
    
    # Add message handler for all text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_message))
    
    app_logger.info("Dispatcher setup completed")