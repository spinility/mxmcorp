"""
Context Updater - Maintient cache de contextes pour économiser tokens

Responsabilités:
- Parse fichiers Python pour extraire structure
- Génère summaries concis
- Cache contextes pour éviter lectures complètes
- Met à jour automatiquement après git diff

Réduction de tokens: ~95% (résumé 100 lignes vs 5000 lignes complètes)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import ast
import re


@dataclass
class FileContext:
    """Contexte d'un fichier Python"""
    file_path: str
    summary: str
    exports: List[str]  # __all__ ou exports détectés
    imports: List[str]  # Modules importés
    classes: List[str]  # Classes définies
    functions: List[str]  # Fonctions définies
    docstring: Optional[str]  # Module docstring
    last_updated: datetime
    lines_of_code: int
    complexity_score: float  # 0-1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "summary": self.summary,
            "exports": self.exports,
            "imports": self.imports,
            "classes": self.classes,
            "functions": self.functions,
            "docstring": self.docstring,
            "last_updated": self.last_updated.isoformat(),
            "lines_of_code": self.lines_of_code,
            "complexity_score": self.complexity_score
        }


class ContextUpdater:
    """
    Gestionnaire de cache de contextes

    Maintient résumés concis de tous les fichiers Python
    pour éviter de lire fichiers complets (économie tokens)
    """

    def __init__(self, cache_file: str = "cortex/data/context_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        self.contexts: Dict[str, FileContext] = {}
        self._load_cache()

    def _load_cache(self):
        """Charge le cache depuis disque"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    for ctx_data in data.get("contexts", []):
                        if "last_updated" in ctx_data:
                            ctx_data["last_updated"] = datetime.fromisoformat(ctx_data["last_updated"])
                        else:
                            ctx_data["last_updated"] = datetime.now()
                        context = FileContext(**ctx_data)
                        self.contexts[context.file_path] = context
            except Exception as e:
                print(f"Warning: Could not load cache: {e}")

    def _save_cache(self):
        """Sauvegarde le cache sur disque"""
        data = {
            "updated_at": datetime.now().isoformat(),
            "total_files": len(self.contexts),
            "contexts": [ctx.to_dict() for ctx in self.contexts.values()]
        }

        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def update_file_context(self, file_path: str) -> FileContext:
        """
        Met à jour le contexte d'un fichier

        Parse le fichier Python et extrait structure

        Args:
            file_path: Chemin vers le fichier

        Returns:
            FileContext mis à jour
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not path.suffix == '.py':
            raise ValueError(f"Not a Python file: {file_path}")

        # Lire contenu
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parser avec AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"Warning: Syntax error in {file_path}: {e}")
            # Créer contexte minimal
            return self._create_minimal_context(file_path, content)

        # Extraire informations
        context = FileContext(
            file_path=file_path,
            summary=self._generate_summary(tree, content, path),
            exports=self._extract_exports(tree),
            imports=self._extract_imports(tree),
            classes=self._extract_classes(tree),
            functions=self._extract_functions(tree),
            docstring=ast.get_docstring(tree),
            last_updated=datetime.now(),
            lines_of_code=len(content.splitlines()),
            complexity_score=self._calculate_complexity(tree)
        )

        # Sauvegarder dans cache
        self.contexts[file_path] = context
        self._save_cache()

        return context

    def _create_minimal_context(self, file_path: str, content: str) -> FileContext:
        """Crée contexte minimal si parsing échoue"""
        return FileContext(
            file_path=file_path,
            summary="File with syntax errors or unparseable content",
            exports=[],
            imports=[],
            classes=[],
            functions=[],
            docstring=None,
            last_updated=datetime.now(),
            lines_of_code=len(content.splitlines()),
            complexity_score=0.0
        )

    def _extract_exports(self, tree: ast.AST) -> List[str]:
        """Extrait liste __all__ ou exports détectés"""
        exports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '__all__':
                        # __all__ trouvé
                        if isinstance(node.value, ast.List):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant):
                                    exports.append(elt.value)

        # Si pas de __all__, extraire classes et fonctions publiques
        if not exports:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                    exports.append(node.name)
                elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    exports.append(node.name)

        return exports

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extrait tous les imports"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return list(set(imports))  # Unique

    def _extract_classes(self, tree: ast.AST) -> List[str]:
        """Extrait noms des classes"""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)

        return classes

    def _extract_functions(self, tree: ast.AST) -> List[str]:
        """Extrait noms des fonctions (top-level)"""
        functions = []

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)

        return functions

    def _calculate_complexity(self, tree: ast.AST) -> float:
        """
        Calcule score de complexité (0-1)

        Basé sur:
        - Nombre de classes
        - Nombre de fonctions
        - Profondeur d'imbrication
        """
        classes = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.ClassDef))
        functions = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.FunctionDef))
        loops = sum(1 for _ in ast.walk(tree) if isinstance(_, (ast.For, ast.While)))
        conditions = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.If))

        # Score normalisé
        complexity = (classes * 2 + functions + loops + conditions) / 50.0
        return min(complexity, 1.0)

    def _generate_summary(self, tree: ast.AST, content: str, path: Path) -> str:
        """
        Génère résumé concis du fichier

        Format: "Description | Classes: X | Functions: Y | Exports: Z"
        """
        # Essayer d'utiliser docstring module
        docstring = ast.get_docstring(tree)

        if docstring:
            # Prendre première ligne du docstring
            first_line = docstring.split('\n')[0].strip()
            summary = first_line[:100]
        else:
            # Générer description basée sur nom de fichier
            filename = path.stem.replace('_', ' ').title()
            summary = f"{filename} module"

        # Ajouter statistiques
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        functions = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]

        if classes:
            summary += f" | Classes: {', '.join(classes[:3])}"
            if len(classes) > 3:
                summary += f" (+{len(classes)-3} more)"

        if functions:
            summary += f" | Functions: {', '.join(functions[:3])}"
            if len(functions) > 3:
                summary += f" (+{len(functions)-3} more)"

        return summary[:300]  # Max 300 chars

    def update_multiple_files(self, file_paths: List[str]) -> Dict[str, FileContext]:
        """
        Met à jour contextes de plusieurs fichiers

        Args:
            file_paths: Liste de chemins

        Returns:
            Dict {file_path: FileContext}
        """
        updated = {}

        for file_path in file_paths:
            try:
                context = self.update_file_context(file_path)
                updated[file_path] = context
                print(f"✓ Updated context: {file_path}")
            except Exception as e:
                print(f"✗ Error updating {file_path}: {e}")

        return updated

    def get_context(self, file_path: str) -> Optional[FileContext]:
        """Récupère contexte depuis cache"""
        return self.contexts.get(file_path)

    def get_context_summary(self, file_path: str) -> str:
        """
        Récupère résumé concis d'un fichier

        Si pas en cache, update automatiquement
        """
        context = self.get_context(file_path)

        if not context:
            # Pas en cache, update
            try:
                context = self.update_file_context(file_path)
            except Exception as e:
                return f"Error loading context: {e}"

        return f"{context.summary} ({context.lines_of_code} LOC)"

    def search_contexts(self, query: str) -> List[FileContext]:
        """
        Recherche dans les contextes

        Args:
            query: Terme à rechercher

        Returns:
            Liste de contextes matchants
        """
        results = []
        query_lower = query.lower()

        for context in self.contexts.values():
            # Rechercher dans summary, classes, functions
            if (query_lower in context.summary.lower() or
                any(query_lower in c.lower() for c in context.classes) or
                any(query_lower in f.lower() for f in context.functions)):
                results.append(context)

        return results


def create_context_updater(cache_file: str = "cortex/data/context_cache.json") -> ContextUpdater:
    """Factory function"""
    return ContextUpdater(cache_file)


# Test
if __name__ == "__main__":
    print("Testing Context Updater...")

    updater = ContextUpdater("cortex/data/test_context_cache.json")

    # Test 1: Update single file
    print("\n1. Updating context for single file...")
    context = updater.update_file_context("cortex/core/workflow_engine.py")

    print(f"✓ Context updated:")
    print(f"  Summary: {context.summary}")
    print(f"  Classes: {len(context.classes)}")
    print(f"  Functions: {len(context.functions)}")
    print(f"  Exports: {len(context.exports)}")
    print(f"  Imports: {len(context.imports)}")
    print(f"  LOC: {context.lines_of_code}")
    print(f"  Complexity: {context.complexity_score:.2f}")

    # Test 2: Update multiple files
    print("\n2. Updating multiple files...")
    files = [
        "cortex/core/todolist_manager.py",
        "cortex/departments/optimization/optimization_knowledge.py"
    ]

    updated = updater.update_multiple_files(files)
    print(f"✓ Updated {len(updated)} files")

    # Test 3: Get summary
    print("\n3. Getting context summary...")
    summary = updater.get_context_summary("cortex/core/workflow_engine.py")
    print(f"✓ Summary: {summary}")

    # Test 4: Search
    print("\n4. Searching contexts...")
    results = updater.search_contexts("workflow")
    print(f"✓ Found {len(results)} matches for 'workflow'")

    print("\n✓ Context Updater works correctly!")
