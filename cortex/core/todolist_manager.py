"""
TodoList Manager - Système de gestion de tâches avec checkboxes (style Claude Code)

Features:
- Affichage temps réel avec checkboxes ☐/☑
- États: pending, in_progress, completed, failed, blocked
- Tracking de durée et agent assigné
- Intégration avec département Maintenance

Usage:
    manager = TodoListManager()
    manager.create_task_list(["Task 1", "Task 2"], workflow="CODE_DEVELOPMENT")
    manager.start_task("task_0", "CodeWriterAgent")
    manager.complete_task("task_0")
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import json


class TaskStatus(Enum):
    """Status possibles d'une tâche"""
    PENDING = "pending"           # ☐ En attente
    IN_PROGRESS = "in_progress"   # ☐ 🔄 En cours
    COMPLETED = "completed"       # ☑ ✅ Complété
    FAILED = "failed"             # ☒ ❌ Échoué
    BLOCKED = "blocked"           # ⊘ 🚫 Bloqué


@dataclass
class TodoTask:
    """
    Tâche individuelle dans une todo list

    Attributes:
        id: Identifiant unique
        description: Description de la tâche
        status: Status actuel
        workflow: Workflow parent
        assigned_to: Agent assigné (si en cours)
        started_at: Timestamp de début
        completed_at: Timestamp de fin
        duration_seconds: Durée d'exécution
        error: Message d'erreur (si échec)
        dependencies: IDs des tâches dont celle-ci dépend
        metadata: Données additionnelles
    """
    id: str
    description: str
    status: TaskStatus
    created_at: datetime
    workflow: str
    assigned_to: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "workflow": self.workflow,
            "assigned_to": self.assigned_to,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
            "dependencies": self.dependencies,
            "metadata": self.metadata
        }


class TodoListManager:
    """
    Gestionnaire de todo list avec affichage checkboxes (style Claude Code)

    Affichage:
        📋 Workflow Name

        ☐ ⏳ Task 1 (pending)
        ☐ 🔄 Task 2 (in progress)
           └─> CodeWriterAgent is working...
        ☑ ✅ Task 3 (completed)
           └─> Completed in 5.2s
        ☒ ❌ Task 4 (failed)
           └─> Error: Syntax error in code
        ⊘ 🚫 Task 5 (blocked)
           └─> Waiting for Task 1
    """

    def __init__(self, storage_path: str = "cortex/data/todolists"):
        self.tasks: List[TodoTask] = []
        self.active_workflow: Optional[str] = None
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def create_task_list(self, task_descriptions: List[str], workflow: str) -> List[str]:
        """
        Crée une nouvelle liste de tâches

        Args:
            task_descriptions: Liste des descriptions de tâches
            workflow: Nom du workflow

        Returns:
            Liste des IDs de tâches créées
        """
        self.active_workflow = workflow
        self.tasks = []

        task_ids = []
        for i, description in enumerate(task_descriptions):
            task_id = f"task_{i}"
            task = TodoTask(
                id=task_id,
                description=description,
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                workflow=workflow
            )
            self.tasks.append(task)
            task_ids.append(task_id)

        self.display()
        self._save()
        return task_ids

    def start_task(self, task_id: str, agent_name: str):
        """
        Marque une tâche comme en cours

        Args:
            task_id: ID de la tâche
            agent_name: Nom de l'agent qui commence
        """
        task = self._get_task(task_id)
        task.status = TaskStatus.IN_PROGRESS
        task.assigned_to = agent_name
        task.started_at = datetime.now()

        self.display()
        self._save()

    def complete_task(self, task_id: str, metadata: Optional[Dict] = None):
        """
        Coche une tâche comme complétée (☐ → ☑)

        Args:
            task_id: ID de la tâche
            metadata: Métadonnées additionnelles
        """
        task = self._get_task(task_id)
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()

        if task.started_at:
            duration = (task.completed_at - task.started_at).total_seconds()
            task.duration_seconds = duration

        if metadata:
            task.metadata.update(metadata)

        self.display()
        self._save()

        # Notifier département Maintenance (si disponible)
        self._notify_maintenance(task)

    def fail_task(self, task_id: str, error: str):
        """
        Marque une tâche comme échouée (☐ → ☒)

        Args:
            task_id: ID de la tâche
            error: Message d'erreur
        """
        task = self._get_task(task_id)
        task.status = TaskStatus.FAILED
        task.error = error
        task.completed_at = datetime.now()

        if task.started_at:
            duration = (task.completed_at - task.started_at).total_seconds()
            task.duration_seconds = duration

        self.display()
        self._save()

    def block_task(self, task_id: str, reason: str, dependencies: List[str] = None):
        """
        Marque une tâche comme bloquée (☐ → ⊘)

        Args:
            task_id: ID de la tâche
            reason: Raison du blocage
            dependencies: IDs des tâches bloquantes
        """
        task = self._get_task(task_id)
        task.status = TaskStatus.BLOCKED
        task.error = reason

        if dependencies:
            task.dependencies.extend(dependencies)

        self.display()
        self._save()

    def unblock_task(self, task_id: str):
        """Débloque une tâche (⊘ → ☐)"""
        task = self._get_task(task_id)
        task.status = TaskStatus.PENDING
        task.error = None

        self.display()
        self._save()

    def display(self):
        """
        Affiche la todo list avec checkboxes

        Format style Claude Code:
            📋 Workflow Name

            ☐ ⏳ Task 1
            ☑ ✅ Task 2
               └─> Completed in 5.2s
        """
        if not self.active_workflow:
            return

        print(f"\n{'='*60}")
        print(f"📋 {self.active_workflow}")
        print(f"{'='*60}\n")

        for task in self.tasks:
            self._print_task(task)

        # Summary
        summary = self.get_summary()
        print(f"\n{'-'*60}")
        print(f"Progress: {summary['completed']}/{summary['total']} tasks "
              f"({summary['success_rate']:.1%} success rate)")
        if summary['total_duration'] > 0:
            print(f"Total time: {summary['total_duration']:.1f}s")
        print(f"{'-'*60}\n")

    def _print_task(self, task: TodoTask):
        """Affiche une tâche individuelle"""
        # Checkbox selon status
        checkbox = {
            TaskStatus.PENDING: "☐",
            TaskStatus.IN_PROGRESS: "☐",
            TaskStatus.COMPLETED: "☑",
            TaskStatus.FAILED: "☒",
            TaskStatus.BLOCKED: "⊘"
        }[task.status]

        # Emoji selon status
        emoji = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.BLOCKED: "🚫"
        }[task.status]

        # Ligne principale
        print(f"{checkbox} {emoji} {task.description}")

        # Détails selon status
        if task.status == TaskStatus.IN_PROGRESS:
            print(f"   └─> {task.assigned_to} is working...")

        elif task.status == TaskStatus.COMPLETED:
            if task.duration_seconds:
                print(f"   └─> Completed in {task.duration_seconds:.1f}s")
            if task.metadata:
                print(f"       Metadata: {task.metadata}")

        elif task.status == TaskStatus.FAILED:
            print(f"   └─> Error: {task.error}")
            if task.duration_seconds:
                print(f"       Failed after {task.duration_seconds:.1f}s")

        elif task.status == TaskStatus.BLOCKED:
            print(f"   └─> Blocked: {task.error}")
            if task.dependencies:
                deps_str = ", ".join(task.dependencies)
                print(f"       Waiting for: {deps_str}")

    def get_task(self, task_id: str) -> Optional[TodoTask]:
        """Récupère une tâche par ID"""
        return self._get_task(task_id)

    def get_summary(self) -> Dict[str, Any]:
        """
        Résumé de la todo list

        Returns:
            Dict avec statistiques
        """
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)
        blocked = sum(1 for t in self.tasks if t.status == TaskStatus.BLOCKED)
        in_progress = sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS)

        total_duration = sum(
            t.duration_seconds for t in self.tasks
            if t.duration_seconds is not None
        )

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "blocked": blocked,
            "in_progress": in_progress,
            "pending": total - completed - failed - blocked - in_progress,
            "success_rate": completed / total if total > 0 else 0.0,
            "total_duration": total_duration
        }

    def get_all_tasks(self) -> List[TodoTask]:
        """Retourne toutes les tâches"""
        return self.tasks

    def _get_task(self, task_id: str) -> TodoTask:
        """Récupère tâche ou lève exception"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise ValueError(f"Task '{task_id}' not found")

    def _save(self):
        """Sauvegarde la todo list sur disque"""
        if not self.active_workflow:
            return

        filename = f"{self.active_workflow}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.storage_path / filename

        data = {
            "workflow": self.active_workflow,
            "created_at": datetime.now().isoformat(),
            "tasks": [task.to_dict() for task in self.tasks],
            "summary": self.get_summary()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _notify_maintenance(self, task: TodoTask):
        """
        Notifie le département Maintenance qu'une tâche est complétée

        Le département Maintenance peut alors mettre à jour le roadmap
        """
        # TODO: Implémenter intégration avec département Maintenance
        # Pour l'instant, juste un placeholder
        pass


def create_todolist_manager() -> TodoListManager:
    """Factory function pour créer un TodoListManager"""
    return TodoListManager()


# Test si exécuté directement
if __name__ == "__main__":
    print("Testing TodoList Manager...")

    # Test 1: Créer todo list
    print("\n1. Creating todo list...")
    manager = TodoListManager()
    task_ids = manager.create_task_list([
        "Analyze codebase structure",
        "Create agent hierarchy",
        "Implement workflows",
        "Write tests",
        "Deploy to production"
    ], workflow="PHASE_3_IMPLEMENTATION")

    # Test 2: Démarrer tâche
    print("\n2. Starting first task...")
    manager.start_task(task_ids[0], "AnalysisAgent")
    input("Press Enter to continue...")

    # Test 3: Compléter tâche
    print("\n3. Completing first task...")
    manager.complete_task(task_ids[0], metadata={"files_analyzed": 42})
    input("Press Enter to continue...")

    # Test 4: Démarrer deuxième tâche
    print("\n4. Starting second task...")
    manager.start_task(task_ids[1], "ArchitectAgent")
    input("Press Enter to continue...")

    # Test 5: Bloquer tâche
    print("\n5. Blocking third task...")
    manager.block_task(task_ids[2], "Waiting for architecture design", [task_ids[1]])
    input("Press Enter to continue...")

    # Test 6: Compléter deuxième
    print("\n6. Completing second task...")
    manager.complete_task(task_ids[1])
    input("Press Enter to continue...")

    # Test 7: Débloquer troisième
    print("\n7. Unblocking third task...")
    manager.unblock_task(task_ids[2])
    manager.start_task(task_ids[2], "DevelopmentAgent")
    input("Press Enter to continue...")

    # Test 8: Échouer une tâche
    print("\n8. Failing a task...")
    manager.fail_task(task_ids[3], "Tests not written yet - no test framework")
    input("Press Enter to continue...")

    # Test 9: Summary final
    print("\n9. Final summary...")
    summary = manager.get_summary()
    print(f"\nFinal Stats:")
    print(f"  Total: {summary['total']}")
    print(f"  Completed: {summary['completed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Success rate: {summary['success_rate']:.1%}")

    print("\n✓ TodoList Manager works correctly!")
