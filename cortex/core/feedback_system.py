"""
Feedback System - Retour utilisateur sur l'exécution des tools et tâches
Système léger et non-intrusif pour informer l'utilisateur
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class FeedbackLevel(Enum):
    """Niveaux de feedback"""
    SUCCESS = "✓"
    INFO = "ℹ"
    WARNING = "⚠"
    ERROR = "✗"
    PROGRESS = "→"


@dataclass
class FeedbackMessage:
    """Message de feedback"""
    level: FeedbackLevel
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def format(self, verbose: bool = False) -> str:
        """Formate le message pour affichage"""
        base = f"{self.level.value} {self.message}"

        if verbose and self.details:
            details_str = "\n".join([f"  {k}: {v}" for k, v in self.details.items()])
            return f"{base}\n{details_str}"

        return base


class FeedbackCollector:
    """
    Collecte et formate les messages de feedback
    Thread-safe et léger
    """

    def __init__(self, max_messages: int = 100):
        self.messages: List[FeedbackMessage] = []
        self.max_messages = max_messages

    def add(
        self,
        level: FeedbackLevel,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Ajoute un message de feedback"""
        msg = FeedbackMessage(level=level, message=message, details=details)
        self.messages.append(msg)

        # Limiter la taille
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

        return msg

    def success(self, message: str, **details):
        """Feedback de succès"""
        return self.add(FeedbackLevel.SUCCESS, message, details or None)

    def info(self, message: str, **details):
        """Feedback d'information"""
        return self.add(FeedbackLevel.INFO, message, details or None)

    def warning(self, message: str, **details):
        """Feedback d'avertissement"""
        return self.add(FeedbackLevel.WARNING, message, details or None)

    def error(self, message: str, **details):
        """Feedback d'erreur"""
        return self.add(FeedbackLevel.ERROR, message, details or None)

    def progress(self, message: str, **details):
        """Feedback de progression"""
        return self.add(FeedbackLevel.PROGRESS, message, details or None)

    def get_recent(self, count: int = 10) -> List[FeedbackMessage]:
        """Récupère les N derniers messages"""
        return self.messages[-count:]

    def get_by_level(self, level: FeedbackLevel) -> List[FeedbackMessage]:
        """Récupère les messages d'un niveau spécifique"""
        return [msg for msg in self.messages if msg.level == level]

    def clear(self):
        """Efface tous les messages"""
        self.messages.clear()

    def format_all(self, verbose: bool = False) -> str:
        """Formate tous les messages"""
        return "\n".join([msg.format(verbose) for msg in self.messages])

    def format_recent(self, count: int = 10, verbose: bool = False) -> str:
        """Formate les N derniers messages"""
        recent = self.get_recent(count)
        return "\n".join([msg.format(verbose) for msg in recent])


# Instance globale
_global_feedback: Optional[FeedbackCollector] = None


def get_feedback() -> FeedbackCollector:
    """Récupère l'instance globale de feedback"""
    global _global_feedback
    if _global_feedback is None:
        _global_feedback = FeedbackCollector()
    return _global_feedback


def feedback_success(message: str, **details):
    """Shortcut pour feedback de succès"""
    return get_feedback().success(message, **details)


def feedback_info(message: str, **details):
    """Shortcut pour feedback d'information"""
    return get_feedback().info(message, **details)


def feedback_warning(message: str, **details):
    """Shortcut pour feedback d'avertissement"""
    return get_feedback().warning(message, **details)


def feedback_error(message: str, **details):
    """Shortcut pour feedback d'erreur"""
    return get_feedback().error(message, **details)


def feedback_progress(message: str, **details):
    """Shortcut pour feedback de progression"""
    return get_feedback().progress(message, **details)


if __name__ == "__main__":
    # Test
    feedback = FeedbackCollector()

    feedback.success("Tool 'read_file' executed successfully", file="test.txt", lines=42)
    feedback.progress("Processing data...", progress=50, total=100)
    feedback.warning("Cache miss, fetching from API", cache_key="model_prices")
    feedback.error("Failed to connect to database", error="Connection timeout")
    feedback.info("Using fallback model", model="nano", reason="Cost optimization")

    print("=== All Messages ===")
    print(feedback.format_all())

    print("\n=== Verbose Mode ===")
    print(feedback.format_all(verbose=True))

    print("\n=== Errors Only ===")
    errors = feedback.get_by_level(FeedbackLevel.ERROR)
    for err in errors:
        print(err.format(verbose=True))
