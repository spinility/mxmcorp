"""
Département d'OPTIMISATION

Rôle: Analyse tout ce qui se passe, apprend continuellement, optimise

Agents:
- HistoryAnalyzer (EXPERT) - Analyse l'historique
- SuccessPatternDetector (EXPERT) - Détecte patterns de succès
- FailureAnalyzer (EXPERT) - Analyse les échecs
- OptimizationRecommender (DIRECTEUR) - Recommande optimisations

Consulté AVANT toute action importante
Enregistre APRÈS chaque action
"""

from cortex.departments.optimization.history_analyzer import HistoryAnalyzer
from cortex.departments.optimization.optimization_knowledge import OptimizationKnowledge

__all__ = [
    'HistoryAnalyzer',
    'OptimizationKnowledge'
]
