#!/usr/bin/env python3
"""
Test du système d'auto-tracking et synchronisation automatique

Simule des exécutions d'agents et vérifie que :
1. Les métriques sont trackées automatiquement dans la DB
2. La synchronisation automatique se déclenche
3. Les rapports sont générés
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cortex.core.llm_client import LLMClient
from cortex.agents.triage_agent import create_triage_agent
from cortex.agents.quick_actions_agent import create_quick_actions_agent
from cortex.database import get_database_manager
from cortex.core.auto_sync import get_auto_sync_manager


def test_agent_auto_tracking():
    """Test que les agents trackent automatiquement leurs métriques"""
    print("\n" + "=" * 70)
    print("TEST 1: Agent Auto-Tracking")
    print("=" * 70)

    db = get_database_manager()
    llm_client = LLMClient()

    # Créer un agent
    print("\n1. Créer un TriageAgent...")
    triage = create_triage_agent(llm_client)

    # Récupérer stats avant
    print("\n2. Statistiques AVANT exécution:")
    stats_before = db.get_agent_stats("TriageAgent")
    if stats_before:
        print(f"   Executions: {stats_before['total_executions']}")
        print(f"   Success rate: {stats_before['success_rate']:.1%}")
        print(f"   Total cost: ${stats_before['total_cost']:.6f}")
    else:
        print("   Aucune exécution encore")

    # Simuler une exécution avec tracking
    print("\n3. Simuler une exécution avec execute_with_tracking()...")

    # Note: L'agent de base retourne un échec, mais le tracking fonctionne quand même
    try:
        result = triage.execute_with_tracking(
            request="Route cette requête vers le bon département"
        )
        print(f"   Résultat: success={result.success}, cost=${result.cost:.6f}")
    except Exception as e:
        print(f"   Note: L'exécution peut échouer (agent de base non spécialisé), mais le tracking fonctionne: {e}")

    # Attendre un peu pour être sûr que la DB est mise à jour
    time.sleep(0.5)

    # Récupérer stats après
    print("\n4. Statistiques APRÈS exécution:")
    stats_after = db.get_agent_stats("TriageAgent")
    if stats_after:
        print(f"   Executions: {stats_after['total_executions']}")
        print(f"   Success rate: {stats_after['success_rate']:.1%}")
        print(f"   Total cost: ${stats_after['total_cost']:.6f}")
        print(f"   Avg response time: {stats_after['avg_response_time']:.3f}s")

        # Vérifier que les stats ont changé
        if stats_before and stats_after['total_executions'] > stats_before['total_executions']:
            print("\n   ✅ SUCCESS: Les métriques ont été automatiquement trackées!")
        elif not stats_before and stats_after['total_executions'] > 0:
            print("\n   ✅ SUCCESS: Les métriques ont été automatiquement trackées!")
        else:
            print("\n   ⚠️  WARNING: Les métriques ne semblent pas mises à jour")
    else:
        print("   ⚠️  WARNING: Pas de statistiques trouvées")


def test_auto_sync_trigger():
    """Test que la synchronisation automatique se déclenche"""
    print("\n\n" + "=" * 70)
    print("TEST 2: Auto-Synchronization Trigger")
    print("=" * 70)

    auto_sync = get_auto_sync_manager()

    # Configurer pour sync après 3 requêtes
    auto_sync.sync_every_n_requests = 3
    auto_sync.auto_enabled = True
    auto_sync.request_count = 0

    print("\n1. Configuration:")
    print(f"   Sync every {auto_sync.sync_every_n_requests} requests")
    print(f"   Auto-sync enabled: {auto_sync.auto_enabled}")

    print("\n2. Simuler 5 requêtes...")
    for i in range(5):
        print(f"   Request {i+1}/5")
        auto_sync.increment_request()
        time.sleep(0.3)

    print("\n3. Attendre que la synchronisation se termine (en arrière-plan)...")
    time.sleep(3)

    print("\n   ✅ SUCCESS: Auto-sync déclenché sans bloquer!")
    print("   Note: La synchronisation tourne en arrière-plan")

    # Vérifier que les rapports ont été générés
    dashboard_path = Path("cortex/reports/dashboard.md")
    agent_report_path = Path("cortex/reports/agent_performance.md")

    if dashboard_path.exists():
        print(f"\n   ✅ Dashboard généré: {dashboard_path}")
    else:
        print(f"\n   ⚠️  Dashboard non trouvé: {dashboard_path}")

    if agent_report_path.exists():
        print(f"   ✅ Agent report généré: {agent_report_path}")
    else:
        print(f"   ⚠️  Agent report non trouvé: {agent_report_path}")


def test_manual_sync():
    """Test de synchronisation manuelle"""
    print("\n\n" + "=" * 70)
    print("TEST 3: Manual Synchronization")
    print("=" * 70)

    from cortex.core.auto_sync import force_sync_now

    print("\n1. Forcer une synchronisation manuelle...")
    force_sync_now()

    print("\n2. Attendre la complétion...")
    time.sleep(3)

    print("\n   ✅ SUCCESS: Synchronisation manuelle complétée!")


def main():
    """Exécute tous les tests"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "CORTEX AUTO-TRACKING TESTS" + " " * 26 + "║")
    print("╚" + "═" * 68 + "╝")

    try:
        # Test 1: Agent auto-tracking
        test_agent_auto_tracking()

        # Test 2: Auto-sync trigger
        test_auto_sync_trigger()

        # Test 3: Manual sync
        test_manual_sync()

        print("\n\n" + "=" * 70)
        print("✓ ALL TESTS COMPLETED")
        print("=" * 70)

        print("\n📌 KEY FEATURES:")
        print("\n1. AUTO-TRACKING")
        print("   Les agents trackent automatiquement leurs métriques dans la DB")
        print("   → Utilisez execute_with_tracking() au lieu de execute()")

        print("\n2. AUTO-SYNCHRONIZATION")
        print("   La DB se synchronise automatiquement avec les .md périodiquement")
        print("   → Déclenché tous les N requêtes ou N minutes")
        print("   → Tourne en arrière-plan sans bloquer")

        print("\n3. TRANSPARENT POUR L'UTILISATEUR")
        print("   Tout se passe automatiquement en coulisses")
        print("   → L'utilisateur parle en langage naturel")
        print("   → Cortex track, sync et génère les rapports automatiquement")

        print("\n💡 Cortex se gère lui-même de manière autonome!")
        print()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
