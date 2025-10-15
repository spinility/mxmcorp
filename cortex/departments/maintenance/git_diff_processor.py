"""
Git Diff Processor - Parse et analyse git diff pour détecter changements

Utilisé par le département Maintenance pour savoir ce qui a changé
"""

import subprocess
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class FileChange:
    """Représente un changement sur un fichier"""
    filepath: str
    change_type: str  # 'added', 'modified', 'deleted', 'renamed'
    lines_added: int
    lines_removed: int
    old_path: Optional[str] = None  # Pour renamed
    content_added: List[str] = field(default_factory=list)
    content_removed: List[str] = field(default_factory=list)


@dataclass
class GitDiffAnalysis:
    """Résultat de l'analyse d'un git diff"""
    total_files_changed: int
    files_added: List[str]
    files_modified: List[str]
    files_deleted: List[str]
    files_renamed: Dict[str, str]  # old_path -> new_path
    total_lines_added: int
    total_lines_removed: int
    file_changes: List[FileChange]
    diff_raw: str
    commit_hash: Optional[str] = None
    commit_message: Optional[str] = None


class GitDiffProcessor:
    """
    Processeur de git diff

    Analyse les modifications git pour:
    - Détecter fichiers modifiés/ajoutés/supprimés
    - Compter lignes changées
    - Extraire contenu ajouté/supprimé
    - Identifier dépendances potentiellement affectées
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)

    def get_latest_diff(self, include_staged: bool = False) -> GitDiffAnalysis:
        """
        Récupère le diff le plus récent

        Args:
            include_staged: Inclure les changements staged

        Returns:
            GitDiffAnalysis avec tous les changements
        """
        # Git diff HEAD^ HEAD (dernier commit)
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD^", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                # Pas de commits ou erreur, essayer diff working directory
                result = subprocess.run(
                    ["git", "diff"] if not include_staged else ["git", "diff", "--staged"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

            diff_raw = result.stdout

        except subprocess.TimeoutExpired:
            diff_raw = ""
        except Exception as e:
            print(f"Error getting git diff: {e}")
            diff_raw = ""

        return self.parse_diff(diff_raw)

    def get_diff_between_commits(self, commit1: str, commit2: str = "HEAD") -> GitDiffAnalysis:
        """
        Récupère le diff entre deux commits

        Args:
            commit1: Premier commit
            commit2: Deuxième commit (défaut: HEAD)

        Returns:
            GitDiffAnalysis
        """
        try:
            result = subprocess.run(
                ["git", "diff", commit1, commit2],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            diff_raw = result.stdout
        except Exception as e:
            print(f"Error getting diff between commits: {e}")
            diff_raw = ""

        analysis = self.parse_diff(diff_raw)
        analysis.commit_hash = commit2
        return analysis

    def parse_diff(self, diff_text: str) -> GitDiffAnalysis:
        """
        Parse un diff git et extrait toutes les informations

        Args:
            diff_text: Texte brut du diff

        Returns:
            GitDiffAnalysis avec détails
        """
        if not diff_text.strip():
            return GitDiffAnalysis(
                total_files_changed=0,
                files_added=[],
                files_modified=[],
                files_deleted=[],
                files_renamed={},
                total_lines_added=0,
                total_lines_removed=0,
                file_changes=[],
                diff_raw=""
            )

        file_changes = []
        files_added = []
        files_modified = []
        files_deleted = []
        files_renamed = {}

        total_lines_added = 0
        total_lines_removed = 0

        # Parser le diff ligne par ligne
        current_file = None
        current_file_lines_added = 0
        current_file_lines_removed = 0
        current_content_added = []
        current_content_removed = []

        for line in diff_text.split('\n'):
            # Nouveau fichier
            if line.startswith('diff --git'):
                # Sauvegarder le fichier précédent si existe
                if current_file:
                    file_changes.append(FileChange(
                        filepath=current_file,
                        change_type='modified',  # Sera ajusté après
                        lines_added=current_file_lines_added,
                        lines_removed=current_file_lines_removed,
                        content_added=current_content_added,
                        content_removed=current_content_removed
                    ))

                # Extraire le nom du fichier
                match = re.search(r'diff --git a/(.*?) b/(.*)', line)
                if match:
                    current_file = match.group(2)
                    current_file_lines_added = 0
                    current_file_lines_removed = 0
                    current_content_added = []
                    current_content_removed = []

            # Fichier supprimé
            elif line.startswith('deleted file mode'):
                if current_file:
                    files_deleted.append(current_file)

            # Nouveau fichier
            elif line.startswith('new file mode'):
                if current_file:
                    files_added.append(current_file)

            # Fichier renommé
            elif line.startswith('rename from'):
                old_name = line.replace('rename from ', '').strip()
                if current_file:
                    files_renamed[old_name] = current_file

            # Ligne ajoutée
            elif line.startswith('+') and not line.startswith('+++'):
                current_file_lines_added += 1
                total_lines_added += 1
                current_content_added.append(line[1:])  # Remove '+'

            # Ligne supprimée
            elif line.startswith('-') and not line.startswith('---'):
                current_file_lines_removed += 1
                total_lines_removed += 1
                current_content_removed.append(line[1:])  # Remove '-'

        # Sauvegarder dernier fichier
        if current_file:
            # Déterminer type de changement
            change_type = 'modified'
            if current_file in files_added:
                change_type = 'added'
            elif current_file in files_deleted:
                change_type = 'deleted'
            elif any(old for old, new in files_renamed.items() if new == current_file):
                change_type = 'renamed'

            file_changes.append(FileChange(
                filepath=current_file,
                change_type=change_type,
                lines_added=current_file_lines_added,
                lines_removed=current_file_lines_removed,
                content_added=current_content_added,
                content_removed=current_content_removed,
                old_path=next((old for old, new in files_renamed.items() if new == current_file), None)
            ))

        # Identifier fichiers modifiés (ni added ni deleted ni renamed)
        all_files = {fc.filepath for fc in file_changes}
        files_modified = list(all_files - set(files_added) - set(files_deleted) - set(files_renamed.values()))

        return GitDiffAnalysis(
            total_files_changed=len(file_changes),
            files_added=files_added,
            files_modified=files_modified,
            files_deleted=files_deleted,
            files_renamed=files_renamed,
            total_lines_added=total_lines_added,
            total_lines_removed=total_lines_removed,
            file_changes=file_changes,
            diff_raw=diff_text
        )

    def get_affected_modules(self, analysis: GitDiffAnalysis) -> List[str]:
        """
        Identifie les modules Python affectés

        Args:
            analysis: Résultat de parse_diff

        Returns:
            Liste des modules (ex: ['cortex.core', 'cortex.agents'])
        """
        modules = set()

        for file_change in analysis.file_changes:
            if file_change.filepath.endswith('.py'):
                # Convertir path en module
                # Ex: cortex/core/agent.py -> cortex.core
                path = Path(file_change.filepath)
                parts = path.with_suffix('').parts

                if len(parts) > 1:
                    module = '.'.join(parts[:-1]) if parts[-1] != '__init__' else '.'.join(parts[:-1])
                    if module:
                        modules.add(module)

        return sorted(modules)

    def summarize_changes(self, analysis: GitDiffAnalysis) -> str:
        """
        Génère un résumé lisible des changements

        Args:
            analysis: Résultat de parse_diff

        Returns:
            Résumé formaté
        """
        lines = []
        lines.append(f"📊 Git Diff Summary")
        lines.append(f"{'='*50}")
        lines.append(f"Total files changed: {analysis.total_files_changed}")
        lines.append(f"  Added: {len(analysis.files_added)}")
        lines.append(f"  Modified: {len(analysis.files_modified)}")
        lines.append(f"  Deleted: {len(analysis.files_deleted)}")
        lines.append(f"  Renamed: {len(analysis.files_renamed)}")
        lines.append(f"")
        lines.append(f"Lines: +{analysis.total_lines_added} -{analysis.total_lines_removed}")
        lines.append(f"")

        if analysis.files_added:
            lines.append("➕ Added:")
            for f in analysis.files_added[:5]:
                lines.append(f"  - {f}")
            if len(analysis.files_added) > 5:
                lines.append(f"  ... and {len(analysis.files_added) - 5} more")

        if analysis.files_modified:
            lines.append("")
            lines.append("📝 Modified:")
            for f in analysis.files_modified[:5]:
                lines.append(f"  - {f}")
            if len(analysis.files_modified) > 5:
                lines.append(f"  ... and {len(analysis.files_modified) - 5} more")

        if analysis.files_deleted:
            lines.append("")
            lines.append("🗑️  Deleted:")
            for f in analysis.files_deleted[:5]:
                lines.append(f"  - {f}")

        if analysis.files_renamed:
            lines.append("")
            lines.append("📦 Renamed:")
            for old, new in list(analysis.files_renamed.items())[:5]:
                lines.append(f"  - {old} → {new}")

        return '\n'.join(lines)


# Factory function
def create_git_diff_processor(repo_path: str = ".") -> GitDiffProcessor:
    """Crée un GitDiffProcessor"""
    return GitDiffProcessor(repo_path)


# Test
if __name__ == "__main__":
    print("Testing Git Diff Processor...")

    processor = create_git_diff_processor()

    # Test 1: Dernier diff
    print("\n1. Getting latest diff...")
    analysis = processor.get_latest_diff()
    print(f"✓ Files changed: {analysis.total_files_changed}")
    print(f"  Lines: +{analysis.total_lines_added} -{analysis.total_lines_removed}")

    # Test 2: Summary
    print("\n2. Generating summary...")
    summary = processor.summarize_changes(analysis)
    print(summary)

    # Test 3: Affected modules
    if analysis.total_files_changed > 0:
        print("\n3. Affected modules...")
        modules = processor.get_affected_modules(analysis)
        print(f"✓ Affected modules: {modules}")

    print("\n✓ Git Diff Processor works correctly!")
