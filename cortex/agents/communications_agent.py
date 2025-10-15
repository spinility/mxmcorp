"""
Communications Agent - Responsable de la communication avec l'utilisateur

Le Communications Agent formule des recommandations claires et utiles pour
l'utilisateur basées sur les recherches du Tooler.
"""

from typing import Dict, Any
from cortex.core.llm_client import LLMClient, ModelTier


class CommunicationsAgent:
    """Agent responsable de communiquer avec l'utilisateur"""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Communications Agent

        Args:
            llm_client: LLM client for crafting responses
        """
        self.llm_client = llm_client

    def craft_recommendation(
        self,
        tooler_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crée une recommandation claire pour l'utilisateur

        Args:
            tooler_request: Requête du Tooler avec les résultats de recherche

        Returns:
            Recommandation formatée pour l'utilisateur
        """
        prompt = f"""Tu es un expert en communication technique.
Tu dois expliquer clairement à l'utilisateur ce qui peut être fait.

CONTEXTE:
Requête utilisateur: "{tooler_request['user_request']}"
Capacité manquante: {tooler_request['capability_needed']}

RECHERCHE DU TOOLER:
{tooler_request['research_findings']}

TA MISSION:
Crée un message clair pour l'utilisateur avec:
1. Ce que Cortex ne peut pas faire actuellement
2. Les solutions qui existent
3. Les prochaines étapes recommandées

TON: {tooler_request['tone']} - Sois utile, positif, et actionnable

FORMAT (utilise les emojis):
🎯 **Situation:** [Explication courte de ce qui manque]

🔍 **Solutions trouvées:** [2-3 options avec noms d'outils/packages]

💡 **Recommandation:** [Action concrète que l'utilisateur peut prendre]

⚙️ **Prochaines étapes:**
- [Étape 1]
- [Étape 2]
- [Optionnel: Étape 3]

Sois concis (max 150 mots) mais informatif."""

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Crée la recommandation"}
        ]

        # Utiliser DeepSeek pour la communication (bon équilibre)
        response = self.llm_client.complete(
            messages=messages,
            tier=ModelTier.DEEPSEEK,
            max_tokens=500,
            temperature=0.8
        )

        return {
            "recommendation_ready": True,
            "message": response.content,
            "model_used": response.model,
            "cost": response.cost
        }


def create_communications_agent(llm_client: LLMClient) -> CommunicationsAgent:
    """Factory function to create a Communications Agent"""
    return CommunicationsAgent(llm_client)
