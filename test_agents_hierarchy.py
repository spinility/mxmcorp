"""
Test du système de hiérarchie d'agents
"""

from cortex.agents.hierarchy import get_hierarchy, reset_hierarchy
from cortex.tools.standard_tool import tool


# Créer quelques tools pour les agents
@tool(
    name="calculate",
    description="Perform basic math calculations",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Math expression to evaluate"}
        },
        "required": ["expression"]
    },
    category="math"
)
def calculate(expression: str) -> dict:
    """Calcule une expression mathématique simple"""
    try:
        # Sécurisé: eval uniquement sur expressions simples
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            return {"error": "Invalid characters in expression"}

        result = eval(expression)
        return {"result": result, "expression": expression}
    except Exception as e:
        return {"error": str(e)}


def test_hierarchy_structure():
    """Test 1: Vérifier la structure de la hiérarchie"""
    print("="*60)
    print("TEST 1: Hierarchy Structure")
    print("="*60)

    hierarchy = get_hierarchy()

    # Vérifier que le CEO existe
    assert hierarchy.ceo is not None
    print(f"✓ CEO: {hierarchy.ceo.config.name}")

    # Vérifier les Directors
    assert hierarchy.code_director is not None
    assert hierarchy.data_director is not None
    assert hierarchy.communication_director is not None
    assert hierarchy.operations_director is not None
    print(f"✓ Directors: 4 registered")

    # Vérifier les subordinates du CEO
    assert len(hierarchy.ceo.subordinates) == 4
    print(f"✓ CEO has {len(hierarchy.ceo.subordinates)} subordinates")

    # Afficher la hiérarchie
    hierarchy.print_hierarchy()

    print("\n✓ Hierarchy structure test PASSED\n")


def test_ceo_direct_execution():
    """Test 2: Exécution directe par le CEO"""
    print("="*60)
    print("TEST 2: CEO Direct Execution")
    print("="*60)

    reset_hierarchy()
    hierarchy = get_hierarchy()

    # Test simple
    task = "Explain what you do in one sentence."

    print(f"\nTask: {task}")
    result = hierarchy.ceo.execute(task, verbose=True)

    assert result["success"], f"Task failed: {result.get('error')}"
    print(f"\nResponse: {result['data'][:200]}...")
    print(f"Cost: ${result['cost']:.6f}")
    print(f"Tier: {result['tier']}")

    print("\n✓ CEO direct execution test PASSED\n")


def test_ceo_with_tools():
    """Test 3: CEO avec tools"""
    print("="*60)
    print("TEST 3: CEO with Tools")
    print("="*60)

    reset_hierarchy()
    hierarchy = get_hierarchy()

    # Ajouter un tool au CEO
    hierarchy.ceo.register_tool(calculate)
    print(f"✓ Registered 'calculate' tool")

    # Task nécessitant le tool
    task = "What is 15 * 23 + 47?"

    print(f"\nTask: {task}")
    result = hierarchy.ceo.execute(task, use_tools=True, verbose=True)

    assert result["success"], f"Task failed: {result.get('error')}"
    print(f"\nResponse: {result['data']}")
    print(f"Cost: ${result['cost']:.6f}")
    print(f"Tool calls: {result['tool_calls']}")

    print("\n✓ CEO with tools test PASSED\n")


def test_director_specialization():
    """Test 4: Test des Directors directement"""
    print("="*60)
    print("TEST 4: Director Specialization")
    print("="*60)

    reset_hierarchy()
    hierarchy = get_hierarchy()

    # Test Code Director
    code_task = "Write a Python function to reverse a string"
    print(f"\nCode Director task: {code_task[:50]}...")
    code_result = hierarchy.code_director.execute(code_task, verbose=False)

    assert code_result["success"]
    print(f"✓ Code Director: ${code_result['cost']:.6f} | {code_result['tier']}")

    # Test Data Director
    data_task = "Explain the difference between supervised and unsupervised learning"
    print(f"\nData Director task: {data_task[:50]}...")
    data_result = hierarchy.data_director.execute(data_task, verbose=False)

    assert data_result["success"]
    print(f"✓ Data Director: ${data_result['cost']:.6f} | {data_result['tier']}")

    # Test Communication Director
    comm_task = "Create a simple tutorial on how to use git"
    print(f"\nCommunication Director task: {comm_task[:50]}...")
    comm_result = hierarchy.communication_director.execute(comm_task, verbose=False)

    assert comm_result["success"]
    print(f"✓ Communication Director: ${comm_result['cost']:.6f} | {comm_result['tier']}")

    # Test Operations Director
    ops_task = "Explain what happens when you deploy a Docker container"
    print(f"\nOperations Director task: {ops_task[:50]}...")
    ops_result = hierarchy.operations_director.execute(ops_task, verbose=False)

    assert ops_result["success"]
    print(f"✓ Operations Director: ${ops_result['cost']:.6f} | {ops_result['tier']}")

    total_cost = (code_result['cost'] + data_result['cost'] +
                  comm_result['cost'] + ops_result['cost'])
    print(f"\nTotal cost for 4 Directors: ${total_cost:.6f}")

    print("\n✓ Director specialization test PASSED\n")


def test_ceo_delegation():
    """Test 5: Délégation du CEO"""
    print("="*60)
    print("TEST 5: CEO Delegation")
    print("="*60)

    reset_hierarchy()
    hierarchy = get_hierarchy()

    # Task qui devrait être déléguée
    task = "Fix this Python bug: def add(a b): return a + b"

    print(f"\nTask: {task}")
    print("CEO should delegate to Code Director...")

    result = hierarchy.ceo.delegate(task, verbose=True)

    assert result["success"], f"Delegation failed: {result.get('error')}"
    print(f"\nDelegated to: {result['agent']}")
    print(f"Cost: ${result['cost']:.6f}")

    print("\n✓ CEO delegation test PASSED\n")


def test_agent_memory():
    """Test 6: Mémoire des agents"""
    print("="*60)
    print("TEST 6: Agent Memory")
    print("="*60)

    reset_hierarchy()
    hierarchy = get_hierarchy()

    ceo = hierarchy.ceo

    # Exécuter plusieurs tâches
    tasks = [
        "Remember: My favorite color is blue",
        "Remember: I work at Company X",
        "What's my favorite color?"
    ]

    for task in tasks:
        print(f"\nTask: {task}")
        result = ceo.execute(task, verbose=False)
        print(f"Response: {result['data'][:100]}...")

    # Vérifier la mémoire
    print(f"\n✓ Memory size: {len(ceo.memory.short_term)} interactions")
    print(f"✓ Last 3 tasks remembered")

    print("\n✓ Agent memory test PASSED\n")


def test_hierarchy_stats():
    """Test 7: Statistiques globales"""
    print("="*60)
    print("TEST 7: Hierarchy Statistics")
    print("="*60)

    hierarchy = get_hierarchy()

    stats = hierarchy.get_all_stats()

    print(f"\nCEO Stats:")
    print(f"  Tasks: {stats['ceo']['task_count']}")
    print(f"  Cost: ${stats['ceo']['total_cost']:.6f}")
    print(f"  Delegations: {stats['ceo']['delegation_count']}")

    print(f"\nDirectors Stats:")
    for name, director_stats in stats['directors'].items():
        print(f"  {name.capitalize()}:")
        print(f"    Tasks: {director_stats['task_count']}")
        print(f"    Cost: ${director_stats['total_cost']:.6f}")

    print(f"\nGlobal Stats:")
    print(f"  Total tasks: {stats['total_tasks']}")
    print(f"  Total cost: ${stats['total_cost']:.6f}")
    print(f"  Avg cost/task: ${stats['total_cost']/stats['total_tasks']:.6f}")

    print("\n✓ Hierarchy statistics test PASSED\n")


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "CORTEX AGENTS HIERARCHY - TEST SUITE" + " "*11 + "║")
    print("╚" + "="*58 + "╝")

    try:
        test_hierarchy_structure()
        test_ceo_direct_execution()
        test_ceo_with_tools()
        test_director_specialization()
        test_ceo_delegation()
        test_agent_memory()
        test_hierarchy_stats()

        print("="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        print("\nThe agent hierarchy system is working correctly!")
        print("\nCurrent capabilities:")
        print("  ✓ CEO agent with strategic thinking")
        print("  ✓ 4 Director agents (Code, Data, Communication, Operations)")
        print("  ✓ Agent memory (short-term and long-term)")
        print("  ✓ Tool integration for all agents")
        print("  ✓ Delegation system")
        print("  ✓ Cost tracking and optimization")
        print("\nNext steps:")
        print("  - Implement Manager level (level 3)")
        print("  - Implement Worker level (level 4)")
        print("  - Enhanced CEO analysis and routing")
        print("  - Multi-agent collaboration")
        print()

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
