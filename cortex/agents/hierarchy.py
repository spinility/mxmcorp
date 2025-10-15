"""
Agent Hierarchy - Système complet de gestion des agents
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


class AgentHierarchy:
    """
    Hiérarchie complète des agents Cortex

    Structure:
    CEO
    ├── Code Director
    │   ├── Backend Manager (TODO)
    │   ├── Frontend Manager (TODO)
    │   └── DevOps Manager (TODO)
    ├── Data Director
    │   ├── Analytics Manager (TODO)
    │   ├── ML Manager (TODO)
    │   └── Data Engineering Manager (TODO)
    ├── Communication Director
    │   ├── Training Manager (TODO)
    │   ├── Documentation Manager (TODO)
    │   └── Support Manager (TODO)
    └── Operations Director
        ├── Infrastructure Manager (TODO)
        ├── Deployment Manager (TODO)
        └── Monitoring Manager (TODO)
    """

    def __init__(self):
        # Niveau 1: CEO
        self.ceo: CEOAgent = create_ceo()

        # Niveau 2: Directors
        directors = create_all_directors()
        self.code_director: CodeDirector = directors["code"]
        self.data_director: DataDirector = directors["data"]
        self.communication_director: CommunicationDirector = directors["communication"]
        self.operations_director: OperationsDirector = directors["operations"]

        # Enregistrer les Directors sous le CEO
        self.ceo.register_subordinate(self.code_director)
        self.ceo.register_subordinate(self.data_director)
        self.ceo.register_subordinate(self.communication_director)
        self.ceo.register_subordinate(self.operations_director)

        # TODO: Niveau 3 (Managers) et 4 (Workers) à implémenter

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
        """Récupère les stats de tous les agents"""
        return {
            "ceo": self.ceo.get_stats(),
            "directors": {
                "code": self.code_director.get_stats(),
                "data": self.data_director.get_stats(),
                "communication": self.communication_director.get_stats(),
                "operations": self.operations_director.get_stats()
            },
            "total_cost": self._calculate_total_cost(),
            "total_tasks": self._calculate_total_tasks()
        }

    def _calculate_total_cost(self) -> float:
        """Calcule le coût total de tous les agents"""
        return (
            self.ceo.total_cost +
            self.code_director.total_cost +
            self.data_director.total_cost +
            self.communication_director.total_cost +
            self.operations_director.total_cost
        )

    def _calculate_total_tasks(self) -> int:
        """Calcule le nombre total de tâches"""
        return (
            self.ceo.task_count +
            self.code_director.task_count +
            self.data_director.task_count +
            self.communication_director.task_count +
            self.operations_director.task_count
        )

    def print_hierarchy(self):
        """Affiche la hiérarchie des agents"""
        print("\n" + "="*60)
        print("CORTEX MXMCORP - AGENT HIERARCHY")
        print("="*60)

        print(f"\n{self.ceo.config.name} ({self.ceo.config.role})")
        print(f"  Tasks: {self.ceo.task_count} | Cost: ${self.ceo.total_cost:.6f}")

        for director in [self.code_director, self.data_director,
                        self.communication_director, self.operations_director]:
            print(f"\n  ├── {director.config.name} ({director.config.role})")
            print(f"      Tasks: {director.task_count} | Cost: ${director.total_cost:.6f}")
            print(f"      Specializations: {', '.join(director.config.specializations[:3])}")

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
