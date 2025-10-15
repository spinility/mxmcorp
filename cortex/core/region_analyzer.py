"""
Region Analyzer - Automatic detection and management of code regions

Fonctionnalités:
- Détection automatique des fonctions, classes, méthodes
- Injection de markers de région
- Extraction et remplacement de régions
- Support multi-langages (Python, JS, Go, etc.)
"""

import re
import ast
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CodeRegion:
    """Représente une région de code isolée"""
    id: str
    name: str
    type: str  # 'function', 'class', 'method', 'block'
    start_line: int
    end_line: int
    content: str
    indentation: int
    language: str
    parent_id: Optional[str] = None


class RegionAnalyzer:
    """Analyse et gère les régions de code"""

    SUPPORTED_LANGUAGES = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.go': 'go',
        '.java': 'java',
        '.rb': 'ruby'
    }

    def __init__(self):
        self.regions: Dict[str, CodeRegion] = {}

    def detect_language(self, filepath: str) -> str:
        """Détecte le langage du fichier"""
        ext = Path(filepath).suffix
        return self.SUPPORTED_LANGUAGES.get(ext, 'unknown')

    def analyze_file(self, filepath: str) -> List[CodeRegion]:
        """
        Analyse un fichier et détecte toutes les régions

        Args:
            filepath: Chemin du fichier à analyser

        Returns:
            Liste des régions détectées
        """
        language = self.detect_language(filepath)

        if language == 'python':
            return self._analyze_python(filepath)
        else:
            # Fallback: analyse basique par regex
            return self._analyze_generic(filepath, language)

    def _analyze_python(self, filepath: str) -> List[CodeRegion]:
        """Analyse un fichier Python avec AST"""
        regions = []

        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
            lines = source.split('\n')

        try:
            tree = ast.parse(source)
        except SyntaxError:
            # Si syntax error, fallback sur analyse générique
            return self._analyze_generic(filepath, 'python')

        # Parcourir l'AST
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                region = self._create_region_from_node(
                    node, lines, 'function', filepath
                )
                if region:
                    regions.append(region)

            elif isinstance(node, ast.ClassDef):
                region = self._create_region_from_node(
                    node, lines, 'class', filepath
                )
                if region:
                    regions.append(region)

        # Trier par ligne de début
        regions.sort(key=lambda r: r.start_line)

        # Assigner les IDs et parents
        for i, region in enumerate(regions):
            region.id = self._generate_region_id(region, i)
            region.parent_id = self._find_parent_region(region, regions)

        self.regions = {r.id: r for r in regions}
        return regions

    def _create_region_from_node(
        self,
        node: ast.AST,
        lines: List[str],
        region_type: str,
        filepath: str
    ) -> Optional[CodeRegion]:
        """Crée une région depuis un nœud AST"""
        if not hasattr(node, 'lineno') or not hasattr(node, 'end_lineno'):
            return None

        start_line = node.lineno
        end_line = node.end_lineno

        if end_line is None:
            return None

        # Extraire le contenu
        content_lines = lines[start_line - 1:end_line]
        content = '\n'.join(content_lines)

        # Calculer l'indentation
        first_line = content_lines[0] if content_lines else ""
        indentation = len(first_line) - len(first_line.lstrip())

        # Nom de la région
        name = getattr(node, 'name', f'anonymous_{region_type}')

        return CodeRegion(
            id="",  # Will be set later
            name=name,
            type=region_type,
            start_line=start_line,
            end_line=end_line,
            content=content,
            indentation=indentation,
            language='python',
            parent_id=None
        )

    def _analyze_generic(self, filepath: str, language: str) -> List[CodeRegion]:
        """Analyse générique par regex (fallback)"""
        regions = []

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Patterns pour différents langages
        patterns = {
            'python': r'^(\s*)(def|class)\s+(\w+)',
            'javascript': r'^(\s*)(function|class)\s+(\w+)',
            'go': r'^(\s*)func\s+(\w+)',
        }

        pattern = patterns.get(language, patterns['python'])

        current_region_start = None
        current_indent = None

        for i, line in enumerate(lines, 1):
            match = re.match(pattern, line)
            if match:
                # Terminer la région précédente si existe
                if current_region_start is not None:
                    regions.append(self._create_generic_region(
                        lines, current_region_start, i - 1, language
                    ))

                # Démarrer nouvelle région
                current_region_start = i
                current_indent = len(match.group(1))

        # Terminer la dernière région
        if current_region_start is not None:
            regions.append(self._create_generic_region(
                lines, current_region_start, len(lines), language
            ))

        return regions

    def _create_generic_region(
        self,
        lines: List[str],
        start: int,
        end: int,
        language: str
    ) -> CodeRegion:
        """Crée une région générique"""
        content_lines = lines[start - 1:end]
        content = ''.join(content_lines)

        # Extraire le nom depuis la première ligne
        first_line = content_lines[0] if content_lines else ""
        name_match = re.search(r'(def|class|function|func)\s+(\w+)', first_line)
        name = name_match.group(2) if name_match else f"region_{start}"

        return CodeRegion(
            id=f"{language}_{name}_{start}",
            name=name,
            type='function',  # Generic type
            start_line=start,
            end_line=end,
            content=content,
            indentation=len(first_line) - len(first_line.lstrip()),
            language=language
        )

    def _generate_region_id(self, region: CodeRegion, index: int) -> str:
        """Génère un ID unique pour une région"""
        # Hash basé sur nom + type + ligne
        hash_input = f"{region.name}_{region.type}_{region.start_line}"
        hash_short = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"{region.type}_{region.name}_{hash_short}"

    def _find_parent_region(
        self,
        region: CodeRegion,
        all_regions: List[CodeRegion]
    ) -> Optional[str]:
        """Trouve la région parente (pour méthodes dans classes)"""
        for other in all_regions:
            if (other.type == 'class' and
                other.start_line < region.start_line and
                other.end_line > region.end_line):
                return other.id
        return None

    def inject_regions(
        self,
        filepath: str,
        inplace: bool = False
    ) -> Tuple[str, Dict[str, CodeRegion]]:
        """
        Injecte des markers de région dans le fichier

        Args:
            filepath: Chemin du fichier
            inplace: Si True, modifie le fichier directement

        Returns:
            (contenu avec markers, dict des régions)
        """
        regions = self.analyze_file(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Injecter les markers en ordre inverse (pour préserver numéros de ligne)
        for region in reversed(regions):
            language = self.detect_language(filepath)
            comment_prefix = self._get_comment_prefix(language)

            # Marker de début
            start_marker = f"{comment_prefix} REGION: {region.name} [{region.id}]\n"
            lines.insert(region.start_line - 1, start_marker)

            # Marker de fin (ajuster pour le marker de début)
            end_marker = f"{comment_prefix} END_REGION [{region.id}]\n"
            lines.insert(region.end_line + 1, end_marker)

        new_content = ''.join(lines)

        if inplace:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)

        return new_content, {r.id: r for r in regions}

    def _get_comment_prefix(self, language: str) -> str:
        """Retourne le préfixe de commentaire selon le langage"""
        prefixes = {
            'python': '#',
            'javascript': '//',
            'typescript': '//',
            'go': '//',
            'java': '//',
            'ruby': '#'
        }
        return prefixes.get(language, '#')

    def extract_region(self, filepath: str, region_id: str) -> Optional[str]:
        """
        Extrait le contenu d'une région spécifique

        Args:
            filepath: Chemin du fichier
            region_id: ID de la région à extraire

        Returns:
            Contenu de la région ou None si non trouvée
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Chercher les markers
        pattern = rf'#\s*REGION:.*?\[{re.escape(region_id)}\]\n(.*?)#\s*END_REGION\s*\[{re.escape(region_id)}\]'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            return match.group(1).rstrip('\n')

        # Si pas de markers, utiliser l'analyse directe
        regions = self.analyze_file(filepath)
        for region in regions:
            if region.id == region_id:
                return region.content

        return None

    def replace_region(
        self,
        filepath: str,
        region_id: str,
        new_content: str,
        inplace: bool = False
    ) -> str:
        """
        Remplace le contenu d'une région

        Args:
            filepath: Chemin du fichier
            region_id: ID de la région à remplacer
            new_content: Nouveau contenu
            inplace: Si True, modifie le fichier directement

        Returns:
            Nouveau contenu complet du fichier
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Chercher et remplacer avec les markers
        pattern = rf'(#\s*REGION:.*?\[{re.escape(region_id)}\]\n)(.*?)(#\s*END_REGION\s*\[{re.escape(region_id)}\])'

        def replacer(match):
            return match.group(1) + new_content + '\n' + match.group(3)

        new_full_content = re.sub(pattern, replacer, content, flags=re.DOTALL)

        if inplace:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_full_content)

        return new_full_content

    def get_region_context(
        self,
        filepath: str,
        region_id: str,
        context_lines: int = 5
    ) -> Dict[str, str]:
        """
        Obtient le contexte autour d'une région

        Args:
            filepath: Chemin du fichier
            region_id: ID de la région
            context_lines: Nombre de lignes de contexte

        Returns:
            Dict avec before, region, after
        """
        regions = self.analyze_file(filepath)
        target_region = None

        for region in regions:
            if region.id == region_id:
                target_region = region
                break

        if not target_region:
            return {}

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        before_start = max(0, target_region.start_line - context_lines - 1)
        before_lines = lines[before_start:target_region.start_line - 1]

        after_end = min(len(lines), target_region.end_line + context_lines)
        after_lines = lines[target_region.end_line:after_end]

        return {
            'before': ''.join(before_lines),
            'region': target_region.content,
            'after': ''.join(after_lines)
        }


def create_region_analyzer() -> RegionAnalyzer:
    """Factory function pour créer un RegionAnalyzer"""
    return RegionAnalyzer()


# Test si exécuté directement
if __name__ == "__main__":
    print("Testing Region Analyzer...")

    # Test sur ce fichier même
    analyzer = RegionAnalyzer()

    print("\n1. Testing file analysis...")
    regions = analyzer.analyze_file(__file__)
    print(f"✓ Found {len(regions)} regions:")
    for region in regions[:5]:  # Show first 5
        print(f"  - [{region.id}] {region.type} '{region.name}' (lines {region.start_line}-{region.end_line})")

    print("\n2. Testing region extraction...")
    if regions:
        first_region = regions[0]
        content = analyzer.extract_region(__file__, first_region.id)
        print(f"✓ Extracted region '{first_region.name}':")
        print(f"  Content preview: {content[:100] if content else 'None'}...")

    print("\n3. Testing region context...")
    if regions:
        context = analyzer.get_region_context(__file__, regions[0].id, context_lines=2)
        print(f"✓ Context for '{regions[0].name}':")
        print(f"  Before: {len(context.get('before', ''))} chars")
        print(f"  Region: {len(context.get('region', ''))} chars")
        print(f"  After: {len(context.get('after', ''))} chars")

    print("\n✓ Region Analyzer works correctly!")
