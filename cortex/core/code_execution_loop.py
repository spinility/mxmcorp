"""
Code Execution Loop - Système autonome de développement avec escalation

Architecture:
1. User Request → Planner → Developer → Tester → Committer
2. If success → Commit + Push
3. If failure → Loop detection → Escalate tier
4. Repeat until success or max escalations reached

Tier Escalation (selon votre spécification):
- Tier 1: DeepSeek-V3.2-Exp (rapide, économique)
- Tier 2: GPT-5 (intelligent, équilibré)
- Tier 3: Claude 4.5 (ultra-puissant, coûteux)
"""

import subprocess
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier
from cortex.agents.developer_agent import DeveloperAgent, create_developer_agent
from cortex.agents.tester_agent import TesterAgent, create_tester_agent, TestStatus
from cortex.core.loop_detector import LoopDetector, create_loop_detector


class ExecutionStatus(Enum):
    """Statut de l'exécution"""
    SUCCESS = "success"
    FAILED_ALL_TIERS = "failed_all_tiers"
    LOOP_DETECTED = "loop_detected"
    TIMEOUT = "timeout"
    MANUAL_INTERVENTION_REQUIRED = "manual_intervention_required"


@dataclass
class ExecutionResult:
    """Résultat d'une exécution complète"""
    status: ExecutionStatus
    task: str
    total_attempts: int
    total_cost: float
    elapsed_time: float
    tier_usage: Dict[str, int]
    final_tier: Optional[str]
    committed: bool
    commit_hash: Optional[str] = None
    error_summary: Optional[str] = None
    report: Optional[Dict[str, Any]] = None


class CodeExecutionLoop:
    """
    Boucle d'exécution autonome avec escalation 3-tier

    Flow:
    1. Developer (DeepSeek) → Tester (Nano) → Success? → Commit
    2. If Failure → Loop detector → Escalate to GPT-5
    3. Developer (GPT-5) → Tester (Nano) → Success? → Commit
    4. If Failure → Loop detector → Escalate to Claude 4.5
    5. Developer (Claude) → Tester (Nano) → Success? → Commit
    6. If Failure → Final Report + Last Commit (WIP)
    """

    # Tier hierarchy selon vos spécifications
    TIER_HIERARCHY = [
        ModelTier.DEEPSEEK,  # Tier 1: rapide, économique
        ModelTier.GPT5,      # Tier 2: intelligent, équilibré
        ModelTier.CLAUDE     # Tier 3: ultra-puissant, coûteux
    ]

    MAX_ATTEMPTS_PER_TIER = 3

    def __init__(
        self,
        llm_client: LLMClient,
        max_cost_per_task: float = 1.0,
        auto_commit: bool = True,
        create_feature_branch: bool = False
    ):
        """
        Initialize Code Execution Loop

        Args:
            llm_client: Client LLM
            max_cost_per_task: Budget maximum par tâche ($)
            auto_commit: Commit automatiquement si succès
            create_feature_branch: Créer une feature branch
        """
        self.llm_client = llm_client
        self.max_cost_per_task = max_cost_per_task
        self.auto_commit = auto_commit
        self.create_feature_branch = create_feature_branch

        # Agents
        self.developer = create_developer_agent(llm_client)
        self.tester = create_tester_agent(llm_client)

        # Loop detector
        self.loop_detector = create_loop_detector(
            max_same_errors=3,
            max_total_attempts=12,  # 3 attempts × 4 tiers possible
            timeout_minutes=30
        )

        # Metrics
        self.total_cost = 0.0
        self.start_time = 0.0

    def execute(
        self,
        task: str,
        filepaths: List[str],
        context: str = ""
    ) -> ExecutionResult:
        """
        Exécute une tâche de développement avec escalation automatique

        Args:
            task: Description de la tâche
            filepaths: Fichiers à modifier
            context: Contexte additionnel

        Returns:
            ExecutionResult avec résultats complets
        """
        self.start_time = time.time()
        print(f"\n{'='*60}")
        print(f"🚀 CODE EXECUTION LOOP STARTED")
        print(f"{'='*60}")
        print(f"Task: {task}")
        print(f"Files: {', '.join(filepaths)}")
        print(f"Max cost: ${self.max_cost_per_task}")
        print(f"{'='*60}\n")

        # Créer feature branch si demandé
        if self.create_feature_branch:
            self._create_feature_branch(task)

        # Boucle d'escalation par tier
        for tier_idx, tier in enumerate(self.TIER_HIERARCHY):
            print(f"\n{'─'*60}")
            print(f"🎯 TIER {tier_idx + 1}: {tier.value.upper()}")
            print(f"{'─'*60}")

            # Tenter plusieurs fois par tier
            for attempt in range(self.MAX_ATTEMPTS_PER_TIER):
                print(f"\n  Attempt {attempt + 1}/{self.MAX_ATTEMPTS_PER_TIER}")

                # Vérifier budget
                if self.total_cost >= self.max_cost_per_task:
                    return self._create_result(
                        ExecutionStatus.TIMEOUT,
                        task,
                        error="Max cost exceeded"
                    )

                # 1. Developer codes
                dev_result = self._developer_step(task, filepaths, tier, context)

                if not dev_result.success:
                    print(f"    ❌ Developer failed: {dev_result.error}")
                    continue

                # 2. Tester validates
                test_result = self._tester_step(filepaths)

                if test_result.status == TestStatus.PASS:
                    # ✅ SUCCESS! Commit and return
                    print(f"\n    ✅ ALL TESTS PASSED!")
                    return self._handle_success(task, dev_result, tier)

                # ❌ Tests failed
                print(f"    ❌ Tests failed: {test_result.recommendation}")

                # Enregistrer tentative dans loop detector
                self.loop_detector.add_attempt(
                    tier=tier.value,
                    diff=dev_result.changes[0].diff if dev_result.changes else "",
                    error=self._format_test_errors(test_result),
                    success=False
                )

                # 3. Détecter boucle
                loop_detection = self.loop_detector.detect_loop()

                if loop_detection.detected:
                    print(f"\n    ⚠️  LOOP DETECTED: {loop_detection.loop_type.value}")
                    print(f"       Confidence: {loop_detection.confidence:.0%}")
                    print(f"       Evidence: {loop_detection.evidence[0]}")
                    break  # Escalate to next tier

            # Fin des tentatives pour ce tier
            print(f"\n  Tier {tier.value} exhausted or loop detected")

        # Tous les tiers épuisés
        print(f"\n{'='*60}")
        print(f"❌ ALL TIERS EXHAUSTED")
        print(f"{'='*60}\n")

        return self._handle_failure(task)

    def _developer_step(
        self,
        task: str,
        filepaths: List[str],
        tier: ModelTier,
        context: str
    ):
        """Exécute l'étape de développement"""
        print(f"    🔨 Developer coding with {tier.value}...")

        result = self.developer.develop(
            task=task,
            filepaths=filepaths,
            tier=tier,
            context=context,
            use_partial_updates=True
        )

        self.total_cost += result.cost
        print(f"       Cost: ${result.cost:.4f} (Total: ${self.total_cost:.4f})")

        if result.success:
            print(f"       ✓ Generated {len(result.changes)} changes")

            # Appliquer les changements
            if self.developer.apply_changes(result.changes, backup=True):
                print(f"       ✓ Changes applied successfully")
            else:
                result.success = False
                result.error = "Failed to apply changes"

        return result

    def _tester_step(self, filepaths: List[str]):
        """Exécute l'étape de test"""
        print(f"    🧪 Tester validating with nano...")

        result = self.tester.validate_code(
            filepaths=filepaths,
            run_tests=True,
            test_timeout=30
        )

        print(f"       Status: {result.status.value}")
        print(f"       Execution time: {result.execution_time:.2f}s")

        if result.syntax_errors:
            print(f"       Syntax errors: {len(result.syntax_errors)}")
        if result.import_errors:
            print(f"       Import errors: {len(result.import_errors)}")
        if result.test_failures:
            print(f"       Test failures: {len(result.test_failures)}")

        return result

    def _format_test_errors(self, test_result) -> str:
        """Formatte les erreurs de test en string"""
        errors = []

        for e in test_result.syntax_errors:
            errors.append(e.message)
        for e in test_result.import_errors:
            errors.append(e.message)
        for e in test_result.test_failures:
            errors.append(e.message)

        return "; ".join(errors[:3])  # Max 3 erreurs

    def _handle_success(self, task: str, dev_result, tier: ModelTier) -> ExecutionResult:
        """Gère le succès - commit les changements"""
        commit_hash = None
        committed = False

        if self.auto_commit:
            print(f"\n  📦 Committing changes...")
            commit_hash = self._commit_changes(
                task=task,
                tier=tier,
                attempt=len(self.loop_detector.attempts)
            )

            if commit_hash:
                print(f"     ✓ Committed: {commit_hash[:8]}")
                committed = True

                # Push to remote
                print(f"  🚀 Pushing to remote...")
                if self._push_changes():
                    print(f"     ✓ Pushed successfully")

        elapsed = time.time() - self.start_time
        stats = self.loop_detector.get_statistics()

        return ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            task=task,
            total_attempts=stats['total_attempts'],
            total_cost=self.total_cost,
            elapsed_time=elapsed,
            tier_usage=stats['tier_distribution'],
            final_tier=tier.value,
            committed=committed,
            commit_hash=commit_hash
        )

    def _handle_failure(self, task: str) -> ExecutionResult:
        """Gère l'échec - génère rapport et commit WIP"""
        print(f"\n  📝 Generating failure report...")

        elapsed = time.time() - self.start_time
        stats = self.loop_detector.get_statistics()

        report = self._generate_failure_report(task, stats)

        # Commit partial work as WIP
        commit_hash = None
        if self.auto_commit:
            print(f"\n  📦 Committing partial work (WIP)...")
            commit_hash = self._commit_wip(task)

        return ExecutionResult(
            status=ExecutionStatus.FAILED_ALL_TIERS,
            task=task,
            total_attempts=stats['total_attempts'],
            total_cost=self.total_cost,
            elapsed_time=elapsed,
            tier_usage=stats['tier_distribution'],
            final_tier=self.TIER_HIERARCHY[-1].value,
            committed=commit_hash is not None,
            commit_hash=commit_hash,
            error_summary="Failed after all tier escalations",
            report=report
        )

    def _generate_failure_report(self, task: str, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un rapport d'échec détaillé"""
        return {
            'task': task,
            'status': 'failed_after_all_escalations',
            'total_attempts': stats['total_attempts'],
            'total_cost': self.total_cost,
            'elapsed_time': stats['elapsed_time'],
            'tier_usage': stats['tier_distribution'],
            'loop_detection': {
                'type': 'multiple_errors' if self.tester.detect_repeated_errors() else 'unknown',
                'evidence': 'See attempt history'
            },
            'recommendation': 'Manual intervention required',
            'next_steps': [
                'Review error logs in attempt history',
                'Check test failures manually',
                'Consider alternative approach',
                'Review WIP commit for partial progress'
            ]
        }

    def _create_feature_branch(self, task: str):
        """Crée une feature branch pour la tâche"""
        # Slugify task name
        branch_name = f"feature/{task.lower().replace(' ', '-')[:50]}"

        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                check=True,
                capture_output=True
            )
            print(f"  ✓ Created feature branch: {branch_name}")
        except subprocess.CalledProcessError:
            print(f"  ⚠️  Could not create branch (already exists?)")

    def _commit_changes(self, task: str, tier: ModelTier, attempt: int) -> Optional[str]:
        """Commit les changements avec un message descriptif"""
        message = f"""feat: {task}

Developed by Code Execution Loop
- Tier: {tier.value}
- Attempt: {attempt}
- Cost: ${self.total_cost:.4f}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

        try:
            # Git add
            subprocess.run(["git", "add", "."], check=True, capture_output=True)

            # Git commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                check=True,
                capture_output=True,
                text=True
            )

            # Extract commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True
            )

            return hash_result.stdout.strip()

        except subprocess.CalledProcessError as e:
            print(f"     ❌ Commit failed: {e}")
            return None

    def _commit_wip(self, task: str) -> Optional[str]:
        """Commit WIP pour travail partiel"""
        message = f"""WIP: {task}

Failed after all tier escalations - needs manual review

Cost: ${self.total_cost:.4f}
Attempts: {len(self.loop_detector.attempts)}

🤖 Generated with [Claude Code](https://claude.com/claude-code)"""

        try:
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            result = subprocess.run(
                ["git", "commit", "-m", message],
                check=True,
                capture_output=True,
                text=True
            )

            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True
            )

            return hash_result.stdout.strip()

        except subprocess.CalledProcessError:
            return None

    def _push_changes(self) -> bool:
        """Push les changements au remote"""
        try:
            subprocess.run(
                ["git", "push"],
                check=True,
                capture_output=True,
                timeout=30
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _create_result(
        self,
        status: ExecutionStatus,
        task: str,
        error: str = None
    ) -> ExecutionResult:
        """Crée un ExecutionResult"""
        elapsed = time.time() - self.start_time
        stats = self.loop_detector.get_statistics()

        return ExecutionResult(
            status=status,
            task=task,
            total_attempts=stats['total_attempts'],
            total_cost=self.total_cost,
            elapsed_time=elapsed,
            tier_usage=stats['tier_distribution'],
            final_tier=None,
            committed=False,
            error_summary=error
        )


def create_code_execution_loop(
    llm_client: LLMClient,
    max_cost_per_task: float = 1.0,
    auto_commit: bool = True
) -> CodeExecutionLoop:
    """Factory function pour créer un CodeExecutionLoop"""
    return CodeExecutionLoop(
        llm_client=llm_client,
        max_cost_per_task=max_cost_per_task,
        auto_commit=auto_commit
    )


# Test si exécuté directement
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    print("Testing Code Execution Loop...")
    print("Note: This is a smoke test, not a full execution\n")

    client = LLMClient()
    loop = CodeExecutionLoop(
        llm_client=client,
        max_cost_per_task=0.10,  # Small budget for test
        auto_commit=False  # Don't actually commit
    )

    print(f"✓ Code Execution Loop initialized")
    print(f"  Tier hierarchy: {[t.value for t in loop.TIER_HIERARCHY]}")
    print(f"  Max attempts per tier: {loop.MAX_ATTEMPTS_PER_TIER}")
    print(f"  Max cost per task: ${loop.max_cost_per_task}")

    print("\n✓ Code Execution Loop works correctly!")
