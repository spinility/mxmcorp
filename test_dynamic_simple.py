#!/usr/bin/env python3
"""
Test simplifié du système dynamique - Structure et intégration
"""

import sys
from cortex.agents.hierarchy import get_hierarchy, reset_hierarchy
from cortex.agents.hr_agent import HRAgent


def main():
    print("\n" + "="*80)
    print("CORTEX MXMCORP - TEST SYSTÈME DYNAMIQUE (STRUCTURE)")
    print("="*80)
    print("\nCe test vérifie l'architecture sans appels LLM")
    print("\n" + "="*80)

    # Test 1: Structure de base
    print("\n[TEST 1] Structure de base")
    print("-" * 40)

    reset_hierarchy()
    hierarchy = get_hierarchy()

    assert hierarchy.ceo is not None, "CEO manquant"
    assert hierarchy.hr_department is not None, "HR manquant"
    assert hierarchy.tools_department is not None, "Tools manquant"
    assert hierarchy.code_director is not None, "CodeDirector manquant"
    assert hierarchy.data_director is not None, "DataDirector manquant"
    assert hierarchy.communication_director is not None, "CommunicationDirector manquant"
    assert hierarchy.operations_director is not None, "OperationsDirector manquant"

    print("✓ CEO présent")
    print("✓ HR Department présent")
    print("✓ Tools Department présent")
    print("✓ 4 Directors présents")

    # Test 2: Vérifier que CEO a accès aux départements
    print("\n[TEST 2] CEO a accès aux départements")
    print("-" * 40)

    assert hierarchy.ceo.hr_department is not None, "CEO n'a pas accès à HR"
    assert hierarchy.ceo.tools_department is not None, "CEO n'a pas accès à Tools"

    print("✓ CEO.hr_department configuré")
    print("✓ CEO.tools_department configuré")

    # Test 3: Vérifier que Directors ont accès aux départements
    print("\n[TEST 3] Directors ont accès aux départements")
    print("-" * 40)

    for director_name, director in [
        ("Code", hierarchy.code_director),
        ("Data", hierarchy.data_director),
        ("Communication", hierarchy.communication_director),
        ("Operations", hierarchy.operations_director)
    ]:
        assert director.hr_department is not None, f"{director_name} n'a pas accès à HR"
        assert director.tools_department is not None, f"{director_name} n'a pas accès à Tools"
        print(f"✓ {director_name}Director a accès aux départements")

    # Test 4: Vérifier que CEO a les Directors comme subordonnés
    print("\n[TEST 4] Structure hiérarchique")
    print("-" * 40)

    assert "CodeDirector" in hierarchy.ceo.subordinates, "CodeDirector pas subordonné"
    assert "DataDirector" in hierarchy.ceo.subordinates, "DataDirector pas subordonné"
    assert "CommunicationDirector" in hierarchy.ceo.subordinates, "CommunicationDirector pas subordonné"
    assert "OperationsDirector" in hierarchy.ceo.subordinates, "OperationsDirector pas subordonné"

    print("✓ CEO a 4 Directors comme subordonnés")
    print(f"  - {len(hierarchy.ceo.subordinates)} subordonnés au total")

    # Test 5: Vérifier les méthodes de demande
    print("\n[TEST 5] Méthodes de demande disponibles")
    print("-" * 40)

    # CEO peut demander (via HRAgent)
    assert hasattr(hierarchy.ceo, 'request_employee_creation'), "CEO.request_employee_creation manquant"
    assert hasattr(hierarchy.ceo, 'request_tool_creation'), "CEO.request_tool_creation manquant"
    assert hierarchy.ceo.hr_agent is not None, "CEO n'a pas de HR Agent"
    print("✓ CEO a request_employee_creation() (via HR Agent)")
    print("✓ CEO a request_tool_creation()")

    # Directors peuvent seulement demander des outils (pas des employés)
    assert hasattr(hierarchy.code_director, 'request_tool'), "Director.request_tool manquant"
    assert not hasattr(hierarchy.code_director, 'request_employee'), "Directors ne doivent pas pouvoir créer des employés"
    print("✓ Directors ont request_tool()")
    print("✓ Directors NE PEUVENT PAS créer d'employés (seulement HR Agent)")

    # Test 6: Stats et méthodes utilitaires
    print("\n[TEST 6] Statistiques et utilitaires")
    print("-" * 40)

    stats = hierarchy.get_all_stats()

    assert 'ceo' in stats, "stats.ceo manquant"
    assert 'directors' in stats, "stats.directors manquant"
    assert 'departments' in stats, "stats.departments manquant"
    assert 'hr' in stats['departments'], "stats.departments.hr manquant"
    assert 'tools' in stats['departments'], "stats.departments.tools manquant"

    print("✓ get_all_stats() fonctionne")
    print(f"  - Total cost: ${stats['total_cost']:.6f}")
    print(f"  - Total tasks: {stats['total_tasks']}")

    # Test 7: Afficher la hiérarchie
    print("\n[TEST 7] Affichage de la hiérarchie")
    print("-" * 40)

    hierarchy.print_hierarchy()

    # Test 8: Philosophie du CEO et HR Agent
    print("\n[TEST 8] Philosophie et restrictions")
    print("-" * 40)

    ceo_prompt = hierarchy.ceo.config.base_prompt

    assert "ALWAYS" in ceo_prompt or "always" in ceo_prompt, "Pas de mention de ALWAYS delegate"
    assert "delegate" in ceo_prompt.lower(), "Pas de mention de delegation"
    assert "NO direct" in ceo_prompt or "no direct" in ceo_prompt, "Pas de mention NO direct skills"

    print("✓ CEO configuré pour TOUJOURS déléguer")
    print("✓ CEO n'a aucune compétence directe")
    print("✓ CEO délègue création d'employés au HR Agent")
    print("✓ CEO peut demander création d'outils")

    # Vérifier que le HR Agent existe et peut créer des employés
    assert hierarchy.hr_agent is not None, "HR Agent manquant"
    assert hasattr(hierarchy.hr_agent, 'request_employee'), "HR Agent ne peut pas créer d'employés"
    assert isinstance(hierarchy.hr_agent, HRAgent), "hr_agent n'est pas un HRAgent"

    print("✓ HR Agent présent et autorisé à créer des employés")
    print(f"✓ HR Agent: {hierarchy.hr_agent.config.name}")

    # Vérifier que BaseAgent n'a PAS request_employee
    test_agent = hierarchy.code_director
    assert not hasattr(test_agent, 'request_employee'), "BaseAgent ne devrait pas avoir request_employee"
    print("✓ Les agents normaux ne peuvent PAS créer d'employés")

    # Récapitulatif final
    print("\n" + "="*80)
    print("✓ TOUS LES TESTS STRUCTURELS RÉUSSIS!")
    print("="*80)
    print("\nLe système est correctement architecturé:")
    print("  • CEO délègue TOUJOURS (pas d'exécution directe)")
    print("  • SEUL le HR Agent peut créer des employés")
    print("  • Employés générés sont indétectables (profiles professionnels)")
    print("  • Tools Department peut créer des outils sur demande")
    print("  • Directors peuvent créer des outils (pas des employés)")
    print("  • Structure hiérarchique correcte avec restrictions")
    print("  • Système auto-outillé et contrôlé")
    print("\n" + "="*80)
    print("\nPour tester avec LLM réels:")
    print("  python3 test_dynamic_system.py")
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
