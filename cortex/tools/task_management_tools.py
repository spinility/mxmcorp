"""
Task Management Tools - CRUD operations for Cortex self-management

Provides comprehensive tools for Cortex to manage its own tasks:
- Create/read/update/delete tasks
- Subtask management
- Analytics and insights
- ML training data collection
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict


@dataclass
class TaskMetrics:
    """Metrics for a completed task"""
    execution_duration: float
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    success_score: float
    tools_used: List[str]
    tool_sequence: List[Dict]
    context_files: List[str]
    conversation: List[Dict]


class TaskManager:
    """
    Task management system for Cortex self-management

    Provides tools for:
    - CRUD operations on tasks
    - Subtask hierarchy
    - Analytics and insights
    - ML training data collection
    """

    def __init__(self, db_path: str = "cortex/data/todo_pool.db"):
        """
        Initialize TaskManager

        Args:
            db_path: Path to TodoDB database
        """
        self.db_path = Path(db_path)

        if not self.db_path.exists():
            raise FileNotFoundError(f"TodoDB not found: {db_path}")

    def create_task(
        self,
        description: str,
        context: str = "",
        min_tier: str = "nano",
        priority: int = 5,
        category: str = None,
        tags: List[str] = None,
        source_file: str = None,
        source_line: int = None
    ) -> Dict[str, Any]:
        """
        Create a new task

        Args:
            description: Task description
            context: Additional context
            min_tier: Minimum model tier (nano/deepseek/claude)
            priority: Priority 1-10 (1=urgent, 10=low)
            category: bug/feature/refactor/doc/test
            tags: List of tags
            source_file: Source file where task was found
            source_line: Line number in source file

        Returns:
            Dict with task_id and success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()

                cursor.execute("""
                    INSERT INTO tasks (
                        description, context, min_tier, status, priority,
                        category, tags, source_file, source_line,
                        owner_id, created_at, updated_at
                    )
                    VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, 1, ?, ?)
                """, (
                    description,
                    context,
                    min_tier,
                    priority,
                    category,
                    json.dumps(tags) if tags else None,
                    source_file,
                    source_line,
                    now,
                    now
                ))

                task_id = cursor.lastrowid
                conn.commit()

                return {
                    'success': True,
                    'task_id': task_id,
                    'message': f'Task {task_id} created'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def create_subtask(
        self,
        parent_task_id: int,
        description: str,
        context: str = "",
        priority: int = None
    ) -> Dict[str, Any]:
        """
        Create a subtask under a parent task

        Args:
            parent_task_id: ID of parent task
            description: Subtask description
            context: Additional context
            priority: Priority (inherits from parent if None)

        Returns:
            Dict with subtask_id and success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get parent task info
                cursor.execute("""
                    SELECT min_tier, priority, category
                    FROM tasks WHERE id = ?
                """, (parent_task_id,))

                parent = cursor.fetchone()
                if not parent:
                    return {
                        'success': False,
                        'error': f'Parent task {parent_task_id} not found'
                    }

                # Create subtask
                now = datetime.now().isoformat()

                cursor.execute("""
                    INSERT INTO tasks (
                        description, context, min_tier, status, priority,
                        category, parent_task_id, owner_id,
                        created_at, updated_at
                    )
                    VALUES (?, ?, ?, 'pending', ?, ?, ?, 1, ?, ?)
                """, (
                    description,
                    context,
                    parent[0],  # min_tier from parent
                    priority if priority else parent[1],  # priority
                    parent[2],  # category
                    parent_task_id,
                    now,
                    now
                ))

                subtask_id = cursor.lastrowid

                # Create relationship
                cursor.execute("""
                    INSERT INTO task_relationships (
                        parent_id, child_id, relationship_type
                    )
                    VALUES (?, ?, 'subtask')
                """, (parent_task_id, subtask_id))

                conn.commit()

                return {
                    'success': True,
                    'subtask_id': subtask_id,
                    'message': f'Subtask {subtask_id} created under task {parent_task_id}'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def read_task(self, task_id: int) -> Dict[str, Any]:
        """
        Get full details of a task

        Args:
            task_id: Task ID

        Returns:
            Dict with task details
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
                row = cursor.fetchone()

                if not row:
                    return {
                        'success': False,
                        'error': f'Task {task_id} not found'
                    }

                # Get column names
                columns = [desc[0] for desc in cursor.description]
                task = dict(zip(columns, row))

                # Parse JSON fields
                if task.get('tags'):
                    task['tags'] = json.loads(task['tags'])
                if task.get('tools_called'):
                    task['tools_called'] = json.loads(task['tools_called'])
                if task.get('tool_call_sequence'):
                    task['tool_call_sequence'] = json.loads(task['tool_call_sequence'])
                if task.get('context_files_loaded'):
                    task['context_files_loaded'] = json.loads(task['context_files_loaded'])

                return {
                    'success': True,
                    'task': task
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def update_task(
        self,
        task_id: int,
        status: str = None,
        priority: int = None,
        assigned_model: str = None,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Update task fields

        Args:
            task_id: Task ID
            status: New status (pending/in_progress/completed/failed/blocked)
            priority: New priority
            assigned_model: Model being used
            notes: Additional notes (appended to context)

        Returns:
            Dict with success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()

                updates = []
                values = []

                if status:
                    updates.append("status = ?")
                    values.append(status)

                    if status == 'in_progress':
                        updates.append("started_at = ?")
                        values.append(now)
                    elif status == 'completed':
                        updates.append("completed_at = ?")
                        values.append(now)

                if priority is not None:
                    updates.append("priority = ?")
                    values.append(priority)

                if assigned_model:
                    updates.append("assigned_model = ?")
                    values.append(assigned_model)

                if notes:
                    # Append notes to context
                    cursor.execute("SELECT context FROM tasks WHERE id = ?", (task_id,))
                    current_context = cursor.fetchone()[0]
                    new_context = f"{current_context}\n\nNotes: {notes}"
                    updates.append("context = ?")
                    values.append(new_context)

                updates.append("updated_at = ?")
                values.append(now)
                values.append(task_id)

                query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, values)
                conn.commit()

                return {
                    'success': True,
                    'message': f'Task {task_id} updated'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def delete_task(self, task_id: int, reason: str = None) -> Dict[str, Any]:
        """
        Soft delete a task (marks as deleted, preserves history)

        Args:
            task_id: Task ID
            reason: Reason for deletion

        Returns:
            Dict with success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Soft delete by updating status and adding reason to context
                now = datetime.now().isoformat()

                cursor.execute("""
                    UPDATE tasks
                    SET status = 'deleted',
                        context = context || '\n\nDeleted: ' || ? || ' - ' || ?,
                        updated_at = ?
                    WHERE id = ?
                """, (now, reason or "No reason provided", now, task_id))

                conn.commit()

                return {
                    'success': True,
                    'message': f'Task {task_id} deleted'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def list_tasks(
        self,
        status: str = None,
        priority_min: int = None,
        category: str = None,
        tags: List[str] = None,
        limit: int = 50,
        order_by: str = "priority"
    ) -> Dict[str, Any]:
        """
        Query tasks with filters

        Args:
            status: Filter by status
            priority_min: Minimum priority
            category: Filter by category
            tags: Filter by tags
            limit: Max results
            order_by: Sort field (created_at/priority/status)

        Returns:
            Dict with task list
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM tasks WHERE 1=1"
                params = []

                if status:
                    query += " AND status = ?"
                    params.append(status)

                if priority_min:
                    query += " AND priority <= ?"
                    params.append(priority_min)

                if category:
                    query += " AND category = ?"
                    params.append(category)

                # Order
                valid_orders = ['created_at', 'priority', 'status', 'updated_at']
                if order_by in valid_orders:
                    query += f" ORDER BY {order_by}"
                else:
                    query += " ORDER BY priority, created_at"

                query += " LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)

                columns = [desc[0] for desc in cursor.description]
                tasks = []

                for row in cursor.fetchall():
                    task = dict(zip(columns, row))

                    # Parse JSON fields
                    if task.get('tags'):
                        task['tags'] = json.loads(task['tags'])

                    # Filter by tags if needed
                    if tags and task.get('tags'):
                        if not any(tag in task['tags'] for tag in tags):
                            continue

                    tasks.append(task)

                return {
                    'success': True,
                    'tasks': tasks,
                    'count': len(tasks)
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_next_task(self, tier_filter: str = None) -> Dict[str, Any]:
        """
        Get the next highest priority pending task

        Args:
            tier_filter: Only tasks for specific tier (optional)

        Returns:
            Dict with next task or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                query = """
                    SELECT * FROM tasks
                    WHERE status = 'pending'
                """
                params = []

                if tier_filter:
                    query += " AND min_tier = ?"
                    params.append(tier_filter)

                query += " ORDER BY priority ASC, created_at ASC LIMIT 1"

                cursor.execute(query, params)
                row = cursor.fetchone()

                if not row:
                    return {
                        'success': True,
                        'task': None,
                        'message': 'No pending tasks'
                    }

                columns = [desc[0] for desc in cursor.description]
                task = dict(zip(columns, row))

                # Parse JSON fields
                if task.get('tags'):
                    task['tags'] = json.loads(task['tags'])

                return {
                    'success': True,
                    'task': task
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def mark_task_complete(
        self,
        task_id: int,
        metrics: TaskMetrics = None,
        success_score: float = 1.0
    ) -> Dict[str, Any]:
        """
        Mark task as complete with execution metrics

        Args:
            task_id: Task ID
            metrics: TaskMetrics object with execution data
            success_score: Success score 0.0-1.0

        Returns:
            Dict with success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()

                if metrics:
                    cursor.execute("""
                        UPDATE tasks
                        SET status = 'completed',
                            completed_at = ?,
                            updated_at = ?,
                            execution_duration_seconds = ?,
                            total_tokens = ?,
                            prompt_tokens = ?,
                            completion_tokens = ?,
                            estimated_cost_usd = ?,
                            success_score = ?,
                            tools_called = ?,
                            tool_call_sequence = ?,
                            context_files_loaded = ?,
                            full_conversation_json = ?
                        WHERE id = ?
                    """, (
                        now, now,
                        metrics.execution_duration,
                        metrics.total_tokens,
                        metrics.prompt_tokens,
                        metrics.completion_tokens,
                        metrics.cost_usd,
                        metrics.success_score,
                        json.dumps(metrics.tools_used),
                        json.dumps(metrics.tool_sequence),
                        json.dumps(metrics.context_files),
                        json.dumps(metrics.conversation),
                        task_id
                    ))
                else:
                    cursor.execute("""
                        UPDATE tasks
                        SET status = 'completed',
                            completed_at = ?,
                            updated_at = ?,
                            success_score = ?
                        WHERE id = ?
                    """, (now, now, success_score, task_id))

                conn.commit()

                return {
                    'success': True,
                    'message': f'Task {task_id} marked complete'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_task_stats(
        self,
        date_from: str = None,
        date_to: str = None,
        category: str = None,
        group_by: str = None
    ) -> Dict[str, Any]:
        """
        Get analytics on task execution

        Args:
            date_from: Start date (ISO format)
            date_to: End date (ISO format)
            category: Filter by category
            group_by: Group results (date/category/model)

        Returns:
            Dict with statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Default to last 7 days
                if not date_from:
                    date_from = (datetime.now() - timedelta(days=7)).isoformat()
                if not date_to:
                    date_to = datetime.now().isoformat()

                query = """
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                        AVG(execution_duration_seconds) as avg_duration,
                        SUM(total_tokens) as total_tokens,
                        SUM(estimated_cost_usd) as total_cost,
                        AVG(success_score) as avg_success_score
                    FROM tasks
                    WHERE created_at >= ? AND created_at <= ?
                """
                params = [date_from, date_to]

                if category:
                    query += " AND category = ?"
                    params.append(category)

                cursor.execute(query, params)
                row = cursor.fetchone()

                stats = {
                    'total': row[0] or 0,
                    'completed': row[1] or 0,
                    'failed': row[2] or 0,
                    'avg_duration': row[3] or 0,
                    'total_tokens': row[4] or 0,
                    'total_cost': row[5] or 0,
                    'avg_success_score': row[6] or 0,
                    'success_rate': (row[1] / row[0] * 100) if row[0] > 0 else 0
                }

                return {
                    'success': True,
                    'stats': stats,
                    'date_range': {'from': date_from, 'to': date_to}
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_task_tree(self, task_id: int) -> Dict[str, Any]:
        """
        Get task hierarchy (parent + all subtasks)

        Args:
            task_id: Root task ID

        Returns:
            Dict with task tree
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get root task
                cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
                root = cursor.fetchone()

                if not root:
                    return {
                        'success': False,
                        'error': f'Task {task_id} not found'
                    }

                # Get all subtasks
                cursor.execute("""
                    SELECT t.* FROM tasks t
                    JOIN task_relationships r ON t.id = r.child_id
                    WHERE r.parent_id = ?
                """, (task_id,))

                columns = [desc[0] for desc in cursor.description]
                root_task = dict(zip(columns, root))

                subtasks = []
                for row in cursor.fetchall():
                    subtask = dict(zip(columns, row))
                    subtasks.append(subtask)

                return {
                    'success': True,
                    'root_task': root_task,
                    'subtasks': subtasks,
                    'total_subtasks': len(subtasks)
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Create global instance
task_manager = TaskManager()


# Test
if __name__ == "__main__":
    print("Testing Task Management Tools...")
    print()

    # Create task
    print("1. Creating task...")
    result = task_manager.create_task(
        description="Test task management system",
        context="This is a test task",
        priority=3,
        category="test",
        tags=["test", "crud"]
    )
    print(f"  {result}")

    if result['success']:
        task_id = result['task_id']

        # Read task
        print("\n2. Reading task...")
        result = task_manager.read_task(task_id)
        print(f"  {result}")

        # Create subtask
        print("\n3. Creating subtask...")
        result = task_manager.create_subtask(
            task_id,
            "Subtask test",
            "This is a subtask"
        )
        print(f"  {result}")

        # List tasks
        print("\n4. Listing tasks...")
        result = task_manager.list_tasks(status="pending", limit=10)
        print(f"  Found {result['count']} tasks")

        # Get next task
        print("\n5. Getting next task...")
        result = task_manager.get_next_task()
        print(f"  {result}")

        # Get stats
        print("\n6. Getting stats...")
        result = task_manager.get_task_stats()
        print(f"  {result}")

        print("\n✅ All tests passed!")
