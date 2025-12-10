"""
Configuration module for the Jarvis Telegram bot.
Loads environment variables and defines constants.
"""

import os
from pathlib import Path

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Parse ADMIN_IDS as a list of integers
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(",") if id.strip().isdigit()]

# Define project paths
PROJECT_ROOT = Path(__file__).parent.absolute()
ALLOWED_ROOT = os.getenv("ALLOWED_ROOT", str(PROJECT_ROOT))
ALLOWED_ROOT_PATH = Path(ALLOWED_ROOT).resolve()

# Define critical files that trigger full restart
RELOAD_CRITICAL_FILES = {
    "main.py",
    "jarvis/config.py",
    "requirements.txt"
}

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Timeouts
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
RELOAD_TIMEOUT = int(os.getenv("RELOAD_TIMEOUT", "10"))