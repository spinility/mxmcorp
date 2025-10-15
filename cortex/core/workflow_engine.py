"""
Workflow Engine - Orchestrateur central qui lie tous les départements

Responsabilités:
- Exécute workflows avec consultation automatique Optimization
- Gère TodoList avec checkboxes temps réel
- Enregistre résultats après chaque action
- Déclenche Maintenance après changements code
- Génère rapports CEO automatiquement
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import time

from cortex.core.todolist_manager import TodoListManager, TodoTask
from cortex.core.department_system import DepartmentRegistry
from cortex.departments.optimization.optimization_knowledge import (
    OptimizationKnowledge,
    HistoricalRequest,
    RequestOutcome
)
from cortex.departments.maintenance.git_diff_processor import GitDiffProcessor
from cortex.departments.maintenance.roadmap_manager import RoadmapManager
from cortex.departments.communication.ceo_reporter import CEOReporter


@dataclass
class WorkflowStep:
    """Étape dans un workflow"""
    name: str
    action: Callable
    department: str
    agent_name: str
    required: bool = True  # Si False, continue même si échoue
    consult_optimization: bool = True


@dataclass
class WorkflowResult:
    """Résultat d'exécution d'un workflow"""
    workflow_name: str
    success: bool
    duration_seconds: float
    steps_completed: int
    steps_total: int
    errors: List[str]
    output: Any
    optimization_advice_used: bool


class WorkflowEngine:
    """
    Moteur d'orchestration central

    Pattern d'utilisation:
    1. BEFORE action → Consulte Optimization pour conseils
    2. Exécute workflow → Suit avec TodoList checkboxes
    3. AFTER action → Enregistre résultats dans Optimization
    4. Si code changé → Déclenche Maintenance
    5. En fin de journée → Génère rapport CEO
    """

    def __init__(
        self,
        optimization_knowledge: Optional[OptimizationKnowledge] = None,
        roadmap_manager: Optional[RoadmapManager] = None,
        ceo_reporter: Optional[CEOReporter] = None,
        git_processor: Optional[GitDiffProcessor] = None
    ):
        # Managers
        self.todolist = TodoListManager()
        self.departments = DepartmentRegistry()

        # Départements
        self.optimization = optimization_knowledge or OptimizationKnowledge()
        self.roadmap = roadmap_manager or RoadmapManager()
        self.ceo_reporter = ceo_reporter or CEOReporter()
        self.git_processor = git_processor or GitDiffProcessor()

        # État
        self.current_workflow: Optional[str] = None
        self.current_request: Optional[str] = None

    def execute_workflow(
        self,
        workflow_name: str,
        request_text: str,
        steps: List[WorkflowStep],
        request_type: str = "general"
    ) -> WorkflowResult:
        """
        Exécute un workflow complet avec orchestration automatique

        Args:
            workflow_name: Nom du workflow
            request_text: Requête utilisateur originale
            steps: Liste des étapes à exécuter
            request_type: Type de requête (code/analysis/optimization/etc)

        Returns:
            WorkflowResult avec détails d'exécution
        """
        self.current_workflow = workflow_name
        self.current_request = request_text

        start_time = time.time()
        errors = []
        output = None

        print(f"\n{'='*70}")
        print(f"🚀 WORKFLOW: {workflow_name}")
        print(f"{'='*70}\n")

        # STEP 0: Consulter Optimization AVANT de commencer
        optimization_advice = None
        if steps and steps[0].consult_optimization:
            print("📊 Consulting Optimization Department...")
            optimization_advice = self.optimization.get_optimization_advice(
                request_text=request_text,
                request_type=request_type
            )

            if optimization_advice:
                print(f"✓ Found {optimization_advice['similar_requests_count']} similar past requests")

                if optimization_advice.get("recommended_pattern"):
                    pattern = optimization_advice["recommended_pattern"]
                    print(f"  → Recommended pattern: {pattern['name']} (confidence: {pattern['confidence']:.0%})")

                if optimization_advice.get("warnings"):
                    print(f"  ⚠️  Warnings:")
                    for warning in optimization_advice["warnings"][:3]:
                        print(f"     - {warning}")

                if optimization_advice.get("recommended_tools"):
                    tools = [t["tool"] for t in optimization_advice["recommended_tools"][:3]]
                    print(f"  🔧 Recommended tools: {', '.join(tools)}")

                print()

        # STEP 1: Créer TodoList
        task_names = [step.name for step in steps]
        task_ids = self.todolist.create_task_list(
            task_descriptions=task_names,
            workflow=workflow_name
        )

        # Afficher TodoList initiale
        self.todolist.display()

        # STEP 2: Exécuter chaque étape
        steps_completed = 0

        for i, step in enumerate(steps):
            task_id = task_ids[i]

            try:
                # Marquer tâche en cours
                self.todolist.start_task(task_id, agent_name=step.agent_name)
                print(f"\n🔄 Executing: {step.name}")
                print(f"   Agent: {step.agent_name} ({step.department})")

                # Exécuter action
                step_start = time.time()
                result = step.action()
                step_duration = time.time() - step_start

                # Marquer tâche complétée
                self.todolist.complete_task(
                    task_id,
                    metadata={"duration": step_duration, "result": str(result)[:100]}
                )

                output = result
                steps_completed += 1

                print(f"✅ Completed in {step_duration:.2f}s")

            except Exception as e:
                error_msg = f"Error in {step.name}: {str(e)}"
                errors.append(error_msg)

                self.todolist.fail_task(task_id, error=error_msg)
                print(f"❌ Failed: {error_msg}")

                if step.required:
                    # Échec sur étape requise → arrêter workflow
                    break

        # Afficher TodoList finale
        print()
        self.todolist.display()

        duration = time.time() - start_time
        success = len(errors) == 0 and steps_completed == len(steps)

        # STEP 3: Enregistrer dans Optimization APRÈS exécution
        self._record_in_optimization(
            request_text=request_text,
            workflow_name=workflow_name,
            success=success,
            duration=duration,
            errors=errors,
            steps=steps,
            optimization_advice=optimization_advice
        )

        # STEP 4: Si code a changé → déclencher Maintenance
        if self._should_trigger_maintenance(steps):
            print("\n🔧 Triggering Maintenance Department...")
            self._trigger_maintenance()

        # STEP 5: Envoyer alerte CEO si nécessaire
        if not success:
            self.ceo_reporter.send_alert(
                title=f"Workflow Failed: {workflow_name}",
                message=f"Workflow completed {steps_completed}/{len(steps)} steps. Errors: {'; '.join(errors[:2])}",
                severity="warning",
                source_department="workflow_engine"
            )
        elif steps_completed >= 3:  # Workflow significatif
            self.ceo_reporter.send_alert(
                title=f"Workflow Complete: {workflow_name}",
                message=f"Successfully completed {steps_completed} steps in {duration:.1f}s",
                severity="success",
                source_department="workflow_engine"
            )

        result = WorkflowResult(
            workflow_name=workflow_name,
            success=success,
            duration_seconds=duration,
            steps_completed=steps_completed,
            steps_total=len(steps),
            errors=errors,
            output=output,
            optimization_advice_used=optimization_advice is not None
        )

        print(f"\n{'='*70}")
        print(f"{'✅' if success else '❌'} Workflow {workflow_name}: {'SUCCESS' if success else 'FAILED'}")
        print(f"   Duration: {duration:.2f}s | Steps: {steps_completed}/{len(steps)}")
        print(f"{'='*70}\n")

        return result

    def _record_in_optimization(
        self,
        request_text: str,
        workflow_name: str,
        success: bool,
        duration: float,
        errors: List[str],
        steps: List[WorkflowStep],
        optimization_advice: Optional[Dict[str, Any]]
    ):
        """Enregistre le résultat dans Optimization"""
        outcome = RequestOutcome.SUCCESS if success else RequestOutcome.FAILURE

        agents_involved = list(set(step.agent_name for step in steps))
        patterns_applied = []
        if optimization_advice and optimization_advice.get("recommended_pattern"):
            patterns_applied.append(optimization_advice["recommended_pattern"]["name"])

        request = HistoricalRequest(
            id=f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            request_text=request_text,
            request_type=self.current_request or "general",
            outcome=outcome,
            workflow_used=workflow_name,
            agents_involved=agents_involved,
            duration_seconds=duration,
            cost=0.0,  # À calculer
            files_modified=[],  # À tracker via git
            lines_added=0,  # À tracker via git
            lines_removed=0,  # À tracker via git
            tools_used=[],  # À tracker
            patterns_applied=patterns_applied,
            errors_encountered=errors,
            lessons_learned=[]  # À générer
        )

        self.optimization.record_request(request)
        print(f"📊 Recorded in Optimization Knowledge")

    def _should_trigger_maintenance(self, steps: List[WorkflowStep]) -> bool:
        """Détermine si Maintenance doit être déclenché"""
        # Déclencher si workflow a touché code
        code_departments = ["development", "tooling", "testing"]
        return any(step.department in code_departments for step in steps)

    def _trigger_maintenance(self):
        """Déclenche département Maintenance pour mise à jour automatique"""
        # 1. Analyser git diff
        git_analysis = self.git_processor.get_latest_diff(include_staged=True)

        if git_analysis.total_files_changed == 0:
            print("   No code changes detected")
            return

        print(f"   Detected {git_analysis.total_files_changed} files changed")

        # 2. Mettre à jour roadmap
        updates = self.roadmap.update_from_git_diff(git_analysis)
        print(f"   Roadmap updated:")
        print(f"     Tasks completed: {len(updates['tasks_marked_completed'])}")
        print(f"     New tasks: {len(updates['tasks_detected_new'])}")

        # 3. TODO: Mettre à jour contextes
        # 4. TODO: Mettre à jour graphe de dépendances
        # 5. TODO: Mettre à jour documentation

    def generate_daily_report(self):
        """Génère rapport CEO quotidien"""
        print("\n📊 Generating daily CEO report...")

        # Récupérer git analysis
        git_analysis = self.git_processor.get_latest_diff()

        # Récupérer insights optimization
        insights = []  # TODO: Extraire du optimization knowledge

        # Générer rapport
        report = self.ceo_reporter.generate_daily_report(
            roadmap_manager=self.roadmap,
            git_analysis=git_analysis,
            optimization_insights=insights
        )

        self.ceo_reporter.display_daily_report(report)

        return report

    def generate_weekly_report(self):
        """Génère rapport CEO hebdomadaire"""
        print("\n📊 Generating weekly CEO report...")

        report = self.ceo_reporter.generate_weekly_report(self.roadmap)
        self.ceo_reporter.display_weekly_report(report)

        return report


def create_workflow_engine() -> WorkflowEngine:
    """Factory function"""
    return WorkflowEngine()


# Test
if __name__ == "__main__":
    print("Testing Workflow Engine...")

    engine = create_workflow_engine()

    # Test 1: Workflow simple
    print("\n1. Testing simple workflow...")

    def step1_analyze():
        time.sleep(0.1)
        return "Analysis complete"

    def step2_implement():
        time.sleep(0.2)
        return "Implementation complete"

    def step3_test():
        time.sleep(0.1)
        return "Tests passing"

    steps = [
        WorkflowStep(
            name="Analyze requirements",
            action=step1_analyze,
            department="analysis",
            agent_name="RequirementsAnalyzer"
        ),
        WorkflowStep(
            name="Implement solution",
            action=step2_implement,
            department="development",
            agent_name="CodeImplementer"
        ),
        WorkflowStep(
            name="Run tests",
            action=step3_test,
            department="testing",
            agent_name="TestRunner"
        )
    ]

    result = engine.execute_workflow(
        workflow_name="feature_implementation",
        request_text="Add new feature X with tests",
        steps=steps,
        request_type="code"
    )

    print(f"✓ Workflow result: {result.success}")
    print(f"  Duration: {result.duration_seconds:.2f}s")
    print(f"  Steps: {result.steps_completed}/{result.steps_total}")

    # Test 2: Workflow avec échec
    print("\n2. Testing workflow with failure...")

    def step_fail():
        raise Exception("Simulated failure")

    steps_with_failure = [
        WorkflowStep(
            name="Step that succeeds",
            action=step1_analyze,
            department="analysis",
            agent_name="Agent1"
        ),
        WorkflowStep(
            name="Step that fails",
            action=step_fail,
            department="development",
            agent_name="Agent2"
        ),
        WorkflowStep(
            name="Step that won't run",
            action=step3_test,
            department="testing",
            agent_name="Agent3"
        )
    ]

    result2 = engine.execute_workflow(
        workflow_name="workflow_with_failure",
        request_text="Test error handling",
        steps=steps_with_failure,
        request_type="test"
    )

    print(f"✓ Workflow result: {result2.success}")
    print(f"  Errors: {len(result2.errors)}")

    # Test 3: Générer rapports
    print("\n3. Testing reports...")

    # Ajouter quelques tâches au roadmap
    engine.roadmap.add_task(
        title="Complete Phase 3.2",
        description="Finish all Phase 3.2 components",
        priority="critical",
        estimated_hours=6.0,
        assigned_department="development"
    )

    # Rapport quotidien
    daily = engine.generate_daily_report()
    print("✓ Daily report generated")

    # Rapport hebdomadaire
    weekly = engine.generate_weekly_report()
    print("✓ Weekly report generated")

    print("\n✓ Workflow Engine works correctly!")
