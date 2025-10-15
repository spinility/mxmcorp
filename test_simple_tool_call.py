#!/usr/bin/env python3
"""
Simple test to verify NANO can call tools at all
"""

from cortex.core.llm_client import LLMClient, ModelTier
from cortex.tools.intelligence_tools import get_all_intelligence_tools

def test_simple_tool_call():
    """Test if NANO can call scrape_xpath with a simple system message"""

    llm_client = LLMClient()
    tools = get_all_intelligence_tools()

    print("=" * 80)
    print("Simple NANO Tool Call Test")
    print("=" * 80)
    print()

    # Minimal system message
    messages = [
        {"role": "system", "content": "You are a helpful assistant. When asked to scrape or extract data from URLs, use the scrape_xpath tool."},
        {"role": "user", "content": "Use scrape_xpath to extract h1 text from https://example.com using xpath //h1/text()"}
    ]

    print("Request: Extract h1 from https://example.com")
    print()

    response = llm_client.complete(
        messages=messages,
        tier=ModelTier.NANO,
        max_tokens=500,
        temperature=0.1,
        tools=tools,
        tool_choice="auto"
    )

    print(f"Response content: {response.content}")
    print(f"Tool calls: {response.tool_calls}")
    print()

    if response.tool_calls:
        print(f"✅ SUCCESS: NANO called {len(response.tool_calls)} tool(s)")
        for tc in response.tool_calls:
            print(f"   - {tc.name}({tc.arguments})")
    else:
        print(f"❌ FAIL: NANO did not call any tools")
        print(f"   Content was: {response.content[:200] if response.content else '(empty)'}")

    return 0 if response.tool_calls else 1

if __name__ == "__main__":
    import sys
    sys.exit(test_simple_tool_call())
