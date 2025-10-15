# Cortex Auto-Evolutionary Organization Design

## Vision: Organisation Vivante et Auto-Évolutive

Cortex n'est pas un système statique - c'est une **organisation qui apprend, s'adapte et évolue**.

### Principes Fondamentaux

1. **4 niveaux hiérarchiques FIXES:**
   - EXÉCUTANT (exécution rapide)
   - EXPERT (analyse approfondie)
   - DIRECTEUR (décisions stratégiques)
   - CORTEX_CENTRAL (coordination système)

2. **Départements AUTO-ÉVOLUTIFS:**
   - Peuvent être créés dynamiquement
   - Apprennent de l'historique
   - S'optimisent continuellement

3. **Agents AUTO-GÉRÉS:**
   - Le système décide quand créer de nouveaux agents
   - Le système décide de leur affectation
   - Le système mesure leur performance

4. **Outils AUTO-ÉVOLUTIFS:**
   - Bibliothèque d'outils qui grandit
   - Optimisation continue basée sur usage
   - Documentation automatique

## Architecture Complète

### 1. Départements Core (Toujours actifs)

#### 📁 Département d'OPTIMISATION

**Rôle:** Analyse tout ce qui se passe, optimise continuellement

**Agents:**
- `HistoryAnalyzer` (EXPERT) - Analyse l'historique des tâches
- `SuccessPatternDetector` (EXPERT) - Détecte ce qui fonctionne
- `FailureAnalyzer` (EXPERT) - Analyse les échecs
- `OptimizationRecommender` (DIRECTEUR) - Recommande améliorations

**Knowledge Base:**
```json
{
  "historical_requests": [],      // Toutes les requêtes passées
  "successful_patterns": [],      // Patterns qui ont fonctionné
  "failed_patterns": [],          // Patterns qui ont échoué
  "optimization_history": [],     // Historique des optimisations
  "performance_metrics": {},      // Métriques par agent/département
  "tool_usage_stats": {},         // Statistiques d'usage des outils
  "git_diff_history": []          // Historique des modifications
}
```

**Workflows consultés AVANT toute action:**
1. **Consulte l'historique:** "Est-ce qu'on a déjà fait quelque chose de similaire?"
2. **Analyse les patterns:** "Qu'est-ce qui a fonctionné? Échoué?"
3. **Recommande approche:** "Voici la meilleure façon basée sur l'historique"

**Après toute action:**
1. **Enregistre résultat:** Succès/échec avec contexte
2. **Met à jour patterns:** Apprend des résultats
3. **Suggère optimisations:** Pour les prochaines fois

#### 📁 Département de MAINTENANCE

**Rôle:** Garde tout à jour automatiquement

**Agents:**
- `ContextUpdater` (EXÉCUTANT) - Met à jour tous les contextes
- `RoadmapManager` (EXPERT) - Gère le roadmap complet
- `GitDiffProcessor` (EXÉCUTANT) - Parse git diff
- `DependencyTracker` (EXPERT) - Trace les dépendances
- `DocumentationUpdater` (EXÉCUTANT) - Met à jour docs

**Déclenché par:** Git diff (après chaque modification)

**Actions automatiques:**
1. **Analyse git diff:**
   - Fichiers modifiés
   - Lignes changées
   - Impact sur dépendances

2. **Met à jour contextes:**
   - Cache de contexte par fichier
   - Embeddings des modules modifiés
   - Relations entre fichiers

3. **Met à jour roadmap:**
   - Marque tâches complétées (si git diff correspond)
   - Identifie nouvelles tâches nécessaires
   - Recalcule estimations

4. **Met à jour documentation:**
   - SITEPLAN.md (structure projet)
   - DEPENDENCIES.md (graphe dépendances)
   - CHANGELOG.md (historique modifications)

**Knowledge Base:**
```json
{
  "file_contexts": {},           // Contexte par fichier
  "dependency_graph": {},        // Graphe complet des dépendances
  "roadmap": {
    "completed_tasks": [],
    "in_progress_tasks": [],
    "pending_tasks": [],
    "blocked_tasks": []
  },
  "git_history": [],            // Historique git diff
  "impact_analysis": {}         // Impact des modifications
}
```

#### 📁 Département de COMMUNICATION

**Rôle:** Communiquer l'essentiel au CEO

**Agents:**
- `ExecutiveSummarizer` (EXPERT) - Résume pour C-level
- `ProgressReporter` (EXÉCUTANT) - Rapporte progression
- `AlertManager` (EXÉCUTANT) - Signale problèmes critiques
- `InsightGenerator` (DIRECTEUR) - Génère insights stratégiques

**Produit automatiquement:**

1. **Daily Summary (fin de journée):**
   ```
   📊 CORTEX Daily Summary - 2025-10-15

   ✅ Completed Today:
   - [x] Implemented OAuth2 authentication (3h)
   - [x] Created 5 new bash tools (1h)
   - [x] Optimized 12 existing functions (2h)

   🔄 In Progress:
   - [ ] Refactoring user management (60% done)

   🚨 Issues Detected:
   - Performance degradation in payment module (flagged by Optimization)

   💡 Insights:
   - Authentication tasks are 40% faster since optimization #47
   - Tool reuse increased 25% this week

   📈 Metrics:
   - Cost: $2.34 (85% below baseline)
   - Speed: 3.2x faster than last week
   - Success rate: 94%
   ```

2. **Weekly Strategic Report:**
   ```
   🎯 CORTEX Weekly Strategic Report

   Key Achievements:
   - Developed 15 new features
   - Created 23 reusable tools
   - Reduced costs by 82%

   Department Performance:
   - Development: 47 tasks, 94% success
   - Optimization: 156 improvements applied
   - Maintenance: 100% roadmap accuracy

   Strategic Recommendations:
   - Consider creating "Security" department (12 security-related requests)
   - Invest in "API Integration" specialist agent (high demand)
   ```

3. **Real-time Alerts:**
   ```
   🚨 CRITICAL: Production bug detected in payment flow
   🔍 Analysis: Git diff shows breaking change in models/payment.py
   🛠️ Action: Rolled back + hotfix in progress (ETA: 15min)
   ```

**Knowledge Base:**
```json
{
  "daily_summaries": [],
  "weekly_reports": [],
  "alerts_history": [],
  "ceo_preferences": {
    "summary_frequency": "daily",
    "alert_threshold": "critical",
    "detail_level": "executive"
  },
  "key_metrics": {}
}
```

#### 📁 Département de DÉVELOPPEMENT

**Rôle:** Tout ce qui touche au code

**Agents:**
- `CodeWriterAgent` (EXÉCUTANT) - Écrit code simple
- `CodeAnalystAgent` (EXPERT) - Analyse et code complexe
- `ArchitectAgent` (DIRECTEUR) - Décisions architecturales
- `CodeValidatorAgent` (EXÉCUTANT) - Valide et teste

**AVANT chaque tâche de code:**
1. **Consulte Optimisation:** "Comment a-t-on résolu ça avant?"
2. **Consulte Outillage:** "Y a-t-il un outil existant?"
3. **Consulte Maintenance:** "Quel est le contexte actuel?"

**APRÈS chaque modification:**
1. **Déclenche Maintenance** (mise à jour contextes/roadmap)
2. **Enregistre dans Optimisation** (succès/échec/patterns)

#### 📁 Département d'OUTILLAGE

**Rôle:** Créer et gérer les outils bash réutilisables

**Agents:**
- `BashToolCreator` (EXÉCUTANT) - Crée scripts bash
- `ToolOptimizer` (EXPERT) - Optimise les outils (OBLIGATOIRE)
- `ToolDocumenter` (EXÉCUTANT) - Documente usage
- `ToolTester` (EXÉCUTANT) - Teste les outils

**Workflow de création d'outil:**
```
1. BashToolCreator crée l'outil de base
   └─> Consulte Optimisation: "Y a-t-il des outils similaires?"
   └─> Consulte Outillage: "Quels sont les standards?"

2. ToolOptimizer (OBLIGATOIRE)
   └─> Consulte historique d'usage des outils similaires
   └─> Consulte échecs passés (erreurs communes)
   └─> Optimise: error handling, validation, performance
   └─> Enregistre dans Optimisation: "Nouveau pattern ajouté"

3. ToolTester valide
   └─> Tests unitaires
   └─> Tests edge cases (basés sur échecs historiques)

4. ToolDocumenter
   └─> Génère doc: usage, paramètres, exemples
   └─> Enregistre dans knowledge base
```

**Tool Registry (Knowledge Base):**
```json
{
  "tools": {
    "git_smart_commit": {
      "script_path": "/tools/git_smart_commit.sh",
      "description": "Smart git commit avec validation",
      "parameters": ["message", "files"],
      "usage_count": 156,
      "success_rate": 0.98,
      "last_optimized": "2025-10-14",
      "optimization_history": [
        "Added pre-commit validation",
        "Improved error messages",
        "Added rollback capability"
      ],
      "examples": ["git_smart_commit 'feat: add auth' src/"]
    }
  },
  "optimization_patterns": [],
  "common_failures": [],
  "best_practices": []
}
```

**Consultation systématique:**
- Tout département/agent consulte l'Outillage AVANT de créer un outil
- Tout outil créé DOIT passer par ToolOptimizer
- ToolOptimizer consulte Optimisation pour apprendre des échecs passés

#### 📁 Département de CONTEXTE

**Rôle:** Gestion intelligente du contexte applicatif

**Agents:**
- `ContextAgent` (EXÉCUTANT) - Prépare contexte
- `EmbeddingManager` (EXÉCUTANT) - Gère embeddings
- `ContextOptimizer` (EXPERT) - Optimise sélection

#### 📁 Département de PLANIFICATION

**Rôle:** Décomposition et suivi des tâches

**Agents:**
- `TaskPlanner` (EXPERT) - Décompose tâches
- `StrategyAgent` (DIRECTEUR) - Décisions stratégiques
- `TodoListManager` (EXÉCUTANT) - Gère todo list avec checkboxes

### 2. TodoList System (Style Claude Code)

```python
# cortex/core/todolist_manager.py

class TodoListManager:
    """
    Gestion de todo list avec checkboxes (comme Claude Code)

    Affichage en temps réel:
    ☐ Implement authentication system
    ☑ Create user model
    ☑ Create OAuth2 handler
    ☐ Integrate with FastAPI
    ☐ Write tests
    """

    def __init__(self):
        self.tasks: List[TodoTask] = []
        self.active_workflow: Optional[str] = None

    def create_task_list(self, tasks: List[str], workflow: str):
        """Crée une liste de tâches pour un workflow"""
        self.active_workflow = workflow
        self.tasks = [
            TodoTask(
                id=generate_id(),
                description=task,
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                workflow=workflow
            )
            for task in tasks
        ]
        self._display_tasks()

    def check_task(self, task_id: str):
        """Coche une tâche (☐ → ☑)"""
        task = self._get_task(task_id)
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        self._display_tasks()

        # Notifie Maintenance pour mise à jour roadmap
        self._notify_maintenance(task)

    def _display_tasks(self):
        """Affiche la liste avec checkboxes"""
        print(f"\n📋 {self.active_workflow}\n")
        for task in self.tasks:
            checkbox = "☑" if task.status == TaskStatus.COMPLETED else "☐"
            status_emoji = {
                TaskStatus.PENDING: "⏳",
                TaskStatus.IN_PROGRESS: "🔄",
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌"
            }[task.status]

            print(f"{checkbox} {status_emoji} {task.description}")

            if task.status == TaskStatus.IN_PROGRESS:
                print(f"   └─> {task.current_agent} is working...")
            elif task.status == TaskStatus.COMPLETED:
                print(f"   └─> Completed in {task.duration}s")
```

**Intégration avec workflows:**

```python
# Exemple: Workflow CODE_DEVELOPMENT

async def execute_code_development(request: str):
    # 1. Planification
    planner = TaskPlanner()
    tasks = planner.decompose(request)

    # 2. Créer todo list
    todo_manager = TodoListManager()
    todo_manager.create_task_list(tasks, workflow="CODE_DEVELOPMENT")

    # 3. Exécuter tâches une par une
    for task in tasks:
        # Marquer en cours
        todo_manager.mark_in_progress(task.id, agent=current_agent)

        # Consulter Optimisation AVANT
        optimization = await consult_optimization(task)

        # Exécuter
        result = await execute_task(task, optimization)

        # Cocher si succès
        if result.success:
            todo_manager.check_task(task.id)
        else:
            todo_manager.mark_failed(task.id, error=result.error)

    # 4. Déclencher Maintenance (mise à jour roadmap)
    await trigger_maintenance_workflow(todo_manager.tasks)
```

### 3. Système Auto-Évolutif

#### Gestion Auto-Évolutive des Départements

```python
# cortex/core/auto_evolution.py

class AutoEvolutionManager:
    """
    Gestionnaire d'évolution automatique de l'organisation

    Responsabilités:
    - Détecter besoin de nouveaux départements
    - Créer de nouveaux agents selon demande
    - Optimiser allocation des ressources
    - Mesurer performance et adapter
    """

    def analyze_request_patterns(self) -> List[DepartmentRecommendation]:
        """
        Analyse les patterns de requêtes pour détecter besoins

        Exemple:
        - 20 requêtes "sécurité" → Recommande département Security
        - 15 requêtes "API externe" → Recommande département Integration
        """
        request_history = self.optimization_dept.get_knowledge("historical_requests")

        # Clustering des requêtes
        clusters = cluster_requests(request_history)

        recommendations = []
        for cluster in clusters:
            if cluster.count > 10 and not self.department_exists(cluster.theme):
                recommendations.append(
                    DepartmentRecommendation(
                        name=cluster.theme,
                        reason=f"{cluster.count} requêtes similaires détectées",
                        suggested_agents=[
                            AgentSpec(role=AgentRole.EXÉCUTANT, specialization=...),
                            AgentSpec(role=AgentRole.EXPERT, specialization=...)
                        ]
                    )
                )

        return recommendations

    def create_department_if_needed(self, recommendation: DepartmentRecommendation):
        """Crée un département si validé par DIRECTEUR"""
        # Valider avec DIRECTEUR du département Optimisation
        director = self.get_agent(AgentRole.DIRECTEUR, dept="optimization")
        validation = director.validate_new_department(recommendation)

        if validation.approved:
            # Créer département
            new_dept = Department(name=recommendation.name)

            # Créer agents suggérés
            for agent_spec in recommendation.suggested_agents:
                agent = self.create_agent(agent_spec)
                new_dept.register_agent(agent)

            # Enregistrer
            self.departments[recommendation.name] = new_dept

            # Logger dans Communication
            self.communication_dept.notify_ceo(
                f"🆕 New department created: {recommendation.name}",
                reason=recommendation.reason
            )

    def optimize_agent_allocation(self):
        """
        Optimise l'allocation des agents selon la charge

        Si département Development surchargé → Créer nouveau CodeWriterAgent
        Si outil peu utilisé → Archiver
        """
        for dept_name, dept in self.departments.items():
            metrics = dept.get_performance_metrics()

            # Département surchargé?
            if metrics.avg_response_time > threshold:
                # Créer agent supplémentaire du type le plus sollicité
                bottleneck_role = metrics.bottleneck_role
                new_agent = self.create_agent(
                    AgentSpec(role=bottleneck_role, dept=dept_name)
                )
                dept.register_agent(new_agent)

                self.communication_dept.notify_ceo(
                    f"📈 Scaled {dept_name}: Added {bottleneck_role}",
                    reason=f"Response time exceeded threshold"
                )
```

#### Création Dynamique d'Agents

```python
class AgentFactory:
    """Factory pour créer agents dynamiquement"""

    def create_agent(
        self,
        role: AgentRole,
        department: str,
        specialization: str,
        learn_from_history: bool = True
    ) -> BaseAgent:
        """
        Crée un agent avec apprentissage de l'historique

        Si learn_from_history=True:
        - Consulte historique du département
        - Initialise avec patterns de succès
        - Configure selon best practices apprises
        """
        # Base agent selon role
        agent_class = {
            AgentRole.EXÉCUTANT: ExecutionAgent,
            AgentRole.EXPERT: AnalysisAgent,
            AgentRole.DIRECTEUR: DecisionAgent,
            AgentRole.CORTEX_CENTRAL: CoordinationAgent
        }[role]

        agent = agent_class(
            llm_client=self.llm_client,
            specialization=specialization,
            department=department
        )

        if learn_from_history:
            # Apprendre de l'historique
            dept = self.get_department(department)
            history = dept.knowledge_base.get("successful_patterns")
            agent.initialize_from_history(history)

        return agent
```

### 4. Flux de Travail Complet

#### Exemple: Requête "Implémenter paiement Stripe"

```
┌─────────────────────────────────────────────────────────────┐
│ 1. REQUÊTE ENTRE                                            │
└─────────────────────────────────────────────────────────────┘
   "Implémenter paiement Stripe"
            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. CONSULTATION OPTIMISATION (AVANT toute action)          │
└─────────────────────────────────────────────────────────────┘
   HistoryAnalyzer cherche dans historical_requests:

   Trouvé: "Implémentation PayPal" (similaire, succès)
   Pattern utilisé: API wrapper → Tests → Intégration
   Outils créés: payment_validator.sh, api_tester.sh

   Recommandation: "Suivre même pattern, réutiliser outils"
            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. PLANIFICATION                                            │
└─────────────────────────────────────────────────────────────┘
   TaskPlanner (dept: planning, EXPERT) décompose:

   📋 TodoList créée:
   ☐ Installer bibliothèque stripe
   ☐ Créer models/payment.py
   ☐ Créer services/stripe_service.py
   ☐ Créer API endpoints
   ☐ Tests unitaires
   ☐ Tests d'intégration
   ☐ Documentation
            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. CONSULTATION OUTILLAGE                                   │
└─────────────────────────────────────────────────────────────┘
   ToolRegistry consulté:
   - payment_validator.sh ✅ (existe, 98% success rate)
   - api_tester.sh ✅ (existe, optimisé 3x)

   Décision: Réutiliser outils existants
            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. EXÉCUTION (avec checkboxes en temps réel)               │
└─────────────────────────────────────────────────────────────┘

   ☑ ✅ Installer bibliothèque stripe
      └─> CodeWriterAgent (EXÉCUTANT) - 2s

   ☑ ✅ Créer models/payment.py
      └─> CodeWriterAgent (EXÉCUTANT) - 15s

   ☐ 🔄 Créer services/stripe_service.py
      └─> CodeAnalystAgent (EXPERT) is working...

   [CodeAnalystAgent consulte Optimisation:]
   - Pattern PayPal: API wrapper avec retry logic
   - Échec historique: Pas de timeout → Ajouté timeout
   - Best practice: Utiliser async/await

   ☑ ✅ Créer services/stripe_service.py
      └─> CodeAnalystAgent (EXPERT) - 45s

   ☑ ✅ Créer API endpoints
      └─> ArchitectAgent (DIRECTEUR) - 60s

   ☑ ✅ Tests unitaires
      └─> CodeValidatorAgent (EXÉCUTANT) - 30s
      └─> Utilise: payment_validator.sh ✅

   ☑ ✅ Tests d'intégration
      └─> CodeValidatorAgent (EXÉCUTANT) - 45s
      └─> Utilise: api_tester.sh ✅

   ☑ ✅ Documentation
      └─> CodeWriterAgent (EXÉCUTANT) - 10s
            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. MAINTENANCE (Auto-déclenché par git diff)               │
└─────────────────────────────────────────────────────────────┘

   GitDiffProcessor analyse:
   - 3 fichiers créés: models/payment.py, services/stripe_service.py, api/payment.py
   - 247 lignes ajoutées

   ContextUpdater met à jour:
   - Cache contexte pour payment.py
   - Embeddings des nouveaux modules

   DependencyTracker détecte:
   - payment.py ← stripe_service.py ← payment.py (API)
   - Nouvelles dépendances: stripe, pydantic

   RoadmapManager met à jour:
   - ☑ "Implémenter paiement Stripe" (COMPLETED)
   - Détecte besoin: "Ajouter webhooks Stripe" (PENDING)

   DocumentationUpdater:
   - SITEPLAN.md: +section "Payment Integration"
   - DEPENDENCIES.md: +graphe stripe
   - CHANGELOG.md: +entry "feat: Stripe payment"
            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. OPTIMISATION (Enregistre pour futur)                    │
└─────────────────────────────────────────────────────────────┘

   Enregistre dans historical_requests:
   {
     "request": "Implémenter paiement Stripe",
     "pattern_used": "API wrapper avec retry + timeout",
     "tools_used": ["payment_validator.sh", "api_tester.sh"],
     "success": true,
     "duration": "3m 27s",
     "files_created": 3,
     "lines_added": 247,
     "lessons_learned": [
       "Async/await essentiel pour API calls",
       "Timeout évite freeze sur erreur réseau",
       "Réutilisation outils = 40% plus rapide"
     ]
   }

   Met à jour successful_patterns:
   - "API payment integration" → 2 succès (PayPal, Stripe)
   - Confidence: 95%
   - Template créé pour futurs paiements
            ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. COMMUNICATION CEO                                        │
└─────────────────────────────────────────────────────────────┘

   ExecutiveSummarizer génère:

   ✅ Task Completed: Stripe Payment Integration

   📊 Summary:
   - Duration: 3m 27s
   - Files: 3 created, 0 modified
   - Tests: 12/12 passing ✅
   - Reused tools: 2 (saved 40% time)

   💡 Insight:
   - Payment integration pattern solidified (2/2 success)
   - Recommendation: Create "PaymentIntegration" template tool

   📋 Roadmap Updated:
   - ☑ Stripe integration
   - 🆕 Webhooks needed (detected automatically)
```

## Implémentation Technique

### Phase 1: Core Infrastructure (3-4h)

#### 1.1 Department System avec Knowledge Base

```python
# cortex/core/department_system.py

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

class DepartmentKnowledgeBase:
    """Base de connaissance partagée d'un département"""

    def __init__(self, department_name: str, storage_path: str):
        self.department_name = department_name
        self.storage_path = Path(storage_path) / f"{department_name}_kb.json"
        self.data: Dict[str, Any] = self._load()

    def store(self, key: str, value: Any, metadata: Optional[Dict] = None):
        """Stocke une connaissance avec métadonnées"""
        self.data[key] = {
            "value": value,
            "updated_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self._save()

    def retrieve(self, key: str) -> Any:
        """Récupère une connaissance"""
        return self.data.get(key, {}).get("value")

    def search(self, query: str) -> List[Dict]:
        """Recherche dans la base de connaissance"""
        # TODO: Utiliser embeddings pour recherche sémantique
        pass

    def get_history(self, key: str) -> List[Dict]:
        """Récupère l'historique d'une connaissance"""
        pass

class Department:
    """Département avec agents et knowledge base"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.knowledge_base = DepartmentKnowledgeBase(name, "cortex/data/departments")
        self.agents: Dict[AgentRole, List[BaseAgent]] = {
            AgentRole.EXÉCUTANT: [],
            AgentRole.EXPERT: [],
            AgentRole.DIRECTEUR: [],
            AgentRole.CORTEX_CENTRAL: []
        }
        self.metrics = DepartmentMetrics()

    def register_agent(self, agent: BaseAgent):
        """Enregistre un agent dans le département"""
        self.agents[agent.role].append(agent)
        agent.department = self

    def get_agents_by_role(self, role: AgentRole) -> List[BaseAgent]:
        """Récupère tous les agents d'un rôle"""
        return self.agents[role]

    def share_knowledge(self, key: str, value: Any, metadata: Optional[Dict] = None):
        """Partage connaissance entre agents du département"""
        self.knowledge_base.store(key, value, metadata)

    def consult_knowledge(self, key: str) -> Any:
        """Consulte connaissance partagée"""
        return self.knowledge_base.retrieve(key)

    def get_performance_metrics(self) -> DepartmentMetrics:
        """Récupère métriques de performance du département"""
        return self.metrics
```

#### 1.2 TodoList Manager avec Checkboxes

```python
# cortex/core/todolist_manager.py

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from rich.console import Console
from rich.table import Table

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

@dataclass
class TodoTask:
    id: str
    description: str
    status: TaskStatus
    created_at: datetime
    workflow: str
    assigned_to: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    dependencies: List[str] = None

class TodoListManager:
    """
    Gestionnaire de todo list avec affichage checkboxes (style Claude Code)
    """

    def __init__(self):
        self.console = Console()
        self.tasks: List[TodoTask] = []
        self.active_workflow: Optional[str] = None

    def create_task_list(self, tasks: List[str], workflow: str):
        """Crée liste de tâches pour un workflow"""
        self.active_workflow = workflow
        self.tasks = [
            TodoTask(
                id=f"task_{i}",
                description=task,
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                workflow=workflow,
                dependencies=[]
            )
            for i, task in enumerate(tasks)
        ]
        self.display()

    def start_task(self, task_id: str, agent_name: str):
        """Marque tâche comme en cours"""
        task = self._get_task(task_id)
        task.status = TaskStatus.IN_PROGRESS
        task.assigned_to = agent_name
        task.started_at = datetime.now()
        self.display()

    def complete_task(self, task_id: str):
        """Coche tâche comme complétée (☐ → ☑)"""
        task = self._get_task(task_id)
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()

        if task.started_at:
            task.duration_seconds = (task.completed_at - task.started_at).total_seconds()

        self.display()

        # Notifier département Maintenance
        from cortex.departments.maintenance import notify_task_completed
        notify_task_completed(task)

    def fail_task(self, task_id: str, error: str):
        """Marque tâche comme échouée"""
        task = self._get_task(task_id)
        task.status = TaskStatus.FAILED
        task.error = error
        self.display()

    def display(self):
        """Affiche la todo list avec checkboxes"""
        self.console.clear()

        # Header
        table = Table(title=f"📋 {self.active_workflow}", show_header=False)

        for task in self.tasks:
            # Checkbox
            checkbox = {
                TaskStatus.PENDING: "☐",
                TaskStatus.IN_PROGRESS: "☐",
                TaskStatus.COMPLETED: "☑",
                TaskStatus.FAILED: "☒",
                TaskStatus.BLOCKED: "⊘"
            }[task.status]

            # Status emoji
            status_emoji = {
                TaskStatus.PENDING: "⏳",
                TaskStatus.IN_PROGRESS: "🔄",
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.BLOCKED: "🚫"
            }[task.status]

            # Ligne principale
            line = f"{checkbox} {status_emoji} {task.description}"

            # Détails selon status
            if task.status == TaskStatus.IN_PROGRESS:
                line += f"\n   └─> {task.assigned_to} is working..."
            elif task.status == TaskStatus.COMPLETED:
                line += f"\n   └─> Completed in {task.duration_seconds:.1f}s"
            elif task.status == TaskStatus.FAILED:
                line += f"\n   └─> Error: {task.error}"

            table.add_row(line)

        self.console.print(table)

    def get_summary(self) -> Dict[str, Any]:
        """Résumé de la todo list"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks if t.status == TaskStatus.FAILED)

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total if total > 0 else 0,
            "total_duration": sum(
                t.duration_seconds for t in self.tasks
                if t.duration_seconds is not None
            )
        }

    def _get_task(self, task_id: str) -> TodoTask:
        """Récupère tâche par ID"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise ValueError(f"Task {task_id} not found")
```

#### 1.3 Workflow Engine

```python
# cortex/core/workflow_engine.py

from typing import List, Dict, Any, Callable
from dataclasses import dataclass

@dataclass
class WorkflowStep:
    """Étape d'un workflow"""
    name: str
    agent_type: str  # Nom de l'agent à utiliser
    department: str
    required_role: AgentRole
    consult_optimization: bool = True  # Consulter avant?
    auto_trigger_maintenance: bool = False
    auto_trigger_optimization: bool = False

class Workflow:
    """Workflow d'exécution"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []
        self.todo_manager = TodoListManager()

    def add_step(self, step: WorkflowStep):
        """Ajoute étape au workflow"""
        self.steps.append(step)

    async def execute(
        self,
        request: str,
        context: Dict[str, Any],
        organization: 'CortexOrganization'
    ) -> WorkflowResult:
        """Exécute le workflow complet"""

        # Créer todo list
        task_descriptions = [step.name for step in self.steps]
        self.todo_manager.create_task_list(task_descriptions, self.name)

        results = []

        for i, step in enumerate(self.steps):
            task_id = f"task_{i}"

            # 1. Consulter Optimisation AVANT (si requis)
            optimization_advice = None
            if step.consult_optimization:
                optimization_dept = organization.get_department("optimization")
                optimization_advice = await self._consult_optimization(
                    step, request, optimization_dept
                )

            # 2. Obtenir agent approprié
            department = organization.get_department(step.department)
            agent = department.get_agents_by_role(step.required_role)[0]

            # 3. Marquer tâche en cours
            self.todo_manager.start_task(task_id, agent.__class__.__name__)

            # 4. Exécuter
            try:
                result = await agent.execute(
                    request=step.name,
                    context={
                        **context,
                        "optimization_advice": optimization_advice
                    }
                )

                if result.success:
                    # Cocher tâche
                    self.todo_manager.complete_task(task_id)
                    results.append(result)
                else:
                    # Marquer échouée
                    self.todo_manager.fail_task(task_id, result.error)

                    # Escalade si nécessaire
                    if result.should_escalate:
                        escalated_result = await self._escalate_step(
                            step, request, context, organization
                        )
                        results.append(escalated_result)

            except Exception as e:
                self.todo_manager.fail_task(task_id, str(e))
                raise

            # 5. Triggers post-exécution
            if step.auto_trigger_maintenance:
                await self._trigger_maintenance(organization, result)

            if step.auto_trigger_optimization:
                await self._trigger_optimization(organization, step, result)

        return WorkflowResult(
            success=all(r.success for r in results),
            steps_results=results,
            todo_summary=self.todo_manager.get_summary()
        )
```

### Phase 2: Départements Spécialisés (4-5h)

Je vais créer les fichiers pour chaque département dans le prochain message. Voulez-vous que je commence l'implémentation ou souhaitez-vous d'abord valider ce design?

**Points clés à confirmer:**
1. TodoList avec checkboxes en temps réel (style Claude Code) ✓
2. Consultation systématique de l'Optimisation AVANT chaque action ✓
3. Département Maintenance auto-déclenché sur git diff ✓
4. Département Communication pour rapports CEO ✓
5. Système auto-évolutif pour départements/agents/outils ✓
6. Tous consultent l'historique (succès/échecs) ✓

Dois-je commencer l'implémentation?
