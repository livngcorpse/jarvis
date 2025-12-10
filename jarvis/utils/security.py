"""
Security utilities for the Jarvis Telegram bot.
Includes admin checks and path sanitization.
"""

import os
from pathlib import Path
from config import ADMIN_IDS, ALLOWED_ROOT_PATH

def is_admin(user_id: int) -> bool:
    """
    Check if a user ID is in the admin list.
    
    Args:
        user_id: Telegram user ID to check
        
    Returns:
        True if user is admin, False otherwise
    """
    return user_id in ADMIN_IDS

def sanitize_path(path: str) -> str:
    """
    Sanitize a file path to prevent directory traversal.
    
    Args:
        path: Path to sanitize
        
    Returns:
        Sanitized path
    """
    # Normalize the path to resolve any '..' or '.'
    normalized = os.path.normpath(path)
    
    # Remove leading slashes to prevent absolute paths
    normalized = normalized.lstrip('/')
    
    return normalized

def is_path_allowed(path: str) -> bool:
    """
    Check if a path is within the allowed root directory.
    
    Args:
        path: Path to check
        
    Returns:
        True if path is allowed, False otherwise
    """
    try:
        # Resolve the full path
        full_path = Path(path).resolve()
        
        # Check if the path is within the allowed root
        return ALLOWED_ROOT_PATH in full_path.parents or ALLOWED_ROOT_PATH == full_path
    except Exception:
        return False