"""
Agent Hierarchy - Système complet de gestion des agents
Inclut les départements RH et Outils pour création dynamique
Seuls les HRAgents peuvent créer des employés
"""

from typing import Dict, Any, Optional, List
from cortex.agents.ceo_agent import CEOAgent, create_ceo
from cortex.agents.directors import (
    create_all_directors,
    CodeDirector,
    DataDirector,
    CommunicationDirector,
    OperationsDirector
)
from cortex.agents.base_agent import BaseAgent
from cortex.agents.hr_department import HRDepartment
from cortex.agents.tools_department import ToolsDepartment
from cortex.agents.hr_agent import create_hr_agent, HRAgent
from cortex.agents.expert_pool import ExpertPool, create_expert_pool
from cortex.tools.builtin_tools import get_all_builtin_tools


class AgentHierarchy:
    """
    Hiérarchie complète des agents Cortex avec création dynamique

    Structure fixe:
    CEO (pure orchestration)
    ├── Code Director
    ├── Data Director
    ├── Communication Director
    └── Operations Director

    Départements de support:
    - HR Department: Crée des employés spécialisés à la demande
    - Tools Department: Fabrique des outils personnalisés
    - Expert Pool: Pool d'experts hautement spécialisés pour escalades complexes

    Structure dynamique:
    - Employés créés par HR selon les besoins
    - Outils créés par Tools Department selon les demandes
    - Experts consultés via ExpertPool pour tâches très complexes
    - Tous les employés peuvent demander nouveaux employés et outils
    """

    def __init__(self):
        # Départements de support (créés en premier)
        # Créer Tools d'abord, puis HR avec référence à Tools
        self.tools_department = ToolsDepartment()
        self.hr_department = HRDepartment(tools_department=self.tools_department)

        # Charger les outils built-in (disponibles pour tous)
        self.builtin_tools = get_all_builtin_tools()

        # Créer ExpertPool (utilisera les départements)
        self.expert_pool = create_expert_pool(
            tools_department=self.tools_department,
            hr_department=self.hr_department
        )

        # Créer un HRAgent (seul type d'agent autorisé à créer des employés)
        self.hr_agent: HRAgent = create_hr_agent(
            name="ChiefRecruiter",
            hr_department=self.hr_department,
            tools_department=self.tools_department
        )

        # Enregistrer le HR Agent dans le département
        self.hr_department.add_hr_agent(self.hr_agent)

        # Niveau 1: CEO (avec accès aux départements, HR Agent ET ExpertPool)
        self.ceo: CEOAgent = create_ceo(
            hr_department=self.hr_department,
            tools_department=self.tools_department,
            hr_agent=self.hr_agent,
            expert_pool=self.expert_pool
        )

        # Enregistrer les outils built-in pour le CEO
        self.ceo.register_tools(self.builtin_tools)

        # Niveau 2: Directors (avec accès aux départements)
        directors = create_all_directors()
        self.code_director: CodeDirector = directors["code"]
        self.data_director: DataDirector = directors["data"]
        self.communication_director: CommunicationDirector = directors["communication"]
        self.operations_director: OperationsDirector = directors["operations"]

        # Donner accès aux départements, expert pool et outils built-in à tous les Directors
        for director in [self.code_director, self.data_director,
                        self.communication_director, self.operations_director]:
            director.hr_department = self.hr_department
            director.tools_department = self.tools_department
            director.expert_pool = self.expert_pool
            # Enregistrer les outils built-in
            director.register_tools(self.builtin_tools)

        # Enregistrer les Directors sous le CEO
        self.ceo.register_subordinate(self.code_director)
        self.ceo.register_subordinate(self.data_director)
        self.ceo.register_subordinate(self.communication_director)
        self.ceo.register_subordinate(self.operations_director)

        # Note: Employés dynamiques créés à la demande via HR

    def process_request(
        self,
        user_request: str,
        use_ceo: bool = True,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Traite une requête utilisateur via la hiérarchie

        Args:
            user_request: Requête de l'utilisateur
            use_ceo: Passer par le CEO (recommandé) ou direct aux Directors
            verbose: Mode verbose

        Returns:
            Résultat avec succès, données, coûts, etc.
        """
        if use_ceo:
            # Analyse et délégation par le CEO
            return self.ceo.analyze_and_delegate(user_request, verbose=verbose)
        else:
            # Traitement direct (pour tests)
            return self.ceo.execute(user_request, verbose=verbose)

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Récupère un agent par son nom"""
        agents = {
            "CEO": self.ceo,
            "CodeDirector": self.code_director,
            "DataDirector": self.data_director,
            "CommunicationDirector": self.communication_director,
            "OperationsDirector": self.operations_director
        }
        return agents.get(name)

    def get_all_stats(self) -> Dict[str, Any]:
        """Récupère les stats de tous les agents et départements"""
        return {
            "ceo": self.ceo.get_stats(),
            "directors": {
                "code": self.code_director.get_stats(),
                "data": self.data_director.get_stats(),
                "communication": self.communication_director.get_stats(),
                "operations": self.operations_director.get_stats()
            },
            "departments": {
                "hr": self.hr_department.get_stats(),
                "tools": self.tools_department.get_stats(),
                "expert_pool": self.expert_pool.get_stats()
            },
            "total_cost": self._calculate_total_cost(),
            "total_tasks": self._calculate_total_tasks()
        }

    def _calculate_total_cost(self) -> float:
        """Calcule le coût total de tous les agents et départements"""
        agent_costs = (
            self.ceo.total_cost +
            self.code_director.total_cost +
            self.data_director.total_cost +
            self.communication_director.total_cost +
            self.operations_director.total_cost
        )

        department_costs = (
            self.hr_department.total_cost +
            self.hr_department.get_stats()["total_employee_cost"] +
            self.tools_department.total_cost +
            self.expert_pool.get_stats()["total_expert_cost"]
        )

        return agent_costs + department_costs

    def _calculate_total_tasks(self) -> int:
        """Calcule le nombre total de tâches incluant employés dynamiques"""
        agent_tasks = (
            self.ceo.task_count +
            self.code_director.task_count +
            self.data_director.task_count +
            self.communication_director.task_count +
            self.operations_director.task_count
        )

        employee_tasks = self.hr_department.get_stats()["total_employee_tasks"]

        return agent_tasks + employee_tasks

    def print_hierarchy(self):
        """Affiche la hiérarchie des agents avec départements"""
        print("\n" + "="*60)
        print("CORTEX MXMCORP - AGENT HIERARCHY")
        print("="*60)

        print(f"\n{self.ceo.config.name} ({self.ceo.config.role})")
        print(f"  Tasks: {self.ceo.task_count} | Cost: ${self.ceo.total_cost:.6f}")
        print(f"  Philosophy: ALWAYS delegates, NO direct execution")

        print(f"\n  DIRECTORS:")
        for director in [self.code_director, self.data_director,
                        self.communication_director, self.operations_director]:
            print(f"\n    ├── {director.config.name} ({director.config.role})")
            print(f"        Tasks: {director.task_count} | Cost: ${director.total_cost:.6f}")
            print(f"        Specializations: {', '.join(director.config.specializations[:3])}")

        print(f"\n  SUPPORT DEPARTMENTS:")

        hr_stats = self.hr_department.get_stats()
        print(f"\n    ├── HR Department")
        print(f"        HR Agents: {len(self.hr_department.hr_agents)}")
        print(f"        Employees created: {hr_stats['employees_created']}")
        print(f"        Active employees: {hr_stats['active_employees']}")
        print(f"        Total employee tasks: {hr_stats['total_employee_tasks']}")
        print(f"        Cost: ${hr_stats['total_cost']:.6f} (creation)")
        print(f"        Employee work cost: ${hr_stats['total_employee_cost']:.6f}")
        print(f"        NOTE: Only HR Agents can create employees")

        tools_stats = self.tools_department.get_stats()
        print(f"\n    ├── Tools Department")
        print(f"        Tools created: {tools_stats['tools_created']}")
        print(f"        Available tools: {tools_stats['available_tools']}")
        print(f"        Total usage: {tools_stats['total_usage']}")
        print(f"        Cost: ${tools_stats['total_cost']:.6f}")

        expert_stats = self.expert_pool.get_stats()
        print(f"\n    └── Expert Pool")
        print(f"        Expert consultations: {expert_stats['total_consultations']}")
        print(f"        Experts created: {expert_stats['experts_created']}")
        print(f"        Available expert types: {len(expert_stats['available_expert_types'])}")
        print(f"        Cost: ${expert_stats['total_expert_cost']:.6f}")
        if expert_stats['consultations_by_type']:
            print(f"        Consultations by type:")
            for expert_type, count in expert_stats['consultations_by_type'].items():
                print(f"          - {expert_type}: {count}")

        print(f"\n{'='*60}")
        print(f"TOTAL: {self._calculate_total_tasks()} tasks | ${self._calculate_total_cost():.6f}")
        print("="*60 + "\n")


# Instance globale (singleton pattern)
_hierarchy_instance: Optional[AgentHierarchy] = None


def get_hierarchy() -> AgentHierarchy:
    """Récupère l'instance globale de la hiérarchie"""
    global _hierarchy_instance
    if _hierarchy_instance is None:
        _hierarchy_instance = AgentHierarchy()
    return _hierarchy_instance


def reset_hierarchy():
    """Reset la hiérarchie (pour tests)"""
    global _hierarchy_instance
    _hierarchy_instance = None
