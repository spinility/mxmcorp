"""
Département d'OPTIMISATION

Rôle: Analyse tout ce qui se passe, apprend continuellement, optimise

Agents:
- HistoryAnalyzer (EXPERT) - Analyse l'historique (TODO)
- SuccessPatternDetector (EXPERT) - Détecte patterns de succès (TODO)
- FailureAnalyzer (EXPERT) - Analyse les échecs (TODO)
- OptimizationRecommender (DIRECTEUR) - Recommande optimisations (TODO)

Composants actifs:
- OptimizationOrchestrator: Coordonne les optimisations basées sur QC
- OptimizationKnowledge: Base de connaissances d'optimisation

Consulté AVANT toute action importante
Enregistre APRÈS chaque action
"""

from cortex.departments.optimization.optimization_knowledge import OptimizationKnowledge
from cortex.departments.optimization.optimization_orchestrator import OptimizationOrchestrator

__all__ = [
    'OptimizationKnowledge',
    'OptimizationOrchestrator'
]
