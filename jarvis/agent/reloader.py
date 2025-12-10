"""
Reloader module for the Jarvis Telegram bot.
Handles soft reloads and full restarts.
"""

import sys
import os
import importlib
from typing import List
from config import RELOAD_CRITICAL_FILES
from utils.logger import app_logger

# Exit codes for different restart reasons
EXIT_CODE_NORMAL_RESTART = 0
EXIT_CODE_CRITICAL_FILE_CHANGED = 42
EXIT_CODE_DEPENDENCY_CHANGED = 43

def soft_reload(changed_modules: List[str]) -> bool:
    """
    Perform a soft reload of specified modules.
    
    Args:
        changed_modules: List of module names to reload
        
    Returns:
        True if reload successful, False otherwise
    """
    try:
        for module_name in changed_modules:
            if module_name in sys.modules:
                app_logger.info(f"Reloading module: {module_name}")
                importlib.reload(sys.modules[module_name])
            else:
                app_logger.warning(f"Module {module_name} not found in sys.modules")
                
        app_logger.info("Soft reload completed successfully")
        return True
    except Exception as e:
        app_logger.error(f"Soft reload failed: {e}")
        return False

def full_restart() -> None:
    """
    Perform a full restart of the application.
    """
    app_logger.info("Performing full restart...")
    try:
        # Use os.execv to restart the process with the same arguments
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        app_logger.error(f"Full restart failed: {e}")
        # If execv fails, exit with restart code
        sys.exit(EXIT_CODE_NORMAL_RESTART)

def determine_reload_type(changed_files: List[str]) -> str:
    """
    Determine whether to perform a soft reload or full restart.
    
    Args:
        changed_files: List of changed file paths
        
    Returns:
        "soft" for soft reload, "full" for full restart
    """
    # Check if any critical files were changed
    for file_path in changed_files:
        file_name = os.path.basename(file_path)
        if file_name in RELOAD_CRITICAL_FILES:
            app_logger.info(f"Critical file {file_name} changed, triggering full restart")
            return "full"
            
    # Check if requirements.txt was changed (new dependencies)
    if "requirements.txt" in [os.path.basename(f) for f in changed_files]:
        app_logger.info("Requirements file changed, triggering full restart")
        return "full"
        
    app_logger.info("Non-critical files changed, triggering soft reload")
    return "soft"

def health_check() -> bool:
    """
    Perform a basic health check.
    
    Returns:
        True if healthy, False otherwise
    """
    # Simple health check - verify we can import core modules
    try:
        import bot.handlers.normal_chat
        import bot.dispatcher
        app_logger.info("Health check passed")
        return True
    except Exception as e:
        app_logger.error(f"Health check failed: {e}")
        return False