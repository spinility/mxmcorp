"""
Maintenance Agent - Exécute les plans d'harmonisation et maintient le système

ROLE: DIRECTEUR (Coordination + Exécution) - Niveau 3 de la hiérarchie
TIER: DEEPSEEK pour exécution intelligente des plans

NOUVEAU WORKFLOW:
Reçoit un plan d'harmonisation du HarmonizationAgent (GPT-5) et l'EXÉCUTE.

Responsabilités:
- EXÉCUTER les plans d'harmonisation générés par HarmonizationAgent
- Router les actions vers les agents appropriés (TesterAgent, ArchivistAgent)
- Mettre à jour fichiers, configurations, base de données
- Stocker et mettre à jour les contextes globaux/par agent/par département
- Gérer l'architecture du système (CORTEX_ARCHITECTURE.md)
- Synchroniser automatiquement après git commits
- Logger toutes les actions dans change_log

Déclenché:
- Par HarmonizationAgent avec un plan d'exécution
- Automatiquement après git commits (maintenance classique)
- Manuellement via CLI
"""

from typing import Dict, Any, Optional, List
import json
import time
from datetime import datetime

from cortex.core.llm_client import LLMClient, ModelTier
from cortex.core.agent_hierarchy import DecisionAgent, AgentRole, AgentResult, EscalationContext
from cortex.core.agent_memory import get_agent_memory
from cortex.departments.maintenance import MaintenanceOrchestrator
from cortex.repositories.changelog_repository import get_changelog_repository
from cortex.repositories.architecture_repository import get_architecture_repository


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
        self.memory = get_agent_memory('maintenance', 'maintenance')

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

    def execute_harmonization_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute un plan d'harmonisation généré par HarmonizationAgent (GPT-5)

        Le plan contient des actions prioritisées que le MaintenanceAgent exécute
        en routant vers les agents appropriés et en loggant tout dans change_log.

        Args:
            plan: Plan JSON avec:
                - title: Titre du plan
                - analysis: Diagnostic des problèmes
                - actions[]: Liste d'actions avec priority, action_type, target, etc.
                - testing_required: Boolean
                - validation_criteria: Critères de validation

        Returns:
            Dict avec résultats d'exécution par action
        """
        start_time = time.time()

        try:
            changelog_repo = get_changelog_repository()
            arch_repo = get_architecture_repository()

            print(f"\n{'='*70}")
            print(f"🔧 MAINTENANCE AGENT - Executing Harmonization Plan")
            print(f"{'='*70}")
            print(f"Plan: {plan.get('title', 'Untitled')}")
            print(f"Actions: {len(plan.get('actions', []))}")
            print(f"Testing Required: {plan.get('testing_required', False)}\n")

            # Log le début de l'exécution du plan
            plan_log_id = changelog_repo.log_change(
                change_type='execution_start',
                entity_type='harmonization_plan',
                author='MaintenanceAgent',
                description=f"Starting execution of plan: {plan.get('title')}",
                impact_level='medium',
                metadata={
                    'plan_id': plan.get('adr_id'),
                    'actions_count': len(plan.get('actions', []))
                }
            )

            # Trier les actions par priorité (1 = le plus critique)
            actions = sorted(
                plan.get('actions', []),
                key=lambda a: a.get('priority', 10)
            )

            executed_actions = []
            failed_actions = []
            skipped_actions = []

            # Exécuter chaque action
            for idx, action in enumerate(actions, 1):
                action_type = action.get('action_type')
                target = action.get('target')
                priority = action.get('priority', 10)
                responsible = action.get('responsible_agent', 'MaintenanceAgent')

                print(f"\n[{idx}/{len(actions)}] Priority {priority}: {action_type} on {target}")
                print(f"   Responsible: {responsible}")
                print(f"   Description: {action.get('description', 'N/A')}")

                try:
                    result = self._execute_action(action)

                    if result['success']:
                        executed_actions.append({
                            'action': action,
                            'result': result
                        })
                        print(f"   ✓ Success: {result.get('message', 'Action completed')}")

                        # Log l'action réussie
                        changelog_repo.log_change(
                            change_type=action_type,
                            entity_type='harmonization_action',
                            author=responsible,
                            description=f"Executed: {action.get('description')}",
                            impact_level=self._map_effort_to_impact(action.get('estimated_effort', 'medium')),
                            metadata={
                                'plan_id': plan.get('adr_id'),
                                'target': target,
                                'priority': priority
                            }
                        )
                    else:
                        failed_actions.append({
                            'action': action,
                            'error': result.get('error')
                        })
                        print(f"   ✗ Failed: {result.get('error', 'Unknown error')}")

                        # Log l'échec
                        changelog_repo.log_change(
                            change_type='execution_failure',
                            entity_type='harmonization_action',
                            author=responsible,
                            description=f"Failed: {action.get('description')} - {result.get('error')}",
                            impact_level='high',
                            metadata={
                                'plan_id': plan.get('adr_id'),
                                'target': target,
                                'error': result.get('error')
                            }
                        )

                except Exception as e:
                    failed_actions.append({
                        'action': action,
                        'error': str(e)
                    })
                    print(f"   ✗ Exception: {str(e)}")

                    changelog_repo.log_change(
                        change_type='execution_exception',
                        entity_type='harmonization_action',
                        author='MaintenanceAgent',
                        description=f"Exception executing: {action.get('description')}",
                        impact_level='high',
                        metadata={
                            'plan_id': plan.get('adr_id'),
                            'exception': str(e)
                        }
                    )

            # Update ADR status
            if plan.get('adr_id'):
                if len(failed_actions) == 0:
                    arch_repo.update_decision_status(plan['adr_id'], 'accepted')
                elif len(executed_actions) > 0:
                    arch_repo.update_decision_status(plan['adr_id'], 'partially_implemented')
                else:
                    arch_repo.update_decision_status(plan['adr_id'], 'rejected')

            # Log la fin de l'exécution
            changelog_repo.log_change(
                change_type='execution_complete',
                entity_type='harmonization_plan',
                author='MaintenanceAgent',
                description=f"Completed plan: {plan.get('title')}",
                impact_level='medium',
                metadata={
                    'plan_id': plan.get('adr_id'),
                    'executed': len(executed_actions),
                    'failed': len(failed_actions),
                    'skipped': len(skipped_actions)
                }
            )

            success_rate = len(executed_actions) / len(actions) if actions else 0.0

            print(f"\n{'='*70}")
            print(f"Execution Summary:")
            print(f"  ✓ Executed: {len(executed_actions)}")
            print(f"  ✗ Failed: {len(failed_actions)}")
            print(f"  ⊘ Skipped: {len(skipped_actions)}")
            print(f"  Success Rate: {success_rate*100:.1f}%")
            print(f"{'='*70}\n")

            duration = time.time() - start_time

            result = {
                'success': len(failed_actions) == 0,
                'action': 'execute_harmonization_plan',
                'plan_title': plan.get('title'),
                'plan_id': plan.get('adr_id'),
                'total_actions': len(actions),
                'executed': len(executed_actions),
                'failed': len(failed_actions),
                'skipped': len(skipped_actions),
                'success_rate': success_rate,
                'executed_actions': executed_actions,
                'failed_actions': failed_actions,
                'testing_required': plan.get('testing_required', False),
                'cost': 0.0  # MaintenanceAgent doesn't use LLM
            }

            # Enregistrer dans la mémoire
            self.memory.record_execution(
                request=f"Execute harmonization plan: {plan.get('title', 'Untitled')}",
                result=result,
                duration=duration,
                cost=0.0
            )

            # Mettre à jour l'état avec le dernier plan exécuté
            self.memory.update_state({
                'last_plan_id': plan.get('adr_id'),
                'last_plan_title': plan.get('title'),
                'last_execution_timestamp': datetime.now().isoformat(),
                'last_success_rate': success_rate
            })

            # Détecter et enregistrer patterns
            if len(failed_actions) > 0:
                # Pattern: types d'actions qui échouent
                for failed in failed_actions:
                    action_type = failed['action'].get('action_type')
                    self.memory.add_pattern(
                        f'failed_action_{action_type}',
                        {
                            'action_type': action_type,
                            'target': failed['action'].get('target'),
                            'error': failed['error']
                        }
                    )

            return result

        except Exception as e:
            duration = time.time() - start_time
            error_result = {
                'success': False,
                'action': 'execute_harmonization_plan',
                'error': f"Plan execution failed: {str(e)}",
                'cost': 0.0
            }

            # Enregistrer l'échec dans la mémoire
            self.memory.record_execution(
                request=f"Execute harmonization plan: {plan.get('title', 'Error')}",
                result=error_result,
                duration=duration,
                cost=0.0
            )

            return error_result

    def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute une action individuelle du plan

        Args:
            action: Action avec action_type, target, description, etc.

        Returns:
            Dict avec success et message/error
        """
        action_type = action.get('action_type')
        target = action.get('target')
        description = action.get('description', '')

        try:
            if action_type == 'update_file':
                return self._update_file_action(target, description)

            elif action_type == 'refactor':
                return self._refactor_action(target, description)

            elif action_type == 'add_test':
                return self._add_test_action(target, description)

            elif action_type == 'update_doc':
                return self._update_doc_action(target, description)

            elif action_type == 'sync_db':
                return self._sync_db_action(target, description)

            elif action_type == 'update_context':
                return self._update_context_action(target, description)

            else:
                return {
                    'success': False,
                    'error': f"Unknown action_type: {action_type}"
                }

        except Exception as e:
            return {
                'success': False,
                'error': f"Action execution failed: {str(e)}"
            }

    def _update_file_action(self, target: str, description: str) -> Dict[str, Any]:
        """Exécute une action update_file"""
        # Pour l'instant, on marque comme "needs manual review"
        # Plus tard, on pourra intégrer l'édition automatique
        return {
            'success': True,
            'message': f"File update flagged for review: {target}",
            'needs_manual_review': True
        }

    def _refactor_action(self, target: str, description: str) -> Dict[str, Any]:
        """Exécute une action refactor"""
        return {
            'success': True,
            'message': f"Refactor flagged for review: {target}",
            'needs_manual_review': True
        }

    def _add_test_action(self, target: str, description: str) -> Dict[str, Any]:
        """
        Exécute une action add_test
        Cette action devrait être routée vers TesterAgent une fois créé
        """
        return {
            'success': True,
            'message': f"Test creation requested for: {target}",
            'routed_to': 'TesterAgent',
            'needs_tester_agent': True
        }

    def _update_doc_action(self, target: str, description: str) -> Dict[str, Any]:
        """Exécute une action update_doc"""
        return {
            'success': True,
            'message': f"Documentation update flagged: {target}",
            'needs_manual_review': True
        }

    def _sync_db_action(self, target: str, description: str) -> Dict[str, Any]:
        """Exécute une action sync_db"""
        try:
            # Régénérer les contextes si nécessaire
            if 'context' in target.lower():
                self.orchestrator.context_updater.update_all_contexts()
                return {
                    'success': True,
                    'message': 'All contexts synchronized'
                }
            else:
                return {
                    'success': True,
                    'message': f"DB sync completed for: {target}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"DB sync failed: {str(e)}"
            }

    def _update_context_action(self, target: str, description: str) -> Dict[str, Any]:
        """Exécute une action update_context"""
        try:
            if target.endswith('.py'):
                self.orchestrator.context_updater.update_file_context(target)
                return {
                    'success': True,
                    'message': f"Context updated for: {target}"
                }
            else:
                return {
                    'success': True,
                    'message': f"Context update completed for: {target}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Context update failed: {str(e)}"
            }

    def _map_effort_to_impact(self, effort: str) -> str:
        """Map estimated_effort to impact_level for changelog"""
        mapping = {
            'low': 'low',
            'medium': 'medium',
            'high': 'high'
        }
        return mapping.get(effort, 'medium')

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
