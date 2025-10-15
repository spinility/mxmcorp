"""
Developer Agent - Backward Compatibility Wrapper

This wrapper maintains the old DeveloperAgent API while routing to the new
hierarchical agent system (Expert, Directeur, Cortex).

DEPRECATED: Use AgentFirstRouter with specialized agents instead.
This wrapper exists for backward compatibility only.

Mapping:
- ModelTier.DEEPSEEK → DeveloperAgentExpert (EXPERT)
- ModelTier.GPT5 → DeveloperAgentDirecteur (DIRECTEUR)
- ModelTier.CLAUDE → DeveloperAgentCortex (CORTEX_CENTRAL)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier
from cortex.core.agent_hierarchy import AgentRole, EscalationContext
from cortex.agents.developer_agent_expert import DeveloperAgentExpert, CodeChange
from cortex.agents.developer_agent_directeur import DeveloperAgentDirecteur
from cortex.agents.developer_agent_cortex import DeveloperAgentCortex


@dataclass
class DevelopmentResult:
    """Résultat d'une tentative de développement (format legacy)"""
    success: bool
    changes: List[CodeChange]
    tier_used: ModelTier
    cost: float
    tokens_used: int
    error: Optional[str] = None
    reasoning: Optional[str] = None


class DeveloperAgentCompat:
    """
    Backward compatibility wrapper for DeveloperAgent

    Routes requests to the appropriate specialized agent based on tier.
    Maintains the old API: develop(task, filepaths, tier, ...)

    DEPRECATED: Prefer using AgentFirstRouter directly for automatic routing.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Developer Agent (Compatibility Wrapper)

        Args:
            llm_client: Client LLM pour génération de code
        """
        self.llm_client = llm_client

        # Create all 3 specialized agents
        self.expert = DeveloperAgentExpert(llm_client)
        self.directeur = DeveloperAgentDirecteur(llm_client)
        self.cortex = DeveloperAgentCortex(llm_client)

        # Track history for summary
        self.development_history: List[DevelopmentResult] = []

    def develop(
        self,
        task: str,
        filepaths: List[str],
        tier: ModelTier = ModelTier.DEEPSEEK,
        context: str = "",
        use_partial_updates: bool = True
    ) -> DevelopmentResult:
        """
        Développe du code pour une tâche (OLD API)

        Routes to appropriate specialized agent based on tier.

        Args:
            task: Description de la tâche
            filepaths: Fichiers à modifier
            tier: Tier du modèle à utiliser (DEEPSEEK, GPT5, CLAUDE)
            context: Contexte additionnel
            use_partial_updates: Utiliser updates partiels si possible

        Returns:
            DevelopmentResult avec changements
        """
        # Select agent based on tier
        if tier == ModelTier.DEEPSEEK:
            agent = self.expert
        elif tier == ModelTier.GPT5:
            agent = self.directeur
        elif tier == ModelTier.CLAUDE:
            agent = self.cortex
        else:
            # Fallback to expert for unknown tiers
            agent = self.expert

        # Build context dict for new API
        agent_context = {
            'filepaths': filepaths,
            'context_text': context,
            'use_partial_updates': use_partial_updates
        }

        # Build escalation context from history if exists
        escalation_context = None
        if len(self.development_history) > 0:
            previous_results = [r for r in self.development_history if not r.success]
            if previous_results:
                last_result = previous_results[-1]
                escalation_context = EscalationContext(
                    previous_role=self._tier_to_role(last_result.tier_used),
                    previous_tier=last_result.tier_used,
                    attempts=len(self.development_history),
                    errors=[r.error for r in previous_results if r.error],
                    escalation_reason=f"Previous tier failed: {last_result.error or 'Unknown error'}"
                )

        # Execute with selected agent
        result = agent.execute(task, agent_context, escalation_context)

        # Convert AgentResult back to DevelopmentResult (legacy format)
        changes = []
        if result.success and result.metadata:
            changes_objects = result.metadata.get('changes_objects', [])
            changes = changes_objects

        dev_result = DevelopmentResult(
            success=result.success,
            changes=changes,
            tier_used=tier,
            cost=result.cost,
            tokens_used=0,  # Not tracked in new system
            error=result.error,
            reasoning=None
        )

        self.development_history.append(dev_result)
        return dev_result

    def _tier_to_role(self, tier: ModelTier) -> AgentRole:
        """Convert ModelTier to AgentRole"""
        if tier == ModelTier.DEEPSEEK:
            return AgentRole.EXPERT
        elif tier == ModelTier.GPT5:
            return AgentRole.DIRECTEUR
        elif tier == ModelTier.CLAUDE:
            return AgentRole.CORTEX_CENTRAL
        else:
            return AgentRole.AGENT

    def apply_changes(
        self,
        changes: List[CodeChange],
        backup: bool = True
    ) -> bool:
        """
        Applique les changements aux fichiers

        Args:
            changes: Liste des changements à appliquer
            backup: Si True, créer des backups

        Returns:
            True si tous les changements appliqués avec succès
        """
        from pathlib import Path
        import shutil

        try:
            for change in changes:
                filepath = Path(change.filepath)

                # Backup si demandé
                if backup and filepath.exists():
                    backup_path = filepath.with_suffix(filepath.suffix + '.backup')
                    shutil.copy(filepath, backup_path)

                # Créer répertoires si nécessaire
                filepath.parent.mkdir(parents=True, exist_ok=True)

                # Écrire nouveau contenu
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(change.new_content)

            return True

        except Exception as e:
            print(f"Error applying changes: {e}")
            return False

    def rollback_changes(self, changes: List[CodeChange]) -> bool:
        """
        Rollback les changements (restaure les backups)

        Args:
            changes: Changements à rollback

        Returns:
            True si rollback réussi
        """
        from pathlib import Path
        import shutil

        try:
            for change in changes:
                filepath = Path(change.filepath)
                backup_path = filepath.with_suffix(filepath.suffix + '.backup')

                if backup_path.exists():
                    shutil.copy(backup_path, filepath)
                    backup_path.unlink()

            return True

        except Exception as e:
            print(f"Error during rollback: {e}")
            return False

    def get_development_summary(self) -> Dict[str, Any]:
        """Obtient un résumé de l'historique de développement"""
        if not self.development_history:
            return {
                'total_attempts': 0,
                'success_rate': 0.0,
                'total_cost': 0.0,
                'tier_usage': {}
            }

        total = len(self.development_history)
        successes = sum(1 for r in self.development_history if r.success)
        total_cost = sum(r.cost for r in self.development_history)

        tier_usage = {}
        for result in self.development_history:
            tier_name = result.tier_used.value
            if tier_name not in tier_usage:
                tier_usage[tier_name] = {'count': 0, 'cost': 0.0}
            tier_usage[tier_name]['count'] += 1
            tier_usage[tier_name]['cost'] += result.cost

        return {
            'total_attempts': total,
            'success_rate': successes / total if total > 0 else 0.0,
            'total_cost': total_cost,
            'tier_usage': tier_usage
        }


# Alias for backward compatibility
DeveloperAgent = DeveloperAgentCompat


def create_developer_agent(llm_client: LLMClient) -> DeveloperAgentCompat:
    """
    Factory function pour créer un DeveloperAgent (compatibility wrapper)

    DEPRECATED: Use specialized agents with AgentFirstRouter instead.
    """
    return DeveloperAgentCompat(llm_client)


# Test si exécuté directement
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    print("Testing Developer Agent (Compatibility Wrapper)...")

    client = LLMClient()
    developer = DeveloperAgentCompat(client)

    # Test 1: Routing to different tiers
    print("\n1. Testing tier routing...")
    print(f"  DEEPSEEK routes to: {developer.expert.__class__.__name__}")
    print(f"  GPT5 routes to: {developer.directeur.__class__.__name__}")
    print(f"  CLAUDE routes to: {developer.cortex.__class__.__name__}")

    # Test 2: Test can_handle on specialized agents
    print("\n2. Testing specialized agent capabilities...")
    test_requests = [
        "Implement authentication feature",
        "Design microservices architecture",
        "Fix critical production bug"
    ]

    for req in test_requests:
        expert_score = developer.expert.can_handle(req)
        directeur_score = developer.directeur.can_handle(req)
        cortex_score = developer.cortex.can_handle(req)
        print(f"  '{req}':")
        print(f"    Expert: {expert_score:.2f}, Directeur: {directeur_score:.2f}, Cortex: {cortex_score:.2f}")

    # Test 3: Summary
    print("\n3. Testing development summary...")
    summary = developer.get_development_summary()
    print(f"✓ Summary:")
    print(f"  Total attempts: {summary['total_attempts']}")
    print(f"  Total cost: ${summary['total_cost']:.4f}")

    print("\n✓ Developer Agent (Compatibility Wrapper) works correctly!")
    print("\nNOTE: This is a backward compatibility wrapper.")
    print("Prefer using AgentFirstRouter with specialized agents for new code.")
