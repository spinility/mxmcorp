"""
Exemple d'utilisation du système de seuils de similarité adaptatifs

Montre comment utiliser les différents niveaux de gravité et analyser
la qualité du contexte généré.
"""

from pathlib import Path
from cortex.core.smart_context_builder import (
    SmartContextBuilder,
    TaskSeverity
)


def main():
    print("=" * 70)
    print("DÉMONSTRATION: Système de Seuils de Similarité Adaptatifs")
    print("=" * 70)

    # Initialize builder
    builder = SmartContextBuilder(project_root=Path.cwd())

    # Index if needed
    if builder.kb:
        stats = builder.kb.get_stats()
        if stats.get("total_chunks", 0) == 0:
            print("\n📚 Indexing project...")
            builder.kb.index_project(verbose=False)
            print("✅ Project indexed\n")

    # Exemple 1: Tâche CRITIQUE avec détection auto
    print("\n" + "─" * 70)
    print("EXEMPLE 1: Tâche Critique (Auto-Détection)")
    print("─" * 70)

    task1 = "Fix critical authentication vulnerability in production"
    print(f"\n📋 Task: {task1}")

    # Détection automatique
    severity1 = builder.detect_task_severity(task1)
    print(f"🔍 Auto-detected severity: {severity1.value.upper()}")

    # Build context
    context1 = builder.build_context(
        task=task1,
        severity=severity1
    )

    # Analyser la qualité
    quality1 = builder.get_last_quality_report()

    print(f"\n📊 Quality Report:")
    print(f"   Threshold: {quality1['threshold']:.2f} (strict)")
    print(f"   Total results found: {quality1['total_count']}")
    print(f"   Filtered out: {quality1['filtered_count']}")

    if quality1['total_count'] > 0:
        accepted = quality1['total_count'] - quality1['filtered_count']
        rate = (accepted / quality1['total_count']) * 100
        print(f"   Acceptance rate: {rate:.1f}%")

    if quality1['warnings']:
        print(f"\n⚠️  Warnings: {len(quality1['warnings'])}")
        for w in quality1['warnings'][:2]:
            print(f"   - {w}")

    print(f"\n✅ Context tokens: {builder.get_token_estimate(context1)}")

    # Exemple 2: Tâche STANDARD
    print("\n" + "─" * 70)
    print("EXEMPLE 2: Tâche Standard (MEDIUM)")
    print("─" * 70)

    task2 = "Create new dashboard feature for analytics"
    print(f"\n📋 Task: {task2}")

    severity2 = TaskSeverity.MEDIUM
    print(f"🔍 Severity: {severity2.value.upper()}")

    context2 = builder.build_context(
        task=task2,
        severity=severity2
    )

    quality2 = builder.get_last_quality_report()

    print(f"\n📊 Quality Report:")
    print(f"   Threshold: {quality2['threshold']:.2f} (standard)")
    print(f"   Total results found: {quality2['total_count']}")
    print(f"   Filtered out: {quality2['filtered_count']}")

    if quality2['total_count'] > 0:
        accepted = quality2['total_count'] - quality2['filtered_count']
        rate = (accepted / quality2['total_count']) * 100
        print(f"   Acceptance rate: {rate:.1f}%")

    print(f"\n✅ Context tokens: {builder.get_token_estimate(context2)}")

    # Exemple 3: Tâche FAIBLE (refactoring)
    print("\n" + "─" * 70)
    print("EXEMPLE 3: Tâche Faible (LOW - Refactoring)")
    print("─" * 70)

    task3 = "Refactor code and add documentation"
    print(f"\n📋 Task: {task3}")

    severity3 = builder.detect_task_severity(task3)
    print(f"🔍 Auto-detected severity: {severity3.value.upper()}")

    context3 = builder.build_context(
        task=task3,
        severity=severity3
    )

    quality3 = builder.get_last_quality_report()

    print(f"\n📊 Quality Report:")
    print(f"   Threshold: {quality3['threshold']:.2f} (permissive)")
    print(f"   Total results found: {quality3['total_count']}")
    print(f"   Filtered out: {quality3['filtered_count']}")

    if quality3['total_count'] > 0:
        accepted = quality3['total_count'] - quality3['filtered_count']
        rate = (accepted / quality3['total_count']) * 100
        print(f"   Acceptance rate: {rate:.1f}%")

    print(f"\n✅ Context tokens: {builder.get_token_estimate(context3)}")

    # Exemple 4: Comparaison avec rapport inclus
    print("\n" + "─" * 70)
    print("EXEMPLE 4: Avec Rapport de Qualité Inclus")
    print("─" * 70)

    task4 = "Update payment processing system"
    print(f"\n📋 Task: {task4}")

    context4 = builder.build_context(
        task=task4,
        severity=TaskSeverity.CRITICAL,
        include_quality_report=True  # Inclut le rapport dans le contexte
    )

    print("\n📄 Context Preview (with embedded quality report):")
    print(context4[:800])
    print("...")

    # Résumé comparatif
    print("\n" + "=" * 70)
    print("RÉSUMÉ COMPARATIF")
    print("=" * 70)

    examples = [
        ("CRITICAL (auth)", severity1, quality1),
        ("MEDIUM (feature)", severity2, quality2),
        ("LOW (refactor)", severity3, quality3),
    ]

    print(f"\n{'Task':<20} {'Severity':<10} {'Threshold':<10} {'Found':<8} {'Filtered':<10} {'Rate':<10}")
    print("─" * 70)

    for name, severity, quality in examples:
        if quality['total_count'] > 0:
            accepted = quality['total_count'] - quality['filtered_count']
            rate = f"{(accepted / quality['total_count']) * 100:.1f}%"
        else:
            rate = "N/A"

        print(f"{name:<20} {severity.value:<10} {quality['threshold']:<10.2f} "
              f"{quality['total_count']:<8} {quality['filtered_count']:<10} {rate:<10}")

    print("\n💡 OBSERVATIONS:")
    print("   • CRITICAL tasks filter more aggressively (stricter threshold)")
    print("   • LOW tasks accept more results (permissive threshold)")
    print("   • Higher severity = better quality but fewer results")
    print("   • Lower severity = more context but variable quality")

    print("\n🎯 RECOMMANDATION:")
    print("   • Utiliser auto-detection pour la plupart des tâches")
    print("   • Forcer CRITICAL pour production/sécurité")
    print("   • Utiliser LOW pour refactoring/documentation")
    print("   • Monitorer les warnings pour détecter les problèmes")

    print("\n" + "=" * 70)
    print("✅ DÉMONSTRATION TERMINÉE")
    print("=" * 70)


if __name__ == "__main__":
    main()
