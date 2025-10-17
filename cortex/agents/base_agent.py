"""
Base Agent - Classe de base pour tous les agents du Cortex
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json

from cortex.core.llm_client import LLMClient, LLMResponse
from cortex.core.model_router import ModelRouter, ModelTier
from cortex.core.quality_evaluator import QualityEvaluator, QualityAssessment
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
        model_router: Optional[ModelRouter] = None,
        hr_department=None,
        tools_department=None,
        expert_pool=None,
        print_updates: bool = True  # Nouveau: contrôle les prints terminal
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

        # Départements (pour création dynamique)
        self.hr_department = hr_department
        self.tools_department = tools_department
        self.expert_pool = expert_pool

        # Stats
        self.task_count = 0
        self.total_cost = 0.0
        self.delegation_count = 0
        self.escalation_count = 0

        # Quality evaluator (partagé)
        self.quality_evaluator = QualityEvaluator(self.llm_client)

        # Contrôle des updates terminal
        self.print_updates = print_updates

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

    def _print_update(self, message: str, level: str = "info"):
        """
        Print obligatoire d'un update au terminal

        Tous les agents DOIVENT appeler cette méthode pour informer l'utilisateur
        de ce qu'ils font.

        Args:
            message: Message à afficher
            level: "start", "progress", "success", "error", "info"
        """
        if not self.print_updates:
            return

        symbols = {
            "start": "🚀",
            "progress": "⚙️",
            "success": "✅",
            "error": "❌",
            "info": "ℹ️",
            "tool": "🔧",
            "delegate": "👥",
            "escalate": "⬆️"
        }

        symbol = symbols.get(level, "•")
        print(f"{symbol} [{self.config.name}] {message}")

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

        # UPDATE TERMINAL OBLIGATOIRE - Début de tâche
        self._print_update(f"Starting: {task[:60]}{'...' if len(task) > 60 else ''}", level="start")

        if verbose:
            print(f"\n[{self.config.name}] Executing task: {task[:80]}...")

        # Construire les messages
        messages = self._build_messages(task, context)

        # Sélectionner le modèle approprié
        tier = self._select_tier(task)

        # UPDATE TERMINAL OBLIGATOIRE - Modèle sélectionné
        self._print_update(f"Using {tier.value} model", level="progress")

        if verbose:
            print(f"[{self.config.name}] Using tier: {tier.value}")

        try:
            # Exécuter avec ou sans tools
            if use_tools and self.available_tools:
                self._print_update(f"Executing with {len(self.available_tools)} tools available", level="tool")

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

            # UPDATE TERMINAL OBLIGATOIRE - Succès
            self._print_update(
                f"Task completed (cost: ${response.cost:.6f}, tokens: {response.tokens_input}→{response.tokens_output})",
                level="success"
            )

            if verbose:
                print(f"[{self.config.name}] ✓ Task completed")
                print(f"  Cost: ${response.cost:.6f} | Tokens: {response.tokens_input}→{response.tokens_output}")

            return result

        except Exception as e:
            # UPDATE TERMINAL OBLIGATOIRE - Erreur
            self._print_update(f"Task failed: {str(e)[:80]}", level="error")

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

        # UPDATE TERMINAL OBLIGATOIRE - Délégation
        self._print_update(f"Delegating to {agent.config.name}", level="delegate")

        if verbose:
            print(f"[{self.config.name}] Delegating to {agent.config.name}...")

        # Exécuter via le subordonné
        result = agent.execute(task, context, verbose=verbose)

        # Mettre à jour nos stats
        if result.get("success"):
            self.total_cost += result.get("cost", 0)
            self._print_update(f"Delegation to {agent.config.name} succeeded", level="success")
        else:
            self._print_update(f"Delegation to {agent.config.name} failed", level="error")

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

IMPORTANT - Response Style:
- Keep responses as SHORT as possible while still communicating perfectly
- Be direct and to the point
- Avoid unnecessary explanations or verbosity
- Every token costs money - maximize value per token
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

    def request_tool(
        self,
        tool_purpose: str,
        input_description: str,
        output_description: str,
        example_usage: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Demande au département des Outils de créer un outil

        Args:
            tool_purpose: But de l'outil
            input_description: Description des entrées
            output_description: Description des sorties
            example_usage: Exemple d'utilisation
            verbose: Mode verbose

        Returns:
            Outil créé ou erreur
        """
        if not self.tools_department:
            return {
                "success": False,
                "error": "Tools Department not available"
            }

        from cortex.agents.tools_department import ToolRequest

        request = ToolRequest(
            requested_by=self.config.name,
            tool_purpose=tool_purpose,
            input_description=input_description,
            output_description=output_description,
            example_usage=example_usage
        )

        result = self.tools_department.create_tool(request, verbose=verbose)

        if result["success"]:
            # Enregistrer l'outil
            tool = result["tool"]
            self.register_tool(tool)

            if verbose:
                print(f"[{self.config.name}] ✓ New tool {result['tool_name']} available")

        return result

    def execute_with_escalation(
        self,
        task: str,
        max_tier: ModelTier = ModelTier.CLAUDE,
        max_attempts: int = 3,
        quality_threshold: float = 6.0,
        context: Optional[Dict[str, Any]] = None,
        use_tools: bool = True,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Exécute avec escalade automatique vers tiers supérieurs si nécessaire

        Stratégie:
        1. Essaie avec le tier préféré de l'agent (ou NANO par défaut)
        2. Évalue la qualité via LLM
        3. Si insuffisant (< quality_threshold), escalade au tier supérieur
        4. Si max_tier atteint et toujours insuffisant, délègue à un expert

        Args:
            task: Tâche à exécuter
            max_tier: Tier maximum avant délégation à expert
            max_attempts: Nombre max de tentatives d'escalade
            quality_threshold: Score minimum acceptable (0-10)
            context: Contexte additionnel
            use_tools: Utiliser les tools disponibles
            verbose: Mode verbose

        Returns:
            Résultat avec escalation_history et quality_score
        """
        escalation_history = []
        total_cost = 0.0
        current_tier = self.config.tier_preference
        best_result = None
        best_quality = 0.0

        if verbose:
            print(f"\n[{self.config.name}] ═══ EXECUTE WITH ESCALATION ═══")
            print(f"[{self.config.name}] Task: {task[:80]}...")
            print(f"[{self.config.name}] Starting tier: {current_tier.value}")
            print(f"[{self.config.name}] Quality threshold: {quality_threshold}/10")

        for attempt in range(max_attempts):
            if verbose:
                print(f"\n[{self.config.name}] ─── Attempt {attempt + 1}/{max_attempts} ───")
                print(f"[{self.config.name}] Using tier: {current_tier.value}")

            # Construire les messages avec le tier actuel
            messages = self._build_messages(task, context)

            try:
                # Exécuter avec le tier actuel
                if use_tools and self.available_tools:
                    response = self.tool_executor.execute_with_tools(
                        messages=messages,
                        tier=current_tier,
                        tools=list(self.available_tools.values()),
                        temperature=1.0,
                        verbose=False
                    )
                else:
                    response = self.llm_client.complete(
                        messages=messages,
                        tier=current_tier,
                        temperature=1.0
                    )

                execution_cost = response.cost
                total_cost += execution_cost
                self.total_cost += execution_cost

                if verbose:
                    print(f"[{self.config.name}] Execution cost: ${execution_cost:.6f}")
                    print(f"[{self.config.name}] Response length: {len(response.content)} chars")

                # Évaluer la qualité via LLM
                assessment = self.quality_evaluator.evaluate(
                    task=task,
                    response=response.content,
                    tier_used=current_tier,
                    quality_threshold=quality_threshold,
                    verbose=verbose
                )

                total_cost += assessment.cost
                self.total_cost += assessment.cost

                # Enregistrer dans l'historique
                escalation_history.append({
                    "attempt": attempt + 1,
                    "tier": current_tier.value,
                    "quality_score": assessment.score,
                    "confidence": assessment.confidence,
                    "execution_cost": execution_cost,
                    "evaluation_cost": assessment.cost,
                    "issues": assessment.issues,
                    "strengths": assessment.strengths
                })

                # Garder le meilleur résultat
                if assessment.score > best_quality:
                    best_quality = assessment.score
                    best_result = {
                        "success": True,
                        "data": response.content,
                        "agent": self.config.name,
                        "role": self.config.role,
                        "tier": current_tier.value,
                        "tokens_input": response.tokens_input,
                        "tokens_output": response.tokens_output,
                        "tool_calls": len(response.tool_calls) if response.tool_calls else 0
                    }

                # Vérifier si qualité suffisante
                if assessment.score >= quality_threshold:
                    if verbose:
                        print(f"[{self.config.name}] ✓ Quality threshold met!")
                        print(f"[{self.config.name}] Final score: {assessment.score:.1f}/10")

                    # Sauvegarder en mémoire
                    self.memory.add_to_short_term({
                        "task": task,
                        "summary": response.content[:100],
                        "cost": total_cost,
                        "tier": current_tier.value,
                        "escalated": attempt > 0,
                        "quality_score": assessment.score
                    })

                    return {
                        **best_result,
                        "cost": total_cost,
                        "total_cost": total_cost,
                        "final_tier": current_tier.value,
                        "quality_score": assessment.score,
                        "quality_confidence": assessment.confidence,
                        "escalation_history": escalation_history,
                        "escalated": attempt > 0,
                        "attempts": attempt + 1
                    }

                # Qualité insuffisante, décider de l'escalade
                if verbose:
                    print(f"[{self.config.name}] Quality insufficient: {assessment.score:.1f}/10")
                    print(f"[{self.config.name}] Reasoning: {assessment.reasoning}")

                # Si suggestion d'expert, déléguer
                if assessment.suggested_expert:
                    if verbose:
                        print(f"[{self.config.name}] Expert recommended: {assessment.suggested_expert}")

                    return self._escalate_to_expert(
                        task=task,
                        expert_type=assessment.suggested_expert,
                        context=context,
                        escalation_history=escalation_history,
                        total_cost=total_cost,
                        verbose=verbose
                    )

                # Si suggestion de tier et dans les limites, escalader
                if assessment.suggested_tier:
                    if self._is_tier_within_limit(assessment.suggested_tier, max_tier):
                        current_tier = assessment.suggested_tier
                        if verbose:
                            print(f"[{self.config.name}] Escalating to: {current_tier.value}")
                        continue
                    else:
                        if verbose:
                            print(f"[{self.config.name}] Suggested tier {assessment.suggested_tier.value} exceeds max_tier")
                        break

                # Aucune suggestion, essayer tier supérieur
                next_tier = self._get_next_tier(current_tier)
                if next_tier and self._is_tier_within_limit(next_tier, max_tier):
                    current_tier = next_tier
                    if verbose:
                        print(f"[{self.config.name}] Escalating to: {current_tier.value}")
                    continue
                else:
                    if verbose:
                        print(f"[{self.config.name}] No higher tier available within limits")
                    break

            except Exception as e:
                if verbose:
                    print(f"[{self.config.name}] Error during execution: {e}")

                escalation_history.append({
                    "attempt": attempt + 1,
                    "tier": current_tier.value,
                    "error": str(e)
                })

                # Essayer tier supérieur en cas d'erreur
                next_tier = self._get_next_tier(current_tier)
                if next_tier and self._is_tier_within_limit(next_tier, max_tier):
                    current_tier = next_tier
                    continue
                break

        # Retourner le meilleur résultat même si sous le seuil
        if best_result:
            if verbose:
                print(f"\n[{self.config.name}] Returning best result: {best_quality:.1f}/10")
                print(f"[{self.config.name}] Warning: Quality threshold not met")

            self.memory.add_to_short_term({
                "task": task,
                "summary": best_result["data"][:100],
                "cost": total_cost,
                "tier": best_result["tier"],
                "escalated": True,
                "quality_score": best_quality,
                "warning": "Quality threshold not met"
            })

            return {
                **best_result,
                "cost": total_cost,
                "total_cost": total_cost,
                "final_tier": best_result["tier"],
                "quality_score": best_quality,
                "escalation_history": escalation_history,
                "escalated": True,
                "attempts": len(escalation_history),
                "warning": f"Quality threshold ({quality_threshold}) not met. Best score: {best_quality:.1f}"
            }

        # Aucun résultat valide
        return {
            "success": False,
            "error": "All escalation attempts failed",
            "agent": self.config.name,
            "escalation_history": escalation_history,
            "total_cost": total_cost
        }

    def _get_next_tier(self, current_tier: ModelTier) -> Optional[ModelTier]:
        """Retourne le tier supérieur"""
        tier_order = [ModelTier.NANO, ModelTier.DEEPSEEK, ModelTier.CLAUDE]
        try:
            current_index = tier_order.index(current_tier)
            if current_index < len(tier_order) - 1:
                return tier_order[current_index + 1]
        except ValueError:
            pass
        return None

    def _is_tier_within_limit(self, tier: ModelTier, max_tier: ModelTier) -> bool:
        """Vérifie si un tier est dans la limite autorisée"""
        tier_order = [ModelTier.NANO, ModelTier.DEEPSEEK, ModelTier.CLAUDE]
        try:
            tier_index = tier_order.index(tier)
            max_index = tier_order.index(max_tier)
            return tier_index <= max_index
        except ValueError:
            return False

    def _escalate_to_expert(
        self,
        task: str,
        expert_type: str,
        context: Optional[Dict[str, Any]],
        escalation_history: List[Dict],
        total_cost: float,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Délègue à un agent expert spécialisé

        Utilise l'ExpertPool pour consulter un expert hautement spécialisé
        """
        if verbose:
            print(f"\n[{self.config.name}] ═══ EXPERT ESCALATION ═══")
            print(f"[{self.config.name}] Expert type needed: {expert_type}")

        self.escalation_count += 1

        # Vérifier si ExpertPool disponible
        if not self.expert_pool:
            if verbose:
                print(f"[{self.config.name}] Warning: ExpertPool not available")

            escalation_history.append({
                "tier": "expert_required",
                "expert_type": expert_type,
                "note": "ExpertPool not available"
            })

            return {
                "success": False,
                "expert_required": True,
                "expert_type": expert_type,
                "agent": self.config.name,
                "escalation_history": escalation_history,
                "total_cost": total_cost,
                "message": f"Task requires expert: {expert_type}, but ExpertPool not available."
            }

        # Mapper le expert_type string vers ExpertType enum
        from cortex.agents.expert_pool import ExpertType

        expert_type_map = {
            "security_expert": ExpertType.SECURITY_EXPERT,
            "system_designer": ExpertType.SYSTEM_DESIGNER,
            "algorithm_specialist": ExpertType.ALGORITHM_SPECIALIST,
            "data_scientist": ExpertType.DATA_SCIENTIST,
            "code_architect": ExpertType.CODE_ARCHITECT,
            "performance_optimizer": ExpertType.PERFORMANCE_OPTIMIZER,
            "database_architect": ExpertType.DATABASE_ARCHITECT,
            "network_specialist": ExpertType.NETWORK_SPECIALIST
        }

        expert_enum = expert_type_map.get(expert_type.lower())

        if not expert_enum:
            # Tenter de suggérer un expert via LLM
            if verbose:
                print(f"[{self.config.name}] Unknown expert type, using LLM to suggest...")

            expert_enum = self.expert_pool.suggest_expert_for_task(task, verbose=verbose)

            if not expert_enum:
                escalation_history.append({
                    "tier": "expert_suggestion_failed",
                    "expert_type": expert_type,
                    "note": "Could not map to expert type"
                })

                return {
                    "success": False,
                    "error": f"Unknown expert type: {expert_type}",
                    "agent": self.config.name,
                    "escalation_history": escalation_history,
                    "total_cost": total_cost
                }

        # Consulter l'expert
        try:
            if verbose:
                print(f"[{self.config.name}] Consulting {expert_enum.value}...")

            expert_result = self.expert_pool.consult_expert(
                expert_type=expert_enum,
                task=task,
                context=context,
                use_tools=True,
                verbose=verbose
            )

            total_cost += expert_result.get("cost", 0.0)
            self.total_cost += expert_result.get("cost", 0.0)

            # Enregistrer l'escalade vers l'expert
            escalation_history.append({
                "tier": "expert",
                "expert_type": expert_enum.value,
                "expert_name": expert_result.get("expert_name"),
                "cost": expert_result.get("cost", 0.0),
                "success": expert_result.get("success", False)
            })

            if expert_result.get("success"):
                if verbose:
                    print(f"[{self.config.name}] ✓ Expert consultation successful")
                    print(f"[{self.config.name}] Total cost: ${total_cost:.6f}")

                # Sauvegarder en mémoire
                self.memory.add_to_short_term({
                    "task": task,
                    "summary": f"Escalated to {expert_enum.value}: {expert_result.get('data', '')[:80]}...",
                    "cost": total_cost,
                    "tier": "expert",
                    "expert_type": expert_enum.value,
                    "escalated": True
                })

                return {
                    "success": True,
                    "data": expert_result.get("data"),
                    "agent": self.config.name,
                    "role": self.config.role,
                    "expert_used": expert_enum.value,
                    "expert_name": expert_result.get("expert_name"),
                    "cost": total_cost,
                    "total_cost": total_cost,
                    "final_tier": "expert",
                    "escalation_history": escalation_history,
                    "escalated": True,
                    "tokens_input": expert_result.get("tokens_input", 0),
                    "tokens_output": expert_result.get("tokens_output", 0),
                    "quality_score": 10.0  # Assume expert provides high quality
                }
            else:
                if verbose:
                    print(f"[{self.config.name}] Expert consultation failed")

                return {
                    "success": False,
                    "error": expert_result.get("error", "Expert consultation failed"),
                    "agent": self.config.name,
                    "expert_type": expert_enum.value,
                    "escalation_history": escalation_history,
                    "total_cost": total_cost
                }

        except Exception as e:
            if verbose:
                print(f"[{self.config.name}] Error during expert consultation: {e}")

            escalation_history.append({
                "tier": "expert",
                "expert_type": expert_enum.value if expert_enum else expert_type,
                "error": str(e)
            })

            return {
                "success": False,
                "error": f"Expert consultation error: {e}",
                "agent": self.config.name,
                "escalation_history": escalation_history,
                "total_cost": total_cost
            }

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de l'agent"""
        evaluator_stats = self.quality_evaluator.get_stats()

        return {
            "name": self.config.name,
            "role": self.config.role,
            "task_count": self.task_count,
            "delegation_count": self.delegation_count,
            "escalation_count": self.escalation_count,
            "total_cost": self.total_cost,
            "avg_cost_per_task": self.total_cost / self.task_count if self.task_count > 0 else 0,
            "memory_size": len(self.memory.short_term),
            "tools_count": len(self.available_tools),
            "subordinates_count": len(self.subordinates),
            "evaluation_cost": evaluator_stats["total_evaluation_cost"]
        }

    def __repr__(self):
        return f"<Agent '{self.config.name}' ({self.config.role})>"
