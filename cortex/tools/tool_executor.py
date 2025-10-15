"""
Tool Executor - Exécute automatiquement les tools demandés par le LLM
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from cortex.tools.standard_tool import StandardTool
from cortex.core.llm_client import LLMClient, LLMResponse, ModelTier, ToolCall


@dataclass
class ExecutionResult:
    """Résultat de l'exécution d'un tool"""
    tool_name: str
    tool_call_id: str
    success: bool
    result: Any
    error: Optional[str] = None


class ToolExecutor:
    """
    Exécuteur de tools avec support du tool calling natif

    Workflow:
    1. Envoyer requête au LLM avec tools disponibles
    2. Si LLM demande un tool, l'exécuter
    3. Renvoyer le résultat au LLM
    4. Répéter jusqu'à réponse finale
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.tools: Dict[str, StandardTool] = {}
        self.max_iterations = 10  # Protection contre boucles infinies

    def register_tool(self, tool: StandardTool):
        """Enregistre un tool disponible"""
        self.tools[tool.name] = tool

    def register_tools(self, tools: List[StandardTool]):
        """Enregistre plusieurs tools"""
        for tool in tools:
            self.register_tool(tool)

    def execute_with_tools(
        self,
        messages: List[Dict[str, str]],
        tier: ModelTier = ModelTier.DEEPSEEK,
        max_tokens: int = 2048,
        temperature: float = 1.0,
        tools: Optional[List[StandardTool]] = None,
        verbose: bool = False
    ) -> LLMResponse:
        """
        Exécute une requête avec support automatique des tools

        Args:
            messages: Messages de conversation
            tier: Tier du modèle LLM
            max_tokens: Tokens max
            temperature: Température
            tools: Tools à utiliser (si None, utilise tous les tools enregistrés)
            verbose: Afficher les étapes intermédiaires

        Returns:
            Réponse finale du LLM
        """
        # Utiliser les tools fournis ou ceux enregistrés
        available_tools = tools or list(self.tools.values())

        if not available_tools:
            # Pas de tools, appel direct
            return self.llm_client.complete(
                messages=messages,
                tier=tier,
                max_tokens=max_tokens,
                temperature=temperature
            )

        # Conversation avec tools
        conversation_messages = messages.copy()
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1

            if verbose:
                print(f"\n[Iteration {iteration}] Calling LLM...")

            # Appeler le LLM avec les tools
            response = self.llm_client.complete(
                messages=conversation_messages,
                tier=tier,
                max_tokens=max_tokens,
                temperature=temperature,
                tools=available_tools
            )

            # Si pas de tool calls, c'est la réponse finale
            if not response.tool_calls:
                if verbose:
                    print(f"[Iteration {iteration}] Final response received")
                return response

            # Exécuter les tools demandés
            if verbose:
                print(f"[Iteration {iteration}] Executing {len(response.tool_calls)} tool(s)...")

            tool_results = []
            for tool_call in response.tool_calls:
                result = self._execute_tool_call(tool_call, verbose)
                tool_results.append(result)

            # Ajouter les résultats à la conversation
            # Format différent selon le provider
            if tier == ModelTier.CLAUDE:
                # Format Anthropic
                conversation_messages.append({
                    "role": "assistant",
                    "content": [{
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments
                    } for tc in response.tool_calls]
                })

                conversation_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": result.tool_call_id,
                        "content": str(result.result) if result.success else result.error
                    } for result, tc in zip(tool_results, response.tool_calls)]
                })
            else:
                # Format OpenAI (Nano et DeepSeek)
                conversation_messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": str(tc.arguments)
                        }
                    } for tc in response.tool_calls]
                })

                for result, tc in zip(tool_results, response.tool_calls):
                    conversation_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": str(result.result) if result.success else result.error
                    })

        # Si on arrive ici, on a dépassé max_iterations
        raise RuntimeError(f"Max iterations ({self.max_iterations}) reached")

    def _execute_tool_call(self, tool_call: ToolCall, verbose: bool = False) -> ExecutionResult:
        """Exécute un tool call"""
        tool_name = tool_call.name

        if verbose:
            print(f"  - Executing tool: {tool_name}")

        # Vérifier que le tool existe
        if tool_name not in self.tools:
            error_msg = f"Tool '{tool_name}' not found"
            if verbose:
                print(f"    ERROR: {error_msg}")
            return ExecutionResult(
                tool_name=tool_name,
                tool_call_id=tool_call.id,
                success=False,
                result=None,
                error=error_msg
            )

        tool = self.tools[tool_name]

        # Valider les paramètres
        valid, error = tool.validate_params(tool_call.arguments)
        if not valid:
            if verbose:
                print(f"    ERROR: {error}")
            return ExecutionResult(
                tool_name=tool_name,
                tool_call_id=tool_call.id,
                success=False,
                result=None,
                error=error
            )

        # Exécuter le tool
        try:
            result = tool.execute(**tool_call.arguments)

            if verbose:
                print(f"    SUCCESS: {result}")

            return ExecutionResult(
                tool_name=tool_name,
                tool_call_id=tool_call.id,
                success=True,
                result=result
            )
        except Exception as e:
            error_msg = f"Execution error: {str(e)}"
            if verbose:
                print(f"    ERROR: {error_msg}")

            return ExecutionResult(
                tool_name=tool_name,
                tool_call_id=tool_call.id,
                success=False,
                result=None,
                error=error_msg
            )


# Exemple d'utilisation
if __name__ == "__main__":
    from cortex.tools.standard_tool import tool

    # Créer quelques tools de test
    @tool(
        name="add",
        description="Add two numbers together",
        parameters={
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        }
    )
    def add(a: float, b: float) -> float:
        return a + b

    @tool(
        name="multiply",
        description="Multiply two numbers",
        parameters={
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        }
    )
    def multiply(a: float, b: float) -> float:
        return a * b

    # Créer l'exécuteur
    executor = ToolExecutor()
    executor.register_tools([add, multiply])

    print("Tool Executor initialized with tools:")
    print(f"  - {list(executor.tools.keys())}")

    # Test (nécessite une clé API configurée)
    try:
        messages = [
            {"role": "user", "content": "What is 5 + 3, and then multiply that result by 2?"}
        ]

        print("\nExecuting request with tools...")
        response = executor.execute_with_tools(
            messages=messages,
            tier=ModelTier.DEEPSEEK,
            verbose=True
        )

        print(f"\n=== Final Response ===")
        print(f"Content: {response.content}")
        print(f"Tokens: {response.tokens_input} in, {response.tokens_output} out")
        print(f"Cost: ${response.cost:.6f}")

    except Exception as e:
        print(f"\nTest skipped (API key not configured or other error): {e}")
