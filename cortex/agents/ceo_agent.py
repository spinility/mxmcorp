"""
CEO Agent - Orchestrateur principal du Cortex
"""

from cortex.agents.base_agent import BaseAgent, AgentConfig
from cortex.core.model_router import ModelTier


class CEOAgent(BaseAgent):
    """
    CEO Agent - Le chef d'orchestre

    Responsabilités:
    - Analyser les demandes utilisateur
    - Décomposer en sous-tâches
    - Déléguer aux Directors appropriés
    - Synthétiser les résultats
    - Optimiser les coûts globaux
    """

    def __init__(self, **kwargs):
        config = AgentConfig(
            name="CEO",
            role="Chief Executive Officer",
            description="Strategic orchestrator and task coordinator",
            base_prompt="""You are the CEO of Cortex MXMCorp, an intelligent AI system.

Your mission:
1. Understand user requests deeply
2. Break down complex tasks into manageable sub-tasks
3. Delegate to the most appropriate Directors (Code, Data, Communication, Operations)
4. Ensure cost optimization at every step
5. Synthesize results into clear, actionable responses

Your philosophy:
- ALWAYS seek the cheapest solution that works
- Delegate when specialists can do better
- Keep responses concise and focused
- Track costs and optimize continuously

You have access to 4 Directors:
- Code Director: Software development, debugging, refactoring
- Data Director: Data analysis, processing, ML/AI tasks
- Communication Director: User interaction, training, documentation
- Operations Director: System operations, infrastructure, deployment
""",
            tier_preference=ModelTier.DEEPSEEK,  # CEO uses mid-tier for strategic thinking
            can_delegate=True,
            specializations=["orchestration", "strategy", "coordination"],
            max_delegation_depth=3
        )

        super().__init__(config, **kwargs)

    def analyze_and_delegate(self, user_request: str, verbose: bool = False):
        """
        Analyse une requête utilisateur et délègue intelligemment

        Args:
            user_request: Requête de l'utilisateur
            verbose: Mode verbose

        Returns:
            Résultat final synthétisé
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"CEO: Analyzing request...")
            print(f"{'='*60}")

        # Étape 1: Analyser la requête
        analysis_prompt = f"""Analyze this user request and determine:
1. What is the main goal?
2. Can it be done in one step or needs decomposition?
3. Which Director(s) should handle it? (Code/Data/Communication/Operations)
4. Estimated complexity (low/medium/high)

User request: {user_request}

Response format (JSON):
{{
    "goal": "...",
    "complexity": "low|medium|high",
    "needs_decomposition": true|false,
    "primary_director": "Code|Data|Communication|Operations",
    "sub_tasks": ["task1", "task2"] // if needs_decomposition
}}
"""

        analysis_result = self.execute(
            task=analysis_prompt,
            use_tools=False,
            verbose=verbose
        )

        if not analysis_result["success"]:
            return analysis_result

        # Pour l'instant, retourner l'analyse
        # TODO: Implémenter la délégation réelle aux Directors
        return {
            "success": True,
            "analysis": analysis_result["data"],
            "message": "Analysis complete. Directors system coming soon.",
            "cost": analysis_result["cost"]
        }


def create_ceo() -> CEOAgent:
    """Factory function pour créer le CEO"""
    return CEOAgent()
