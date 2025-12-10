"""
Reloader module for the Jarvis Telegram bot.
Handles soft reloads and full restarts.
"""

import sys
import os
import importlib
from typing import List, Dict, Any
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

def full_restart(exit_code: int = EXIT_CODE_NORMAL_RESTART) -> None:
    """
    Perform a full restart of the application.
    
    Args:
        exit_code: Exit code to use when restarting
    """
    app_logger.info("Performing full restart...")
    try:
        # Use os.execv to restart the process with the same arguments
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        app_logger.error(f"Full restart failed: {e}")
        # If execv fails, exit with restart code
        sys.exit(exit_code)

def determine_reload_type(changes: Dict[str, Any]) -> str:
    """
    Determine whether to perform a soft reload or full restart based on changes.
    
    Args:
        changes: Dictionary with file changes information
        
    Returns:
        "soft" for soft reload, "full" for full restart
    """
    changed_files = changes.get("changed_files", [])
    dependencies_changed = changes.get("dependencies_changed", False)
    
    # Check if any critical files were changed
    for file_path in changed_files:
        # Check both the full path and basename for critical files
        if file_path in RELOAD_CRITICAL_FILES or os.path.basename(file_path) in RELOAD_CRITICAL_FILES:
            app_logger.info(f"Critical file {file_path} changed, triggering full restart")
            return "full"
            
    # Check if requirements.txt was changed (new dependencies)
    if dependencies_changed or "requirements.txt" in [os.path.basename(f) for f in changed_files]:
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
        # Try to call a simple function to verify functionality
        from bot.handlers.normal_chat import reply_to_text
        test_response = reply_to_text("health check")
        if not isinstance(test_response, str) or len(test_response) == 0:
            raise Exception("Health check function returned invalid response")
        app_logger.info("Health check passed")
        return True
    except Exception as e:
        app_logger.error(f"Health check failed: {e}")
        return False

def verify_reload_success() -> bool:
    """
    Verify that the reload was successful by performing a health check.
    
    Returns:
        True if verification passes, False otherwise
    """
    # Wait a moment for reload to complete
    import time
    time.sleep(1)
    
    # Perform health check
    return health_check()
