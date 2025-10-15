"""
Optimization Knowledge - Structure de la base de connaissance d'optimisation

Cette base contient TOUT ce qui permet d'apprendre et d'optimiser:
- Historique complet des requêtes
- Patterns de succès identifiés
- Échecs et leçons apprises
- Statistiques d'usage des outils
- Git diff history
- Métriques de performance
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class RequestOutcome(Enum):
    """Résultat d'une requête"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    BLOCKED = "blocked"


@dataclass
class HistoricalRequest:
    """
    Enregistrement d'une requête historique

    Tout est enregistré pour apprentissage futur
    """
    id: str
    timestamp: datetime
    request_text: str
    request_type: str  # "code", "tool_creation", "planning", etc.
    outcome: RequestOutcome
    workflow_used: str
    agents_involved: List[str]
    duration_seconds: float
    cost: float
    files_modified: List[str]
    lines_added: int
    lines_removed: int
    tools_used: List[str]
    patterns_applied: List[str]
    errors_encountered: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dict pour stockage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['outcome'] = self.outcome.value
        return data


@dataclass
class SuccessPattern:
    """
    Pattern identifié qui mène au succès

    Exemple:
    - "API integration" → toujours utiliser async/await + timeout
    - "Test création" → toujours valider avec validator tool
    """
    id: str
    name: str
    description: str
    context: str  # Quand appliquer ce pattern
    actions: List[str]  # Étapes du pattern
    success_count: int
    failure_count: int
    confidence: float  # success_count / (success + failure)
    avg_duration: float
    avg_cost: float
    examples: List[str]  # IDs de HistoricalRequest
    created_at: datetime
    last_used: datetime

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_used'] = self.last_used.isoformat()
        return data


@dataclass
class FailureAnalysis:
    """
    Analyse d'un échec pour éviter de répéter

    Exemple:
    - Échec: API call sans timeout → freeze
    - Leçon: Toujours ajouter timeout=30
    """
    id: str
    timestamp: datetime
    request_id: str  # Lien vers HistoricalRequest
    error_type: str
    error_message: str
    root_cause: str
    impact: str  # "minor", "major", "critical"
    fix_applied: Optional[str]
    prevention_strategy: str
    recurrence_count: int  # Combien de fois cet échec s'est répété
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class ToolUsageStats:
    """
    Statistiques d'usage d'un outil

    Permet de savoir quels outils sont efficaces
    """
    tool_name: str
    total_uses: int
    success_uses: int
    failure_uses: int
    avg_duration: float
    total_cost: float
    contexts_used_in: List[str]  # Contextes où l'outil est utilisé
    common_errors: List[Dict[str, int]]  # {error: count}
    optimization_suggestions: List[str]
    last_optimized: Optional[datetime]

    @property
    def success_rate(self) -> float:
        if self.total_uses == 0:
            return 0.0
        return self.success_uses / self.total_uses

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.last_optimized:
            data['last_optimized'] = self.last_optimized.isoformat()
        return data


class OptimizationKnowledge:
    """
    Classe centrale de la base de connaissance d'optimisation

    Centralise TOUT ce qu'on apprend pour optimiser continuellement
    """

    def __init__(self):
        # Historique complet
        self.historical_requests: List[HistoricalRequest] = []

        # Patterns de succès
        self.success_patterns: Dict[str, SuccessPattern] = {}

        # Analyses d'échecs
        self.failure_analyses: List[FailureAnalysis] = []

        # Stats d'usage des outils
        self.tool_stats: Dict[str, ToolUsageStats] = {}

        # Git diff history
        self.git_diff_history: List[Dict[str, Any]] = []

        # Métriques globales
        self.global_metrics = {
            "total_requests": 0,
            "success_rate": 0.0,
            "avg_cost": 0.0,
            "avg_duration": 0.0,
            "cost_savings": 0.0,  # Grâce aux optimisations
            "time_savings": 0.0   # Grâce aux optimisations
        }

    def record_request(self, request: HistoricalRequest):
        """Enregistre une requête dans l'historique"""
        self.historical_requests.append(request)
        self._update_global_metrics()

    def add_success_pattern(self, pattern: SuccessPattern):
        """Ajoute un pattern de succès identifié"""
        self.success_patterns[pattern.id] = pattern

    def record_failure(self, failure: FailureAnalysis):
        """Enregistre une analyse d'échec"""
        self.failure_analyses.append(failure)

        # Vérifier si c'est une récurrence
        similar_failures = [
            f for f in self.failure_analyses
            if f.error_type == failure.error_type and f.id != failure.id
        ]
        failure.recurrence_count = len(similar_failures)

    def update_tool_stats(self, tool_name: str, success: bool, duration: float, cost: float):
        """Met à jour stats d'usage d'un outil"""
        if tool_name not in self.tool_stats:
            self.tool_stats[tool_name] = ToolUsageStats(
                tool_name=tool_name,
                total_uses=0,
                success_uses=0,
                failure_uses=0,
                avg_duration=0.0,
                total_cost=0.0,
                contexts_used_in=[],
                common_errors=[],
                optimization_suggestions=[],
                last_optimized=None
            )

        stats = self.tool_stats[tool_name]
        stats.total_uses += 1

        if success:
            stats.success_uses += 1
        else:
            stats.failure_uses += 1

        # Mise à jour moyenne durée
        n = stats.total_uses
        stats.avg_duration = ((stats.avg_duration * (n - 1)) + duration) / n

        stats.total_cost += cost

    def find_similar_requests(self, request_text: str, top_k: int = 5) -> List[HistoricalRequest]:
        """
        Trouve des requêtes similaires dans l'historique

        TODO: Utiliser embeddings pour meilleure similarité
        Pour l'instant: simple keyword matching
        """
        keywords = set(request_text.lower().split())

        scored_requests = []
        for hist_req in self.historical_requests:
            hist_keywords = set(hist_req.request_text.lower().split())
            overlap = len(keywords.intersection(hist_keywords))
            if overlap > 0:
                scored_requests.append((overlap, hist_req))

        # Trier par score descendant
        scored_requests.sort(key=lambda x: x[0], reverse=True)

        return [req for _, req in scored_requests[:top_k]]

    def get_best_pattern_for_context(self, context: str) -> Optional[SuccessPattern]:
        """
        Trouve le meilleur pattern pour un contexte donné

        Args:
            context: Description du contexte (ex: "API integration")

        Returns:
            Le pattern avec la plus haute confidence, ou None
        """
        matching_patterns = [
            p for p in self.success_patterns.values()
            if context.lower() in p.context.lower()
        ]

        if not matching_patterns:
            return None

        # Retourner pattern avec meilleure confidence
        return max(matching_patterns, key=lambda p: p.confidence)

    def get_common_failures_for_type(self, error_type: str) -> List[FailureAnalysis]:
        """Récupère les échecs communs d'un type"""
        return [
            f for f in self.failure_analyses
            if f.error_type == error_type
        ]

    def get_optimization_advice(self, request_text: str, request_type: str) -> Dict[str, Any]:
        """
        Génère des conseils d'optimisation basés sur l'historique

        Returns:
            Dict avec:
            - similar_requests: Requêtes similaires passées
            - recommended_pattern: Pattern recommandé
            - tools_to_use: Outils recommandés
            - warnings: Pièges à éviter (échecs communs)
        """
        # Trouver requêtes similaires
        similar = self.find_similar_requests(request_text)

        # Identifier pattern recommandé
        recommended_pattern = self.get_best_pattern_for_context(request_type)

        # Identifier outils efficaces
        successful_similar = [r for r in similar if r.outcome == RequestOutcome.SUCCESS]
        tools_used = {}
        for req in successful_similar:
            for tool in req.tools_used:
                tools_used[tool] = tools_used.get(tool, 0) + 1

        # Trier par fréquence d'usage
        recommended_tools = sorted(tools_used.items(), key=lambda x: x[1], reverse=True)

        # Identifier pièges (échecs communs)
        failed_similar = [r for r in similar if r.outcome == RequestOutcome.FAILURE]
        warnings = []
        for req in failed_similar:
            warnings.extend(req.errors_encountered)

        return {
            "similar_requests_count": len(similar),
            "success_rate_similar": len(successful_similar) / len(similar) if similar else 0.0,
            "recommended_pattern": recommended_pattern.to_dict() if recommended_pattern else None,
            "recommended_tools": [{"tool": tool, "uses": count} for tool, count in recommended_tools[:5]],
            "warnings": list(set(warnings)),  # Unique warnings
            "avg_duration_similar": sum(r.duration_seconds for r in similar) / len(similar) if similar else 0.0,
            "avg_cost_similar": sum(r.cost for r in similar) / len(similar) if similar else 0.0
        }

    def _update_global_metrics(self):
        """Met à jour les métriques globales"""
        if not self.historical_requests:
            return

        total = len(self.historical_requests)
        successes = sum(1 for r in self.historical_requests if r.outcome == RequestOutcome.SUCCESS)

        self.global_metrics["total_requests"] = total
        self.global_metrics["success_rate"] = successes / total
        self.global_metrics["avg_cost"] = sum(r.cost for r in self.historical_requests) / total
        self.global_metrics["avg_duration"] = sum(r.duration_seconds for r in self.historical_requests) / total

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Résumé des métriques globales"""
        return {
            **self.global_metrics,
            "total_patterns": len(self.success_patterns),
            "total_failures_analyzed": len(self.failure_analyses),
            "tools_tracked": len(self.tool_stats),
            "most_used_tool": max(
                self.tool_stats.values(),
                key=lambda t: t.total_uses
            ).tool_name if self.tool_stats else None
        }


# Factory function
def create_optimization_knowledge() -> OptimizationKnowledge:
    """Crée une base de connaissance d'optimisation"""
    return OptimizationKnowledge()


# Test
if __name__ == "__main__":
    print("Testing Optimization Knowledge...")

    knowledge = create_optimization_knowledge()

    # Test 1: Enregistrer requête
    print("\n1. Recording historical request...")
    req = HistoricalRequest(
        id="req_001",
        timestamp=datetime.now(),
        request_text="Implement OAuth2 authentication",
        request_type="code_development",
        outcome=RequestOutcome.SUCCESS,
        workflow_used="CODE_DEVELOPMENT",
        agents_involved=["CodeAnalystAgent", "CodeValidatorAgent"],
        duration_seconds=45.5,
        cost=0.03,
        files_modified=["auth/oauth.py", "models/user.py"],
        lines_added=150,
        lines_removed=10,
        tools_used=["code_validator.sh"],
        patterns_applied=["API_INTEGRATION"],
        lessons_learned=["Always use async/await for API calls"]
    )
    knowledge.record_request(req)
    print(f"✓ Recorded request: {req.id}")

    # Test 2: Ajouter pattern
    print("\n2. Adding success pattern...")
    pattern = SuccessPattern(
        id="pattern_001",
        name="API Integration Pattern",
        description="Standard pattern for integrating external APIs",
        context="API integration, external services",
        actions=["Use async/await", "Add timeout", "Handle errors", "Log requests"],
        success_count=5,
        failure_count=1,
        confidence=5 / 6,
        avg_duration=40.0,
        avg_cost=0.025,
        examples=["req_001"],
        created_at=datetime.now(),
        last_used=datetime.now()
    )
    knowledge.add_success_pattern(pattern)
    print(f"✓ Added pattern: {pattern.name} (confidence: {pattern.confidence:.1%})")

    # Test 3: Trouver requêtes similaires
    print("\n3. Finding similar requests...")
    similar = knowledge.find_similar_requests("Implement authentication system")
    print(f"✓ Found {len(similar)} similar requests")

    # Test 4: Obtenir conseil d'optimisation
    print("\n4. Getting optimization advice...")
    advice = knowledge.get_optimization_advice("Add payment integration", "code_development")
    print(f"✓ Advice generated:")
    print(f"  Similar requests: {advice['similar_requests_count']}")
    print(f"  Recommended tools: {advice['recommended_tools']}")

    # Test 5: Métriques
    print("\n5. Getting metrics summary...")
    metrics = knowledge.get_metrics_summary()
    print(f"✓ Metrics:")
    print(f"  Total requests: {metrics['total_requests']}")
    print(f"  Success rate: {metrics['success_rate']:.1%}")
    print(f"  Total patterns: {metrics['total_patterns']}")

    print("\n✓ Optimization Knowledge works correctly!")
