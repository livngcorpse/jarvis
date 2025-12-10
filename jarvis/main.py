"""
Main launcher for the Jarvis Telegram bot.
Connects to Telegram, sets up handlers, and starts the bot.
"""

import asyncio
import signal
import sys
from telegram.ext import Application
from config import TELEGRAM_TOKEN
from bot.dispatcher import setup_dispatcher
from utils.logger import app_logger

# Global variable to hold the application instance
application = None

async def shutdown(signal_num: int, app: Application) -> None:
    """
    Shutdown the bot gracefully.
    
    Args:
        signal_num: Signal number
        app: Telegram Application instance
    """
    app_logger.info(f"Received exit signal {signal_num.name}...")
    
    # Stop the application
    await app.stop()
    await app.shutdown()
    
    app_logger.info("Bot shut down gracefully")

async def main() -> None:
    """Main function to run the bot."""
    global application
    
    app_logger.info("Starting Jarvis Telegram bot...")
    
    if not TELEGRAM_TOKEN:
        app_logger.error("TELEGRAM_TOKEN not set in environment variables")
        sys.exit(1)
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Set up dispatcher
    setup_dispatcher(application)
    
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig, 
            lambda s=sig: asyncio.create_task(shutdown(s, application))
        )
    
    # Start the bot
    app_logger.info("Starting bot polling...")
    await application.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        app_logger.info("Bot interrupted by user")
    except Exception as e:
        app_logger.error(f"Bot crashed with error: {e}")
        sys.exit(1)