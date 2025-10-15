"""
Base Tool - Classe de base pour tous les outils
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class ToolMetadata:
    """Métadonnées d'un outil"""
    name: str
    description: str
    version: str
    author: str  # "human" ou "ai_generated"
    created_at: datetime
    category: str  # "filesystem", "web", "database", "code", etc.
    tags: list
    cost_estimate: str  # "free", "low", "medium", "high"


@dataclass
class ToolResult:
    """Résultat de l'exécution d'un outil"""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Optional[Dict] = None


class BaseTool(ABC):
    """
    Classe de base pour tous les outils du Cortex

    Chaque outil doit:
    - Avoir des métadonnées claires
    - Implémenter execute()
    - Gérer les erreurs proprement
    - Être testable
    """

    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata
        self.usage_count = 0
        self.total_execution_time = 0.0
        self.error_count = 0

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Exécute l'outil avec les paramètres fournis

        Args:
            **kwargs: Paramètres spécifiques à l'outil

        Returns:
            ToolResult avec succès/échec et données
        """
        pass

    @abstractmethod
    def validate_params(self, **kwargs) -> Tuple[bool, Optional[str]]:
        """
        Valide les paramètres avant exécution

        Returns:
            (valide: bool, erreur: Optional[str])
        """
        pass

    def run(self, **kwargs) -> ToolResult:
        """
        Wrapper qui gère validation, exécution, et tracking
        """
        import time

        # Valider les paramètres
        valid, error = self.validate_params(**kwargs)
        if not valid:
            self.error_count += 1
            return ToolResult(
                success=False,
                data=None,
                error=f"Validation error: {error}"
            )

        # Exécuter
        start_time = time.time()
        try:
            result = self.execute(**kwargs)
            execution_time = time.time() - start_time

            # Tracking
            self.usage_count += 1
            self.total_execution_time += execution_time
            result.execution_time = execution_time

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.error_count += 1

            return ToolResult(
                success=False,
                data=None,
                error=f"Execution error: {str(e)}",
                execution_time=execution_time
            )

    def get_stats(self) -> Dict:
        """Récupère les statistiques d'utilisation"""
        avg_time = (
            self.total_execution_time / self.usage_count
            if self.usage_count > 0
            else 0
        )

        error_rate = (
            self.error_count / self.usage_count
            if self.usage_count > 0
            else 0
        )

        return {
            "name": self.metadata.name,
            "usage_count": self.usage_count,
            "error_count": self.error_count,
            "error_rate": error_rate,
            "total_execution_time": self.total_execution_time,
            "avg_execution_time": avg_time
        }

    def to_dict(self) -> Dict:
        """Sérialise l'outil en dictionnaire"""
        return {
            "metadata": {
                "name": self.metadata.name,
                "description": self.metadata.description,
                "version": self.metadata.version,
                "author": self.metadata.author,
                "created_at": self.metadata.created_at.isoformat(),
                "category": self.metadata.category,
                "tags": self.metadata.tags,
                "cost_estimate": self.metadata.cost_estimate
            },
            "stats": self.get_stats()
        }

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.metadata.name}' v{self.metadata.version}>"
