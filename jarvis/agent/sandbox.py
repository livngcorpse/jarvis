"""
Sandbox enforcement for the Jarvis Telegram bot.
Ensures file operations stay within allowed boundaries.
"""

import os
from pathlib import Path
from config import ALLOWED_ROOT_PATH
from utils.security import is_path_allowed
from utils.logger import app_logger

# Maximum file size allowed (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB in bytes

def check_target_path(target_path: str) -> bool:
    """
    Check if a target path is allowed within the sandbox.
    
    Args:
        target_path: Path to check
        
    Returns:
        True if path is allowed, False otherwise
        
    Raises:
        ValueError: If path is not allowed
    """
    # Resolve the full path
    full_path = Path(target_path).resolve()
    
    # Check if path is within allowed root
    if not is_path_allowed(full_path):
        app_logger.error(f"Path {full_path} is outside allowed root {ALLOWED_ROOT_PATH}")
        raise ValueError(f"Path {full_path} is outside allowed root {ALLOWED_ROOT_PATH}")
    
    # Check file size if file exists
    if full_path.exists() and full_path.is_file():
        file_size = full_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            app_logger.error(f"File {full_path} exceeds maximum size limit ({file_size} > {MAX_FILE_SIZE})")
            raise ValueError(f"File {full_path} exceeds maximum size limit ({file_size} > {MAX_FILE_SIZE})")
    
    # Check for symlinks that escape sandbox
    try:
        if full_path.is_symlink():
            link_target = Path(os.readlink(full_path)).resolve()
            if not is_path_allowed(link_target):
                app_logger.error(f"Symlink {full_path} points outside allowed root")
                raise ValueError(f"Symlink {full_path} points outside allowed root")
    except (OSError, ValueError):
        # If we can't check the symlink, reject it
        app_logger.error(f"Cannot verify symlink {full_path}")
        raise ValueError(f"Cannot verify symlink {full_path}")
    
    return True

def enforce_sandbox(target_paths: list) -> None:
    """
    Enforce sandbox rules on a list of target paths.
    
    Args:
        target_paths: List of paths to check
        
    Raises:
        ValueError: If any path is not allowed
    """
    for path in target_paths:
        check_target_path(path)
        
    app_logger.info(f"All {len(target_paths)} paths passed sandbox check")