"""
Context Agent - Employé spécialisé dans la gestion du contexte applicatif

Responsabilités:
- Fusionner git diff avec contexte optimisé
- Décider si contexte nécessaire (économie tokens)
- Rechercher dans le cache par embedding
- Optimiser le contexte selon le tier du modèle
"""

from typing import Dict, Any, Optional
from cortex.core.llm_client import LLMClient
from cortex.core.context_manager import ContextManager, create_context_manager
from cortex.core.model_router import ModelTier


class ContextAgent:
    """Agent spécialisé dans la gestion intelligente du contexte"""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Context Agent

        Args:
            llm_client: Client LLM pour les opérations
        """
        self.llm_client = llm_client
        self.context_manager = create_context_manager(llm_client)

    def prepare_context_for_request(
        self,
        user_request: str,
        target_tier: ModelTier,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Prépare le contexte optimisé pour une requête

        Args:
            user_request: Requête utilisateur
            target_tier: Tier du modèle cible (pour optimiser la taille)
            max_tokens: Budget de tokens maximum

        Returns:
            Dict avec contexte et métadonnées
        """
        # Adapter le budget selon le tier
        tier_budgets = {
            ModelTier.NANO: 1000,      # Limité pour nano
            ModelTier.DEEPSEEK: 2000,  # Moyen pour deepseek
            ModelTier.CLAUDE: 4000     # Généreux pour claude
        }

        adjusted_budget = min(max_tokens, tier_budgets.get(target_tier, 2000))

        # Construire le contexte optimisé
        result = self.context_manager.build_optimized_context(
            user_request=user_request,
            include_git_diff=True,
            max_tokens=adjusted_budget
        )

        # Ajouter des informations sur l'optimisation
        result['tier'] = target_tier.value
        result['budget'] = adjusted_budget

        return result

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Obtient des statistiques sur le cache de contexte"""
        cache = self.context_manager.context_cache

        if not cache:
            return {
                'total_contexts': 0,
                'total_usage': 0,
                'most_used': None
            }

        total_usage = sum(ctx.usage_count for ctx in cache)
        most_used = max(cache, key=lambda x: x.usage_count) if cache else None

        return {
            'total_contexts': len(cache),
            'total_usage': total_usage,
            'most_used': {
                'id': most_used.id,
                'usage_count': most_used.usage_count,
                'metadata': most_used.metadata
            } if most_used else None
        }

    def search_similar_contexts(
        self,
        query: str,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Recherche des contextes similaires dans le cache

        Args:
            query: Requête de recherche
            top_k: Nombre de résultats

        Returns:
            Dict avec résultats de recherche
        """
        results = self.context_manager.search_cache_by_embedding(query, top_k=top_k)

        return {
            'query': query,
            'results_count': len(results),
            'results': [
                {
                    'id': ctx.id,
                    'similarity': sim,
                    'content_preview': ctx.content[:200],
                    'metadata': ctx.metadata,
                    'usage_count': ctx.usage_count
                }
                for ctx, sim in results
            ]
        }


def create_context_agent(llm_client: LLMClient) -> ContextAgent:
    """Factory function pour créer un ContextAgent"""
    return ContextAgent(llm_client)


# Test si exécuté directement
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    print("Testing Context Agent...")

    client = LLMClient()
    agent = ContextAgent(client)

    # Test 1: Préparer contexte
    print("\n1. Testing context preparation for different tiers...")

    for tier in [ModelTier.NANO, ModelTier.DEEPSEEK, ModelTier.CLAUDE]:
        result = agent.prepare_context_for_request(
            user_request="Fix authentication bug in login.py",
            target_tier=tier
        )
        print(f"  {tier.value}:")
        print(f"    Budget: {result['budget']} tokens")
        print(f"    Context needed: {result['metadata']['context_needed']['needed']}")

    # Test 2: Statistiques du cache
    print("\n2. Testing cache statistics...")
    stats = agent.get_cache_statistics()
    print(f"  Total contexts: {stats['total_contexts']}")
    print(f"  Total usage: {stats['total_usage']}")

    # Test 3: Recherche de contextes similaires
    print("\n3. Testing similar context search...")
    search_result = agent.search_similar_contexts("authentication problem", top_k=3)
    print(f"  Query: {search_result['query']}")
    print(f"  Results: {search_result['results_count']}")

    print("\n✓ Context Agent works correctly!")
