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

# Import from new department structure
from cortex.departments.communication.agents.triage import TriageAgent, create_triage_agent
from cortex.departments.execution.agents.quick_actions import QuickActionsAgent, create_quick_actions_agent
from cortex.departments.communication.agents.communications import CommunicationsAgent, create_communications_agent
from cortex.departments.execution.agents.planner import PlannerAgent, create_planner_agent
from cortex.departments.maintenance.agents.maintenance import MaintenanceAgent, create_maintenance_agent
from cortex.departments.maintenance.agents.harmonizer import HarmonizationAgent, create_harmonization_agent
from cortex.departments.intelligence.agents.watcher import GitWatcherAgent, create_git_watcher_agent
from cortex.departments.optimization.agents.tester import TesterAgent, create_tester_agent

# Import from old structure (agents not yet migrated with memory integration)
from cortex.agents.tooler_agent import ToolerAgent, create_tooler_agent
from cortex.agents.smart_router_agent import SmartRouterAgent, create_smart_router_agent
from cortex.agents.quality_control_agent import QualityControlAgent, create_quality_control_agent
from cortex.agents.archivist_agent import ArchivistAgent, create_archivist_agent
from cortex.agents.context_agent import ContextAgent, create_context_agent

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
    'GitWatcherAgent',
    'ArchivistAgent',
    'ContextAgent',
    'TesterAgent',
    'create_triage_agent',
    'create_quick_actions_agent',
    'create_tooler_agent',
    'create_communications_agent',
    'create_planner_agent',
    'create_smart_router_agent',
    'create_maintenance_agent',
    'create_harmonization_agent',
    'create_quality_control_agent',
    'create_git_watcher_agent',
    'create_archivist_agent',
    'create_context_agent',
    'create_tester_agent'
]
