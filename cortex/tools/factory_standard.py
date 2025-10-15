"""
Tool Factory - Version Standard (génère des Standard Tools)
"""

import os
import re
import ast
import importlib.util
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Union
from datetime import datetime

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier
from cortex.tools.standard_tool import StandardTool, tool


class StandardToolFactory:
    """
    Factory qui génère automatiquement des StandardTools via LLM

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
        test_mode: bool = True
    ) -> Tuple[bool, Optional[StandardTool], Optional[str]]:
        """
        Crée un nouvel outil depuis une description

        Args:
            description: Description de ce que l'outil doit faire
            name: Nom de l'outil (généré auto si None)
            category: Catégorie (filesystem, web, database, etc.)
            test_mode: Si True, teste l'outil avant de le sauvegarder

        Returns:
            (succès, outil, erreur)
        """
        # Étape 1: Analyser le besoin et générer le nom
        if not name:
            name = self._generate_tool_name(description)

        # Étape 2: Générer le code
        code_result = self._generate_tool_code(name, description, category)
        if not code_result[0]:
            return False, None, code_result[1]

        code = code_result[1]

        # Étape 3: Valider le code
        valid, error = self._validate_code(code)
        if not valid:
            return False, None, f"Code validation failed: {error}"

        # Étape 4: Créer le fichier
        tool_path = self.tools_dir / f"{name.lower()}.py"
        tool_path.write_text(code)

        # Étape 5: Charger l'outil
        tool = self._load_tool(tool_path)
        if not tool:
            return False, None, "Failed to load generated tool"

        # Étape 6: Tester (si demandé)
        if test_mode:
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

        # snake_case pour les fonctions
        name = "_".join(significant_words)

        return name

    def _generate_tool_code(
        self,
        name: str,
        description: str,
        category: str
    ) -> Tuple[bool, Optional[str]]:
        """Génère le code Python de l'outil via LLM"""

        prompt = f"""Tu es un expert en génération de code Python pour des outils.

Génère un outil Python avec le décorateur @tool (format standard OpenAI/Anthropic).

**Besoin:** {description}
**Nom fonction:** {name}
**Catégorie:** {category}

**Requirements:**
1. Utiliser le décorateur @tool de cortex.tools.standard_tool
2. Définir les paramètres JSON Schema explicitement
3. Implémenter la fonction avec type hints
4. Gérer les erreurs proprement
5. Retourner le résultat directement (dict ou autre type Python)
6. Code propre, documenté, type hints
7. IMPORTANT: NE PAS utiliser eval(), exec(), __import__(), os.system(), subprocess
8. IMPORTANT: Code sécurisé et sandbox-friendly

**Template:**

```python
from cortex.tools.standard_tool import tool
from typing import Any, Dict

@tool(
    name="{name}",
    description="{description}",
    parameters={{
        "type": "object",
        "properties": {{
            # Définir les paramètres ici avec leurs types
            # Exemple: "text": {{"type": "string", "description": "Input text"}}
        }},
        "required": []  # Liste des paramètres requis
    }},
    category="{category}",
    tags=["auto-generated"]
)
def {name}(**kwargs) -> Any:
    \"\"\"
    {description}

    Args:
        **kwargs: Paramètres de l'outil

    Returns:
        Résultat de l'exécution
    \"\"\"
    try:
        # Implémenter la logique ici

        return {{
            "success": True,
            "data": {{}}  # Données de résultat
        }}
    except Exception as e:
        return {{
            "success": False,
            "error": str(e)
        }}
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

        # Validation 3: Vérifier qu'il utilise le décorateur @tool
        if "@tool" not in code:
            return False, "Tool must use @tool decorator"

        # Validation 4: Vérifier l'import
        if "from cortex.tools.standard_tool import tool" not in code:
            return False, "Missing import: from cortex.tools.standard_tool import tool"

        return True, None

    def _load_tool(self, tool_path: Path) -> Optional[StandardTool]:
        """Charge un outil depuis un fichier Python"""
        try:
            # Charger le module dynamiquement
            spec = importlib.util.spec_from_file_location(
                tool_path.stem,
                tool_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Trouver le StandardTool dans le module
            for item_name in dir(module):
                item = getattr(module, item_name)
                if isinstance(item, StandardTool):
                    return item

            return None

        except Exception as e:
            print(f"Failed to load tool: {e}")
            return None

    def _test_tool(self, tool: StandardTool) -> Tuple[bool, Optional[str]]:
        """Teste basiquement un outil"""
        try:
            # Test 1: Vérifier que validate_params fonctionne
            valid, error = tool.validate_params({})
            # C'est OK si validation échoue pour params vides

            # Test 2: Vérifier que execute ne crash pas
            try:
                result = tool.execute()
                # Si execute retourne un résultat sans crash, c'est bon
                return True, None
            except TypeError:
                # Params manquants, c'est OK
                return True, None

        except Exception as e:
            return False, str(e)


# Exemple d'utilisation
if __name__ == "__main__":
    factory = StandardToolFactory()

    # Test: Créer un outil simple
    description = "Un outil qui compte le nombre de mots dans un texte"

    print(f"Creating tool: {description}")
    success, tool, error = factory.create_tool(description, category="text")

    if success:
        print(f"\n✓ Tool created successfully!")
        print(f"  Name: {tool.name}")
        print(f"  Description: {tool.description}")
        print(f"  Category: {tool.category}")

        # Tester l'outil
        print(f"\nTesting tool...")
        try:
            result = tool.execute(text="Hello world this is a test")
            print(f"  Result: {result}")
        except Exception as e:
            print(f"  Test error (expected): {e}")
    else:
        print(f"\n✗ Tool creation failed: {error}")
