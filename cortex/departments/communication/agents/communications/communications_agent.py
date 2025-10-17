"""
Communications Agent - Responsable de la communication avec l'utilisateur

ROLE: COMMUNICATIONS (Synthesis + Reporting) - Niveau 2 de la hiérarchie
TIER: NANO pour résumés rapides et économiques

NOUVEAU WORKFLOW:
1. Reçoit logs filtrés du workflow (via LogFilterService)
2. Résume le "thinking" de Cortex: décisions prises, alternatives considérées
3. Présente de manière claire pour que l'utilisateur comprenne le raisonnement
4. Facilite feedback: "voici ce qui a été fait, qu'auriez-vous préféré?"

Responsabilités:
- Résumer workflows de requêtes avec thinking transparent
- Expliquer décisions des agents (pourquoi X au lieu de Y)
- Présenter alternatives considérées mais non choisies
- Faciliter feedback utilisateur sur le raisonnement
- Formater recommandations du Tooler (fonctionnalité existante)

Déclenché:
- Après chaque requête utilisateur complétée
- Sur demande utilisateur ("explique-moi ce qui s'est passé")
- En fin de git_integration_workflow
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import time
from cortex.core.llm_client import LLMClient, ModelTier
from cortex.core.agent_hierarchy import DecisionAgent, AgentRole, AgentResult, EscalationContext
from cortex.services.log_filter_service import get_log_filter_service
from cortex.core.agent_memory import get_agent_memory


class CommunicationsAgent(DecisionAgent):
    """Agent responsable de communiquer avec l'utilisateur"""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Communications Agent

        Args:
            llm_client: LLM client for crafting responses
        """
        super().__init__(llm_client, specialization="communications")
        self.log_filter = get_log_filter_service()
        self.memory = get_agent_memory('communication', 'communications')

    def craft_recommendation(
        self,
        tooler_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crée une recommandation claire pour l'utilisateur

        Args:
            tooler_request: Requête du Tooler avec les résultats de recherche

        Returns:
            Recommandation formatée pour l'utilisateur
        """
        start_time = time.time()

        prompt = f"""Tu es un expert en communication technique.
Tu dois expliquer clairement à l'utilisateur ce qui peut être fait.

CONTEXTE:
Requête utilisateur: "{tooler_request['user_request']}"
Capacité manquante: {tooler_request['capability_needed']}

RECHERCHE DU TOOLER:
{tooler_request['research_findings']}

TA MISSION:
Crée un message clair pour l'utilisateur avec:
1. Ce que Cortex ne peut pas faire actuellement
2. Les solutions qui existent
3. Les prochaines étapes recommandées

TON: {tooler_request['tone']} - Sois utile, positif, et actionnable

FORMAT (utilise les emojis):
🎯 **Situation:** [Explication courte de ce qui manque]

🔍 **Solutions trouvées:** [2-3 options avec noms d'outils/packages]

💡 **Recommandation:** [Action concrète que l'utilisateur peut prendre]

⚙️ **Prochaines étapes:**
- [Étape 1]
- [Étape 2]
- [Optionnel: Étape 3]

Sois concis (max 150 mots) mais informatif."""

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Crée la recommandation"}
        ]

        # Utiliser DeepSeek pour la communication (bon équilibre)
        response = self.llm_client.complete(
            messages=messages,
            tier=ModelTier.DEEPSEEK,
            max_tokens=500,
            temperature=0.8
        )

        result = {
            "recommendation_ready": True,
            "message": response.content,
            "model_used": response.model,
            "cost": response.cost
        }

        # Record to memory
        duration = time.time() - start_time
        self.memory.record_execution(
            request=f"Craft recommendation: {tooler_request.get('capability_needed', 'Unknown')}",
            result=result,
            duration=duration,
            cost=response.cost
        )

        # Update state
        self.memory.update_state({
            'last_recommendation_timestamp': datetime.now().isoformat(),
            'last_capability_needed': tooler_request.get('capability_needed')
        })

        # Detect patterns in capability types
        self.memory.add_pattern(
            f'capability_needed_{tooler_request.get("capability_needed", "unknown")}',
            {
                'capability': tooler_request.get('capability_needed'),
                'tone': tooler_request.get('tone'),
                'user_request': tooler_request.get('user_request', '')[:100]
            }
        )

        return result

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """
        Évalue si le CommunicationsAgent peut gérer la requête

        Keywords: explain, summary, workflow, thinking, what happened, why
        """
        request_lower = request.lower()

        comm_keywords = [
            'explain', 'summary', 'workflow', 'thinking',
            'what happened', 'why did', 'how did',
            'summarize', 'tell me about', 'show me'
        ]

        # Haute confiance si contient keywords
        if any(kw in request_lower for kw in comm_keywords):
            return 0.9

        return 0.0

    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[EscalationContext] = None
    ) -> AgentResult:
        """
        Exécute une opération de communication

        Args:
            request: Requête utilisateur
            context: Contexte avec session_start, agents_involved, etc.
            escalation_context: Contexte si escalation

        Returns:
            AgentResult avec résumé/explication
        """
        # Déterminer le type de communication demandé
        if 'workflow' in request.lower() or 'summary' in request.lower():
            result = self.summarize_workflow(context)
        elif 'explain' in request.lower() or 'why' in request.lower():
            result = self.explain_agent_decision(request, context)
        else:
            # Fallback: résumé général
            result = self.summarize_workflow(context)

        return AgentResult(
            success=result['success'],
            role=self.role,
            tier=self.tier,
            content=result,
            cost=result.get('cost', 0.0),
            confidence=0.85,
            should_escalate=False,
            escalation_reason=None,
            error=result.get('error'),
            metadata={'communication_result': result}
        )

    def summarize_workflow(
        self,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Résume le workflow d'une requête avec thinking transparent

        Args:
            context: Contexte avec:
                - session_start: Début de la session
                - request: Requête utilisateur originale
                - agents_involved: Liste des agents impliqués
                - focus: 'all', 'planning', 'execution', 'testing'

        Returns:
            Dict avec:
                - summary: Résumé du workflow
                - thinking: Détails du raisonnement
                - decisions: Décisions clés prises
                - alternatives: Alternatives considérées
                - feedback_prompt: Question pour feedback utilisateur
        """
        start_time = time.time()

        try:
            print(f"\n{'='*70}")
            print(f"💬 COMMUNICATIONS AGENT - Workflow Summary")
            print(f"{'='*70}\n")

            # Récupérer les logs pertinents
            session_start = context.get('session_start') if context else None
            if not session_start:
                session_start = datetime.now()

            logs = self.log_filter.get_workflow_logs(
                session_start=session_start,
                limit=100
            )

            if not logs:
                return {
                    'success': True,
                    'summary': "Aucun workflow récent détecté.",
                    'thinking': {},
                    'decisions': [],
                    'alternatives': [],
                    'feedback_prompt': None,
                    'cost': 0.0
                }

            # Analyser les logs pour extraire thinking
            thinking_analysis = self._analyze_thinking(logs)

            # Construire le résumé avec NANO LLM
            summary_text = self._generate_summary(logs, thinking_analysis, context)

            # Extraire décisions clés
            key_decisions = self._extract_key_decisions(logs)

            # Extraire alternatives considérées
            alternatives = self._extract_alternatives(logs, thinking_analysis)

            # Générer question pour feedback
            feedback_prompt = self._generate_feedback_prompt(key_decisions, alternatives)

            print(f"\n{'='*70}")
            print(f"Summary Generated:")
            print(f"  Logs analyzed: {len(logs)}")
            print(f"  Key decisions: {len(key_decisions)}")
            print(f"  Alternatives found: {len(alternatives)}")
            print(f"{'='*70}\n")

            result = {
                'success': True,
                'action': 'summarize_workflow',
                'summary': summary_text,
                'thinking': thinking_analysis,
                'decisions': key_decisions,
                'alternatives': alternatives,
                'feedback_prompt': feedback_prompt,
                'logs_analyzed': len(logs),
                'cost': 0.0001  # NANO cost estimate
            }

            # Record to memory
            duration = time.time() - start_time
            self.memory.record_execution(
                request=f"Summarize workflow: {len(logs)} logs analyzed",
                result=result,
                duration=duration,
                cost=result['cost']
            )

            # Update state
            self.memory.update_state({
                'last_summary_timestamp': datetime.now().isoformat(),
                'logs_analyzed': len(logs),
                'key_decisions_count': len(key_decisions),
                'alternatives_count': len(alternatives)
            })

            # Detect patterns in workflow types
            agents_involved = set(log.get('author', 'Unknown') for log in logs)
            for agent in agents_involved:
                self.memory.add_pattern(
                    f'agent_involved_{agent}',
                    {
                        'agent': agent,
                        'logs_count': sum(1 for log in logs if log.get('author') == agent)
                    }
                )

            return result

        except Exception as e:
            duration = time.time() - start_time
            result = {
                'success': False,
                'action': 'summarize_workflow',
                'error': f"Workflow summary failed: {str(e)}",
                'cost': 0.0
            }

            # Record failure to memory
            self.memory.record_execution(
                request="Summarize workflow",
                result=result,
                duration=duration,
                cost=0.0
            )

            return result

    def _analyze_thinking(self, logs: List[Dict]) -> Dict[str, Any]:
        """
        Analyse les logs pour extraire le "thinking" de Cortex

        Returns:
            Dict avec:
                - planning: Logs de planification
                - execution: Logs d'exécution
                - testing: Logs de tests
                - escalations: Logs d'escalations
        """
        thinking = {
            'planning': [],
            'execution': [],
            'testing': [],
            'escalations': [],
            'errors': []
        }

        for log in logs:
            change_type = log.get('change_type', '')

            if 'plan' in change_type or 'decision' in change_type:
                thinking['planning'].append(log)
            elif 'execution' in change_type or 'update' in change_type:
                thinking['execution'].append(log)
            elif 'test' in change_type:
                thinking['testing'].append(log)
            elif 'escalation' in change_type:
                thinking['escalations'].append(log)
            elif 'fail' in change_type or 'error' in change_type:
                thinking['errors'].append(log)

        return thinking

    def _generate_summary(
        self,
        logs: List[Dict],
        thinking: Dict[str, Any],
        context: Optional[Dict]
    ) -> str:
        """
        Génère un résumé textuel avec NANO LLM

        Returns:
            Résumé formaté en markdown
        """
        # Préparer un résumé compact des logs pour NANO
        log_summary = {
            'total_logs': len(logs),
            'planning_steps': len(thinking['planning']),
            'execution_steps': len(thinking['execution']),
            'test_steps': len(thinking['testing']),
            'escalations': len(thinking['escalations']),
            'errors': len(thinking['errors'])
        }

        # Extraire agents impliqués
        agents = set(log.get('author', 'Unknown') for log in logs)

        prompt = f"""Tu es le Communications Agent de Cortex. Résume ce workflow de manière claire et concise.

WORKFLOW STATS:
- Logs totaux: {log_summary['total_logs']}
- Agents impliqués: {', '.join(agents)}
- Planning: {log_summary['planning_steps']} décisions
- Exécution: {log_summary['execution_steps']} actions
- Tests: {log_summary['test_steps']} vérifications
- Escalations: {log_summary['escalations']}
- Erreurs: {log_summary['errors']}

RÉSUMÉ (max 100 mots, markdown):
- Commence par "🧠 **Thinking de Cortex:**"
- Explique le flux: planning → exécution → tests
- Mentionne décisions clés et agents responsables
- Sois clair et concis"""

        try:
            response = self.llm_client.complete(
                messages=[{"role": "user", "content": prompt}],
                tier=ModelTier.NANO,
                max_tokens=200
            )
            return response.content

        except Exception as e:
            # Fallback: résumé basique
            return f"""🧠 **Thinking de Cortex:**

{log_summary['planning_steps']} décisions de planification ont été prises par {', '.join(agents)}.
{log_summary['execution_steps']} actions ont été exécutées.
{log_summary['test_steps']} vérifications de tests ont été effectuées.
{log_summary['errors']} erreurs ont été rencontrées."""

    def _extract_key_decisions(self, logs: List[Dict]) -> List[Dict[str, Any]]:
        """
        Extrait les décisions clés du workflow

        Returns:
            Liste de décisions avec agent, description, rationale
        """
        key_decisions = []

        decision_types = [
            'harmonization_plan', 'test_analysis', 'execution_start',
            'agent_decision', 'agent_escalation'
        ]

        for log in logs:
            if log.get('change_type') in decision_types:
                key_decisions.append({
                    'agent': log.get('author', 'Unknown'),
                    'decision': log.get('description', ''),
                    'timestamp': log.get('timestamp'),
                    'impact': log.get('impact_level', 'medium'),
                    'metadata': log.get('metadata', {})
                })

        return key_decisions

    def _extract_alternatives(
        self,
        logs: List[Dict],
        thinking: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extrait les alternatives considérées mais non choisies

        Returns:
            Liste d'alternatives avec description
        """
        alternatives = []

        # Chercher dans les metadata des logs de planification
        for log in thinking['planning']:
            metadata = log.get('metadata', {})

            # HarmonizationAgent inclut alternatives dans ses plans
            if 'alternatives' in metadata:
                alternatives.append({
                    'context': log.get('description'),
                    'alternatives': metadata['alternatives'],
                    'chosen': 'Plan principal sélectionné'
                })

        return alternatives

    def _generate_feedback_prompt(
        self,
        decisions: List[Dict],
        alternatives: List[Dict]
    ) -> str:
        """
        Génère une question pour solliciter feedback utilisateur

        Returns:
            Question formatée en markdown
        """
        if not decisions:
            return "✅ Workflow complété. Avez-vous des commentaires ou suggestions?"

        # Résumer les décisions clés
        decision_summary = []
        for idx, decision in enumerate(decisions[:3], 1):
            agent = decision['agent']
            desc = decision['decision'][:80]
            decision_summary.append(f"{idx}. **{agent}**: {desc}")

        summary_text = "\n".join(decision_summary)

        prompt = f"""💭 **Feedback souhaité:**

Voici les décisions clés prises par Cortex:

{summary_text}

**Question:** Est-ce que ces décisions vous semblent appropriées? Auriez-vous préféré une approche différente?"""

        return prompt

    def explain_agent_decision(
        self,
        request: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Explique une décision spécifique d'un agent

        Args:
            request: Requête utilisateur demandant explication
            context: Contexte

        Returns:
            Dict avec explication détaillée
        """
        start_time = time.time()

        try:
            # Récupérer les logs thinking
            logs = self.log_filter.get_agent_thinking_logs(
                agent_name=None,  # Tous les agents
                time_period='recent',
                limit=50
            )

            # Trouver la décision la plus pertinente à la requête
            # (pour simplification, on prend la plus récente)
            if not logs:
                return {
                    'success': True,
                    'explanation': "Aucune décision récente à expliquer.",
                    'cost': 0.0
                }

            recent_decision = logs[0]

            explanation = f"""🔍 **Explication de décision:**

**Agent:** {recent_decision.get('author')}
**Décision:** {recent_decision.get('description')}
**Timestamp:** {recent_decision.get('timestamp')}
**Impact:** {recent_decision.get('impact_level')}

**Contexte:** {recent_decision.get('metadata', {}).get('context', 'N/A')}

**Rationale:** Cette décision a été prise pour {recent_decision.get('description')}"""

            result = {
                'success': True,
                'action': 'explain_decision',
                'explanation': explanation,
                'decision': recent_decision,
                'cost': 0.0
            }

            # Record to memory
            duration = time.time() - start_time
            self.memory.record_execution(
                request=f"Explain decision: {recent_decision.get('author', 'Unknown')}",
                result=result,
                duration=duration,
                cost=0.0
            )

            # Update state
            self.memory.update_state({
                'last_explanation_timestamp': datetime.now().isoformat(),
                'last_decision_explained': recent_decision.get('description', '')[:100]
            })

            # Detect patterns in decision types explained
            self.memory.add_pattern(
                f'decision_type_{recent_decision.get("change_type", "unknown")}',
                {
                    'agent': recent_decision.get('author'),
                    'change_type': recent_decision.get('change_type'),
                    'impact': recent_decision.get('impact_level')
                }
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            result = {
                'success': False,
                'action': 'explain_decision',
                'error': f"Decision explanation failed: {str(e)}",
                'cost': 0.0
            }

            # Record failure to memory
            self.memory.record_execution(
                request="Explain decision",
                result=result,
                duration=duration,
                cost=0.0
            )

            return result


def create_communications_agent(llm_client: LLMClient) -> CommunicationsAgent:
    """Factory function to create a Communications Agent"""
    return CommunicationsAgent(llm_client)
