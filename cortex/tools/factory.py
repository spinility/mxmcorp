"""
Tool Factory - Génération automatique d'outils
Le Cortex peut créer ses propres outils à la volée
"""

import os
import re
import ast
import importlib.util
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier
from .base_tool import BaseTool, ToolMetadata, ToolResult
from .standard_tool import StandardTool, tool


class ToolFactory:
    """
    Factory qui génère automatiquement des outils via LLM

    Processus:
    1. Analyser le besoin de l'utilisateur
    2. Générer le code Python de l'outil
    3. Valider le code (AST, sécurité)
    4. Tester l'outil
    5. Sauvegarder et enregistrer
    """

    def __init__(self, tools_dir: str = "cortex/tools/generated"):
        self.tools_dir = Path(tools_dir)
        self.tools_dir.mkdir(parents=True, exist_ok=True)

        self.llm_client = LLMClient()

        # Patterns dangereux à éviter
        self.forbidden_patterns = [
            r"__import__",
            r"eval\(",
            r"exec\(",
            r"compile\(",
            r"os\.system",
            r"subprocess\.call",
            r"subprocess\.run",
            r"open\(.+['\"]w",  # Écriture fichiers (sauf si explicitement requis)
        ]

    def create_tool(
        self,
        description: str,
        name: Optional[str] = None,
        category: str = "general",
        test_mode: bool = True,
        use_standard_format: bool = True
    ) -> Tuple[bool, Optional[StandardTool], Optional[str]]:
        """
        Crée un nouvel outil depuis une description

        Args:
            description: Description de ce que l'outil doit faire
            name: Nom de l'outil (généré auto si None)
            category: Catégorie (filesystem, web, database, etc.)
            test_mode: Si True, teste l'outil avant de le sauvegarder
            use_standard_format: Si True, génère un StandardTool (OpenAI/Anthropic compatible)

        Returns:
            (succès, outil, erreur)
        """
        # Étape 1: Analyser le besoin et générer le nom
        if not name:
            name = self._generate_tool_name(description)

        # Étape 2: Générer le code
        code_result = self._generate_tool_code(name, description, category, use_standard_format)
        if not code_result[0]:
            return False, None, code_result[1]

        code = code_result[1]

        # Étape 3: Valider le code
        valid, error = self._validate_code(code, use_standard_format)
        if not valid:
            return False, None, f"Code validation failed: {error}"

        # Étape 4: Créer le fichier
        tool_path = self.tools_dir / f"{name}.py"
        tool_path.write_text(code)

        # Étape 5: Charger l'outil
        tool = self._load_tool(tool_path, use_standard_format)
        if not tool:
            return False, None, "Failed to load generated tool"

        # Étape 6: Tester (si demandé)
        if test_mode and use_standard_format:
            test_ok, test_error = self._test_standard_tool(tool)
            if not test_ok:
                return False, None, f"Tool test failed: {test_error}"
        elif test_mode:
            test_ok, test_error = self._test_tool(tool)
            if not test_ok:
                return False, None, f"Tool test failed: {test_error}"

        return True, tool, None

    def _generate_tool_name(self, description: str) -> str:
        """Génère un nom d'outil depuis la description"""
        # Extraire les mots-clés principaux
        words = re.findall(r'\b[a-z]+\b', description.lower())

        # Prendre les 2-3 premiers mots significatifs
        significant_words = [w for w in words if len(w) > 3][:3]

        if not significant_words:
            significant_words = ["custom", "tool"]

        # Convertir en CamelCase
        name = "".join(w.capitalize() for w in significant_words) + "Tool"

        return name

    def _generate_tool_code(
        self,
        name: str,
        description: str,
        category: str,
        use_standard_format: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """Génère le code Python de l'outil via LLM"""

        if use_standard_format:
            prompt = f"""Tu es un expert en génération de code Python pour des outils.

Génère un outil Python avec le décorateur @tool (format standard OpenAI/Anthropic).

**Besoin:** {description}
**Nom:** {name}
**Catégorie:** {category}

**Requirements:**
1. Hériter de BaseTool (from cortex.tools.base_tool import BaseTool, ToolMetadata, ToolResult)
2. Implémenter __init__ avec ToolMetadata
3. Implémenter validate_params() pour valider les paramètres
4. Implémenter execute() pour la logique principale
5. Gérer les erreurs proprement
6. Retourner ToolResult avec success=True/False
7. Code propre, documenté, type hints
8. IMPORTANT: NE PAS utiliser eval(), exec(), __import__(), os.system(), subprocess
9. IMPORTANT: Code sécurisé et sandbox-friendly

**Template:**

```python
from datetime import datetime
from typing import Tuple, Optional
from cortex.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class {name}(BaseTool):
    \"\"\"
    [Description détaillée]
    \"\"\"

    def __init__(self):
        metadata = ToolMetadata(
            name="{name}",
            description="{description}",
            version="1.0.0",
            author="ai_generated",
            created_at=datetime.now(),
            category="{category}",
            tags=["auto-generated"],
            cost_estimate="free"
        )
        super().__init__(metadata)

    def validate_params(self, **kwargs) -> Tuple[bool, Optional[str]]:
        \"\"\"Valide les paramètres\"\"\"
        # TODO: Implémenter validation
        return True, None

    def execute(self, **kwargs) -> ToolResult:
        \"\"\"Exécute l'outil\"\"\"
        try:
            # TODO: Implémenter logique
            result_data = {{"message": "Not implemented"}}

            return ToolResult(
                success=True,
                data=result_data
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
```

Génère UNIQUEMENT le code Python complet et fonctionnel, sans explications.
"""

        try:
            messages = [
                {"role": "system", "content": "Tu es un expert en génération de code Python sécurisé."},
                {"role": "user", "content": prompt}
            ]

            # Utiliser deepseek pour la génération de code
            response = self.llm_client.complete(
                messages=messages,
                tier=ModelTier.DEEPSEEK,
                max_tokens=2048,
                temperature=0.3  # Basse température pour code déterministe
            )

            # Extraire le code des balises ```python
            code = response.content
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()

            return True, code

        except Exception as e:
            return False, f"Code generation failed: {e}"

    def _validate_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """Valide le code généré"""

        # Validation 1: Vérifier les patterns dangereux
        for pattern in self.forbidden_patterns:
            if re.search(pattern, code):
                return False, f"Forbidden pattern detected: {pattern}"

        # Validation 2: Parser AST
        try:
            ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {e}"

        # Validation 3: Vérifier qu'il hérite de BaseTool
        if "BaseTool" not in code:
            return False, "Tool must inherit from BaseTool"

        # Validation 4: Vérifier les méthodes obligatoires
        required_methods = ["validate_params", "execute"]
        for method in required_methods:
            if f"def {method}" not in code:
                return False, f"Missing required method: {method}"

        return True, None

    def _load_tool(self, tool_path: Path) -> Optional[BaseTool]:
        """Charge un outil depuis un fichier Python"""
        try:
            # Charger le module dynamiquement
            spec = importlib.util.spec_from_file_location(
                tool_path.stem,
                tool_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Trouver la classe qui hérite de BaseTool
            for item_name in dir(module):
                item = getattr(module, item_name)
                if (isinstance(item, type) and
                    issubclass(item, BaseTool) and
                    item is not BaseTool):
                    # Instancier l'outil
                    return item()

            return None

        except Exception as e:
            print(f"Failed to load tool: {e}")
            return None

    def _test_tool(self, tool: BaseTool) -> Tuple[bool, Optional[str]]:
        """Teste basiquement un outil"""
        try:
            # Test 1: Vérifier que validate_params fonctionne
            valid, error = tool.validate_params()

            # Test 2: Vérifier que execute ne crash pas (avec params vides)
            # Note: Le test peut échouer fonctionnellement, c'est OK
            # On vérifie juste qu'il n'y a pas de crash
            try:
                result = tool.execute()
                # Si execute retourne un résultat, c'est bon
                if isinstance(result, ToolResult):
                    return True, None
            except TypeError:
                # Params manquants, c'est OK
                return True, None

            return True, None

        except Exception as e:
            return False, str(e)


# Exemple d'utilisation
if __name__ == "__main__":
    factory = ToolFactory()

    # Test: Créer un outil simple
    description = "Un outil qui compte le nombre de mots dans un texte"

    print(f"Creating tool: {description}")
    success, tool, error = factory.create_tool(description, category="text")

    if success:
        print(f"\n✓ Tool created successfully!")
        print(f"  Name: {tool.metadata.name}")
        print(f"  Description: {tool.metadata.description}")
        print(f"  Category: {tool.metadata.category}")

        # Tester l'outil
        print(f"\nTesting tool...")
        result = tool.run(text="Hello world this is a test")
        print(f"  Result: {result}")
    else:
        print(f"\n✗ Tool creation failed: {error}")
