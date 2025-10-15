"""
TodoDB - Authenticated task pool database using SQLite

Features:
- Multi-user task pool with ownership
- Authentication via AuthManager + JWT
- Role-based permissions (admin/developer/viewer)
- Persistent SQLite storage
- Task assignment and tracking
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from cortex.core.auth_manager import AuthManager, UserRole
from cortex.core.model_router import ModelTier


@dataclass
class TodoTask:
    """Task in the pool"""
    id: int
    description: str
    context: str
    min_tier: str
    status: str  # pending, in_progress, completed, blocked
    owner_id: int
    owner_name: str
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    assigned_to: Optional[int] = None  # Can be assigned to another user

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return {
            'id': self.id,
            'description': self.description,
            'context': self.context,
            'min_tier': self.min_tier,
            'status': self.status,
            'owner_id': self.owner_id,
            'owner_name': self.owner_name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'completed_at': self.completed_at,
            'assigned_to': self.assigned_to
        }


class TodoDB:
    """Authenticated task pool database"""

    def __init__(
        self,
        db_path: str = "cortex/data/todo_pool.db",
        auth_manager: Optional[AuthManager] = None
    ):
        """
        Initialize TodoDB

        Args:
            db_path: Path to SQLite database
            auth_manager: AuthManager instance (creates new if None)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Auth manager (shared auth database)
        self.auth = auth_manager or AuthManager()

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    context TEXT NOT NULL,
                    min_tier TEXT NOT NULL,
                    status TEXT NOT NULL,
                    owner_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    assigned_to INTEGER,
                    FOREIGN KEY (owner_id) REFERENCES users(id)
                )
            """)

            # Task history for audit trail
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks(id)
                )
            """)

            conn.commit()

    def _check_permission(
        self,
        token: str,
        required_role: Optional[UserRole] = None,
        task_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Check if user has permission for operation

        Args:
            token: JWT token
            required_role: Minimum role required (None = any authenticated user)
            task_id: Task ID to check ownership (None = skip ownership check)

        Returns:
            Dict with permission status and user info
        """
        # Verify token
        auth_result = self.auth.verify_token(token)
        if not auth_result['success']:
            return auth_result

        user_role = UserRole(auth_result['role'])
        user_id = auth_result['user_id']

        # Check role requirement
        if required_role:
            # Admin can do everything
            if user_role == UserRole.ADMIN:
                return {
                    'success': True,
                    'user_id': user_id,
                    'username': auth_result['username'],
                    'role': user_role
                }

            # Check specific role
            role_hierarchy = {
                UserRole.VIEWER: 0,
                UserRole.DEVELOPER: 1,
                UserRole.ADMIN: 2
            }

            if role_hierarchy[user_role] < role_hierarchy[required_role]:
                return {
                    'success': False,
                    'error': f'Insufficient permissions. Required: {required_role.value}'
                }

        # Check task ownership if task_id provided
        if task_id is not None and user_role != UserRole.ADMIN:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT owner_id FROM tasks WHERE id = ?", (task_id,))
                row = cursor.fetchone()

                if not row:
                    return {
                        'success': False,
                        'error': 'Task not found'
                    }

                if row[0] != user_id:
                    return {
                        'success': False,
                        'error': 'You can only modify your own tasks'
                    }

        return {
            'success': True,
            'user_id': user_id,
            'username': auth_result['username'],
            'role': user_role
        }

    def _log_action(
        self,
        task_id: int,
        user_id: int,
        action: str,
        details: Optional[str] = None
    ):
        """Log task action to history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_history (task_id, user_id, action, timestamp, details)
                VALUES (?, ?, ?, ?, ?)
            """, (task_id, user_id, action, datetime.now().isoformat(), details))
            conn.commit()

    def add_task(
        self,
        token: str,
        description: str,
        context: str,
        min_tier: ModelTier
    ) -> Dict[str, Any]:
        """
        Add a new task to the pool

        Args:
            token: JWT authentication token
            description: Task description
            context: Optimized context
            min_tier: Minimum tier required

        Returns:
            Dict with success status and task info
        """
        # Check permission (developer role required)
        perm = self._check_permission(token, required_role=UserRole.DEVELOPER)
        if not perm['success']:
            return perm

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()

                cursor.execute("""
                    INSERT INTO tasks (
                        description, context, min_tier, status,
                        owner_id, created_at, updated_at
                    )
                    VALUES (?, ?, ?, 'pending', ?, ?, ?)
                """, (description, context, min_tier.value, perm['user_id'], now, now))

                task_id = cursor.lastrowid
                conn.commit()

                # Log action
                self._log_action(task_id, perm['user_id'], 'created')

                return {
                    'success': True,
                    'task_id': task_id,
                    'message': f'Task created successfully by {perm["username"]}'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create task: {str(e)}'
            }

    def get_task(self, token: str, task_id: int) -> Dict[str, Any]:
        """Get a specific task (any authenticated user can view)"""
        perm = self._check_permission(token)
        if not perm['success']:
            return perm

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM tasks WHERE id = ?
            """, (task_id,))

            row = cursor.fetchone()

            if not row:
                return {
                    'success': False,
                    'error': 'Task not found'
                }

            # Get owner name from auth manager
            owner = self.auth.get_user(row[5])
            owner_name = owner.username if owner else f"User#{row[5]}"

            task = TodoTask(
                id=row[0],
                description=row[1],
                context=row[2],
                min_tier=row[3],
                status=row[4],
                owner_id=row[5],
                owner_name=owner_name,
                created_at=row[6],
                updated_at=row[7],
                completed_at=row[8],
                assigned_to=row[9] if len(row) > 9 else None
            )

            return {
                'success': True,
                'task': task.to_dict()
            }

    def list_tasks(
        self,
        token: str,
        status: Optional[str] = None,
        owner_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        List tasks from the pool

        Args:
            token: JWT token
            status: Filter by status (None = all)
            owner_id: Filter by owner (None = all)

        Returns:
            Dict with task list
        """
        perm = self._check_permission(token)
        if not perm['success']:
            return perm

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Build query
            query = "SELECT * FROM tasks WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            if owner_id:
                query += " AND owner_id = ?"
                params.append(owner_id)

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)

            tasks = []
            for row in cursor.fetchall():
                # Get owner name from auth manager
                owner = self.auth.get_user(row[5])
                owner_name = owner.username if owner else f"User#{row[5]}"

                tasks.append(TodoTask(
                    id=row[0],
                    description=row[1],
                    context=row[2],
                    min_tier=row[3],
                    status=row[4],
                    owner_id=row[5],
                    owner_name=owner_name,
                    created_at=row[6],
                    updated_at=row[7],
                    completed_at=row[8],
                    assigned_to=row[9] if len(row) > 9 else None
                ).to_dict())

            return {
                'success': True,
                'tasks': tasks,
                'count': len(tasks)
            }

    def update_task_status(
        self,
        token: str,
        task_id: int,
        new_status: str
    ) -> Dict[str, Any]:
        """
        Update task status

        Args:
            token: JWT token
            task_id: Task ID
            new_status: New status

        Returns:
            Dict with success status
        """
        # Check permission (must own the task or be admin)
        perm = self._check_permission(token, task_id=task_id)
        if not perm['success']:
            return perm

        valid_statuses = ['pending', 'in_progress', 'completed', 'blocked']
        if new_status not in valid_statuses:
            return {
                'success': False,
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()

                update_data = {
                    'status': new_status,
                    'updated_at': now
                }

                if new_status == 'completed':
                    update_data['completed_at'] = now

                cursor.execute("""
                    UPDATE tasks
                    SET status = ?, updated_at = ?, completed_at = ?
                    WHERE id = ?
                """, (new_status, now, update_data.get('completed_at'), task_id))

                conn.commit()

                # Log action
                self._log_action(
                    task_id,
                    perm['user_id'],
                    'status_changed',
                    f'Changed to {new_status}'
                )

                return {
                    'success': True,
                    'message': f'Task status updated to {new_status}'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to update task: {str(e)}'
            }

    def get_statistics(self, token: str) -> Dict[str, Any]:
        """Get task pool statistics"""
        perm = self._check_permission(token)
        if not perm['success']:
            return perm

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Overall stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) as blocked
                FROM tasks
            """)

            row = cursor.fetchone()

            # User's own stats
            cursor.execute("""
                SELECT
                    COUNT(*) as my_total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as my_completed
                FROM tasks
                WHERE owner_id = ?
            """, (perm['user_id'],))

            my_row = cursor.fetchone()

            return {
                'success': True,
                'pool_stats': {
                    'total': row[0],
                    'pending': row[1],
                    'in_progress': row[2],
                    'completed': row[3],
                    'blocked': row[4],
                    'completion_rate': (row[3] / row[0] * 100) if row[0] > 0 else 0
                },
                'my_stats': {
                    'total': my_row[0],
                    'completed': my_row[1],
                    'completion_rate': (my_row[1] / my_row[0] * 100) if my_row[0] > 0 else 0
                }
            }


def create_todo_db(
    db_path: str = "cortex/data/todo_pool.db",
    auth_manager: Optional[AuthManager] = None
) -> TodoDB:
    """Factory function to create TodoDB"""
    return TodoDB(db_path, auth_manager)


# Test if run directly
if __name__ == "__main__":
    from cortex.core.auth_manager import create_auth_manager

    print("Testing TodoDB with Authentication...")

    # Create auth manager and TodoDB
    auth = create_auth_manager("cortex/data/test_auth.db")
    todo_db = create_todo_db("cortex/data/test_todo_pool.db", auth)

    # Login as admin
    print("\n1. Logging in as admin...")
    login_result = auth.login("Cortex", "cortex123")
    if not login_result['success']:
        print(f"✗ Login failed: {login_result['error']}")
        exit(1)

    token = login_result['token']
    print(f"✓ Logged in as {login_result['user']['username']}")

    # Add a task
    print("\n2. Adding a task...")
    task_result = todo_db.add_task(
        token=token,
        description="Implement user authentication",
        context="Add JWT-based auth with bcrypt password hashing",
        min_tier=ModelTier.DEEPSEEK
    )

    if task_result['success']:
        print(f"✓ {task_result['message']}")
        task_id = task_result['task_id']
    else:
        print(f"✗ Failed: {task_result['error']}")
        exit(1)

    # List tasks
    print("\n3. Listing all tasks...")
    list_result = todo_db.list_tasks(token)
    if list_result['success']:
        print(f"✓ Found {list_result['count']} tasks:")
        for task in list_result['tasks']:
            print(f"  - [{task['status']}] {task['description']} (by {task['owner_name']})")
    else:
        print(f"✗ Failed: {list_result['error']}")

    # Update status
    print("\n4. Updating task status...")
    update_result = todo_db.update_task_status(token, task_id, 'in_progress')
    if update_result['success']:
        print(f"✓ {update_result['message']}")
    else:
        print(f"✗ Failed: {update_result['error']}")

    # Get statistics
    print("\n5. Getting statistics...")
    stats_result = todo_db.get_statistics(token)
    if stats_result['success']:
        print(f"✓ Pool stats:")
        print(f"  Total: {stats_result['pool_stats']['total']}")
        print(f"  Pending: {stats_result['pool_stats']['pending']}")
        print(f"  In Progress: {stats_result['pool_stats']['in_progress']}")
        print(f"  Completed: {stats_result['pool_stats']['completed']}")
    else:
        print(f"✗ Failed: {stats_result['error']}")

    print("\n✓ TodoDB with authentication works correctly!")
