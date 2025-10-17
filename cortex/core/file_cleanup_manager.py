"""
File Cleanup Manager - Automatic cleanup of generated files

Tracks and cleans up temporary/generated files after processing.

Features:
- Automatic tracking of generated files
- Cleanup after task completion
- Safe deletion with backup option
- Pattern-based cleanup rules
"""

import os
import shutil
import json
from pathlib import Path
from typing import List, Set, Optional
from datetime import datetime
import re


class FileCleanupManager:
    """
    Manages automatic cleanup of generated files

    Tracks files created during task execution and cleans them up
    after processing is complete.
    """

    def __init__(
        self,
        tracking_file: str = "cortex/data/generated_files.json",
        backup_dir: str = "cortex/data/file_backups",
        auto_cleanup: bool = True
    ):
        """
        Initialize FileCleanupManager

        Args:
            tracking_file: File to track generated files
            backup_dir: Directory to store backups before deletion
            auto_cleanup: Enable automatic cleanup
        """
        self.tracking_file = Path(tracking_file)
        self.backup_dir = Path(backup_dir)
        self.auto_cleanup = auto_cleanup

        # Create directories
        self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Load tracked files
        self.tracked_files: Set[str] = self._load_tracked_files()

        # Cleanup patterns (files matching these patterns are auto-cleaned)
        self.cleanup_patterns = [
            r".*\.tmp$",
            r".*\.temp$",
            r".*_temp\..*$",
            r".*_generated\..*$",
            r"cortex/output/.*\.json$",
            r"cortex/output/.*\.txt$",
        ]

    def _load_tracked_files(self) -> Set[str]:
        """Load tracked files from JSON"""
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('files', []))
            except Exception:
                return set()
        return set()

    def _save_tracked_files(self):
        """Save tracked files to JSON"""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump({
                    'files': list(self.tracked_files),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save tracked files: {e}")

    def track_file(self, file_path: str):
        """
        Track a file for cleanup

        Args:
            file_path: Path to file to track
        """
        file_path = str(Path(file_path).resolve())
        self.tracked_files.add(file_path)
        self._save_tracked_files()

    def track_files(self, file_paths: List[str]):
        """
        Track multiple files for cleanup

        Args:
            file_paths: List of file paths to track
        """
        for file_path in file_paths:
            file_path = str(Path(file_path).resolve())
            self.tracked_files.add(file_path)
        self._save_tracked_files()

    def should_cleanup(self, file_path: str) -> bool:
        """
        Check if file matches cleanup patterns

        Args:
            file_path: Path to file

        Returns:
            True if file should be cleaned up
        """
        for pattern in self.cleanup_patterns:
            if re.match(pattern, file_path):
                return True
        return False

    def backup_file(self, file_path: Path) -> Optional[Path]:
        """
        Create backup of file before deletion

        Args:
            file_path: Path to file

        Returns:
            Path to backup file or None
        """
        try:
            if not file_path.exists():
                return None

            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_name

            # Copy file
            shutil.copy2(file_path, backup_path)
            return backup_path

        except Exception as e:
            print(f"⚠️  Failed to backup {file_path}: {e}")
            return None

    def cleanup_file(
        self,
        file_path: str,
        create_backup: bool = True,
        force: bool = False
    ) -> bool:
        """
        Clean up a single file

        Args:
            file_path: Path to file to delete
            create_backup: Create backup before deletion
            force: Force deletion even if not tracked

        Returns:
            True if deleted successfully
        """
        file_path = Path(file_path).resolve()

        # Check if tracked or force
        if str(file_path) not in self.tracked_files and not force:
            return False

        # Check if exists
        if not file_path.exists():
            # Remove from tracking
            self.tracked_files.discard(str(file_path))
            self._save_tracked_files()
            return True

        try:
            # Backup if requested
            if create_backup:
                backup_path = self.backup_file(file_path)
                if backup_path:
                    print(f"  📦 Backed up: {file_path.name} → {backup_path.name}")

            # Delete file
            file_path.unlink()
            print(f"  🗑️  Deleted: {file_path}")

            # Remove from tracking
            self.tracked_files.discard(str(file_path))
            self._save_tracked_files()

            return True

        except Exception as e:
            print(f"  ⚠️  Failed to delete {file_path}: {e}")
            return False

    def cleanup_all_tracked(self, create_backup: bool = True) -> int:
        """
        Clean up all tracked files

        Args:
            create_backup: Create backups before deletion

        Returns:
            Number of files deleted
        """
        if not self.auto_cleanup:
            print("⚠️  Auto-cleanup is disabled")
            return 0

        if not self.tracked_files:
            return 0

        print(f"\n🧹 Cleaning up {len(self.tracked_files)} tracked files...")

        deleted = 0
        files_to_delete = list(self.tracked_files)

        for file_path in files_to_delete:
            if self.cleanup_file(file_path, create_backup=create_backup):
                deleted += 1

        print(f"✓ Cleaned up {deleted} files")
        return deleted

    def cleanup_by_pattern(
        self,
        pattern: str = None,
        directory: str = ".",
        create_backup: bool = True
    ) -> int:
        """
        Clean up files matching pattern in directory

        Args:
            pattern: Regex pattern (uses default patterns if None)
            directory: Directory to scan
            create_backup: Create backups before deletion

        Returns:
            Number of files deleted
        """
        directory = Path(directory)
        patterns = [pattern] if pattern else self.cleanup_patterns

        deleted = 0

        for file_path in directory.rglob("*"):
            if not file_path.is_file():
                continue

            relative_path = str(file_path.relative_to(directory))

            for pat in patterns:
                if re.match(pat, relative_path):
                    # Track and cleanup
                    self.track_file(str(file_path))
                    if self.cleanup_file(str(file_path), create_backup=create_backup):
                        deleted += 1
                    break

        return deleted

    def cleanup_task_files(self, task_id: int, create_backup: bool = True) -> int:
        """
        Clean up files associated with a specific task

        Args:
            task_id: Task ID
            create_backup: Create backups before deletion

        Returns:
            Number of files deleted
        """
        # Find files with task_id in name
        pattern = rf".*task_{task_id}_.*"
        deleted = 0

        for file_path in self.tracked_files.copy():
            if re.match(pattern, Path(file_path).name):
                if self.cleanup_file(file_path, create_backup=create_backup):
                    deleted += 1

        return deleted

    def get_cleanup_summary(self) -> dict:
        """
        Get summary of tracked files

        Returns:
            Dict with cleanup statistics
        """
        total_size = 0
        file_types = {}

        for file_path in self.tracked_files:
            path = Path(file_path)
            if path.exists():
                # Size
                total_size += path.stat().st_size

                # Type
                ext = path.suffix or 'no_extension'
                file_types[ext] = file_types.get(ext, 0) + 1

        return {
            'total_files': len(self.tracked_files),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / 1024 / 1024,
            'file_types': file_types
        }

    def add_cleanup_pattern(self, pattern: str):
        """
        Add a new cleanup pattern

        Args:
            pattern: Regex pattern to match files
        """
        if pattern not in self.cleanup_patterns:
            self.cleanup_patterns.append(pattern)

    def disable_auto_cleanup(self):
        """Disable automatic cleanup"""
        self.auto_cleanup = False

    def enable_auto_cleanup(self):
        """Enable automatic cleanup"""
        self.auto_cleanup = True


# Create global instance
cleanup_manager = FileCleanupManager()


# Test
if __name__ == "__main__":
    import tempfile

    print("Testing File Cleanup Manager...")
    print()

    # Create temporary test files
    test_dir = Path("cortex/test_cleanup")
    test_dir.mkdir(parents=True, exist_ok=True)

    test_files = [
        test_dir / "test_temp.txt",
        test_dir / "test_generated.json",
        test_dir / "task_123_output.txt",
    ]

    print("1. Creating test files...")
    for file_path in test_files:
        file_path.write_text("Test content")
        print(f"  ✓ Created: {file_path}")

    # Track files
    print("\n2. Tracking files...")
    mgr = FileCleanupManager()
    mgr.track_files([str(f) for f in test_files])
    print(f"  ✓ Tracking {len(mgr.tracked_files)} files")

    # Get summary
    print("\n3. Cleanup summary...")
    summary = mgr.get_cleanup_summary()
    print(f"  Files: {summary['total_files']}")
    print(f"  Size: {summary['total_size_mb']:.4f} MB")

    # Cleanup
    print("\n4. Cleaning up tracked files...")
    deleted = mgr.cleanup_all_tracked(create_backup=False)
    print(f"  ✓ Deleted {deleted} files")

    # Cleanup test directory
    if test_dir.exists():
        shutil.rmtree(test_dir)

    print("\n✅ File cleanup manager works!")
