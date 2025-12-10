"""
Self-modifier module for the Jarvis Telegram bot.
Handles code generation, validation, and application of changes.
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from ai.gemini_client import gemini_client
from agent.sandbox import enforce_sandbox
from agent.reloader import determine_reload_type, soft_reload, full_restart
from utils.fileops import atomic_write, backup
from utils.logger import setup_logger, app_logger
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
        self.max_backups = 5  # Keep only the last 5 backups
        
        # Create directories if they don't exist
        self.staging_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Set up logging
        self.log_file = self.logs_dir / "self_modify.log"
        # Set up a dedicated logger for self-modification
        self.logger = setup_logger("self_modifier", str(self.log_file))
        
    def process_dev_request(self, dev_request: DevRequest) -> Dict[str, Any]:
        """
        Process a development request from an admin.
        
        Args:
            dev_request: The development request to process
            
        Returns:
            Result dictionary with status and message
        """
        try:
            self.logger.info(f"Processing dev request: {dev_request.goal_description}")
            
            # Step 1: Get current project context
            context = self._get_project_context(dev_request.target_files)
            
            # Step 2: Get code changes from AI
            changes = gemini_client.generate_code_update(context, dev_request.goal_description)
            
            # Step 3: Validate and apply changes
            result = self._apply_changes(changes, dev_request)
            
            return result
        except Exception as e:
            self.logger.error(f"Failed to process dev request: {e}")
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
        
        # Add general project structure information
        context_parts.append("PROJECT STRUCTURE:")
        try:
            from pathlib import Path
            project_items = []
            for item in PROJECT_ROOT.iterdir():
                if item.is_dir():
                    project_items.append(f"{item.name}/")
                else:
                    project_items.append(item.name)
            context_parts.append(", ".join(project_items))
        except Exception as e:
            context_parts.append(f"Error reading project structure: {e}")
        
        # Add information about target files
        context_parts.append("\nTARGET FILES CONTENT:")
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
                
        # Add information about related files (files in the same directories)
        context_parts.append("\nRELATED FILES CONTENT:")
        related_dirs = set()
        for file_path in target_files:
            parent_dir = str(Path(file_path).parent)
            if parent_dir != ".":
                related_dirs.add(parent_dir)
                
        for dir_path in related_dirs:
            dir_full_path = PROJECT_ROOT / dir_path
            if dir_full_path.exists() and dir_full_path.is_dir():
                try:
                    for item in dir_full_path.iterdir():
                        if item.is_file() and item.name not in [Path(f).name for f in target_files]:
                            # Read small files only
                            if item.stat().st_size < 5000:  # Less than 5KB
                                with open(item, 'r') as f:
                                    content = f.read()
                                    context_parts.append(f"{item.relative_to(PROJECT_ROOT)}:\n{content}")
                except Exception as e:
                    context_parts.append(f"Error reading directory {dir_path}: {e}")
        
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
        backup_path = None
        staged_files = {}
        
        try:
            # Extract file changes
            file_changes = self._extract_file_changes(changes)
            
            if not file_changes:
                self.logger.warning("No file changes detected in AI response")
                return {
                    "status": "warning",
                    "message": "No file changes detected in AI response"
                }
            
            # Get list of target paths
            target_paths = list(file_changes.keys())
            
            # Step 0: Create backup
            self.logger.info("Creating backup of files to be changed")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / timestamp
            backup(target_paths, backup_path)
            
            # Step 1: Write to staging area
            self.logger.info("Writing changes to staging area")
            staged_files = self._write_to_staging(file_changes)
            
            # Step 2: Run validation
            self.logger.info("Running validation checks")
            if not self._validate_changes(staged_files):
                raise Exception("Validation failed")
            
            # Step 3: Apply changes atomically
            self.logger.info("Applying changes atomically")
            self._apply_staged_files(staged_files)
            
            # Step 3.1: Clean up old backups (after successful application)
            self._cleanup_old_backups()
            
            # Step 4: Apply reload rule
            reload_info = {
                "changed_files": target_paths,
                "dependencies_changed": self._check_dependencies_changed(file_changes)
            }
            reload_type = determine_reload_type(reload_info)
            self.logger.info(f"Applying {reload_type} reload")
            
            if reload_type == "full":
                # For full restart, we just exit with the appropriate code
                # The process manager should restart us
                self.logger.info("Full restart required - exiting")
                # Import the full_restart function and exit codes
                from agent.reloader import full_restart, EXIT_CODE_CRITICAL_FILE_CHANGED, EXIT_CODE_DEPENDENCY_CHANGED
                # Determine the appropriate exit code
                exit_code = EXIT_CODE_CRITICAL_FILE_CHANGED
                if self._check_dependencies_changed(file_changes):
                    exit_code = EXIT_CODE_DEPENDENCY_CHANGED
                # Trigger full restart
                full_restart(exit_code)
                # This point should never be reached
                return {
                    "status": "success",
                    "message": "Changes applied. Full restart performed.",
                    "restart_required": True
                }
            else:
                # Soft reload
                module_names = self._get_module_names(target_paths)
                if soft_reload(module_names):
                    # Verify reload success
                    from agent.reloader import verify_reload_success
                    if verify_reload_success():
                        self.logger.info("Changes applied and loaded successfully")
                        return {
                            "status": "success",
                            "message": "Changes applied and loaded successfully."
                        }
                    else:
                        raise Exception("Reload verification failed")
                else:
                    raise Exception("Soft reload failed")
                    
        except Exception as e:
            self.logger.error(f"Failed to apply changes: {e}")
            # Rollback changes if backup was created
            if backup_path and backup_path.exists():
                self._rollback_changes(backup_path, target_paths)
            return {
                "status": "error",
                "message": f"Failed to apply changes: {str(e)}"
            }
    
    def _cleanup_old_backups(self) -> None:
        """
        Clean up old backups, keeping only the most recent ones.
        """
        try:
            # Get all backup directories
            backup_dirs = [d for d in self.backup_dir.iterdir() if d.is_dir()]
            
            # Sort by modification time (oldest first)
            backup_dirs.sort(key=lambda x: x.stat().st_mtime)
            
            # Remove oldest backups if we have more than max_backups
            while len(backup_dirs) > self.max_backups:
                oldest_backup = backup_dirs.pop(0)
                import shutil
                shutil.rmtree(oldest_backup)
                self.logger.info(f"Removed old backup: {oldest_backup}")
        except Exception as e:
            self.logger.error(f"Error cleaning up old backups: {e}")
    
    def _rollback_changes(self, backup_path: Path, target_paths: List[str]) -> None:
        """
        Rollback changes from a backup.
        
        Args:
            backup_path: Path to the backup directory
            target_paths: List of file paths that were changed
        """
        try:
            self.logger.info(f"Rolling back changes from backup: {backup_path}")
            from utils.fileops import restore
            # Restore from backup
            restore(backup_path, PROJECT_ROOT)
            self.logger.info("Rollback completed successfully")
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            # If rollback fails, log the error but continue
            # The system may be in an inconsistent state
    
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
        if "files" in changes and isinstance(changes["files"], list):
            # JSON format with files array
            for file_info in changes["files"]:
                if isinstance(file_info, dict) and "path" in file_info and "content" in file_info:
                    file_changes[file_info["path"]] = file_info["content"]
                elif isinstance(file_info, dict) and "path" in file_info and "diff" in file_info:
                    # Handle diff format
                    diff_content = file_info["diff"]
                    file_path = file_info["path"]
                    # Apply the diff to get the new content
                    new_content = self._apply_unified_diff(file_path, diff_content)
                    if new_content is not None:
                        file_changes[file_path] = new_content
                    else:
                        self.logger.warning(f"Failed to apply diff for {file_path}")
        elif isinstance(changes, dict) and "text" in changes:
            # Text format - try to parse as file content
            text = changes["text"]
            lines = text.split("\n")
            current_file = None
            current_content = []
            
            for line in lines:
                if line.startswith("--- ") and " ---" in line and line.endswith(" ---"):
                    # New file header - save previous file if we had one
                    if current_file and current_content:
                        file_changes[current_file] = "\n".join(current_content)
                        current_content = []
                        
                    # Extract file path from --- path/to/file.py ---
                    current_file = line[4:-4]  # Remove --- markers
                elif current_file:
                    current_content.append(line)
                    
            # Don't forget the last file
            if current_file and current_content:
                file_changes[current_file] = "\n".join(current_content)
        else:
            # Try to parse as a simple text response with file markers
            # This is a more robust parser that handles various edge cases
            if isinstance(changes, str):
                text = changes
            elif isinstance(changes, dict):
                text = str(changes)
            else:
                text = ""
                
            # Look for file markers in the text
            import re
            file_pattern = r"---\s+(.*?)\s+---"
            matches = list(re.finditer(file_pattern, text))
            
            if matches:
                for i, match in enumerate(matches):
                    file_path = match.group(1)
                    # Get content between this match and the next one (or end of text)
                    start_pos = match.end()
                    end_pos = matches[i+1].start() if i+1 < len(matches) else len(text)
                    content = text[start_pos:end_pos].strip()
                    file_changes[file_path] = content
            else:
                self.logger.warning("Could not parse file changes from AI response")
                
        return file_changes
    
    def _apply_unified_diff(self, file_path: str, diff_content: str) -> Optional[str]:
        """
        Apply a unified diff to get the new file content.
        
        Args:
            file_path: Path to the file
            diff_content: Unified diff content
            
        Returns:
            New file content, or None if failed
        """
        try:
            # Read the original file content
            original_path = PROJECT_ROOT / file_path
            if original_path.exists():
                with open(original_path, 'r') as f:
                    original_content = f.read()
            else:
                original_content = ""
            
            # For now, we'll use a simpler approach
            # In a production system, you'd want to use a proper diff library
            # For this implementation, we'll assume the diff_content is actually
            # the full new content when provided in diff format
            # This is a simplification to avoid complex diff parsing
            
            self.logger.info(f"Using diff content as new file content for {file_path}")
            return diff_content
        except Exception as e:
            self.logger.error(f"Error applying diff for {file_path}: {e}")
            return None
    
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
                        self.logger.error(f"Syntax check failed for {file_path}: {result.stderr}")
                        return False
            
            # Run linter (if available)
            try:
                result = subprocess.run([
                    sys.executable, "-m", "ruff", "check", str(self.staging_dir)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.logger.warning(f"Linting issues found: {result.stdout}")
                    # Not failing on linting issues for now
            except FileNotFoundError:
                self.logger.warning("Ruff not found, skipping linting")
            
            # Check if any new test files were generated and validate them
            test_files = [f for f in staged_files.keys() if f.startswith("tests/") and f.endswith(".py")]
            if test_files:
                self.logger.info(f"Found {len(test_files)} new test files to validate: {test_files}")
                # Run only the new test files
                try:
                    # Create a temporary test environment
                    import shutil
                    test_env_dir = self.staging_dir / "test_env"
                    test_env_dir.mkdir(exist_ok=True)
                    
                    # Copy the entire project to the test environment
                    for item in PROJECT_ROOT.iterdir():
                        if item.name != ".staging":  # Don't copy the staging directory
                            if item.is_dir():
                                shutil.copytree(item, test_env_dir / item.name, dirs_exist_ok=True)
                            else:
                                shutil.copy2(item, test_env_dir / item.name)
                    
                    # Replace staged files in the test environment
                    for file_path, staging_path in staged_files.items():
                        test_file_path = test_env_dir / file_path
                        test_file_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(staging_path, test_file_path)
                    
                    # Run only the new test files
                    for test_file in test_files:
                        self.logger.info(f"Running new test file: {test_file}")
                        result = subprocess.run([
                            sys.executable, "-m", "pytest", "-v", test_file
                        ], cwd=test_env_dir, capture_output=True, text=True)
                        
                        if result.returncode != 0:
                            self.logger.error(f"New test {test_file} failed: {result.stdout}\n{result.stderr}")
                            # Clean up
                            shutil.rmtree(test_env_dir)
                            return False
                    
                    # Clean up
                    shutil.rmtree(test_env_dir)
                except Exception as e:
                    self.logger.error(f"Error validating new test files: {e}")
                    # Clean up on error
                    test_env_dir = self.staging_dir / "test_env"
                    if test_env_dir.exists():
                        import shutil
                        shutil.rmtree(test_env_dir)
                    return False
            
            # Run all tests (if available)
            try:
                # Create a temporary test environment that mimics the project structure
                import shutil
                test_env_dir = self.staging_dir / "test_env"
                test_env_dir.mkdir(exist_ok=True)
                
                # Copy the entire project to the test environment
                for item in PROJECT_ROOT.iterdir():
                    if item.name != ".staging":  # Don't copy the staging directory
                        if item.is_dir():
                            shutil.copytree(item, test_env_dir / item.name, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, test_env_dir / item.name)
                
                # Replace staged files in the test environment
                for file_path, staging_path in staged_files.items():
                    test_file_path = test_env_dir / file_path
                    test_file_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(staging_path, test_file_path)
                
                # Run tests from the test environment
                result = subprocess.run([
                    sys.executable, "-m", "pytest", "-q", "tests/"
                ], cwd=test_env_dir, capture_output=True, text=True)
                
                # Clean up
                shutil.rmtree(test_env_dir)
                
                if result.returncode != 0:
                    self.logger.error(f"Tests failed: {result.stdout}\n{result.stderr}")
                    return False
            except FileNotFoundError:
                self.logger.warning("Pytest not found, skipping tests")
            except Exception as e:
                self.logger.error(f"Error running tests: {e}")
                # Clean up on error
                test_env_dir = self.staging_dir / "test_env"
                if test_env_dir.exists():
                    import shutil
                    shutil.rmtree(test_env_dir)
                return False
            
            self.logger.info("Validation passed")
            return True
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
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
            self.logger.info(f"Applied changes to {file_path}")
    
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
    
    def _check_dependencies_changed(self, file_changes: Dict[str, str]) -> bool:
        """
        Check if dependencies were changed in the file changes.
        
        Args:
            file_changes: Dictionary mapping file paths to content
            
        Returns:
            True if dependencies were changed, False otherwise
        """
        # Check if requirements.txt was modified
        if "requirements.txt" in file_changes:
            return True
            
        # Check if any Python files added new imports
        for file_path, content in file_changes.items():
            if file_path.endswith(".py"):
                # Parse the content to check for new external imports
                lines = content.split("\n")
                for line in lines:
                    line = line.strip()
                    # Check for import statements that might indicate new dependencies
                    if (line.startswith("import ") or 
                        (line.startswith("from ") and " import " in line)):
                        # Check if this is importing from a third-party library
                        # This is a simple heuristic - in a real implementation,
                        # you might want to check against a list of standard library modules
                        parts = line.split()
                        if len(parts) >= 2:
                            module_name = parts[1]
                            # Skip standard library modules
                            stdlib_modules = {
                                'os', 'sys', 'json', 'time', 'logging', 'pathlib',
                                'typing', 'subprocess', 'shutil', 'tempfile', 're'
                            }
                            if module_name not in stdlib_modules and not module_name.startswith('.'):
                                self.logger.info(f"Potential new dependency detected: {module_name}")
                                return True
                        
        return False

# Global instance
self_modifier = SelfModifier()