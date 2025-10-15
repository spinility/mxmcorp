# PromptEngineer - Système Intelligent de Génération de Prompts

## 🎯 Problème Résolu

Quand tu as testé Cortex avec la requête **"Implémente l'outil pour effacer des fichiers"**, nano a retourné une réponse vide au lieu de détecter que `delete_file` existait déjà.

Le problème était double:
1. **Pas de détection de contradiction** - Le système ne vérifiait pas si l'outil demandé existait déjà
2. **Prompt générique** - Le même prompt était utilisé pour nano, deepseek et claude, alors que nano a besoin d'un prompt court et direct

## 🚀 Solution: PromptEngineer

J'ai créé un système intelligent qui:

### 1. Détecte les Contradictions

Le `PromptEngineer` analyse chaque requête **avant** d'appeler le LLM pour détecter:

```python
# Exemple de détection
requête = "Implémente l'outil pour effacer des fichiers"
contradiction = prompt_engineer.detect_contradiction(requête, available_tools)

# Résultat:
{
    "type": "tool_already_exists",
    "tool_name": "delete_file",
    "message": "L'outil 'delete_file' existe déjà dans le système!"
}
```

**Méthodes de détection:**

**Méthode 1: Par nom d'outil**
- Cherche "delete_file", "delete file", "deletefile" dans la requête
- Variations avec underscores, espaces, tirets

**Méthode 2: Par mots-clés sémantiques**
- "efface" → `delete_file`
- "crée" → `create_file`
- "lit" → `read_file`
- "météo" → `get_weather`
- etc.

Support bilingue (français/anglais)!

### 2. Génère des Prompts Optimisés par Tier

Chaque modèle reçoit un prompt adapté à ses capacités:

#### NANO (gpt-3.5-turbo) - 446 caractères
```
Agent with tools. Use them directly.

TOOLS:
- create_file
- read_file
- delete_file
...

RULES:
1. Have tool? USE IT
2. No tool? Say "Tools Department will create it"
3. Response format:

🎯 Result: [1 sentence]
💭 Confidence: [HIGH/MEDIUM/LOW]
⚠️ Severity: [CRITICAL/HIGH/MEDIUM/LOW]
🔧 Actions: [Tools used]
```

**Pourquoi court?** Nano a une capacité limitée - il faut être direct et concis.

#### DEEPSEEK - 1,376 caractères
```
Tu es Cortex, un agent avec des outils.

OUTILS DISPONIBLES:
- create_file: Create a new file with the given content...
- read_file: Read the content of a file
...

RÈGLES:
1. Si l'outil existe: UTILISE-LE directement
2. Si l'outil n'existe pas: Informe que le Tools Department va le créer
3. Format de réponse obligatoire:

🎯 **Résultat:** [Réponse claire]
💭 **Confiance:** [HAUTE/MOYENNE/FAIBLE] - [Justification]
⚠️ **Gravité:** [CRITIQUE/HAUTE/MOYENNE/FAIBLE] - [Impact]
🔧 **Actions:** [Outils utilisés]

EXEMPLES:

Requête: "Crée un fichier test.txt"
Réponse:
🎯 **Résultat:** Fichier créé.
💭 **Confiance:** HAUTE - Tool confirmé.
...
```

**Pourquoi structuré?** DeepSeek bénéficie d'exemples concrets.

#### CLAUDE - 2,249 caractères
```
Tu es Cortex, un agent intelligent équipé d'outils pour accomplir des tâches.

PHILOSOPHIE:
- Privilégier l'action directe avec les outils disponibles
- Être transparent sur les limitations
- Fournir des réponses structurées et informatives

OUTILS DISPONIBLES:

FILESYSTEM:
  - create_file: Create a new file with the given content...
  - read_file: Read the content of a file
  - delete_file: Delete a file or directory...

WEB & REAL-TIME:
  - get_weather: Get current weather information...
  - web_search: Search the web using DuckDuckGo...
  - web_fetch: Fetch content from a URL...

PROCESSUS DE DÉCISION:
1. Analyse la requête utilisateur
2. Identifie les outils nécessaires
3. Si l'outil existe: exécute-le immédiatement
4. Si l'outil manque: explique la situation et propose une solution

FORMAT DE RÉPONSE (OBLIGATOIRE):

🎯 **Résultat:** [Réponse détaillée en 1-3 phrases]
💭 **Confiance:** [HAUTE/MOYENNE/FAIBLE] - [Justification avec contexte]
⚠️ **Gravité:** [CRITIQUE/HAUTE/MOYENNE/FAIBLE] - [Analyse d'impact]
🔧 **Actions:** [Liste détaillée des outils utilisés avec paramètres]

EXEMPLES DÉTAILLÉS:
...
```

**Pourquoi détaillé?** Claude peut gérer des prompts complexes avec philosophie et raisonnement.

### 3. Prompts Spéciaux pour les Contradictions

Quand une contradiction est détectée, le LLM reçoit un **prompt spécial** qui l'informe:

#### Pour NANO:
```
CONTRADICTION DETECTED!

User requested to create tool "delete_file"
BUT this tool ALREADY EXISTS!

Tool: delete_file
Description: Delete a file or directory. Be careful, this action is irreversible!

Response format:
🎯 Result: Tool already exists!
💭 Confidence: HIGH
⚠️ Severity: LOW
🔧 Actions: None needed
```

#### Pour DeepSeek/Claude:
```
⚠️ CONTRADICTION DÉTECTÉE

La requête utilisateur demande de créer/implémenter l'outil "delete_file",
MAIS cet outil EXISTE DÉJÀ dans le système!

OUTIL EXISTANT:
  Nom: delete_file
  Description: Delete a file or directory. Be careful, this action is irreversible!
  Catégorie: filesystem
  Tags: file, delete, remove

INSTRUCTION:
Réponds à l'utilisateur en l'informant que:
1. L'outil "delete_file" existe déjà
2. Il est pleinement fonctionnel
3. Propose de l'utiliser directement si la requête peut être reformulée

FORMAT DE RÉPONSE:

🎯 **Résultat:** L'outil "delete_file" existe déjà dans le système!
                Aucune implémentation nécessaire.

💭 **Confiance:** HAUTE - Outil vérifié et fonctionnel.

⚠️ **Gravité si erreur:** FAIBLE - Aucune erreur, juste une clarification.

🔧 **Actions:** Aucune - L'outil est déjà disponible pour utilisation.

SUGGESTION: Propose à l'utilisateur d'utiliser l'outil directement.
```

## 🔄 Flux dans Cortex CLI

```
User: "Implémente l'outil pour effacer des fichiers"
  ↓
1. Model Selection
   → nano sélectionné (tâche simple)
  ↓
2. Contradiction Detection
   → ⚠️ Contradiction détectée: delete_file existe déjà!
  ↓
3. Prompt Generation
   → Prompt de contradiction pour nano généré
  ↓
4. LLM Execution
   → nano reçoit le prompt optimisé
   → nano répond: "L'outil delete_file existe déjà!"
  ↓
5. Response Display
   → Réponse colorisée affichée à l'utilisateur
```

## 📊 Tests et Validation

J'ai créé `test_prompt_engineer.py` qui valide:

✅ **Détection de contradictions**
- ✓ Détecte "Implémente l'outil pour effacer des fichiers" → delete_file
- ✓ Détecte "Crée un tool pour créer des fichiers" → create_file
- ✓ Pas de faux positif sur "Crée un fichier test.txt"
- ✓ Pas de faux positif sur "Implémente un tool pour traduire" (n'existe pas)

✅ **Génération de prompts par tier**
- ✓ Nano: 446 chars (court)
- ✓ DeepSeek: 1,376 chars (structuré)
- ✓ Claude: 2,249 chars (détaillé)

✅ **Prompts de contradiction**
- ✓ Prompt NANO informatif
- ✓ Prompt DeepSeek/Claude détaillé avec suggestions

## 💡 Concept Clé: Prompt Engineering par Tier

**Ta remarque était excellente:**
> "N'oublie pas que le prompt de nano input peut être énorme 2000-5000.
> Ça ne veut pas dire de mettre du superflu, au contraire, les prompts
> doivent être fait par le modèle GPT-5 et il doit savoir pour quel
> modèle est destiné son prompt de base."

C'est exactement ce que fait le PromptEngineer:

1. **Nano (2000-5000 tokens input max)**
   - Prompt: 446 chars (~110 tokens)
   - Laisse ~1900 tokens pour le contexte et les outils
   - Direct et actionnable

2. **DeepSeek (8000 tokens input)**
   - Prompt: 1,376 chars (~344 tokens)
   - Assez d'espace pour exemples et structure
   - Bénéficie d'exemples concrets

3. **Claude (200,000 tokens input)**
   - Prompt: 2,249 chars (~562 tokens)
   - Peut se permettre philosophie et détails
   - Raisonnement approfondi

## 🎨 Architecture

```
cortex/core/prompt_engineer.py
├── PromptEngineer
│   ├── detect_contradiction()      # Détecte les contradictions
│   ├── build_agent_prompt()        # Génère prompt selon tier
│   ├── _format_tools_list()        # Formate liste d'outils
│   ├── _build_nano_prompt()        # Prompt court pour nano
│   ├── _build_deepseek_prompt()    # Prompt structuré
│   ├── _build_claude_prompt()      # Prompt détaillé
│   └── _build_contradiction_prompt() # Prompt spécial contradiction
```

## 🚀 Usage

Le PromptEngineer est automatiquement intégré dans `cortex_cli.py`:

```python
# Initialisation
self.prompt_engineer = PromptEngineer(self.llm_client)

# Dans cmd_task():
# 1. Détection de contradiction
contradiction = self.prompt_engineer.detect_contradiction(
    description,
    self.available_tools
)

# 2. Génération du prompt optimisé
system_prompt = self.prompt_engineer.build_agent_prompt(
    tier=selection.tier,
    user_request=description,
    available_tools=self.available_tools,
    contradiction=contradiction
)

# 3. Exécution avec le prompt optimisé
response = self.tool_executor.execute_with_tools(
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": description}
    ],
    tier=selection.tier,
    tools=self.available_tools
)
```

## 📝 Résumé

Le **PromptEngineer** résout deux problèmes critiques:

1. **Détection de contradictions** - Empêche les réponses vides en détectant les outils existants
2. **Prompts optimisés par tier** - Chaque modèle reçoit un prompt adapté à ses capacités

Résultat: Cortex peut maintenant gérer intelligemment les requêtes contradictoires et générer des réponses appropriées selon le modèle utilisé!

---

**Commit:** `61c77fa` - feat: Add intelligent PromptEngineer with contradiction detection
