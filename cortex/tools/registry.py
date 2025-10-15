"""
Tool Registry - Catalogue de tous les outils disponibles
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .base_tool import BaseTool


class ToolRegistry:
    """
    Registre centralisé de tous les outils

    Fonctionnalités:
    - Enregistrer/désenregistrer des outils
    - Rechercher des outils par nom, catégorie, tags
    - Sauvegarder/charger le registre
    - Statistiques d'utilisation globales
    """

    def __init__(self, registry_file: str = "data/tools_registry.json"):
        self.registry_file = Path(registry_file)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

        # Catalogue des outils
        self.tools: Dict[str, BaseTool] = {}

        # Charger le registre existant
        self.load()

    def register(self, tool: BaseTool) -> bool:
        """
        Enregistre un nouvel outil

        Args:
            tool: Instance de l'outil

        Returns:
            True si enregistrement réussi
        """
        tool_name = tool.metadata.name

        if tool_name in self.tools:
            print(f"Warning: Tool '{tool_name}' already registered, overwriting")

        self.tools[tool_name] = tool
        self.save()

        return True

    def unregister(self, tool_name: str) -> bool:
        """Désenregistre un outil"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            self.save()
            return True
        return False

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """Récupère un outil par son nom"""
        return self.tools.get(tool_name)

    def list_all(self) -> List[BaseTool]:
        """Liste tous les outils"""
        return list(self.tools.values())

    def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[BaseTool]:
        """
        Recherche des outils

        Args:
            query: Recherche textuelle dans nom/description
            category: Filtrer par catégorie
            tags: Filtrer par tags

        Returns:
            Liste des outils correspondants
        """
        results = []

        for tool in self.tools.values():
            # Filtre par catégorie
            if category and tool.metadata.category != category:
                continue

            # Filtre par tags
            if tags:
                if not any(tag in tool.metadata.tags for tag in tags):
                    continue

            # Recherche textuelle
            if query:
                query_lower = query.lower()
                if (query_lower not in tool.metadata.name.lower() and
                    query_lower not in tool.metadata.description.lower()):
                    continue

            results.append(tool)

        return results

    def get_by_category(self, category: str) -> List[BaseTool]:
        """Récupère tous les outils d'une catégorie"""
        return [
            tool for tool in self.tools.values()
            if tool.metadata.category == category
        ]

    def get_categories(self) -> List[str]:
        """Liste toutes les catégories disponibles"""
        categories = set()
        for tool in self.tools.values():
            categories.add(tool.metadata.category)
        return sorted(list(categories))

    def get_stats(self) -> Dict:
        """Statistiques globales du registre"""
        total_tools = len(self.tools)
        total_usage = sum(tool.usage_count for tool in self.tools.values())
        total_errors = sum(tool.error_count for tool in self.tools.values())

        categories_count = {}
        for tool in self.tools.values():
            cat = tool.metadata.category
            categories_count[cat] = categories_count.get(cat, 0) + 1

        # Top tools par usage
        top_tools = sorted(
            self.tools.values(),
            key=lambda t: t.usage_count,
            reverse=True
        )[:10]

        return {
            "total_tools": total_tools,
            "total_usage": total_usage,
            "total_errors": total_errors,
            "error_rate": total_errors / total_usage if total_usage > 0 else 0,
            "categories": categories_count,
            "top_tools": [
                {
                    "name": t.metadata.name,
                    "usage_count": t.usage_count,
                    "error_rate": t.error_count / t.usage_count if t.usage_count > 0 else 0
                }
                for t in top_tools
            ]
        }

    def save(self):
        """Sauvegarde le registre sur disque"""
        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "tools": {
                name: tool.to_dict()
                for name, tool in self.tools.items()
            }
        }

        self.registry_file.write_text(json.dumps(data, indent=2))

    def load(self):
        """Charge le registre depuis le disque"""
        if not self.registry_file.exists():
            return

        try:
            data = json.loads(self.registry_file.read_text())

            # Note: On ne charge que les métadonnées, pas les outils eux-mêmes
            # Les outils doivent être re-enregistrés au démarrage
            # Ceci permet de garder une trace même si le code change

        except Exception as e:
            print(f"Warning: Failed to load registry: {e}")

    def export_catalog(self, format: str = "markdown") -> str:
        """
        Exporte un catalogue des outils

        Args:
            format: "markdown" ou "json"

        Returns:
            Catalogue formaté
        """
        if format == "json":
            return json.dumps([tool.to_dict() for tool in self.tools.values()], indent=2)

        elif format == "markdown":
            lines = ["# Cortex Tools Catalog\n"]

            # Grouper par catégorie
            categories = {}
            for tool in self.tools.values():
                cat = tool.metadata.category
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(tool)

            # Générer le markdown
            for category in sorted(categories.keys()):
                lines.append(f"\n## {category.capitalize()}\n")

                for tool in sorted(categories[category], key=lambda t: t.metadata.name):
                    lines.append(f"### {tool.metadata.name}\n")
                    lines.append(f"**Description:** {tool.metadata.description}\n")
                    lines.append(f"**Version:** {tool.metadata.version}\n")
                    lines.append(f"**Author:** {tool.metadata.author}\n")
                    lines.append(f"**Usage:** {tool.usage_count} times\n")

                    if tool.metadata.tags:
                        lines.append(f"**Tags:** {', '.join(tool.metadata.tags)}\n")

                    lines.append("\n---\n")

            return "\n".join(lines)

        else:
            raise ValueError(f"Unsupported format: {format}")


# Exemple d'utilisation
if __name__ == "__main__":
    from .base_tool import ToolMetadata, ToolResult
    from datetime import datetime

    # Créer un outil de test
    class TestTool(BaseTool):
        def __init__(self):
            metadata = ToolMetadata(
                name="TestTool",
                description="A test tool",
                version="1.0.0",
                author="human",
                created_at=datetime.now(),
                category="testing",
                tags=["test"],
                cost_estimate="free"
            )
            super().__init__(metadata)

        def validate_params(self, **kwargs):
            return True, None

        def execute(self, **kwargs):
            return ToolResult(success=True, data={"message": "Test successful"})

    # Tester le registre
    registry = ToolRegistry()

    tool = TestTool()
    registry.register(tool)

    print(f"Registered tools: {len(registry.list_all())}")
    print(f"Categories: {registry.get_categories()}")

    # Statistiques
    stats = registry.get_stats()
    print(f"\nRegistry stats:")
    print(f"  Total tools: {stats['total_tools']}")
    print(f"  Categories: {stats['categories']}")

    # Export catalogue
    catalog = registry.export_catalog("markdown")
    print(f"\nCatalog preview:")
    print(catalog[:500] + "...")
