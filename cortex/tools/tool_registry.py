"""
Tool Registry - Liste minimaliste des outils disponibles

Pensé pour les tools: chaque fonctionnalité doit être un outil réutilisable.
Le registry permet aux agents de découvrir les outils disponibles sans coût.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class ToolInfo:
    """Information minimaliste sur un tool"""
    name: str
    description: str  # Description ultra-courte (1 ligne)
    category: str  # read, write, compute, api, system
    cost_estimate: str  # "free", "cheap", "medium", "expensive"


class ToolRegistry:
    """
    Registry ultra-léger des outils disponibles

    Permet aux agents de:
    1. Découvrir quels outils existent (sans coût)
    2. Comprendre rapidement ce que fait un outil
    3. Savoir si un outil est coûteux ou pas
    """

    def __init__(self, registry_file: Optional[Path] = None):
        if registry_file is None:
            registry_file = Path(__file__).parent / "available_tools.json"

        self.registry_file = registry_file
        self.tools: Dict[str, ToolInfo] = {}

        # Charger le registry si existe
        if self.registry_file.exists():
            self._load()
        else:
            # Créer avec les outils built-in
            self._initialize_builtin_tools()
            self._save()

    def _initialize_builtin_tools(self):
        """Initialise les outils built-in du système"""

        # Outils de fichiers (built-in)
        self.register(ToolInfo(
            name="read_file",
            description="Read file content",
            category="read",
            cost_estimate="free"
        ))

        self.register(ToolInfo(
            name="write_file",
            description="Write content to file",
            category="write",
            cost_estimate="free"
        ))

        self.register(ToolInfo(
            name="list_files",
            description="List files in directory",
            category="read",
            cost_estimate="free"
        ))

        self.register(ToolInfo(
            name="search_files",
            description="Search for text in files",
            category="read",
            cost_estimate="cheap"
        ))

        # Outils de données
        self.register(ToolInfo(
            name="get_pricing",
            description="Get model pricing data",
            category="read",
            cost_estimate="free"
        ))

        self.register(ToolInfo(
            name="calculate_cost",
            description="Calculate API call cost",
            category="compute",
            cost_estimate="free"
        ))

        # Outils système
        self.register(ToolInfo(
            name="execute_shell",
            description="Execute shell command",
            category="system",
            cost_estimate="free"
        ))

        self.register(ToolInfo(
            name="get_system_stats",
            description="Get system performance stats",
            category="system",
            cost_estimate="free"
        ))

        # Outils d'analyse
        self.register(ToolInfo(
            name="analyze_logs",
            description="Analyze system logs",
            category="compute",
            cost_estimate="cheap"
        ))

        self.register(ToolInfo(
            name="validate_data",
            description="Validate data structure",
            category="compute",
            cost_estimate="free"
        ))

    def register(self, tool: ToolInfo):
        """Enregistre un nouvel outil"""
        self.tools[tool.name] = tool

    def unregister(self, tool_name: str):
        """Retire un outil du registry"""
        if tool_name in self.tools:
            del self.tools[tool_name]

    def get(self, tool_name: str) -> Optional[ToolInfo]:
        """Récupère les infos d'un outil"""
        return self.tools.get(tool_name)

    def list_all(self) -> List[ToolInfo]:
        """Liste tous les outils"""
        return list(self.tools.values())

    def list_by_category(self, category: str) -> List[ToolInfo]:
        """Liste les outils d'une catégorie"""
        return [tool for tool in self.tools.values() if tool.category == category]

    def search(self, keyword: str) -> List[ToolInfo]:
        """Recherche des outils par mot-clé"""
        keyword_lower = keyword.lower()
        return [
            tool for tool in self.tools.values()
            if keyword_lower in tool.name.lower() or keyword_lower in tool.description.lower()
        ]

    def get_summary(self) -> str:
        """
        Génère un résumé ultra-compact pour les agents

        Format minimaliste pour économiser les tokens:
        - read_file: Read file content [read/free]
        - write_file: Write content to file [write/free]
        """
        lines = []
        for tool in sorted(self.tools.values(), key=lambda t: t.category):
            lines.append(f"- {tool.name}: {tool.description} [{tool.category}/{tool.cost_estimate}]")

        return "\n".join(lines)

    def get_summary_by_category(self) -> str:
        """Résumé organisé par catégorie"""
        categories = {}
        for tool in self.tools.values():
            if tool.category not in categories:
                categories[tool.category] = []
            categories[tool.category].append(tool)

        lines = []
        for category in sorted(categories.keys()):
            lines.append(f"\n{category.upper()}:")
            for tool in sorted(categories[category], key=lambda t: t.name):
                lines.append(f"  {tool.name}: {tool.description} ({tool.cost_estimate})")

        return "\n".join(lines)

    def _load(self):
        """Charge le registry depuis le fichier"""
        with open(self.registry_file, 'r') as f:
            data = json.load(f)

        for tool_data in data["tools"]:
            self.register(ToolInfo(**tool_data))

    def _save(self):
        """Sauvegarde le registry dans le fichier"""
        data = {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "category": tool.category,
                    "cost_estimate": tool.cost_estimate
                }
                for tool in self.tools.values()
            ]
        }

        # Créer le dossier si nécessaire
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.registry_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_tool_from_dict(self, tool_dict: Dict[str, str]):
        """Ajoute un outil depuis un dictionnaire"""
        tool = ToolInfo(
            name=tool_dict["name"],
            description=tool_dict["description"],
            category=tool_dict.get("category", "compute"),
            cost_estimate=tool_dict.get("cost_estimate", "cheap")
        )
        self.register(tool)
        self._save()


# Instance globale
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Récupère l'instance globale du registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(name: str, description: str, category: str = "compute", cost_estimate: str = "cheap"):
    """Shortcut pour enregistrer un outil"""
    registry = get_tool_registry()
    registry.register(ToolInfo(
        name=name,
        description=description,
        category=category,
        cost_estimate=cost_estimate
    ))
    registry._save()


if __name__ == "__main__":
    # Test
    registry = ToolRegistry()

    print("=== ALL TOOLS ===")
    print(registry.get_summary())

    print("\n=== BY CATEGORY ===")
    print(registry.get_summary_by_category())

    print("\n=== SEARCH 'file' ===")
    results = registry.search("file")
    for tool in results:
        print(f"  - {tool.name}: {tool.description}")

    print("\n=== READ TOOLS ===")
    read_tools = registry.list_by_category("read")
    for tool in read_tools:
        print(f"  - {tool.name}: {tool.description}")

    print(f"\n=== STATS ===")
    print(f"Total tools: {len(registry.list_all())}")
    print(f"Categories: {len(set(t.category for t in registry.list_all()))}")
