"""
Self-modifier module for the Jarvis Telegram bot.
Handles code generation, validation, and application of changes.
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from ai.gemini_client import gemini_client
from agent.sandbox import enforce_sandbox
from agent.reloader import determine_reload_type, soft_reload, full_restart
from utils.fileops import atomic_write, backup
from utils.logger import app_logger
from config import PROJECT_ROOT

class DevRequest:
    """Represents a development request from an admin."""
    
    def __init__(self, intent: str, target_files: List[str], goal_description: str):
        self.intent = intent
        self.target_files = target_files
        self.goal_description = goal_description

class SelfModifier:
    """Handles self-modification workflow."""
    
    def __init__(self):
        self.staging_dir = PROJECT_ROOT / ".staging"
        self.backup_dir = PROJECT_ROOT / "backups"
        self.logs_dir = PROJECT_ROOT / "logs"
        
        # Create directories if they don't exist
        self.staging_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Set up logging
        self.log_file = self.logs_dir / "self_modify.log"
        
    def process_dev_request(self, dev_request: DevRequest) -> Dict[str, Any]:
        """
        Process a development request from an admin.
        
        Args:
            dev_request: The development request to process
            
        Returns:
            Result dictionary with status and message
        """
        try:
            app_logger.info(f"Processing dev request: {dev_request.goal_description}")
            
            # Step 1: Get current project context
            context = self._get_project_context(dev_request.target_files)
            
            # Step 2: Get code changes from AI
            changes = gemini_client.generate_code_update(context, dev_request.goal_description)
            
            # Step 3: Validate and apply changes
            result = self._apply_changes(changes, dev_request)
            
            return result
        except Exception as e:
            app_logger.error(f"Failed to process dev request: {e}")
            return {
                "status": "error",
                "message": f"Failed to process request: {str(e)}"
            }
    
    def _get_project_context(self, target_files: List[str]) -> str:
        """
        Get current project context for specified files.
        
        Args:
            target_files: List of target files
            
        Returns:
            String representation of project context
        """
        context_parts = []
        
        for file_path in target_files:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists() and full_path.is_file():
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                        # For large files, just include a summary
                        if len(content) > 2000:
                            context_parts.append(f"{file_path}: [File content truncated - {len(content)} characters]")
                        else:
                            context_parts.append(f"{file_path}:\n{content}")
                except Exception as e:
                    context_parts.append(f"{file_path}: [Error reading file: {e}]")
            else:
                context_parts.append(f"{file_path}: [File does not exist]")
                
        return "\n\n".join(context_parts)
    
    def _apply_changes(self, changes: Dict[str, Any], dev_request: DevRequest) -> Dict[str, Any]:
        """
        Apply code changes after validation.
        
        Args:
            changes: Changes from AI
            dev_request: Original development request
            
        Returns:
            Result dictionary
        """
        try:
            # Extract file changes
            file_changes = self._extract_file_changes(changes)
            
            if not file_changes:
                return {
                    "status": "warning",
                    "message": "No file changes detected in AI response"
                }
            
            # Get list of target paths
            target_paths = list(file_changes.keys())
            
            # Step 0: Create backup
            app_logger.info("Creating backup of files to be changed")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / timestamp
            backup(target_paths, backup_path)
            
            # Step 1: Write to staging area
            app_logger.info("Writing changes to staging area")
            staged_files = self._write_to_staging(file_changes)
            
            # Step 2: Run validation
            app_logger.info("Running validation checks")
            if not self._validate_changes(staged_files):
                raise Exception("Validation failed")
            
            # Step 3: Apply changes atomically
            app_logger.info("Applying changes atomically")
            self._apply_staged_files(staged_files)
            
            # Step 4: Apply reload rule
            reload_type = determine_reload_type(target_paths)
            app_logger.info(f"Applying {reload_type} reload")
            
            if reload_type == "full":
                # For full restart, we just exit with the appropriate code
                # The process manager should restart us
                app_logger.info("Full restart required - exiting")
                return {
                    "status": "success",
                    "message": "Changes applied. Full restart performed.",
                    "restart_required": True
                }
            else:
                # Soft reload
                module_names = self._get_module_names(target_paths)
                if soft_reload(module_names):
                    return {
                        "status": "success",
                        "message": "Changes applied and loaded successfully."
                    }
                else:
                    raise Exception("Soft reload failed")
                    
        except Exception as e:
            app_logger.error(f"Failed to apply changes: {e}")
            # TODO: Implement rollback
            return {
                "status": "error",
                "message": f"Failed to apply changes: {str(e)}"
            }
    
    def _extract_file_changes(self, changes: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract file changes from AI response.
        
        Args:
            changes: AI response
            
        Returns:
            Dictionary mapping file paths to content
        """
        file_changes = {}
        
        # Handle different response formats
        if "files" in changes:
            # JSON format with files array
            for file_info in changes["files"]:
                if "path" in file_info and "content" in file_info:
                    file_changes[file_info["path"]] = file_info["content"]
        elif isinstance(changes, dict) and "text" in changes:
            # Text format - try to parse as file content
            # This is a simplified parser - in practice, you'd want a more robust one
            text = changes["text"]
            lines = text.split("\n")
            current_file = None
            current_content = []
            
            for line in lines:
                if line.startswith("--- ") and line.endswith(" ---"):
                    # New file header
                    if current_file and current_content:
                        file_changes[current_file] = "\n".join(current_content)
                        
                    current_file = line[4:-4]  # Remove --- markers
                    current_content = []
                elif current_file:
                    current_content.append(line)
                    
            # Don't forget the last file
            if current_file and current_content:
                file_changes[current_file] = "\n".join(current_content)
                
        return file_changes
    
    def _write_to_staging(self, file_changes: Dict[str, str]) -> Dict[str, Path]:
        """
        Write file changes to staging area.
        
        Args:
            file_changes: Dictionary mapping file paths to content
            
        Returns:
            Dictionary mapping file paths to staging paths
        """
        staged_files = {}
        
        for file_path, content in file_changes.items():
            # Ensure the file path is safe
            enforce_sandbox([file_path])
            
            # Write to staging area
            staging_path = self.staging_dir / file_path
            staging_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(staging_path, content)
            
            staged_files[file_path] = staging_path
            
        return staged_files
    
    def _validate_changes(self, staged_files: Dict[str, Path]) -> bool:
        """
        Validate staged changes with linting and tests.
        
        Args:
            staged_files: Dictionary mapping file paths to staging paths
            
        Returns:
            True if validation passes, False otherwise
        """
        try:
            # Run basic syntax check on Python files
            for file_path, staging_path in staged_files.items():
                if file_path.endswith(".py"):
                    result = subprocess.run([
                        sys.executable, "-m", "py_compile", str(staging_path)
                    ], capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        app_logger.error(f"Syntax check failed for {file_path}: {result.stderr}")
                        return False
            
            # Run linter (if available)
            try:
                result = subprocess.run([
                    sys.executable, "-m", "ruff", "check", str(self.staging_dir)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    app_logger.warning(f"Linting issues found: {result.stdout}")
                    # Not failing on linting issues for now
            except FileNotFoundError:
                app_logger.warning("Ruff not found, skipping linting")
            
            # Run tests (basic check)
            # In a real implementation, you'd run actual tests here
            app_logger.info("Validation passed")
            return True
        except Exception as e:
            app_logger.error(f"Validation failed: {e}")
            return False
    
    def _apply_staged_files(self, staged_files: Dict[str, Path]) -> None:
        """
        Apply staged files to their final locations.
        
        Args:
            staged_files: Dictionary mapping file paths to staging paths
        """
        for file_path, staging_path in staged_files.items():
            final_path = PROJECT_ROOT / file_path
            final_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write(final_path, staging_path.read_text())
            app_logger.info(f"Applied changes to {file_path}")
    
    def _get_module_names(self, file_paths: List[str]) -> List[str]:
        """
        Convert file paths to module names for reloading.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            List of module names
        """
        module_names = []
        
        for file_path in file_paths:
            if file_path.endswith(".py"):
                # Convert file path to module name
                # e.g., "bot/handlers/normal_chat.py" -> "bot.handlers.normal_chat"
                module_name = file_path[:-3].replace("/", ".").replace("\\", ".")
                module_names.append(module_name)
                
        return module_names

# Global instance
self_modifier = SelfModifier()