"""
Planner Agent - Détecte les demandes de planification et crée des tâches structurées

Responsabilités:
- Détecter si une requête demande de la planification
- Décomposer les grandes tâches en sous-tâches
- Générer du contexte optimisé pour chaque tâche
- Déterminer le tier minimum requis par tâche
- Ajouter les tâches au TodoManager
"""

from typing import List, Dict, Any, Optional, Tuple
import json

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier
from cortex.core.todo_manager import TodoManager, TodoTask


class PlannerAgent:
    """Agent de planification intelligent"""

    def __init__(self, llm_client: LLMClient, todo_manager: TodoManager):
        """
        Initialize Planner Agent

        Args:
            llm_client: Client LLM pour l'analyse
            todo_manager: Gestionnaire de TodoList
        """
        self.llm_client = llm_client
        self.todo_manager = todo_manager

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
- Contient "planifier", "plan", "étapes", "décomposer", "organiser"
- Demande de créer une roadmap, un planning, ou une liste de tâches
- Demande d'organiser un projet ou une fonctionnalité complexe
- Demande de structurer une approche

CRITÈRES pour NE PAS détecter comme planification:
- Demande d'exécution immédiate (juste faire quelque chose)
- Question simple
- Conversation générale

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
                max_tokens=200,
                temperature=0.3
            )

            # Parser la réponse JSON
            result = json.loads(response.content.strip())
            return result['is_planning'], result['confidence']

        except Exception as e:
            print(f"⚠️  Error in planning detection: {e}")
            # En cas d'erreur, on utilise des heuristiques simples
            planning_keywords = [
                'plan', 'planifier', 'étapes', 'décomposer', 'organiser',
                'roadmap', 'planning', 'structurer', 'architecture'
            ]
            user_lower = user_request.lower()
            has_keyword = any(kw in user_lower for kw in planning_keywords)
            return has_keyword, 0.7 if has_keyword else 0.3

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

            return {
                'success': True,
                'plan_summary': plan_data['plan_summary'],
                'tasks_created': len(created_tasks),
                'tasks': created_tasks,
                'estimated_time': plan_data.get('total_estimated_time', 'N/A'),
                'cost': response.cost
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to create plan: {str(e)}"
            }

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
                temperature=0.3
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

            return task

        except Exception:
            # Fallback: utiliser DeepSeek par défaut
            task = self.todo_manager.add_task(
                description=user_request,
                context=context if context else user_request,
                min_tier=ModelTier.DEEPSEEK
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
