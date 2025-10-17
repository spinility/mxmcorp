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
import time
from datetime import datetime

from cortex.core.llm_client import LLMClient, ModelTier
from cortex.core.agent_hierarchy import DecisionAgent, AgentRole, AgentResult
from cortex.core.agent_memory import get_agent_memory


class TriageAgent(DecisionAgent):
    """Agent de triage ultra-rapide pour décisions initiales"""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Triage Agent

        Args:
            llm_client: Client LLM pour l'analyse
        """
        super().__init__(llm_client, specialization="triage")
        self.memory = get_agent_memory('communication', 'triage')

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
        start_time = time.time()

        # Vérifier si cache_hits disponible
        cache_hits = context.get('cache_hits', []) if context else []
        has_cache = len(cache_hits) > 0

        triage_prompt = f"""Tu es le PREMIER FILTRE du système. Analyse cette requête et décide du routage optimal.

REQUÊTE: "{user_request}"

CACHE: {"✓ Cache hits disponibles" if has_cache else "✗ Pas de cache"}

TU AS 4 ROUTES POSSIBLES:

1. ROUTE "quick" (opération atomique READ-ONLY):
   - 1 SEUL outil simple nécessaire
   - Opération de VÉRIFICATION ou CONSULTATION (pas de modification)
   - Exemples: "fichier X existe?", "quelle heure?", "liste fichiers ici", "cherche fichier Y"
   - Outils autorisés: file_exists, list_files, get_current_time, read_env_var, file_stats, search_files
   → Quick Actions Agent (NANO + 1 outil simple)

2. ROUTE "direct" (réponse immédiate sans outils):
   - Conversation simple (salutation, remerciement)
   - Question de CONNAISSANCE GÉNÉRALE (explique OAuth, c'est quoi Python)
   - AUCUN besoin d'accéder au système (fichiers, réseau, etc.)
   → Direct Response Agent (NANO sans outils)

3. ROUTE "expert" (opération complexe ou modification):
   - MULTIPLES outils nécessaires OU
   - Opération de MODIFICATION (créer, éditer, supprimer fichiers, git, etc.) OU
   - Besoin de CONTEXTE ou ANALYSE
   - Exemples: "crée fichier X", "commit git", "analyse le code", "scrape site web"
   → Task Executor (DeepSeek/Claude + tous outils)

4. ROUTE "planner" (demande de planification):
   - Contient "planifie", "crée un plan", "décompose", "organise"
   - Demande EXPLICITE de créer une roadmap
   → Planner Agent

⚠️ IMPORTANT:
- "fichier X existe?" = QUICK (vérification simple, 1 outil read-only)
- "liste fichiers" = QUICK (consultation simple)
- "crée fichier X" = EXPERT (modification système)
- "C'est quoi OAuth?" = DIRECT (connaissance pure)

Pour ROUTE "expert", évalue needs_context:
- true: Modification code existant, analyse architecture
- false: Action simple mais avec modification (delete, create)

Réponds UNIQUEMENT avec un JSON:
{{
  "route": "quick|direct|expert|planner",
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

            # Record to memory
            duration = time.time() - start_time
            self.memory.record_execution(
                request=f"Triage: {user_request[:100]}",
                result=result,
                duration=duration,
                cost=response.cost
            )

            # Update state
            self.memory.update_state({
                'last_triage_timestamp': datetime.now().isoformat(),
                'last_route': result['route'],
                'last_complexity': result['complexity']
            })

            # Detect patterns in triage routes
            self.memory.add_pattern(
                f'route_{result["route"]}',
                {
                    'route': result['route'],
                    'complexity': result['complexity'],
                    'confidence': result['confidence'],
                    'needs_context': result.get('needs_context', False)
                }
            )

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

            # Mots-clés pour actions QUICK (vérifications simples, read-only)
            quick_keywords = [
                'existe', 'exists',
                'liste', 'list', 'ls', 'dir',
                'heure', 'time', 'date', 'now',
                'check', 'vérifie', 'verify',
                'cherche', 'find', 'search', 'trouve',
                'fichier', 'file', 'dossier', 'folder'
            ]

            # Mots-clés pour actions EXPERT (modifications, multiples outils)
            expert_keywords = [
                'create', 'crée', 'make', 'fais',
                'scrape', 'extract', 'extrais',
                'git', 'commit', 'push',
                'install', 'pip', 'npm',
                'delete', 'efface', 'remove', 'supprime',
                'edit', 'modifie', 'modify', 'change'
            ]

            # Mots-clés pour conversations simples (CONNAISSANCE uniquement, pas vérification)
            simple_keywords = [
                'hello', 'bonjour', 'salut', 'hi',
                'how are you', 'comment ça va', 'ça va',
                'thank', 'merci', 'thanks'
            ]

            # Mots-clés pour questions de connaissance (DIRECT si pas de fichier/système)
            knowledge_keywords = [
                'what is', 'qu\'est-ce que', 'c\'est quoi',
                'explain', 'explique', 'how does', 'comment fonctionne'
            ]

            # Détecter le type de requête
            is_planning = any(kw in user_lower for kw in planning_keywords)
            is_quick = any(kw in user_lower for kw in quick_keywords)
            is_expert = any(kw in user_lower for kw in expert_keywords)
            is_simple = any(kw in user_lower for kw in simple_keywords)
            is_knowledge = any(kw in user_lower for kw in knowledge_keywords)

            # Déterminer le résultat basé sur les heuristiques
            # Priorité 1: Planification
            if is_planning:
                result = {
                    'route': 'planner',
                    'confidence': 0.75,
                    'reason': 'Planning request detected',
                    'needs_context': False,
                    'complexity': 'medium',
                    'enhanced_request': user_request,
                    'cost': 0.0
                }
            # Priorité 2: Quick action (vérification simple READ-ONLY)
            # MAIS SEULEMENT si pas de modification demandée
            elif is_quick and not is_expert:
                result = {
                    'route': 'quick',
                    'confidence': 0.80,
                    'reason': 'Simple verification with read-only tool',
                    'needs_context': False,
                    'complexity': 'simple',
                    'enhanced_request': user_request,
                    'cost': 0.0
                }
            # Priorité 3: Expert (modification ou opération complexe)
            elif is_expert or (is_quick and is_expert):
                result = {
                    'route': 'expert',
                    'confidence': 0.75,
                    'reason': 'Tool usage with modification or complex operation',
                    'needs_context': 'code' in user_lower or 'analyse' in user_lower,
                    'complexity': 'simple' if not ('code' in user_lower or 'analyse' in user_lower) else 'medium',
                    'enhanced_request': user_request,
                    'cost': 0.0
                }
            # Priorité 4: Conversation simple (salutation) ou connaissance pure
            elif is_simple or is_knowledge:
                result = {
                    'route': 'direct',
                    'confidence': 0.70,
                    'reason': 'General knowledge question or simple conversation',
                    'needs_context': False,
                    'complexity': 'simple',
                    'enhanced_request': user_request,
                    'cost': 0.0
                }
            # Priorité 5: Par défaut expert
            else:
                result = {
                    'route': 'expert',
                    'confidence': 0.60,
                    'reason': 'Complex request or unclear intent',
                    'needs_context': False,
                    'complexity': 'medium',
                    'enhanced_request': user_request,
                    'cost': 0.0
                }

            # Record fallback to memory
            duration = time.time() - start_time
            self.memory.record_execution(
                request=f"Triage (fallback): {user_request[:100]}",
                result=result,
                duration=duration,
                cost=0.0
            )

            # Update state
            self.memory.update_state({
                'last_triage_timestamp': datetime.now().isoformat(),
                'last_route': result['route'],
                'last_complexity': result['complexity'],
                'fallback_used': True
            })

            # Detect patterns in fallback triage routes
            self.memory.add_pattern(
                f'fallback_route_{result["route"]}',
                {
                    'route': result['route'],
                    'complexity': result['complexity'],
                    'confidence': result['confidence'],
                    'reason': result['reason']
                }
            )

            return result

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
