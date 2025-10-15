"""
HR Department - Département des Ressources Humaines
Crée et gère dynamiquement les employés selon les besoins
Emploie des HRAgents qui sont les seuls autorisés à créer des employés
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import json

from cortex.agents.base_agent import BaseAgent, AgentConfig
from cortex.core.model_router import ModelTier
from cortex.core.llm_client import LLMClient


@dataclass
class EmployeeRequest:
    """Requête pour créer un nouvel employé"""
    requested_by: str  # Nom de l'agent demandeur
    task_description: str  # Description de la tâche
    required_skills: List[str]  # Compétences requises
    expected_tier: ModelTier  # Tier LLM suggéré
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class HRDepartment:
    """
    Département des Ressources Humaines

    Responsabilités:
    - Analyser les demandes de création d'employés
    - Générer des configurations d'agents optimales
    - Créer et enregistrer de nouveaux employés
    - Maintenir un registre des employés créés
    - Optimiser les coûts (utilise NANO pour l'analyse)
    """

    def __init__(self, llm_client: Optional[LLMClient] = None, tools_department=None):
        self.llm_client = llm_client or LLMClient()

        # Référence au département des Outils (pour donner accès aux employés créés)
        self.tools_department = tools_department

        # Registre des employés créés
        self.employee_registry: Dict[str, Dict[str, Any]] = {}

        # Employés RH (seuls autorisés à créer d'autres employés)
        self.hr_agents: List = []

        # Compteurs
        self.employees_created = 0
        self.requests_processed = 0
        self.total_cost = 0.0

    def add_hr_agent(self, hr_agent):
        """
        Ajoute un agent RH au département

        Seuls les HRAgents peuvent créer des employés
        """
        self.hr_agents.append(hr_agent)

    def get_hr_agents(self) -> List:
        """Retourne la liste des agents RH"""
        return self.hr_agents

    def create_employee(
        self,
        request: EmployeeRequest,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Crée un nouvel employé sur mesure pour une tâche

        Args:
            request: Requête de création
            verbose: Mode verbose

        Returns:
            Dict avec agent créé et métadonnées
        """
        self.requests_processed += 1

        if verbose:
            print(f"\n[HR] Processing employee creation request from {request.requested_by}")
            print(f"[HR] Task: {request.task_description[:80]}...")

        try:
            # Analyser la requête et générer la configuration
            config = self._generate_agent_config(request, verbose)

            # Créer l'agent avec accès aux départements
            agent = BaseAgent(
                config,
                llm_client=self.llm_client,
                hr_department=self,  # L'employé peut aussi demander d'autres employés
                tools_department=self.tools_department  # L'employé peut demander des outils
            )

            # Enregistrer dans le registre
            employee_record = {
                "agent": agent,
                "config": config,
                "created_at": datetime.now().isoformat(),
                "requested_by": request.requested_by,
                "task_description": request.task_description,
                "usage_count": 0
            }

            self.employee_registry[config.name] = employee_record
            self.employees_created += 1

            if verbose:
                print(f"[HR] ✓ Created employee: {config.name}")
                print(f"[HR] Role: {config.role}")
                print(f"[HR] Tier: {config.tier_preference.value}")

            return {
                "success": True,
                "agent": agent,
                "employee_name": config.name,
                "role": config.role,
                "cost": self.total_cost
            }

        except Exception as e:
            if verbose:
                print(f"[HR] ✗ Failed to create employee: {e}")

            return {
                "success": False,
                "error": str(e),
                "request": request
            }

    def _generate_agent_config(
        self,
        request: EmployeeRequest,
        verbose: bool = False
    ) -> AgentConfig:
        """
        Génère une configuration d'agent optimale via LLM
        Les employés générés sont indétectables des employés standards
        """
        # Construire le prompt pour créer un employé indétectable
        prompt = f"""You are an expert HR specialist creating a professional employee profile.

IMPORTANT: Create a profile that looks completely natural and professional,
indistinguishable from manually-created employees. Use professional business language.

TASK TO ACCOMPLISH:
{request.task_description}

REQUIRED SKILLS:
{', '.join(request.required_skills)}

REQUESTED BY:
{request.requested_by}

TIER LEVEL:
{request.expected_tier.value}

Create a JSON configuration for a highly professional specialized employee:

1. NAME: Professional, memorable name (CamelCase format like "SeniorAnalyst", "DataEngineer", etc.)
   - Should sound like a real job title or professional designation
   - Examples: "BackendArchitect", "QualityAssurance", "DatabaseOptimizer"

2. ROLE: Official-sounding job title
   - Examples: "Senior Data Analyst", "Software Architect", "Quality Assurance Specialist"

3. DESCRIPTION: Professional bio highlighting expertise
   - Write as if for a company directory
   - Mention years of experience, key skills, domain expertise
   - 2-3 sentences, professional tone

4. BASE_PROMPT: Detailed professional instruction set
   - Define responsibilities and work approach
   - Mention professional standards and best practices
   - Emphasize efficiency, quality, and expertise
   - 3-5 sentences explaining how they work

5. SPECIALIZATIONS: 3-5 professional keywords
   - Use industry-standard terminology
   - Examples: ["software-architecture", "design-patterns", "code-review"]

6. CAN_DELEGATE: Usually false for specialized roles

Return ONLY valid JSON:
{{
  "name": "ProfessionalEmployeeName",
  "role": "Official Job Title",
  "description": "Professional bio describing expertise and experience...",
  "base_prompt": "You are a professional [role] with expertise in... Your responsibilities include... You approach tasks by...",
  "specializations": ["skill1", "skill2", "skill3"],
  "can_delegate": false,
  "tier_preference": "{request.expected_tier.value}"
}}
"""

        messages = [
            {"role": "user", "content": prompt}
        ]

        # Utiliser NANO pour économiser
        response = self.llm_client.complete(
            messages=messages,
            tier=ModelTier.NANO,
            temperature=1.0
        )

        self.total_cost += response.cost

        if verbose:
            print(f"[HR] Profile generation cost: ${response.cost:.6f}")

        # Parser le JSON
        try:
            # Extraire le JSON de la réponse (peut contenir du texte autour)
            content = response.content.strip()

            # Trouver le JSON entre accolades
            start = content.find('{')
            end = content.rfind('}') + 1

            if start == -1 or end == 0:
                raise ValueError("No JSON found in response")

            json_str = content[start:end]
            config_data = json.loads(json_str)

            # Convertir en AgentConfig
            tier_str = config_data.get('tier_preference', request.expected_tier.value)
            tier = ModelTier(tier_str) if isinstance(tier_str, str) else tier_str

            config = AgentConfig(
                name=config_data['name'],
                role=config_data['role'],
                description=config_data['description'],
                base_prompt=config_data['base_prompt'],
                tier_preference=tier,
                can_delegate=config_data.get('can_delegate', False),
                specializations=config_data.get('specializations', []),
                max_delegation_depth=1  # Workers ne délèguent pas profondément
            )

            return config

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            if verbose:
                print(f"[HR] Warning: Failed to parse LLM response, using fallback config")
                print(f"[HR] Error: {e}")

            # Fallback: créer une config basique
            return self._create_fallback_config(request)

    def _create_fallback_config(self, request: EmployeeRequest) -> AgentConfig:
        """Crée une configuration de secours si l'analyse LLM échoue"""
        # Générer un nom basé sur les skills
        name_parts = [s.capitalize() for s in request.required_skills[:2]]
        name = ''.join(name_parts) + 'Worker'

        return AgentConfig(
            name=name,
            role=f"Specialized {' '.join(request.required_skills)} Worker",
            description=f"Expert in {', '.join(request.required_skills)}",
            base_prompt=f"""You are a specialized worker focused on {', '.join(request.required_skills)}.
Your task: {request.task_description}
Be efficient, precise, and cost-effective in your work.""",
            tier_preference=request.expected_tier,
            can_delegate=False,
            specializations=request.required_skills,
            max_delegation_depth=0
        )

    def get_employee(self, name: str) -> Optional[BaseAgent]:
        """Récupère un employé par son nom"""
        record = self.employee_registry.get(name)
        if record:
            record['usage_count'] += 1
            return record['agent']
        return None

    def list_employees(self) -> List[Dict[str, Any]]:
        """Liste tous les employés créés"""
        return [
            {
                "name": record['config'].name,
                "role": record['config'].role,
                "created_at": record['created_at'],
                "requested_by": record['requested_by'],
                "usage_count": record['usage_count'],
                "task_count": record['agent'].task_count,
                "total_cost": record['agent'].total_cost
            }
            for record in self.employee_registry.values()
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Statistiques du département RH"""
        return {
            "employees_created": self.employees_created,
            "requests_processed": self.requests_processed,
            "total_cost": self.total_cost,
            "active_employees": len(self.employee_registry),
            "total_employee_tasks": sum(
                record['agent'].task_count
                for record in self.employee_registry.values()
            ),
            "total_employee_cost": sum(
                record['agent'].total_cost
                for record in self.employee_registry.values()
            )
        }

    def __repr__(self):
        return f"<HRDepartment: {self.employees_created} employees created>"
