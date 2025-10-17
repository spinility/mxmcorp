"""
Quality Evaluator - Évalue la qualité des réponses via LLM
Utilise un LLM pour juger objectivement la qualité d'une réponse
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json
import re

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier


@dataclass
class QualityAssessment:
    """Résultat de l'évaluation de qualité"""
    score: float  # 0-10
    confidence: float  # 0-1
    issues: List[str]  # Problèmes identifiés
    strengths: List[str]  # Points forts
    needs_escalation: bool  # True si escalade recommandée
    suggested_tier: Optional[ModelTier]  # Tier suggéré si escalade
    suggested_expert: Optional[str]  # Type d'expert si nécessaire
    reasoning: str  # Explication du jugement
    cost: float  # Coût de l'évaluation


class QualityEvaluator:
    """
    Évalue la qualité des réponses en utilisant un LLM

    Utilise NANO pour l'évaluation (rapide et économique)
    Peut escalader à DEEPSEEK si l'évaluation elle-même est complexe
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.evaluation_tier = ModelTier.NANO  # Par défaut, évalue avec NANO
        self.total_evaluation_cost = 0.0

    def evaluate(
        self,
        task: str,
        response: str,
        tier_used: ModelTier,
        quality_threshold: float = 6.0,
        verbose: bool = False
    ) -> QualityAssessment:
        """
        Évalue la qualité d'une réponse via LLM

        Args:
            task: Tâche originale
            response: Réponse à évaluer
            tier_used: Tier qui a généré cette réponse
            quality_threshold: Seuil minimum acceptable
            verbose: Mode verbose

        Returns:
            QualityAssessment avec score et recommandations
        """
        if verbose:
            print(f"[QualityEvaluator] Evaluating response from {tier_used.value}...")

        # Construire le prompt d'évaluation
        evaluation_prompt = self._build_evaluation_prompt(
            task=task,
            response=response,
            tier_used=tier_used,
            quality_threshold=quality_threshold
        )

        # Demander au LLM d'évaluer
        messages = [
            {
                "role": "system",
                "content": """You are an expert quality assessor for AI responses.
Your job is to objectively evaluate if a response adequately answers the given task.
You must be strict but fair in your evaluation."""
            },
            {
                "role": "user",
                "content": evaluation_prompt
            }
        ]

        try:
            # Utiliser NANO pour évaluation (rapide et économique)
            llm_response = self.llm_client.complete(
                messages=messages,
                tier=self.evaluation_tier,
                temperature=1.0
            )

            self.total_evaluation_cost += llm_response.cost

            if verbose:
                print(f"[QualityEvaluator] Evaluation cost: ${llm_response.cost:.6f}")

            # Parser la réponse JSON
            assessment = self._parse_evaluation_response(
                llm_response.content,
                tier_used,
                llm_response.cost,
                verbose
            )

            if verbose:
                print(f"[QualityEvaluator] Quality score: {assessment.score:.1f}/10")
                print(f"[QualityEvaluator] Needs escalation: {assessment.needs_escalation}")

            return assessment

        except Exception as e:
            if verbose:
                print(f"[QualityEvaluator] Error during evaluation: {e}")

            # Fallback: évaluation basique sans LLM
            return self._fallback_evaluation(task, response, tier_used, llm_response.cost if 'llm_response' in locals() else 0.0)

    def _build_evaluation_prompt(
        self,
        task: str,
        response: str,
        tier_used: ModelTier,
        quality_threshold: float
    ) -> str:
        """Construit le prompt d'évaluation pour le LLM"""

        return f"""Evaluate the quality of this AI response.

ORIGINAL TASK:
{task}

RESPONSE TO EVALUATE:
{response}

CONTEXT:
- This response was generated using tier: {tier_used.value}
- Quality threshold required: {quality_threshold}/10

EVALUATION CRITERIA:
1. **Completeness**: Does it fully answer the task? (0-3 points)
2. **Correctness**: Is the information accurate and relevant? (0-3 points)
3. **Clarity**: Is it clear, well-structured, and easy to understand? (0-2 points)
4. **Usefulness**: Can the user directly use this response? (0-2 points)

SPECIFIC CHECKS:
- If task asks for code, does response contain actual code?
- If task asks for explanation, is it detailed enough?
- Are there disclaimers like "I cannot", "I don't know", "need more info"?
- Is the response too short/vague for the complexity of the task?

⚠️ TEMPORAL VOLATILITY CHECK (CRITICAL):
- Does the response contain information that could become OUTDATED or INVALID over time?
- Examples of VOLATILE responses:
  * "Yes, file X exists" / "File Y is in directory Z" (file could be deleted later)
  * "The current value is X" (value could change)
  * "User A has access to B" (permissions could change)
  * "The system is running" / "Service X is online" (status could change)
  * "There are N items in the database" (count could change)
- If response contains VOLATILE information, flag it as an ISSUE with severity "temporal_volatility"
- Volatile responses should LOSE 1-2 points depending on severity
- Suggest adding timestamps or disclaimers like "as of [date/time]" or "this may have changed"

Return your evaluation as JSON in this EXACT format:
{{
  "score": <float 0-10>,
  "confidence": <float 0-1>,
  "issues": [<list of problems found, if any>],
  "strengths": [<list of good aspects>],
  "needs_escalation": <true/false>,
  "suggested_tier": "<nano/deepseek/claude or null>",
  "suggested_expert": "<expert_type or null>",
  "reasoning": "<brief explanation of your evaluation>"
}}

ESCALATION RULES:
- If score < {quality_threshold} and tier_used is "nano", suggest "deepseek"
- If score < {quality_threshold} and tier_used is "deepseek", suggest "claude"
- If score < {quality_threshold} and tier_used is "claude", suggest an expert:
  * "security_expert" for security/vulnerability tasks
  * "system_designer" for architecture/scalability tasks
  * "algorithm_specialist" for algorithm/optimization tasks
  * "data_scientist" for ML/statistics tasks
  * "code_architect" for design patterns/refactoring tasks

Be objective and strict. Return ONLY the JSON, no other text.
"""

    def _parse_evaluation_response(
        self,
        response: str,
        tier_used: ModelTier,
        evaluation_cost: float,
        verbose: bool = False
    ) -> QualityAssessment:
        """Parse la réponse JSON du LLM évaluateur"""

        try:
            # Extraire le JSON de la réponse
            response = response.strip()

            # Trouver le JSON entre accolades
            start = response.find('{')
            end = response.rfind('}') + 1

            if start == -1 or end == 0:
                raise ValueError("No JSON found in evaluation response")

            json_str = response[start:end]
            data = json.loads(json_str)

            # Valider et extraire les champs
            score = float(data.get('score', 5.0))
            confidence = float(data.get('confidence', 0.5))
            issues = data.get('issues', [])
            strengths = data.get('strengths', [])
            needs_escalation = bool(data.get('needs_escalation', False))

            # Parser suggested_tier
            suggested_tier_str = data.get('suggested_tier')
            suggested_tier = None
            if suggested_tier_str and suggested_tier_str != "null":
                tier_map = {
                    "nano": ModelTier.NANO,
                    "deepseek": ModelTier.DEEPSEEK,
                    "claude": ModelTier.CLAUDE
                }
                suggested_tier = tier_map.get(suggested_tier_str.lower())

            # Parser suggested_expert
            suggested_expert_str = data.get('suggested_expert')
            suggested_expert = None
            if suggested_expert_str and suggested_expert_str != "null":
                suggested_expert = suggested_expert_str

            reasoning = data.get('reasoning', 'No reasoning provided')

            return QualityAssessment(
                score=score,
                confidence=confidence,
                issues=issues,
                strengths=strengths,
                needs_escalation=needs_escalation,
                suggested_tier=suggested_tier,
                suggested_expert=suggested_expert,
                reasoning=reasoning,
                cost=evaluation_cost
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            if verbose:
                print(f"[QualityEvaluator] Failed to parse evaluation, using fallback: {e}")

            # Fallback
            return QualityAssessment(
                score=5.0,
                confidence=0.3,
                issues=["Failed to parse evaluation"],
                strengths=[],
                needs_escalation=True,
                suggested_tier=self._get_next_tier(tier_used),
                suggested_expert=None,
                reasoning="Evaluation parsing failed, assuming needs escalation",
                cost=evaluation_cost
            )

    def _fallback_evaluation(
        self,
        task: str,
        response: str,
        tier_used: ModelTier,
        cost: float
    ) -> QualityAssessment:
        """Évaluation de secours sans LLM (heuristiques basiques)"""

        score = 5.0
        issues = []
        strengths = []

        # Vérifications basiques
        if len(response) < 50:
            issues.append("Response too short")
            score -= 2.0
        elif len(response) > 200:
            strengths.append("Detailed response")
            score += 1.0

        # Disclaimers négatifs
        negative_patterns = ["i cannot", "i can't", "unable to", "don't know"]
        if any(pattern in response.lower() for pattern in negative_patterns):
            issues.append("Contains negative disclaimer")
            score -= 2.0

        # Présence de code si demandé
        task_lower = task.lower()
        if any(kw in task_lower for kw in ["code", "function", "implement"]):
            if any(kw in response for kw in ["def ", "function", "class ", "const ", "let "]):
                strengths.append("Contains code as expected")
                score += 2.0
            else:
                issues.append("Code expected but not found")
                score -= 2.0

        score = max(0.0, min(10.0, score))

        return QualityAssessment(
            score=score,
            confidence=0.4,
            issues=issues,
            strengths=strengths,
            needs_escalation=score < 6.0,
            suggested_tier=self._get_next_tier(tier_used) if score < 6.0 else None,
            suggested_expert=None,
            reasoning="Fallback heuristic evaluation",
            cost=cost
        )

    def _get_next_tier(self, current_tier: ModelTier) -> Optional[ModelTier]:
        """Retourne le tier supérieur"""
        tier_order = [ModelTier.NANO, ModelTier.DEEPSEEK, ModelTier.CLAUDE]
        try:
            current_index = tier_order.index(current_tier)
            if current_index < len(tier_order) - 1:
                return tier_order[current_index + 1]
        except ValueError:
            pass
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'évaluation"""
        return {
            "total_evaluation_cost": self.total_evaluation_cost,
            "evaluation_tier": self.evaluation_tier.value
        }


# Exemple d'utilisation
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    evaluator = QualityEvaluator()

    # Test 1: Bonne réponse
    task1 = "Write a function to sort a list of numbers"
    response1 = """Here's a function to sort a list:

def sort_numbers(numbers):
    return sorted(numbers)

This uses Python's built-in sorted() function."""

    assessment1 = evaluator.evaluate(task1, response1, ModelTier.NANO, verbose=True)
    print(f"\nTest 1 - Score: {assessment1.score}/10")
    print(f"Needs escalation: {assessment1.needs_escalation}")

    # Test 2: Réponse insuffisante
    task2 = "Design a scalable microservices architecture"
    response2 = "Use Docker and Kubernetes."

    assessment2 = evaluator.evaluate(task2, response2, ModelTier.NANO, verbose=True)
    print(f"\nTest 2 - Score: {assessment2.score}/10")
    print(f"Needs escalation: {assessment2.needs_escalation}")
    print(f"Suggested tier: {assessment2.suggested_tier}")
