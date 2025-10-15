"""
Tooler Agent - Responsable de la recherche et recommandation d'outils

Le Tooler est appelé automatiquement quand Cortex identifie qu'il ne peut pas
accomplir une tâche avec les outils actuels. Il:

1. Recherche sur internet si des outils/packages existent
2. Consulte des LLMs pour des recommandations
3. Demande aux Communications de formuler des recommandations pour l'utilisateur
"""

from typing import Dict, Any, List, Optional
from cortex.core.llm_client import LLMClient, ModelTier


class ToolerAgent:
    """Agent responsable de trouver et recommander des outils manquants"""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Tooler Agent

        Args:
            llm_client: LLM client for research and analysis
        """
        self.llm_client = llm_client

    def research_missing_capability(
        self,
        capability_description: str,
        user_request: str,
        available_tools: List[str]
    ) -> Dict[str, Any]:
        """
        Recherche des solutions pour une capacité manquante

        Args:
            capability_description: Description de la capacité manquante
            user_request: Requête originale de l'utilisateur
            available_tools: Liste des outils déjà disponibles

        Returns:
            Dict avec recommandations et options
        """
        # Prompt pour rechercher des solutions
        research_prompt = f"""Tu es un expert en recherche d'outils et de solutions techniques.

SITUATION:
L'utilisateur a demandé: "{user_request}"
Capacité manquante: {capability_description}

Outils actuellement disponibles:
{chr(10).join([f"- {tool}" for tool in available_tools])}

TA MISSION:
1. Identifier des solutions existantes (packages Python, APIs, outils CLI, etc.)
2. Évaluer leur faisabilité d'intégration
3. Recommander la meilleure approche

ANALYSE:
- Existe-t-il des packages Python qui font ça? (ex: GitPython pour git)
- Y a-t-il des APIs REST disponibles?
- Peut-on utiliser des outils CLI via subprocess?
- Quelle est la complexité d'implémentation?

FORMAT DE RÉPONSE:
1. **Solutions trouvées:** [Liste 2-3 solutions avec noms]
2. **Recommandation principale:** [Solution recommandée]
3. **Complexité:** [FACILE/MOYENNE/DIFFICILE]
4. **Justification:** [Pourquoi cette solution]

Sois concis mais précis."""

        messages = [
            {"role": "system", "content": research_prompt},
            {"role": "user", "content": f"Recherche pour: {capability_description}"}
        ]

        # Utiliser DeepSeek pour la recherche (bon rapport qualité/prix)
        # max_tokens=1500 pour éviter troncature sur recherches complexes
        response = self.llm_client.complete(
            messages=messages,
            tier=ModelTier.DEEPSEEK,
            max_tokens=1500,
            temperature=0.7
        )

        return {
            "research_complete": True,
            "capability": capability_description,
            "user_request": user_request,
            "recommendations": response.content,
            "model_used": response.model,
            "cost": response.cost
        }

    def create_communication_request(
        self,
        research_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crée une requête pour l'agent Communications

        Args:
            research_results: Résultats de la recherche du Tooler

        Returns:
            Requête formatée pour Communications
        """
        return {
            "type": "tool_recommendation",
            "user_request": research_results["user_request"],
            "capability_needed": research_results["capability"],
            "research_findings": research_results["recommendations"],
            "urgency": "medium",
            "tone": "helpful_and_technical"
        }


def create_tooler_agent(llm_client: LLMClient) -> ToolerAgent:
    """Factory function to create a Tooler Agent"""
    return ToolerAgent(llm_client)
