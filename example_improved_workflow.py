"""
Exemple de workflow amélioré avec tous les systèmes intégrés

Démontre comment le CEO utilise maintenant:
- Feedback utilisateur automatique
- Logging pour auto-analyse
- Validation automatique des résultats
- Détection et correction des problèmes
"""

from cortex.core.feedback_system import get_feedback
from cortex.core.cortex_logger import get_logger, EventType
from cortex.core.self_validator import get_validator
from cortex.agents.meta_architect_agent import create_meta_architect
from cortex.agents.data_manager_agent import create_data_manager


def example_workflow_with_feedback():
    """
    Exemple : Une requête utilisateur qui passe par tout le système
    """
    print("\n" + "=" * 70)
    print("EXEMPLE: Workflow utilisateur complet avec feedback")
    print("=" * 70)

    feedback = get_feedback()
    logger = get_logger()
    validator = get_validator()

    # Simuler une requête utilisateur
    user_request = "Quel est le coût actuel pour analyser 100k tokens avec chaque modèle?"

    print(f"\n📥 User Request: {user_request}\n")

    # 1. FEEDBACK: Informer l'utilisateur
    feedback.progress("Processing your request...")

    # 2. LOGGING: Logger la requête
    logger.log(
        event_type=EventType.TASK_START,
        agent="CEO",
        message="New user request",
        data={"request": user_request},
        task_id="user_req_001"
    )

    # 3. CEO décide de déléguer au Data Manager
    feedback.info("Routing to Data Manager agent")

    logger.log(
        event_type=EventType.DELEGATION,
        agent="CEO",
        message="Delegating to Data Manager",
        data={"reason": "Pricing information request"},
        task_id="user_req_001"
    )

    # 4. Data Manager exécute
    feedback.progress("Data Manager fetching pricing data...")

    data_manager = create_data_manager()
    pricing_result = data_manager.execute_data_task({"type": "verify_pricing"})

    # 5. Calculer les coûts pour 100k tokens
    if pricing_result["success"]:
        feedback.progress("Calculating costs for 100k tokens...")

        costs = {}
        for model, prices in pricing_result["prices"].items():
            # 100k tokens = 0.1M tokens
            input_cost = prices["input"] * 0.1
            output_cost = prices["output"] * 0.1
            total = input_cost + output_cost

            costs[model] = {
                "input_cost": input_cost,
                "output_cost": output_cost,
                "total_cost": total,
                "model_name": prices["name"]
            }

        # Créer le résultat final
        result = {
            "success": True,
            "data": costs,
            "agent": "Data Manager",
            "cost": 0.0001,  # Coût du Data Manager lui-même
            "tokens_input": 50,
            "tokens_output": 200
        }

        # 6. VALIDATION: Valider le résultat
        feedback.progress("Validating results...")
        validated_result = validator.validate_and_apply(
            result,
            context={"agent": "Data Manager", "task": user_request}
        )

        # 7. LOGGING: Logger la complétion
        logger.log(
            event_type=EventType.TASK_COMPLETE,
            agent="Data Manager",
            message="Pricing calculation complete",
            data={"models_analyzed": len(costs)},
            cost=result["cost"],
            task_id="user_req_001"
        )

        # 8. FEEDBACK: Retourner le résultat à l'utilisateur
        feedback.success(
            "Analysis complete!",
            models_analyzed=len(costs),
            cost=f"${result['cost']:.6f}"
        )

        print("\n📊 RESULTS:\n")
        print("Cost analysis for 100,000 tokens (50k input + 50k output):\n")

        for model, cost_data in costs.items():
            print(f"  {model.upper()} ({cost_data['model_name']})")
            print(f"    Input cost:  ${cost_data['input_cost']:.4f}")
            print(f"    Output cost: ${cost_data['output_cost']:.4f}")
            print(f"    TOTAL:       ${cost_data['total_cost']:.4f}")
            print()

        # Ajouter une recommandation
        cheapest = min(costs.items(), key=lambda x: x[1]["total_cost"])
        most_expensive = max(costs.items(), key=lambda x: x[1]["total_cost"])

        print(f"  💡 Recommendation:")
        print(f"     Cheapest: {cheapest[0].upper()} (${cheapest[1]['total_cost']:.4f})")
        print(f"     Most expensive: {most_expensive[0].upper()} (${most_expensive[1]['total_cost']:.4f})")
        print(f"     Savings: {most_expensive[1]['total_cost'] / cheapest[1]['total_cost']:.1f}x cheaper with {cheapest[0]}")

    else:
        feedback.error(
            "Failed to fetch pricing data",
            error=pricing_result.get("error", "Unknown")
        )

    # 9. Afficher le feedback complet
    print("\n" + "=" * 70)
    print("USER-VISIBLE FEEDBACK HISTORY:")
    print("=" * 70)
    print(feedback.format_all())


def example_meta_analysis():
    """
    Exemple : Le Meta-Architect analyse le système après plusieurs tâches
    """
    print("\n\n" + "=" * 70)
    print("EXEMPLE: Meta-Architect analyse le système")
    print("=" * 70)

    logger = get_logger()
    feedback = get_feedback()

    # Simuler quelques tâches additionnelles pour avoir des données
    feedback.clear()

    print("\n🔍 Running system analysis...\n")

    # Créer le Meta-Architect
    meta = create_meta_architect()

    # Analyse complète
    feedback.progress("Meta-Architect analyzing system performance...")

    report = meta.analyze_system_health(verbose=False)

    print("=" * 70)
    print("SYSTEM HEALTH REPORT")
    print("=" * 70)

    print(f"\n📊 Overall Health: {report['status'].upper()}")
    print(f"   Score: {report['health_score']:.1f}/100")

    print(f"\n📈 Performance Metrics:")
    perf = report['performance']
    print(f"   Success Rate:     {perf['success_rate']:.1%}")
    print(f"   Total Tasks:      {perf['total_tasks']}")
    print(f"   Failed Tasks:     {perf['failed_tasks']}")
    print(f"   Escalation Rate:  {perf['escalation_rate']:.1%}")
    print(f"   Total Cost:       ${perf['total_cost']:.4f}")
    print(f"   Avg Cost/Task:    ${perf['avg_cost_per_task']:.6f}")

    if perf['most_used_agents']:
        print(f"\n🤖 Most Active Agents:")
        for agent, count in perf['most_used_agents'][:5]:
            print(f"   - {agent}: {count} events")

    if report['improvement_opportunities']:
        print(f"\n💡 Improvement Opportunities:")
        for i, opp in enumerate(report['improvement_opportunities'], 1):
            print(f"\n   {i}. [{opp['priority'].upper()}] {opp['category']}")
            print(f"      Issue: {opp['issue']}")
            print(f"      → {opp['suggestion']}")

    # Détecter les capacités manquantes
    missing = meta.detect_missing_capabilities(verbose=False)

    if missing:
        print(f"\n🔧 Missing Capabilities Detected:")
        for cap in missing[:3]:
            print(f"\n   • {cap['capability']}")
            print(f"     Suggestion: {cap['suggestion']}")

    feedback.success("System analysis complete")

    print("\n" + "=" * 70)

    # Recommandations finales
    if report['health_score'] < 70:
        print("\n⚠️  SYSTEM NEEDS ATTENTION")
        print("   The Meta-Architect recommends immediate review and improvements.")
    elif report['health_score'] < 90:
        print("\n✓ SYSTEM PERFORMING ADEQUATELY")
        print("   Some optimizations recommended for better performance.")
    else:
        print("\n✓✓ SYSTEM PERFORMING EXCELLENTLY")
        print("   Continue current operations.")


def example_self_healing():
    """
    Exemple : Le système détecte et corrige automatiquement un problème
    """
    print("\n\n" + "=" * 70)
    print("EXEMPLE: Auto-correction d'un problème récurrent")
    print("=" * 70)

    feedback = get_feedback()
    logger = get_logger()
    meta = create_meta_architect()

    feedback.clear()

    print("\n🔍 Detecting recurring issues...\n")

    # Simuler des échecs récurrents
    for i in range(3):
        logger.log(
            event_type=EventType.TASK_FAIL,
            agent="Worker",
            message=f"Database timeout #{i+1}",
            data={"error": "Connection timeout to database"},
            success=False,
            task_id=f"fail_{i}"
        )

    # Analyser
    analysis = logger.analyze_recent_performance(last_n=50)

    if analysis["recurring_issues"]:
        print("📋 Recurring issues detected:")
        for issue, count in analysis["recurring_issues"]:
            if count >= 3:
                print(f"\n   ⚠️  '{issue}' occurred {count} times")

                feedback.warning(
                    f"Recurring issue detected: {issue}",
                    occurrences=count
                )

                # Le Meta-Architect propose une correction
                print("\n   🤖 Meta-Architect analyzing root cause...")

                correction = meta.auto_correct_recurring_issue(
                    issue=issue,
                    occurrences=count,
                    verbose=False
                )

                if correction["success"]:
                    print("\n   ✓ Auto-correction plan generated:")
                    print(f"\n{correction['data'][:500]}...")

                    feedback.success(
                        "Auto-correction plan ready",
                        issue=issue
                    )

                    # Dans un système réel, cela pourrait:
                    # 1. Créer un agent "Database Connection Manager"
                    # 2. Ajuster les timeouts automatiquement
                    # 3. Implémenter un retry mechanism
                    # 4. Ajouter du connection pooling

                    print("\n   📝 Next steps:")
                    print("      1. Review the auto-correction plan")
                    print("      2. Apply the fix (auto or manual)")
                    print("      3. Validate the fix works")
                    print("      4. Monitor for recurrence")


def main():
    """Exécute tous les exemples"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 10 + "CORTEX IMPROVED WORKFLOW EXAMPLES" + " " * 24 + "║")
    print("╚" + "═" * 68 + "╝")

    # 1. Workflow utilisateur avec feedback
    example_workflow_with_feedback()

    # 2. Meta-analyse du système
    example_meta_analysis()

    # 3. Auto-correction
    example_self_healing()

    print("\n\n" + "=" * 70)
    print("✓ ALL EXAMPLES COMPLETED")
    print("=" * 70)

    print("\n📌 KEY TAKEAWAYS:")
    print("\n1. TRANSPARENCY")
    print("   Users now get real-time feedback on what's happening")

    print("\n2. SELF-AWARENESS")
    print("   The system logs everything and analyzes its own performance")

    print("\n3. AUTO-VALIDATION")
    print("   Results are automatically validated and corrected")

    print("\n4. CONTINUOUS IMPROVEMENT")
    print("   Meta-Architect detects issues and proposes solutions")

    print("\n5. AUTO-HEALING")
    print("   Recurring problems trigger automatic correction plans")

    print("\n💡 The system is now truly autonomous and self-improving!")
    print()


if __name__ == "__main__":
    main()
