"""
Département de MAINTENANCE

Rôle: Garde tout à jour automatiquement basé sur git diff

Déclenché AUTOMATIQUEMENT après chaque modification de code

Agents:
- GitDiffProcessor (EXÉCUTANT) - Parse git diff
- ContextUpdater (EXÉCUTANT) - Met à jour contextes
- DependencyTracker (EXPERT) - Trace dépendances
- RoadmapManager (EXPERT) - Gère le roadmap complet
- DocumentationUpdater (EXÉCUTANT) - Met à jour docs

Actions automatiques:
1. Parse git diff
2. Met à jour cache de contexte
3. Met à jour graphe de dépendances
4. Met à jour roadmap (marque tâches complétées, identifie nouvelles)
5. Met à jour documentation (SITEPLAN, DEPENDENCIES, CHANGELOG)
"""

from cortex.departments.maintenance.git_diff_processor import GitDiffProcessor
from cortex.departments.maintenance.roadmap_manager import RoadmapManager

__all__ = [
    'GitDiffProcessor',
    'RoadmapManager'
]
