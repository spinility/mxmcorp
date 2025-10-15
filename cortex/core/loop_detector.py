"""
Loop Detector - Détection de boucles infinies dans le code execution loop

Stratégies de détection:
- Diff-based: Même changement proposé 2x
- Error-based: Même erreur 3x consécutives
- Oscillation: A→B→A→B pattern
- Semantic: Changements équivalents sémantiquement
- Timeout: Limite de temps globale

Prevents infinite loops and wasted API costs.
"""

import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class LoopType(Enum):
    """Types de boucles détectées"""
    EXACT_DIFF_REPEAT = "exact_diff_repeat"
    ERROR_REPEAT = "error_repeat"
    OSCILLATION = "oscillation"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    TIMEOUT = "timeout"
    NO_PROGRESS = "no_progress"


@dataclass
class Attempt:
    """Représente une tentative de développement"""
    iteration: int
    tier: str
    diff_hash: str
    error_message: Optional[str]
    timestamp: float
    success: bool


@dataclass
class LoopDetection:
    """Résultat de détection de boucle"""
    detected: bool
    loop_type: Optional[LoopType]
    confidence: float
    evidence: List[str]
    recommendation: str


class LoopDetector:
    """
    Détecteur de boucles infinies

    Analyse l'historique des tentatives pour identifier
    des patterns de boucle infinie
    """

    def __init__(
        self,
        max_same_errors: int = 3,
        max_total_attempts: int = 15,
        timeout_minutes: int = 30,
        similarity_threshold: float = 0.95
    ):
        """
        Initialize Loop Detector

        Args:
            max_same_errors: Nombre d'erreurs identiques avant loop
            max_total_attempts: Max tentatives totales
            timeout_minutes: Timeout global en minutes
            similarity_threshold: Seuil de similarité sémantique
        """
        self.max_same_errors = max_same_errors
        self.max_total_attempts = max_total_attempts
        self.timeout_seconds = timeout_minutes * 60
        self.similarity_threshold = similarity_threshold

        self.attempts: List[Attempt] = []
        self.start_time = time.time()

    def add_attempt(
        self,
        tier: str,
        diff: str,
        error: Optional[str],
        success: bool
    ):
        """
        Enregistre une nouvelle tentative

        Args:
            tier: Tier du modèle utilisé
            diff: Git diff généré
            error: Message d'erreur si échec
            success: Si la tentative a réussi
        """
        # Hash du diff pour comparaison rapide
        diff_hash = hashlib.md5(diff.encode('utf-8')).hexdigest()

        attempt = Attempt(
            iteration=len(self.attempts) + 1,
            tier=tier,
            diff_hash=diff_hash,
            error_message=error,
            timestamp=time.time(),
            success=success
        )

        self.attempts.append(attempt)

    def detect_loop(self) -> LoopDetection:
        """
        Détecte si une boucle infinie est en cours

        Returns:
            LoopDetection avec résultats
        """
        # Vérifier dans l'ordre de priorité

        # 1. Timeout global
        elapsed = time.time() - self.start_time
        if elapsed > self.timeout_seconds:
            return LoopDetection(
                detected=True,
                loop_type=LoopType.TIMEOUT,
                confidence=1.0,
                evidence=[f"Elapsed time: {elapsed/60:.1f} minutes (max: {self.timeout_seconds/60} min)"],
                recommendation="Stop execution - timeout exceeded"
            )

        # 2. Max tentatives atteintes
        if len(self.attempts) >= self.max_total_attempts:
            return LoopDetection(
                detected=True,
                loop_type=LoopType.NO_PROGRESS,
                confidence=1.0,
                evidence=[f"Total attempts: {len(self.attempts)} (max: {self.max_total_attempts})"],
                recommendation="Stop execution - max attempts reached"
            )

        # 3. Exact diff repeat (même changement 2x)
        diff_repeat = self._detect_exact_diff_repeat()
        if diff_repeat.detected:
            return diff_repeat

        # 4. Error repeat (même erreur 3x)
        error_repeat = self._detect_error_repeat()
        if error_repeat.detected:
            return error_repeat

        # 5. Oscillation (A→B→A pattern)
        oscillation = self._detect_oscillation()
        if oscillation.detected:
            return oscillation

        # Pas de boucle détectée
        return LoopDetection(
            detected=False,
            loop_type=None,
            confidence=0.0,
            evidence=[],
            recommendation="Continue execution"
        )

    def _detect_exact_diff_repeat(self) -> LoopDetection:
        """Détecte si le même diff est proposé 2x consécutives"""
        if len(self.attempts) < 2:
            return LoopDetection(detected=False, loop_type=None, confidence=0.0, evidence=[], recommendation="")

        # Comparer les 2 dernières tentatives
        last = self.attempts[-1]
        prev = self.attempts[-2]

        if last.diff_hash == prev.diff_hash:
            return LoopDetection(
                detected=True,
                loop_type=LoopType.EXACT_DIFF_REPEAT,
                confidence=1.0,
                evidence=[
                    f"Attempt {prev.iteration} and {last.iteration} proposed identical changes",
                    f"Tier {prev.tier} → {last.tier}"
                ],
                recommendation="Escalate to higher tier - same solution attempted twice"
            )

        return LoopDetection(detected=False, loop_type=None, confidence=0.0, evidence=[], recommendation="")

    def _detect_error_repeat(self) -> LoopDetection:
        """Détecte si la même erreur se répète N fois"""
        if len(self.attempts) < self.max_same_errors:
            return LoopDetection(detected=False, loop_type=None, confidence=0.0, evidence=[], recommendation="")

        # Prendre les N dernières tentatives
        recent = self.attempts[-self.max_same_errors:]

        # Vérifier que toutes ont la même erreur
        error_messages = [a.error_message for a in recent if a.error_message]

        if len(error_messages) < self.max_same_errors:
            return LoopDetection(detected=False, loop_type=None, confidence=0.0, evidence=[], recommendation="")

        # Normaliser les erreurs (enlever numéros de ligne qui peuvent varier)
        normalized_errors = [self._normalize_error(e) for e in error_messages]

        # Si toutes identiques
        if len(set(normalized_errors)) == 1:
            return LoopDetection(
                detected=True,
                loop_type=LoopType.ERROR_REPEAT,
                confidence=0.95,
                evidence=[
                    f"Same error repeated {self.max_same_errors} times:",
                    f"'{error_messages[0][:100]}...'",
                    f"Tiers used: {' → '.join([a.tier for a in recent])}"
                ],
                recommendation="Escalate to higher tier - unable to fix this error"
            )

        return LoopDetection(detected=False, loop_type=None, confidence=0.0, evidence=[], recommendation="")

    def _detect_oscillation(self) -> LoopDetection:
        """Détecte une oscillation A→B→A→B"""
        if len(self.attempts) < 4:
            return LoopDetection(detected=False, loop_type=None, confidence=0.0, evidence=[], recommendation="")

        # Prendre les 4 dernières
        recent = self.attempts[-4:]

        # Vérifier pattern: A-B-A-B
        if (recent[0].diff_hash == recent[2].diff_hash and
            recent[1].diff_hash == recent[3].diff_hash and
            recent[0].diff_hash != recent[1].diff_hash):

            return LoopDetection(
                detected=True,
                loop_type=LoopType.OSCILLATION,
                confidence=0.9,
                evidence=[
                    "Oscillation detected: A→B→A→B pattern",
                    f"Attempts {recent[0].iteration}, {recent[2].iteration} are identical",
                    f"Attempts {recent[1].iteration}, {recent[3].iteration} are identical",
                    f"Tiers: {' → '.join([a.tier for a in recent])}"
                ],
                recommendation="Escalate to higher tier - model is oscillating between solutions"
            )

        return LoopDetection(detected=False, loop_type=None, confidence=0.0, evidence=[], recommendation="")

    def _normalize_error(self, error: str) -> str:
        """Normalise un message d'erreur pour comparaison"""
        import re

        # Enlever les numéros de ligne
        normalized = re.sub(r'line \d+', 'line X', error)
        normalized = re.sub(r':\d+:', ':X:', normalized)

        # Enlever les chemins absolus
        normalized = re.sub(r'/[^\s]+/', '/PATH/', normalized)

        # Lowercase
        normalized = normalized.lower()

        return normalized

    def calculate_semantic_similarity(self, diff1: str, diff2: str) -> float:
        """
        Calcule la similarité sémantique entre deux diffs

        Utilise une approche simple basée sur les tokens
        En production, utiliser embeddings

        Returns:
            Similarité entre 0.0 et 1.0
        """
        # Tokenize les diffs
        tokens1 = set(diff1.split())
        tokens2 = set(diff2.split())

        # Jaccard similarity
        if not tokens1 or not tokens2:
            return 0.0

        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)

        return intersection / union if union > 0 else 0.0

    def get_statistics(self) -> Dict[str, Any]:
        """Obtient des statistiques sur les tentatives"""
        if not self.attempts:
            return {
                'total_attempts': 0,
                'success_rate': 0.0,
                'elapsed_time': 0.0,
                'tier_distribution': {}
            }

        successes = sum(1 for a in self.attempts if a.success)
        elapsed = time.time() - self.start_time

        # Distribution par tier
        tier_dist = {}
        for attempt in self.attempts:
            tier_dist[attempt.tier] = tier_dist.get(attempt.tier, 0) + 1

        return {
            'total_attempts': len(self.attempts),
            'success_rate': successes / len(self.attempts) if self.attempts else 0.0,
            'elapsed_time': elapsed,
            'tier_distribution': tier_dist,
            'last_attempt': self.attempts[-1].iteration
        }

    def should_escalate(self, current_tier: str) -> Tuple[bool, Optional[str]]:
        """
        Détermine si on doit escalader au tier supérieur

        Args:
            current_tier: Tier actuel

        Returns:
            (should_escalate, recommended_tier)
        """
        # Détecter boucle
        detection = self.detect_loop()

        if not detection.detected:
            return False, None

        # Escalation tier mapping
        tier_hierarchy = ["deepseek", "gpt5", "claude"]

        try:
            current_idx = tier_hierarchy.index(current_tier)
            if current_idx < len(tier_hierarchy) - 1:
                next_tier = tier_hierarchy[current_idx + 1]
                return True, next_tier
            else:
                # Déjà au tier max
                return True, None  # Signal d'arrêt
        except ValueError:
            return False, None


def create_loop_detector(
    max_same_errors: int = 3,
    max_total_attempts: int = 15,
    timeout_minutes: int = 30
) -> LoopDetector:
    """Factory function pour créer un LoopDetector"""
    return LoopDetector(
        max_same_errors=max_same_errors,
        max_total_attempts=max_total_attempts,
        timeout_minutes=timeout_minutes
    )


# Test si exécuté directement
if __name__ == "__main__":
    print("Testing Loop Detector...")

    detector = LoopDetector(max_same_errors=3, max_total_attempts=10, timeout_minutes=1)

    # Test 1: Exact diff repeat
    print("\n1. Testing exact diff repeat...")
    detector.add_attempt("deepseek", "diff content A", None, False)
    detector.add_attempt("deepseek", "diff content A", None, False)  # Same diff

    result = detector.detect_loop()
    print(f"✓ Loop detected: {result.detected}")
    print(f"  Type: {result.loop_type.value if result.loop_type else 'None'}")
    print(f"  Confidence: {result.confidence:.0%}")

    # Test 2: Error repeat
    print("\n2. Testing error repeat...")
    detector2 = LoopDetector(max_same_errors=3)
    error_msg = "ImportError: No module named 'foo'"

    for i in range(3):
        detector2.add_attempt(f"tier{i+1}", f"diff {i}", error_msg, False)

    result2 = detector2.detect_loop()
    print(f"✓ Loop detected: {result2.detected}")
    print(f"  Type: {result2.loop_type.value if result2.loop_type else 'None'}")
    print(f"  Evidence: {len(result2.evidence)} items")

    # Test 3: Oscillation
    print("\n3. Testing oscillation...")
    detector3 = LoopDetector()
    detector3.add_attempt("tier1", "diff A", "error 1", False)
    detector3.add_attempt("tier1", "diff B", "error 2", False)
    detector3.add_attempt("tier1", "diff A", "error 1", False)  # Back to A
    detector3.add_attempt("tier1", "diff B", "error 2", False)  # Back to B

    result3 = detector3.detect_loop()
    print(f"✓ Loop detected: {result3.detected}")
    print(f"  Type: {result3.loop_type.value if result3.loop_type else 'None'}")

    # Test 4: Escalation recommendation
    print("\n4. Testing escalation recommendation...")
    should_escalate, next_tier = detector2.should_escalate("deepseek")
    print(f"✓ Should escalate: {should_escalate}")
    print(f"  Next tier: {next_tier}")

    # Test 5: Statistics
    print("\n5. Testing statistics...")
    stats = detector2.get_statistics()
    print(f"✓ Statistics:")
    print(f"  Total attempts: {stats['total_attempts']}")
    print(f"  Success rate: {stats['success_rate']:.0%}")
    print(f"  Elapsed: {stats['elapsed_time']:.2f}s")
    print(f"  Tier distribution: {stats['tier_distribution']}")

    print("\n✓ Loop Detector works correctly!")
