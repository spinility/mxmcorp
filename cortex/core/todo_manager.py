"""
Todo Manager - Gestion de la TodoList persistante de Cortex

Chaque tâche contient:
- Description de la tâche
- Contexte optimisé (résumé des infos pertinentes)
- Tier minimum requis pour l'exécution
- Statut (pending/in_progress/completed)
- Timestamps de création/modification
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from cortex.core.model_router import ModelTier


class TaskStatus(Enum):
    """Statut d'une tâche"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


@dataclass
class TodoTask:
    """Une tâche dans la TodoList"""
    id: str
    description: str
    context: str  # Contexte optimisé pour l'exécution
    min_tier: str  # "nano", "deepseek", ou "claude"
    status: TaskStatus
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    parent_task_id: Optional[str] = None  # Pour les sous-tâches

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dict pour JSON"""
        data = asdict(self)
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TodoTask':
        """Crée une tâche depuis un dict"""
        data['status'] = TaskStatus(data['status'])
        return cls(**data)


class TodoManager:
    """Gestionnaire de TodoList persistante"""

    def __init__(self, storage_path: str = "cortex/data/todolist.json"):
        """
        Initialize Todo Manager

        Args:
            storage_path: Chemin du fichier JSON de stockage
        """
        self.storage_path = Path(storage_path)
        self.tasks: List[TodoTask] = []
        self._load()

    def _load(self):
        """Charge la TodoList depuis le fichier"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = [TodoTask.from_dict(task) for task in data.get('tasks', [])]
            except Exception as e:
                print(f"Warning: Failed to load todolist: {e}")
                self.tasks = []
        else:
            # Créer le répertoire si nécessaire
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.tasks = []

    def _save(self):
        """Sauvegarde la TodoList dans le fichier"""
        try:
            data = {
                'tasks': [task.to_dict() for task in self.tasks],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error: Failed to save todolist: {e}")

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
            parent_task_id: ID de la tâche parente (pour sous-tâches)

        Returns:
            La tâche créée
        """
        task_id = f"task_{len(self.tasks) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        now = datetime.now().isoformat()

        task = TodoTask(
            id=task_id,
            description=description,
            context=context,
            min_tier=min_tier.value,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            parent_task_id=parent_task_id
        )

        self.tasks.append(task)
        self._save()
        return task

    def get_task(self, task_id: str) -> Optional[TodoTask]:
        """Récupère une tâche par son ID"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_next_pending_task(self) -> Optional[TodoTask]:
        """Récupère la prochaine tâche en attente"""
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                return task
        return None

    def get_current_task(self) -> Optional[TodoTask]:
        """Récupère la tâche en cours"""
        for task in self.tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                return task
        return None

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
        task = self.get_task(task_id)
        if not task:
            return False

        task.status = status
        task.updated_at = datetime.now().isoformat()

        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now().isoformat()

        self._save()
        return True

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
        if status is None:
            return self.tasks
        return [task for task in self.tasks if task.status == status]

    def get_tasks_summary(self) -> Dict[str, Any]:
        """
        Obtient un résumé de la TodoList

        Returns:
            Dict avec statistiques
        """
        total = len(self.tasks)
        pending = len([t for t in self.tasks if t.status == TaskStatus.PENDING])
        in_progress = len([t for t in self.tasks if t.status == TaskStatus.IN_PROGRESS])
        completed = len([t for t in self.tasks if t.status == TaskStatus.COMPLETED])
        blocked = len([t for t in self.tasks if t.status == TaskStatus.BLOCKED])

        return {
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'completed': completed,
            'blocked': blocked,
            'progress_percent': (completed / total * 100) if total > 0 else 0
        }

    def clear_completed_tasks(self):
        """Supprime toutes les tâches complétées"""
        self.tasks = [t for t in self.tasks if t.status != TaskStatus.COMPLETED]
        self._save()

    def delete_task(self, task_id: str) -> bool:
        """
        Supprime une tâche

        Args:
            task_id: ID de la tâche à supprimer

        Returns:
            True si la suppression a réussi
        """
        initial_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.id != task_id]

        if len(self.tasks) < initial_len:
            self._save()
            return True
        return False


def create_todo_manager(storage_path: str = "cortex/data/todolist.json") -> TodoManager:
    """Factory function pour créer un TodoManager"""
    return TodoManager(storage_path)


# Test si exécuté directement
if __name__ == "__main__":
    print("Testing Todo Manager...")

    manager = TodoManager("cortex/data/test_todolist.json")

    # Test 1: Ajouter une tâche
    print("\n1. Adding a task...")
    task1 = manager.add_task(
        description="Implement authentication system",
        context="User requested OAuth2 integration. Existing auth is basic. Need to add JWT tokens.",
        min_tier=ModelTier.DEEPSEEK
    )
    print(f"Created task: {task1.id}")

    # Test 2: Récupérer la prochaine tâche
    print("\n2. Getting next pending task...")
    next_task = manager.get_next_pending_task()
    if next_task:
        print(f"Next task: {next_task.description}")

    # Test 3: Mettre à jour le statut
    print("\n3. Updating task status...")
    manager.update_task_status(task1.id, TaskStatus.IN_PROGRESS)
    print(f"Task status: {task1.status.value}")

    # Test 4: Résumé
    print("\n4. Getting summary...")
    summary = manager.get_tasks_summary()
    print(f"Summary: {summary}")

    print("\n✓ Todo Manager works correctly!")
