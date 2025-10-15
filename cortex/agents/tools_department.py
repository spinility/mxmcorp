"""
Tools Department - Département des Outils
Fabrique et gère dynamiquement les outils selon les besoins des employés
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
import json
import re

from cortex.tools.standard_tool import StandardTool, tool
from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier


@dataclass
class ToolRequest:
    """Requête pour créer un nouvel outil"""
    requested_by: str  # Nom de l'agent/employé demandeur
    tool_purpose: str  # But de l'outil
    input_description: str  # Description des inputs
    output_description: str  # Description des outputs attendus
    example_usage: Optional[str] = None  # Exemple d'utilisation
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class ToolsDepartment:
    """
    Département des Outils

    Responsabilités:
    - Analyser les demandes de création d'outils
    - Générer du code d'outil fonctionnel
    - Valider et tester les outils
    - Maintenir un catalogue d'outils disponibles
    - Rendre les outils disponibles à tous les employés
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

        # Catalogue des outils créés
        self.tool_catalog: Dict[str, Dict[str, Any]] = {}

        # Compteurs
        self.tools_created = 0
        self.requests_processed = 0
        self.total_cost = 0.0

    def create_tool(
        self,
        request: ToolRequest,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Crée un nouvel outil sur mesure

        Args:
            request: Requête de création d'outil
            verbose: Mode verbose

        Returns:
            Dict avec outil créé et métadonnées
        """
        self.requests_processed += 1

        if verbose:
            print(f"\n[Tools] Processing tool creation request from {request.requested_by}")
            print(f"[Tools] Purpose: {request.tool_purpose[:80]}...")

        try:
            # Générer le code de l'outil
            tool_code = self._generate_tool_code(request, verbose)

            # Créer l'outil exécutable
            tool_obj = self._create_executable_tool(tool_code, request, verbose)

            # Enregistrer dans le catalogue
            tool_record = {
                "tool": tool_obj,
                "code": tool_code,
                "created_at": datetime.now().isoformat(),
                "requested_by": request.requested_by,
                "purpose": request.tool_purpose,
                "usage_count": 0
            }

            tool_name = tool_obj.name
            self.tool_catalog[tool_name] = tool_record
            self.tools_created += 1

            if verbose:
                print(f"[Tools] ✓ Created tool: {tool_name}")
                print(f"[Tools] Description: {tool_obj.description[:80]}...")

            return {
                "success": True,
                "tool": tool_obj,
                "tool_name": tool_name,
                "code": tool_code,
                "cost": self.total_cost
            }

        except Exception as e:
            if verbose:
                print(f"[Tools] ✗ Failed to create tool: {e}")

            return {
                "success": False,
                "error": str(e),
                "request": request
            }

    def _generate_tool_code(
        self,
        request: ToolRequest,
        verbose: bool = False
    ) -> str:
        """
        Génère le code Python d'un outil via LLM
        Utilise DEEPSEEK pour un bon équilibre coût/qualité de code
        """
        # Construire le prompt sans f-string pour éviter les problèmes de backslash
        example_part = f"\n\nEXAMPLE USAGE:\n{request.example_usage}" if request.example_usage else ""

        prompt = """You are an expert Python developer creating a tool/function.

TOOL PURPOSE:
""" + request.tool_purpose + """

INPUT DESCRIPTION:
""" + request.input_description + """

OUTPUT DESCRIPTION:
""" + request.output_description + example_part + """

Generate a complete, working Python function that:
1. Has a clear, descriptive name (snake_case)
2. Includes proper type hints
3. Has a detailed docstring
4. Handles errors gracefully
5. Returns the expected output format
6. Is decorated with @tool (imported from cortex.tools.standard_tool)

The function should be production-ready and efficient.

Return ONLY the Python code, no explanations before or after.
Start with the import statement and end with the function definition.

Example format:
```python
from cortex.tools.standard_tool import tool

@tool(name="tool_name", description="Tool description")
def tool_name(param1: str, param2: int) -> dict:
    '''
    Detailed docstring explaining what the tool does.

    Args:
        param1: Description
        param2: Description

    Returns:
        dict: Description of return value
    '''
    try:
        # Implementation
        result = ...
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```
"""

        messages = [
            {"role": "user", "content": prompt}
        ]

        # Utiliser DEEPSEEK (bon pour le code, pas cher)
        response = self.llm_client.complete(
            messages=messages,
            tier=ModelTier.DEEPSEEK,
            temperature=1.0  # DeepSeek reasoner exige temperature=1
        )

        self.total_cost += response.cost

        if verbose:
            print(f"[Tools] Code generation cost: ${response.cost:.6f}")

        # Extraire le code
        code = self._extract_code_from_response(response.content)

        return code

    def _extract_code_from_response(self, content: str) -> str:
        """Extrait le code Python de la réponse LLM"""
        # Chercher un bloc de code markdown
        pattern = r'```(?:python)?\s*\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)

        if matches:
            return matches[0].strip()

        # Sinon, prendre tout le contenu
        return content.strip()

    def _create_executable_tool(
        self,
        code: str,
        request: ToolRequest,
        verbose: bool = False
    ) -> StandardTool:
        """
        Crée un outil exécutable depuis le code généré
        """
        try:
            # Préparer l'environnement d'exécution
            namespace = {
                'tool': tool,
                'StandardTool': StandardTool,
            }

            # Importer les modules couramment utilisés
            exec("import json", namespace)
            exec("import re", namespace)
            exec("import os", namespace)
            exec("import datetime", namespace)
            exec("from typing import Dict, List, Any, Optional", namespace)

            # Exécuter le code
            exec(code, namespace)

            # Trouver la fonction décorée (elle sera dans namespace)
            tool_obj = None
            for name, obj in namespace.items():
                if isinstance(obj, StandardTool):
                    tool_obj = obj
                    break

            if not tool_obj:
                raise ValueError("No tool function found in generated code")

            return tool_obj

        except Exception as e:
            if verbose:
                print(f"[Tools] Error executing generated code: {e}")

            # Fallback: créer un outil basique qui retourne une erreur
            return self._create_fallback_tool(request)

    def _create_fallback_tool(self, request: ToolRequest) -> StandardTool:
        """Crée un outil de secours si la génération échoue"""
        # Générer un nom basé sur le purpose
        words = re.findall(r'\w+', request.tool_purpose.lower())
        tool_name = '_'.join(words[:3])

        @tool(name=tool_name, description=request.tool_purpose)
        def fallback_tool(**kwargs) -> dict:
            """
            Fallback tool - needs manual implementation
            """
            return {
                "success": False,
                "error": "This tool requires manual implementation",
                "purpose": request.tool_purpose,
                "inputs": kwargs
            }

        return fallback_tool

    def get_tool(self, name: str) -> Optional[StandardTool]:
        """Récupère un outil par son nom"""
        record = self.tool_catalog.get(name)
        if record:
            record['usage_count'] += 1
            return record['tool']
        return None

    def get_all_tools(self) -> List[StandardTool]:
        """Récupère tous les outils disponibles"""
        return [record['tool'] for record in self.tool_catalog.values()]

    def list_tools(self) -> List[Dict[str, Any]]:
        """Liste tous les outils avec leurs métadonnées"""
        return [
            {
                "name": record['tool'].name,
                "description": record['tool'].description,
                "created_at": record['created_at'],
                "requested_by": record['requested_by'],
                "usage_count": record['usage_count']
            }
            for record in self.tool_catalog.values()
        ]

    def search_tools(self, query: str) -> List[StandardTool]:
        """Cherche des outils par mot-clé"""
        query_lower = query.lower()
        matching_tools = []

        for record in self.tool_catalog.values():
            tool_obj = record['tool']
            if (query_lower in tool_obj.name.lower() or
                query_lower in tool_obj.description.lower() or
                query_lower in record['purpose'].lower()):
                matching_tools.append(tool_obj)

        return matching_tools

    def get_stats(self) -> Dict[str, Any]:
        """Statistiques du département des Outils"""
        return {
            "tools_created": self.tools_created,
            "requests_processed": self.requests_processed,
            "total_cost": self.total_cost,
            "available_tools": len(self.tool_catalog),
            "total_usage": sum(
                record['usage_count']
                for record in self.tool_catalog.values()
            )
        }

    def export_tool_code(self, tool_name: str) -> Optional[str]:
        """Exporte le code source d'un outil"""
        record = self.tool_catalog.get(tool_name)
        if record:
            return record['code']
        return None

    def __repr__(self):
        return f"<ToolsDepartment: {self.tools_created} tools created>"
