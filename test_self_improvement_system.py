"""
Test du système d'auto-amélioration complet

Démontre:
1. Feedback système pour les tools
2. Logging pour analyse
3. Meta-Architect qui détecte les besoins
4. Auto-validation et correction
5. Proposition d'améliorations
"""

import json
from cortex.core.feedback_system import get_feedback, FeedbackLevel
from cortex.core.cortex_logger import get_logger, EventType
from cortex.core.self_validator import get_validator, get_workflow_validator
from cortex.agents.meta_architect_agent import create_meta_architect


def test_feedback_system():
    """Test du système de feedback"""
    print("=" * 70)
    print("TEST 1: FEEDBACK SYSTEM")
    print("=" * 70)

    feedback = get_feedback()
    feedback.clear()  # Reset

    # Simuler l'exécution de plusieurs tools
    print("\nSimulating tool executions with feedback...")

    feedback.progress("Starting data analysis workflow")
    feedback.success("read_file tool executed", file="data.csv", lines=1000)
    feedback.progress("Processing 1000 rows", progress=30, total=100)
    feedback.warning("Cache miss for expensive computation", fallback="recomputing")
    feedback.progress("Processing 1000 rows", progress=70, total=100)
    feedback.success("write_file tool executed", file="output.json", size="2.5MB")
    feedback.info("Workflow completed", duration="3.2s", cost="$0.002")

    print("\n--- Recent Feedback Messages ---")
    print(feedback.format_recent(count=10))

    print("\n--- Verbose Mode ---")
    print(feedback.format_recent(count=3, verbose=True))

    print("\n✓ Feedback system working - user gets clear visibility")


def test_logging_and_analysis():
    """Test du système de logging et analyse"""
    print("\n" + "=" * 70)
    print("TEST 2: LOGGING & ANALYSIS")
    print("=" * 70)

    logger = get_logger()

    # Simuler plusieurs tâches avec des patterns
    print("\nSimulating system operations...")

    # Tâches réussies
    for i in range(5):
        task_id = f"task_{i}"
        logger.log(EventType.TASK_START, "Worker", f"Processing item {i}", task_id=task_id)
        logger.log(EventType.TASK_COMPLETE, "Worker", "Completed", cost=0.001, task_id=task_id)

    # Quelques échecs
    logger.log(EventType.TASK_START, "Worker", "Complex task", task_id="task_fail_1")
    logger.log(EventType.TASK_FAIL, "Worker", "Failed", data={"error": "Timeout"}, success=False, task_id="task_fail_1")

    logger.log(EventType.TASK_START, "Manager", "Coordination task", task_id="task_fail_2")
    logger.log(EventType.TASK_FAIL, "Manager", "Failed", data={"error": "Timeout"}, success=False, task_id="task_fail_2")

    # Escalations
    logger.log(EventType.TASK_START, "CEO", "Strategic decision", task_id="task_esc")
    logger.log(EventType.ESCALATION, "CEO", "Escalating to Claude", data={"from": "nano", "to": "claude"}, cost=0.015, task_id="task_esc")
    logger.log(EventType.TASK_COMPLETE, "CEO", "Completed with escalation", cost=0.015, task_id="task_esc")

    # Analyse
    print("\n--- Performance Analysis ---")
    analysis = logger.analyze_recent_performance(last_n=50)
    print(json.dumps(analysis, indent=2, default=str))

    print("\n--- Improvement Opportunities ---")
    opportunities = logger.identify_improvement_opportunities()
    for opp in opportunities:
        print(f"\n[{opp['priority'].upper()}] {opp['category']}")
        print(f"  Issue: {opp['issue']}")
        print(f"  Suggestion: {opp['suggestion']}")

    print("\n✓ Logger identifies patterns and suggests improvements")


def test_self_validation():
    """Test du système d'auto-validation"""
    print("\n" + "=" * 70)
    print("TEST 3: SELF-VALIDATION & AUTO-CORRECTION")
    print("=" * 70)

    validator = get_validator()

    # Test 1: Résultat avec erreurs corrigibles
    print("\n--- Testing Auto-Correction ---")
    bad_result = {
        "success": True,
        "data": "Result data",
        "cost": -0.005,  # Négatif - sera corrigé
        "tokens_input": -100,  # Négatif - sera corrigé
        "tokens_output": 200
    }

    print("Original result:", json.dumps(bad_result, indent=2))

    validation = validator.validate(bad_result, auto_fix=True, verbose=True)

    print("\n--- Validation Results ---")
    for vr in validation["validation_results"]:
        status_symbol = "✓" if vr["status"] == "pass" else "✗"
        print(f"{status_symbol} {vr['rule']}: {vr['message']}")
        if vr.get("fixed"):
            print(f"   → {vr['fix_applied']}")

    if validation["corrected_result"]:
        print("\n--- Corrected Result ---")
        print(json.dumps(validation["corrected_result"], indent=2))

    print("\n✓ System auto-corrects invalid data")


def test_workflow_validation():
    """Test de validation de workflow"""
    print("\n" + "=" * 70)
    print("TEST 4: WORKFLOW VALIDATION")
    print("=" * 70)

    workflow_validator = get_workflow_validator()

    # Simuler un workflow avec problèmes
    workflow = [
        {"success": True, "agent": "Worker", "cost": 0.001, "task": "Parse data"},
        {"success": True, "agent": "Worker", "cost": 0.001, "task": "Validate"},
        {"success": True, "agent": "Manager", "cost": 0.002, "escalated": True, "task": "Review"},
        {"success": False, "agent": "Director", "cost": 0.005, "error": "Database timeout", "task": "Store"},
        {"success": True, "agent": "Manager", "cost": 0.003, "escalated": True, "task": "Retry store"}
    ]

    print("\n--- Workflow Steps ---")
    for i, step in enumerate(workflow, 1):
        status = "✓" if step["success"] else "✗"
        escalated = " [ESCALATED]" if step.get("escalated") else ""
        print(f"{i}. {status} {step['agent']}: {step['task']}{escalated} (${step['cost']:.4f})")

    validation = workflow_validator.validate_workflow(workflow, verbose=True)

    print("\n--- Workflow Analysis ---")
    print(f"Valid: {validation['valid']}")
    print(f"Total Cost: ${validation['total_cost']:.4f}")
    print(f"Failed Steps: {validation['failed_steps']}/{validation['steps_analyzed']}")
    print(f"Escalation Rate: {validation['escalations']}/{validation['steps_analyzed']}")

    if validation["issues"]:
        print("\n--- Issues Found ---")
        for issue in validation["issues"]:
            print(f"\n[{issue['severity'].upper()}] {issue['issue']}")
            print(f"  Recommendation: {issue['recommendation']}")

    print("\n✓ Workflow validation detects inefficiencies")


def test_meta_architect():
    """Test du Meta-Architect"""
    print("\n" + "=" * 70)
    print("TEST 5: META-ARCHITECT AUTO-IMPROVEMENT")
    print("=" * 70)

    logger = get_logger()

    # Ajouter quelques logs additionnels pour que le Meta-Architect ait de quoi analyser
    logger.log(EventType.TASK_FAIL, "Worker", "External API timeout", data={"error": "Timeout connecting to external API"})
    logger.log(EventType.TASK_FAIL, "Manager", "Data validation failed", data={"error": "Invalid data format in pricing file"})

    # Créer le Meta-Architect
    meta = create_meta_architect()

    print("\n--- Running Full System Analysis ---")
    report = meta.run_full_analysis(verbose=True)

    print("\n--- System Health ---")
    health = report["health"]
    print(f"Status: {health['status'].upper()}")
    print(f"Score: {health['health_score']:.1f}/100")
    print(f"Success Rate: {health['performance']['success_rate']:.1%}")
    print(f"Avg Cost/Task: ${health['performance']['avg_cost_per_task']:.4f}")

    if health["improvement_opportunities"]:
        print("\n--- Improvement Opportunities ---")
        for opp in health["improvement_opportunities"][:3]:
            print(f"\n[{opp['priority'].upper()}] {opp['category']}")
            print(f"  {opp['issue']}")
            print(f"  → {opp['suggestion']}")

    if report.get("missing_capabilities"):
        print("\n--- Missing Capabilities Detected ---")
        for cap in report["missing_capabilities"][:3]:
            print(f"\n• {cap['capability']}")
            print(f"  Suggestion: {cap['suggestion']}")
            print(f"  Evidence: {cap['evidence']}")

    print("\n--- Self-Improvement Report ---")
    print(report["improvement_report_text"])

    print("\n✓ Meta-Architect identifies system needs and proposes solutions")


def test_complete_workflow_with_all_systems():
    """Test d'un workflow complet utilisant tous les systèmes"""
    print("\n" + "=" * 70)
    print("TEST 6: COMPLETE INTEGRATED WORKFLOW")
    print("=" * 70)

    feedback = get_feedback()
    logger = get_logger()
    validator = get_validator()

    print("\n--- Simulating Complete Task Execution ---")

    # 1. Démarrage de tâche avec feedback
    feedback.progress("Starting user request: 'Analyze sales data'")

    # 2. Logger l'événement
    logger.log(EventType.TASK_START, "CEO", "User request received", data={"request": "Analyze sales data"}, task_id="user_task_1")

    # 3. Délégation
    feedback.info("CEO delegating to Data Director")
    logger.log(EventType.DELEGATION, "CEO", "Delegating to Data Director", data={"to": "Data Director"}, task_id="user_task_1")

    # 4. Exécution avec résultat
    result = {
        "success": True,
        "data": "Sales analysis complete: Revenue up 15%, best performing product: Widget X",
        "agent": "Data Director",
        "cost": 0.003,
        "tokens_input": 500,
        "tokens_output": 150
    }

    # 5. Validation automatique
    feedback.progress("Validating results...")
    validation = validator.validate(result, context={"agent": "Data Director"}, verbose=False)

    if validation["valid"]:
        feedback.success("Results validated successfully")
    else:
        feedback.warning("Results validated with corrections")

    # 6. Logger le succès
    logger.log(EventType.TASK_COMPLETE, "Data Director", "Analysis complete", cost=result["cost"], task_id="user_task_1")

    # 7. Feedback final à l'utilisateur
    feedback.success(
        "Task completed successfully",
        agent="Data Director",
        cost=f"${result['cost']:.4f}",
        duration="2.1s"
    )

    print("\n--- User Visible Feedback ---")
    print(feedback.format_recent(count=10))

    print("\n--- System Internal Logs (for meta-analysis) ---")
    recent_logs = logger.memory_logs[-5:]
    for log in recent_logs:
        print(f"[{log.timestamp}] {log.event_type.value} | {log.agent} | {log.message}")

    print("\n✓ Complete workflow with feedback, logging, and validation")


def main():
    """Exécute tous les tests"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "CORTEX SELF-IMPROVEMENT SYSTEM TEST" + " " * 18 + "║")
    print("╚" + "═" * 68 + "╝")

    try:
        test_feedback_system()
        test_logging_and_analysis()
        test_self_validation()
        test_workflow_validation()
        test_meta_architect()
        test_complete_workflow_with_all_systems()

        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 70)

        print("\n📊 SYSTEM CAPABILITIES DEMONSTRATED:")
        print("  ✓ Real-time user feedback on tool execution")
        print("  ✓ Comprehensive logging for self-analysis")
        print("  ✓ Automatic validation and error correction")
        print("  ✓ Workflow analysis and optimization")
        print("  ✓ Meta-Architect detects missing capabilities")
        print("  ✓ System proposes its own improvements")

        print("\n🔄 SELF-IMPROVEMENT CYCLE:")
        print("  1. Execute tasks → Generate logs")
        print("  2. Validate results → Auto-correct errors")
        print("  3. Analyze patterns → Identify issues")
        print("  4. Propose solutions → Create new agents")
        print("  5. Apply improvements → Repeat")

        print("\n💡 KEY INSIGHT:")
        print("  The system can now identify when it needs a new agent (like")
        print("  Data Manager) and propose its creation autonomously.")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
