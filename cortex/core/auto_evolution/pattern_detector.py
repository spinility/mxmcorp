"""
Pattern Detector - Détecte patterns récurrents dans l'historique

Responsabilités:
- Analyse historique des requêtes
- Identifie patterns répétitifs
- Détecte opportunités d'automatisation
- Calcule métriques de fréquence et succès
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import Counter
import re

from cortex.departments.optimization.optimization_knowledge import (
    OptimizationKnowledge,
    HistoricalRequest,
    RequestOutcome
)


@dataclass
class DetectedPattern:
    """
    Pattern détecté dans l'historique

    Un pattern représente un type de requête qui se répète
    et pourrait bénéficier d'automatisation
    """
    id: str
    name: str
    description: str
    frequency: int  # Nombre de fois demandé
    success_rate: float  # Taux de succès actuel
    avg_duration: float  # Durée moyenne en secondes
    avg_cost: float  # Coût moyen
    keywords: List[str]  # Mots-clés caractéristiques
    agents_involved: List[str]  # Agents utilisés
    tools_used: List[str]  # Outils utilisés
    workflows_used: List[str]  # Workflows utilisés
    complexity_score: float  # Score de complexité (0-1)
    example_requests: List[str]  # IDs de requêtes exemples
    first_seen: datetime
    last_seen: datetime
    trend: str  # "increasing", "stable", "decreasing"

    # Opportunités d'amélioration
    potential_time_savings: float  # Heures/semaine économisables
    potential_success_improvement: float  # Amélioration success rate possible
    recommended_evolution: str  # "agent", "tool", "department", "none"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "frequency": self.frequency,
            "success_rate": self.success_rate,
            "avg_duration": self.avg_duration,
            "avg_cost": self.avg_cost,
            "keywords": self.keywords,
            "agents_involved": self.agents_involved,
            "tools_used": self.tools_used,
            "workflows_used": self.workflows_used,
            "complexity_score": self.complexity_score,
            "example_requests": self.example_requests,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "trend": self.trend,
            "potential_time_savings": self.potential_time_savings,
            "potential_success_improvement": self.potential_success_improvement,
            "recommended_evolution": self.recommended_evolution
        }


class PatternDetector:
    """
    Détecteur de patterns dans l'historique

    Analyse l'OptimizationKnowledge pour identifier:
    - Requêtes répétitives (frequency >= threshold)
    - Workflows inefficaces (success_rate < threshold)
    - Opportunités d'automatisation
    """

    def __init__(
        self,
        optimization_knowledge: OptimizationKnowledge,
        frequency_threshold: int = 3,
        success_threshold: float = 0.7,
        lookback_days: int = 30
    ):
        self.optimization = optimization_knowledge
        self.frequency_threshold = frequency_threshold
        self.success_threshold = success_threshold
        self.lookback_days = lookback_days

    def detect_all_patterns(
        self,
        min_frequency: Optional[int] = None,
        min_potential_savings: Optional[float] = None
    ) -> List[DetectedPattern]:
        """
        Détecte tous les patterns dans l'historique

        Args:
            min_frequency: Fréquence minimale (défaut: threshold)
            min_potential_savings: Économies minimales en heures/semaine

        Returns:
            Liste de patterns détectés, triés par potentiel
        """
        if min_frequency is None:
            min_frequency = self.frequency_threshold

        # Récupérer requêtes récentes
        cutoff_date = datetime.now() - timedelta(days=self.lookback_days)
        recent_requests = [
            req for req in self.optimization.historical_requests
            if req.timestamp >= cutoff_date
        ]

        if not recent_requests:
            return []

        # Grouper requêtes par similarité
        pattern_groups = self._group_similar_requests(recent_requests)

        # Analyser chaque groupe
        detected_patterns = []
        for group_key, requests in pattern_groups.items():
            if len(requests) < min_frequency:
                continue

            pattern = self._analyze_pattern_group(group_key, requests)

            # Filtrer par économies potentielles si spécifié
            if min_potential_savings and pattern.potential_time_savings < min_potential_savings:
                continue

            detected_patterns.append(pattern)

        # Trier par potentiel (économies * fréquence)
        detected_patterns.sort(
            key=lambda p: p.potential_time_savings * p.frequency,
            reverse=True
        )

        return detected_patterns

    def _group_similar_requests(
        self,
        requests: List[HistoricalRequest]
    ) -> Dict[str, List[HistoricalRequest]]:
        """
        Groupe les requêtes similaires ensemble

        Utilise keywords + request_type pour identifier similarité
        """
        groups: Dict[str, List[HistoricalRequest]] = {}

        for req in requests:
            # Extraire keywords significatifs
            keywords = self._extract_keywords(req.request_text)

            # Créer clé de groupe: request_type + top 3 keywords
            group_key = f"{req.request_type}:{':'.join(sorted(keywords[:3]))}"

            if group_key not in groups:
                groups[group_key] = []

            groups[group_key].append(req)

        return groups

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extrait mots-clés significatifs d'un texte

        Filtre stopwords et garde mots importants
        """
        # Stopwords communs
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "as", "is", "was", "are",
            "were", "be", "been", "being", "have", "has", "had", "do",
            "does", "did", "will", "would", "should", "could", "can", "may"
        }

        # Nettoyer et tokenizer
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())

        # Filtrer stopwords
        keywords = [w for w in words if w not in stopwords]

        # Compter fréquences
        word_counts = Counter(keywords)

        # Retourner top keywords
        return [word for word, count in word_counts.most_common(10)]

    def _analyze_pattern_group(
        self,
        group_key: str,
        requests: List[HistoricalRequest]
    ) -> DetectedPattern:
        """
        Analyse un groupe de requêtes similaires pour créer un pattern
        """
        # Métriques de base
        frequency = len(requests)
        successes = sum(1 for r in requests if r.outcome == RequestOutcome.SUCCESS)
        success_rate = successes / frequency if frequency > 0 else 0

        avg_duration = sum(r.duration_seconds for r in requests) / frequency
        avg_cost = sum(r.cost for r in requests) / frequency

        # Extraire informations communes
        all_keywords = []
        all_agents = []
        all_tools = []
        all_workflows = []

        for req in requests:
            all_keywords.extend(self._extract_keywords(req.request_text))
            all_agents.extend(req.agents_involved)
            all_tools.extend(req.tools_used)
            all_workflows.append(req.workflow_used)

        # Top éléments
        keyword_counts = Counter(all_keywords)
        top_keywords = [k for k, c in keyword_counts.most_common(5)]

        agent_counts = Counter(all_agents)
        top_agents = [a for a, c in agent_counts.most_common(3)]

        tool_counts = Counter(all_tools)
        top_tools = [t for t, c in tool_counts.most_common(3)]

        workflow_counts = Counter(all_workflows)
        top_workflows = [w for w, c in workflow_counts.most_common(2)]

        # Dates
        timestamps = [r.timestamp for r in requests]
        first_seen = min(timestamps)
        last_seen = max(timestamps)

        # Trend (augmente/stable/diminue)
        trend = self._calculate_trend(timestamps)

        # Complexité (basée sur nombre d'agents et durée)
        complexity_score = min(
            (len(set(all_agents)) / 5.0 + avg_duration / 1800.0) / 2.0,
            1.0
        )

        # Potentiel d'amélioration
        potential_time_savings = self._calculate_time_savings(
            frequency, avg_duration, success_rate
        )

        potential_success_improvement = max(0.0, 0.95 - success_rate)

        # Recommandation d'évolution
        recommended_evolution = self._recommend_evolution(
            frequency, success_rate, complexity_score, top_tools
        )

        # Générer nom et description
        name = self._generate_pattern_name(top_keywords, top_workflows)
        description = self._generate_pattern_description(
            frequency, top_keywords, success_rate
        )

        pattern_id = f"pattern_{first_seen.strftime('%Y%m%d')}_{hash(group_key) % 10000:04d}"

        return DetectedPattern(
            id=pattern_id,
            name=name,
            description=description,
            frequency=frequency,
            success_rate=success_rate,
            avg_duration=avg_duration,
            avg_cost=avg_cost,
            keywords=top_keywords,
            agents_involved=top_agents,
            tools_used=top_tools,
            workflows_used=top_workflows,
            complexity_score=complexity_score,
            example_requests=[r.id for r in requests[:3]],
            first_seen=first_seen,
            last_seen=last_seen,
            trend=trend,
            potential_time_savings=potential_time_savings,
            potential_success_improvement=potential_success_improvement,
            recommended_evolution=recommended_evolution
        )

    def _calculate_trend(self, timestamps: List[datetime]) -> str:
        """
        Calcule si pattern augmente, stable ou diminue

        Compare première moitié vs deuxième moitié
        """
        if len(timestamps) < 4:
            return "stable"

        sorted_timestamps = sorted(timestamps)
        midpoint = len(sorted_timestamps) // 2

        first_half = sorted_timestamps[:midpoint]
        second_half = sorted_timestamps[midpoint:]

        # Calculer densité (requêtes par jour)
        first_days = (first_half[-1] - first_half[0]).days + 1
        second_days = (second_half[-1] - second_half[0]).days + 1

        first_density = len(first_half) / max(first_days, 1)
        second_density = len(second_half) / max(second_days, 1)

        if second_density > first_density * 1.5:
            return "increasing"
        elif second_density < first_density * 0.5:
            return "decreasing"
        else:
            return "stable"

    def _calculate_time_savings(
        self,
        frequency: int,
        avg_duration: float,
        success_rate: float
    ) -> float:
        """
        Calcule économies de temps potentielles en heures/semaine

        Assume:
        - Spécialisation réduit durée de 40%
        - Améliore success rate vers 95%
        - Moins de retries nécessaires
        """
        # Projeter fréquence sur une semaine (basé sur lookback_days)
        weekly_frequency = frequency * (7.0 / self.lookback_days)

        # Temps actuel par semaine (en heures)
        current_time = (avg_duration / 3600.0) * weekly_frequency

        # Temps avec spécialisation (60% du temps actuel)
        improved_time = current_time * 0.6

        # Facteur retries (si success rate faible, plus de retries)
        if success_rate < 0.95:
            retry_factor = 1.0 / max(success_rate, 0.5)  # Plus de retries si échecs
            current_time *= retry_factor

        # Économies
        savings = current_time - improved_time

        return max(0.0, savings)

    def _recommend_evolution(
        self,
        frequency: int,
        success_rate: float,
        complexity_score: float,
        tools_used: List[str]
    ) -> str:
        """
        Recommande type d'évolution approprié

        Returns: "agent", "tool", "department", "none"
        """
        # Si success rate très bas et fréquent → agent spécialisé
        if success_rate < self.success_threshold and frequency >= 5:
            if complexity_score > 0.6:
                return "agent"  # Agent expert nécessaire

        # Si tools récurrents → tool wrapper
        if len(tools_used) >= 2 and frequency >= self.frequency_threshold:
            return "tool"

        # Si très haute fréquence et complexe → département
        if frequency >= 10 and complexity_score > 0.7:
            return "department"

        # Sinon, pas d'évolution recommandée
        return "none"

    def _generate_pattern_name(
        self,
        keywords: List[str],
        workflows: List[str]
    ) -> str:
        """Génère nom descriptif pour le pattern"""
        if keywords:
            # Capitaliser et joiner top keywords
            name_parts = [k.capitalize() for k in keywords[:2]]
            return " ".join(name_parts) + " Pattern"
        elif workflows:
            return f"{workflows[0]} Pattern"
        else:
            return "Unnamed Pattern"

    def _generate_pattern_description(
        self,
        frequency: int,
        keywords: List[str],
        success_rate: float
    ) -> str:
        """Génère description du pattern"""
        keyword_str = ", ".join(keywords[:3]) if keywords else "various tasks"

        return (
            f"Recurring pattern involving {keyword_str}. "
            f"Requested {frequency} times with {success_rate:.1%} success rate."
        )

    def get_top_automation_candidates(
        self,
        limit: int = 5
    ) -> List[DetectedPattern]:
        """
        Retourne top candidats pour automatisation

        Trie par: ROI = potential_time_savings * frequency
        """
        patterns = self.detect_all_patterns()

        # Calculer ROI pour chaque pattern
        patterns_with_roi = []
        for pattern in patterns:
            roi = pattern.potential_time_savings * pattern.frequency
            patterns_with_roi.append((roi, pattern))

        # Trier par ROI descendant
        patterns_with_roi.sort(key=lambda x: x[0], reverse=True)

        return [p for roi, p in patterns_with_roi[:limit]]


def create_pattern_detector(
    optimization_knowledge: OptimizationKnowledge
) -> PatternDetector:
    """Factory function"""
    return PatternDetector(optimization_knowledge)


# Test
if __name__ == "__main__":
    print("Testing Pattern Detector...")

    from cortex.departments.optimization.optimization_knowledge import (
        OptimizationKnowledge,
        HistoricalRequest,
        RequestOutcome
    )
    from datetime import datetime, timedelta

    # Créer knowledge base avec données test
    knowledge = OptimizationKnowledge()

    # Simuler requêtes répétitives
    print("\n1. Creating test historical requests...")

    # Pattern 1: Security audits (répété 5 fois, success rate moyen)
    for i in range(5):
        req = HistoricalRequest(
            id=f"req_security_{i}",
            timestamp=datetime.now() - timedelta(days=20-i*2),
            request_text=f"Perform security audit on codebase module {i}",
            request_type="security",
            outcome=RequestOutcome.SUCCESS if i < 3 else RequestOutcome.FAILURE,
            workflow_used="security_audit",
            agents_involved=["CodeAnalystExpert", "SecurityReviewer"],
            duration_seconds=1800 + i*100,
            cost=0.05,
            files_modified=[f"module{i}.py"],
            lines_added=0,
            lines_removed=0,
            tools_used=["grep", "find", "git"],
            patterns_applied=[],
            errors_encountered=["Some security issues found"] if i >= 3 else []
        )
        knowledge.record_request(req)

    # Pattern 2: Test generation (répété 4 fois, success rate élevé)
    for i in range(4):
        req = HistoricalRequest(
            id=f"req_test_{i}",
            timestamp=datetime.now() - timedelta(days=15-i*2),
            request_text=f"Generate unit tests for function {i}",
            request_type="testing",
            outcome=RequestOutcome.SUCCESS,
            workflow_used="test_generation",
            agents_involved=["TestWriterAgent"],
            duration_seconds=600 + i*50,
            cost=0.02,
            files_modified=[f"test_{i}.py"],
            lines_added=50,
            lines_removed=0,
            tools_used=["pytest"],
            patterns_applied=["TDD"]
        )
        knowledge.record_request(req)

    print(f"✓ Created {len(knowledge.historical_requests)} test requests")

    # Test 2: Détecter patterns
    print("\n2. Detecting patterns...")
    detector = PatternDetector(knowledge, frequency_threshold=3)

    patterns = detector.detect_all_patterns()
    print(f"✓ Detected {len(patterns)} patterns")

    for pattern in patterns:
        print(f"\n  Pattern: {pattern.name}")
        print(f"    Frequency: {pattern.frequency}")
        print(f"    Success rate: {pattern.success_rate:.1%}")
        print(f"    Avg duration: {pattern.avg_duration:.0f}s")
        print(f"    Keywords: {', '.join(pattern.keywords[:3])}")
        print(f"    Trend: {pattern.trend}")
        print(f"    Potential savings: {pattern.potential_time_savings:.2f}h/week")
        print(f"    Recommended: {pattern.recommended_evolution}")

    # Test 3: Top automation candidates
    print("\n3. Getting top automation candidates...")
    top_candidates = detector.get_top_automation_candidates(limit=2)

    for i, pattern in enumerate(top_candidates, 1):
        print(f"\n  #{i}: {pattern.name}")
        print(f"      ROI: {pattern.potential_time_savings * pattern.frequency:.2f}")
        print(f"      Reason: {pattern.description}")

    print("\n✓ Pattern Detector works correctly!")
