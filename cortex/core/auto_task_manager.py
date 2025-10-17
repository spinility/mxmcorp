"""
Auto Task Manager - Cortex self-management system

Reads plans, roadmaps, and documentation to automatically create and manage tasks.

Features:
1. Scans docs/roadmaps for pending tasks
2. Parses task lists (- [ ] format, TODO comments)
3. Creates tasks in TodoDB automatically
4. Prevents duplicate task creation
5. Priority-based task ordering
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class AutoTaskManager:
    """
    Manages automatic task creation from documentation and plans

    Workflow:
    1. Scan specified files for task patterns
    2. Parse tasks with priority/tier inference
    3. Create non-duplicate tasks in TodoDB
    4. Return summary of tasks created
    """

    def __init__(self, todo_manager):
        """
        Initialize AutoTaskManager

        Args:
            todo_manager: TodoDB manager instance
        """
        self.todo_manager = todo_manager
        self.scanned_files: List[Path] = []
        self.created_tasks: List[Dict] = []

    def scan_and_create_tasks(self, base_path: Path = None) -> Dict[str, Any]:
        """
        Scan all relevant files and create tasks

        Args:
            base_path: Base directory to scan (default: /github/mxmcorp)

        Returns:
            Dict with scan results
        """
        if base_path is None:
            base_path = Path("/github/mxmcorp")

        print("🔍 AutoTaskManager: Scanning for tasks...")
        print()

        # Files to scan
        scan_targets = [
            base_path / "roadmap.md",
            base_path / "docs" / "ROADMAP.md",
            base_path / "docs" / "UX_ENHANCEMENTS.md",
            base_path / "TODO.md",
        ]

        tasks_found = []

        for file_path in scan_targets:
            if file_path.exists():
                print(f"  📄 Scanning: {file_path.name}")
                file_tasks = self._parse_file(file_path)
                tasks_found.extend(file_tasks)
                self.scanned_files.append(file_path)

        print()
        print(f"  ✓ Found {len(tasks_found)} tasks")
        print()

        # Create tasks in TodoDB
        created_count = 0
        duplicate_count = 0

        for task_data in tasks_found:
            # Check if task already exists
            if self._task_exists(task_data['description']):
                duplicate_count += 1
                continue

            # Create task
            try:
                task_id = self.todo_manager.create_task(
                    description=task_data['description'],
                    context=task_data['context'],
                    min_tier=task_data['tier']
                )

                if task_id:
                    created_count += 1
                    self.created_tasks.append({
                        'id': task_id,
                        'description': task_data['description'],
                        'tier': task_data['tier'],
                        'source': task_data['source']
                    })

            except Exception as e:
                print(f"  ⚠️  Failed to create task: {task_data['description'][:50]}... - {str(e)}")

        return {
            'success': True,
            'files_scanned': len(self.scanned_files),
            'tasks_found': len(tasks_found),
            'tasks_created': created_count,
            'tasks_skipped_duplicate': duplicate_count,
            'created_tasks': self.created_tasks
        }

    def _parse_file(self, file_path: Path) -> List[Dict]:
        """
        Parse a file for task patterns

        Args:
            file_path: Path to file to parse

        Returns:
            List of task dictionaries
        """
        tasks = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            current_section = ""

            for i, line in enumerate(lines):
                # Track sections for context
                if line.startswith('#'):
                    current_section = line.strip('# ').strip()

                # Pattern 1: Markdown checkbox - [ ] Task
                checkbox_match = re.match(r'^[\s\-]*\[\s\]\s+(.+)$', line)
                if checkbox_match:
                    task_desc = checkbox_match.group(1).strip()

                    # Infer tier from keywords
                    tier = self._infer_tier(task_desc)

                    # Build context
                    context = f"From {file_path.name}"
                    if current_section:
                        context += f" - Section: {current_section}"

                    # Get surrounding lines for more context
                    context_lines = []
                    for j in range(max(0, i-2), min(len(lines), i+3)):
                        if j != i and lines[j].strip():
                            context_lines.append(lines[j].strip())

                    if context_lines:
                        context += f"\n\nNearby context:\n" + "\n".join(context_lines[:3])

                    tasks.append({
                        'description': task_desc,
                        'context': context,
                        'tier': tier,
                        'source': str(file_path),
                        'line': i + 1
                    })

                # Pattern 2: TODO: Task
                todo_match = re.search(r'TODO:\s*(.+)$', line, re.IGNORECASE)
                if todo_match:
                    task_desc = todo_match.group(1).strip()
                    tier = self._infer_tier(task_desc)

                    context = f"From {file_path.name} (line {i+1})"
                    if current_section:
                        context += f" - Section: {current_section}"

                    tasks.append({
                        'description': task_desc,
                        'context': context,
                        'tier': tier,
                        'source': str(file_path),
                        'line': i + 1
                    })

        except Exception as e:
            print(f"  ⚠️  Error parsing {file_path}: {e}")

        return tasks

    def _infer_tier(self, task_description: str) -> str:
        """
        Infer task tier from description

        Args:
            task_description: Task description text

        Returns:
            Tier string (nano, deepseek, claude)
        """
        desc_lower = task_description.lower()

        # Claude tier keywords
        claude_keywords = ['architecture', 'design', 'refactor', 'complex', 'analyze', 'review']
        if any(keyword in desc_lower for keyword in claude_keywords):
            return 'claude'

        # DeepSeek tier keywords
        deepseek_keywords = ['implement', 'create', 'build', 'write', 'develop']
        if any(keyword in desc_lower for keyword in deepseek_keywords):
            return 'deepseek'

        # Default to nano for simple tasks
        return 'nano'

    def _task_exists(self, description: str) -> bool:
        """
        Check if task already exists in TodoDB

        Args:
            description: Task description

        Returns:
            True if task exists
        """
        try:
            all_tasks = self.todo_manager.get_all_tasks()

            # Check for exact or very similar descriptions
            for task in all_tasks:
                if task.description.lower().strip() == description.lower().strip():
                    return True

                # Check for 80% similarity
                similarity = self._similarity_score(task.description, description)
                if similarity > 0.8:
                    return True

        except Exception:
            pass

        return False

    def _similarity_score(self, str1: str, str2: str) -> float:
        """
        Calculate simple similarity score between two strings

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score (0.0 to 1.0)
        """
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def get_summary(self) -> str:
        """
        Get summary of scan results

        Returns:
            Formatted summary string
        """
        if not self.created_tasks:
            return "No new tasks created"

        summary = f"Created {len(self.created_tasks)} new tasks:\n\n"

        for i, task in enumerate(self.created_tasks[:10], 1):
            summary += f"{i}. [{task['tier']}] {task['description'][:60]}\n"
            summary += f"   Source: {Path(task['source']).name}\n\n"

        if len(self.created_tasks) > 10:
            summary += f"... and {len(self.created_tasks) - 10} more tasks\n"

        return summary


# Test
if __name__ == "__main__":
    print("Testing AutoTaskManager...")
    print()

    # Mock todo manager
    class MockTodoManager:
        def __init__(self):
            self.tasks = []

        def create_task(self, description, context, min_tier):
            task_id = len(self.tasks)
            self.tasks.append({
                'id': task_id,
                'description': description,
                'context': context,
                'tier': min_tier
            })
            return task_id

        def get_all_tasks(self):
            return [type('obj', (object,), {'description': t['description']})() for t in self.tasks]

    mock_manager = MockTodoManager()
    auto_mgr = AutoTaskManager(mock_manager)

    # Test scan
    result = auto_mgr.scan_and_create_tasks()

    print(f"✓ Scan complete!")
    print(f"  Files scanned: {result['files_scanned']}")
    print(f"  Tasks found: {result['tasks_found']}")
    print(f"  Tasks created: {result['tasks_created']}")
    print()
    print(auto_mgr.get_summary())
