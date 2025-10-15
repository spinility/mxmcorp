"""
Auto-Evolution System

Système qui permet à Cortex de créer dynamiquement:
- Nouveaux départements
- Nouveaux agents spécialisés
- Nouveaux outils bash

Basé sur l'analyse des patterns d'utilisation
"""

from cortex.core.auto_evolution.pattern_detector import PatternDetector, DetectedPattern
from cortex.core.auto_evolution.tool_evolver import ToolEvolver, GeneratedTool
from cortex.core.auto_evolution.agent_evolver import AgentEvolver, GeneratedAgent

__all__ = [
    'PatternDetector',
    'DetectedPattern',
    'ToolEvolver',
    'GeneratedTool',
    'AgentEvolver',
    'GeneratedAgent'
]
