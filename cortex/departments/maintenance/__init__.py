"""
Département de MAINTENANCE

Rôle: Garde tout à jour automatiquement basé sur git diff

Déclenché AUTOMATIQUEMENT après chaque modification de code

Agents:
- GitDiffProcessor (EXÉCUTANT) - Parse git diff
- ContextUpdater (EXÉCUTANT) - Met à jour contextes (économie 95% tokens)
- DependencyTracker (EXPERT) - Trace dépendances et détecte cycles
- RoadmapManager (EXPERT) - Gère le roadmap complet
- MaintenanceOrchestrator (DIRECTEUR) - Coordonne tous les agents

Actions automatiques:
1. Parse git diff
2. Met à jour cache de contexte (AST parsing)
3. Met à jour graphe de dépendances (imports/exports)
4. Détecte breaking changes automatiquement
5. Met à jour roadmap (marque tâches complétées, identifie nouvelles)
6. Validation qualité multi-niveaux
"""

from cortex.departments.maintenance.git_diff_processor import GitDiffProcessor
from cortex.departments.maintenance.roadmap_manager import RoadmapManager
from cortex.departments.maintenance.context_updater import ContextUpdater
from cortex.departments.maintenance.dependency_tracker import DependencyTracker
from cortex.departments.maintenance.maintenance_orchestrator import MaintenanceOrchestrator

__all__ = [
    'GitDiffProcessor',
    'RoadmapManager',
    'ContextUpdater',
    'DependencyTracker',
    'MaintenanceOrchestrator'
]
