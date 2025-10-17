"""
Agent Hierarchy System - Base classes for 4-level organizational structure

Hiérarchie:
1. AGENT (Exécution) - Tier: Nano
2. EXPERT (Analyse) - Tier: DeepSeek
3. DIRECTEUR (Décision) - Tier: GPT-5
4. CORTEX_CENTRAL (Coordination) - Tier: Claude 4.5

Principe: AgentFirst - Toute requête démarre au niveau AGENT et escalade si nécessaire
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import time

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier
from cortex.database import get_database_manager


class AgentRole(Enum):
    """Rôles hiérarchiques des agents"""
    AGENT = "agent"                    # Niveau 1: Exécution (nano)
    EXPERT = "expert"                  # Niveau 2: Analyse (deepseek)
    DIRECTEUR = "directeur"            # Niveau 3: Décision (gpt5)
    CORTEX_CENTRAL = "cortex_central"  # Niveau 4: Coordination (claude)


class RequestComplexity(Enum):
    """Complexité d'une requête"""
    TRIVIAL = 0      # AGENT direct
    SIMPLE = 1       # AGENT avec escalation possible
    MODERATE = 2     # EXPERT direct
    COMPLEX = 3      # EXPERT avec escalation possible
    CRITICAL = 4     # DIRECTEUR direct
    STRATEGIC = 5    # CORTEX CENTRAL direct


@dataclass
class AgentResult:
    """Résultat d'exécution d'un agent"""
    success: bool
    role: AgentRole
    tier: ModelTier
    content: Any
    cost: float
    confidence: float
    should_escalate: bool = False
    escalation_reason: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class EscalationContext:
    """Contexte pour escalation au niveau supérieur"""
    original_request: str
    previous_role: AgentRole
    previous_tier: ModelTier
    attempts: int
    errors: List[str]
    partial_results: List[Any]
    total_cost: float


class BaseAgent(ABC):
    """
    Classe de base pour tous les agents hiérarchiques

    Chaque agent:
    - A un rôle défini (AGENT, EXPERT, DIRECTEUR, CORTEX)
    - Utilise un tier LLM spécifique
    - Peut juger s'il peut gérer une requête
    - Peut exécuter une requête
    - Peut décider s'il faut escalader
    """

    def __init__(
        self,
        llm_client: LLMClient,
        role: AgentRole,
        tier: ModelTier,
        max_attempts: int = 3,
        escalation_threshold: float = 0.7
    ):
        """
        Initialize Base Agent

        Args:
            llm_client: Client LLM
            role: Rôle de l'agent dans la hiérarchie
            tier: Tier LLM à utiliser
            max_attempts: Nombre max de tentatives
            escalation_threshold: Seuil de confidence pour escalation
        """
        self.llm_client = llm_client
        self.role = role
        self.tier = tier
        self.max_attempts = max_attempts
        self.escalation_threshold = escalation_threshold
        self.execution_history: List[AgentResult] = []

        # Intelligence Database pour auto-tracking
        try:
            self.db = get_database_manager()
        except Exception as e:
            # Si DB non disponible, continuer sans tracking
            self.db = None
            import warnings
            warnings.warn(f"Database not available for agent tracking: {e}")

    @abstractmethod
    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """
        Évalue si l'agent peut gérer cette requête

        Args:
            request: Requête utilisateur
            context: Contexte additionnel

        Returns:
            Score de confidence (0.0-1.0)
        """
        pass

    @abstractmethod
    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[EscalationContext] = None
    ) -> AgentResult:
        """
        Exécute la requête

        Args:
            request: Requête utilisateur
            context: Contexte additionnel
            escalation_context: Contexte si escalation

        Returns:
            AgentResult avec résultat
        """
        pass

    def should_escalate(self, result: AgentResult) -> bool:
        """
        Détermine si on doit escalader au niveau supérieur

        Args:
            result: Résultat de l'exécution

        Returns:
            True si escalation nécessaire
        """
        # Escalader si échec
        if not result.success:
            return True

        # Escalader si confidence trop basse
        if result.confidence < self.escalation_threshold:
            return True

        # Escalader si explicitement demandé
        if result.should_escalate:
            return True

        return False

    def get_escalation_context(self, request: str, result: AgentResult) -> EscalationContext:
        """Prépare le contexte pour escalation"""
        errors = [result.error] if result.error else []
        partial_results = [result.content] if result.content else []

        return EscalationContext(
            original_request=request,
            previous_role=self.role,
            previous_tier=self.tier,
            attempts=len(self.execution_history),
            errors=errors,
            partial_results=partial_results,
            total_cost=sum(r.cost for r in self.execution_history)
        )

    def _track_execution(self, result: AgentResult, response_time: float):
        """
        Track agent execution metrics dans la base de données
        Appelé automatiquement après chaque execute()

        Args:
            result: Résultat de l'exécution
            response_time: Temps de réponse en secondes
        """
        if self.db is None:
            return  # Pas de DB disponible

        try:
            # Obtenir le nom de la classe (ex: TriageAgent, TaskExecutor)
            agent_name = self.__class__.__name__

            # Tracker les métriques
            self.db.update_agent_metrics(
                agent_name=agent_name,
                cost=result.cost,
                response_time=response_time,
                success=result.success
            )
        except Exception as e:
            # Ne pas bloquer l'exécution si tracking échoue
            import warnings
            warnings.warn(f"Failed to track agent execution: {e}")

    def execute_with_tracking(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[EscalationContext] = None
    ) -> AgentResult:
        """
        Wrapper autour de execute() qui track automatiquement les métriques
        Utilisez cette méthode au lieu de execute() directement
        """
        start_time = time.time()

        # Exécuter la requête
        result = self.execute(request, context, escalation_context)

        # Calculer le temps de réponse
        response_time = time.time() - start_time

        # Ajouter à l'historique
        self.execution_history.append(result)

        # Tracker dans la DB automatiquement
        self._track_execution(result, response_time)

        return result


class ExecutionAgent(BaseAgent):
    """
    Agent de niveau 1: AGENT (Exécution)

    Responsabilités:
    - Tâches simples et répétitives
    - Validation et tests
    - Parsing et extraction
    - Classification et routing

    Tier: Nano (~$0.0001 / 1M tokens)
    """

    def __init__(
        self,
        llm_client: LLMClient,
        specialization: Optional[str] = None
    ):
        super().__init__(
            llm_client=llm_client,
            role=AgentRole.AGENT,
            tier=ModelTier.NANO,
            max_attempts=2,
            escalation_threshold=0.7
        )
        self.specialization = specialization

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """Évalue si tâche simple/répétitive"""
        # Patterns que les agents d'exécution peuvent gérer
        simple_patterns = [
            'validate', 'check', 'test', 'parse', 'extract',
            'list', 'show', 'display', 'get', 'read',
            'classify', 'route', 'count', 'find'
        ]

        request_lower = request.lower()
        matches = sum(1 for pattern in simple_patterns if pattern in request_lower)

        # Plus de matches = plus de confidence
        confidence = min(matches / 3.0, 1.0)

        # Bonus si correspond à spécialisation
        if self.specialization and self.specialization in request_lower:
            confidence = min(confidence + 0.3, 1.0)

        return confidence

    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[EscalationContext] = None
    ) -> AgentResult:
        """Exécute avec nano tier"""
        # Implementation sera fournie par sous-classes spécialisées
        return AgentResult(
            success=False,
            role=self.role,
            tier=self.tier,
            content=None,
            cost=0.0,
            confidence=0.0,
            should_escalate=True,
            escalation_reason="Base ExecutionAgent not specialized"
        )


class AnalysisAgent(BaseAgent):
    """
    Agent de niveau 2: EXPERT (Analyse)

    Responsabilités:
    - Analyse de code complexe
    - Génération de code standard
    - Refactoring localisé
    - Debugging et investigation

    Tier: DeepSeek (~$0.14-0.28 / 1M tokens)
    """

    def __init__(
        self,
        llm_client: LLMClient,
        specialization: Optional[str] = None
    ):
        super().__init__(
            llm_client=llm_client,
            role=AgentRole.EXPERT,
            tier=ModelTier.DEEPSEEK,
            max_attempts=3,
            escalation_threshold=0.6
        )
        self.specialization = specialization

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """Évalue si analyse/génération de code"""
        moderate_patterns = [
            'analyze', 'implement', 'create', 'generate',
            'refactor', 'fix', 'debug', 'optimize',
            'explain', 'investigate', 'improve'
        ]

        request_lower = request.lower()
        matches = sum(1 for pattern in moderate_patterns if pattern in request_lower)

        confidence = min(matches / 2.0, 1.0)

        if self.specialization and self.specialization in request_lower:
            confidence = min(confidence + 0.2, 1.0)

        return confidence

    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[EscalationContext] = None
    ) -> AgentResult:
        """Exécute avec deepseek tier"""
        return AgentResult(
            success=False,
            role=self.role,
            tier=self.tier,
            content=None,
            cost=0.0,
            confidence=0.0,
            should_escalate=True,
            escalation_reason="Base AnalysisAgent not specialized"
        )


class DecisionAgent(BaseAgent):
    """
    Agent de niveau 3: DIRECTEUR (Décision)

    Responsabilités:
    - Décisions architecturales
    - Évaluation de trade-offs
    - Planning complexe
    - Design patterns

    Tier: GPT-5 (~$2.00-8.00 / 1M tokens)
    """

    def __init__(
        self,
        llm_client: LLMClient,
        specialization: Optional[str] = None
    ):
        super().__init__(
            llm_client=llm_client,
            role=AgentRole.DIRECTEUR,
            tier=ModelTier.GPT5,
            max_attempts=3,
            escalation_threshold=0.5
        )
        self.specialization = specialization

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """Évalue si décision/architecture"""
        critical_patterns = [
            'decide', 'choose', 'design', 'architect',
            'plan', 'strategy', 'evaluate', 'compare',
            'trade-off', 'recommend', 'assess'
        ]

        request_lower = request.lower()
        matches = sum(1 for pattern in critical_patterns if pattern in request_lower)

        confidence = min(matches / 2.0, 1.0)

        if self.specialization and self.specialization in request_lower:
            confidence = min(confidence + 0.2, 1.0)

        return confidence

    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[EscalationContext] = None
    ) -> AgentResult:
        """Exécute avec gpt5 tier"""
        return AgentResult(
            success=False,
            role=self.role,
            tier=self.tier,
            content=None,
            cost=0.0,
            confidence=0.0,
            should_escalate=True,
            escalation_reason="Base DecisionAgent not specialized"
        )


class CoordinationAgent(BaseAgent):
    """
    Agent de niveau 4: CORTEX CENTRAL (Coordination)

    Responsabilités:
    - Coordination de tous les agents
    - Vision système globale
    - Résolution de problèmes critiques
    - Innovation et créativité

    Tier: Claude 4.5 (~$3.00-15.00 / 1M tokens)
    """

    def __init__(
        self,
        llm_client: LLMClient,
        specialization: Optional[str] = None
    ):
        super().__init__(
            llm_client=llm_client,
            role=AgentRole.CORTEX_CENTRAL,
            tier=ModelTier.CLAUDE,
            max_attempts=2,
            escalation_threshold=0.0  # Pas d'escalation au-dessus
        )
        self.specialization = specialization

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """Cortex Central peut tout gérer (dernier niveau)"""
        return 1.0  # Toujours capable (c'est le dernier recours)

    def should_escalate(self, result: AgentResult) -> bool:
        """Cortex Central ne peut pas escalader plus haut"""
        return False  # Dernier niveau

    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[EscalationContext] = None
    ) -> AgentResult:
        """Exécute avec claude tier (maximum power)"""
        return AgentResult(
            success=False,
            role=self.role,
            tier=self.tier,
            content=None,
            cost=0.0,
            confidence=0.0,
            should_escalate=False,
            escalation_reason="Cortex Central is highest level"
        )


# Mapping rôle → tier
ROLE_TO_TIER = {
    AgentRole.AGENT: ModelTier.NANO,
    AgentRole.EXPERT: ModelTier.DEEPSEEK,
    AgentRole.DIRECTEUR: ModelTier.GPT5,
    AgentRole.CORTEX_CENTRAL: ModelTier.CLAUDE
}

# Hiérarchie d'escalation
ESCALATION_HIERARCHY = [
    AgentRole.AGENT,
    AgentRole.EXPERT,
    AgentRole.DIRECTEUR,
    AgentRole.CORTEX_CENTRAL
]


def get_next_role(current_role: AgentRole) -> Optional[AgentRole]:
    """Retourne le prochain rôle dans la hiérarchie"""
    try:
        current_idx = ESCALATION_HIERARCHY.index(current_role)
        if current_idx < len(ESCALATION_HIERARCHY) - 1:
            return ESCALATION_HIERARCHY[current_idx + 1]
    except ValueError:
        pass
    return None


# Test si exécuté directement
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    print("Testing Agent Hierarchy System...")

    client = LLMClient()

    # Test 1: Créer agents de chaque niveau
    print("\n1. Testing agent creation...")
    agent = ExecutionAgent(client, specialization="testing")
    expert = AnalysisAgent(client, specialization="development")
    directeur = DecisionAgent(client, specialization="architecture")
    cortex = CoordinationAgent(client)

    print(f"✓ Created {len([agent, expert, directeur, cortex])} agents")
    print(f"  - Agent: {agent.role.value} (tier: {agent.tier.value})")
    print(f"  - Expert: {expert.role.value} (tier: {expert.tier.value})")
    print(f"  - Directeur: {directeur.role.value} (tier: {directeur.tier.value})")
    print(f"  - Cortex: {cortex.role.value} (tier: {cortex.tier.value})")

    # Test 2: can_handle pour différentes requêtes
    print("\n2. Testing can_handle...")
    requests = [
        "Validate this code syntax",
        "Implement authentication system",
        "Design the microservices architecture"
    ]

    for req in requests:
        print(f"\n  Request: '{req}'")
        print(f"    Agent: {agent.can_handle(req):.2f}")
        print(f"    Expert: {expert.can_handle(req):.2f}")
        print(f"    Directeur: {directeur.can_handle(req):.2f}")
        print(f"    Cortex: {cortex.can_handle(req):.2f}")

    # Test 3: Escalation hierarchy
    print("\n3. Testing escalation hierarchy...")
    for role in ESCALATION_HIERARCHY:
        next_role = get_next_role(role)
        print(f"  {role.value} → {next_role.value if next_role else 'NONE'}")

    # Test 4: Role to tier mapping
    print("\n4. Testing role to tier mapping...")
    for role, tier in ROLE_TO_TIER.items():
        print(f"  {role.value}: {tier.value}")

    print("\n✓ Agent Hierarchy System works correctly!")
