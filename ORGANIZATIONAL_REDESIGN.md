# Cortex Organizational Redesign

## Problèmes Identifiés

### ❌ Confusion Hiérarchie vs Spécialisation

**Actuel:** DeveloperAgentExpert, DeveloperAgentDirecteur, DeveloperAgentCortex
- "Developer" est une **spécialisation**, pas un niveau hiérarchique
- EXPERT/DIRECTEUR/CORTEX sont des **niveaux de pouvoir décisionnel**

**Exemple réel d'entreprise:**
- ❌ "DeveloperDirecteur" n'existe pas
- ✅ "Directeur du département de développement" existe
- ✅ "Expert en optimisation" existe

## Nouveau Modèle Organisationnel

### 1. Hiérarchie (4 niveaux de pouvoir)

```
CORTEX CENTRAL (Vision stratégique, coordination système)
    ↑
DIRECTEUR (Décisions départementales, architecture)
    ↑
EXPERT (Analyse approfondie, solutions complexes)
    ↑
EXÉCUTANT (Exécution, validation, tâches simples)
```

**Note importante:** "AGENT" → "EXÉCUTANT" (plus clair)

### 2. Départements (Spécialisations)

```
📁 Département de DÉVELOPPEMENT
   - Exécutants: TesterAgent, CodeWriterAgent
   - Experts: CodeAnalystAgent, RefactoringAgent
   - Directeur: ArchitectAgent
   - Partage: Standards de code, patterns, best practices

📁 Département d'OPTIMISATION
   - Exécutants: GitDiffAnalyzer
   - Experts: RelationshipMapper, SiteplanUpdater
   - Directeur: OptimizationDirector
   - Partage: Graphe des dépendances, métriques de performance

📁 Département d'OUTILLAGE
   - Exécutants: BashToolCreator
   - Experts: ToolOptimizer
   - Directeur: ToolingDirector
   - Partage: Bibliothèque d'outils, scripts réutilisables

📁 Département de CONTEXTE
   - Exécutants: ContextAgent
   - Experts: ContextOptimizer
   - Partage: Cache de contexte, embeddings

📁 Département de PLANIFICATION
   - Experts: PlannerAgent
   - Directeur: StrategyAgent
   - Partage: Templates de plans, estimations
```

### 3. Workflows (Processus métier)

Un workflow est déclenché par **détection de type de requête**:

#### Workflow: CODE_DEVELOPMENT

```
1. [DÉTECTION] RequestClassifier → "C'est une requête de code"
2. [CONTEXTE] ContextAgent (Exécutant) → Prépare contexte
3. [PLANIFICATION] PlannerAgent (Expert) → Décompose si nécessaire
4. [DÉVELOPPEMENT]
   - Simple → CodeWriterAgent (Exécutant)
   - Complexe → CodeAnalystAgent (Expert)
   - Architecture → ArchitectAgent (Directeur)
5. [VALIDATION] TesterAgent (Exécutant) → Valide le code
6. [OPTIMISATION - AUTO-FLAGGED] OptimizationDepartment → Analyse post-modif
```

#### Workflow: TOOL_CREATION

```
1. [DÉTECTION] RequestClassifier → "Besoin d'un outil"
2. [CRÉATION] BashToolCreator (Exécutant) → Crée script bash
3. [OPTIMISATION - OBLIGATOIRE] ToolOptimizer (Expert) → Améliore l'outil
4. [ENREGISTREMENT] ToolRegistry → Sauvegarde dans bibliothèque
```

#### Workflow: OPTIMIZATION (Auto-déclenché)

```
TRIGGER: Après toute modification de code
1. [GIT DIFF] GitDiffAnalyzer (Exécutant) → Parse git diff
2. [RELATIONS] RelationshipMapper (Expert) → Met à jour graphe dépendances
3. [SITE PLAN] SiteplanUpdater (Expert) → Met à jour plan du projet
4. [RAPPORT] OptimizationReport → Suggère améliorations
```

## Architecture Technique

### Structure de fichiers proposée

```
cortex/
├── core/
│   ├── agent_hierarchy.py          # Niveaux: EXÉCUTANT → EXPERT → DIRECTEUR → CORTEX
│   ├── department_system.py        # NEW: Système de départements
│   ├── workflow_engine.py          # NEW: Moteur de workflows
│   └── request_classifier.py       # NEW: Détection de type de requête
│
├── departments/
│   ├── development/
│   │   ├── __init__.py
│   │   ├── knowledge_base.py       # Partage département
│   │   ├── code_writer_agent.py    # Exécutant
│   │   ├── code_analyst_agent.py   # Expert
│   │   └── architect_agent.py      # Directeur
│   │
│   ├── optimization/
│   │   ├── __init__.py
│   │   ├── knowledge_base.py
│   │   ├── git_diff_analyzer.py    # Exécutant
│   │   ├── relationship_mapper.py  # Expert
│   │   └── siteplan_updater.py     # Expert
│   │
│   ├── tooling/
│   │   ├── __init__.py
│   │   ├── tool_registry.py        # Bibliothèque d'outils
│   │   ├── bash_tool_creator.py    # Exécutant
│   │   └── tool_optimizer.py       # Expert
│   │
│   ├── context/
│   │   ├── context_agent.py        # Exécutant
│   │   └── context_optimizer.py    # Expert
│   │
│   └── planning/
│       ├── planner_agent.py        # Expert
│       └── strategy_agent.py       # Directeur
│
└── workflows/
    ├── code_development.py
    ├── tool_creation.py
    └── optimization.py
```

### Classes de base

```python
# cortex/core/department_system.py

class Department:
    """Département avec partage de connaissance"""

    def __init__(self, name: str):
        self.name = name
        self.knowledge_base = DepartmentKnowledgeBase()
        self.agents: Dict[AgentRole, List[BaseAgent]] = {
            AgentRole.EXÉCUTANT: [],
            AgentRole.EXPERT: [],
            AgentRole.DIRECTEUR: []
        }

    def share_knowledge(self, key: str, value: Any):
        """Partage connaissance entre agents du département"""
        self.knowledge_base.store(key, value)

    def get_knowledge(self, key: str) -> Any:
        """Récupère connaissance partagée"""
        return self.knowledge_base.retrieve(key)

    def register_agent(self, agent: BaseAgent):
        """Enregistre un agent dans le département"""
        self.agents[agent.role].append(agent)
```

```python
# cortex/core/workflow_engine.py

class Workflow:
    """Workflow métier avec étapes définies"""

    def __init__(self, name: str, trigger_patterns: List[str]):
        self.name = name
        self.trigger_patterns = trigger_patterns
        self.steps: List[WorkflowStep] = []

    def add_step(self, step: WorkflowStep):
        self.steps.append(step)

    def execute(self, request: str, context: Dict) -> WorkflowResult:
        """Exécute le workflow étape par étape"""
        pass

class WorkflowStep:
    """Étape d'un workflow"""

    def __init__(
        self,
        name: str,
        agent_type: Type[BaseAgent],
        required_role: AgentRole,
        department: str,
        auto_flag_optimization: bool = False
    ):
        self.name = name
        self.agent_type = agent_type
        self.required_role = required_role
        self.department = department
        self.auto_flag_optimization = auto_flag_optimization
```

## Migration depuis l'existant

### Renommages nécessaires

| Ancien | Nouveau | Raison |
|--------|---------|--------|
| `AgentRole.AGENT` | `AgentRole.EXÉCUTANT` | Plus clair en français |
| `DeveloperAgentExpert` | `CodeAnalystAgent` (dept: development) | Séparer hiérarchie/spécialisation |
| `DeveloperAgentDirecteur` | `ArchitectAgent` (dept: development) | Séparer hiérarchie/spécialisation |
| `DeveloperAgentCortex` | `SystemArchitectAgent` (dept: development) | Séparer hiérarchie/spécialisation |
| `TesterAgent` | `CodeValidatorAgent` (dept: development) | Plus précis |

### Nouveaux agents à créer

1. **RequestClassifier** (EXÉCUTANT, dept: routing)
   - Détecte le type de requête
   - Route vers le bon workflow

2. **GitDiffAnalyzer** (EXÉCUTANT, dept: optimization)
   - Parse git diff après modifications
   - Extrait fichiers modifiés, lignes changées

3. **RelationshipMapper** (EXPERT, dept: optimization)
   - Analyse imports et dépendances
   - Met à jour graphe des relations

4. **SiteplanUpdater** (EXPERT, dept: optimization)
   - Met à jour le plan du site
   - Maintient la documentation de structure

5. **BashToolCreator** (EXÉCUTANT, dept: tooling)
   - Crée des scripts bash avec paramètres
   - Rend réutilisables

6. **ToolOptimizer** (EXPERT, dept: tooling)
   - Optimise les outils créés
   - Ajoute error handling, validation

## Exemple concret

### Requête: "Implémente l'authentification OAuth2"

```
1. RequestClassifier (nano) → Détecte: CODE_DEVELOPMENT workflow
   └─> "C'est du développement de code complexe"

2. CODE_DEVELOPMENT workflow démarre:

   Step 1: ContextAgent (dept: context, EXÉCUTANT)
   └─> Prépare contexte: fichiers auth existants, dépendances

   Step 2: PlannerAgent (dept: planning, EXPERT)
   └─> Décompose en 5 tâches:
       - Créer models/user.py
       - Créer auth/oauth2_handler.py
       - Intégrer avec FastAPI
       - Tests unitaires
       - Tests d'intégration

   Step 3: Pour chaque tâche:

   Tâche 1 (simple): CodeWriterAgent (dept: dev, EXÉCUTANT, DeepSeek)
   └─> Crée models/user.py

   Tâche 2 (complexe): CodeAnalystAgent (dept: dev, EXPERT, DeepSeek)
   └─> Analyse architecture OAuth2, crée oauth2_handler.py

   Tâche 3 (décision): ArchitectAgent (dept: dev, DIRECTEUR, GPT5)
   └─> Décide de l'intégration avec FastAPI, génère code

   Step 4: CodeValidatorAgent (dept: dev, EXÉCUTANT, nano)
   └─> Valide syntaxe, imports, lance tests

   Step 5: [AUTO-FLAGGED] OPTIMIZATION workflow

   GitDiffAnalyzer (dept: optimization, EXÉCUTANT, nano)
   └─> Parse git diff: 3 fichiers modifiés, 200 lignes ajoutées

   RelationshipMapper (dept: optimization, EXPERT, DeepSeek)
   └─> Détecte: models/user.py utilisé par auth/oauth2_handler.py
   └─> Met à jour graphe: [user.py] ← [oauth2_handler.py] ← [main.py]

   SiteplanUpdater (dept: optimization, EXPERT, DeepSeek)
   └─> Met à jour SITEPLAN.md:
       ```
       /models/user.py - User model with OAuth2 fields
       /auth/oauth2_handler.py - OAuth2 authentication handler
       Dependencies: FastAPI, authlib
       ```

3. Résultat final:
   ✅ Code généré et testé
   ✅ Plan du site à jour
   ✅ Relations documentées
   ✅ Prêt pour commit
```

## Bénéfices du nouveau modèle

### 1. Clarté organisationnelle
- ✅ Hiérarchie = pouvoir décisionnel
- ✅ Département = spécialisation métier
- ✅ Workflow = processus d'exécution

### 2. Partage de connaissance
- ✅ Knowledge base par département
- ✅ Agents collaborent via département
- ✅ Patterns et outils réutilisables

### 3. Optimisation automatique
- ✅ Département d'optimisation après modifications
- ✅ Plan du site toujours à jour
- ✅ Relations entre fichiers tracées

### 4. Outillage structuré
- ✅ Outils bash créés méthodiquement
- ✅ Optimisation systématique
- ✅ Bibliothèque d'outils partagée

### 5. Détection intelligente
- ✅ Type de requête détecté d'abord
- ✅ Bon workflow activé
- ✅ Bons agents mobilisés

## Plan d'implémentation

### Phase 1: Core infrastructure (2-3 heures)
- [ ] Créer `department_system.py`
- [ ] Créer `workflow_engine.py`
- [ ] Créer `request_classifier.py`
- [ ] Renommer AGENT → EXÉCUTANT

### Phase 2: Département d'optimisation (3-4 heures)
- [ ] Créer `GitDiffAnalyzer`
- [ ] Créer `RelationshipMapper`
- [ ] Créer `SiteplanUpdater`
- [ ] Implémenter workflow d'optimisation
- [ ] Auto-flag après modifications

### Phase 3: Département d'outillage (2-3 heures)
- [ ] Créer `BashToolCreator`
- [ ] Créer `ToolOptimizer`
- [ ] Implémenter ToolRegistry
- [ ] Workflow de création d'outils

### Phase 4: Réorganisation agents existants (2-3 heures)
- [ ] Migrer agents vers départements
- [ ] Renommer selon nouvelle convention
- [ ] Implémenter knowledge bases

### Phase 5: Tests et intégration (2-3 heures)
- [ ] Tester workflows bout en bout
- [ ] Valider optimisation automatique
- [ ] Valider partage de connaissance

**Total estimé: 11-16 heures**

## Prochaine étape recommandée

**Créer les 3 modules core en priorité:**
1. `department_system.py` - Base du système de départements
2. `workflow_engine.py` - Moteur d'exécution
3. `request_classifier.py` - Détection de requêtes

Ceci établira la fondation pour migrer progressivement.

---

**Question pour validation:**
Cette refonte répond-elle à vos attentes? Avez-vous des ajustements sur:
- La structure départementale?
- Les workflows proposés?
- Le département d'optimisation?
- L'agent outilleur?
