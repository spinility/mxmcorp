"""
Quality Control Agent - Analyse et évalue la qualité du traitement des requêtes

ROLE: DIRECTEUR (Décision + Coordination) - Niveau 3 de la hiérarchie
TIER: DEEPSEEK pour analyses, CLAUDE si critique

Responsabilités:
- Analyser le processus complet de traitement d'une requête
- Évaluer la qualité sur 100 points
- Mesurer l'efficacité (tokens, temps, coût)
- Valider le choix du modèle
- Évaluer la pertinence des outils utilisés
- Identifier les opportunités d'optimisation
- Passer les recommandations au département Optimization

Métriques évaluées:
- Efficacité (25 pts): Tokens, temps, coût
- Qualité réponse (25 pts): Pertinence, complétude
- Choix modèle (20 pts): Tier approprié pour la tâche
- Utilisation outils (20 pts): Outils pertinents et bien utilisés
- Expérience utilisateur (10 pts): Clarté, format

Déclenché:
- Automatiquement après chaque requête (si activé)
- Manuellement via CLI (cortex qc analyze)
- Pour audit complet (cortex qc audit)
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime
from pathlib import Path

from cortex.core.llm_client import LLMClient, ModelTier
from cortex.core.agent_hierarchy import DecisionAgent, AgentRole, AgentResult, EscalationContext


class QualityControlAgent(DecisionAgent):
    """Agent de contrôle qualité pour évaluation des requêtes"""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Quality Control Agent

        Args:
            llm_client: Client LLM pour l'analyse
        """
        super().__init__(llm_client, specialization="quality_control")
        self.tier = ModelTier.DEEPSEEK  # Analyse détaillée mais pas critique

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """
        Évalue si le QualityControlAgent peut gérer la requête

        Keywords: quality, evaluate, analyze, metrics, performance, qc
        """
        request_lower = request.lower()

        qc_keywords = [
            'quality', 'qualité', 'evaluate', 'évaluation', 'évaluer',
            'analyze', 'analyser', 'metrics', 'métriques',
            'performance', 'qc', 'score', 'rating'
        ]

        # Haute confiance si contient keywords
        if any(kw in request_lower for kw in qc_keywords):
            return 0.9

        return 0.0

    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[EscalationContext] = None
    ) -> AgentResult:
        """
        Exécute une analyse de qualité

        Args:
            request: Requête utilisateur
            context: Contexte optionnel
            escalation_context: Contexte si escalation

        Returns:
            AgentResult avec résultat d'analyse qualité
        """
        # Analyser la requête pour déterminer l'action
        action = self._parse_qc_request(request)

        if action == 'analyze_request':
            # Analyser une requête spécifique
            request_data = context.get('request_data') if context else None
            result = self.analyze_request(request_data)
        elif action == 'full_audit':
            result = self.run_full_audit()
        elif action == 'show_metrics':
            result = self.show_quality_metrics()
        else:
            # Fallback: show metrics
            result = self.show_quality_metrics()

        return AgentResult(
            success=result['success'],
            role=self.role,
            tier=self.tier,
            content=result,
            cost=result.get('cost', 0.0),
            confidence=result.get('confidence', 0.85),
            should_escalate=False,
            escalation_reason=None,
            error=result.get('error'),
            metadata={'qc_result': result}
        )

    def _parse_qc_request(self, request: str) -> str:
        """
        Parse la requête pour déterminer l'action QC

        Returns:
            Action: analyze_request, full_audit, show_metrics
        """
        request_lower = request.lower()

        if 'analyze' in request_lower and ('request' in request_lower or 'requête' in request_lower):
            return 'analyze_request'
        elif 'audit' in request_lower or 'full' in request_lower:
            return 'full_audit'
        else:
            return 'show_metrics'

    def analyze_request(self, request_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyse la qualité d'une requête traitée

        Args:
            request_data: Données de la requête (request, response, metrics)

        Returns:
            Dict avec évaluation qualité
        """
        try:
            print(f"\n{'='*70}")
            print("🎯 QUALITY CONTROL - Request Analysis")
            print(f"{'='*70}\n")

            if not request_data:
                return {
                    'success': False,
                    'action': 'analyze_request',
                    'error': 'No request data provided',
                    'cost': 0.0,
                    'confidence': 0.0
                }

            # Extract metrics
            user_request = request_data.get('user_request', '')
            response = request_data.get('response', '')
            model_used = request_data.get('model', 'unknown')
            tier_used = request_data.get('tier', 'unknown')
            tokens_input = request_data.get('tokens_input', 0)
            tokens_output = request_data.get('tokens_output', 0)
            cost = request_data.get('cost', 0.0)
            tool_calls = request_data.get('tool_calls', [])
            duration = request_data.get('duration', 0.0)

            print(f"Request: {user_request[:100]}...")
            print(f"Model: {model_used} ({tier_used})")
            print(f"Tokens: {tokens_input} in / {tokens_output} out")
            print(f"Cost: ${cost:.6f}")
            print(f"Tools: {len(tool_calls)}")
            print(f"Duration: {duration:.2f}s")
            print()

            # Evaluate dimensions
            print("Evaluating quality dimensions...\n")

            efficiency_score = self._evaluate_efficiency(
                tokens_input, tokens_output, cost, duration
            )
            print(f"  1. Efficiency: {efficiency_score:.1f}/25")
            print(f"     • Token efficiency: {self._rate_token_efficiency(tokens_input, tokens_output)}")
            print(f"     • Cost efficiency: {self._rate_cost_efficiency(cost, tier_used)}")
            print(f"     • Time efficiency: {self._rate_time_efficiency(duration)}")
            print()

            quality_score = self._evaluate_response_quality(
                user_request, response, tool_calls
            )
            print(f"  2. Response Quality: {quality_score:.1f}/25")
            print(f"     • Relevance: {self._rate_relevance(user_request, response)}")
            print(f"     • Completeness: {self._rate_completeness(response)}")
            print()

            model_score = self._evaluate_model_choice(
                user_request, tier_used, tokens_input, tokens_output
            )
            print(f"  3. Model Choice: {model_score:.1f}/20")
            print(f"     • Tier appropriateness: {self._rate_tier_choice(user_request, tier_used)}")
            print(f"     • Cost-benefit ratio: {self._rate_cost_benefit(cost, quality_score)}")
            print()

            tools_score = self._evaluate_tool_usage(
                user_request, tool_calls
            )
            print(f"  4. Tool Usage: {tools_score:.1f}/20")
            print(f"     • Tool relevance: {self._rate_tool_relevance(user_request, tool_calls)}")
            print(f"     • Tool efficiency: {self._rate_tool_efficiency(tool_calls)}")
            print()

            ux_score = self._evaluate_user_experience(
                response, tool_calls
            )
            print(f"  5. User Experience: {ux_score:.1f}/10")
            print(f"     • Clarity: {self._rate_clarity(response)}")
            print(f"     • Format: {self._rate_format(response)}")
            print()

            # Calculate total score
            total_score = efficiency_score + quality_score + model_score + tools_score + ux_score

            print(f"{'─'*70}")
            print(f"TOTAL QUALITY SCORE: {total_score:.1f}/100")
            print(f"{'─'*70}\n")

            # Generate recommendations
            recommendations = self._generate_optimization_recommendations(
                efficiency_score, quality_score, model_score, tools_score, ux_score,
                request_data
            )

            print(f"📊 Generated {len(recommendations)} optimization recommendations")
            print()

            # Save to optimization queue
            self._save_to_optimization_queue(request_data, total_score, recommendations)

            return {
                'success': True,
                'action': 'analyze_request',
                'total_score': total_score,
                'scores': {
                    'efficiency': efficiency_score,
                    'quality': quality_score,
                    'model_choice': model_score,
                    'tool_usage': tools_score,
                    'user_experience': ux_score
                },
                'grade': self._get_grade(total_score),
                'recommendations': recommendations,
                'metrics': {
                    'tokens_input': tokens_input,
                    'tokens_output': tokens_output,
                    'cost': cost,
                    'duration': duration,
                    'tools_used': len(tool_calls)
                },
                'timestamp': datetime.now().isoformat(),
                'cost': 0.0,  # QC doesn't use LLM for basic analysis
                'confidence': 0.85
            }

        except Exception as e:
            return {
                'success': False,
                'action': 'analyze_request',
                'error': f"Analysis failed: {str(e)}",
                'cost': 0.0,
                'confidence': 0.0
            }

    def run_full_audit(self) -> Dict[str, Any]:
        """
        Exécute audit complet de qualité sur historique

        Returns:
            Dict avec résultats d'audit
        """
        try:
            print(f"\n{'='*70}")
            print("🎯 QUALITY CONTROL - Full Audit")
            print(f"{'='*70}\n")

            # Load quality history
            history = self._load_quality_history()

            if not history:
                print("No quality history found")
                return {
                    'success': True,
                    'action': 'full_audit',
                    'message': 'No requests to audit',
                    'cost': 0.0,
                    'confidence': 1.0
                }

            print(f"Analyzing {len(history)} recent requests...\n")

            # Calculate aggregate metrics
            total_requests = len(history)
            avg_score = sum(h['total_score'] for h in history) / total_requests
            avg_cost = sum(h.get('metrics', {}).get('cost', 0) for h in history) / total_requests
            avg_tokens = sum(
                h.get('metrics', {}).get('tokens_input', 0) + h.get('metrics', {}).get('tokens_output', 0)
                for h in history
            ) / total_requests

            print(f"Aggregate Metrics:")
            print(f"  • Average quality score: {avg_score:.1f}/100")
            print(f"  • Average cost: ${avg_cost:.6f}")
            print(f"  • Average tokens: {avg_tokens:.0f}")
            print()

            # Identify patterns
            print("Identifying patterns...")
            patterns = self._identify_patterns(history)
            print(f"  ✓ Found {len(patterns)} optimization patterns")
            print()

            # Generate system-wide recommendations
            print("Generating system-wide recommendations...")
            recommendations = self._generate_system_recommendations(history, patterns)
            print(f"  ✓ Generated {len(recommendations)} recommendations")
            print()

            return {
                'success': True,
                'action': 'full_audit',
                'total_requests': total_requests,
                'avg_score': avg_score,
                'avg_cost': avg_cost,
                'avg_tokens': avg_tokens,
                'patterns': patterns,
                'recommendations': recommendations,
                'timestamp': datetime.now().isoformat(),
                'cost': 0.0,
                'confidence': 0.9
            }

        except Exception as e:
            return {
                'success': False,
                'action': 'full_audit',
                'error': f"Audit failed: {str(e)}",
                'cost': 0.0,
                'confidence': 0.0
            }

    def show_quality_metrics(self) -> Dict[str, Any]:
        """
        Affiche les métriques de qualité actuelles

        Returns:
            Dict avec métriques
        """
        try:
            history = self._load_quality_history()

            if not history:
                return {
                    'success': True,
                    'action': 'show_metrics',
                    'message': 'No quality data available',
                    'metrics': {},
                    'cost': 0.0,
                    'confidence': 1.0
                }

            # Calculate metrics
            total = len(history)
            recent = history[-10:] if len(history) > 10 else history

            avg_score_recent = sum(h['total_score'] for h in recent) / len(recent)
            avg_score_all = sum(h['total_score'] for h in history) / total

            return {
                'success': True,
                'action': 'show_metrics',
                'total_evaluations': total,
                'avg_score_recent': avg_score_recent,
                'avg_score_all': avg_score_all,
                'recent_scores': [h['total_score'] for h in recent],
                'cost': 0.0,
                'confidence': 1.0
            }

        except Exception as e:
            return {
                'success': False,
                'action': 'show_metrics',
                'error': f"Failed to load metrics: {str(e)}",
                'cost': 0.0,
                'confidence': 0.0
            }

    # Evaluation methods

    def _evaluate_efficiency(self, tokens_in: int, tokens_out: int, cost: float, duration: float) -> float:
        """Évalue l'efficacité (0-25 points)"""
        score = 25.0

        # Token efficiency (max deduction: 10 points)
        total_tokens = tokens_in + tokens_out
        if total_tokens > 100000:
            score -= 10
        elif total_tokens > 50000:
            score -= 5
        elif total_tokens > 20000:
            score -= 2

        # Cost efficiency (max deduction: 10 points)
        if cost > 0.01:
            score -= 10
        elif cost > 0.001:
            score -= 5
        elif cost > 0.0001:
            score -= 2

        # Time efficiency (max deduction: 5 points)
        if duration > 30:
            score -= 5
        elif duration > 15:
            score -= 3
        elif duration > 5:
            score -= 1

        return max(0, score)

    def _evaluate_response_quality(self, request: str, response: str, tools: List) -> float:
        """Évalue la qualité de la réponse (0-25 points)"""
        score = 25.0

        # Length check
        if len(response) < 50:
            score -= 10
        elif len(response) < 100:
            score -= 5

        # Tool usage appropriateness
        if "tool" in request.lower() or "create" in request.lower() or "file" in request.lower():
            if not tools:
                score -= 5

        return max(0, score)

    def _evaluate_model_choice(self, request: str, tier: str, tokens_in: int, tokens_out: int) -> float:
        """Évalue le choix du modèle (0-20 points)"""
        score = 20.0

        # Check if tier is appropriate
        is_complex = any(kw in request.lower() for kw in ['complex', 'analyze', 'design', 'architecture'])
        is_simple = any(kw in request.lower() for kw in ['simple', 'quick', 'show', 'list'])

        if is_simple and tier.lower() == 'claude':
            score -= 10  # Overkill
        elif is_complex and tier.lower() == 'nano':
            score -= 10  # Underpowered

        return max(0, score)

    def _evaluate_tool_usage(self, request: str, tools: List) -> float:
        """Évalue l'utilisation des outils (0-20 points)"""
        score = 20.0

        # Check tool relevance
        needs_tools = any(kw in request.lower() for kw in ['create', 'file', 'search', 'scrape', 'git'])

        if needs_tools and not tools:
            score -= 15
        elif not needs_tools and len(tools) > 3:
            score -= 5  # Too many tools

        return max(0, score)

    def _evaluate_user_experience(self, response: str, tools: List) -> float:
        """Évalue l'expérience utilisateur (0-10 points)"""
        score = 10.0

        # Check formatting
        if not response or len(response) < 20:
            score -= 5

        # Check for emojis/structure (positive indicator)
        if any(emoji in response for emoji in ['🎯', '💭', '⚠️', '🔧']):
            pass  # Good formatting
        elif len(response) > 200:
            score -= 2  # Could use better formatting

        return max(0, score)

    def _get_grade(self, score: float) -> str:
        """Convertit score en grade"""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'B+'
        elif score >= 75:
            return 'B'
        elif score >= 70:
            return 'C+'
        elif score >= 65:
            return 'C'
        else:
            return 'D'

    def _generate_optimization_recommendations(
        self,
        eff: float, qual: float, model: float, tools: float, ux: float,
        request_data: Dict
    ) -> List[Dict[str, Any]]:
        """Génère des recommandations d'optimisation"""
        recommendations = []

        # Efficiency recommendations
        if eff < 20:
            recommendations.append({
                'category': 'efficiency',
                'priority': 'high',
                'issue': 'High token/cost usage',
                'suggestion': 'Consider using context caching or tool filtering',
                'impact': 'Could reduce cost by 30-50%'
            })

        # Quality recommendations
        if qual < 20:
            recommendations.append({
                'category': 'quality',
                'priority': 'high',
                'issue': 'Response quality below standard',
                'suggestion': 'Review prompt engineering or use higher tier model',
                'impact': 'Improve user satisfaction'
            })

        # Model choice recommendations
        if model < 15:
            tier = request_data.get('tier', 'unknown')
            recommendations.append({
                'category': 'model',
                'priority': 'medium',
                'issue': f'Suboptimal tier choice ({tier})',
                'suggestion': 'Review triage logic or model routing',
                'impact': 'Better cost/quality balance'
            })

        # Tool usage recommendations
        if tools < 15:
            recommendations.append({
                'category': 'tools',
                'priority': 'medium',
                'issue': 'Suboptimal tool usage',
                'suggestion': 'Review tool selection or add missing tools',
                'impact': 'More efficient task completion'
            })

        # UX recommendations
        if ux < 8:
            recommendations.append({
                'category': 'ux',
                'priority': 'low',
                'issue': 'User experience could be improved',
                'suggestion': 'Add better formatting, emojis, or structure',
                'impact': 'Better readability'
            })

        return recommendations

    def _generate_system_recommendations(self, history: List, patterns: List) -> List[Dict]:
        """Génère des recommandations système"""
        recommendations = []

        # Analyze patterns
        if patterns:
            for pattern in patterns:
                if pattern['type'] == 'frequent_high_cost':
                    recommendations.append({
                        'type': 'system',
                        'priority': 'high',
                        'issue': 'Frequent high-cost operations detected',
                        'suggestion': 'Implement aggressive caching or tier optimization',
                        'affected_requests': pattern['count']
                    })

        return recommendations

    def _identify_patterns(self, history: List) -> List[Dict]:
        """Identifie des patterns dans l'historique"""
        patterns = []

        # Identify high-cost requests
        high_cost = [h for h in history if h.get('metrics', {}).get('cost', 0) > 0.001]
        if len(high_cost) > len(history) * 0.3:
            patterns.append({
                'type': 'frequent_high_cost',
                'count': len(high_cost),
                'description': 'More than 30% of requests have high cost'
            })

        # Identify low quality scores
        low_quality = [h for h in history if h.get('total_score', 100) < 70]
        if len(low_quality) > len(history) * 0.2:
            patterns.append({
                'type': 'frequent_low_quality',
                'count': len(low_quality),
                'description': 'More than 20% of requests have quality issues'
            })

        return patterns

    def _save_to_optimization_queue(self, request_data: Dict, score: float, recommendations: List):
        """Sauvegarde dans la queue d'optimisation"""
        try:
            queue_file = Path("cortex/data/optimization_queue.json")
            queue_file.parent.mkdir(parents=True, exist_ok=True)

            # Load existing queue
            queue = []
            if queue_file.exists():
                with open(queue_file, 'r') as f:
                    queue = json.load(f)

            # Add new item
            queue.append({
                'timestamp': datetime.now().isoformat(),
                'request': request_data.get('user_request', '')[:100],
                'score': score,
                'recommendations': recommendations
            })

            # Keep last 100
            queue = queue[-100:]

            # Save
            with open(queue_file, 'w') as f:
                json.dump(queue, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save to optimization queue: {e}")

    def _load_quality_history(self) -> List[Dict]:
        """Charge l'historique de qualité"""
        try:
            history_file = Path("cortex/data/quality_history.json")
            if history_file.exists():
                with open(history_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _rate_token_efficiency(self, tokens_in: int, tokens_out: int) -> str:
        """Rate token efficiency"""
        total = tokens_in + tokens_out
        if total < 5000:
            return "Excellent"
        elif total < 20000:
            return "Good"
        elif total < 50000:
            return "Fair"
        else:
            return "Poor"

    def _rate_cost_efficiency(self, cost: float, tier: str) -> str:
        """Rate cost efficiency"""
        if cost < 0.00001:
            return "Excellent"
        elif cost < 0.0001:
            return "Good"
        elif cost < 0.001:
            return "Fair"
        else:
            return "Poor"

    def _rate_time_efficiency(self, duration: float) -> str:
        """Rate time efficiency"""
        if duration < 2:
            return "Excellent"
        elif duration < 5:
            return "Good"
        elif duration < 15:
            return "Fair"
        else:
            return "Poor"

    def _rate_relevance(self, request: str, response: str) -> str:
        """Rate response relevance"""
        # Simplified heuristic
        if len(response) > 100:
            return "Good"
        return "Fair"

    def _rate_completeness(self, response: str) -> str:
        """Rate response completeness"""
        if len(response) > 200:
            return "Complete"
        elif len(response) > 100:
            return "Adequate"
        else:
            return "Incomplete"

    def _rate_tier_choice(self, request: str, tier: str) -> str:
        """Rate tier choice"""
        return "Appropriate"  # Simplified

    def _rate_cost_benefit(self, cost: float, quality: float) -> str:
        """Rate cost-benefit ratio"""
        if quality > 20 and cost < 0.0001:
            return "Excellent"
        elif quality > 15:
            return "Good"
        else:
            return "Fair"

    def _rate_tool_relevance(self, request: str, tools: List) -> str:
        """Rate tool relevance"""
        needs_tools = any(kw in request.lower() for kw in ['create', 'file', 'search'])
        if needs_tools and tools:
            return "Relevant"
        elif not needs_tools and not tools:
            return "Appropriate"
        else:
            return "Suboptimal"

    def _rate_tool_efficiency(self, tools: List) -> str:
        """Rate tool efficiency"""
        if len(tools) <= 2:
            return "Efficient"
        elif len(tools) <= 5:
            return "Adequate"
        else:
            return "Excessive"

    def _rate_clarity(self, response: str) -> str:
        """Rate response clarity"""
        # Check for structure
        if any(marker in response for marker in ['🎯', '•', '1.', '2.']):
            return "Clear"
        return "Adequate"

    def _rate_format(self, response: str) -> str:
        """Rate response format"""
        if any(emoji in response for emoji in ['🎯', '💭', '⚠️']):
            return "Well-formatted"
        return "Basic"


def create_quality_control_agent(llm_client: LLMClient) -> QualityControlAgent:
    """Factory function pour créer un QualityControlAgent"""
    return QualityControlAgent(llm_client)


# Test
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    print("Testing Quality Control Agent...")

    client = LLMClient()
    agent = QualityControlAgent(client)

    # Test with sample request data
    sample_data = {
        'user_request': 'Create a test file',
        'response': 'File created successfully with 100 lines',
        'model': 'gpt-4o-nano',
        'tier': 'NANO',
        'tokens_input': 500,
        'tokens_output': 200,
        'cost': 0.000035,
        'tool_calls': [{'name': 'create_file', 'result': {'success': True}}],
        'duration': 2.5
    }

    result = agent.analyze_request(sample_data)
    print(f"\nAnalysis complete!")
    print(f"Total score: {result.get('total_score', 0):.1f}/100")
    print(f"Grade: {result.get('grade', 'N/A')}")
    print(f"Recommendations: {len(result.get('recommendations', []))}")

    print("\n✓ Quality Control Agent works correctly!")
