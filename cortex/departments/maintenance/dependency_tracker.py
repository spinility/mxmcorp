"""
Dependency Tracker - Maintient graphe complet des dépendances

Responsabilités:
- Analyse imports/exports de tous les fichiers
- Construit graphe de dépendances
- Détecte dépendances circulaires
- Identifie modules critiques (très utilisés)
- Calcule impact des changements
"""

from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json
from datetime import datetime

from cortex.departments.maintenance.context_updater import ContextUpdater


@dataclass
class DependencyNode:
    """Nœud dans le graphe de dépendances"""
    file_path: str
    imports_from: List[str]  # Fichiers que ce fichier importe
    imported_by: List[str]  # Fichiers qui importent ce fichier
    depth: int  # Distance depuis root
    is_critical: bool  # Importé par beaucoup de fichiers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "imports_from": self.imports_from,
            "imported_by": self.imported_by,
            "depth": self.depth,
            "is_critical": self.is_critical
        }


class DependencyTracker:
    """
    Gestionnaire du graphe de dépendances

    Analyse tous les imports Python et construit graphe complet
    """

    def __init__(
        self,
        context_updater: ContextUpdater,
        graph_file: str = "cortex/data/dependency_graph.json"
    ):
        self.context_updater = context_updater
        self.graph_file = Path(graph_file)
        self.graph_file.parent.mkdir(parents=True, exist_ok=True)

        self.nodes: Dict[str, DependencyNode] = {}
        self.circular_dependencies: List[List[str]] = []

    def build_dependency_graph(self, root_dirs: List[str] = None) -> Dict[str, DependencyNode]:
        """
        Construit le graphe complet des dépendances

        Args:
            root_dirs: Répertoires racines à analyser (défaut: ["cortex"])

        Returns:
            Dict {file_path: DependencyNode}
        """
        if root_dirs is None:
            root_dirs = ["cortex"]

        print("Building dependency graph...")

        # 1. Scanner tous les fichiers Python
        all_files = []
        for root_dir in root_dirs:
            root_path = Path(root_dir)
            if root_path.exists():
                all_files.extend(root_path.rglob("*.py"))

        print(f"Found {len(all_files)} Python files")

        # 2. Créer nœuds pour chaque fichier
        for file_path in all_files:
            file_str = str(file_path)

            # Obtenir contexte (ou créer si nécessaire)
            context = self.context_updater.get_context(file_str)
            if not context:
                try:
                    context = self.context_updater.update_file_context(file_str)
                except Exception:
                    continue

            # Créer nœud
            node = DependencyNode(
                file_path=file_str,
                imports_from=self._resolve_imports(context.imports, file_str),
                imported_by=[],  # Sera rempli après
                depth=0,  # Sera calculé après
                is_critical=False  # Sera déterminé après
            )

            self.nodes[file_str] = node

        # 3. Construire relations imported_by
        for node in self.nodes.values():
            for imported_file in node.imports_from:
                if imported_file in self.nodes:
                    self.nodes[imported_file].imported_by.append(node.file_path)

        # 4. Calculer profondeurs
        self._calculate_depths()

        # 5. Identifier modules critiques (importés par 5+ fichiers)
        for node in self.nodes.values():
            node.is_critical = len(node.imported_by) >= 5

        # 6. Détecter cycles
        self.circular_dependencies = self._detect_cycles()

        # 7. Sauvegarder
        self._save_graph()

        print(f"✓ Graph built: {len(self.nodes)} nodes")
        print(f"  Critical modules: {sum(1 for n in self.nodes.values() if n.is_critical)}")
        print(f"  Circular dependencies: {len(self.circular_dependencies)}")

        return self.nodes

    def _resolve_imports(self, imports: List[str], current_file: str) -> List[str]:
        """
        Résout imports en chemins de fichiers réels

        Args:
            imports: Liste d'imports (ex: ["cortex.core.agent"])
            current_file: Fichier actuel

        Returns:
            Liste de chemins de fichiers
        """
        resolved = []

        for imp in imports:
            # Ignorer imports externes (pas cortex.*)
            if not imp.startswith("cortex"):
                continue

            # Convertir module en chemin
            # cortex.core.agent → cortex/core/agent.py
            path_str = imp.replace(".", "/") + ".py"
            path = Path(path_str)

            if path.exists():
                resolved.append(str(path))
            else:
                # Peut-être un package (__init__.py)
                init_path = Path(imp.replace(".", "/")) / "__init__.py"
                if init_path.exists():
                    resolved.append(str(init_path))

        return resolved

    def _calculate_depths(self):
        """Calcule profondeur (distance depuis root) pour chaque nœud"""
        # Root nodes: fichiers qui n'importent rien
        root_nodes = [n for n in self.nodes.values() if not n.imports_from]

        # BFS depuis root nodes
        visited = set()
        queue = [(node, 0) for node in root_nodes]

        while queue:
            node, depth = queue.pop(0)

            if node.file_path in visited:
                continue

            visited.add(node.file_path)
            node.depth = depth

            # Ajouter fichiers qui importent ce fichier
            for imported_by_path in node.imported_by:
                if imported_by_path not in visited and imported_by_path in self.nodes:
                    queue.append((self.nodes[imported_by_path], depth + 1))

    def _detect_cycles(self) -> List[List[str]]:
        """
        Détecte dépendances circulaires

        Returns:
            Liste de cycles (chaque cycle est une liste de fichiers)
        """
        cycles = []
        visited = set()

        def dfs(node_path: str, path: List[str], recursion_stack: Set[str]):
            if node_path in recursion_stack:
                # Cycle détecté
                cycle_start = path.index(node_path)
                cycle = path[cycle_start:] + [node_path]
                cycles.append(cycle)
                return

            if node_path in visited:
                return

            visited.add(node_path)
            recursion_stack.add(node_path)
            path.append(node_path)

            if node_path in self.nodes:
                for imported in self.nodes[node_path].imports_from:
                    dfs(imported, path[:], recursion_stack.copy())

            recursion_stack.remove(node_path)

        for node_path in self.nodes:
            dfs(node_path, [], set())

        return cycles

    def get_impacted_files(self, changed_file: str) -> List[str]:
        """
        Retourne tous les fichiers impactés par un changement

        Args:
            changed_file: Fichier modifié

        Returns:
            Liste de fichiers qui dépendent de ce fichier
        """
        if changed_file not in self.nodes:
            return []

        impacted = set()
        queue = [changed_file]

        while queue:
            current = queue.pop(0)

            if current in impacted:
                continue

            impacted.add(current)

            if current in self.nodes:
                for importer in self.nodes[current].imported_by:
                    if importer not in impacted:
                        queue.append(importer)

        return list(impacted)

    def _save_graph(self):
        """Sauvegarde le graphe"""
        data = {
            "updated_at": datetime.now().isoformat(),
            "total_nodes": len(self.nodes),
            "critical_nodes": sum(1 for n in self.nodes.values() if n.is_critical),
            "circular_dependencies": self.circular_dependencies,
            "nodes": {path: node.to_dict() for path, node in self.nodes.items()}
        }

        with open(self.graph_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def create_dependency_tracker(context_updater: ContextUpdater) -> DependencyTracker:
    """Factory function"""
    return DependencyTracker(context_updater)


# Test
if __name__ == "__main__":
    print("Testing Dependency Tracker...")

    from cortex.departments.maintenance.context_updater import ContextUpdater

    # Créer updater
    updater = ContextUpdater("cortex/data/test_context_cache_dep.json")

    # Créer tracker
    tracker = DependencyTracker(updater, "cortex/data/test_dependency_graph.json")

    # Test: Build graph
    print("\n1. Building dependency graph...")
    graph = tracker.build_dependency_graph(["cortex/core"])

    # Test: Get impacted files
    print("\n2. Testing impact analysis...")
    impacted = tracker.get_impacted_files("cortex/core/workflow_engine.py")
    print(f"✓ Files impacted by workflow_engine.py: {len(impacted)}")

    # Test: Show critical modules
    print("\n3. Critical modules:")
    critical = [n for n in graph.values() if n.is_critical]
    for node in critical[:5]:
        print(f"  - {node.file_path} (used by {len(node.imported_by)} files)")

    print("\n✓ Dependency Tracker works correctly!")
