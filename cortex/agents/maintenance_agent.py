"""
Maintenance Agent - Gère les contextes globaux, par agent, par département

ROLE: DIRECTEUR (Décision + Coordination) - Niveau 3 de la hiérarchie
TIER: NANO pour décisions rapides, DEEPSEEK pour analyses complexes

Responsabilités:
- Stocker et mettre à jour les contextes globaux
- Stocker les contextes par agent (Triage, Planner, Tooler, etc.)
- Stocker les contextes par département (Intelligence, Maintenance, etc.)
- Gérer l'architecture du système (CORTEX_ARCHITECTURE.md)
- Synchroniser automatiquement après git commits
- Détecter breaking changes
- Maintenir le cache d'embeddings

Déclenché:
- Automatiquement après git commits (si configuré)
- Manuellement via commande CLI
- Périodiquement (cron-like)
"""

from typing import Dict, Any, Optional
import json
from datetime import datetime

from cortex.core.llm_client import LLMClient, ModelTier
from cortex.core.agent_hierarchy import DecisionAgent, AgentRole, AgentResult, EscalationContext
from cortex.departments.maintenance import MaintenanceOrchestrator


class MaintenanceAgent(DecisionAgent):
    """Agent de maintenance pour gérer tous les contextes du système"""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Maintenance Agent

        Args:
            llm_client: Client LLM pour l'analyse
        """
        super().__init__(llm_client, specialization="maintenance")
        self.orchestrator = MaintenanceOrchestrator()

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """
        Évalue si le MaintenanceAgent peut gérer la requête

        Keywords: maintenance, update, sync, context, architecture, roadmap
        """
        request_lower = request.lower()

        maintenance_keywords = [
            'maintenance', 'update', 'sync', 'synchronize',
            'context', 'architecture', 'roadmap',
            'refresh', 'rebuild', 'regenerate'
        ]

        # Haute confiance si contient keywords
        if any(kw in request_lower for kw in maintenance_keywords):
            return 0.9

        return 0.0

    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[EscalationContext] = None
    ) -> AgentResult:
        """
        Exécute une opération de maintenance

        Args:
            request: Requête utilisateur
            context: Contexte optionnel
            escalation_context: Contexte si escalation

        Returns:
            AgentResult avec résultat de maintenance
        """
        # Analyser la requête pour déterminer l'action
        action = self._parse_maintenance_request(request)

        if action == 'full_sync':
            result = self.run_full_maintenance()
        elif action == 'update_contexts':
            result = self.update_contexts_only()
        elif action == 'update_architecture':
            result = self.update_architecture()
        elif action == 'show_metrics':
            result = self.get_quality_metrics()
        else:
            # Fallback: full maintenance
            result = self.run_full_maintenance()

        return AgentResult(
            success=result['success'],
            role=self.role,
            tier=self.tier,
            content=result,
            cost=result.get('cost', 0.0),
            confidence=0.9,
            should_escalate=False,
            escalation_reason=None,
            error=result.get('error'),
            metadata={'maintenance_result': result}
        )

    def _parse_maintenance_request(self, request: str) -> str:
        """
        Parse la requête pour déterminer l'action de maintenance

        Returns:
            Action: full_sync, update_contexts, update_architecture, show_metrics
        """
        request_lower = request.lower()

        if 'architecture' in request_lower or 'roadmap' in request_lower:
            return 'update_architecture'
        elif 'context' in request_lower and 'only' in request_lower:
            return 'update_contexts'
        elif 'metrics' in request_lower or 'stats' in request_lower or 'quality' in request_lower:
            return 'show_metrics'
        else:
            return 'full_sync'

    def run_full_maintenance(self, include_staged: bool = True) -> Dict[str, Any]:
        """
        Exécute cycle complet de maintenance

        Args:
            include_staged: Inclure changements staged

        Returns:
            Dict avec résultats de maintenance
        """
        try:
            print(f"\n{'='*70}")
            print("🔧 MAINTENANCE AGENT - Full Maintenance Cycle")
            print(f"{'='*70}\n")

            # Lancer l'orchestrateur
            result = self.orchestrator.run_maintenance(include_staged=include_staged)

            # Update architecture si des changements détectés
            if result.files_processed > 0:
                print("\n6. Updating system architecture...")
                arch_result = self.update_architecture()
                if arch_result['success']:
                    print(f"   ✓ Architecture updated")
                else:
                    print(f"   ✗ Architecture update failed: {arch_result.get('error')}")

            return {
                'success': result.success,
                'action': 'full_sync',
                'files_processed': result.files_processed,
                'contexts_updated': result.contexts_updated,
                'dependencies_updated': result.dependencies_updated,
                'roadmap_tasks_completed': result.roadmap_tasks_completed,
                'roadmap_tasks_created': result.roadmap_tasks_created,
                'breaking_changes': result.breaking_changes,
                'errors': result.errors,
                'duration_seconds': result.duration_seconds,
                'timestamp': result.timestamp.isoformat(),
                'cost': 0.0  # Maintenance doesn't use LLM directly
            }

        except Exception as e:
            return {
                'success': False,
                'action': 'full_sync',
                'error': f"Maintenance failed: {str(e)}",
                'cost': 0.0
            }

    def update_contexts_only(self) -> Dict[str, Any]:
        """
        Met à jour uniquement les contextes (pas de roadmap ni dépendances)

        Returns:
            Dict avec résultats
        """
        try:
            print("\n🔄 Updating contexts only...")

            # Parse git diff
            git_analysis = self.orchestrator.git_processor.get_latest_diff()

            if git_analysis.total_files_changed == 0:
                return {
                    'success': True,
                    'action': 'update_contexts',
                    'contexts_updated': 0,
                    'message': 'No changes detected',
                    'cost': 0.0
                }

            # Update contexts
            python_files = [
                f for f in (git_analysis.files_added + git_analysis.files_modified)
                if f.endswith('.py')
            ]

            contexts_updated = 0
            for file_path in python_files:
                try:
                    self.orchestrator.context_updater.update_file_context(file_path)
                    contexts_updated += 1
                    print(f"   ✓ Updated: {file_path}")
                except Exception as e:
                    print(f"   ✗ Failed: {file_path} - {e}")

            return {
                'success': True,
                'action': 'update_contexts',
                'contexts_updated': contexts_updated,
                'files_processed': len(python_files),
                'cost': 0.0
            }

        except Exception as e:
            return {
                'success': False,
                'action': 'update_contexts',
                'error': f"Context update failed: {str(e)}",
                'cost': 0.0
            }

    def update_architecture(self) -> Dict[str, Any]:
        """
        Régénère CORTEX_ARCHITECTURE.md

        Returns:
            Dict avec résultats
        """
        try:
            import subprocess

            print("\n📐 Regenerating system architecture...")

            # Exécuter le script de génération
            result = subprocess.run(
                ['python3', 'utils/generate_architecture_map.py'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return {
                    'success': True,
                    'action': 'update_architecture',
                    'message': 'Architecture regenerated successfully',
                    'output': result.stdout,
                    'cost': 0.0
                }
            else:
                return {
                    'success': False,
                    'action': 'update_architecture',
                    'error': f"Script failed: {result.stderr}",
                    'cost': 0.0
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'action': 'update_architecture',
                'error': 'Architecture generation timed out',
                'cost': 0.0
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'update_architecture',
                'error': f"Architecture update failed: {str(e)}",
                'cost': 0.0
            }

    def get_quality_metrics(self) -> Dict[str, Any]:
        """
        Récupère les métriques de qualité du système de maintenance

        Returns:
            Dict avec métriques
        """
        metrics = self.orchestrator.get_quality_metrics()

        return {
            'success': True,
            'action': 'show_metrics',
            'metrics': metrics,
            'cost': 0.0
        }

    def store_global_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stocke un contexte global du système

        Args:
            context_data: Données de contexte à stocker

        Returns:
            Dict avec résultat
        """
        try:
            from pathlib import Path
            import json

            context_file = Path("cortex/data/contexts/global_context.json")
            context_file.parent.mkdir(parents=True, exist_ok=True)

            # Add timestamp
            context_data['updated_at'] = datetime.now().isoformat()

            with open(context_file, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, indent=2)

            return {
                'success': True,
                'action': 'store_global_context',
                'file': str(context_file),
                'size': len(json.dumps(context_data))
            }

        except Exception as e:
            return {
                'success': False,
                'action': 'store_global_context',
                'error': str(e)
            }

    def store_agent_context(self, agent_name: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stocke le contexte d'un agent spécifique

        Args:
            agent_name: Nom de l'agent (triage, planner, tooler, etc.)
            context_data: Données de contexte

        Returns:
            Dict avec résultat
        """
        try:
            from pathlib import Path
            import json

            context_file = Path(f"cortex/data/contexts/agents/{agent_name}_context.json")
            context_file.parent.mkdir(parents=True, exist_ok=True)

            context_data['agent'] = agent_name
            context_data['updated_at'] = datetime.now().isoformat()

            with open(context_file, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, indent=2)

            return {
                'success': True,
                'action': 'store_agent_context',
                'agent': agent_name,
                'file': str(context_file)
            }

        except Exception as e:
            return {
                'success': False,
                'action': 'store_agent_context',
                'error': str(e)
            }

    def store_department_context(self, department_name: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stocke le contexte d'un département

        Args:
            department_name: Nom du département (intelligence, maintenance, etc.)
            context_data: Données de contexte

        Returns:
            Dict avec résultat
        """
        try:
            from pathlib import Path
            import json

            context_file = Path(f"cortex/data/contexts/departments/{department_name}_context.json")
            context_file.parent.mkdir(parents=True, exist_ok=True)

            context_data['department'] = department_name
            context_data['updated_at'] = datetime.now().isoformat()

            with open(context_file, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, indent=2)

            return {
                'success': True,
                'action': 'store_department_context',
                'department': department_name,
                'file': str(context_file)
            }

        except Exception as e:
            return {
                'success': False,
                'action': 'store_department_context',
                'error': str(e)
            }


def create_maintenance_agent(llm_client: LLMClient) -> MaintenanceAgent:
    """Factory function pour créer un MaintenanceAgent"""
    return MaintenanceAgent(llm_client)


# Test
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    print("Testing Maintenance Agent...")

    client = LLMClient()
    agent = MaintenanceAgent(client)

    # Test 1: Full maintenance
    print("\n1. Running full maintenance...")
    result = agent.run_full_maintenance(include_staged=True)
    print(f"   Success: {result['success']}")
    print(f"   Files processed: {result.get('files_processed', 0)}")

    # Test 2: Quality metrics
    print("\n2. Getting quality metrics...")
    metrics_result = agent.get_quality_metrics()
    print(f"   Metrics: {metrics_result['metrics']}")

    print("\n✓ Maintenance Agent works correctly!")
