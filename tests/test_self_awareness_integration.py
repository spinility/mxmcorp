"""
Test d'intégration du système Self-Awareness (Phase 4.2)

Teste:
- Découverte automatique des capacités
- Scanning de l'environnement
- Génération de rapports
- Réponses aux questions "Que peux-tu faire?"
"""

from cortex.core import (
    CapabilityRegistry,
    EnvironmentScanner,
    SelfIntrospectionAgent
)


def test_self_awareness_integration():
    """Test complet du système self-awareness"""

    print("="*70)
    print("PHASE 4.2 - SELF-AWARENESS SYSTEM - INTEGRATION TEST")
    print("="*70)

    # STEP 1: Capability Discovery
    print("\n1. Testing Capability Discovery...")
    registry = CapabilityRegistry()
    capabilities = registry.discover_all_capabilities()

    assert len(capabilities) > 0, "No capabilities discovered"
    assert 'department' in [c.type for c in capabilities.values()], "No departments found"
    assert 'agent' in [c.type for c in capabilities.values()], "No agents found"
    assert 'tool' in [c.type for c in capabilities.values()], "No tools found"

    print(f"✓ Discovered {len(capabilities)} capabilities")

    # STEP 2: Environment Scanning
    print("\n2. Testing Environment Scanning...")
    scanner = EnvironmentScanner()
    env_info = scanner.scan_full_environment()

    assert env_info.python_version is not None, "Python version not detected"
    assert env_info.platform is not None, "Platform not detected"
    assert env_info.working_directory is not None, "Working directory not detected"

    print(f"✓ Environment scanned: {env_info.platform} Python {env_info.python_version}")

    # STEP 3: Statistics
    print("\n3. Testing Statistics...")
    stats = registry.get_statistics()

    assert stats['total_capabilities'] == len(capabilities)
    assert 'by_type' in stats
    assert 'by_status' in stats

    print(f"✓ Statistics: {stats['total_capabilities']} total capabilities")
    print(f"  By type: {stats['by_type']}")

    # STEP 4: Search
    print("\n4. Testing Capability Search...")
    web_results = registry.search_capabilities("web")

    print(f"✓ Search 'web': {len(web_results)} results")
    if web_results:
        print(f"  Top result: {web_results[0].name}")

    # STEP 5: Self Introspection Agent
    print("\n5. Testing Self Introspection Agent...")
    agent = SelfIntrospectionAgent(registry, scanner)

    # Generate report
    report = agent.generate_capability_report()

    assert "CORTEX SELF-AWARENESS REPORT" in report
    assert "WHAT I CAN DO" in report
    assert "CURRENT LIMITATIONS" in report
    assert "ENVIRONMENT STATUS" in report

    print(f"✓ Report generated ({len(report)} chars)")

    # Test can_i_do
    print("\n6. Testing 'can_i_do' functionality...")
    test_queries = [
        "analyze code",
        "scrape website",
        "generate report"
    ]

    for query in test_queries:
        result = agent.can_i_do(query)
        print(f"  '{query}': can_do={result['can_do']}, confidence={result.get('confidence', 'N/A')}")

    # STEP 6: Agent Statistics
    print("\n7. Testing Agent Statistics...")
    agent_stats = agent.get_statistics()

    assert 'capabilities' in agent_stats
    assert 'environment' in agent_stats
    assert agent_stats['capabilities']['total_capabilities'] > 0

    print(f"✓ Agent statistics:")
    print(f"  Total capabilities: {agent_stats['capabilities']['total_capabilities']}")
    print(f"  Platform: {agent_stats['environment']['platform']}")
    print(f"  API keys configured: {agent_stats['environment']['api_keys_configured']}/3")

    # STEP 7: Save capabilities
    print("\n8. Testing capability persistence...")
    registry.save_to_file("cortex/data/test_self_awareness_capabilities.json")
    print("✓ Capabilities saved to file")

    # STEP 8: Display
    print("\n9. Testing display functionality...")
    print("\nDepartments:")
    registry.display_capabilities("department")

    print("\n" + "="*70)
    print("✅ SELF-AWARENESS SYSTEM - ALL TESTS PASSED!")
    print("="*70)

    return True


if __name__ == "__main__":
    try:
        success = test_self_awareness_integration()

        if success:
            print("\n✅ Integration test passed successfully!")
        else:
            print("\n❌ Some tests failed")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
