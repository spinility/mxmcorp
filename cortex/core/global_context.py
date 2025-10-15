"""
Global Context - Context ultra-léger partagé entre tous les agents

IMPORTANT: Ce context est conçu pour être MINIMAL pour réduire les coûts.
Il contient seulement l'information ESSENTIELLE que les agents consultent fréquemment.

Principe:
- Lightweight (< 500 tokens total)
- Consultable sans coût (cached agressivement)
- Mis à jour rarement
- Contient seulement ce qui change ou ce qui est critique
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import json


@dataclass
class SystemStatus:
    """Statut système ultra-compact"""
    health_score: float  # 0-100
    active_agents: int
    total_tasks_today: int
    total_cost_today: float
    last_updated: str


@dataclass
class QuickFacts:
    """Facts rapides et souvent consultés"""
    model_prices: Dict[str, Dict[str, float]]  # {nano: {input: 0.05, output: 0.40}}
    available_tools_count: int
    system_mode: str  # "normal", "cost_saving", "high_performance"


@dataclass
class GlobalContext:
    """
    Context global ultra-léger

    RÈGLE: Garder < 500 tokens total
    Ce context est ajouté au prompt des agents seulement si nécessaire
    """
    system_status: SystemStatus
    quick_facts: QuickFacts
    current_priorities: list = field(default_factory=list)  # Max 3 priorités
    recent_issues: list = field(default_factory=list)  # Max 3 issues récents

    def to_compact_str(self) -> str:
        """
        Génère une représentation ultra-compacte (< 200 tokens)

        Format optimisé pour économiser les tokens
        """
        lines = [
            f"[SYSTEM] Health:{self.system_status.health_score:.0f}/100 | Agents:{self.system_status.active_agents} | Tasks:{self.system_status.total_tasks_today} | Cost:${self.system_status.total_cost_today:.4f}",
            f"[PRICES] nano:${self.quick_facts.model_prices['nano']['input']}/{self.quick_facts.model_prices['nano']['output']} deepseek:${self.quick_facts.model_prices['deepseek']['input']}/{self.quick_facts.model_prices['deepseek']['output']} claude:${self.quick_facts.model_prices['claude']['input']}/{self.quick_facts.model_prices['claude']['output']}",
            f"[MODE] {self.quick_facts.system_mode} | Tools:{self.quick_facts.available_tools_count}"
        ]

        if self.current_priorities:
            lines.append(f"[PRIORITIES] {', '.join(self.current_priorities[:3])}")

        if self.recent_issues:
            lines.append(f"[ISSUES] {', '.join(self.recent_issues[:3])}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "system_status": asdict(self.system_status),
            "quick_facts": asdict(self.quick_facts),
            "current_priorities": self.current_priorities,
            "recent_issues": self.recent_issues
        }


class GlobalContextManager:
    """
    Gestionnaire du context global

    Responsabilités:
    - Charger/sauvegarder le context
    - Fournir le context aux agents (en version compacte)
    - Mettre à jour le context sans surcoût
    """

    def __init__(self, context_file: Optional[Path] = None):
        if context_file is None:
            context_file = Path(__file__).parent.parent / "data" / "global_context.json"

        self.context_file = context_file
        self.context: Optional[GlobalContext] = None

        # Charger ou initialiser
        if self.context_file.exists():
            self.load()
        else:
            self._initialize_default()
            self.save()

    def _initialize_default(self):
        """Initialise un context par défaut"""
        self.context = GlobalContext(
            system_status=SystemStatus(
                health_score=100.0,
                active_agents=0,
                total_tasks_today=0,
                total_cost_today=0.0,
                last_updated=datetime.now().isoformat()
            ),
            quick_facts=QuickFacts(
                model_prices={
                    "nano": {"input": 0.05, "output": 0.40},
                    "deepseek": {"input": 0.28, "output": 0.42},
                    "claude": {"input": 3.0, "output": 15.0}
                },
                available_tools_count=10,
                system_mode="normal"
            ),
            current_priorities=[],
            recent_issues=[]
        )

    def get_context(self, compact: bool = True) -> str:
        """
        Récupère le context

        Args:
            compact: Si True, retourne version ultra-compacte (< 200 tokens)

        Returns:
            Context string à inclure dans le prompt
        """
        if self.context is None:
            self.load()

        if compact:
            return self.context.to_compact_str()
        else:
            return json.dumps(self.context.to_dict(), indent=2)

    def update_status(self, **kwargs):
        """Met à jour le statut système"""
        if self.context is None:
            self.load()

        for key, value in kwargs.items():
            if hasattr(self.context.system_status, key):
                setattr(self.context.system_status, key, value)

        self.context.system_status.last_updated = datetime.now().isoformat()
        self.save()

    def update_prices(self, prices: Dict[str, Dict[str, float]]):
        """Met à jour les prix des modèles"""
        if self.context is None:
            self.load()

        self.context.quick_facts.model_prices.update(prices)
        self.save()

    def set_system_mode(self, mode: str):
        """Change le mode système"""
        if self.context is None:
            self.load()

        self.context.quick_facts.system_mode = mode
        self.save()

    def add_priority(self, priority: str):
        """Ajoute une priorité (max 3)"""
        if self.context is None:
            self.load()

        if priority not in self.context.current_priorities:
            self.context.current_priorities.insert(0, priority)
            # Garder seulement les 3 plus récentes
            self.context.current_priorities = self.context.current_priorities[:3]
            self.save()

    def add_issue(self, issue: str):
        """Ajoute un issue récent (max 3)"""
        if self.context is None:
            self.load()

        if issue not in self.context.recent_issues:
            self.context.recent_issues.insert(0, issue)
            # Garder seulement les 3 plus récents
            self.context.recent_issues = self.context.recent_issues[:3]
            self.save()

    def clear_issues(self):
        """Efface les issues (quand résolus)"""
        if self.context is None:
            self.load()

        self.context.recent_issues = []
        self.save()

    def load(self):
        """Charge le context depuis le fichier"""
        with open(self.context_file, 'r') as f:
            data = json.load(f)

        self.context = GlobalContext(
            system_status=SystemStatus(**data["system_status"]),
            quick_facts=QuickFacts(**data["quick_facts"]),
            current_priorities=data.get("current_priorities", []),
            recent_issues=data.get("recent_issues", [])
        )

    def save(self):
        """Sauvegarde le context dans le fichier"""
        if self.context is None:
            return

        # Créer le dossier si nécessaire
        self.context_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.context_file, 'w') as f:
            json.dump(self.context.to_dict(), f, indent=2)

    def get_token_count_estimate(self) -> int:
        """Estime le nombre de tokens du context compact"""
        compact = self.get_context(compact=True)
        # Estimation rough: 1 token ≈ 4 chars
        return len(compact) // 4

    def should_include_in_prompt(self, agent_role: str) -> bool:
        """
        Détermine si le context doit être inclus dans le prompt

        Principe: Seulement les agents qui en ont besoin
        - CEO: Oui (décisions stratégiques)
        - Directors: Oui (coordination)
        - Managers: Parfois (si délégation)
        - Workers: Non (économie)
        """
        include_roles = {"CEO", "Director", "Manager", "Meta-Architect", "Data Manager"}
        return agent_role in include_roles


# Instance globale
_global_context_manager: Optional[GlobalContextManager] = None


def get_global_context() -> GlobalContextManager:
    """Récupère l'instance globale du context manager"""
    global _global_context_manager
    if _global_context_manager is None:
        _global_context_manager = GlobalContextManager()
    return _global_context_manager


if __name__ == "__main__":
    # Test
    manager = GlobalContextManager()

    print("=== GLOBAL CONTEXT (COMPACT) ===")
    print(manager.get_context(compact=True))

    print(f"\n=== TOKEN ESTIMATE ===")
    print(f"Estimated tokens: {manager.get_token_count_estimate()}")

    print("\n=== UPDATING STATUS ===")
    manager.update_status(
        health_score=85.0,
        active_agents=5,
        total_tasks_today=42,
        total_cost_today=0.1234
    )

    print("\n=== ADDING PRIORITY ===")
    manager.add_priority("Reduce costs")
    manager.add_priority("Improve success rate")

    print("\n=== ADDING ISSUE ===")
    manager.add_issue("Database timeout (3x)")

    print("\n=== UPDATED CONTEXT ===")
    print(manager.get_context(compact=True))

    print(f"\n=== SHOULD INCLUDE IN PROMPT? ===")
    for role in ["CEO", "Director", "Manager", "Worker"]:
        should = manager.should_include_in_prompt(role)
        print(f"  {role}: {'YES' if should else 'NO'}")

    print("\n=== FULL CONTEXT (JSON) ===")
    print(manager.get_context(compact=False))
