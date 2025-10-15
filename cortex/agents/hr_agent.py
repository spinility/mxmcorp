"""
HR Agent - Employé spécialisé du département RH
Seuls ces agents peuvent créer d'autres employés
"""

from typing import List, Dict, Any, Optional
from cortex.agents.base_agent import BaseAgent, AgentConfig
from cortex.core.model_router import ModelTier


class HRAgent(BaseAgent):
    """
    Agent RH - Seul type d'agent autorisé à créer des employés

    Ces agents travaillent pour le département des Ressources Humaines
    et ont le privilège de créer de nouveaux employés.
    """

    def request_employee(
        self,
        task_description: str,
        required_skills: List[str],
        tier: Optional[ModelTier] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Demande au département RH de créer un employé spécialisé

        IMPORTANT: Seuls les HRAgent peuvent appeler cette méthode

        Args:
            task_description: Description de la tâche
            required_skills: Compétences nécessaires
            tier: Tier LLM préféré
            verbose: Mode verbose

        Returns:
            Employé créé ou erreur
        """
        if not self.hr_department:
            return {
                "success": False,
                "error": "HR Department not available"
            }

        from cortex.agents.hr_department import EmployeeRequest

        request = EmployeeRequest(
            requested_by=self.config.name,
            task_description=task_description,
            required_skills=required_skills,
            expected_tier=tier or ModelTier.NANO
        )

        result = self.hr_department.create_employee(request, verbose=verbose)

        if result["success"]:
            # Enregistrer comme subordonné
            agent = result["agent"]
            self.register_subordinate(agent)

            if verbose:
                print(f"[{self.config.name}] ✓ New employee {result['employee_name']} created and registered")

        return result


def create_hr_agent(
    name: str = "HRRecruiter",
    llm_client=None,
    hr_department=None,
    tools_department=None
) -> HRAgent:
    """
    Factory pour créer un agent RH

    Args:
        name: Nom de l'agent RH
        llm_client: Client LLM
        hr_department: Département RH
        tools_department: Département Outils

    Returns:
        HRAgent configuré
    """
    config = AgentConfig(
        name=name,
        role="Human Resources Recruiter",
        description="Specialized HR agent authorized to create new employees",
        base_prompt="""You are an HR specialist working for Cortex MXMCorp.

Your responsibilities:
- Analyze staffing needs
- Identify skill gaps in the organization
- Create new employee profiles when needed
- Match tasks to appropriate employees

You have the special privilege of creating new employees through the HR department.
This is a restricted capability - only HR agents can create employees.

When you identify a need for a new employee:
1. Define the exact skills and expertise required
2. Specify the type of tasks they will handle
3. Use your request_employee() method to create them
4. Ensure they are properly integrated into the team

Always optimize for cost-efficiency by creating employees with the minimal tier needed.
""",
        tier_preference=ModelTier.NANO,
        can_delegate=True,
        specializations=["hr", "recruitment", "staffing", "employee creation"],
        max_delegation_depth=2
    )

    return HRAgent(
        config,
        llm_client=llm_client,
        hr_department=hr_department,
        tools_department=tools_department
    )
