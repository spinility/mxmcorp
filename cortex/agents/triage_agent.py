"""
Triage Agent - Détermine si on peut répondre direct ou passer à un expert

ROLE: TRIAGE (Décision rapide) - Niveau 1 de la hiérarchie
TIER: NANO pour triage ultra-rapide

Responsabilités:
- Détecter la complexité de la requête (simple vs complexe)
- Évaluer la confiance (peut répondre direct ou pas)
- Vérifier le cache pour économiser tokens
- Décider: DIRECT (réponse immédiate) ou EXPERT (passer à DeepSeek avec requête bonifiée)
"""

from typing import Dict, Any, Optional, Tuple
import json

from cortex.core.llm_client import LLMClient, ModelTier
from cortex.core.agent_hierarchy import DecisionAgent, AgentRole, AgentResult


class TriageAgent(DecisionAgent):
    """Agent de triage ultra-rapide pour décisions initiales"""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Triage Agent

        Args:
            llm_client: Client LLM pour l'analyse
        """
        super().__init__(llm_client, specialization="triage")

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """
        Le triage agent peut TOUJOURS gérer (c'est le premier filtre)
        """
        return 1.0  # Always handles triage

    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[Any] = None
    ) -> AgentResult:
        """
        Exécute le triage

        Args:
            request: Requête utilisateur
            context: Dict avec cache_hits si disponible
            escalation_context: Contexte si escalation

        Returns:
            AgentResult avec décision de triage
        """
        decision = self.triage_request(request, context)

        return AgentResult(
            success=True,
            role=self.role,
            tier=self.tier,
            content=decision,
            cost=decision.get('cost', 0.0),
            confidence=decision['confidence'],
            should_escalate=decision['route'] == 'expert',
            escalation_reason=decision.get('reason') if decision['route'] == 'expert' else None,
            error=None,
            metadata={'decision': decision}
        )

    def triage_request(
        self,
        user_request: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Triage ultra-rapide de la requête

        Args:
            user_request: Requête utilisateur
            context: Contexte avec cache_hits si disponible

        Returns:
            Dict avec:
            - route: 'direct' (répondre immédiatement) ou 'expert' (passer à DeepSeek)
            - confidence: 0.0-1.0
            - reason: Explication du choix
            - needs_context: True si besoin de Context Agent
            - enhanced_request: Requête bonifiée si route='expert'
        """
        # Vérifier si cache_hits disponible
        cache_hits = context.get('cache_hits', []) if context else []
        has_cache = len(cache_hits) > 0

        triage_prompt = f"""Tu es le PREMIER FILTRE du système. Analyse cette requête et décide du routage optimal.

REQUÊTE: "{user_request}"

CACHE: {"✓ Cache hits disponibles" if has_cache else "✗ Pas de cache"}

TU AS 3 ROUTES POSSIBLES:

1. ROUTE "planner" (demande de PLANIFICATION):
   - Contient "planifie", "crée un plan", "décompose", "organise"
   - Demande EXPLICITE de créer une roadmap
   - Demande d'organiser un projet complexe
   → Escalade vers Planner Agent (modèle moyen)

2. ROUTE "direct" (réponse immédiate sans outils):
   - Conversation simple (salutation, question générale)
   - Requête d'information simple
   - Pas d'outils nécessaires
   → Réponse directe

3. ROUTE "expert" (besoin d'outils):
   - Utilise des outils (fichiers, git, web)
   - Analyse ou génération de contenu
   - Action concrète nécessaire
   → Task Executor avec outils

Pour ROUTE "expert", évalue needs_context:
- true: Modification code existant, analyse architecture
- false: Action simple (delete, read, search, create nouveau fichier)

Réponds UNIQUEMENT avec un JSON:
{{
  "route": "planner|direct|expert",
  "confidence": 0.0-1.0,
  "reason": "explication courte",
  "needs_context": true/false,
  "complexity": "simple|medium|complex"
}}"""

        try:
            response = self.llm_client.complete(
                messages=[{"role": "user", "content": triage_prompt}],
                tier=ModelTier.NANO,  # Ultra-rapide et économique
                max_tokens=1000,  # Increased from 200 to prevent truncation
                temperature=1.0
            )

            # Parser la réponse JSON
            result = json.loads(response.content.strip())

            # Ajouter le coût
            result['cost'] = response.cost

            # Si route='expert', bonifier la requête
            if result['route'] == 'expert' and result['complexity'] != 'simple':
                result['enhanced_request'] = self._enhance_request(user_request)
            else:
                result['enhanced_request'] = user_request

            return result

        except (json.JSONDecodeError, KeyError) as e:
            # Fallback: heuristiques simples
            user_lower = user_request.lower()

            # Mots-clés pour planification
            planning_keywords = [
                'planifie', 'planifier', 'plan',
                'décompose', 'organise', 'structure',
                'roadmap', 'étapes', 'phases'
            ]

            # Mots-clés pour actions nécessitant tools
            action_keywords = [
                'create', 'crée', 'make', 'fais',
                'scrape', 'extract', 'extrais',
                'git', 'commit', 'push',
                'install', 'pip', 'npm',
                'delete', 'efface', 'remove', 'supprime',
                'search', 'find', 'cherche', 'trouve'
            ]

            # Mots-clés pour conversations simples
            simple_keywords = [
                'hello', 'bonjour', 'salut', 'hi',
                'how are you', 'comment ça va', 'ça va',
                'what is', 'qu\'est-ce que', 'c\'est quoi',
                'explain', 'explique'
            ]

            # Détecter le type de requête
            is_planning = any(kw in user_lower for kw in planning_keywords)
            is_simple = any(kw in user_lower for kw in simple_keywords)
            needs_action = any(kw in user_lower for kw in action_keywords)

            # Priorité 1: Planification
            if is_planning:
                return {
                    'route': 'planner',
                    'confidence': 0.75,
                    'reason': 'Planning request detected',
                    'needs_context': False,
                    'complexity': 'medium',
                    'enhanced_request': user_request,
                    'cost': 0.0
                }
            # Priorité 2: Conversation simple
            elif is_simple and not needs_action:
                return {
                    'route': 'direct',
                    'confidence': 0.7,
                    'reason': 'Simple conversation detected',
                    'needs_context': False,
                    'complexity': 'simple',
                    'enhanced_request': user_request,
                    'cost': 0.0
                }
            # Priorité 3: Action avec tools
            else:
                return {
                    'route': 'expert',
                    'confidence': 0.6,
                    'reason': 'Action or complex analysis needed',
                    'needs_context': needs_action and 'code' in user_lower,
                    'complexity': 'medium',
                    'enhanced_request': user_request,
                    'cost': 0.0
                }

    def _enhance_request(self, user_request: str) -> str:
        """
        Bonifie la requête pour l'expert (ajoute contexte, clarifications)

        Args:
            user_request: Requête utilisateur originale

        Returns:
            Requête bonifiée
        """
        # Pour l'instant, retourner tel quel
        # TODO: Implémenter bonification intelligente
        return user_request


def create_triage_agent(llm_client: LLMClient) -> TriageAgent:
    """Factory function pour créer un TriageAgent"""
    return TriageAgent(llm_client)
