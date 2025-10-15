#!/usr/bin/env python3
"""
Test rapide du Smart Router et des Intelligence tools

Démontre que le système peut maintenant:
1. Détecter automatiquement les requêtes XPath/web scraping
2. Router vers le département Intelligence approprié
3. Utiliser les tools scrape_xpath et validate_xpath
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from cortex.agents.smart_router_agent import SmartRouterAgent
from cortex.tools.intelligence_tools import get_all_intelligence_tools

def test_smart_routing():
    """Test du smart router avec différentes requêtes"""

    print("=" * 80)
    print("TEST SMART ROUTING - Intelligence Department")
    print("=" * 80)
    print()

    # Initialize
    router = SmartRouterAgent()
    tools = get_all_intelligence_tools()
    tool_names = [t.name for t in tools]

    print(f"✓ Intelligence tools loaded: {', '.join(tool_names)}")
    print()

    # Test 1: XPath request (should route to Intelligence)
    print("Test 1: XPath extraction request")
    print("-" * 80)
    request1 = "Extract text from https://example.com using XPath //h1/text()"
    decision1 = router.route_request(request1, tool_names)

    print(f"Request: {request1}")
    print(f"Route to: {decision1['route_to'].upper()}")
    print(f"Confidence: {decision1['confidence']:.2f}")

    if decision1['route_to'] == 'department':
        print(f"✓ Department: {decision1['department'].upper()}")
        print(f"✓ Agent: {decision1['agent_suggestion']}")

    print()

    # Test 2: Web scraping request (should route to Intelligence)
    print("Test 2: Web scraping request")
    print("-" * 80)
    request2 = "Scrape data from a website with DOM navigation"
    decision2 = router.route_request(request2, tool_names)

    print(f"Request: {request2}")
    print(f"Route to: {decision2['route_to'].upper()}")
    print(f"Confidence: {decision2['confidence']:.2f}")

    if decision2['route_to'] == 'department':
        print(f"✓ Department: {decision2['department'].upper()}")
        print(f"✓ Agent: {decision2['agent_suggestion']}")

    print()

    # Test 3: Git request (should route to Maintenance)
    print("Test 3: Git operations request")
    print("-" * 80)
    request3 = "Show me the git diff for recent changes"
    decision3 = router.route_request(request3, tool_names)

    print(f"Request: {request3}")
    print(f"Route to: {decision3['route_to'].upper()}")
    print(f"Confidence: {decision3['confidence']:.2f}")

    if decision3['route_to'] == 'department':
        print(f"✓ Department: {decision3['department'].upper()}")
        print(f"✓ Agent: {decision3['agent_suggestion']}")

    print()

    # Test 4: Unknown request (should route to Tooler)
    print("Test 4: Unknown capability request")
    print("-" * 80)
    request4 = "Send an email notification to support@example.com"
    decision4 = router.route_request(request4, tool_names)

    print(f"Request: {request4}")
    print(f"Route to: {decision4['route_to'].upper()}")
    print(f"Confidence: {decision4['confidence']:.2f}")
    print(f"Reason: {decision4['reason']}")

    print()

    # Summary
    print("=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    print()

    results = [
        ("XPath extraction", decision1['route_to'] == 'department' and decision1['department'] == 'intelligence'),
        ("Web scraping", decision2['route_to'] == 'department' and decision2['department'] == 'intelligence'),
        ("Git operations", decision3['route_to'] == 'department' and decision3['department'] == 'maintenance'),
        ("Unknown capability", decision4['route_to'] == 'tooler')
    ]

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print()

    all_passed = all(result[1] for result in results)
    if all_passed:
        print("🎉 All tests passed! Smart routing is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check routing logic.")
        return False


def test_intelligence_tools():
    """Test que les intelligence tools sont bien exposés"""

    print()
    print("=" * 80)
    print("TEST INTELLIGENCE TOOLS AVAILABILITY")
    print("=" * 80)
    print()

    tools = get_all_intelligence_tools()

    expected_tools = ['scrape_xpath', 'validate_xpath', 'add_web_source']

    print(f"Expected tools: {len(expected_tools)}")
    print(f"Loaded tools: {len(tools)}")
    print()

    for tool in tools:
        print(f"✓ {tool.name}")
        print(f"  Category: {tool.category}")
        print(f"  Description: {tool.description}")
        print(f"  Parameters: {', '.join(tool.parameters.keys())}")
        print()

    all_found = all(tool_name in [t.name for t in tools] for tool_name in expected_tools)

    if all_found and len(tools) == len(expected_tools):
        print("✅ All intelligence tools are available!")
        return True
    else:
        print("❌ Some intelligence tools are missing!")
        return False


if __name__ == "__main__":
    print()
    print("🧠 CORTEX MXMCorp - Smart Routing & Intelligence Tools Test")
    print()

    try:
        # Test 1: Smart routing
        routing_success = test_smart_routing()

        # Test 2: Intelligence tools
        tools_success = test_intelligence_tools()

        # Final result
        print()
        print("=" * 80)
        print("FINAL RESULT")
        print("=" * 80)
        print()

        if routing_success and tools_success:
            print("🎉 ALL TESTS PASSED!")
            print()
            print("✓ Smart Router correctly routes web/XPath requests to Intelligence")
            print("✓ Intelligence tools (scrape_xpath, validate_xpath, add_web_source) are available")
            print("✓ System will no longer freeze on XPath extraction requests")
            print()
            sys.exit(0)
        else:
            print("❌ SOME TESTS FAILED")
            print()
            sys.exit(1)

    except Exception as e:
        print()
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
