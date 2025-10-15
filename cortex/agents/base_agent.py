"""
Base Agent - Classe de base pour tous les agents du Cortex
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json

from cortex.core.llm_client import LLMClient, LLMResponse
from cortex.core.model_router import ModelRouter, ModelTier
from cortex.tools.standard_tool import StandardTool
from cortex.tools.tool_executor import ToolExecutor


@dataclass
class AgentMemory:
    """Mémoire d'un agent"""
    short_term: List[Dict[str, Any]] = field(default_factory=list)  # Dernières N interactions
    long_term: Dict[str, Any] = field(default_factory=dict)  # Connaissances persistantes
    max_short_term: int = 10  # Nombre max d'éléments en mémoire court terme

    def add_to_short_term(self, interaction: Dict[str, Any]):
        """Ajoute une interaction en mémoire court terme"""
        self.short_term.append({
            "timestamp": datetime.now().isoformat(),
            **interaction
        })

        # Limiter la taille
        if len(self.short_term) > self.max_short_term:
            self.short_term.pop(0)

    def add_to_long_term(self, key: str, value: Any):
        """Ajoute une connaissance en mémoire long terme"""
        self.long_term[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }

    def get_context(self) -> str:
        """Génère un contexte depuis la mémoire"""
        context_parts = []

        # Mémoire court terme
        if self.short_term:
            context_parts.append("Recent interactions:")
            for item in self.short_term[-5:]:  # 5 dernières
                context_parts.append(f"  - {item.get('summary', 'N/A')}")

        # Mémoire long terme (éléments importants)
        if self.long_term:
            context_parts.append("\nKnown facts:")
            for key, data in list(self.long_term.items())[:5]:  # 5 premiers
                context_parts.append(f"  - {key}: {data['value']}")

        return "\n".join(context_parts) if context_parts else "No prior context"


@dataclass
class AgentConfig:
    """Configuration d'un agent"""
    name: str
    role: str
    description: str
    base_prompt: str
    tier_preference: ModelTier = ModelTier.DEEPSEEK  # Tier par défaut
    can_delegate: bool = True
    specializations: List[str] = field(default_factory=list)
    max_delegation_depth: int = 3


class BaseAgent:
    """
    Agent de base pour le système Cortex

    Chaque agent a:
    - Un rôle et des responsabilités
    - Sa propre mémoire (court terme et long terme)
    - Son propre prompt de base
    - Des tools disponibles
    - Capacité de délégation (optionnelle)
    """

    def __init__(
        self,
        config: AgentConfig,
        llm_client: Optional[LLMClient] = None,
        model_router: Optional[ModelRouter] = None
    ):
        self.config = config
        self.memory = AgentMemory()

        # Clients
        self.llm_client = llm_client or LLMClient()
        self.model_router = model_router or ModelRouter()

        # Tools
        self.tool_executor = ToolExecutor(self.llm_client)
        self.available_tools: Dict[str, StandardTool] = {}

        # Subordinates (pour délégation)
        self.subordinates: Dict[str, 'BaseAgent'] = {}

        # Stats
        self.task_count = 0
        self.total_cost = 0.0
        self.delegation_count = 0

    def register_tool(self, tool: StandardTool):
        """Enregistre un tool disponible pour cet agent"""
        self.available_tools[tool.name] = tool
        self.tool_executor.register_tool(tool)

    def register_tools(self, tools: List[StandardTool]):
        """Enregistre plusieurs tools"""
        for tool in tools:
            self.register_tool(tool)

    def register_subordinate(self, agent: 'BaseAgent'):
        """Enregistre un agent subordonné"""
        self.subordinates[agent.config.name] = agent

    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        use_tools: bool = True,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Exécute une tâche

        Args:
            task: Description de la tâche
            context: Contexte additionnel
            use_tools: Utiliser les tools disponibles
            verbose: Mode verbose

        Returns:
            Résultat avec success, data, cost, etc.
        """
        self.task_count += 1

        if verbose:
            print(f"\n[{self.config.name}] Executing task: {task[:80]}...")

        # Construire les messages
        messages = self._build_messages(task, context)

        # Sélectionner le modèle approprié
        tier = self._select_tier(task)

        if verbose:
            print(f"[{self.config.name}] Using tier: {tier.value}")

        try:
            # Exécuter avec ou sans tools
            if use_tools and self.available_tools:
                response = self.tool_executor.execute_with_tools(
                    messages=messages,
                    tier=tier,
                    tools=list(self.available_tools.values()),
                    temperature=1.0,  # Default temperature
                    verbose=verbose
                )
            else:
                response = self.llm_client.complete(
                    messages=messages,
                    tier=tier,
                    temperature=1.0  # Default temperature
                )

            # Mettre à jour les stats
            self.total_cost += response.cost

            # Sauvegarder en mémoire
            self.memory.add_to_short_term({
                "task": task,
                "summary": response.content[:100] if response.content else "Tool calls only",
                "cost": response.cost,
                "tier": tier.value
            })

            result = {
                "success": True,
                "data": response.content,
                "agent": self.config.name,
                "role": self.config.role,
                "cost": response.cost,
                "tokens_input": response.tokens_input,
                "tokens_output": response.tokens_output,
                "tier": tier.value,
                "tool_calls": len(response.tool_calls) if response.tool_calls else 0
            }

            if verbose:
                print(f"[{self.config.name}] ✓ Task completed")
                print(f"  Cost: ${response.cost:.6f} | Tokens: {response.tokens_input}→{response.tokens_output}")

            return result

        except Exception as e:
            if verbose:
                print(f"[{self.config.name}] ✗ Task failed: {e}")

            return {
                "success": False,
                "error": str(e),
                "agent": self.config.name,
                "role": self.config.role
            }

    def delegate(
        self,
        task: str,
        to_agent: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Délègue une tâche à un subordonné

        Args:
            task: Tâche à déléguer
            to_agent: Nom de l'agent cible (auto-sélection si None)
            context: Contexte
            verbose: Mode verbose

        Returns:
            Résultat de l'agent subordonné
        """
        if not self.config.can_delegate:
            return {
                "success": False,
                "error": f"{self.config.name} cannot delegate tasks"
            }

        if not self.subordinates:
            return {
                "success": False,
                "error": f"{self.config.name} has no subordinates"
            }

        # Sélectionner l'agent approprié
        if to_agent and to_agent in self.subordinates:
            agent = self.subordinates[to_agent]
        else:
            agent = self._select_best_subordinate(task)

        if not agent:
            return {
                "success": False,
                "error": "No suitable subordinate found"
            }

        self.delegation_count += 1

        if verbose:
            print(f"[{self.config.name}] Delegating to {agent.config.name}...")

        # Exécuter via le subordonné
        result = agent.execute(task, context, verbose=verbose)

        # Mettre à jour nos stats
        if result.get("success"):
            self.total_cost += result.get("cost", 0)

        return result

    def _build_messages(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Construit les messages pour le LLM"""
        # System prompt avec mémoire
        memory_context = self.memory.get_context()

        system_prompt = f"""{self.config.base_prompt}

Your role: {self.config.role}
Your name: {self.config.name}

{memory_context}

Remember:
- Always seek the cheapest solution that works
- Be concise and efficient
- Use tools when available
"""

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Ajouter le contexte si fourni
        if context:
            context_str = json.dumps(context, indent=2)
            messages.append({
                "role": "user",
                "content": f"Context:\n{context_str}"
            })

        # Ajouter la tâche
        messages.append({
            "role": "user",
            "content": task
        })

        return messages

    def _select_tier(self, task: str) -> ModelTier:
        """Sélectionne le tier approprié pour la tâche"""
        # Utiliser le model router pour analyser la complexité
        selection = self.model_router.select_model(
            task=task,
            agent_role=self.config.role
        )

        # Respecter la préférence de l'agent si possible
        if selection.tier == self.config.tier_preference:
            return selection.tier

        # Sinon utiliser la recommandation du router
        return selection.tier

    def _select_best_subordinate(self, task: str) -> Optional['BaseAgent']:
        """Sélectionne le meilleur subordonné pour une tâche"""
        if not self.subordinates:
            return None

        # Analyser la tâche pour trouver les spécialisations
        task_lower = task.lower()

        best_match = None
        best_score = 0

        for agent in self.subordinates.values():
            score = 0

            # Vérifier les spécialisations
            for spec in agent.config.specializations:
                if spec.lower() in task_lower:
                    score += 10

            # Bonus si agent a moins de tâches (load balancing)
            score += (100 - agent.task_count) / 10

            if score > best_score:
                best_score = score
                best_match = agent

        # Fallback: premier agent disponible
        return best_match or list(self.subordinates.values())[0]

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'agent"""
        return {
            "name": self.config.name,
            "role": self.config.role,
            "task_count": self.task_count,
            "delegation_count": self.delegation_count,
            "total_cost": self.total_cost,
            "avg_cost_per_task": self.total_cost / self.task_count if self.task_count > 0 else 0,
            "memory_size": len(self.memory.short_term),
            "tools_count": len(self.available_tools),
            "subordinates_count": len(self.subordinates)
        }

    def __repr__(self):
        return f"<Agent '{self.config.name}' ({self.config.role})>"
