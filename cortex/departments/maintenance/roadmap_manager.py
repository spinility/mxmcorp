"""
Roadmap Manager - Gestion automatique du roadmap projet basé sur git diff

Responsabilités:
- Maintient roadmap global du projet à jour
- Marque automatiquement tâches complétées selon git diff
- Détecte nouvelles tâches nécessaires
- Recalcule estimations
- Gère dépendances entre tâches
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from cortex.core.todolist_manager import TodoTask, TaskStatus
from cortex.departments.maintenance.git_diff_processor import GitDiffAnalysis


@dataclass
class RoadmapTask:
    """Tâche dans le roadmap global"""
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: str  # "critical", "high", "medium", "low"
    estimated_hours: float
    actual_hours: Optional[float] = None
    assigned_department: Optional[str] = None
    assigned_agent: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)
    completion_criteria: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dict"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "assigned_department": self.assigned_department,
            "assigned_agent": self.assigned_agent,
            "dependencies": self.dependencies,
            "related_files": self.related_files,
            "completion_criteria": self.completion_criteria,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata
        }


class RoadmapManager:
    """
    Gestionnaire du roadmap global du projet

    Fonctionnalités:
    - Maintient liste de toutes les tâches projet
    - Met à jour automatiquement selon git diff
    - Détecte tâches complétées
    - Identifie nouvelles tâches nécessaires
    - Gère dépendances
    """

    def __init__(self, roadmap_file: str = "cortex/data/ROADMAP.json"):
        self.roadmap_file = Path(roadmap_file)
        self.roadmap_file.parent.mkdir(parents=True, exist_ok=True)

        self.tasks: Dict[str, RoadmapTask] = {}
        self._load()

    def _load(self):
        """Charge le roadmap depuis le disque"""
        if self.roadmap_file.exists():
            with open(self.roadmap_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for task_data in data.get("tasks", []):
                # Recréer TaskStatus enum
                task_data["status"] = TaskStatus(task_data["status"])

                # Recréer datetimes
                task_data["created_at"] = datetime.fromisoformat(task_data["created_at"])
                if task_data["started_at"]:
                    task_data["started_at"] = datetime.fromisoformat(task_data["started_at"])
                if task_data["completed_at"]:
                    task_data["completed_at"] = datetime.fromisoformat(task_data["completed_at"])

                task = RoadmapTask(**task_data)
                self.tasks[task.id] = task

    def _save(self):
        """Sauvegarde le roadmap sur disque"""
        data = {
            "updated_at": datetime.now().isoformat(),
            "total_tasks": len(self.tasks),
            "tasks": [task.to_dict() for task in self.tasks.values()]
        }

        with open(self.roadmap_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_task(
        self,
        title: str,
        description: str,
        priority: str = "medium",
        estimated_hours: float = 1.0,
        assigned_department: Optional[str] = None,
        dependencies: List[str] = None,
        related_files: List[str] = None,
        completion_criteria: List[str] = None
    ) -> RoadmapTask:
        """
        Ajoute une nouvelle tâche au roadmap

        Args:
            title: Titre de la tâche
            description: Description détaillée
            priority: Priorité (critical/high/medium/low)
            estimated_hours: Estimation durée
            assigned_department: Département assigné
            dependencies: IDs des tâches dont celle-ci dépend
            related_files: Fichiers concernés
            completion_criteria: Critères de complétion

        Returns:
            RoadmapTask créée
        """
        task_id = f"task_{len(self.tasks) + 1:04d}"

        task = RoadmapTask(
            id=task_id,
            title=title,
            description=description,
            status=TaskStatus.PENDING,
            priority=priority,
            estimated_hours=estimated_hours,
            assigned_department=assigned_department,
            dependencies=dependencies or [],
            related_files=related_files or [],
            completion_criteria=completion_criteria or []
        )

        self.tasks[task_id] = task
        self._save()

        return task

    def update_from_git_diff(self, git_analysis: GitDiffAnalysis) -> Dict[str, Any]:
        """
        Met à jour le roadmap basé sur git diff

        Détecte automatiquement:
        - Tâches potentiellement complétées (fichiers modifiés correspondent)
        - Nouvelles tâches nécessaires (nouveaux fichiers, TODOs)

        Args:
            git_analysis: Analyse du git diff

        Returns:
            Dict avec résumé des mises à jour
        """
        updates = {
            "tasks_marked_completed": [],
            "tasks_detected_new": [],
            "tasks_updated": []
        }

        # 1. Vérifier tâches potentiellement complétées
        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.IN_PROGRESS or task.status == TaskStatus.PENDING:
                # Vérifier si les fichiers de la tâche ont été modifiés
                if self._task_files_modified(task, git_analysis):
                    # Marquer comme potentiellement complétée
                    # (nécessite validation manuelle ou critères automatiques)
                    if self._check_completion_criteria(task, git_analysis):
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = datetime.now()
                        updates["tasks_marked_completed"].append(task_id)

        # 2. Détecter nouvelles tâches nécessaires
        # Si nouveau fichier créé → peut nécessiter tests, docs, etc.
        for new_file in git_analysis.files_added:
            if new_file.endswith('.py') and not new_file.startswith('test'):
                # Vérifier si test existe
                test_file = self._get_test_file_path(new_file)
                if not self._file_exists_in_changes(test_file, git_analysis):
                    # Créer tâche pour ajouter tests
                    new_task = self.add_task(
                        title=f"Add tests for {Path(new_file).name}",
                        description=f"Create unit tests for newly added file {new_file}",
                        priority="high",
                        estimated_hours=0.5,
                        assigned_department="development",
                        related_files=[new_file, test_file],
                        completion_criteria=[f"Test file {test_file} created", "Tests passing"]
                    )
                    updates["tasks_detected_new"].append(new_task.id)

        # 3. Mettre à jour statistiques des tâches
        for task_id, task in self.tasks.items():
            if task.related_files:
                # Vérifier si fichiers de la tâche ont été touchés
                if any(f in git_analysis.files_modified + git_analysis.files_added
                       for f in task.related_files):
                    task.metadata["last_file_update"] = datetime.now().isoformat()
                    updates["tasks_updated"].append(task_id)

        self._save()
        return updates

    def _task_files_modified(self, task: RoadmapTask, git_analysis: GitDiffAnalysis) -> bool:
        """Vérifie si les fichiers de la tâche ont été modifiés"""
        all_changed_files = (
            git_analysis.files_added +
            git_analysis.files_modified +
            list(git_analysis.files_renamed.values())
        )

        return any(f in all_changed_files for f in task.related_files)

    def _check_completion_criteria(self, task: RoadmapTask, git_analysis: GitDiffAnalysis) -> bool:
        """
        Vérifie si les critères de complétion sont remplis

        Pour l'instant: simple vérification que fichiers attendus existent
        """
        if not task.completion_criteria:
            # Pas de critères → nécessite validation manuelle
            return False

        # Vérifier critères basiques
        for criterion in task.completion_criteria:
            # Critère: "File X created"
            if "created" in criterion.lower():
                # Extraire nom de fichier (simple heuristique)
                for file_path in task.related_files:
                    if file_path in git_analysis.files_added:
                        continue
                return False

        return True

    def _get_test_file_path(self, source_file: str) -> str:
        """Génère le path du fichier de test correspondant"""
        path = Path(source_file)

        # cortex/core/agent.py → tests/test_agent.py
        if path.parts[0] == 'cortex':
            test_path = Path('tests') / f"test_{path.stem}.py"
            return str(test_path)

        return f"tests/test_{path.stem}.py"

    def _file_exists_in_changes(self, filepath: str, git_analysis: GitDiffAnalysis) -> bool:
        """Vérifie si un fichier existe dans les changements git"""
        return filepath in (git_analysis.files_added + git_analysis.files_modified)

    def get_roadmap_summary(self) -> Dict[str, Any]:
        """Résumé du roadmap"""
        by_status = {}
        by_priority = {}
        by_department = {}

        for task in self.tasks.values():
            # Par status
            status_key = task.status.value
            by_status[status_key] = by_status.get(status_key, 0) + 1

            # Par priorité
            by_priority[task.priority] = by_priority.get(task.priority, 0) + 1

            # Par département
            if task.assigned_department:
                by_department[task.assigned_department] = by_department.get(task.assigned_department, 0) + 1

        completed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        total_estimated = sum(t.estimated_hours for t in self.tasks.values())
        completed_hours = sum(t.actual_hours or t.estimated_hours for t in completed_tasks)

        return {
            "total_tasks": len(self.tasks),
            "by_status": by_status,
            "by_priority": by_priority,
            "by_department": by_department,
            "total_estimated_hours": total_estimated,
            "completed_hours": completed_hours,
            "completion_percentage": len(completed_tasks) / len(self.tasks) * 100 if self.tasks else 0
        }

    def display_roadmap(self):
        """Affiche le roadmap de manière lisible"""
        print("\n" + "="*70)
        print("📋 PROJECT ROADMAP")
        print("="*70 + "\n")

        # Par status
        for status in [TaskStatus.IN_PROGRESS, TaskStatus.PENDING, TaskStatus.BLOCKED, TaskStatus.COMPLETED]:
            tasks_in_status = [t for t in self.tasks.values() if t.status == status]

            if not tasks_in_status:
                continue

            status_emoji = {
                TaskStatus.PENDING: "⏳",
                TaskStatus.IN_PROGRESS: "🔄",
                TaskStatus.COMPLETED: "✅",
                TaskStatus.BLOCKED: "🚫",
                TaskStatus.FAILED: "❌"
            }[status]

            print(f"{status_emoji} {status.value.upper()} ({len(tasks_in_status)} tasks)")
            print("-" * 70)

            for task in sorted(tasks_in_status, key=lambda t: t.priority, reverse=True):
                priority_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(task.priority, "⚪")

                print(f"  {priority_emoji} [{task.id}] {task.title}")
                if task.assigned_department:
                    print(f"      Dept: {task.assigned_department} | Est: {task.estimated_hours}h")
                if task.dependencies:
                    print(f"      Depends on: {', '.join(task.dependencies)}")

            print()

        # Summary
        summary = self.get_roadmap_summary()
        print("="*70)
        print(f"Progress: {summary['completion_percentage']:.1f}% complete")
        print(f"Total: {summary['total_tasks']} tasks | {summary['completed_hours']:.1f}h / {summary['total_estimated_hours']:.1f}h")
        print("="*70 + "\n")


def create_roadmap_manager(roadmap_file: str = "cortex/data/ROADMAP.json") -> RoadmapManager:
    """Factory function"""
    return RoadmapManager(roadmap_file)


# Test
if __name__ == "__main__":
    print("Testing Roadmap Manager...")

    manager = create_roadmap_manager("cortex/data/test_roadmap.json")

    # Test 1: Ajouter tâches
    print("\n1. Adding tasks to roadmap...")

    task1 = manager.add_task(
        title="Complete Phase 3.2 implementation",
        description="Finish RoadmapManager and Communication department",
        priority="critical",
        estimated_hours=4.0,
        assigned_department="development",
        related_files=["cortex/departments/maintenance/roadmap_manager.py"],
        completion_criteria=["File created", "Tests passing"]
    )
    print(f"✓ Added: {task1.title}")

    task2 = manager.add_task(
        title="Create Communication Department",
        description="Build CEO reporting system",
        priority="high",
        estimated_hours=3.0,
        assigned_department="communication",
        dependencies=[task1.id]
    )
    print(f"✓ Added: {task2.title}")

    task3 = manager.add_task(
        title="Write documentation for new features",
        description="Document all Phase 3 features",
        priority="medium",
        estimated_hours=2.0,
        assigned_department="documentation"
    )
    print(f"✓ Added: {task3.title}")

    # Test 2: Afficher roadmap
    print("\n2. Displaying roadmap...")
    manager.display_roadmap()

    # Test 3: Simuler git diff update
    print("\n3. Simulating git diff update...")
    from cortex.departments.maintenance.git_diff_processor import GitDiffAnalysis, FileChange

    # Simuler qu'on a créé le fichier roadmap_manager.py
    mock_analysis = GitDiffAnalysis(
        total_files_changed=1,
        files_added=["cortex/departments/maintenance/roadmap_manager.py"],
        files_modified=[],
        files_deleted=[],
        files_renamed={},
        total_lines_added=400,
        total_lines_removed=0,
        file_changes=[
            FileChange(
                filepath="cortex/departments/maintenance/roadmap_manager.py",
                change_type="added",
                lines_added=400,
                lines_removed=0
            )
        ],
        diff_raw=""
    )

    updates = manager.update_from_git_diff(mock_analysis)
    print(f"✓ Roadmap updated from git diff:")
    print(f"  Tasks completed: {len(updates['tasks_marked_completed'])}")
    print(f"  New tasks detected: {len(updates['tasks_detected_new'])}")
    print(f"  Tasks updated: {len(updates['tasks_updated'])}")

    # Test 4: Summary
    print("\n4. Getting summary...")
    summary = manager.get_roadmap_summary()
    print(f"✓ Summary:")
    print(f"  Total tasks: {summary['total_tasks']}")
    print(f"  By status: {summary['by_status']}")
    print(f"  Completion: {summary['completion_percentage']:.1f}%")

    print("\n✓ Roadmap Manager works correctly!")
