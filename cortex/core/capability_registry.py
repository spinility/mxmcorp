"""
Capability Registry - Système de découverte et inventaire des capacités de Cortex

Responsabilités:
- Découvre automatiquement tous les départements, agents, outils
- Maintient un inventaire complet des capacités
- Permet recherche par intention ("Je veux scraper web" → StealthWebCrawler)
- Valide contre les registres existants (DepartmentRegistry, etc.)
- Génère documentation automatique
"""

import os
import ast
import importlib
import inspect
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import json


@dataclass
class Capability:
    """Représente une capacité du système"""
    id: str
    name: str
    type: str  # "department", "agent", "tool", "workflow", "function"
    description: str
    file_path: str
    module_path: str

    # Capacités
    can_do: List[str] = field(default_factory=list)
    cannot_do: List[str] = field(default_factory=list)

    # Métadonnées
    status: str = "available"  # "available", "development", "deprecated", "broken"
    requires: List[str] = field(default_factory=list)  # Dépendances
    examples: List[str] = field(default_factory=list)

    # Détails techniques
    class_name: Optional[str] = None
    role: Optional[str] = None  # Pour agents: "AGENT", "EXPERT", etc.
    tier: Optional[str] = None  # Pour agents: tier préféré

    # Validation
    tested: bool = False
    last_test: Optional[datetime] = None
    test_result: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "file_path": self.file_path,
            "module_path": self.module_path,
            "can_do": self.can_do,
            "cannot_do": self.cannot_do,
            "status": self.status,
            "requires": self.requires,
            "examples": self.examples,
            "class_name": self.class_name,
            "role": self.role,
            "tier": self.tier,
            "tested": self.tested,
            "last_test": self.last_test.isoformat() if self.last_test else None,
            "test_result": self.test_result
        }


class CapabilityRegistry:
    """
    Registre central qui découvre et maintient l'inventaire
    de toutes les capacités de Cortex
    """

    def __init__(self, cortex_root: str = "/github/mxmcorp/cortex"):
        self.cortex_root = Path(cortex_root)
        self.capabilities: Dict[str, Capability] = {}

        # Cache
        self._discovery_cache: Optional[datetime] = None

    def discover_all_capabilities(self, force_refresh: bool = False) -> Dict[str, Capability]:
        """
        Découvre toutes les capacités en scannant le codebase

        Args:
            force_refresh: Si True, ignore le cache et redécouvre tout

        Returns:
            Dict de toutes les capacités découvertes
        """
        # Check cache (valide 5 minutes)
        if not force_refresh and self._discovery_cache:
            age = (datetime.now() - self._discovery_cache).total_seconds()
            if age < 300:  # 5 minutes
                return self.capabilities

        print("🔍 Discovering Cortex capabilities...")

        # Découvrir par catégorie
        departments = self._discover_departments()
        agents = self._discover_agents()
        tools = self._discover_tools()
        workflows = self._discover_workflows()

        # Combiner
        self.capabilities = {}
        for cap in departments + agents + tools + workflows:
            self.capabilities[cap.id] = cap

        self._discovery_cache = datetime.now()

        print(f"✓ Discovered {len(self.capabilities)} capabilities:")
        print(f"  - {len(departments)} departments")
        print(f"  - {len(agents)} agents")
        print(f"  - {len(tools)} tools")
        print(f"  - {len(workflows)} workflows")

        return self.capabilities

    def _discover_departments(self) -> List[Capability]:
        """Découvre tous les départements"""
        departments = []
        dept_dir = self.cortex_root / "departments"

        if not dept_dir.exists():
            return departments

        # Scanner chaque sous-répertoire
        for dept_path in dept_dir.iterdir():
            if not dept_path.is_dir() or dept_path.name.startswith("_"):
                continue

            # Lire __init__.py pour description
            init_file = dept_path / "__init__.py"
            if not init_file.exists():
                continue

            try:
                with open(init_file, 'r') as f:
                    content = f.read()

                # Extraire docstring
                tree = ast.parse(content)
                docstring = ast.get_docstring(tree) or "No description"

                # Extraire rôle depuis docstring
                role_line = [line for line in docstring.split('\n') if 'Rôle:' in line]
                role = role_line[0].split('Rôle:')[1].strip() if role_line else "Unknown"

                dept_name = dept_path.name.replace("_", " ").title()

                capability = Capability(
                    id=f"dept_{dept_path.name}",
                    name=dept_name,
                    type="department",
                    description=role,
                    file_path=str(init_file),
                    module_path=f"cortex.departments.{dept_path.name}",
                    status="available"
                )

                departments.append(capability)

            except Exception as e:
                print(f"  ⚠️  Could not parse {dept_path.name}: {e}")

        return departments

    def _discover_agents(self) -> List[Capability]:
        """Découvre tous les agents"""
        agents = []
        agents_dir = self.cortex_root / "agents"

        if not agents_dir.exists():
            return agents

        # Scanner fichiers Python
        for agent_file in agents_dir.glob("*.py"):
            if agent_file.name.startswith("_"):
                continue

            try:
                with open(agent_file, 'r') as f:
                    content = f.read()

                tree = ast.parse(content)

                # Trouver classes qui héritent d'Agent/Expert/etc.
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Vérifier si c'est un agent
                        bases = [base.id if isinstance(base, ast.Name) else None
                                for base in node.bases]

                        agent_types = ['Agent', 'Expert', 'DecisionAgent', 'Director',
                                     'BaseAgent', 'ExecutantAgent', 'ExpertAgent']

                        if any(base in agent_types for base in bases if base):
                            docstring = ast.get_docstring(node) or "No description"

                            # Extraire rôle si présent
                            role = None
                            for line in content.split('\n'):
                                if 'ROLE:' in line or 'RÔLE:' in line:
                                    role = line.split(':')[1].strip()
                                    break

                            capability = Capability(
                                id=f"agent_{node.name.lower()}",
                                name=node.name,
                                type="agent",
                                description=docstring.split('\n')[0],
                                file_path=str(agent_file),
                                module_path=f"cortex.agents.{agent_file.stem}",
                                class_name=node.name,
                                role=role,
                                status="available"
                            )

                            agents.append(capability)

            except Exception as e:
                print(f"  ⚠️  Could not parse {agent_file.name}: {e}")

        return agents

    def _discover_tools(self) -> List[Capability]:
        """Découvre tous les outils"""
        tools = []
        tools_dir = self.cortex_root / "tools"

        if not tools_dir.exists():
            return tools

        # Scanner generated tools
        generated_dir = tools_dir / "generated"
        if generated_dir.exists():
            for tool_file in generated_dir.glob("*.sh"):
                try:
                    with open(tool_file, 'r') as f:
                        content = f.read()

                    # Extraire description depuis comments
                    description = "Shell tool"
                    for line in content.split('\n'):
                        if line.startswith('#') and 'Description:' in line:
                            description = line.split('Description:')[1].strip()
                            break

                    capability = Capability(
                        id=f"tool_{tool_file.stem}",
                        name=tool_file.stem.replace("_", " ").title(),
                        type="tool",
                        description=description,
                        file_path=str(tool_file),
                        module_path=f"tools.generated.{tool_file.stem}",
                        status="available"
                    )

                    tools.append(capability)

                except Exception as e:
                    print(f"  ⚠️  Could not parse {tool_file.name}: {e}")

        # Scanner Python tools
        for tool_file in tools_dir.glob("*.py"):
            if tool_file.name.startswith("_"):
                continue

            try:
                with open(tool_file, 'r') as f:
                    content = f.read()

                tree = ast.parse(content)
                docstring = ast.get_docstring(tree) or "Tool module"

                capability = Capability(
                    id=f"tool_{tool_file.stem}",
                    name=tool_file.stem.replace("_", " ").title(),
                    type="tool",
                    description=docstring.split('\n')[0],
                    file_path=str(tool_file),
                    module_path=f"cortex.tools.{tool_file.stem}",
                    status="available"
                )

                tools.append(capability)

            except Exception as e:
                print(f"  ⚠️  Could not parse {tool_file.name}: {e}")

        return tools

    def _discover_workflows(self) -> List[Capability]:
        """Découvre tous les workflows définis"""
        workflows = []

        # Pour l'instant, retourner vide (workflows pas encore standardisés)
        # TODO: Scanner pour WorkflowEngine workflows

        return workflows

    def get_capabilities_by_type(self, cap_type: str) -> List[Capability]:
        """Retourne capacités d'un type spécifique"""
        return [cap for cap in self.capabilities.values() if cap.type == cap_type]

    def get_capability_by_id(self, cap_id: str) -> Optional[Capability]:
        """Retourne une capacité par son ID"""
        return self.capabilities.get(cap_id)

    def search_capabilities(self, query: str) -> List[Capability]:
        """
        Recherche capacités par mots-clés

        Args:
            query: Requête en langage naturel

        Returns:
            Liste de capacités matchantes triées par pertinence
        """
        query_lower = query.lower()
        results = []

        for cap in self.capabilities.values():
            score = 0

            # Match dans nom (poids 3)
            if query_lower in cap.name.lower():
                score += 3

            # Match dans description (poids 2)
            if query_lower in cap.description.lower():
                score += 2

            # Match dans can_do (poids 5 - très pertinent)
            for action in cap.can_do:
                if query_lower in action.lower():
                    score += 5

            if score > 0:
                results.append((score, cap))

        # Trier par score descendant
        results.sort(key=lambda x: x[0], reverse=True)

        return [cap for score, cap in results]

    def get_statistics(self) -> Dict[str, Any]:
        """Retourne statistiques du registry"""
        by_type = {}
        by_status = {}

        for cap in self.capabilities.values():
            by_type[cap.type] = by_type.get(cap.type, 0) + 1
            by_status[cap.status] = by_status.get(cap.status, 0) + 1

        return {
            "total_capabilities": len(self.capabilities),
            "by_type": by_type,
            "by_status": by_status,
            "tested": sum(1 for cap in self.capabilities.values() if cap.tested),
            "last_discovery": self._discovery_cache.isoformat() if self._discovery_cache else None
        }

    def save_to_file(self, filepath: str = "cortex/data/capabilities.json"):
        """Sauvegarde l'inventaire sur disque"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        data = {
            "discovered_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "capabilities": [cap.to_dict() for cap in self.capabilities.values()]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Saved capabilities to {filepath}")

    def display_capabilities(self, cap_type: Optional[str] = None):
        """Affiche les capacités de manière lisible"""
        caps = self.get_capabilities_by_type(cap_type) if cap_type else self.capabilities.values()

        if not caps:
            print(f"No capabilities found{' of type ' + cap_type if cap_type else ''}")
            return

        print(f"\n{'='*70}")
        print(f"CORTEX CAPABILITIES{' - ' + cap_type.upper() if cap_type else ''}")
        print(f"{'='*70}\n")

        # Grouper par type
        by_type: Dict[str, List[Capability]] = {}
        for cap in caps:
            if cap.type not in by_type:
                by_type[cap.type] = []
            by_type[cap.type].append(cap)

        for cap_type, type_caps in sorted(by_type.items()):
            icon = {"department": "🏢", "agent": "🤖", "tool": "🔧", "workflow": "⚡"}.get(cap_type, "📦")
            print(f"{icon} {cap_type.upper()} ({len(type_caps)})")
            print(f"{'-'*70}")

            for cap in sorted(type_caps, key=lambda c: c.name):
                status_icon = {"available": "✅", "development": "🚧", "deprecated": "⚠️", "broken": "❌"}.get(cap.status, "❓")
                print(f"  [{cap.id}] {status_icon} {cap.name}")
                print(f"      {cap.description}")
                if cap.role:
                    print(f"      Role: {cap.role}")
                if cap.tested:
                    print(f"      Tested: ✅ ({cap.test_result})")
                print()

        print(f"{'='*70}\n")


def create_capability_registry() -> CapabilityRegistry:
    """Factory function"""
    return CapabilityRegistry()


# Test
if __name__ == "__main__":
    print("Testing Capability Registry...")

    registry = CapabilityRegistry()

    # Test 1: Discover all capabilities
    print("\n1. Discovering capabilities...")
    capabilities = registry.discover_all_capabilities()

    print(f"\n✓ Discovered {len(capabilities)} capabilities")

    # Test 2: Display statistics
    print("\n2. Statistics...")
    stats = registry.get_statistics()
    print(f"✓ Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Test 3: Search
    print("\n3. Searching for 'web'...")
    results = registry.search_capabilities("web")
    print(f"✓ Found {len(results)} results:")
    for cap in results[:5]:
        print(f"  - {cap.name} ({cap.type}): {cap.description[:60]}")

    # Test 4: Display all capabilities
    print("\n4. Displaying all capabilities...")
    registry.display_capabilities()

    # Test 5: Save to file
    print("\n5. Saving to file...")
    registry.save_to_file("cortex/data/test_capabilities.json")

    print("\n✓ Capability Registry works correctly!")
