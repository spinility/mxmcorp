# Analyse Stratégique: Context du Projet vs Chat History

## Question
**Est-ce moins cher de maintenir un context lightweight du projet entier et balancer avec base_instruction pour éviter:**
1. Lecture constante des fichiers
2. Pousser toute l'historique de chat (qui grossit)
3. Permettre des appels API isolés (1 prompt = 1 réponse)

## TL;DR: Réponse

**OUI, c'est une EXCELLENTE idée, MAIS avec nuances importantes**

✅ **Recommandation**: Hybrid approach
- Context lightweight du projet (500-1000 tokens)
- Historique de chat MINIMAL (3-5 derniers messages pertinents)
- Appels isolés pour 80% des tâches
- Conversation continue seulement pour tâches complexes multi-étapes

---

## Analyse Détaillée

### Scénario Actuel (Chat History)

```
Appel API #1:
[System] Base prompt (200 tokens)
[User] Message 1 (50 tokens)
[Assistant] Response 1 (100 tokens)
[User] Message 2 (50 tokens)
[Assistant] Response 2 (100 tokens)
[User] Message 3 (50 tokens)
─────────────────────────────
Total input: 550 tokens

Appel API #2:
[System] Base prompt (200 tokens)
[User] Message 1 (50 tokens)
[Assistant] Response 1 (100 tokens)
[User] Message 2 (50 tokens)
[Assistant] Response 2 (100 tokens)
[User] Message 3 (50 tokens)
[Assistant] Response 3 (100 tokens)
[User] Message 4 (50 tokens)  ← nouveau
─────────────────────────────
Total input: 700 tokens (+150)

Appel API #10:
Total input: ~2000+ tokens
```

**Problèmes**:
- ❌ Croissance linéaire des tokens
- ❌ 90% du chat history est inutile pour la tâche actuelle
- ❌ Coût croissant à chaque itération
- ❌ Risque d'atteindre la limite de context

### Scénario Proposé (Project Context + Isolated Calls)

```
Appel API (n'importe lequel):
[System] Base prompt (200 tokens)
[Project Context] Lightweight (500 tokens)
  - Structure du projet
  - Fichiers clés et leurs rôles
  - Conventions de code
  - État actuel du système
[Task] Current task only (100 tokens)
─────────────────────────────
Total input: 800 tokens (constant!)

Appel API suivant:
[System] Base prompt (200 tokens)
[Project Context] Updated (500 tokens)
[Task] New task (100 tokens)
─────────────────────────────
Total input: 800 tokens (toujours!)
```

**Avantages**:
- ✅ Coût constant (pas de croissance)
- ✅ Context pertinent pour la tâche
- ✅ Pas de limite atteinte
- ✅ Chaque appel est indépendant

---

## Comparaison Mathématique

### Hypothèse: 50 appels API dans une session

#### MÉTHODE ACTUELLE (Chat History)

```
Croissance moyenne: +100 tokens par appel

Appel 1:  500 tokens input
Appel 2:  600 tokens input
Appel 3:  700 tokens input
...
Appel 50: 5400 tokens input

Total tokens: 500 + 600 + 700 + ... + 5400
            = 147,500 tokens input

Coût (nano):     $0.05/1M × 147,500 = $0.007375
Coût (deepseek): $0.28/1M × 147,500 = $0.041300
Coût (claude):   $3.00/1M × 147,500 = $0.442500
```

#### MÉTHODE PROPOSÉE (Project Context)

```
Coût constant: 800 tokens par appel

Appel 1:  800 tokens input
Appel 2:  800 tokens input
Appel 3:  800 tokens input
...
Appel 50: 800 tokens input

Total tokens: 800 × 50 = 40,000 tokens input

Coût (nano):     $0.05/1M × 40,000 = $0.002000
Coût (deepseek): $0.28/1M × 40,000 = $0.011200
Coût (claude):   $3.00/1M × 40,000 = $0.120000
```

#### ÉCONOMIES

| Modèle | Chat History | Project Context | Économie |
|--------|-------------|-----------------|----------|
| nano | $0.007375 | $0.002000 | **73% cheaper** |
| deepseek | $0.041300 | $0.011200 | **73% cheaper** |
| claude | $0.442500 | $0.120000 | **73% cheaper** |

**Sur 50 appels, économie de 73% en tokens input!**

---

## Avantages du Project Context

### 1. Coût Prévisible et Constant
```
Chat History: O(n) - croissance linéaire
Project Context: O(1) - coût constant
```

**Impact sur 1000 appels**:
- Chat History: ~$0.15 (nano) → $1.50 (deepseek) → $15 (claude)
- Project Context: ~$0.04 (nano) → $0.22 (deepseek) → $2.40 (claude)

### 2. Pas de Limite de Context
- Chat history peut atteindre 200K tokens (claude)
- Project context reste à 800 tokens
- Pas de truncation nécessaire

### 3. Context Pertinent
```
Chat History:
  "Create user model" (5 messages ago)
  "Add validation" (4 messages ago)
  "Fix typo" (3 messages ago)
  "Update tests" (2 messages ago)
  "Deploy to staging" (1 message ago)
  CURRENT: "What's the database schema?"

  → 80% du chat history est INUTILE pour la tâche actuelle
```

```
Project Context:
  Project structure
  Database schema location
  Current system state

  → 100% du context est PERTINENT
```

### 4. Parallélisation Possible
Avec chat history:
```
Task A → depends on Task A history
Task B → depends on Task B history
Cannot run in parallel
```

Avec project context:
```
Task A → uses project context
Task B → uses project context
CAN run in parallel!
```

### 5. Debugging Plus Facile
```
Chat History:
  Need to replay entire conversation to understand

Project Context:
  Each call is self-contained
  Easy to reproduce issues
```

---

## Inconvénients du Project Context

### 1. Perte de Continuité (Résolu)

**Problème**: Agent ne se souvient pas des décisions précédentes

**Solutions**:
```python
# Option A: Memory système (lightweight)
project_context["recent_decisions"] = [
    "User preferred async over sync",
    "Using PostgreSQL not MySQL",
    "Test coverage must be > 80%"
]

# Option B: Mention explicite dans le task
task = "Continue the user authentication system we started. Use JWT tokens as decided."
```

### 2. Overhead de Construction du Context (Négligeable)

**Problème**: Il faut construire le context à chaque appel

**Coût réel**:
```python
# Construction du context: ~10ms
# I/O pour lire project structure: ~5ms
# Total overhead: ~15ms

vs

# Coût d'envoyer 5000 extra tokens: ~500ms
# ÉCONOMIE: 485ms par appel
```

### 3. Context Peut Devenir Obsolète (Gérable)

**Problème**: Si projet change, context doit être mis à jour

**Solution**:
```python
# Update triggers:
- File system watch (automatic)
- After each significant change (automatic)
- Manual refresh command (rare)

# Cost of update: ~$0.000001 (négligeable)
```

### 4. Taille Fixe Peut Être Limitante (Hybride)

**Problème**: 500-1000 tokens peuvent ne pas suffire pour gros projets

**Solution hybride**:
```python
# Base context (500 tokens): Toujours inclus
- Project structure
- Main files
- Current state

# Task-specific context (300 tokens): Dynamique
- Files relevant to current task
- Related functions/classes
- Recent changes to these files

Total: 800 tokens (optimisé pour la tâche)
```

---

## Stratégie Optimale: Hybrid Approach

### Architecture Recommandée

```python
class ContextStrategy:
    def build_context_for_task(self, task: str) -> str:
        """
        Construit un context optimal pour la tâche

        Total budget: 1000 tokens max
        """
        context_parts = []

        # 1. BASE CONTEXT (300 tokens) - Toujours inclus
        context_parts.append(self._get_base_context())
        # - Project name and purpose
        # - Main directory structure
        # - Tech stack
        # - Coding conventions

        # 2. TASK-RELEVANT CONTEXT (500 tokens) - Dynamique
        context_parts.append(self._get_task_context(task))
        # - Files mentioned in task
        # - Related files (imports, dependencies)
        # - Recent changes to these files

        # 3. RECENT DECISIONS (100 tokens) - Mini-memory
        context_parts.append(self._get_recent_decisions(limit=3))
        # - Last 3 important decisions
        # - Current priorities
        # - Known issues

        # 4. SYSTEM STATE (100 tokens) - Current state
        context_parts.append(self._get_system_state())
        # - Health score
        # - Active agents
        # - Current mode (normal/cost-saving/etc)

        return "\n\n".join(context_parts)
```

### Exemple Concret

```
Tâche: "Add validation to the User model"

BASE CONTEXT (300 tokens):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROJECT: MXMCorp Cortex
TYPE: AI Agent System
STACK: Python, FastAPI, PostgreSQL

STRUCTURE:
cortex/
  agents/      → Agent implementations
  core/        → Core systems
  models/      → Data models
  tools/       → Tool implementations

CONVENTIONS:
- Type hints required
- Docstrings for all public methods
- Tests in tests/ directory

TASK-RELEVANT CONTEXT (500 tokens):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILE: cortex/models/user.py
class User(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

RELATED:
- cortex/core/validation.py (validation utilities)
- cortex/models/base.py (BaseModel with common validators)

RECENT CHANGES:
- Added email field (2 hours ago)
- Changed id to UUID (1 day ago)

RECENT DECISIONS (100 tokens):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Use Pydantic for validation (not custom)
2. Email validation must check format + domain
3. All models must have created_at/updated_at

SYSTEM STATE (100 tokens):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Health: 87/100
Mode: normal
Priority: Maintain test coverage > 80%
```

**Total: 1000 tokens - Tout le context nécessaire, rien de superflu**

---

## Quand Utiliser Quelle Méthode?

### Project Context (80% des cas)
✅ **À utiliser pour**:
- Tâches indépendantes
- Bugs fixes
- Feature additions
- Refactoring
- Documentation
- Tests

**Pourquoi**: Chaque tâche est self-contained

### Chat History (20% des cas)
✅ **À utiliser pour**:
- Discussions exploratoires longues
- Architecture decisions multi-étapes
- Debugging complexe avec back-and-forth
- Pair programming sessions

**Pourquoi**: Besoin de continuité de la conversation

### Hybrid (Optimal)
✅ **Meilleure approche**:
```python
if task.is_simple():
    use_project_context()
elif task.requires_continuity():
    use_minimal_chat_history(last_3_messages) + project_context()
else:
    use_task_specific_context()
```

---

## Implémentation Proposée

### Structure du Project Context

```json
{
  "base": {
    "project_name": "MXMCorp Cortex",
    "description": "AI agent system for task automation",
    "tech_stack": ["Python 3.10+", "FastAPI", "PostgreSQL"],
    "structure": {
      "cortex/agents/": "Agent implementations",
      "cortex/core/": "Core systems (LLM, routing, etc)",
      "cortex/tools/": "Reusable tools",
      "cortex/models/": "Data models"
    },
    "conventions": {
      "typing": "Type hints required",
      "docs": "Docstrings for public methods",
      "tests": "In tests/ directory",
      "style": "Black formatter, line length 100"
    }
  },
  "current_state": {
    "health_score": 87,
    "active_agents": 8,
    "total_tasks_today": 156,
    "mode": "normal"
  },
  "recent_decisions": [
    "Use Pydantic for validation",
    "Prefer nano model for simple tasks",
    "All agents must report terminal updates"
  ],
  "key_files": {
    "cortex/agents/base_agent.py": "Base class for all agents",
    "cortex/core/llm_client.py": "LLM interaction layer",
    "cortex/tools/tool_registry.py": "Available tools catalog"
  }
}
```

**Compact form: ~600 tokens**

### Génération Dynamique

```python
class ProjectContextBuilder:
    def build(self, task: str) -> str:
        """Construit un context optimisé pour la tâche"""

        # Parse task pour identifier fichiers pertinents
        relevant_files = self._extract_relevant_files(task)

        # Construire context
        context = {
            "base": self._get_base_context(),
            "task_context": self._get_file_contexts(relevant_files),
            "recent": self._get_recent_decisions(3),
            "state": self._get_system_state()
        }

        # Convertir en format compact
        return self._to_compact_format(context)

    def _extract_relevant_files(self, task: str) -> List[str]:
        """Identifie les fichiers pertinents depuis la tâche"""
        # "Add validation to User model"
        # → ["cortex/models/user.py", "cortex/core/validation.py"]

        keywords = extract_keywords(task)
        files = []

        # Chercher dans l'index de fichiers
        for keyword in keywords:
            files.extend(self.file_index.search(keyword))

        return files[:5]  # Max 5 fichiers les plus pertinents
```

---

## ROI Analysis

### Scénario Réaliste: 1000 tâches/mois

#### Chat History Approach
```
Tokens moyens par appel: ~2000 (avec historique)
Total: 2,000,000 tokens/mois

Coût:
- nano:     $0.10/mois
- deepseek: $0.56/mois
- claude:   $6.00/mois

Avec mix (70% nano, 25% deepseek, 5% claude):
= $0.07 + $0.14 + $0.30 = $0.51/mois
```

#### Project Context Approach
```
Tokens par appel: ~800 (context constant)
Total: 800,000 tokens/mois

Coût:
- nano:     $0.04/mois
- deepseek: $0.22/mois
- claude:   $2.40/mois

Avec mix (70% nano, 25% deepseek, 5% claude):
= $0.028 + $0.055 + $0.120 = $0.203/mois
```

**Économie: $0.31/mois (60% moins cher)**

Sur un an: **$3.72 économisés**

---

## Recommandations Finales

### ✅ À IMPLÉMENTER

1. **Project Context Système**
   - Base context (300 tokens): structure, conventions, tech stack
   - Task context (500 tokens): fichiers pertinents dynamiquement
   - Recent decisions (100 tokens): 3 dernières décisions importantes
   - System state (100 tokens): état actuel

2. **Stratégie Hybride Intelligente**
   ```python
   if task.is_independent():
       use_project_context_only()  # 80% des cas
   elif task.needs_continuity():
       use_project_context() + minimal_history(3)  # 15% des cas
   else:
       use_full_chat_history()  # 5% des cas (debugging complexe)
   ```

3. **Context Caching**
   - Base context cached (change rarement)
   - Task context generated dynamically
   - Cost: première génération, puis cache gratuit

4. **Monitoring**
   - Track tokens saved vs chat history
   - Measure quality (success rate avec vs sans historique)
   - Adjust strategy based on metrics

### ❌ À ÉVITER

1. **NE PAS** abandonner complètement chat history
   - Certaines tâches en ont besoin
   - Stratégie hybride est optimale

2. **NE PAS** faire le context trop gros
   - 1000 tokens max
   - Focus sur l'essentiel

3. **NE PAS** inclure du code complet
   - Juste structure et références
   - Agent lit le fichier si besoin

---

## Conclusion

### Verdict: ✅ EXCELLENTE IDÉE avec nuances

**Pourquoi c'est bon**:
- 💰 60-73% moins cher
- ⚡ Coût constant (pas de croissance)
- 🎯 Context pertinent pour chaque tâche
- 🔄 Permet parallélisation
- 🐛 Debugging plus facile

**Nuances importantes**:
- 🔀 Stratégie hybride (pas 100% project context)
- 📝 Besoin de mini-memory pour décisions récentes
- 🎨 Context dynamique basé sur la tâche
- 🔍 20% des tâches bénéficient encore du chat history

### Implémentation

**Phase 1**: Project context de base (cette semaine)
**Phase 2**: Génération dynamique task-specific (semaine prochaine)
**Phase 3**: Stratégie hybride intelligente (dans 2 semaines)

**Le système devient 60% moins cher ET plus efficient.**
