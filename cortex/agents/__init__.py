"""
Cortex Agents - Specialized autonomous agents

Agents disponibles:
- Triage: Décide du routage optimal (direct vs expert)
- Tooler: Recherche et recommande des outils manquants
- Communications: Formule des recommandations pour l'utilisateur
- Planner: Détecte les demandes de planification et crée des tâches structurées
- SmartRouter: Route intelligemment vers les départements appropriés
- Maintenance: Gère les contextes globaux, par agent, par département
"""

from cortex.agents.triage_agent import TriageAgent, create_triage_agent
from cortex.agents.tooler_agent import ToolerAgent, create_tooler_agent
from cortex.agents.communications_agent import CommunicationsAgent, create_communications_agent
from cortex.agents.planner_agent import PlannerAgent, create_planner_agent
from cortex.agents.smart_router_agent import SmartRouterAgent, create_smart_router_agent
from cortex.agents.maintenance_agent import MaintenanceAgent, create_maintenance_agent

__all__ = [
    'TriageAgent',
    'ToolerAgent',
    'CommunicationsAgent',
    'PlannerAgent',
    'SmartRouterAgent',
    'MaintenanceAgent',
    'create_triage_agent',
    'create_tooler_agent',
    'create_communications_agent',
    'create_planner_agent',
    'create_smart_router_agent',
    'create_maintenance_agent'
]
