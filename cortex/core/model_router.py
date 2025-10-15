"""
Model Router - Routeur intelligent de modèles LLM
Choisit TOUJOURS le modèle le moins cher qui peut faire le job

Hiérarchie des modèles (du moins au plus cher):
1. GPT-5-Nano (~$0.0001/1M tokens) - Tasks simples
2. DeepSeek V3.2 (~$0.15/1M tokens) - Tasks complexes
3. Claude Sonnet 4.5 (~$3/1M tokens) - Tasks critiques

Objectif: 70% nano, 25% deepseek, 5% claude
"""

import re
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from .config_loader import get_config


class ModelTier(Enum):
    """Tiers de modèles disponibles"""
    NANO = "nano"          # GPT-5-Nano (testing only)
    DEEPSEEK = "deepseek"  # DeepSeek V3.2-Exp (Tier 1: rapide, économique)
    GPT5 = "gpt5"          # GPT-5 (Tier 2: intelligent, équilibré)
    CLAUDE = "claude"      # Claude Sonnet 4.5 (Tier 3: ultra-puissant)


@dataclass
class TaskComplexity:
    """Analyse de complexité d'une tâche"""
    score: float  # 0-10
    reasoning: str
    factors: Dict[str, float]


@dataclass
class ModelSelection:
    """Résultat de la sélection de modèle"""
    tier: ModelTier
    model_name: str
    reasoning: str
    estimated_cost: float
    confidence: float  # 0-1


class ModelRouter:
    """
    Routeur intelligent qui sélectionne le modèle optimal
    Philosophie: Le moins cher qui peut faire le job
    """

    def __init__(self):
        self.config = get_config()
        self.models_config = self.config.models.get("models", {})
        self.routing_rules = self.config.models.get("routing_rules", {})

        # Patterns pour détection rapide
        self._simple_patterns = [
            r"(parse|extract|classify|validate|list|count|find)",
            r"(get|read|show|display|print)",
        ]

        self._complex_patterns = [
            r"(generate|create|build|implement|design|architect)",
            r"(analyze|optimize|refactor|improve|enhance)",
            r"(explain|understand|reason|deduce)",
        ]

        self._critical_patterns = [
            r"(strategy|critical|important|decide|choose)",
            r"(complex|difficult|challenging|ambiguous)",
            r"(creative|innovative|novel)",
        ]

    def select_model(
        self,
        task: str,
        agent_role: Optional[str] = None,
        context_size: Optional[int] = None,
        force_tier: Optional[ModelTier] = None
    ) -> ModelSelection:
        """
        Sélectionne le modèle optimal pour une tâche

        Args:
            task: Description de la tâche
            agent_role: Rôle de l'agent ("Worker", "Manager", "Director", "CEO")
            context_size: Taille estimée du contexte en tokens
            force_tier: Forcer un tier spécifique (debug)

        Returns:
            ModelSelection avec le modèle choisi et le raisonnement
        """
        if force_tier:
            return self._create_selection(force_tier, "Forced tier")

        # Stratégie 1: Routing par rôle (prioritaire si défini)
        if agent_role:
            tier_from_role = self._route_by_role(agent_role)
            if tier_from_role:
                # Vérifier quand même si la tâche est trop complexe pour ce tier
                complexity = self.analyze_complexity(task)
                if self._is_tier_sufficient(tier_from_role, complexity):
                    return self._create_selection(
                        tier_from_role,
                        f"Selected by agent role: {agent_role}"
                    )

        # Stratégie 2: Détection rapide par patterns
        tier_from_pattern = self._route_by_pattern(task)
        if tier_from_pattern:
            return self._create_selection(
                tier_from_pattern,
                "Selected by task pattern matching"
            )

        # Stratégie 3: Analyse de complexité complète
        complexity = self.analyze_complexity(task)
        tier_from_complexity = self._route_by_complexity(complexity)

        return self._create_selection(
            tier_from_complexity,
            f"Selected by complexity analysis (score: {complexity.score:.1f}/10)"
        )

    def analyze_complexity(self, task: str) -> TaskComplexity:
        """
        Analyse la complexité d'une tâche (score 0-10)

        Facteurs considérés:
        - Longueur de la tâche
        - Mots-clés de complexité
        - Structure (questions, conditions, etc.)
        - Ambiguïté
        """
        task_lower = task.lower()
        factors = {}
        total_score = 0.0

        # Facteur 1: Longueur (plus long = potentiellement plus complexe)
        word_count = len(task.split())
        if word_count < 10:
            factors["length"] = 1.0
        elif word_count < 30:
            factors["length"] = 3.0
        elif word_count < 100:
            factors["length"] = 5.0
        else:
            factors["length"] = 7.0

        # Facteur 2: Verbes d'action
        simple_verbs = ["get", "show", "list", "count", "find", "read", "display"]
        medium_verbs = ["create", "generate", "write", "update", "modify", "calculate"]
        complex_verbs = ["analyze", "optimize", "design", "architect", "refactor", "explain"]
        critical_verbs = ["strategize", "decide", "evaluate", "innovate", "solve"]

        verb_score = 2.0  # default
        for verb in simple_verbs:
            if verb in task_lower:
                verb_score = 1.0
                break
        for verb in medium_verbs:
            if verb in task_lower:
                verb_score = 4.0
                break
        for verb in complex_verbs:
            if verb in task_lower:
                verb_score = 7.0
                break
        for verb in critical_verbs:
            if verb in task_lower:
                verb_score = 9.0
                break

        factors["action_complexity"] = verb_score

        # Facteur 3: Mots-clés de haute complexité
        complex_keywords = [
            "complex", "difficult", "challenging", "ambiguous",
            "creative", "innovative", "strategic", "critical"
        ]
        complexity_boost = sum(2.0 for kw in complex_keywords if kw in task_lower)
        factors["keywords"] = min(complexity_boost, 5.0)

        # Facteur 4: Structure (questions multiples = plus complexe)
        question_marks = task.count("?")
        factors["structure"] = min(question_marks * 1.5, 4.0)

        # Facteur 5: Références à code/architecture
        tech_indicators = ["code", "function", "class", "api", "database", "architecture"]
        if any(ind in task_lower for ind in tech_indicators):
            factors["technical"] = 3.0
        else:
            factors["technical"] = 0.0

        # Calculer score total (moyenne pondérée)
        weights = {
            "length": 0.15,
            "action_complexity": 0.40,
            "keywords": 0.20,
            "structure": 0.15,
            "technical": 0.10
        }

        for factor, value in factors.items():
            total_score += value * weights.get(factor, 0.1)

        # Normaliser entre 0-10
        total_score = min(10.0, max(0.0, total_score))

        reasoning = self._generate_complexity_reasoning(factors, total_score)

        return TaskComplexity(
            score=total_score,
            reasoning=reasoning,
            factors=factors
        )

    def _route_by_role(self, role: str) -> Optional[ModelTier]:
        """Route selon le rôle de l'agent"""
        role_mapping = self.routing_rules.get("agent_role_routing", {})
        model_name = role_mapping.get(role)

        tier_map = {
            "nano": ModelTier.NANO,
            "deepseek": ModelTier.DEEPSEEK,
            "claude": ModelTier.CLAUDE
        }

        return tier_map.get(model_name)

    def _route_by_pattern(self, task: str) -> Optional[ModelTier]:
        """Route selon des patterns de texte (rapide)"""
        task_lower = task.lower()

        # Vérifier patterns simples d'abord (nano)
        for pattern in self._simple_patterns:
            if re.search(pattern, task_lower):
                return ModelTier.NANO

        # Vérifier patterns critiques (claude)
        for pattern in self._critical_patterns:
            if re.search(pattern, task_lower):
                return ModelTier.CLAUDE

        # Vérifier patterns complexes (deepseek)
        for pattern in self._complex_patterns:
            if re.search(pattern, task_lower):
                return ModelTier.DEEPSEEK

        return None  # Pas de match, utiliser analyse de complexité

    def _route_by_complexity(self, complexity: TaskComplexity) -> ModelTier:
        """Route selon le score de complexité"""
        thresholds = self.routing_rules.get("complexity_thresholds", {})

        # Parse les thresholds (format: "0-3", "3-8", "8-10")
        nano_range = thresholds.get("nano", "0-3")
        deepseek_range = thresholds.get("deepseek", "3-8")

        nano_max = float(nano_range.split("-")[1])
        deepseek_max = float(deepseek_range.split("-")[1])

        if complexity.score <= nano_max:
            return ModelTier.NANO
        elif complexity.score <= deepseek_max:
            return ModelTier.DEEPSEEK
        else:
            return ModelTier.CLAUDE

    def _is_tier_sufficient(self, tier: ModelTier, complexity: TaskComplexity) -> bool:
        """Vérifie si un tier est suffisant pour une complexité donnée"""
        tier_max_complexity = {
            ModelTier.NANO: 3.0,
            ModelTier.DEEPSEEK: 6.0,
            ModelTier.GPT5: 8.5,
            ModelTier.CLAUDE: 10.0
        }

        return complexity.score <= tier_max_complexity.get(tier, 0.0)

    def _create_selection(self, tier: ModelTier, reasoning: str) -> ModelSelection:
        """Crée un ModelSelection à partir d'un tier"""
        model_config = self.models_config.get(tier.value, {})

        return ModelSelection(
            tier=tier,
            model_name=model_config.get("name", "unknown"),
            reasoning=reasoning,
            estimated_cost=model_config.get("cost_per_1m_input", 0.0),
            confidence=0.85  # TODO: Implémenter calcul de confiance réel
        )

    def _generate_complexity_reasoning(
        self,
        factors: Dict[str, float],
        score: float
    ) -> str:
        """Génère une explication de la complexité"""
        parts = []

        # Identifier les facteurs principaux
        sorted_factors = sorted(
            factors.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for factor, value in sorted_factors[:3]:  # Top 3
            if value > 0:
                parts.append(f"{factor}={value:.1f}")

        return f"Complexity {score:.1f}/10 ({', '.join(parts)})"

    def estimate_cost(
        self,
        tier: ModelTier,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estime le coût d'un appel

        Args:
            tier: Tier du modèle
            input_tokens: Tokens d'entrée
            output_tokens: Tokens de sortie

        Returns:
            Coût estimé en dollars
        """
        model_config = self.models_config.get(tier.value, {})

        cost_per_1m_input = model_config.get("cost_per_1m_input", 0.0)
        cost_per_1m_output = model_config.get("cost_per_1m_output", 0.0)

        input_cost = (input_tokens / 1_000_000) * cost_per_1m_input
        output_cost = (output_tokens / 1_000_000) * cost_per_1m_output

        return input_cost + output_cost

    def get_model_info(self, tier: ModelTier) -> Dict[str, Any]:
        """Récupère les infos complètes d'un modèle"""
        return self.models_config.get(tier.value, {})


# Exemple d'utilisation
if __name__ == "__main__":
    router = ModelRouter()

    # Test 1: Tâche simple
    task1 = "List all files in the current directory"
    selection1 = router.select_model(task1)
    print(f"Task: {task1}")
    print(f"Selected: {selection1.model_name} ({selection1.tier.value})")
    print(f"Reasoning: {selection1.reasoning}")
    print(f"Estimated cost: ${selection1.estimated_cost:.6f}/1M tokens\n")

    # Test 2: Tâche complexe
    task2 = "Design a scalable microservices architecture for our e-commerce platform"
    selection2 = router.select_model(task2)
    print(f"Task: {task2}")
    print(f"Selected: {selection2.model_name} ({selection2.tier.value})")
    print(f"Reasoning: {selection2.reasoning}")
    print(f"Estimated cost: ${selection2.estimated_cost:.6f}/1M tokens\n")

    # Test 3: Avec rôle
    task3 = "Refactor this function to improve performance"
    selection3 = router.select_model(task3, agent_role="Worker")
    print(f"Task: {task3} (Worker role)")
    print(f"Selected: {selection3.model_name} ({selection3.tier.value})")
    print(f"Reasoning: {selection3.reasoning}")
    print(f"Estimated cost: ${selection3.estimated_cost:.6f}/1M tokens")
