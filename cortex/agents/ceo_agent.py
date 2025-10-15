"""
CEO Agent - Orchestrateur principal du Cortex
Le CEO n'a aucune compétence directe et délègue TOUJOURS
"""

from typing import Optional, List
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

    def __init__(self, hr_department=None, tools_department=None, hr_agent=None, expert_pool=None, **kwargs):
        config = AgentConfig(
            name="CEO",
            role="Chief Executive Officer",
            description="Strategic orchestrator - ALWAYS delegates, has NO direct skills",
            base_prompt="""You are the CEO of Cortex MXMCorp, an intelligent AI system.

CRITICAL: You have NO direct skills yourself. You are ONLY an orchestrator.

Your ONLY mission:
1. Understand user requests deeply
2. Decide WHO should handle the task (which Director or Employee)
3. Delegate EVERYTHING to appropriate subordinates
4. If no suitable employee exists, delegate to HR Agent who will create one
5. If tools are missing, request Tools Department to create them
6. Synthesize results from subordinates

NEVER ATTEMPT TO:
- Write code yourself
- Analyze data yourself
- Answer questions yourself
- Use tools yourself
- Create employees yourself (only HR Agent can do this)

ALWAYS DELEGATE. Your value is in coordination, not execution.

Available resources:
- 4 Directors: Code, Data, Communication, Operations
- HR Agent: Specialized agent who can create new employees
- HR Department: Manages all employee records
- Tools Department: Can fabricate custom tools for employees
- Expert Pool: Highly specialized experts for complex escalations
- Dynamic employee pool (created by HR Agent as needed)
""",
            tier_preference=ModelTier.NANO,  # CEO just routes, uses cheapest tier
            can_delegate=True,
            specializations=["orchestration", "delegation", "coordination"],
            max_delegation_depth=5
        )

        super().__init__(config, expert_pool=expert_pool, **kwargs)

        # Références aux départements
        self.hr_department = hr_department
        self.tools_department = tools_department
        self.expert_pool = expert_pool

        # HR Agent (seul autorisé à créer des employés)
        self.hr_agent = hr_agent
        if hr_agent:
            self.register_subordinate(hr_agent)

    def analyze_and_delegate(self, user_request: str, verbose: bool = False):
        """
        Analyse une requête utilisateur et DÉLÈGUE TOUJOURS

        Le CEO n'exécute JAMAIS lui-même, il délègue systématiquement.

        Args:
            user_request: Requête de l'utilisateur
            verbose: Mode verbose

        Returns:
            Résultat final synthétisé depuis les subordonnés
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"CEO: Analyzing request for delegation...")
            print(f"{'='*60}")

        # Analyser et trouver le meilleur subordonné
        # Le CEO utilise sa méthode delegate() héritée de BaseAgent
        result = self.delegate(
            task=user_request,
            verbose=verbose
        )

        if verbose:
            print(f"{'='*60}")
            print(f"CEO: Task delegated and completed")
            print(f"{'='*60}\n")

        return result

    def request_employee_creation(
        self,
        task_description: str,
        required_skills: List[str],
        tier: Optional[ModelTier] = None,
        verbose: bool = False
    ):
        """
        Demande à l'agent RH de créer un nouvel employé

        IMPORTANT: CEO ne crée PAS directement, il délègue à son HR Agent

        Args:
            task_description: Description de la tâche nécessitant un employé
            required_skills: Compétences requises
            tier: Tier LLM suggéré (NANO par défaut)
            verbose: Mode verbose

        Returns:
            Nouvel employé créé ou erreur
        """
        if not self.hr_agent:
            return {
                "success": False,
                "error": "HR Agent not available - only HR Agent can create employees"
            }

        if verbose:
            print(f"[CEO] Delegating employee creation to HR Agent...")

        # Déléguer la création à l'agent RH
        result = self.hr_agent.request_employee(
            task_description=task_description,
            required_skills=required_skills,
            tier=tier,
            verbose=verbose
        )

        if result["success"] and verbose:
            print(f"[CEO] ✓ New employee {result['employee_name']} created by HR Agent")

        return result

    def request_tool_creation(
        self,
        tool_purpose: str,
        input_description: str,
        output_description: str,
        example_usage: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Demande au département des Outils de créer un nouvel outil

        Args:
            tool_purpose: But de l'outil
            input_description: Description des inputs
            output_description: Description des outputs
            example_usage: Exemple d'utilisation
            verbose: Mode verbose

        Returns:
            Nouvel outil créé ou erreur
        """
        if not self.tools_department:
            return {
                "success": False,
                "error": "Tools Department not available"
            }

        from cortex.agents.tools_department import ToolRequest

        request = ToolRequest(
            requested_by=self.config.name,
            tool_purpose=tool_purpose,
            input_description=input_description,
            output_description=output_description,
            example_usage=example_usage
        )

        result = self.tools_department.create_tool(request, verbose=verbose)

        if result["success"]:
            # Rendre l'outil disponible à tous les subordonnés
            tool = result["tool"]
            self.register_tool(tool)

            # Propager aux subordonnés
            for subordinate in self.subordinates.values():
                subordinate.register_tool(tool)

            if verbose:
                print(f"[CEO] ✓ New tool {result['tool_name']} available to all employees")

        return result


def create_ceo(hr_department=None, tools_department=None, hr_agent=None, expert_pool=None) -> CEOAgent:
    """Factory function pour créer le CEO"""
    return CEOAgent(
        hr_department=hr_department,
        tools_department=tools_department,
        hr_agent=hr_agent,
        expert_pool=expert_pool
    )
