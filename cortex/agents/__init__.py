"""
Cortex Agents - Specialized autonomous agents

Agents disponibles:
- Triage: Décide du routage optimal (direct vs expert)
- QuickActions: Exécute des opérations atomiques ultra-simples (1 outil read-only)
- Tooler: Recherche et recommande des outils manquants
- Communications: Formule des recommandations pour l'utilisateur
- Planner: Détecte les demandes de planification et crée des tâches structurées
- SmartRouter: Route intelligemment vers les départements appropriés
- Maintenance: Gère les contextes globaux, par agent, par département
- Harmonization: Assure cohérence, synergie et non-duplication architecturale
- QualityControl: Analyse et évalue la qualité du traitement des requêtes
"""

from cortex.agents.triage_agent import TriageAgent, create_triage_agent
from cortex.agents.quick_actions_agent import QuickActionsAgent, create_quick_actions_agent
from cortex.agents.tooler_agent import ToolerAgent, create_tooler_agent
from cortex.agents.communications_agent import CommunicationsAgent, create_communications_agent
from cortex.agents.planner_agent import PlannerAgent, create_planner_agent
from cortex.agents.smart_router_agent import SmartRouterAgent, create_smart_router_agent
from cortex.agents.maintenance_agent import MaintenanceAgent, create_maintenance_agent
from cortex.agents.harmonization_agent import HarmonizationAgent, create_harmonization_agent
from cortex.agents.quality_control_agent import QualityControlAgent, create_quality_control_agent

__all__ = [
    'TriageAgent',
    'QuickActionsAgent',
    'ToolerAgent',
    'CommunicationsAgent',
    'PlannerAgent',
    'SmartRouterAgent',
    'MaintenanceAgent',
    'HarmonizationAgent',
    'QualityControlAgent',
    'create_triage_agent',
    'create_quick_actions_agent',
    'create_tooler_agent',
    'create_communications_agent',
    'create_planner_agent',
    'create_smart_router_agent',
    'create_maintenance_agent',
    'create_harmonization_agent',
    'create_quality_control_agent'
]
