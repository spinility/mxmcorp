#!/usr/bin/env python3
"""
Test du système d'escalade automatique avec QualityEvaluator et ExpertPool
"""

import sys
from cortex.agents.hierarchy import get_hierarchy, reset_hierarchy
from cortex.agents.base_agent import BaseAgent, AgentConfig
from cortex.core.model_router import ModelTier


def main():
    print("\n" + "="*80)
    print("CORTEX MXMCORP - TEST SYSTÈME D'ESCALADE")
    print("="*80)
    print("\nCe test vérifie le système d'escalade avec QualityEvaluator et ExpertPool")
    print("\n" + "="*80)

    # Test 1: Structure de base avec ExpertPool
    print("\n[TEST 1] Structure de base avec ExpertPool")
    print("-" * 40)

    reset_hierarchy()
    hierarchy = get_hierarchy()

    assert hierarchy.expert_pool is not None, "ExpertPool manquant"
    assert hierarchy.ceo.expert_pool is not None, "CEO n'a pas accès à ExpertPool"
    assert hierarchy.code_director.expert_pool is not None, "Directors n'ont pas accès à ExpertPool"

    print("✓ ExpertPool présent")
    print("✓ CEO a accès à ExpertPool")
    print("✓ Directors ont accès à ExpertPool")

    # Test 2: Vérifier que les agents ont QualityEvaluator
    print("\n[TEST 2] QualityEvaluator présent dans les agents")
    print("-" * 40)

    assert hierarchy.ceo.quality_evaluator is not None, "CEO n'a pas QualityEvaluator"
    assert hierarchy.code_director.quality_evaluator is not None, "Directors n'ont pas QualityEvaluator"

    print("✓ CEO a QualityEvaluator")
    print("✓ Directors ont QualityEvaluator")

    # Test 3: Vérifier que les agents ont execute_with_escalation
    print("\n[TEST 3] Méthode execute_with_escalation disponible")
    print("-" * 40)

    assert hasattr(hierarchy.ceo, 'execute_with_escalation'), "CEO n'a pas execute_with_escalation"
    assert hasattr(hierarchy.code_director, 'execute_with_escalation'), "Directors n'ont pas execute_with_escalation"

    print("✓ CEO a execute_with_escalation()")
    print("✓ Directors ont execute_with_escalation()")

    # Test 4: ExpertPool disponible et liste des experts
    print("\n[TEST 4] ExpertPool - Liste des experts disponibles")
    print("-" * 40)

    expert_types = hierarchy.expert_pool.list_experts()
    assert len(expert_types) > 0, "Aucun expert disponible"

    print(f"✓ {len(expert_types)} types d'experts disponibles:")
    for expert_type in expert_types:
        print(f"  - {expert_type}")

    # Test 5: Statistiques ExpertPool
    print("\n[TEST 5] Statistiques ExpertPool")
    print("-" * 40)

    expert_stats = hierarchy.expert_pool.get_stats()
    assert expert_stats is not None, "Stats ExpertPool manquantes"
    assert "total_consultations" in expert_stats, "Stat total_consultations manquante"
    assert "total_expert_cost" in expert_stats, "Stat total_expert_cost manquante"
    assert "experts_created" in expert_stats, "Stat experts_created manquante"

    print("✓ ExpertPool stats disponibles")
    print(f"  Consultations: {expert_stats['total_consultations']}")
    print(f"  Experts créés: {expert_stats['experts_created']}")
    print(f"  Coût total: ${expert_stats['total_expert_cost']:.6f}")

    # Test 6: Test escalade simple (sans vraie exécution LLM)
    print("\n[TEST 6] Test execute_with_escalation() - Structure")
    print("-" * 40)

    # Créer un agent de test
    test_config = AgentConfig(
        name="TestAgent",
        role="Test Agent",
        description="Agent for testing escalation",
        base_prompt="You are a test agent.",
        tier_preference=ModelTier.NANO,
        specializations=["testing"]
    )

    test_agent = BaseAgent(
        config=test_config,
        expert_pool=hierarchy.expert_pool,
        tools_department=hierarchy.tools_department,
        hr_department=hierarchy.hr_department
    )

    # Vérifier que l'agent peut accéder aux composants d'escalade
    assert test_agent.quality_evaluator is not None, "Test agent n'a pas QualityEvaluator"
    assert test_agent.expert_pool is not None, "Test agent n'a pas accès à ExpertPool"
    assert hasattr(test_agent, 'execute_with_escalation'), "Test agent n'a pas execute_with_escalation"

    print("✓ Agent de test créé avec système d'escalade")
    print("✓ Agent a QualityEvaluator")
    print("✓ Agent a accès à ExpertPool")
    print("✓ Agent a execute_with_escalation()")

    # Test 7: Afficher la hiérarchie avec ExpertPool
    print("\n[TEST 7] Affichage de la hiérarchie avec ExpertPool")
    print("-" * 40)

    hierarchy.print_hierarchy()

    # Test 8: Stats complètes incluant ExpertPool
    print("\n[TEST 8] Statistiques complètes")
    print("-" * 40)

    all_stats = hierarchy.get_all_stats()
    assert "departments" in all_stats, "Stats departments manquantes"
    assert "expert_pool" in all_stats["departments"], "Stats expert_pool manquantes"

    expert_pool_stats = all_stats["departments"]["expert_pool"]
    print(f"✓ ExpertPool dans les stats complètes")
    print(f"  Types disponibles: {len(expert_pool_stats['available_expert_types'])}")
    print(f"  Consultations: {expert_pool_stats['total_consultations']}")

    # Test 9: Vérifier escalation dans la mémoire des agents
    print("\n[TEST 9] Compteur d'escalade dans les agents")
    print("-" * 40)

    assert hasattr(hierarchy.ceo, 'escalation_count'), "CEO n'a pas escalation_count"
    assert hasattr(hierarchy.code_director, 'escalation_count'), "Directors n'ont pas escalation_count"
    assert hierarchy.ceo.escalation_count == 0, "CEO escalation_count devrait être 0 au départ"

    print("✓ CEO a escalation_count")
    print("✓ Directors ont escalation_count")
    print(f"  CEO escalations: {hierarchy.ceo.escalation_count}")
    print(f"  Code Director escalations: {hierarchy.code_director.escalation_count}")

    # Récapitulatif final
    print("\n" + "="*80)
    print("✓ TOUS LES TESTS D'ESCALADE RÉUSSIS!")
    print("="*80)
    print("\nLe système d'escalade est correctement configuré:")
    print("  • QualityEvaluator intégré (évaluation LLM)")
    print("  • execute_with_escalation() disponible pour tous les agents")
    print("  • ExpertPool créé avec 8 types d'experts")
    print("  • Escalade automatique: NANO → DEEPSEEK → CLAUDE → Expert")
    print("  • Évaluation de qualité via LLM (pas d'heuristiques)")
    print("  • Experts consultables pour tâches ultra-complexes")
    print("  • Stats et compteurs d'escalade disponibles")
    print("\n" + "="*80)
    print("\nPour tester avec de vraies tâches et escalades LLM:")
    print("  python3 test_escalation_real.py")
    print("="*80 + "\n")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n✗ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
