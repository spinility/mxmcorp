"""
Nano Self-Assessment System

Permet à nano d'évaluer sa propre capacité à gérer une tâche et de router
intelligemment vers l'employé le plus qualifié si nécessaire.

Flow:
1. Nano évalue: confidence + severity + best_employee
2. Décision: peut-il gérer SAFE avec HAUTE confiance?
3. Si OUI → exécute
4. Si NON → route vers employé qualifié avec contexte adapté
"""

import json
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier
from cortex.core.smart_context_builder import TaskSeverity


class ConfidenceLevel(Enum):
    """Niveau de confiance de nano pour gérer une tâche"""
    HIGH = "HIGH"      # Peut gérer facilement
    MEDIUM = "MEDIUM"  # Peut gérer mais attention requise
    LOW = "LOW"        # Ne devrait pas gérer


@dataclass
class TaskAssessment:
    """Évaluation d'une tâche par nano"""
    confidence: ConfidenceLevel
    severity: TaskSeverity
    can_handle_safely: bool
    best_employee: str
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence": self.confidence.value,
            "severity": self.severity.value,
            "can_handle_safely": self.can_handle_safely,
            "best_employee": self.best_employee,
            "reasoning": self.reasoning
        }


SELF_ASSESSMENT_PROMPT = """You are a task evaluator for nano model. Analyze this task and provide a structured assessment.

Task: {task}

Evaluate these aspects:

1. CONFIDENCE: Can nano handle this task safely with HIGH confidence?
   - HIGH: Simple, routine task (comments, formatting, simple functions, basic validation)
   - MEDIUM: Doable but requires careful attention (moderate complexity)
   - LOW: Complex, risky, or outside expertise (architecture, security, complex algorithms)

2. SEVERITY: What's the severity level?
   - CRITICAL: Production changes, security (auth/encryption), payments, database migrations, API keys
   - HIGH: Public APIs, core features, important user-facing functionality
   - MEDIUM: Standard features, general improvements, internal tools
   - LOW: Refactoring, documentation, tests, cleanup, comments

3. BEST_EMPLOYEE: If nano cannot handle with HIGH confidence, who is most qualified?
   - nano: Simple task, nano can handle
   - ceo: Strategic decisions, company-wide changes, high-level planning
   - cto: Technical architecture, system design, complex technical decisions
   - hr: Hiring, employee management, team structure, org design
   - finance: Budget, pricing, cost analysis, financial planning
   - product: Features, roadmap, user experience, product decisions
   - [specific_worker]: Implementation tasks requiring specific expertise

4. REASONING: Brief explanation (1-2 sentences max)

IMPORTANT RULES:
- Be CONSERVATIVE: When in doubt, delegate
- ALWAYS delegate CRITICAL tasks (regardless of confidence)
- ALWAYS delegate if confidence is LOW
- nano should only handle HIGH confidence + (LOW or MEDIUM severity)

Respond ONLY with valid JSON (no markdown, no extra text):
{{
  "confidence": "HIGH|MEDIUM|LOW",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "can_handle_safely": true|false,
  "best_employee": "nano|ceo|cto|hr|finance|product|[worker_name]",
  "reasoning": "brief explanation"
}}"""


class NanoSelfAssessment:
    """
    Système d'auto-évaluation pour nano

    Permet à nano de déterminer s'il peut gérer une tâche en sécurité
    ou s'il doit la déléguer à un employé plus qualifié.
    """

    def __init__(self, llm_client: LLMClient, use_tier: ModelTier = ModelTier.NANO):
        """
        Args:
            llm_client: Client LLM pour communication avec nano
            use_tier: Quel tier utiliser pour l'évaluation (default: NANO)
        """
        self.llm = llm_client
        self.tier = use_tier

    def evaluate(self, task: str, verbose: bool = False) -> TaskAssessment:
        """
        Évalue si nano peut gérer la tâche en sécurité

        Args:
            task: Description de la tâche
            verbose: Si True, affiche les détails

        Returns:
            TaskAssessment avec confidence, severity, routing, etc.
        """
        if verbose:
            print(f"🔍 Nano evaluating: {task[:60]}...")

        # Construire le prompt
        prompt = SELF_ASSESSMENT_PROMPT.format(task=task)

        # Demander à nano d'évaluer
        try:
            llm_response = self.llm.complete(
                messages=[{"role": "user", "content": prompt}],
                tier=self.tier,
                max_tokens=200,
                temperature=1.0  # Nano ne supporte que temperature=1.0
            )

            response = llm_response.content

            # Parser la réponse JSON
            assessment_data = self._parse_response(response)

            # Appliquer les règles de sécurité
            assessment_data = self._apply_safety_rules(assessment_data)

            # Créer l'objet TaskAssessment
            assessment = TaskAssessment(
                confidence=ConfidenceLevel[assessment_data["confidence"]],
                severity=TaskSeverity[assessment_data["severity"]],
                can_handle_safely=assessment_data["can_handle_safely"],
                best_employee=assessment_data["best_employee"],
                reasoning=assessment_data["reasoning"]
            )

            if verbose:
                self._print_assessment(assessment)

            return assessment

        except Exception as e:
            # En cas d'erreur, déléguer par défaut (conservateur)
            print(f"⚠️  Assessment error: {e}")
            return TaskAssessment(
                confidence=ConfidenceLevel.LOW,
                severity=TaskSeverity.MEDIUM,
                can_handle_safely=False,
                best_employee="ceo",
                reasoning=f"Assessment failed: {str(e)}"
            )

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse la réponse JSON de nano"""
        try:
            # Nettoyer la réponse (enlever markdown si présent)
            cleaned = response.strip()
            if cleaned.startswith("```"):
                # Extraire JSON du markdown
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1])

            return json.loads(cleaned)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {response}") from e

    def _apply_safety_rules(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applique les règles de sécurité strictes

        Règles:
        1. Toute tâche CRITICAL → must delegate
        2. Confidence LOW → must delegate
        3. Confidence MEDIUM + Severity HIGH → should delegate
        """
        severity = assessment["severity"]
        confidence = assessment["confidence"]

        # Règle 1: CRITICAL tasks must be delegated
        if severity == "CRITICAL":
            assessment["can_handle_safely"] = False
            if assessment["best_employee"] == "nano":
                assessment["best_employee"] = "cto"  # Default for critical

        # Règle 2: LOW confidence must be delegated
        elif confidence == "LOW":
            assessment["can_handle_safely"] = False

        # Règle 3: MEDIUM confidence + HIGH severity → delegate
        elif confidence == "MEDIUM" and severity == "HIGH":
            assessment["can_handle_safely"] = False

        # Règle 4: HIGH confidence + (LOW or MEDIUM) → can handle
        elif confidence == "HIGH" and severity in ["LOW", "MEDIUM"]:
            assessment["can_handle_safely"] = True
            assessment["best_employee"] = "nano"

        else:
            # Par défaut: être conservateur
            assessment["can_handle_safely"] = False

        return assessment

    def _print_assessment(self, assessment: TaskAssessment):
        """Affiche l'évaluation de manière lisible"""
        print(f"\n📊 Nano Assessment:")
        print(f"   Confidence: {assessment.confidence.value}")
        print(f"   Severity: {assessment.severity.value}")
        print(f"   Can handle safely: {'✅ YES' if assessment.can_handle_safely else '❌ NO'}")
        print(f"   Best employee: {assessment.best_employee}")
        print(f"   Reasoning: {assessment.reasoning}")

    def should_handle(self, task: str) -> bool:
        """
        Détermine rapidement si nano devrait gérer la tâche

        Args:
            task: Description de la tâche

        Returns:
            True si nano peut gérer en sécurité
        """
        assessment = self.evaluate(task)
        return assessment.can_handle_safely


class IntelligentRouter:
    """
    Routeur intelligent basé sur l'évaluation de nano

    Route les tâches vers le bon employé avec le contexte adapté
    selon la sévérité détectée.
    """

    def __init__(self, nano_assessment: NanoSelfAssessment):
        """
        Args:
            nano_assessment: Système d'évaluation nano
        """
        self.nano_assessment = nano_assessment

    def get_routing_decision(
        self,
        task: str,
        verbose: bool = False
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Décide du routing pour une tâche

        Args:
            task: Description de la tâche
            verbose: Si True, affiche les détails

        Returns:
            Tuple (employee_name, execution_params)
        """
        # Phase 1: Évaluation par nano
        assessment = self.nano_assessment.evaluate(task, verbose=verbose)

        # Phase 2: Décision de routing
        if assessment.can_handle_safely:
            # Nano peut gérer
            employee = "nano"
            params = self._get_nano_params(assessment)

            if verbose:
                print(f"\n✅ Decision: NANO handles (safe)")

        else:
            # Déléguer au meilleur employé
            employee = assessment.best_employee

            # Fallback si employé inconnu
            if employee == "nano":
                employee = "ceo"

            params = self._get_delegate_params(assessment)

            if verbose:
                print(f"\n🔄 Decision: DELEGATE to {employee}")

        return employee, params

    def _get_nano_params(self, assessment: TaskAssessment) -> Dict[str, Any]:
        """Paramètres d'exécution pour nano"""
        return {
            "severity": assessment.severity,
            "context_budget": 900,  # Budget standard pour nano
            "assessment": assessment.to_dict(),
            "executor": "nano"
        }

    def _get_delegate_params(self, assessment: TaskAssessment) -> Dict[str, Any]:
        """Paramètres d'exécution pour employé délégué"""

        # Ajuster le budget selon sévérité
        budget_map = {
            TaskSeverity.CRITICAL: 600,  # Strict, peu de tokens
            TaskSeverity.HIGH: 800,
            TaskSeverity.MEDIUM: 900,
            TaskSeverity.LOW: 900
        }

        return {
            "severity": assessment.severity,
            "context_budget": budget_map[assessment.severity],
            "assessment": assessment.to_dict(),
            "delegated_from": "nano",
            "delegation_reason": assessment.reasoning
        }


if __name__ == "__main__":
    # Test rapide
    print("Testing Nano Self-Assessment...\n")

    client = LLMClient()
    nano_eval = NanoSelfAssessment(client)
    router = IntelligentRouter(nano_eval)

    # Test cases
    test_tasks = [
        "Add a comment to the calculate_total function",
        "Fix critical authentication vulnerability in production",
        "Create a new dashboard feature for analytics",
        "Refactor code and add documentation",
        "Redesign the system architecture",
    ]

    for task in test_tasks:
        print("=" * 70)
        print(f"Task: {task}")
        print("=" * 70)

        employee, params = router.get_routing_decision(task, verbose=True)

        print(f"\n🎯 Final Decision:")
        print(f"   Employee: {employee}")
        print(f"   Severity: {params['severity'].value}")
        print(f"   Context Budget: {params['context_budget']} tokens")
        print()
