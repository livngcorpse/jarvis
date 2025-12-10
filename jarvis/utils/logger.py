"""
Logger utility for the Jarvis Telegram bot.
"""

import logging
import os
from config import LOG_LEVEL

def setup_logger(name: str, log_file: str = None, level: str = None) -> logging.Logger:
    """
    Set up a logger with the specified name and log file.
    
    Args:
        name: Name of the logger
        log_file: Path to the log file (optional)
        level: Logging level (defaults to config.LOG_LEVEL)
        
    Returns:
        Configured logger instance
    """
    if level is None:
        level = LOG_LEVEL
        
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Prevent adding multiple handlers if logger already exists
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file is specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

# Default logger for the application
app_logger = setup_logger("jarvis")