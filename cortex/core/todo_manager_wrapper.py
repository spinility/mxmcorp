"""
Todo Manager Wrapper - Bridge entre l'ancienne API JSON et TodoDB authentifié

Permet de migrer progressivement du système JSON au système TodoDB
tout en gardant la compatibilité avec l'API existante.

Fonctionnalités:
- Auto-login avec compte par défaut (Cortex)
- API identique à l'ancien TodoManager
- Utilise TodoDB en backend (SQLite + auth)
- Support multi-utilisateurs optionnel
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from cortex.core.model_router import ModelTier
from cortex.core.auth_manager import create_auth_manager, AuthManager
from cortex.core.todo_db import create_todo_db, TodoDB


class TaskStatus(Enum):
    """Statut d'une tâche (compatible avec l'ancien système)"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


@dataclass
class TodoTask:
    """
    Tâche compatible avec l'ancien système
    (wrapper autour des tâches TodoDB)
    """
    id: str
    description: str
    context: str
    min_tier: str
    status: TaskStatus
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    parent_task_id: Optional[str] = None
    owner_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dict"""
        return {
            'id': self.id,
            'description': self.description,
            'context': self.context,
            'min_tier': self.min_tier,
            'status': self.status.value,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'completed_at': self.completed_at,
            'parent_task_id': self.parent_task_id,
            'owner_name': self.owner_name
        }


class TodoManager:
    """
    Wrapper qui utilise TodoDB en backend avec auto-authentication

    API compatible avec l'ancien TodoManager basé sur JSON
    """

    def __init__(
        self,
        storage_path: str = "cortex/data/todolist.json",
        username: str = "Cortex",
        password: str = "cortex123"
    ):
        """
        Initialize Todo Manager with TodoDB backend

        Args:
            storage_path: Ignoré (gardé pour compatibilité)
            username: Username pour auto-login
            password: Password pour auto-login
        """
        # Initialiser auth et TodoDB
        self.auth_manager = create_auth_manager()
        self.todo_db = create_todo_db(auth_manager=self.auth_manager)

        # Auto-login avec compte par défaut
        self.username = username
        self.password = password
        self.token = self._auto_login()

    def _auto_login(self) -> str:
        """Auto-login et retourne le token JWT"""
        result = self.auth_manager.login(self.username, self.password)
        if not result['success']:
            # Si échec, essayer de créer le compte
            from cortex.core.auth_manager import UserRole
            reg_result = self.auth_manager.register_user(
                self.username,
                self.password,
                UserRole.ADMIN
            )
            if reg_result['success']:
                # Retry login
                result = self.auth_manager.login(self.username, self.password)

        if not result['success']:
            raise RuntimeError(f"Auto-login failed: {result['error']}")

        return result['token']

    def _convert_db_task(self, db_task: Dict[str, Any]) -> TodoTask:
        """Convertit une tâche TodoDB en TodoTask"""
        return TodoTask(
            id=str(db_task['id']),
            description=db_task['description'],
            context=db_task['context'],
            min_tier=db_task['min_tier'],
            status=TaskStatus(db_task['status']),
            created_at=db_task['created_at'],
            updated_at=db_task['updated_at'],
            completed_at=db_task.get('completed_at'),
            parent_task_id=None,  # TodoDB n'a pas encore parent_task_id
            owner_name=db_task.get('owner_name')
        )

    def add_task(
        self,
        description: str,
        context: str,
        min_tier: ModelTier,
        parent_task_id: Optional[str] = None
    ) -> TodoTask:
        """
        Ajoute une nouvelle tâche

        Args:
            description: Description de la tâche
            context: Contexte optimisé pour l'exécution
            min_tier: Tier minimum requis
            parent_task_id: Ignoré (pas encore supporté par TodoDB)

        Returns:
            La tâche créée
        """
        result = self.todo_db.add_task(
            token=self.token,
            description=description,
            context=context,
            min_tier=min_tier
        )

        if not result['success']:
            raise RuntimeError(f"Failed to add task: {result['error']}")

        # Récupérer la tâche créée
        task_result = self.todo_db.get_task(self.token, result['task_id'])
        if not task_result['success']:
            raise RuntimeError(f"Failed to retrieve created task: {task_result['error']}")

        return self._convert_db_task(task_result['task'])

    def get_task(self, task_id: str) -> Optional[TodoTask]:
        """Récupère une tâche par son ID"""
        result = self.todo_db.get_task(self.token, int(task_id.split('_')[-1]) if '_' in task_id else int(task_id))

        if not result['success']:
            return None

        return self._convert_db_task(result['task'])

    def get_next_pending_task(self) -> Optional[TodoTask]:
        """Récupère la prochaine tâche en attente"""
        result = self.todo_db.list_tasks(self.token, status='pending')

        if not result['success'] or result['count'] == 0:
            return None

        # Retourner la première tâche pending
        return self._convert_db_task(result['tasks'][0])

    def get_current_task(self) -> Optional[TodoTask]:
        """Récupère la tâche en cours"""
        result = self.todo_db.list_tasks(self.token, status='in_progress')

        if not result['success'] or result['count'] == 0:
            return None

        # Retourner la première tâche in_progress
        return self._convert_db_task(result['tasks'][0])

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus
    ) -> bool:
        """
        Met à jour le statut d'une tâche

        Args:
            task_id: ID de la tâche
            status: Nouveau statut

        Returns:
            True si la mise à jour a réussi
        """
        # Convertir task_id string en int
        db_task_id = int(task_id.split('_')[-1]) if '_' in task_id else int(task_id)

        result = self.todo_db.update_task_status(
            token=self.token,
            task_id=db_task_id,
            new_status=status.value
        )

        return result['success']

    def get_all_tasks(
        self,
        status: Optional[TaskStatus] = None
    ) -> List[TodoTask]:
        """
        Récupère toutes les tâches (optionnellement filtrées par statut)

        Args:
            status: Statut à filtrer (None = toutes)

        Returns:
            Liste des tâches
        """
        result = self.todo_db.list_tasks(
            self.token,
            status=status.value if status else None
        )

        if not result['success']:
            return []

        return [self._convert_db_task(task) for task in result['tasks']]

    def get_tasks_summary(self) -> Dict[str, Any]:
        """
        Obtient un résumé de la TodoList

        Returns:
            Dict avec statistiques
        """
        result = self.todo_db.get_statistics(self.token)

        if not result['success']:
            return {
                'total': 0,
                'pending': 0,
                'in_progress': 0,
                'completed': 0,
                'blocked': 0,
                'progress_percent': 0
            }

        pool_stats = result['pool_stats']

        return {
            'total': pool_stats['total'],
            'pending': pool_stats['pending'],
            'in_progress': pool_stats['in_progress'],
            'completed': pool_stats['completed'],
            'blocked': pool_stats['blocked'],
            'progress_percent': pool_stats['completion_rate']
        }

    def clear_completed_tasks(self):
        """
        Supprime toutes les tâches complétées

        Note: Pas encore implémenté dans TodoDB
        """
        print("Warning: clear_completed_tasks not yet implemented in TodoDB")

    def delete_task(self, task_id: str) -> bool:
        """
        Supprime une tâche

        Note: Pas encore implémenté dans TodoDB

        Args:
            task_id: ID de la tâche à supprimer

        Returns:
            False (not implemented)
        """
        print("Warning: delete_task not yet implemented in TodoDB")
        return False


def create_todo_manager(
    storage_path: str = "cortex/data/todolist.json",
    username: str = "Cortex",
    password: str = "cortex123"
) -> TodoManager:
    """
    Factory function pour créer un TodoManager

    Args:
        storage_path: Ignoré (gardé pour compatibilité)
        username: Username pour auto-login (default: Cortex)
        password: Password pour auto-login (default: cortex123)

    Returns:
        TodoManager avec TodoDB backend
    """
    return TodoManager(storage_path, username, password)


# Test si exécuté directement
if __name__ == "__main__":
    print("Testing Todo Manager Wrapper with TodoDB backend...")

    manager = TodoManager()

    # Test 1: Ajouter une tâche
    print("\n1. Adding a task...")
    task1 = manager.add_task(
        description="Implement authentication system",
        context="User requested OAuth2 integration. Existing auth is basic. Need to add JWT tokens.",
        min_tier=ModelTier.DEEPSEEK
    )
    print(f"✓ Created task: {task1.id} - {task1.description}")
    print(f"  Owner: {task1.owner_name}")

    # Test 2: Récupérer la prochaine tâche
    print("\n2. Getting next pending task...")
    next_task = manager.get_next_pending_task()
    if next_task:
        print(f"✓ Next task: {next_task.description}")

    # Test 3: Mettre à jour le statut
    print("\n3. Updating task status...")
    success = manager.update_task_status(task1.id, TaskStatus.IN_PROGRESS)
    if success:
        print(f"✓ Task status updated to IN_PROGRESS")

    # Test 4: Résumé
    print("\n4. Getting summary...")
    summary = manager.get_tasks_summary()
    print(f"✓ Summary:")
    print(f"  Total: {summary['total']}")
    print(f"  Pending: {summary['pending']}")
    print(f"  In Progress: {summary['in_progress']}")
    print(f"  Completed: {summary['completed']}")
    print(f"  Progress: {summary['progress_percent']:.1f}%")

    # Test 5: Liste toutes les tâches
    print("\n5. Listing all tasks...")
    all_tasks = manager.get_all_tasks()
    print(f"✓ Found {len(all_tasks)} tasks:")
    for task in all_tasks:
        print(f"  - [{task.status.value}] {task.description} (by {task.owner_name})")

    print("\n✓ Todo Manager Wrapper works correctly with TodoDB backend!")
