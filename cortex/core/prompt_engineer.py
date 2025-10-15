"""
Prompt Engineer - Génère des prompts optimisés selon le modèle cible

Utilise GPT-5 (Claude Sonnet) pour créer des prompts adaptés à:
- nano (gpt-3.5-turbo): Prompts courts, directs, simples
- deepseek: Prompts structurés, avec exemples
- claude: Prompts détaillés, avec raisonnement

Détecte automatiquement les contradictions:
- Demande de créer un outil qui existe déjà
- Demande incompatible avec les outils disponibles
"""

from typing import List, Dict, Any, Optional
from cortex.core.llm_client import LLMClient, ModelTier
from cortex.tools.standard_tool import StandardTool


class PromptEngineer:
    """Génère des prompts optimisés selon le contexte et le modèle"""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Prompt Engineer

        Args:
            llm_client: LLM client for GPT-5 calls
        """
        self.llm_client = llm_client

    def detect_contradiction(
        self,
        user_request: str,
        available_tools: List[StandardTool]
    ) -> Optional[Dict[str, Any]]:
        """
        Détecte si la requête contient une contradiction

        Args:
            user_request: Requête utilisateur
            available_tools: Outils disponibles

        Returns:
            Dict avec contradiction détectée ou None
        """
        # Patterns de contradictions courantes
        create_patterns = [
            "implémente", "implemente", "crée", "cree", "ajoute", "créer", "creer",
            "implement", "create", "add", "make", "build"
        ]

        tool_patterns = [
            "tool", "outil", "fonction", "function", "command", "commande"
        ]

        # Check si c'est une demande de création d'outil
        is_tool_creation = (
            any(pattern in user_request.lower() for pattern in create_patterns) and
            any(pattern in user_request.lower() for pattern in tool_patterns)
        )

        if not is_tool_creation:
            return None

        # Chercher quel outil est demandé
        # Méthode 1: Par nom d'outil
        for tool in available_tools:
            # Variations du nom (avec/sans underscore, etc.)
            name_variations = [
                tool.name,
                tool.name.replace("_", " "),
                tool.name.replace("_", "-"),
                tool.name.replace("_", "")
            ]

            for variation in name_variations:
                if variation.lower() in user_request.lower():
                    # CONTRADICTION DÉTECTÉE!
                    return {
                        "type": "tool_already_exists",
                        "tool_name": tool.name,
                        "requested_variation": variation,
                        "message": f"L'outil '{tool.name}' existe déjà dans le système!"
                    }

        # Méthode 2: Par mots-clés dans la description
        # Mapper des mots-clés à des outils existants
        keyword_mappings = {
            "delete": ["delete_file"],
            "suppr": ["delete_file"],
            "efface": ["delete_file"],
            "remove": ["delete_file"],
            "create": ["create_file"],
            "crée": ["create_file"],
            "cree": ["create_file"],
            "créer": ["create_file"],
            "creer": ["create_file"],
            "read": ["read_file"],
            "lit": ["read_file"],
            "lire": ["read_file"],
            "append": ["append_to_file"],
            "ajoute": ["append_to_file"],
            "list": ["list_directory"],
            "liste": ["list_directory"],
            "exists": ["file_exists"],
            "existe": ["file_exists"],
            "weather": ["get_weather"],
            "météo": ["get_weather"],
            "meteo": ["get_weather"],
            "search": ["web_search"],
            "cherche": ["web_search"],
            "fetch": ["web_fetch"],
        }

        # Vérifier si la requête contient des mots-clés d'action sur fichiers
        request_lower = user_request.lower()

        for keyword, potential_tools in keyword_mappings.items():
            if keyword in request_lower:
                # Vérifier si l'outil correspondant existe
                for tool in available_tools:
                    if tool.name in potential_tools:
                        # Vérifier que c'est bien une demande de création d'outil
                        # (et pas juste utilisation de l'outil)
                        if any(p in request_lower for p in ["fichier", "file", "dossier", "directory"]):
                            return {
                                "type": "tool_already_exists",
                                "tool_name": tool.name,
                                "requested_variation": keyword,
                                "message": f"L'outil '{tool.name}' existe déjà dans le système!"
                            }

        return None

    def build_agent_prompt(
        self,
        tier: ModelTier,
        user_request: str,
        available_tools: List[StandardTool],
        contradiction: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Construit un prompt optimisé selon le tier

        Args:
            tier: Tier du modèle (nano/deepseek/claude)
            user_request: Requête utilisateur
            available_tools: Outils disponibles
            contradiction: Contradiction détectée (optionnelle)

        Returns:
            System prompt optimisé
        """
        # Générer la liste d'outils
        tools_list = self._format_tools_list(available_tools, tier)

        # Si contradiction détectée, créer un prompt spécial
        if contradiction:
            return self._build_contradiction_prompt(
                tier, user_request, available_tools, contradiction
            )

        # Sinon, prompt normal selon le tier
        if tier == ModelTier.NANO:
            return self._build_nano_prompt(tools_list)
        elif tier == ModelTier.DEEPSEEK:
            return self._build_deepseek_prompt(tools_list)
        else:  # Claude
            return self._build_claude_prompt(tools_list)

    def _format_tools_list(
        self,
        tools: List[StandardTool],
        tier: ModelTier
    ) -> str:
        """Formate la liste d'outils selon le tier"""
        if tier == ModelTier.NANO:
            # Court et simple pour nano
            return "\n".join([f"- {tool.name}" for tool in tools])
        elif tier == ModelTier.DEEPSEEK:
            # Avec descriptions courtes
            return "\n".join([
                f"- {tool.name}: {tool.description[:60]}..."
                if len(tool.description) > 60
                else f"- {tool.name}: {tool.description}"
                for tool in tools
            ])
        else:  # Claude
            # Complet avec catégories
            categories = {}
            for tool in tools:
                cat = tool.category or "general"
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(tool)

            result = []
            for cat, cat_tools in categories.items():
                result.append(f"\n{cat.upper()}:")
                for tool in cat_tools:
                    result.append(f"  - {tool.name}: {tool.description}")

            return "\n".join(result)

    def _build_nano_prompt(self, tools_list: str) -> str:
        """Prompt optimisé pour nano (court, direct)"""
        return f"""Agent with tools. Use them directly.

TOOLS:
{tools_list}

RULES:
1. Have tool? USE IT
2. No tool? Say "Tools Department will create it"
3. Response format:

🎯 Result: [1 sentence]
💭 Confidence: [HIGH/MEDIUM/LOW]
⚠️ Severity: [CRITICAL/HIGH/MEDIUM/LOW]
🔧 Actions: [Tools used]

Example:
🎯 Result: File created.
💭 Confidence: HIGH
⚠️ Severity: LOW
🔧 Actions: create_file()"""

    def _build_deepseek_prompt(self, tools_list: str) -> str:
        """Prompt optimisé pour deepseek (structuré, exemples)"""
        return f"""Tu es Cortex, un agent avec des outils.

OUTILS DISPONIBLES:
{tools_list}

RÈGLES:
1. Si l'outil existe: UTILISE-LE directement
2. Si l'outil n'existe pas: Informe que le Tools Department va le créer
3. Format de réponse obligatoire:

🎯 **Résultat:** [Réponse principale claire]

💭 **Confiance:** [HAUTE/MOYENNE/FAIBLE] - [Justification courte]

⚠️ **Gravité si erreur:** [CRITIQUE/HAUTE/MOYENNE/FAIBLE] - [Impact]

🔧 **Actions:** [Outils utilisés ou "Aucun outil disponible"]

EXEMPLES:

Requête: "Crée un fichier test.txt"
Réponse:
🎯 **Résultat:** Fichier test.txt créé avec succès.
💭 **Confiance:** HAUTE - Tool confirmé.
⚠️ **Gravité si erreur:** FAIBLE - Peut recréer facilement.
🔧 **Actions:** create_file(file_path="test.txt", content="")

Requête: "Quelle est la météo à Paris?"
Réponse:
🎯 **Résultat:** Tool météo non disponible. Demande au Tools Department.
💭 **Confiance:** MOYENNE - Tool manquant mais créable.
⚠️ **Gravité si erreur:** FAIBLE - Info non critique.
🔧 **Actions:** Aucun - Outil "get_weather" requis."""

    def _build_claude_prompt(self, tools_list: str) -> str:
        """Prompt optimisé pour claude (détaillé, raisonnement)"""
        return f"""Tu es Cortex, un agent intelligent équipé d'outils pour accomplir des tâches.

PHILOSOPHIE:
- Privilégier l'action directe avec les outils disponibles
- Être transparent sur les limitations
- Fournir des réponses structurées et informatives

OUTILS DISPONIBLES:
{tools_list}

PROCESSUS DE DÉCISION:
1. Analyse la requête utilisateur
2. Identifie les outils nécessaires
3. Si l'outil existe: exécute-le immédiatement
4. Si l'outil manque: explique clairement la situation et propose une solution

FORMAT DE RÉPONSE (OBLIGATOIRE):

🎯 **Résultat:** [Réponse principale détaillée en 1-3 phrases]

💭 **Confiance:** [HAUTE/MOYENNE/FAIBLE] - [Justification avec contexte]

⚠️ **Gravité si erreur:** [CRITIQUE/HAUTE/MOYENNE/FAIBLE] - [Analyse d'impact]

🔧 **Actions:** [Liste des outils utilisés avec paramètres, ou explication si aucun]

EXEMPLES DÉTAILLÉS:

Exemple 1 - Outil disponible:
Requête: "Crée un fichier config.json avec des paramètres par défaut"
Réponse:
🎯 **Résultat:** Fichier config.json créé avec succès contenant la configuration par défaut.
💭 **Confiance:** HAUTE - L'outil create_file est disponible et a été testé.
⚠️ **Gravité si erreur:** FAIBLE - Le fichier peut être recréé sans perte de données.
🔧 **Actions:** create_file(file_path="config.json", content='{{"version": "1.0"}}')

Exemple 2 - Outil manquant:
Requête: "Traduis ce texte en espagnol"
Réponse:
🎯 **Résultat:** Outil de traduction non disponible. Je vais demander au Tools Department de créer un outil "translate_text" avec support multi-langues.
💭 **Confiance:** MOYENNE - L'outil peut être créé facilement via une API de traduction.
⚠️ **Gravité si erreur:** FAIBLE - Tâche non critique, alternatives manuelles disponibles.
🔧 **Actions:** Aucun - Requête de création d'outil "translate_text(text, source_lang, target_lang)" envoyée au Tools Department."""

    def _build_contradiction_prompt(
        self,
        tier: ModelTier,
        user_request: str,
        available_tools: List[StandardTool],
        contradiction: Dict[str, Any]
    ) -> str:
        """
        Construit un prompt spécial quand une contradiction est détectée

        Args:
            tier: Tier du modèle
            user_request: Requête utilisateur
            available_tools: Outils disponibles
            contradiction: Info sur la contradiction

        Returns:
            Prompt qui informe de la contradiction
        """
        tool_name = contradiction["tool_name"]

        # Trouver l'outil en question
        tool = next((t for t in available_tools if t.name == tool_name), None)

        if not tool:
            return self.build_agent_prompt(tier, user_request, available_tools, None)

        # Prompt court pour nano, détaillé pour les autres
        if tier == ModelTier.NANO:
            return f"""CONTRADICTION DETECTED!

User requested to create tool "{tool_name}"
BUT this tool ALREADY EXISTS!

Tool: {tool_name}
Description: {tool.description}

Response format:
🎯 Result: Tool already exists!
💭 Confidence: HIGH
⚠️ Severity: LOW
🔧 Actions: None needed"""

        else:  # DeepSeek et Claude
            return f"""⚠️ CONTRADICTION DÉTECTÉE

La requête utilisateur demande de créer/implémenter l'outil "{tool_name}",
MAIS cet outil EXISTE DÉJÀ dans le système!

OUTIL EXISTANT:
  Nom: {tool_name}
  Description: {tool.description}
  Catégorie: {tool.category}
  Tags: {', '.join(tool.tags) if tool.tags else 'aucun'}

INSTRUCTION:
Réponds à l'utilisateur en l'informant que:
1. L'outil "{tool_name}" existe déjà
2. Il est pleinement fonctionnel
3. Propose de l'utiliser directement si la requête peut être reformulée

FORMAT DE RÉPONSE:

🎯 **Résultat:** L'outil "{tool_name}" existe déjà dans le système! Aucune implémentation nécessaire.

💭 **Confiance:** HAUTE - Outil vérifié et fonctionnel.

⚠️ **Gravité si erreur:** FAIBLE - Aucune erreur, juste une clarification.

🔧 **Actions:** Aucune - L'outil est déjà disponible pour utilisation.

SUGGESTION: Propose à l'utilisateur d'utiliser l'outil directement en reformulant sa requête."""


def create_prompt_engineer(llm_client: LLMClient) -> PromptEngineer:
    """Factory function to create a PromptEngineer"""
    return PromptEngineer(llm_client)
