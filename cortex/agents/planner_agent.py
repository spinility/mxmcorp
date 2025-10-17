"""
Planner Agent - Détecte les demandes de planification et crée des tâches structurées

ROLE: DIRECTEUR (Décision) - Niveau 3 de la hiérarchie
TIER: DEEPSEEK pour planification intelligente

Responsabilités:
- Détecter si une requête demande de la planification
- Décomposer les grandes tâches en sous-tâches
- Générer du contexte optimisé pour chaque tâche
- Déterminer le tier minimum requis par tâche
- Ajouter les tâches au TodoManager
"""

from typing import List, Dict, Any, Optional, Tuple
import json
import time
from datetime import datetime

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier
from cortex.core.todo_manager import TodoManager, TodoTask
from cortex.core.agent_hierarchy import DecisionAgent, AgentRole, AgentResult, EscalationContext
from cortex.core.agent_memory import get_agent_memory


class PlannerAgent(DecisionAgent):
    """Agent de planification intelligent"""

    def __init__(self, llm_client: LLMClient, todo_manager: TodoManager):
        """
        Initialize Planner Agent

        Args:
            llm_client: Client LLM pour l'analyse
            todo_manager: Gestionnaire de TodoList
        """
        # Initialiser DecisionAgent avec spécialisation "planning"
        super().__init__(llm_client, specialization="planning")
        self.todo_manager = todo_manager
        self.memory = get_agent_memory('execution', 'planner')

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """
        Évalue si le PlannerAgent peut gérer la requête

        Override DecisionAgent.can_handle() avec logique spécifique
        """
        # Utiliser is_planning_request pour détection
        is_planning, confidence = self.is_planning_request(request)
        return confidence if is_planning else 0.0

    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[EscalationContext] = None
    ) -> AgentResult:
        """
        Exécute la planification

        Override DecisionAgent.execute() avec logique PlannerAgent

        Args:
            request: Requête de planification
            context: Dict avec optionnel 'current_context'
            escalation_context: Contexte si escalation

        Returns:
            AgentResult avec plan créé
        """
        # Extraire contexte
        current_context = context.get('current_context', '') if context else ''

        # Créer le plan
        plan_result = self.create_plan(request, current_context)

        if plan_result['success']:
            return AgentResult(
                success=True,
                role=self.role,
                tier=self.tier,
                content=plan_result,
                cost=plan_result.get('cost', 0.0),
                confidence=0.9,  # High confidence for successful planning
                should_escalate=False,
                escalation_reason=None,
                error=None,
                metadata={'plan_result': plan_result}
            )
        else:
            return AgentResult(
                success=False,
                role=self.role,
                tier=self.tier,
                content=None,
                cost=0.0,
                confidence=0.0,
                should_escalate=True,
                escalation_reason="Failed to create plan",
                error=plan_result.get('error')
            )

    def is_planning_request(self, user_request: str) -> Tuple[bool, float]:
        """
        Détecte si la requête demande de la planification

        Args:
            user_request: Requête utilisateur

        Returns:
            (is_planning, confidence) - True si c'est une demande de planification, avec score de confiance
        """
        detection_prompt = f"""Analyse cette requête utilisateur et détermine si elle demande de PLANIFIER ou DÉCOMPOSER une tâche complexe.

REQUÊTE: "{user_request}"

CRITÈRES pour détecter une demande de PLANIFICATION:
- Contient "planifier", "planifie", "crée un plan", "décomposer", "organiser"
- Demande EXPLICITE de créer une roadmap ou un planning
- Demande d'organiser un projet ou une fonctionnalité complexe
- Demande de structurer une approche

CRITÈRES pour NE PAS détecter comme planification (IMPORTANT):
- Demande de VOIR/AFFICHER quelque chose existant ("montre", "affiche", "voir le roadmap")
- Demande de LIRE un fichier existant
- Demande d'exécution immédiate (juste faire quelque chose)
- Question simple ou conversation générale

Réponds UNIQUEMENT avec un JSON:
{{
  "is_planning": true/false,
  "confidence": 0.0-1.0,
  "reason": "explication courte"
}}"""

        try:
            response = self.llm_client.complete(
                messages=[{"role": "user", "content": detection_prompt}],
                tier=ModelTier.NANO,  # Rapide et économique
                max_tokens=5000,  # Large marge pour éviter toute troncature JSON
                temperature=1.0  # NANO model requires temperature=1 (default)
            )

            # Parser la réponse JSON
            content = response.content.strip()

            # Vérifier si la réponse a été tronquée
            if response.finish_reason == "length":
                # Réponse tronquée - utiliser fallback
                raise json.JSONDecodeError("Response truncated", content, 0)

            result = json.loads(content)
            return result['is_planning'], result['confidence']

        except (json.JSONDecodeError, KeyError) as e:
            # Fallback silencieux sans afficher l'erreur
            # Fallback intelligent avec détection de "show/display"
            user_lower = user_request.lower()

            # Mots-clés pour AFFICHER quelque chose (PAS de planification)
            show_keywords = ['montre', 'affiche', 'voir', 'display', 'show', 'list', 'liste']

            # Mots-clés pour CRÉER un plan (planification réelle)
            planning_action_keywords = ['planifie', 'crée un plan', 'décompose', 'organise', 'structure']

            # Si demande d'AFFICHER, ce n'est PAS une planification
            if any(kw in user_lower for kw in show_keywords):
                return False, 0.1

            # Si demande explicite de PLANIFIER, c'est une planification
            if any(kw in user_lower for kw in planning_action_keywords):
                return True, 0.8

            # Fallback: utiliser heuristiques basiques
            return False, 0.3

    def create_plan(
        self,
        user_request: str,
        current_context: str = ""
    ) -> Dict[str, Any]:
        """
        Crée un plan détaillé avec tâches et sous-tâches

        Args:
            user_request: Requête utilisateur demandant de la planification
            current_context: Contexte actuel de la conversation

        Returns:
            Dict avec le plan et les tâches créées
        """
        start_time = time.time()

        planning_prompt = f"""Tu es un expert en planification de projets de développement.

REQUÊTE UTILISATEUR:
{user_request}

CONTEXTE ACTUEL:
{current_context if current_context else "Aucun contexte supplémentaire"}

TON TRAVAIL:
1. Décompose cette requête en tâches concrètes et actionnables
2. Pour CHAQUE tâche, fournis:
   - Description claire et actionable
   - Contexte optimisé (ce qu'il faut savoir pour l'exécuter)
   - Tier minimum requis ("nano" pour simple, "deepseek" pour moyen, "claude" pour complexe)
   - Dépendances (quelles tâches doivent être complétées avant)

CRITÈRES pour CHOISIR le TIER:
- NANO: Tâches simples, répétitives, avec instructions claires (ex: créer un fichier vide, copier du code)
- DEEPSEEK: Tâches moyennes nécessitant du raisonnement (ex: écrire une fonction, intégrer une API)
- CLAUDE: Tâches complexes nécessitant architecture et décisions (ex: concevoir un système, refactoring majeur)

Réponds avec un JSON structuré:
{{
  "plan_summary": "Résumé du plan en 2-3 phrases",
  "tasks": [
    {{
      "description": "Description actionable de la tâche",
      "context": "Contexte optimisé pour exécuter cette tâche",
      "min_tier": "nano|deepseek|claude",
      "dependencies": ["task_id1", "task_id2"],
      "estimated_complexity": "low|medium|high"
    }}
  ],
  "total_estimated_time": "Estimation en minutes"
}}

IMPORTANT: Sois précis et concret. Chaque tâche doit être ACTIONABLE."""

        try:
            response = self.llm_client.complete(
                messages=[{"role": "user", "content": planning_prompt}],
                tier=ModelTier.DEEPSEEK,  # Bon équilibre coût/qualité pour la planification
                max_tokens=2000,
                temperature=0.5
            )

            # Parser le plan
            plan_data = json.loads(response.content.strip())

            # Créer les tâches dans le TodoManager
            created_tasks = []
            task_id_map = {}  # Map index → task_id réel

            for idx, task_spec in enumerate(plan_data['tasks']):
                # Convertir tier string en ModelTier
                tier_str = task_spec['min_tier'].lower()
                if tier_str == "nano":
                    tier = ModelTier.NANO
                elif tier_str == "deepseek":
                    tier = ModelTier.DEEPSEEK
                else:
                    tier = ModelTier.CLAUDE

                # Créer la tâche
                task = self.todo_manager.add_task(
                    description=task_spec['description'],
                    context=task_spec['context'],
                    min_tier=tier
                )

                created_tasks.append(task)
                task_id_map[idx] = task.id

            result = {
                'success': True,
                'plan_summary': plan_data['plan_summary'],
                'tasks_created': len(created_tasks),
                'tasks': created_tasks,
                'estimated_time': plan_data.get('total_estimated_time', 'N/A'),
                'cost': response.cost
            }

            # Record to memory
            duration = time.time() - start_time
            self.memory.record_execution(
                request=f"Create plan: {user_request[:100]}",
                result=result,
                duration=duration,
                cost=response.cost
            )

            # Update state
            self.memory.update_state({
                'last_plan_timestamp': datetime.now().isoformat(),
                'last_plan_summary': plan_data['plan_summary'][:200],
                'total_tasks_created': len(created_tasks)
            })

            # Detect patterns in task tiers
            tier_counts = {}
            for task_spec in plan_data['tasks']:
                tier = task_spec['min_tier']
                tier_counts[tier] = tier_counts.get(tier, 0) + 1

            for tier, count in tier_counts.items():
                self.memory.add_pattern(
                    f'tier_usage_{tier}',
                    {
                        'tier': tier,
                        'count': count,
                        'request_type': user_request[:50]
                    }
                )

            return result

        except Exception as e:
            duration = time.time() - start_time
            result = {
                'success': False,
                'error': f"Failed to create plan: {str(e)}"
            }

            # Record failure to memory
            self.memory.record_execution(
                request=f"Create plan: {user_request[:100]}",
                result=result,
                duration=duration,
                cost=0.0
            )

            return result

    def add_single_task_from_request(
        self,
        user_request: str,
        context: str = ""
    ) -> TodoTask:
        """
        Ajoute une tâche unique depuis une requête utilisateur
        (pour les tâches qui ne nécessitent pas de décomposition)

        Args:
            user_request: Requête utilisateur
            context: Contexte actuel

        Returns:
            La tâche créée
        """
        start_time = time.time()

        # Analyser la requête pour déterminer le tier minimum
        analysis_prompt = f"""Analyse cette requête et détermine le tier minimum requis.

REQUÊTE: "{user_request}"

CONTEXTE: {context if context else "Aucun"}

Réponds avec un JSON:
{{
  "description": "Description claire et actionable",
  "min_tier": "nano|deepseek|claude",
  "reason": "Justification du choix de tier"
}}"""

        try:
            response = self.llm_client.complete(
                messages=[{"role": "user", "content": analysis_prompt}],
                tier=ModelTier.NANO,
                max_tokens=200,
                temperature=1.0  # NANO model requires temperature=1 (default)
            )

            result = json.loads(response.content.strip())

            # Convertir tier
            tier_str = result['min_tier'].lower()
            if tier_str == "nano":
                tier = ModelTier.NANO
            elif tier_str == "deepseek":
                tier = ModelTier.DEEPSEEK
            else:
                tier = ModelTier.CLAUDE

            # Créer la tâche
            task = self.todo_manager.add_task(
                description=result['description'],
                context=context if context else user_request,
                min_tier=tier
            )

            # Record to memory
            duration = time.time() - start_time
            self.memory.record_execution(
                request=f"Add single task: {user_request[:100]}",
                result={'success': True, 'task_id': task.id, 'tier': tier_str},
                duration=duration,
                cost=0.0
            )

            # Update state
            self.memory.update_state({
                'last_single_task_timestamp': datetime.now().isoformat(),
                'last_task_description': result['description'][:100]
            })

            # Detect patterns in single task tier usage
            self.memory.add_pattern(
                f'single_task_tier_{tier_str}',
                {
                    'tier': tier_str,
                    'reason': result.get('reason', ''),
                    'request_type': user_request[:50]
                }
            )

            return task

        except Exception as e:
            # Fallback: utiliser DeepSeek par défaut
            duration = time.time() - start_time

            task = self.todo_manager.add_task(
                description=user_request,
                context=context if context else user_request,
                min_tier=ModelTier.DEEPSEEK
            )

            # Record fallback to memory
            self.memory.record_execution(
                request=f"Add single task (fallback): {user_request[:100]}",
                result={'success': True, 'task_id': task.id, 'tier': 'deepseek', 'fallback': True},
                duration=duration,
                cost=0.0
            )

            return task


def create_planner_agent(
    llm_client: LLMClient,
    todo_manager: TodoManager
) -> PlannerAgent:
    """Factory function pour créer un PlannerAgent"""
    return PlannerAgent(llm_client, todo_manager)


# Test si exécuté directement
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient
    from cortex.core.todo_manager import TodoManager

    print("Testing Planner Agent...")

    client = LLMClient()
    todo_manager = TodoManager("cortex/data/test_todolist.json")
    planner = PlannerAgent(client, todo_manager)

    # Test 1: Détection de planification
    print("\n1. Testing planning detection...")
    test_requests = [
        "Planifie l'implémentation d'un système d'authentification OAuth2",
        "Crée un fichier config.json",
        "Comment ça va?"
    ]

    for req in test_requests:
        is_planning, confidence = planner.is_planning_request(req)
        print(f"  '{req}' → Planning: {is_planning} (confidence: {confidence:.2f})")

    print("\n✓ Planner Agent works correctly!")
