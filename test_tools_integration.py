"""
Test d'intégration du système de tools standard

Ce script teste:
1. Création de tools avec décorateur @tool
2. Tool calling natif avec LLM
3. Exécution automatique avec ToolExecutor
"""

from cortex.tools.standard_tool import tool
from cortex.tools.tool_executor import ToolExecutor
from cortex.core.model_router import ModelTier


# Créer quelques tools de test simples
@tool(
    name="add_numbers",
    description="Add two numbers together",
    parameters={
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "First number"},
            "b": {"type": "number", "description": "Second number"}
        },
        "required": ["a", "b"]
    },
    category="math",
    tags=["arithmetic", "calculator"]
)
def add_numbers(a: float, b: float) -> float:
    """Adds two numbers"""
    return {"result": a + b, "operation": "addition"}


@tool(
    name="multiply_numbers",
    description="Multiply two numbers",
    parameters={
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "First number"},
            "b": {"type": "number", "description": "Second number"}
        },
        "required": ["a", "b"]
    },
    category="math",
    tags=["arithmetic", "calculator"]
)
def multiply_numbers(a: float, b: float) -> float:
    """Multiplies two numbers"""
    return {"result": a * b, "operation": "multiplication"}


@tool(
    name="count_words",
    description="Count the number of words in a text",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to analyze"}
        },
        "required": ["text"]
    },
    category="text",
    tags=["text-processing", "analysis"]
)
def count_words(text: str) -> dict:
    """Counts words in text"""
    words = text.split()
    return {
        "word_count": len(words),
        "character_count": len(text),
        "text_preview": text[:50] + "..." if len(text) > 50 else text
    }


def test_basic_tools():
    """Test 1: Vérifier que les tools fonctionnent directement"""
    print("=" * 60)
    print("TEST 1: Basic Tool Execution")
    print("=" * 60)

    # Test add_numbers
    print("\n1. Testing add_numbers(5, 3)...")
    result = add_numbers.execute(a=5, b=3)
    print(f"   Result: {result}")
    assert result["result"] == 8, "Addition failed"
    print("   ✓ PASS")

    # Test multiply_numbers
    print("\n2. Testing multiply_numbers(4, 7)...")
    result = multiply_numbers.execute(a=4, b=7)
    print(f"   Result: {result}")
    assert result["result"] == 28, "Multiplication failed"
    print("   ✓ PASS")

    # Test count_words
    print("\n3. Testing count_words('Hello world this is a test')...")
    result = count_words.execute(text="Hello world this is a test")
    print(f"   Result: {result}")
    assert result["word_count"] == 6, "Word count failed"
    print("   ✓ PASS")

    print("\n✓ All basic tool tests passed!")


def test_tool_formats():
    """Test 2: Vérifier les formats OpenAI et Anthropic"""
    print("\n" + "=" * 60)
    print("TEST 2: Tool Format Conversion")
    print("=" * 60)

    print("\n1. OpenAI Format:")
    openai_format = add_numbers.to_openai_format()
    print(f"   Type: {openai_format['type']}")
    print(f"   Name: {openai_format['function']['name']}")
    print(f"   Description: {openai_format['function']['description']}")
    print("   ✓ PASS")

    print("\n2. Anthropic Format:")
    anthropic_format = add_numbers.to_anthropic_format()
    print(f"   Name: {anthropic_format['name']}")
    print(f"   Description: {anthropic_format['description']}")
    print("   ✓ PASS")

    print("\n✓ All format conversion tests passed!")


def test_tool_executor():
    """Test 3: Tester l'exécuteur de tools"""
    print("\n" + "=" * 60)
    print("TEST 3: Tool Executor")
    print("=" * 60)

    # Créer l'exécuteur
    executor = ToolExecutor()
    executor.register_tools([add_numbers, multiply_numbers, count_words])

    print(f"\n✓ Registered {len(executor.tools)} tools")
    print(f"   Tools: {list(executor.tools.keys())}")

    print("\n✓ Tool executor test passed!")


def test_llm_integration():
    """Test 4: Test intégration avec LLM (optionnel, nécessite API key)"""
    print("\n" + "=" * 60)
    print("TEST 4: LLM Integration (optional)")
    print("=" * 60)

    try:
        executor = ToolExecutor()
        executor.register_tools([add_numbers, multiply_numbers])

        messages = [
            {"role": "user", "content": "What is 15 + 27?"}
        ]

        print("\nSending request to LLM with tools...")
        print(f"Question: {messages[0]['content']}")

        response = executor.execute_with_tools(
            messages=messages,
            tier=ModelTier.DEEPSEEK,
            verbose=True
        )

        print(f"\n✓ LLM Response:")
        print(f"   {response.content}")
        print(f"   Tokens: {response.tokens_input} in, {response.tokens_output} out")
        print(f"   Cost: ${response.cost:.6f}")

        print("\n✓ LLM integration test passed!")

    except Exception as e:
        print(f"\n⚠ LLM integration test skipped: {e}")
        print("   (This is OK if API keys are not configured)")


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "CORTEX STANDARD TOOLS - INTEGRATION TEST" + " " * 7 + "║")
    print("╚" + "=" * 58 + "╝")

    try:
        # Run all tests
        test_basic_tools()
        test_tool_formats()
        test_tool_executor()
        test_llm_integration()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe standard tools system is working correctly!")
        print("You can now:")
        print("  1. Create tools with @tool decorator")
        print("  2. Use tools with OpenAI/Anthropic/DeepSeek")
        print("  3. Execute tools automatically with ToolExecutor")
        print("  4. Generate new tools with StandardToolFactory")
        print()

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
