import os
import shutil
from datetime import datetime
from pathlib import Path

class FileManager:
    def __init__(self):
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, file_path: str):
        """Create backup of file before modification"""
        if os.path.exists(file_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{Path(file_path).stem}_{timestamp}.bak"
            backup_path = self.backup_dir / backup_name
            shutil.copy2(file_path, backup_path)
            return str(backup_path)
        return None
    
    def restore_backup(self) -> bool:
        """Restore from most recent backup"""
        backups = list(self.backup_dir.glob('*.bak'))
        if not backups:
            return False
            
        latest_backup = max(backups, key=os.path.getctime)
        # Logic to restore would go here
        return True
    
    def get_file_tree(self) -> str:
        """Generate file tree visualization"""
        def build_tree(path: Path, prefix: str = "", is_last: bool = True):
            if path.name.startswith('.'):
                return ""
                
            tree = prefix + ("└── " if is_last else "├── ") + path.name + "\n"
            
            if path.is_dir():
                children = [p for p in path.iterdir() if not p.name.startswith('.')]
                for i, child in enumerate(children):
                    is_last_child = i == len(children) - 1
                    extension = "    " if is_last else "│   "
                    tree += build_tree(child, prefix + extension, is_last_child)
            
            return tree
        
        return build_tree(Path('.'))