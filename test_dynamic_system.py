#!/usr/bin/env python3
"""
Test du système dynamique complet:
- Cortex délègue toujours
- Employés créés à la demande par RH
- Outils créés à la demande par département Outils
- Chaque employé peut demander de nouveaux employés et outils
"""

import sys
from cortex.agents.hierarchy import get_hierarchy, reset_hierarchy
from cortex.agents.hr_department import EmployeeRequest
from cortex.agents.tools_department import ToolRequest
from cortex.core.model_router import ModelTier


def test_hierarchy_structure():
    """Test 1: Vérifier la structure de base"""
    print("\n" + "="*80)
    print("TEST 1: Structure de base avec départements")
    print("="*80)

    reset_hierarchy()
    hierarchy = get_hierarchy()
    hierarchy.print_hierarchy()

    assert hierarchy.ceo is not None
    assert hierarchy.hr_department is not None
    assert hierarchy.tools_department is not None
    assert hierarchy.code_director is not None

    print("✓ Structure validée")


def test_hr_creates_employee():
    """Test 2: RH crée un employé spécialisé"""
    print("\n" + "="*80)
    print("TEST 2: Création d'employé par RH")
    print("="*80)

    reset_hierarchy()
    hierarchy = get_hierarchy()

    # Le CEO demande un employé pour une tâche spécifique
    result = hierarchy.ceo.request_employee_creation(
        task_description="Parse CSV files and extract specific columns",
        required_skills=["csv", "parsing", "data extraction"],
        tier=ModelTier.NANO,
        verbose=True
    )

    assert result["success"] is True
    assert result["agent"] is not None

    print(f"\n✓ Employé créé: {result['employee_name']}")
    print(f"  Rôle: {result['role']}")
    print(f"  Coût création: ${result['cost']:.6f}")

    # Vérifier qu'il est enregistré
    employees = hierarchy.hr_department.list_employees()
    assert len(employees) == 1
    print(f"\n✓ {len(employees)} employé(s) dans le registre RH")


def test_tools_creates_tool():
    """Test 3: Département Outils crée un outil"""
    print("\n" + "="*80)
    print("TEST 3: Création d'outil par département Outils")
    print("="*80)

    reset_hierarchy()
    hierarchy = get_hierarchy()

    # Le CEO demande un outil
    result = hierarchy.ceo.request_tool_creation(
        tool_purpose="Calculate file hash (SHA256) for integrity verification",
        input_description="file_path: str - Path to the file",
        output_description="dict with 'success': bool, 'hash': str, 'algorithm': str",
        example_usage="calculate_file_hash('/path/to/file.txt')",
        verbose=True
    )

    assert result["success"] is True
    assert result["tool"] is not None

    print(f"\n✓ Outil créé: {result['tool_name']}")
    print(f"  Coût création: ${result['cost']:.6f}")

    # Vérifier qu'il est dans le catalogue
    tools = hierarchy.tools_department.list_tools()
    assert len(tools) == 1
    print(f"\n✓ {len(tools)} outil(s) dans le catalogue")


def test_director_requests_employee():
    """Test 4: Un Director demande un employé"""
    print("\n" + "="*80)
    print("TEST 4: Director demande un employé aux RH")
    print("="*80)

    reset_hierarchy()
    hierarchy = get_hierarchy()

    # Le Code Director a besoin d'un employé spécialisé
    result = hierarchy.code_director.request_employee(
        task_description="Write unit tests for Python functions using pytest",
        required_skills=["python", "pytest", "testing", "unit tests"],
        tier=ModelTier.NANO,
        verbose=True
    )

    assert result["success"] is True
    print(f"\n✓ Code Director a créé l'employé: {result['employee_name']}")

    # Vérifier qu'il est dans les subordonnés du Director
    assert result["employee_name"] in hierarchy.code_director.subordinates
    print(f"✓ Employé enregistré comme subordonné du Code Director")


def test_director_requests_tool():
    """Test 5: Un Director demande un outil"""
    print("\n" + "="*80)
    print("TEST 5: Director demande un outil")
    print("="*80)

    reset_hierarchy()
    hierarchy = get_hierarchy()

    # Le Data Director a besoin d'un outil
    result = hierarchy.data_director.request_tool(
        tool_purpose="Calculate basic statistics (mean, median, std) for a list of numbers",
        input_description="numbers: List[float] - List of numbers",
        output_description="dict with mean, median, std_dev",
        verbose=True
    )

    assert result["success"] is True
    print(f"\n✓ Data Director a créé l'outil: {result['tool_name']}")

    # Vérifier que le Data Director a l'outil
    assert result["tool_name"] in hierarchy.data_director.available_tools
    print(f"✓ Outil disponible pour Data Director")


def test_ceo_always_delegates():
    """Test 6: CEO délègue TOUJOURS (ne fait rien lui-même)"""
    print("\n" + "="*80)
    print("TEST 6: CEO délègue systématiquement")
    print("="*80)

    reset_hierarchy()
    hierarchy = get_hierarchy()

    # Le CEO reçoit une demande simple
    result = hierarchy.ceo.analyze_and_delegate(
        user_request="What is the capital of France?",
        verbose=True
    )

    # Le CEO doit avoir délégué (delegation_count > 0)
    # et NE PAS avoir exécuté lui-même (task_count devrait être 0 ou minimal)
    print(f"\nCEO stats:")
    print(f"  Delegations: {hierarchy.ceo.delegation_count}")
    print(f"  Direct tasks: {hierarchy.ceo.task_count}")

    # Le CEO délègue, donc delegation_count > 0
    assert hierarchy.ceo.delegation_count > 0
    print(f"\n✓ CEO a bien délégué (pas d'exécution directe)")


def test_complete_workflow():
    """Test 7: Workflow complet"""
    print("\n" + "="*80)
    print("TEST 7: Workflow complet de création dynamique")
    print("="*80)

    reset_hierarchy()
    hierarchy = get_hierarchy()

    # Scénario: Le Code Director a une tâche complexe
    # 1. Il demande un employé spécialisé
    print("\n[Étape 1] Code Director demande un employé...")
    employee_result = hierarchy.code_director.request_employee(
        task_description="Optimize database queries and add indexes",
        required_skills=["sql", "database", "optimization", "indexing"],
        tier=ModelTier.NANO,
        verbose=True
    )

    assert employee_result["success"]
    employee = employee_result["agent"]
    employee_name = employee_result["employee_name"]

    # 2. L'employé a besoin d'un outil pour son travail
    print(f"\n[Étape 2] {employee_name} demande un outil...")
    tool_result = employee.request_tool(
        tool_purpose="Analyze SQL query execution plan and suggest indexes",
        input_description="query: str - SQL query to analyze",
        output_description="dict with execution_time, suggested_indexes, optimization_tips",
        verbose=True
    )

    assert tool_result["success"]

    # 3. L'employé pourrait même demander un autre employé
    print(f"\n[Étape 3] {employee_name} demande un sous-employé...")
    sub_employee_result = employee.request_employee(
        task_description="Test database performance after optimization",
        required_skills=["database", "testing", "performance"],
        tier=ModelTier.NANO,
        verbose=True
    )

    assert sub_employee_result["success"]

    print("\n" + "="*80)
    print("RÉSUMÉ DU WORKFLOW")
    print("="*80)

    hr_stats = hierarchy.hr_department.get_stats()
    tools_stats = hierarchy.tools_department.get_stats()

    print(f"\nEmployés créés: {hr_stats['employees_created']}")
    print(f"Outils créés: {tools_stats['tools_created']}")
    print(f"Coût total RH: ${hr_stats['total_cost']:.6f}")
    print(f"Coût total Outils: ${tools_stats['total_cost']:.6f}")

    assert hr_stats['employees_created'] == 2  # 2 employés créés
    assert tools_stats['tools_created'] == 1   # 1 outil créé

    print("\n✓ Workflow complet validé!")


def test_final_hierarchy_display():
    """Test 8: Affichage final de la hiérarchie complète"""
    print("\n" + "="*80)
    print("TEST 8: Hiérarchie finale avec tous les éléments")
    print("="*80)

    # Utiliser la hiérarchie du test précédent
    hierarchy = get_hierarchy()

    # Ajouter quelques éléments supplémentaires
    hierarchy.ceo.request_tool_creation(
        tool_purpose="Convert JSON to YAML format",
        input_description="json_str: str",
        output_description="yaml_str: str",
        verbose=False
    )

    hierarchy.operations_director.request_employee(
        task_description="Monitor system health and send alerts",
        required_skills=["monitoring", "alerts", "devops"],
        verbose=False
    )

    # Afficher la hiérarchie complète
    hierarchy.print_hierarchy()

    # Stats finales
    stats = hierarchy.get_all_stats()
    print("\nSTATISTIQUES GLOBALES:")
    print(f"  Total tasks: {stats['total_tasks']}")
    print(f"  Total cost: ${stats['total_cost']:.6f}")
    print(f"  Employees created: {stats['departments']['hr']['employees_created']}")
    print(f"  Tools created: {stats['departments']['tools']['tools_created']}")

    print("\n✓ Système complet opérationnel!")


def main():
    """Exécute tous les tests"""
    print("\n" + "="*80)
    print("CORTEX MXMCORP - TEST DU SYSTÈME DYNAMIQUE")
    print("="*80)
    print("\nPhilosophie:")
    print("  1. Le Cortex (CEO) n'a AUCUNE compétence directe")
    print("  2. Il délègue TOUJOURS aux employés")
    print("  3. Si l'employé n'existe pas, RH le crée")
    print("  4. Si un outil manque, département Outils le fabrique")
    print("  5. Chaque employé peut demander employés et outils")
    print("="*80)

    try:
        test_hierarchy_structure()
        test_hr_creates_employee()
        test_tools_creates_tool()
        test_director_requests_employee()
        test_director_requests_tool()
        test_ceo_always_delegates()
        test_complete_workflow()
        test_final_hierarchy_display()

        print("\n" + "="*80)
        print("✓ TOUS LES TESTS RÉUSSIS!")
        print("="*80)
        print("\nLe système est maintenant:")
        print("  • Entièrement dynamique")
        print("  • Auto-extensible (employés créés à la demande)")
        print("  • Auto-outillé (outils créés à la demande)")
        print("  • Hiérarchique (délégation en cascade)")
        print("  • Optimisé coûts (employés NANO par défaut)")
        print("="*80 + "\n")

        return 0

    except Exception as e:
        print(f"\n✗ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
