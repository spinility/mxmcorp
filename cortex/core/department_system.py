"""
Department System - Système de départements avec partage de connaissance

Architecture:
- Department: Contient agents et knowledge base partagée
- DepartmentKnowledgeBase: Base de connaissance départementale
- DepartmentMetrics: Métriques de performance

Usage:
    dept = Department("development", "Code development department")
    dept.register_agent(code_writer_agent)
    dept.share_knowledge("best_practices", ["Use type hints", "Write tests"])
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
from enum import Enum

from cortex.core.agent_hierarchy import BaseAgent, AgentRole


class DepartmentKnowledgeBase:
    """
    Base de connaissance partagée d'un département

    Permet aux agents d'un même département de partager:
    - Patterns de succès
    - Échecs et leçons
    - Outils et standards
    - Métriques et insights
    """

    def __init__(self, department_name: str, storage_path: str = "cortex/data/departments"):
        self.department_name = department_name
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.kb_file = self.storage_path / f"{department_name}_kb.json"
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        """Charge la knowledge base depuis le disque"""
        if self.kb_file.exists():
            with open(self.kb_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save(self):
        """Sauvegarde la knowledge base sur le disque"""
        with open(self.kb_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def store(self, key: str, value: Any, metadata: Optional[Dict] = None):
        """
        Stocke une connaissance avec métadonnées

        Args:
            key: Clé unique
            value: Valeur (peut être dict, list, str, etc.)
            metadata: Métadonnées optionnelles (auteur, date, etc.)
        """
        entry = {
            "value": value,
            "updated_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        # Garder historique si la clé existe déjà
        if key in self.data:
            if "history" not in self.data[key]:
                self.data[key]["history"] = []
            self.data[key]["history"].append({
                "value": self.data[key]["value"],
                "updated_at": self.data[key]["updated_at"]
            })

        self.data[key] = entry
        self._save()

    def retrieve(self, key: str, default: Any = None) -> Any:
        """
        Récupère une connaissance

        Args:
            key: Clé à récupérer
            default: Valeur par défaut si clé n'existe pas

        Returns:
            La valeur stockée ou default
        """
        entry = self.data.get(key)
        if entry:
            return entry.get("value", default)
        return default

    def search(self, pattern: str) -> List[Dict[str, Any]]:
        """
        Recherche dans la base de connaissance

        Args:
            pattern: Pattern à chercher (simple string match pour l'instant)

        Returns:
            Liste de résultats {key, value, metadata}
        """
        results = []
        pattern_lower = pattern.lower()

        for key, entry in self.data.items():
            # Chercher dans la clé
            if pattern_lower in key.lower():
                results.append({
                    "key": key,
                    "value": entry["value"],
                    "metadata": entry.get("metadata", {})
                })
                continue

            # Chercher dans la valeur (si string)
            value = entry["value"]
            if isinstance(value, str) and pattern_lower in value.lower():
                results.append({
                    "key": key,
                    "value": value,
                    "metadata": entry.get("metadata", {})
                })

        return results

    def get_history(self, key: str) -> List[Dict]:
        """
        Récupère l'historique d'une connaissance

        Args:
            key: Clé dont on veut l'historique

        Returns:
            Liste des anciennes valeurs avec timestamps
        """
        entry = self.data.get(key, {})
        return entry.get("history", [])

    def get_all_keys(self) -> List[str]:
        """Retourne toutes les clés disponibles"""
        return list(self.data.keys())

    def delete(self, key: str):
        """Supprime une connaissance"""
        if key in self.data:
            del self.data[key]
            self._save()


@dataclass
class DepartmentMetrics:
    """Métriques de performance d'un département"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_response_time: float = 0.0
    total_cost: float = 0.0
    bottleneck_role: Optional[AgentRole] = None

    @property
    def success_rate(self) -> float:
        """Taux de succès"""
        if self.total_tasks == 0:
            return 0.0
        return self.completed_tasks / self.total_tasks

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.success_rate,
            "avg_response_time": self.avg_response_time,
            "total_cost": self.total_cost,
            "bottleneck_role": self.bottleneck_role.value if self.bottleneck_role else None
        }


class Department:
    """
    Département avec agents et knowledge base partagée

    Un département regroupe des agents de différents niveaux hiérarchiques
    travaillant dans la même spécialisation.

    Example:
        dept = Department("development", "Code development and analysis")
        dept.register_agent(code_writer_agent)
        dept.register_agent(code_analyst_agent)

        # Partager connaissance
        dept.share_knowledge("coding_standards", {...})

        # Consulter connaissance
        standards = dept.consult_knowledge("coding_standards")
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.knowledge_base = DepartmentKnowledgeBase(name)

        # Agents par rôle
        self.agents: Dict[AgentRole, List[BaseAgent]] = {
            AgentRole.AGENT: [],      # Sera renommé EXÉCUTANT dans phase suivante
            AgentRole.EXPERT: [],
            AgentRole.DIRECTEUR: [],
            AgentRole.CORTEX_CENTRAL: []
        }

        self.metrics = DepartmentMetrics()
        self.created_at = datetime.now()

    def register_agent(self, agent: BaseAgent):
        """
        Enregistre un agent dans le département

        Args:
            agent: Agent à enregistrer
        """
        self.agents[agent.role].append(agent)

        # Donner accès au département à l'agent
        if hasattr(agent, 'department'):
            agent.department = self

    def unregister_agent(self, agent: BaseAgent):
        """Retire un agent du département"""
        if agent in self.agents[agent.role]:
            self.agents[agent.role].remove(agent)

    def get_agents_by_role(self, role: AgentRole) -> List[BaseAgent]:
        """
        Récupère tous les agents d'un rôle spécifique

        Args:
            role: Rôle recherché

        Returns:
            Liste des agents de ce rôle
        """
        return self.agents[role]

    def get_all_agents(self) -> List[BaseAgent]:
        """Récupère tous les agents du département"""
        all_agents = []
        for agents_list in self.agents.values():
            all_agents.extend(agents_list)
        return all_agents

    def share_knowledge(self, key: str, value: Any, metadata: Optional[Dict] = None):
        """
        Partage une connaissance entre tous les agents du département

        Args:
            key: Clé de la connaissance
            value: Valeur à partager
            metadata: Métadonnées optionnelles
        """
        self.knowledge_base.store(key, value, metadata)

    def consult_knowledge(self, key: str, default: Any = None) -> Any:
        """
        Consulte une connaissance partagée

        Args:
            key: Clé à consulter
            default: Valeur par défaut

        Returns:
            La valeur ou default
        """
        return self.knowledge_base.retrieve(key, default)

    def search_knowledge(self, pattern: str) -> List[Dict[str, Any]]:
        """
        Recherche dans la base de connaissance

        Args:
            pattern: Pattern à chercher

        Returns:
            Résultats de recherche
        """
        return self.knowledge_base.search(pattern)

    def get_performance_metrics(self) -> DepartmentMetrics:
        """
        Récupère les métriques de performance du département

        Returns:
            Métriques actuelles
        """
        return self.metrics

    def update_metrics(self, task_result: Dict[str, Any]):
        """
        Met à jour les métriques après une tâche

        Args:
            task_result: Résultat de tâche avec success, duration, cost, etc.
        """
        self.metrics.total_tasks += 1

        if task_result.get("success"):
            self.metrics.completed_tasks += 1
        else:
            self.metrics.failed_tasks += 1

        # Mise à jour temps de réponse moyen
        if "duration" in task_result:
            n = self.metrics.total_tasks
            current_avg = self.metrics.avg_response_time
            new_duration = task_result["duration"]
            self.metrics.avg_response_time = ((current_avg * (n - 1)) + new_duration) / n

        # Mise à jour coût
        if "cost" in task_result:
            self.metrics.total_cost += task_result["cost"]

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le département en dictionnaire"""
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "agent_count": {
                role.value: len(agents)
                for role, agents in self.agents.items()
            },
            "metrics": self.metrics.to_dict()
        }


class DepartmentRegistry:
    """
    Registre central de tous les départements

    Permet de:
    - Créer/supprimer départements
    - Lister départements
    - Transférer agents entre départements
    """

    def __init__(self):
        self.departments: Dict[str, Department] = {}

    def create_department(self, name: str, description: str) -> Department:
        """
        Crée un nouveau département

        Args:
            name: Nom du département
            description: Description

        Returns:
            Le département créé
        """
        if name in self.departments:
            raise ValueError(f"Department '{name}' already exists")

        dept = Department(name, description)
        self.departments[name] = dept
        return dept

    def get_department(self, name: str) -> Optional[Department]:
        """
        Récupère un département par nom

        Args:
            name: Nom du département

        Returns:
            Le département ou None
        """
        return self.departments.get(name)

    def list_departments(self) -> List[str]:
        """Liste tous les noms de départements"""
        return list(self.departments.keys())

    def delete_department(self, name: str):
        """Supprime un département"""
        if name in self.departments:
            del self.departments[name]

    def get_all_agents(self) -> List[BaseAgent]:
        """Récupère tous les agents de tous les départements"""
        all_agents = []
        for dept in self.departments.values():
            all_agents.extend(dept.get_all_agents())
        return all_agents

    def transfer_agent(self, agent: BaseAgent, from_dept: str, to_dept: str):
        """
        Transfère un agent d'un département à un autre

        Args:
            agent: Agent à transférer
            from_dept: Département source
            to_dept: Département destination
        """
        source = self.get_department(from_dept)
        dest = self.get_department(to_dept)

        if not source or not dest:
            raise ValueError("Source or destination department not found")

        source.unregister_agent(agent)
        dest.register_agent(agent)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Résumé des métriques de tous les départements"""
        return {
            name: dept.get_performance_metrics().to_dict()
            for name, dept in self.departments.items()
        }


# Factory functions pour faciliter l'usage
def create_department(name: str, description: str) -> Department:
    """Factory function pour créer un département"""
    return Department(name, description)


# Test si exécuté directement
if __name__ == "__main__":
    print("Testing Department System...")

    # Test 1: Créer département
    print("\n1. Creating department...")
    dev_dept = create_department("development", "Code development department")
    print(f"✓ Created: {dev_dept.name}")

    # Test 2: Partager connaissance
    print("\n2. Sharing knowledge...")
    dev_dept.share_knowledge("coding_standards", {
        "use_type_hints": True,
        "write_tests": True,
        "max_line_length": 100
    })
    standards = dev_dept.consult_knowledge("coding_standards")
    print(f"✓ Stored and retrieved: {standards}")

    # Test 3: Historique
    print("\n3. Testing history...")
    dev_dept.share_knowledge("coding_standards", {
        "use_type_hints": True,
        "write_tests": True,
        "max_line_length": 120  # Updated
    })
    history = dev_dept.knowledge_base.get_history("coding_standards")
    print(f"✓ History entries: {len(history)}")

    # Test 4: Recherche
    print("\n4. Testing search...")
    dev_dept.share_knowledge("best_practices", "Always validate input")
    dev_dept.share_knowledge("patterns", "Use factory pattern")
    results = dev_dept.search_knowledge("pattern")
    print(f"✓ Search results: {len(results)} matches")

    # Test 5: Métriques
    print("\n5. Testing metrics...")
    dev_dept.update_metrics({"success": True, "duration": 5.5, "cost": 0.02})
    dev_dept.update_metrics({"success": True, "duration": 3.2, "cost": 0.01})
    metrics = dev_dept.get_performance_metrics()
    print(f"✓ Metrics: {metrics.total_tasks} tasks, {metrics.success_rate:.1%} success rate")

    # Test 6: Registry
    print("\n6. Testing registry...")
    registry = DepartmentRegistry()
    registry.departments["development"] = dev_dept
    opt_dept = registry.create_department("optimization", "Optimization department")
    print(f"✓ Registry: {len(registry.list_departments())} departments")

    print("\n✓ Department System works correctly!")
