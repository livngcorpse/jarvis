"""
File operations utilities for the Jarvis Telegram bot.
Includes atomic write, backup, and restore helpers.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Union
from utils.logger import app_logger

def atomic_write(path: Union[str, Path], content: str) -> None:
    """
    Write content to a file atomically.
    
    Args:
        path: Path to the file
        content: Content to write
    """
    path = Path(path)
    
    # Create parent directories if they don't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to a temporary file first
    with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=path.parent) as tmp_file:
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    # Atomically replace the target file
    try:
        os.replace(tmp_path, path)
    except Exception:
        # Clean up the temporary file if replacement fails
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

def backup(paths: List[Union[str, Path]], dest_dir: Union[str, Path]) -> None:
    """
    Create backups of files.
    
    Args:
        paths: List of file paths to backup
        dest_dir: Destination directory for backups
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    for path in paths:
        path = Path(path)
        if path.exists():
            # Preserve directory structure in backup
            rel_path = path.relative_to(path.anchor) if path.is_absolute() else path
            backup_path = dest_dir / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            if path.is_file():
                shutil.copy2(path, backup_path)
            elif path.is_dir():
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                shutil.copytree(path, backup_path)
                
            app_logger.info(f"Backed up {path} to {backup_path}")

def restore(backup_dir: Union[str, Path], target_dir: Union[str, Path]) -> None:
    """
    Restore files from a backup directory.
    
    Args:
        backup_dir: Directory containing backups
        target_dir: Target directory to restore to
    """
    backup_dir = Path(backup_dir)
    target_dir = Path(target_dir)
    
    if not backup_dir.exists():
        raise FileNotFoundError(f"Backup directory {backup_dir} does not exist")
    
    # Copy all files from backup to target
    for item in backup_dir.rglob('*'):
        if item.is_file():
            rel_path = item.relative_to(backup_dir)
            target_path = target_dir / rel_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target_path)
            
    app_logger.info(f"Restored from {backup_dir} to {target_dir}")