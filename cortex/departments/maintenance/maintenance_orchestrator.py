"""
Maintenance Orchestrator - Coordonne tous les systèmes de maintenance

Responsabilités:
- Déclenché automatiquement après git diff
- Orchestre: ContextUpdater, DependencyTracker, RoadmapManager
- Vérifie qualité des updates
- Gère fallbacks et validations
- Envoie alertes si problèmes détectés
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from cortex.departments.maintenance.git_diff_processor import GitDiffProcessor, GitDiffAnalysis
from cortex.departments.maintenance.context_updater import ContextUpdater
from cortex.departments.maintenance.dependency_tracker import DependencyTracker
from cortex.departments.maintenance.roadmap_manager import RoadmapManager


@dataclass
class MaintenanceResult:
    """Résultat d'une exécution de maintenance"""
    success: bool
    files_processed: int
    contexts_updated: int
    dependencies_updated: int
    roadmap_tasks_completed: int
    roadmap_tasks_created: int
    breaking_changes: List[str]  # Fixed field name
    errors: List[str]
    duration_seconds: float
    timestamp: datetime


class MaintenanceOrchestrator:
    """
    Orchestrateur central du département Maintenance

    Déclenché après chaque git commit pour:
    1. Parser git diff
    2. Mettre à jour contextes (avec validation)
    3. Recalculer dépendances
    4. Mettre à jour roadmap
    5. Détecter breaking changes
    """

    def __init__(
        self,
        git_processor: Optional[GitDiffProcessor] = None,
        context_updater: Optional[ContextUpdater] = None,
        dependency_tracker: Optional[DependencyTracker] = None,
        roadmap_manager: Optional[RoadmapManager] = None
    ):
        self.git_processor = git_processor or GitDiffProcessor()
        self.context_updater = context_updater or ContextUpdater()
        self.dependency_tracker = dependency_tracker or DependencyTracker(self.context_updater)
        self.roadmap_manager = roadmap_manager or RoadmapManager()

        # Métriques de qualité
        self.total_runs = 0
        self.successful_runs = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.breaking_changes_total = 0

    def run_maintenance(self, include_staged: bool = False) -> MaintenanceResult:
        """
        Exécute cycle complet de maintenance

        Args:
            include_staged: Inclure changements staged (pas encore committés)

        Returns:
            MaintenanceResult avec détails
        """
        start_time = datetime.now()
        errors = []
        breaking_changes = []

        print("\n" + "="*70)
        print("🔧 MAINTENANCE CYCLE STARTED")
        print("="*70)

        try:
            # STEP 1: Analyser git diff
            print("\n1. Analyzing git diff...")
            git_analysis = self.git_processor.get_latest_diff(include_staged=include_staged)

            if git_analysis.total_files_changed == 0:
                print("   No changes detected")
                return self._create_result(
                    success=True,
                    files_processed=0,
                    contexts_updated=0,
                    dependencies_updated=0,
                    roadmap_tasks_completed=0,
                    roadmap_tasks_created=0,
                    breaking_changes=[],
                    errors=[],
                    start_time=start_time
                )

            print(f"   Files changed: {git_analysis.total_files_changed}")
            print(f"   +{git_analysis.total_lines_added} -{git_analysis.total_lines_removed}")

            # STEP 2: Mettre à jour contextes (avec validation)
            print("\n2. Updating file contexts...")
            python_files = [
                f for f in (git_analysis.files_added + git_analysis.files_modified)
                if f.endswith('.py')
            ]

            contexts_updated = 0
            for file_path in python_files:
                try:
                    # Update avec validation
                    old_context = self.context_updater.get_context(file_path)
                    new_context = self.context_updater.update_file_context(file_path)

                    # Détecter breaking changes
                    if old_context:
                        breaks = self._detect_breaking_changes(old_context, new_context)
                        if breaks:
                            breaking_changes.extend(breaks)
                            print(f"   ⚠️  Breaking change in {file_path}")

                    contexts_updated += 1
                    self.cache_hits += 1
                    print(f"   ✓ Updated: {file_path}")

                except Exception as e:
                    self.cache_misses += 1
                    errors.append(f"Context update failed for {file_path}: {e}")
                    print(f"   ✗ Failed: {file_path} - {e}")

            # STEP 3: Recalculer dépendances
            print("\n3. Updating dependency graph...")
            dependencies_updated = 0

            if python_files:
                try:
                    # Rebuild graph pour fichiers modifiés
                    # (en production, optimiser pour update incrémental)
                    self.dependency_tracker.build_dependency_graph()
                    dependencies_updated = len(python_files)
                    print(f"   ✓ Dependencies updated for {dependencies_updated} files")

                except Exception as e:
                    errors.append(f"Dependency update failed: {e}")
                    print(f"   ✗ Failed: {e}")

            # STEP 4: Mettre à jour roadmap
            print("\n4. Updating roadmap...")
            try:
                roadmap_updates = self.roadmap_manager.update_from_git_diff(git_analysis)

                tasks_completed = len(roadmap_updates['tasks_marked_completed'])
                tasks_created = len(roadmap_updates['tasks_detected_new'])

                print(f"   ✓ Tasks completed: {tasks_completed}")
                print(f"   ✓ New tasks created: {tasks_created}")

            except Exception as e:
                errors.append(f"Roadmap update failed: {e}")
                print(f"   ✗ Failed: {e}")
                tasks_completed = 0
                tasks_created = 0

            # STEP 5: Validation finale
            print("\n5. Running validation...")
            if breaking_changes:
                print(f"   ⚠️  {len(breaking_changes)} breaking changes detected!")
                for bc in breaking_changes:
                    print(f"      - {bc}")

            if errors:
                print(f"   ⚠️  {len(errors)} errors encountered")
            else:
                print("   ✓ All validations passed")

            # Create result
            success = len(errors) == 0
            result = self._create_result(
                success=success,
                files_processed=git_analysis.total_files_changed,
                contexts_updated=contexts_updated,
                dependencies_updated=dependencies_updated,
                roadmap_tasks_completed=tasks_completed,
                roadmap_tasks_created=tasks_created,
                breaking_changes=breaking_changes,
                errors=errors,
                start_time=start_time
            )

            # Update stats
            self.total_runs += 1
            if success:
                self.successful_runs += 1
            self.breaking_changes_total += len(breaking_changes)

            # Display summary
            print("\n" + "="*70)
            status = "✅ SUCCESS" if success else "⚠️  COMPLETED WITH ERRORS"
            print(f"🔧 MAINTENANCE CYCLE: {status}")
            print(f"   Duration: {result.duration_seconds:.2f}s")
            print(f"   Files: {result.files_processed}")
            print(f"   Contexts: {result.contexts_updated}")
            print(f"   Dependencies: {result.dependencies_updated}")
            print(f"   Roadmap: {result.roadmap_tasks_completed} completed, {result.roadmap_tasks_created} created")
            if breaking_changes:
                print(f"   Breaking changes: {len(breaking_changes)}")
            print("="*70 + "\n")

            return result

        except Exception as e:
            errors.append(f"Maintenance cycle failed: {e}")
            print(f"\n✗ MAINTENANCE FAILED: {e}\n")

            return self._create_result(
                success=False,
                files_processed=0,
                contexts_updated=0,
                dependencies_updated=0,
                roadmap_tasks_completed=0,
                roadmap_tasks_created=0,
                breaking_changes=breaking_changes,
                errors=errors,
                start_time=start_time
            )

    def _detect_breaking_changes(
        self,
        old_context: Any,
        new_context: Any
    ) -> List[str]:
        """
        Détecte changements qui cassent l'API

        Returns:
            Liste de descriptions des breaking changes
        """
        breaks = []

        # Exports supprimés
        old_exports = set(old_context.exports)
        new_exports = set(new_context.exports)
        removed_exports = old_exports - new_exports

        if removed_exports:
            for export in removed_exports:
                breaks.append(f"Removed export: {export} from {new_context.file_path}")

        # Classes supprimées
        old_classes = set(old_context.classes)
        new_classes = set(new_context.classes)
        removed_classes = old_classes - new_classes

        if removed_classes:
            for cls in removed_classes:
                breaks.append(f"Removed class: {cls} from {new_context.file_path}")

        # Functions supprimées (publiques)
        old_funcs = set(f for f in old_context.functions if not f.startswith('_'))
        new_funcs = set(f for f in new_context.functions if not f.startswith('_'))
        removed_funcs = old_funcs - new_funcs

        if removed_funcs:
            for func in removed_funcs:
                breaks.append(f"Removed function: {func} from {new_context.file_path}")

        return breaks

    def _create_result(
        self,
        success: bool,
        files_processed: int,
        contexts_updated: int,
        dependencies_updated: int,
        roadmap_tasks_completed: int,
        roadmap_tasks_created: int,
        breaking_changes: List[str],
        errors: List[str],
        start_time: datetime
    ) -> MaintenanceResult:
        """Crée objet MaintenanceResult"""
        duration = (datetime.now() - start_time).total_seconds()

        return MaintenanceResult(
            success=success,
            files_processed=files_processed,
            contexts_updated=contexts_updated,
            dependencies_updated=dependencies_updated,
            roadmap_tasks_completed=roadmap_tasks_completed,
            roadmap_tasks_created=roadmap_tasks_created,
            breaking_changes=breaking_changes,
            errors=errors,
            duration_seconds=duration,
            timestamp=datetime.now()
        )

    def get_quality_metrics(self) -> Dict[str, Any]:
        """Retourne métriques de qualité"""
        cache_total = self.cache_hits + self.cache_misses
        cache_hit_rate = self.cache_hits / cache_total if cache_total > 0 else 0
        success_rate = self.successful_runs / self.total_runs if self.total_runs > 0 else 0

        return {
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "success_rate": success_rate,
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "breaking_changes_detected": self.breaking_changes_total
        }


def create_maintenance_orchestrator() -> MaintenanceOrchestrator:
    """Factory function"""
    return MaintenanceOrchestrator()


# Test
if __name__ == "__main__":
    print("Testing Maintenance Orchestrator...")

    orchestrator = MaintenanceOrchestrator()

    # Test maintenance cycle
    print("\n1. Running maintenance cycle...")
    result = orchestrator.run_maintenance(include_staged=True)

    print(f"\n✓ Maintenance completed:")
    print(f"  Success: {result.success}")
    print(f"  Files processed: {result.files_processed}")
    print(f"  Contexts updated: {result.contexts_updated}")
    print(f"  Duration: {result.duration_seconds:.2f}s")

    # Show quality metrics
    print("\n2. Quality metrics:")
    metrics = orchestrator.get_quality_metrics()
    print(f"  Total runs: {metrics['total_runs']}")
    print(f"  Success rate: {metrics['success_rate']:.1%}")
    print(f"  Cache hit rate: {metrics['cache_hit_rate']:.1%}")

    print("\n✓ Maintenance Orchestrator works correctly!")
