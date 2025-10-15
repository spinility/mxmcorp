"""
Standard Tool - Compatible avec OpenAI/Anthropic/LangChain
Suit le format JSON Schema standard pour l'interopérabilité
"""

from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
import json
import inspect


@dataclass
class StandardTool:
    """
    Outil au format standard OpenAI/Anthropic

    Compatible avec:
    - OpenAI Function Calling
    - Anthropic Tool Use
    - LangChain Tools
    - Tout LLM supportant JSON Schema
    """

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    function: Callable
    category: str = "general"
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_openai_format(self) -> Dict[str, Any]:
        """
        Format OpenAI Function Calling

        Returns:
            {
                "type": "function",
                "function": {
                    "name": "...",
                    "description": "...",
                    "parameters": {...}
                }
            }
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def to_anthropic_format(self) -> Dict[str, Any]:
        """
        Format Anthropic Tool Use

        Returns:
            {
                "name": "...",
                "description": "...",
                "input_schema": {...}
            }
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters
        }

    def to_langchain_format(self) -> Dict[str, Any]:
        """Format LangChain (pour import/export)"""
        return {
            "name": self.name,
            "description": self.description,
            "args_schema": self.parameters,
            "func": self.function
        }

    def execute(self, **kwargs) -> Any:
        """
        Exécute la fonction avec les paramètres

        Args:
            **kwargs: Paramètres de la fonction

        Returns:
            Résultat de l'exécution
        """
        try:
            return self.function(**kwargs)
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Valide les paramètres selon le JSON Schema

        Args:
            params: Paramètres à valider

        Returns:
            (valide, erreur)
        """
        # Vérifier les paramètres requis
        required = self.parameters.get("required", [])
        for param in required:
            if param not in params:
                return False, f"Missing required parameter: {param}"

        # Vérifier les types (basique)
        properties = self.parameters.get("properties", {})
        for param, value in params.items():
            if param in properties:
                expected_type = properties[param].get("type")
                actual_type = type(value).__name__

                # Mapping Python -> JSON Schema types
                type_mapping = {
                    "str": "string",
                    "int": ["integer", "number"],
                    "float": "number",
                    "bool": "boolean",
                    "list": "array",
                    "dict": "object"
                }

                json_type = type_mapping.get(actual_type, actual_type)

                if isinstance(json_type, list):
                    if expected_type not in json_type:
                        return False, f"Invalid type for {param}: expected {expected_type}, got {actual_type}"
                elif json_type != expected_type:
                    return False, f"Invalid type for {param}: expected {expected_type}, got {actual_type}"

        return True, None

    def __repr__(self):
        return f"<StandardTool '{self.name}'>"


def tool(
    name: str,
    description: str,
    parameters: Optional[Dict[str, Any]] = None,
    category: str = "general",
    tags: Optional[List[str]] = None
):
    """
    Décorateur pour créer facilement des tools standards

    Usage:
        @tool(
            name="my_tool",
            description="Does something cool",
            parameters={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Input text"}
                },
                "required": ["input"]
            }
        )
        def my_tool_func(input: str) -> str:
            return f"Processed: {input}"
    """
    def decorator(func: Callable) -> StandardTool:
        # Si pas de paramètres fournis, les inférer depuis la signature
        if parameters is None:
            params = _infer_parameters(func)
        else:
            params = parameters

        return StandardTool(
            name=name,
            description=description,
            parameters=params,
            function=func,
            category=category,
            tags=tags or []
        )

    return decorator


def _infer_parameters(func: Callable) -> Dict[str, Any]:
    """Infère les paramètres JSON Schema depuis la signature Python"""
    sig = inspect.signature(func)

    properties = {}
    required = []

    type_mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object"
    }

    for param_name, param in sig.parameters.items():
        if param_name == "kwargs":
            continue

        # Inférer le type
        param_type = "string"  # Default
        if param.annotation != inspect.Parameter.empty:
            param_type = type_mapping.get(param.annotation, "string")

        properties[param_name] = {
            "type": param_type,
            "description": f"Parameter {param_name}"
        }

        # Marquer comme requis si pas de valeur par défaut
        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required
    }


# Exemples d'utilisation
if __name__ == "__main__":
    # Méthode 1: Décorateur avec paramètres explicites
    @tool(
        name="add_numbers",
        description="Adds two numbers together",
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
    def add(a: float, b: float) -> float:
        """Adds two numbers"""
        return a + b

    # Méthode 2: Décorateur avec inférence automatique
    @tool(
        name="greet",
        description="Greets someone by name",
        category="text"
    )
    def greet(name: str, formal: bool = False) -> str:
        """Greets someone"""
        if formal:
            return f"Good day, {name}"
        return f"Hello, {name}!"

    # Test
    print("Testing standard tools...")

    # Format OpenAI
    print("\n1. OpenAI format:")
    print(json.dumps(add.to_openai_format(), indent=2))

    # Format Anthropic
    print("\n2. Anthropic format:")
    print(json.dumps(add.to_anthropic_format(), indent=2))

    # Exécution
    print("\n3. Execution:")
    result = add.execute(a=5, b=3)
    print(f"add(5, 3) = {result}")

    result2 = greet.execute(name="Alice", formal=True)
    print(f"greet('Alice', formal=True) = {result2}")

    # Validation
    print("\n4. Validation:")
    valid, error = add.validate_params({"a": 5, "b": 3})
    print(f"Valid params: {valid}")

    valid, error = add.validate_params({"a": 5})  # Missing 'b'
    print(f"Missing param: {valid}, error: {error}")
