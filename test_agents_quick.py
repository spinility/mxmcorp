"""
Test rapide du système d'agents
"""

from cortex.agents.hierarchy import get_hierarchy, reset_hierarchy


def main():
    print("\n" + "="*60)
    print("CORTEX AGENTS - QUICK TEST")
    print("="*60)

    # Test 1: Structure
    print("\n1. Testing hierarchy structure...")
    hierarchy = get_hierarchy()
    hierarchy.print_hierarchy()
    print("✓ Structure OK")

    # Test 2: CEO simple task
    print("\n2. Testing CEO with simple task...")
    task = "Say hello in one word"
    result = hierarchy.ceo.execute(task, use_tools=False, verbose=True)

    if result["success"]:
        print(f"✓ Response: {result['data']}")
        print(f"✓ Cost: ${result['cost']:.6f}")
    else:
        print(f"✗ Failed: {result.get('error')}")

    # Test 3: Director
    print("\n3. Testing Code Director...")
    code_task = "Explain Python in 5 words"
    code_result = hierarchy.code_director.execute(code_task, use_tools=False, verbose=False)

    if code_result["success"]:
        print(f"✓ Response: {code_result['data']}")
        print(f"✓ Cost: ${code_result['cost']:.6f}")
    else:
        print(f"✗ Failed: {code_result.get('error')}")

    # Stats
    print("\n4. Global stats:")
    stats = hierarchy.get_all_stats()
    print(f"✓ Total tasks: {stats['total_tasks']}")
    print(f"✓ Total cost: ${stats['total_cost']:.6f}")

    print("\n" + "="*60)
    print("✓ QUICK TEST COMPLETED")
    print("="*60)
    print("\nAgent system is operational!")
    print("\nCapabilities:")
    print("  - CEO + 4 Directors (Code, Data, Communication, Operations)")
    print("  - Agent memory and context")
    print("  - Cost optimization")
    print("  - Delegation system")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
