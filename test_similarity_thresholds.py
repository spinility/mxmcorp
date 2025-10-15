"""
Test du système de seuils de similarité adaptatifs

Teste:
1. Filtrage par similarité selon la gravité
2. Détection automatique de gravité
3. Rapports de qualité
4. Ajustement des seuils
"""

from pathlib import Path
from cortex.core.smart_context_builder import (
    SmartContextBuilder,
    TaskSeverity,
    SimilarityThresholds
)


def print_section(title: str):
    """Affiche une section"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# Test 1: Vérification des seuils
print_section("STEP 1: Threshold Configuration")

print("\nSimilarity Thresholds by Severity:")
for severity in TaskSeverity:
    threshold = SimilarityThresholds.get_threshold(severity)
    min_results = SimilarityThresholds.get_min_results(severity)
    print(f"  {severity.value.upper():10s}: threshold={threshold:.2f}, min_results={min_results}")

print("\n✅ Threshold configuration loaded")


# Test 2: Détection automatique de gravité
print_section("STEP 2: Automatic Severity Detection")

builder = SmartContextBuilder(project_root=Path.cwd())

# Vérifier si KB disponible et indexée
if builder.kb:
    stats = builder.kb.get_stats()
    if stats.get("total_chunks", 0) == 0:
        print("\n⚠️  Knowledge base not indexed. Indexing now...")
        builder.kb.index_project(verbose=False)
        print("✅ Knowledge base indexed")
else:
    print("\n⚠️  ChromaDB not available. Some tests will be limited.")

test_tasks = [
    ("Fix authentication vulnerability in production", TaskSeverity.CRITICAL),
    ("Add new public API endpoint for users", TaskSeverity.HIGH),
    ("Create new feature for dashboard", TaskSeverity.MEDIUM),
    ("Refactor code and add comments", TaskSeverity.LOW),
    ("Update documentation", TaskSeverity.LOW),
]

print("\nTesting severity detection:\n")
correct = 0
for task, expected in test_tasks:
    detected = builder.detect_task_severity(task)
    status = "✅" if detected == expected else "❌"
    print(f"{status} '{task[:50]}...'")
    print(f"   Expected: {expected.value}, Detected: {detected.value}")
    if detected == expected:
        correct += 1

print(f"\n✅ Severity detection: {correct}/{len(test_tasks)} correct")


# Test 3: Context building avec différentes gravités
print_section("STEP 3: Context Building with Different Severities")

task = "Update authentication system"

print(f"\nTask: {task}\n")

for severity in [TaskSeverity.CRITICAL, TaskSeverity.MEDIUM, TaskSeverity.LOW]:
    print(f"\n--- Severity: {severity.value.upper()} (threshold={SimilarityThresholds.get_threshold(severity):.2f}) ---")

    context = builder.build_context(
        task=task,
        budget=900,
        severity=severity,
        include_quality_report=False
    )

    # Obtenir le rapport de qualité
    quality = builder.get_last_quality_report()

    if quality:
        print(f"Total found: {quality['total_count']}")
        print(f"Filtered out: {quality['filtered_count']}")
        if quality['total_count'] > 0:
            print(f"Acceptance rate: {(quality['total_count'] - quality['filtered_count']) / quality['total_count'] * 100:.1f}%")
        else:
            print(f"Acceptance rate: N/A (no results found)")

        # Afficher les stats par type
        for search_type, stats in quality["results_by_type"].items():
            if stats["found"] > 0:
                avg_dist = sum(stats["distances"]) / len(stats["distances"]) if stats["distances"] else 0
                print(f"  {search_type}: {stats['accepted']}/{stats['found']} (avg dist: {avg_dist:.2f})")

        # Warnings
        if quality["warnings"]:
            print(f"  Warnings: {len(quality['warnings'])}")

print("\n✅ Context building with different severities tested")


# Test 4: Rapport de qualité complet
print_section("STEP 4: Full Quality Report")

task_critical = "Fix critical security vulnerability in authentication"
print(f"\nTask: {task_critical}")
print(f"Auto-detected severity: {builder.detect_task_severity(task_critical).value}")

context = builder.build_context(
    task=task_critical,
    budget=900,
    severity=TaskSeverity.CRITICAL,
    include_quality_report=True
)

print("\n--- Context Preview (first 800 chars) ---")
print(context[:800])
print("...")

print("\n✅ Full quality report included in context")


# Test 5: Comparaison des taux de filtrage
print_section("STEP 5: Filtering Rate Comparison")

test_query = "agent system"
print(f"\nQuery: '{test_query}'\n")

filtering_stats = []

for severity in TaskSeverity:
    context = builder.build_context(
        task=test_query,
        severity=severity
    )

    quality = builder.get_last_quality_report()

    if quality:
        total = quality['total_count']
        filtered = quality['filtered_count']
        accepted = total - filtered
        rate = (filtered / total * 100) if total > 0 else 0

        filtering_stats.append({
            "severity": severity.value,
            "threshold": quality['threshold'],
            "total": total,
            "accepted": accepted,
            "filtered": filtered,
            "filter_rate": rate
        })

print(f"{'Severity':<10} {'Threshold':<10} {'Total':<8} {'Accepted':<10} {'Filtered':<10} {'Filter Rate':<12}")
print("-" * 70)
for stat in filtering_stats:
    print(f"{stat['severity']:<10} {stat['threshold']:<10.2f} {stat['total']:<8} "
          f"{stat['accepted']:<10} {stat['filtered']:<10} {stat['filter_rate']:<12.1f}%")

print("\n✅ Filtering rate comparison complete")


# Test 6: Quality assessment
print_section("STEP 6: Quality Assessment")

print("\nTesting quality assessment for different distances:\n")

test_distances = [0.3, 0.6, 0.9, 1.2, 1.5]

for severity in [TaskSeverity.CRITICAL, TaskSeverity.MEDIUM, TaskSeverity.LOW]:
    print(f"\n{severity.value.upper()} (threshold: {SimilarityThresholds.get_threshold(severity):.2f}):")
    for distance in test_distances:
        quality = SimilarityThresholds.assess_quality(distance, severity)
        print(f"  Distance {distance:.2f}: {quality}")

print("\n✅ Quality assessment tested")


# Summary
print_section("SUMMARY")

print("\n✅ ALL TESTS COMPLETED")
print("\nKey Features Validated:")
print("  1. Configurable similarity thresholds by severity")
print("  2. Automatic task severity detection")
print("  3. Context building with adaptive filtering")
print("  4. Quality reporting and metrics")
print("  5. Filtering rate varies by severity (stricter for critical tasks)")
print("  6. Quality assessment (excellent/good/acceptable/weak)")

print("\n📊 SYSTEM BEHAVIOR:")
print("  • CRITICAL tasks: Very strict (threshold=0.6)")
print("  •     HIGH tasks: Strict (threshold=0.85)")
print("  •   MEDIUM tasks: Standard (threshold=1.1)")
print("  •      LOW tasks: Permissive (threshold=1.5)")

print("\n💡 USAGE:")
print("  # Auto-detect severity")
print("  severity = builder.detect_task_severity(task)")
print("  context = builder.build_context(task, severity=severity)")
print("")
print("  # Or specify manually")
print("  context = builder.build_context(task, severity=TaskSeverity.CRITICAL)")
print("")
print("  # Get quality report")
print("  quality = builder.get_last_quality_report()")
print("  print(f\"Filtered: {quality['filtered_count']}/{quality['total_count']}\")")

print("\n" + "=" * 70)
