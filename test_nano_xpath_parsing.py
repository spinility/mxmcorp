#!/usr/bin/env python3
"""
Test NANO model's ability to parse explicit XPath tool calls
"""

import os
import sys
from cortex.core.llm_client import LLMClient, ModelTier
from cortex.core.prompt_engineer import create_prompt_engineer
from cortex.tools.intelligence_tools import get_all_intelligence_tools

def test_nano_xpath_parsing():
    """Test if NANO can parse explicit tool calls with parameters"""

    print("=" * 80)
    print("Testing NANO Model XPath Tool Call Parsing")
    print("=" * 80)
    print()

    # Initialize components
    llm_client = LLMClient()
    prompt_engineer = create_prompt_engineer(llm_client)
    intelligence_tools = get_all_intelligence_tools()

    # Build NANO prompt
    system_prompt = prompt_engineer.build_agent_prompt(
        tier=ModelTier.NANO,
        user_request="Test request",
        available_tools=intelligence_tools
    )

    # Test cases
    test_cases = [
        {
            "name": "Explicit with 'Use' keyword",
            "request": "Use scrape_xpath with url=https://example.com and xpath=//h1/text()",
            "expected_tool": "scrape_xpath",
            "expected_params": {"url": "https://example.com", "xpath": "//h1/text()"}
        },
        {
            "name": "Explicit with 'Extract' keyword",
            "request": "Extract text from XPATH=/html/body/div[1] at URL=https://site.com",
            "expected_tool": "scrape_xpath",
            "expected_params": {"url": "https://site.com", "xpath": "/html/body/div[1]"}
        },
        {
            "name": "Forbes URL (user's actual request)",
            "request": "utilise un outil pour extraire le texte d'un XPATH=/html/body/div[2]/div[2]/div/div[2]/div[1]/div/section[5]/div[2]/div/div[4]/div[1] dans un URL=https://www.forbes.com/real-time-billionaires/",
            "expected_tool": "scrape_xpath",
            "expected_params": {
                "url": "https://www.forbes.com/real-time-billionaires/",
                "xpath": "/html/body/div[2]/div[2]/div/div[2]/div[1]/div/section[5]/div[2]/div/div[4]/div[1]"
            }
        }
    ]

    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"Test {i}: {test['name']}")
        print(f"{'─' * 80}")
        print(f"Request: {test['request']}")
        print()

        try:
            # Call NANO model
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": test['request']}
            ]

            response = llm_client.complete(
                messages=messages,
                tier=ModelTier.NANO,
                max_tokens=500,  # Increased from 300
                temperature=0.1,
                tools=intelligence_tools,  # Pass the tools!
                tool_choice="auto"
            )

            print(f"NANO Response:")
            print(response.content)
            print()

            # Check if tool was called
            if response.tool_calls and len(response.tool_calls) > 0:
                tool_call = response.tool_calls[0]
                tool_name = tool_call.name  # ToolCall is a dataclass, not a dict
                tool_args = tool_call.arguments

                print(f"✓ Tool called: {tool_name}")
                print(f"  Arguments: {tool_args}")

                # Validate
                success = (
                    tool_name == test['expected_tool'] and
                    tool_args.get('url') == test['expected_params']['url'] and
                    tool_args.get('xpath') == test['expected_params']['xpath']
                )

                if success:
                    print(f"✅ PASS: Tool call matches expected behavior")
                    results.append(("PASS", test['name']))
                else:
                    print(f"❌ FAIL: Tool call doesn't match expected")
                    print(f"   Expected: {test['expected_tool']}{test['expected_params']}")
                    print(f"   Got: {tool_name}{tool_args}")
                    results.append(("FAIL", test['name']))
            else:
                print(f"❌ FAIL: No tool call detected")
                print(f"   Expected: {test['expected_tool']}{test['expected_params']}")
                results.append(("FAIL", test['name']))

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results.append(("ERROR", test['name']))

    # Summary
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    passed = sum(1 for r in results if r[0] == "PASS")
    failed = sum(1 for r in results if r[0] == "FAIL")
    errors = sum(1 for r in results if r[0] == "ERROR")

    for status, name in results:
        icon = "✅" if status == "PASS" else "❌"
        print(f"{icon} [{status:5s}] {name}")

    print()
    print(f"Results: {passed} passed, {failed} failed, {errors} errors out of {len(results)} tests")

    if passed == len(results):
        print()
        print("🎉 All tests passed! NANO model correctly handles explicit XPath tool calls.")
        return 0
    else:
        print()
        print("⚠️  Some tests failed. NANO prompt may need further refinement.")
        return 1

if __name__ == "__main__":
    sys.exit(test_nano_xpath_parsing())
