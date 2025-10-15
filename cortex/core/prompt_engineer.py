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

    def is_general_conversation(self, user_request: str) -> bool:
        """
        Détecte si c'est une conversation générale (pas une tâche technique)

        Args:
            user_request: Requête utilisateur

        Returns:
            True si c'est une conversation générale
        """
        request_lower = user_request.lower()

        # Questions interrogatives (doivent commencer par ces patterns)
        question_starts = [
            "est-ce que", "est ce que", "sais-tu", "connais-tu", "penses-tu",
            "crois-tu", "pourquoi", "comment ça", "c'est quoi", "qu'est-ce",
            "savais-tu", "savais tu", "saviez-vous", "did you know",
            "do you know", "can you tell"
        ]

        # Salutations (peuvent être n'importe où)
        greetings = [
            "bonjour", "salut", "hello", "hi ", "bonsoir", "bonne nuit",
            "good morning", "good evening"
        ]

        # Opinions/discussions (patterns complets)
        opinion_patterns = [
            "selon toi", "à ton avis", "tu penses que", "tu crois que",
            "in your opinion", "what do you think"
        ]

        # Vérifier si commence par une question
        for pattern in question_starts:
            if request_lower.startswith(pattern):
                return True

        # Vérifier salutations et opinions
        for pattern in greetings + opinion_patterns:
            if pattern in request_lower:
                return True

        return False

    def detect_tool_creation_request(self, user_request: str) -> bool:
        """
        Détecte si la requête demande de CRÉER un outil
        (pas d'UTILISER un outil ou de converser)

        Args:
            user_request: Requête utilisateur

        Returns:
            True si c'est une demande de création d'outil
        """
        # Si c'est une conversation générale, pas une demande d'outil
        if self.is_general_conversation(user_request):
            return False

        create_patterns = [
            "implémente", "implemente", "crée", "cree", "ajoute", "créer", "creer",
            "implement", "create", "add", "make", "build", "develop", "code"
        ]

        tool_patterns = [
            "tool", "outil", "fonction", "function", "command", "commande", "feature"
        ]

        request_lower = user_request.lower()

        # Doit contenir à la fois un verbe de création ET un mot "tool"
        has_create = any(pattern in request_lower for pattern in create_patterns)
        has_tool = any(pattern in request_lower for pattern in tool_patterns)

        return has_create and has_tool

    def build_agent_prompt(
        self,
        tier: ModelTier,
        user_request: str,
        available_tools: List[StandardTool]
    ) -> str:
        """
        Construit un prompt optimisé selon le tier

        Args:
            tier: Tier du modèle (nano/deepseek/claude)
            user_request: Requête utilisateur
            available_tools: Outils disponibles

        Returns:
            System prompt optimisé
        """
        # Détecter le type de requête
        is_conversation = self.is_general_conversation(user_request)
        is_tool_creation = self.detect_tool_creation_request(user_request)

        # Si c'est une conversation générale, prompt simplifié
        if is_conversation:
            return self._build_conversation_prompt(tier)

        # Sinon, prompt avec outils
        tools_list = self._format_tools_list(available_tools, tier)

        # Prompt selon le tier
        if tier == ModelTier.NANO:
            return self._build_nano_prompt(tools_list, is_tool_creation)
        elif tier == ModelTier.DEEPSEEK:
            return self._build_deepseek_prompt(tools_list, is_tool_creation)
        else:  # Claude
            return self._build_claude_prompt(tools_list, is_tool_creation)

    def _build_conversation_prompt(self, tier: ModelTier) -> str:
        """
        Prompt simplifié pour les conversations générales
        (pas besoin de la liste d'outils)

        Args:
            tier: Tier du modèle

        Returns:
            Prompt de conversation
        """
        if tier == ModelTier.NANO:
            return """You are Cortex, a helpful AI assistant.

Respond naturally to the user's question.
Be friendly, concise, and informative.

Format:
🎯 Result: [Your answer]
💭 Confidence: [HIGH/MEDIUM/LOW]
⚠️ Severity: LOW
🔧 Actions: None - General conversation"""

        elif tier == ModelTier.DEEPSEEK:
            return """Tu es Cortex, un assistant IA conversationnel.

Réponds naturellement à la question de l'utilisateur.
Sois amical, concis et informatif.

Format:
🎯 **Résultat:** [Ta réponse]
💭 **Confiance:** [HAUTE/MOYENNE/FAIBLE]
⚠️ **Gravité:** FAIBLE
🔧 **Actions:** Aucune - Conversation générale"""

        else:  # Claude
            return """Tu es Cortex, un assistant IA conversationnel intelligent.

Réponds naturellement à la question de l'utilisateur avec:
- Ton amical et engageant
- Précision dans les faits
- Clarté dans l'explication

Format:
🎯 **Résultat:** [Ta réponse détaillée]
💭 **Confiance:** [HAUTE/MOYENNE/FAIBLE] - [Justification]
⚠️ **Gravité:** FAIBLE - Conversation informelle
🔧 **Actions:** Aucune - Conversation générale"""

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

    def _build_nano_prompt(self, tools_list: str, is_tool_creation: bool) -> str:
        """Prompt optimisé pour nano (court, direct)"""

        base_prompt = f"""Agent with tools. Use them directly.

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

        # Si c'est une demande de création d'outil, ajouter l'instruction de vérification
        if is_tool_creation:
            base_prompt += """

⚠️ IMPORTANT: User asks to CREATE a tool.
CHECK if tool already exists in list above!
If exists: Say "Tool [name] already exists"
If not: Say "Will request Tools Department" """

        return base_prompt

    def _build_deepseek_prompt(self, tools_list: str, is_tool_creation: bool) -> str:
        """Prompt optimisé pour deepseek (structuré, exemples)"""

        base_prompt = f"""Tu es Cortex, un agent avec des outils.

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

        # Instruction spéciale si demande de création d'outil
        if is_tool_creation:
            base_prompt += """

⚠️ ATTENTION: L'utilisateur demande de CRÉER un outil.

VÉRIFIE D'ABORD dans la liste d'outils ci-dessus si un outil similaire existe déjà!

Si un outil existe qui fait la même chose:
🎯 **Résultat:** L'outil [nom] existe déjà et fait cette action!
💭 **Confiance:** HAUTE - Outil vérifié dans la liste.
⚠️ **Gravité si erreur:** FAIBLE - Aucune erreur, juste une clarification.
🔧 **Actions:** Aucune - L'outil est disponible.

Si aucun outil similaire n'existe:
🎯 **Résultat:** Outil non disponible. Je demande au Tools Department de le créer.
💭 **Confiance:** MOYENNE - Tool peut être créé.
⚠️ **Gravité si erreur:** FAIBLE - Demande de création.
🔧 **Actions:** Demande de création d'outil au Tools Department."""

        return base_prompt

    def _build_claude_prompt(self, tools_list: str, is_tool_creation: bool) -> str:
        """Prompt optimisé pour claude (détaillé, raisonnement)"""

        base_prompt = f"""Tu es Cortex, un agent intelligent équipé d'outils pour accomplir des tâches.

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

        # Instruction spéciale si demande de création d'outil
        if is_tool_creation:
            base_prompt += """

⚠️ ATTENTION CRITIQUE: L'utilisateur demande de CRÉER ou IMPLÉMENTER un outil.

AVANT DE RÉPONDRE, tu DOIS:
1. Examiner attentivement la liste complète des outils disponibles ci-dessus
2. Analyser sémantiquement si un outil existant fait déjà cette action
3. Comparer la fonctionnalité demandée avec les descriptions des outils

IMPORTANT: Ne te base PAS sur les noms d'outils uniquement!
Analyse les DESCRIPTIONS pour détecter les fonctionnalités similaires.

Exemples:
- "Implémente un outil pour effacer des fichiers" → delete_file EXISTE
- "Crée une fonction pour lire des fichiers" → read_file EXISTE
- "Ajoute un tool pour la météo" → get_weather EXISTE (si présent)

Si un outil similaire existe:
🎯 **Résultat:** L'outil [nom] existe déjà dans le système! Il permet de [description courte]. Aucune implémentation nécessaire.
💭 **Confiance:** HAUTE - Outil vérifié dans la liste des outils disponibles.
⚠️ **Gravité si erreur:** FAIBLE - Aucune erreur, simple clarification sur l'existence de l'outil.
🔧 **Actions:** Aucune - L'outil [nom] est déjà disponible et fonctionnel.

Si AUCUN outil similaire n'existe:
🎯 **Résultat:** Aucun outil ne correspond à cette fonctionnalité. Je demande au Tools Department de créer un nouvel outil "[nom_suggéré]".
💭 **Confiance:** MOYENNE - Le Tools Department peut créer l'outil.
⚠️ **Gravité si erreur:** FAIBLE - Demande de création d'outil.
🔧 **Actions:** Demande de création envoyée au Tools Department avec spécifications."""

        return base_prompt


def create_prompt_engineer(llm_client: LLMClient) -> PromptEngineer:
    """Factory function to create a PromptEngineer"""
    return PromptEngineer(llm_client)
