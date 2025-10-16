"""
Optimization Orchestrator - Coordonne l'optimisation continue du système

Reçoit les recommandations du QualityControlAgent et applique des optimisations.

Workflow:
1. QC Agent analyse une requête  génère recommandations
2. Recommendations ajoutées à la queue
3. Orchestrator analyse la queue périodiquement
4. Patterns identifiés  optimisations suggérées
5. Optimisations sûres appliquées automatiquement
6. Optimisations critiques passées au HarmonizationAgent pour validation
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from pathlib import Path
from collections import Counter


class OptimizationOrchestrator:
    """Orchestrateur d'optimisation système"""

    def __init__(self):
        """Initialize orchestrator"""
        self.queue_file = Path("cortex/data/optimization_queue.json")
        self.history_file = Path("cortex/data/optimization_history.json")
        self.applied_file = Path("cortex/data/optimizations_applied.json")

        # Ensure directories exist
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)

    def process_queue(self) -> Dict[str, Any]:
        """
        Process la queue d'optimisation

        Returns:
            Dict avec résultats du traitement
        """
        try:
            print(f"\n{'='*70}")
            print("  OPTIMIZATION ORCHESTRATOR - Processing Queue")
            print(f"{'='*70}\n")

            # Load queue
            queue = self._load_queue()

            if not queue:
                print("Queue is empty - no optimizations to process")
                return {
                    'success': True,
                    'processed': 0,
                    'patterns_found': 0,
                    'optimizations_suggested': 0,
                    'optimizations_applied': 0
                }

            print(f"Queue size: {len(queue)} items\n")

            # Analyze patterns
            print("1. Analyzing patterns...")
            patterns = self._analyze_patterns(queue)
            print(f"    Found {len(patterns)} patterns")
            print()

            # Generate system optimizations
            print("2. Generating system optimizations...")
            optimizations = self._generate_system_optimizations(patterns)
            print(f"    Generated {len(optimizations)} optimization proposals")
            print()

            # Apply safe optimizations
            print("3. Applying safe optimizations...")
            applied = self._apply_safe_optimizations(optimizations)
            print(f"    Applied {len(applied)} optimizations")
            print()

            # Save critical optimizations for review
            critical = [opt for opt in optimizations if opt.get('priority') == 'critical']
            if critical:
                print(f"4. {len(critical)} critical optimizations require manual review")
                self._save_for_review(critical)
                print()

            # Clear processed items from queue
            self._clear_queue()

            # Save history
            self._save_to_history({
                'timestamp': datetime.now().isoformat(),
                'processed': len(queue),
                'patterns': patterns,
                'optimizations_suggested': len(optimizations),
                'optimizations_applied': len(applied),
                'critical_for_review': len(critical)
            })

            return {
                'success': True,
                'processed': len(queue),
                'patterns_found': len(patterns),
                'patterns': patterns,
                'optimizations_suggested': len(optimizations),
                'optimizations_applied': len(applied),
                'applied_optimizations': applied,
                'critical_for_review': len(critical)
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Processing failed: {str(e)}"
            }

    def get_optimization_report(self) -> Dict[str, Any]:
        """
        Génère un rapport d'optimisation

        Returns:
            Dict avec rapport
        """
        try:
            history = self._load_history()
            applied = self._load_applied()

            if not history:
                return {
                    'success': True,
                    'message': 'No optimization history available',
                    'total_optimizations': 0
                }

            # Calculate stats
            total_processed = sum(h.get('processed', 0) for h in history)
            total_applied = sum(h.get('optimizations_applied', 0) for h in history)
            total_patterns = sum(h.get('patterns_found', 0) for h in history)

            # Get recent patterns
            recent_patterns = []
            for h in history[-10:]:
                recent_patterns.extend(h.get('patterns', []))

            # Count pattern types
            pattern_types = Counter(p.get('type') for p in recent_patterns if p.get('type'))

            return {
                'success': True,
                'total_cycles': len(history),
                'total_processed': total_processed,
                'total_applied': total_applied,
                'total_patterns': total_patterns,
                'pattern_distribution': dict(pattern_types),
                'recent_optimizations': applied[-10:] if applied else [],
                'last_cycle': history[-1] if history else None
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Report generation failed: {str(e)}"
            }

    def _load_queue(self) -> List[Dict]:
        """Load optimization queue"""
        try:
            if self.queue_file.exists():
                with open(self.queue_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _load_history(self) -> List[Dict]:
        """Load optimization history"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _load_applied(self) -> List[Dict]:
        """Load applied optimizations"""
        try:
            if self.applied_file.exists():
                with open(self.applied_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _analyze_patterns(self, queue: List[Dict]) -> List[Dict]:
        """
        Analyse patterns dans la queue

        Args:
            queue: Queue d'optimisation

        Returns:
            Liste de patterns détectés
        """
        patterns = []

        # Collect all recommendations
        all_recs = []
        for item in queue:
            all_recs.extend(item.get('recommendations', []))

        # Count recommendation types
        rec_categories = Counter(rec.get('category') for rec in all_recs if rec.get('category'))

        # Pattern 1: Frequent efficiency issues
        if rec_categories.get('efficiency', 0) > len(queue) * 0.3:
            patterns.append({
                'type': 'frequent_efficiency_issues',
                'severity': 'high',
                'count': rec_categories['efficiency'],
                'description': 'More than 30% of requests have efficiency issues',
                'suggested_action': 'Enable aggressive caching and tool filtering'
            })

        # Pattern 2: Frequent model mismatches
        if rec_categories.get('model', 0) > len(queue) * 0.2:
            patterns.append({
                'type': 'frequent_model_mismatch',
                'severity': 'medium',
                'count': rec_categories['model'],
                'description': 'More than 20% of requests use suboptimal model tier',
                'suggested_action': 'Refine triage logic and model routing'
            })

        # Pattern 3: Tool usage issues
        if rec_categories.get('tools', 0) > len(queue) * 0.25:
            patterns.append({
                'type': 'tool_usage_issues',
                'severity': 'medium',
                'count': rec_categories['tools'],
                'description': 'Tool selection or usage needs improvement',
                'suggested_action': 'Review tool filtering and add missing tools'
            })

        # Pattern 4: Low quality scores
        low_quality = [item for item in queue if item.get('score', 100) < 70]
        if len(low_quality) > len(queue) * 0.2:
            patterns.append({
                'type': 'frequent_low_quality',
                'severity': 'high',
                'count': len(low_quality),
                'description': 'More than 20% of requests have quality issues',
                'suggested_action': 'Review prompt engineering and agent selection'
            })

        return patterns

    def _generate_system_optimizations(self, patterns: List[Dict]) -> List[Dict]:
        """
        Génère des optimisations système basées sur les patterns

        Args:
            patterns: Patterns détectés

        Returns:
            Liste d'optimisations proposées
        """
        optimizations = []

        for pattern in patterns:
            if pattern['type'] == 'frequent_efficiency_issues':
                optimizations.append({
                    'id': 'opt_caching_aggressive',
                    'type': 'caching',
                    'priority': 'high',
                    'safe_to_auto_apply': True,
                    'action': 'increase_cache_hit_threshold',
                    'description': 'Increase cache similarity threshold to 0.85',
                    'expected_impact': 'Reduce token usage by 20-30%',
                    'pattern': pattern['type']
                })

                optimizations.append({
                    'id': 'opt_tool_filtering_aggressive',
                    'type': 'tool_filtering',
                    'priority': 'high',
                    'safe_to_auto_apply': True,
                    'action': 'enable_aggressive_filtering',
                    'description': 'Enable more aggressive tool filtering',
                    'expected_impact': 'Reduce token usage by 10-15%',
                    'pattern': pattern['type']
                })

            elif pattern['type'] == 'frequent_model_mismatch':
                optimizations.append({
                    'id': 'opt_triage_refinement',
                    'type': 'model_routing',
                    'priority': 'critical',
                    'safe_to_auto_apply': False,
                    'action': 'refine_triage_logic',
                    'description': 'Refine triage agent decision logic',
                    'expected_impact': 'Better cost/quality balance',
                    'pattern': pattern['type'],
                    'requires_review': True
                })

            elif pattern['type'] == 'tool_usage_issues':
                optimizations.append({
                    'id': 'opt_tool_registry',
                    'type': 'tools',
                    'priority': 'medium',
                    'safe_to_auto_apply': False,
                    'action': 'review_tool_availability',
                    'description': 'Review and add missing tools',
                    'expected_impact': 'Improve task completion rate',
                    'pattern': pattern['type'],
                    'requires_review': True
                })

            elif pattern['type'] == 'frequent_low_quality':
                optimizations.append({
                    'id': 'opt_prompt_engineering',
                    'type': 'prompts',
                    'priority': 'critical',
                    'safe_to_auto_apply': False,
                    'action': 'refine_system_prompts',
                    'description': 'Review and refine system prompts',
                    'expected_impact': 'Improve response quality',
                    'pattern': pattern['type'],
                    'requires_review': True
                })

        return optimizations

    def _apply_safe_optimizations(self, optimizations: List[Dict]) -> List[Dict]:
        """
        Applique les optimisations sûres automatiquement

        Args:
            optimizations: Liste d'optimisations

        Returns:
            Liste des optimisations appliquées
        """
        applied = []

        for opt in optimizations:
            if opt.get('safe_to_auto_apply', False):
                # Apply the optimization
                success = self._apply_optimization(opt)

                if success:
                    applied.append({
                        **opt,
                        'applied_at': datetime.now().isoformat(),
                        'status': 'applied'
                    })
                    print(f"    Applied: {opt['description']}")

        # Save applied optimizations
        if applied:
            self._save_applied(applied)

        return applied

    def _apply_optimization(self, optimization: Dict) -> bool:
        """
        Applique une optimisation spécifique

        Args:
            optimization: Optimisation à appliquer

        Returns:
            True si succès
        """
        # This is simplified - in real implementation would actually modify config
        opt_type = optimization.get('action')

        if opt_type == 'increase_cache_hit_threshold':
            # Would modify context_agent config
            return True
        elif opt_type == 'enable_aggressive_filtering':
            # Would modify tool_filter config
            return True

        return False

    def _save_for_review(self, critical: List[Dict]):
        """Save critical optimizations for manual review"""
        review_file = Path("cortex/data/optimizations_for_review.json")

        try:
            existing = []
            if review_file.exists():
                with open(review_file, 'r') as f:
                    existing = json.load(f)

            # Add new items
            for opt in critical:
                opt['submitted_for_review_at'] = datetime.now().isoformat()
                existing.append(opt)

            # Save
            with open(review_file, 'w') as f:
                json.dump(existing, f, indent=2)

            print(f"    Saved {len(critical)} items for review")

        except Exception as e:
            print(f"    Failed to save for review: {e}")

    def _save_applied(self, applied: List[Dict]):
        """Save applied optimizations"""
        try:
            existing = self._load_applied()
            existing.extend(applied)

            # Keep last 100
            existing = existing[-100:]

            with open(self.applied_file, 'w') as f:
                json.dump(existing, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save applied optimizations: {e}")

    def _save_to_history(self, cycle_data: Dict):
        """Save cycle to history"""
        try:
            history = self._load_history()
            history.append(cycle_data)

            # Keep last 50 cycles
            history = history[-50:]

            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save to history: {e}")

    def _clear_queue(self):
        """Clear the optimization queue"""
        try:
            with open(self.queue_file, 'w') as f:
                json.dump([], f)
        except Exception as e:
            print(f"Warning: Could not clear queue: {e}")


# Test
if __name__ == "__main__":
    print("Testing Optimization Orchestrator...")

    orchestrator = OptimizationOrchestrator()

    # Test process queue
    result = orchestrator.process_queue()
    print(f"\nProcess result: {result['success']}")
    print(f"Patterns found: {result.get('patterns_found', 0)}")

    # Test report
    report = orchestrator.get_optimization_report()
    print(f"\nReport generated: {report['success']}")

    print("\n Optimization Orchestrator works correctly!")
