"""
AgentFirst Router - Point d'entrée unique pour toutes les requêtes

Principe: Toute requête démarre au niveau AGENT (nano) et escalade si nécessaire.

Flow:
1. Classification de la requête (ultra-rapide avec nano)
2. Route vers le bon niveau de départ
3. Exécution avec escalation automatique
4. Retour du résultat final
"""

import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier
from cortex.core.agent_hierarchy import (
    BaseAgent,
    AgentRole,
    AgentResult,
    RequestComplexity,
    EscalationContext,
    ESCALATION_HIERARCHY,
    get_next_role
)


@dataclass
class RoutingDecision:
    """Décision de routing"""
    complexity: RequestComplexity
    start_role: AgentRole
    confidence: float
    reasoning: str


class AgentFirstRouter:
    """
    Router principal - AgentFirst principe

    Responsabilités:
    - Classifier toutes les requêtes entrantes
    - Router vers le bon niveau de départ
    - Superviser l'exécution avec escalation
    - Retourner résultat final optimisé
    """

    # Prompt ultra-optimisé pour classification nano
    CLASSIFICATION_PROMPT = """You are AgentFirst Router - Ultra-fast request classifier.

MISSION: Classify request complexity to route to correct agent level.

AGENT HIERARCHY:
1. AGENT (nano) - Simple tasks: validate, check, test, parse, list
2. EXPERT (deepseek) - Analysis: implement, create, refactor, debug
3. DIRECTEUR (gpt5) - Decisions: design, architect, plan, choose
4. CORTEX (claude) - Coordination: orchestrate, innovate, critical

REQUEST: "{request}"

CLASSIFY (0-5):
0-TRIVIAL: Direct to AGENT (validation, parsing, simple checks)
1-SIMPLE: Start AGENT, may escalate (explain, summarize)
2-MODERATE: Direct to EXPERT (implement, refactor, debug)
3-COMPLEX: Start EXPERT, may escalate (complex features)
4-CRITICAL: Direct to DIRECTEUR (architecture, decisions)
5-STRATEGIC: Direct to CORTEX (system-wide, coordination)

OUTPUT (JSON only, max 30 tokens):
{{"complexity": 0-5, "reasoning": "1 sentence"}}"""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize AgentFirst Router

        Args:
            llm_client: Client LLM pour classification
        """
        self.llm_client = llm_client
        self.agents: Dict[AgentRole, List[BaseAgent]] = {
            role: [] for role in AgentRole
        }
        self.routing_history: List[RoutingDecision] = []
        self.execution_history: List[AgentResult] = []
        self.total_cost = 0.0

    def register_agent(self, agent: BaseAgent):
        """
        Enregistre un agent dans le router

        Args:
            agent: Agent à enregistrer
        """
        if agent.role not in self.agents:
            self.agents[agent.role] = []

        self.agents[agent.role].append(agent)

    def route(
        self,
        request: str,
        context: Optional[Dict] = None,
        force_role: Optional[AgentRole] = None
    ) -> AgentResult:
        """
        Route une requête vers le bon agent

        Args:
            request: Requête utilisateur
            context: Contexte additionnel
            force_role: Forcer un rôle spécifique (debug)

        Returns:
            AgentResult final
        """
        print(f"\n{'='*60}")
        print(f"🎯 AgentFirst Router")
        print(f"{'='*60}")
        print(f"Request: {request[:100]}...")

        # 1. Classification (ultra-rapide avec nano)
        if force_role:
            routing = RoutingDecision(
                complexity=RequestComplexity.SIMPLE,
                start_role=force_role,
                confidence=1.0,
                reasoning="Forced by caller"
            )
        else:
            routing = self._classify_request(request)

        self.routing_history.append(routing)

        print(f"\n📊 Classification:")
        print(f"  Complexity: {routing.complexity.name} ({routing.complexity.value})")
        print(f"  Start role: {routing.start_role.value.upper()}")
        print(f"  Confidence: {routing.confidence:.0%}")
        print(f"  Reasoning: {routing.reasoning}")

        # 2. Exécution avec escalation
        result = self._execute_with_escalation(
            request=request,
            start_role=routing.start_role,
            context=context
        )

        # 3. Tracking
        self.execution_history.append(result)
        self.total_cost += result.cost

        print(f"\n{'='*60}")
        print(f"✅ FINAL RESULT")
        print(f"{'='*60}")
        print(f"Success: {result.success}")
        print(f"Final role: {result.role.value.upper()}")
        print(f"Cost: ${result.cost:.4f} (Total: ${self.total_cost:.4f})")
        print(f"{'='*60}\n")

        return result

    def _classify_request(self, request: str) -> RoutingDecision:
        """
        Classifie une requête avec nano (ultra-rapide)

        Args:
            request: Requête à classifier

        Returns:
            RoutingDecision avec niveau de départ
        """
        prompt = self.CLASSIFICATION_PROMPT.format(request=request)

        try:
            response = self.llm_client.complete(
                messages=[{"role": "user", "content": prompt}],
                tier=ModelTier.NANO,
                max_tokens=50
                # Note: Nano model only supports temperature=1 (default)
            )

            self.total_cost += response.cost

            # Parser JSON
            result = json.loads(response.content.strip())
            complexity_value = result.get('complexity', 1)
            reasoning = result.get('reasoning', 'No reasoning provided')

            # Mapper complexity → start_role
            complexity = RequestComplexity(complexity_value)
            start_role = self._complexity_to_role(complexity)

            return RoutingDecision(
                complexity=complexity,
                start_role=start_role,
                confidence=0.85,
                reasoning=reasoning
            )

        except Exception as e:
            # Fallback: heuristique simple
            print(f"  ⚠️  Classification failed, using heuristic: {e}")
            return self._heuristic_classification(request)

    def _complexity_to_role(self, complexity: RequestComplexity) -> AgentRole:
        """Map complexity level to starting role"""
        mapping = {
            RequestComplexity.TRIVIAL: AgentRole.AGENT,
            RequestComplexity.SIMPLE: AgentRole.AGENT,
            RequestComplexity.MODERATE: AgentRole.EXPERT,
            RequestComplexity.COMPLEX: AgentRole.EXPERT,
            RequestComplexity.CRITICAL: AgentRole.DIRECTEUR,
            RequestComplexity.STRATEGIC: AgentRole.CORTEX_CENTRAL
        }
        return mapping.get(complexity, AgentRole.AGENT)

    def _heuristic_classification(self, request: str) -> RoutingDecision:
        """Fallback heuristic classification"""
        request_lower = request.lower()

        # Patterns triviaux
        if any(p in request_lower for p in ['validate', 'check', 'test', 'parse', 'list']):
            return RoutingDecision(
                complexity=RequestComplexity.TRIVIAL,
                start_role=AgentRole.AGENT,
                confidence=0.6,
                reasoning="Heuristic: trivial task pattern"
            )

        # Patterns complexes
        if any(p in request_lower for p in ['design', 'architect', 'decide', 'choose']):
            return RoutingDecision(
                complexity=RequestComplexity.CRITICAL,
                start_role=AgentRole.DIRECTEUR,
                confidence=0.6,
                reasoning="Heuristic: decision/architecture pattern"
            )

        # Patterns modérés
        if any(p in request_lower for p in ['implement', 'create', 'refactor', 'debug']):
            return RoutingDecision(
                complexity=RequestComplexity.MODERATE,
                start_role=AgentRole.EXPERT,
                confidence=0.6,
                reasoning="Heuristic: development pattern"
            )

        # Par défaut: AGENT
        return RoutingDecision(
            complexity=RequestComplexity.SIMPLE,
            start_role=AgentRole.AGENT,
            confidence=0.5,
            reasoning="Heuristic: default to AGENT"
        )

    def _execute_with_escalation(
        self,
        request: str,
        start_role: AgentRole,
        context: Optional[Dict]
    ) -> AgentResult:
        """
        Exécute avec escalation automatique

        Args:
            request: Requête
            start_role: Rôle de départ
            context: Contexte

        Returns:
            AgentResult final
        """
        # Trouver l'index de départ dans la hiérarchie
        try:
            start_idx = ESCALATION_HIERARCHY.index(start_role)
        except ValueError:
            start_idx = 0  # Fallback: commencer en bas

        escalation_ctx = None

        # Boucle d'escalation
        for role in ESCALATION_HIERARCHY[start_idx:]:
            print(f"\n{'─'*60}")
            print(f"🎯 Trying {role.value.upper()}")
            print(f"{'─'*60}")

            # Sélectionner un agent pour ce rôle
            agent = self._select_agent(role, request)

            if not agent:
                print(f"  ⚠️  No agent available for {role.value}")
                continue

            # Vérifier si l'agent peut gérer
            can_handle_score = agent.can_handle(request, context)
            print(f"  Can handle: {can_handle_score:.0%}")

            if can_handle_score < 0.3 and role != AgentRole.CORTEX_CENTRAL:
                print(f"  ⬆️  Confidence too low, escalating...")
                continue

            # Exécuter
            result = agent.execute(request, context, escalation_ctx)

            print(f"  Result: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
            print(f"  Confidence: {result.confidence:.0%}")
            print(f"  Cost: ${result.cost:.4f}")

            # Succès?
            if result.success and not agent.should_escalate(result):
                return result

            # Préparer contexte d'escalation
            if agent.should_escalate(result):
                print(f"  ⬆️  Escalating to next level...")
                print(f"      Reason: {result.escalation_reason or 'Low confidence'}")
                escalation_ctx = agent.get_escalation_context(request, result)
            else:
                # Échec sans possibilité d'escalation
                return result

        # Tous les niveaux épuisés
        return AgentResult(
            success=False,
            role=AgentRole.CORTEX_CENTRAL,
            tier=ModelTier.CLAUDE,
            content=None,
            cost=0.0,
            confidence=0.0,
            error="All hierarchy levels exhausted without success"
        )

    def _select_agent(self, role: AgentRole, request: str) -> Optional[BaseAgent]:
        """
        Sélectionne le meilleur agent pour un rôle

        Args:
            role: Rôle recherché
            request: Requête (pour choisir spécialisation)

        Returns:
            BaseAgent ou None
        """
        agents = self.agents.get(role, [])

        if not agents:
            return None

        # Si un seul agent, retourner
        if len(agents) == 1:
            return agents[0]

        # Sinon, choisir celui avec le meilleur score can_handle
        best_agent = None
        best_score = 0.0

        for agent in agents:
            score = agent.can_handle(request)
            if score > best_score:
                best_score = score
                best_agent = agent

        return best_agent

    def get_statistics(self) -> Dict[str, Any]:
        """Obtient des statistiques sur le routing"""
        if not self.execution_history:
            return {
                'total_requests': 0,
                'success_rate': 0.0,
                'total_cost': 0.0,
                'avg_cost': 0.0,
                'role_distribution': {}
            }

        total = len(self.execution_history)
        successes = sum(1 for r in self.execution_history if r.success)

        # Distribution par rôle
        role_dist = {}
        for result in self.execution_history:
            role_name = result.role.value
            if role_name not in role_dist:
                role_dist[role_name] = {' count': 0, 'cost': 0.0, 'successes': 0}
            role_dist[role_name]['count'] += 1
            role_dist[role_name]['cost'] += result.cost
            if result.success:
                role_dist[role_name]['successes'] += 1

        return {
            'total_requests': total,
            'success_rate': successes / total if total > 0 else 0.0,
            'total_cost': self.total_cost,
            'avg_cost': self.total_cost / total if total > 0 else 0.0,
            'role_distribution': role_dist
        }


def create_agent_first_router(llm_client: LLMClient) -> AgentFirstRouter:
    """Factory function pour créer un AgentFirstRouter"""
    return AgentFirstRouter(llm_client)


# Test si exécuté directement
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient
    from cortex.core.agent_hierarchy import (
        ExecutionAgent,
        AnalysisAgent,
        DecisionAgent,
        CoordinationAgent
    )

    print("Testing AgentFirst Router...")

    client = LLMClient()
    router = create_agent_first_router(client)

    # Enregistrer des agents
    print("\n1. Registering agents...")
    router.register_agent(ExecutionAgent(client, specialization="testing"))
    router.register_agent(AnalysisAgent(client, specialization="development"))
    router.register_agent(DecisionAgent(client, specialization="architecture"))
    router.register_agent(CoordinationAgent(client))

    print(f"✓ Registered agents:")
    for role, agents in router.agents.items():
        print(f"  {role.value}: {len(agents)} agent(s)")

    # Test 2: Classification de différentes requêtes
    print("\n2. Testing request classification...")

    test_requests = [
        "Validate this code syntax",
        "Implement authentication system",
        "Design the microservices architecture"
    ]

    for req in test_requests:
        print(f"\n  Request: '{req}'")
        routing = router._classify_request(req)
        print(f"    Complexity: {routing.complexity.name}")
        print(f"    Start role: {routing.start_role.value}")
        print(f"    Reasoning: {routing.reasoning}")

    # Test 3: Statistics
    print("\n3. Testing statistics...")
    stats = router.get_statistics()
    print(f"✓ Statistics:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Total cost: ${stats['total_cost']:.4f}")

    print("\n✓ AgentFirst Router works correctly!")
