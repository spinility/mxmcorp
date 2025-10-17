"""
Git Watcher Agent - Surveille tous les changements git et déclenche l'harmonisation

Responsabilités:
- Surveiller git diff pour détecter les changements
- Analyser les fichiers modifiés
- Identifier les impacts potentiels
- Logger tous les changements dans la DB
- Déclencher l'agent d'harmonisation si nécessaire
- Mettre à jour la structure du codebase automatiquement

L'agent tourne en arrière-plan et est déclenché après chaque commit/modification.
"""

import subprocess
import re
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from cortex.core.agent_hierarchy import CoordinationAgent, AgentRole, AgentResult
from cortex.core.model_router import ModelTier
from cortex.core.llm_client import LLMClient
from cortex.repositories.changelog_repository import get_changelog_repository
from cortex.repositories.file_repository import get_file_repository
from cortex.repositories.codebase_repository import get_codebase_repository
from cortex.core.agent_memory import get_agent_memory


class GitWatcherAgent(CoordinationAgent):
    """
    Agent de surveillance Git - Détecte et analyse tous les changements

    Workflow:
    1. git diff → Détection des changements
    2. Analyse des fichiers modifiés
    3. Évaluation de l'impact
    4. Logging dans change_log
    5. Déclenchement harmonisation si nécessaire
    """

    def __init__(self, llm_client: LLMClient):
        super().__init__(
            llm_client=llm_client,
            specialization="git_change_detection"
        )
        self.tier = ModelTier.DEEPSEEK  # Analyse intelligente des changements

        # Repositories
        self.changelog_repo = get_changelog_repository()
        self.file_repo = get_file_repository()
        self.codebase_repo = get_codebase_repository()

        # Memory
        self.memory = get_agent_memory('intelligence', 'git_watcher')

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """Détecte si la requête concerne git/changements"""
        keywords = ['git', 'diff', 'change', 'commit', 'modified', 'watch']
        request_lower = request.lower()
        matches = sum(1 for kw in keywords if kw in request_lower)
        return min(matches / 2.0, 1.0)

    def execute(self, request: str, context: Optional[Dict] = None,
                escalation_context: Optional[Any] = None) -> AgentResult:
        """
        Exécute la surveillance git et l'analyse des changements

        Args:
            request: "watch", "check", "analyze_last_commit", etc.
            context: {
                'commit_id': optionnel,
                'file_paths': optionnel (liste de fichiers spécifiques)
            }
        """
        try:
            if context is None:
                context = {}

            # Déterminer l'action
            if 'analyze_last_commit' in request.lower() or 'last' in request.lower():
                result = self.analyze_last_commit()
            elif 'watch' in request.lower() or 'check' in request.lower():
                result = self.watch_git_changes()
            elif 'diff' in request.lower():
                result = self.analyze_git_diff(context.get('file_paths'))
            else:
                result = self.watch_git_changes()

            return AgentResult(
                success=True,
                role=AgentRole.CORTEX_CENTRAL,
                tier=self.tier,
                content=result,
                cost=0.0001,  # Coût estimé
                confidence=0.9
            )

        except Exception as e:
            return AgentResult(
                success=False,
                role=AgentRole.CORTEX_CENTRAL,
                tier=self.tier,
                content=None,
                cost=0.0,
                confidence=0.0,
                error=str(e)
            )

    def watch_git_changes(self) -> Dict[str, Any]:
        """
        Surveille les changements git non committés
        Analyse git status + git diff
        """
        start_time = time.time()

        try:
            # Git status pour voir les fichiers modifiés
            status_result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                check=True
            )

            changed_files = self._parse_git_status(status_result.stdout)

            if not changed_files:
                return {
                    'status': 'no_changes',
                    'message': 'No uncommitted changes detected',
                    'changed_files': []
                }

            # Analyser les changements
            analysis = self._analyze_changed_files(changed_files)

            # Logger les changements détectés
            for file_info in changed_files:
                self.changelog_repo.log_change(
                    change_type=file_info['change_type'],
                    entity_type='file',
                    author='GitWatcherAgent',
                    description=f"{file_info['change_type']} {file_info['path']}",
                    impact_level=analysis.get('impact_level', 'low')
                )

            # Décider si harmonisation nécessaire
            needs_harmonization = analysis['impact_level'] in ['high', 'critical']

            result = {
                'status': 'changes_detected',
                'changed_files': changed_files,
                'analysis': analysis,
                'needs_harmonization': needs_harmonization,
                'timestamp': datetime.now().isoformat()
            }

            # Record to memory
            duration = time.time() - start_time
            self.memory.record_execution(
                request=f"Watch git changes: {len(changed_files)} files",
                result=result,
                duration=duration,
                cost=0.0
            )

            # Update state
            self.memory.update_state({
                'last_watch_timestamp': datetime.now().isoformat(),
                'files_changed': len(changed_files),
                'impact_level': analysis['impact_level'],
                'needs_harmonization': needs_harmonization
            })

            # Detect patterns in change types
            for file_info in changed_files:
                self.memory.add_pattern(
                    f'change_type_{file_info["change_type"]}',
                    {
                        'change_type': file_info['change_type'],
                        'path': file_info['path'],
                        'impact': analysis['impact_level']
                    }
                )

            return result

        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            result = {
                'status': 'error',
                'message': f'Git command failed: {e}',
                'error': str(e)
            }

            # Record failure to memory
            self.memory.record_execution(
                request="Watch git changes",
                result=result,
                duration=duration,
                cost=0.0
            )

            return result

    def analyze_last_commit(self) -> Dict[str, Any]:
        """Analyse le dernier commit git"""
        start_time = time.time()

        try:
            # Obtenir le dernier commit
            commit_info = subprocess.run(
                ['git', 'log', '-1', '--pretty=format:%H|%an|%ae|%s|%at'],
                capture_output=True,
                text=True,
                check=True
            )

            commit_hash, author, email, message, timestamp = commit_info.stdout.split('|')

            # Obtenir les fichiers modifiés dans ce commit
            diff_result = subprocess.run(
                ['git', 'diff-tree', '--no-commit-id', '--name-status', '-r', commit_hash],
                capture_output=True,
                text=True,
                check=True
            )

            changed_files = self._parse_git_diff_tree(diff_result.stdout)

            # Analyser l'impact
            analysis = self._analyze_changed_files(changed_files)

            # Logger dans change_log
            self.changelog_repo.log_change(
                change_type='commit',
                entity_type='repository',
                author=author,
                description=f"Commit: {message}",
                impact_level=analysis.get('impact_level', 'medium'),
                metadata={
                    'commit_hash': commit_hash,
                    'email': email,
                    'timestamp': timestamp,
                    'files_changed': len(changed_files)
                }
            )

            result = {
                'status': 'analyzed',
                'commit': {
                    'hash': commit_hash,
                    'author': author,
                    'message': message,
                    'timestamp': timestamp
                },
                'changed_files': changed_files,
                'analysis': analysis,
                'needs_harmonization': analysis['impact_level'] in ['high', 'critical']
            }

            # Record to memory
            duration = time.time() - start_time
            self.memory.record_execution(
                request=f"Analyze last commit: {commit_hash[:8]}",
                result=result,
                duration=duration,
                cost=0.0
            )

            # Update state
            self.memory.update_state({
                'last_commit_analyzed': commit_hash,
                'last_commit_message': message[:100],
                'last_commit_author': author,
                'last_commit_impact': analysis['impact_level']
            })

            # Detect patterns in commit analysis
            self.memory.add_pattern(
                f'commit_impact_{analysis["impact_level"]}',
                {
                    'impact': analysis['impact_level'],
                    'files_changed': len(changed_files),
                    'author': author
                }
            )

            return result

        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            result = {
                'status': 'error',
                'message': f'Failed to analyze commit: {e}',
                'error': str(e)
            }

            # Record failure to memory
            self.memory.record_execution(
                request="Analyze last commit",
                result=result,
                duration=duration,
                cost=0.0
            )

            return result

    def analyze_git_diff(self, file_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyse git diff pour des fichiers spécifiques ou tous"""
        start_time = time.time()

        try:
            cmd = ['git', 'diff', '--name-status']
            if file_paths:
                cmd.extend(file_paths)

            diff_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            changed_files = self._parse_git_diff_tree(diff_result.stdout)
            analysis = self._analyze_changed_files(changed_files)

            result = {
                'status': 'analyzed',
                'changed_files': changed_files,
                'analysis': analysis,
                'needs_harmonization': analysis['impact_level'] in ['high', 'critical']
            }

            # Record to memory
            duration = time.time() - start_time
            file_paths_str = ', '.join(file_paths) if file_paths else 'all files'
            self.memory.record_execution(
                request=f"Analyze git diff: {file_paths_str}",
                result=result,
                duration=duration,
                cost=0.0
            )

            # Update state
            self.memory.update_state({
                'last_diff_timestamp': datetime.now().isoformat(),
                'last_diff_files_count': len(changed_files),
                'last_diff_impact': analysis['impact_level']
            })

            # Detect patterns in diff analysis
            if file_paths:
                self.memory.add_pattern(
                    'specific_file_diff',
                    {
                        'file_paths': file_paths,
                        'impact': analysis['impact_level'],
                        'files_changed': len(changed_files)
                    }
                )

            return result

        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            result = {
                'status': 'error',
                'message': f'Git diff failed: {e}',
                'error': str(e)
            }

            # Record failure to memory
            self.memory.record_execution(
                request="Analyze git diff",
                result=result,
                duration=duration,
                cost=0.0
            )

            return result

    def _parse_git_status(self, status_output: str) -> List[Dict[str, Any]]:
        """Parse la sortie de git status --porcelain"""
        changed_files = []

        for line in status_output.strip().split('\n'):
            if not line:
                continue

            status_code = line[:2]
            file_path = line[3:]

            # Mapper les codes de statut
            change_type = 'modify'
            if 'A' in status_code:
                change_type = 'create'
            elif 'D' in status_code:
                change_type = 'delete'
            elif 'R' in status_code:
                change_type = 'rename'
            elif 'M' in status_code:
                change_type = 'modify'
            elif '?' in status_code:
                change_type = 'untracked'

            changed_files.append({
                'path': file_path,
                'change_type': change_type,
                'status_code': status_code.strip()
            })

        return changed_files

    def _parse_git_diff_tree(self, diff_output: str) -> List[Dict[str, Any]]:
        """Parse la sortie de git diff-tree"""
        changed_files = []

        for line in diff_output.strip().split('\n'):
            if not line:
                continue

            parts = line.split('\t')
            if len(parts) >= 2:
                status_code = parts[0]
                file_path = parts[1]

                change_type = 'modify'
                if status_code == 'A':
                    change_type = 'create'
                elif status_code == 'D':
                    change_type = 'delete'
                elif status_code == 'M':
                    change_type = 'modify'
                elif status_code.startswith('R'):
                    change_type = 'rename'

                changed_files.append({
                    'path': file_path,
                    'change_type': change_type,
                    'status_code': status_code
                })

        return changed_files

    def _analyze_changed_files(self, changed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyse l'impact des fichiers modifiés
        Détermine le niveau d'impact et les zones affectées
        """
        if not changed_files:
            return {
                'impact_level': 'none',
                'affected_areas': [],
                'file_types': {},
                'critical_files': []
            }

        # Catégoriser les fichiers
        file_types = {}
        affected_areas = set()
        critical_files = []

        for file_info in changed_files:
            path = file_info['path']

            # Type de fichier
            ext = os.path.splitext(path)[1]
            file_types[ext] = file_types.get(ext, 0) + 1

            # Zone affectée (première partie du chemin)
            if '/' in path:
                area = path.split('/')[0]
                affected_areas.add(area)

            # Fichiers critiques
            critical_patterns = [
                'database/schema.sql',
                'core/agent_hierarchy.py',
                'database/database_manager.py',
                'config/config.yaml',
                'requirements.txt',
                'setup.py'
            ]
            if any(pattern in path for pattern in critical_patterns):
                critical_files.append(path)

        # Déterminer le niveau d'impact
        impact_level = 'low'

        if critical_files:
            impact_level = 'critical'
        elif len(changed_files) > 10:
            impact_level = 'high'
        elif '.py' in file_types and file_types['.py'] > 3:
            impact_level = 'medium'
        elif 'cortex' in affected_areas or 'core' in affected_areas:
            impact_level = 'medium'

        return {
            'impact_level': impact_level,
            'affected_areas': list(affected_areas),
            'file_types': file_types,
            'critical_files': critical_files,
            'total_files': len(changed_files),
            'change_types': {
                info['change_type']: sum(1 for f in changed_files if f['change_type'] == info['change_type'])
                for info in changed_files
            }
        }

    def get_detailed_diff(self, file_path: str) -> Optional[str]:
        """Récupère le diff détaillé d'un fichier"""
        try:
            result = subprocess.run(
                ['git', 'diff', file_path],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return None


# Factory function
def create_git_watcher_agent(llm_client: LLMClient) -> GitWatcherAgent:
    """Crée une instance du Git Watcher Agent"""
    return GitWatcherAgent(llm_client)
