# Structure Organisationnelle des Agents Cortex

Chaque agent Cortex a maintenant son propre dossier organisé par département avec:
- **base_prompt.md**: Prompt de base et logique de décision
- **memory.json**: Mémoire interne persistante
- **__init__.py**: Import depuis cortex/agents/

## 📊 Vue d'Ensemble

```
cortex/departments/
├── intelligence/          (Recherche, Analyse, Détection)
│   └── agents/
│       ├── git_watcher/   → GitWatcherAgent (NANO)
│       ├── context/       → ContextAgent (DEEPSEEK)
│       └── tooler/        → ToolerAgent (DEEPSEEK)
│
├── maintenance/           (Maintenance Système, Harmonisation)
│   └── agents/
│       ├── maintenance/   → MaintenanceAgent (DEEPSEEK)
│       ├── harmonization/ → HarmonizationAgent (GPT-5)
│       └── archivist/     → ArchivistAgent (DEEPSEEK)
│
├── communication/         (Communication, Routage)
│   └── agents/
│       ├── communications/ → CommunicationsAgent (NANO)
│       ├── triage/        → TriageAgent (NANO)
│       └── smart_router/  → SmartRouterAgent (NANO)
│
├── optimization/          (Qualité, Tests, Performance)
│   └── agents/
│       ├── quality_control/ → QualityControlAgent (DEEPSEEK)
│       └── tester/         → TesterAgent (DEEPSEEK)
│
└── execution/             (Planification, Exécution Tâches)
    └── agents/
        ├── planner/       → PlannerAgent (DEEPSEEK)
        └── quick_actions/ → QuickActionsAgent (NANO)
```

**Total: 13 agents répartis sur 5 départements**

## 🏗️ Structure d'un Agent

Chaque agent suit cette structure standardisée:

```
cortex/departments/{department}/agents/{agent_name}/
├── base_prompt.md    # Prompt de base, logique, responsabilités
├── memory.json       # Mémoire persistante (historique, patterns, état)
└── __init__.py       # Import depuis cortex/agents/{agent_name}_agent.py
```

### base_prompt.md

Template standardisé contenant:
- **Role**: Rôle principal de l'agent
- **Tier**: Modèle LLM utilisé (NANO, DEEPSEEK, GPT-5, CLAUDE)
- **Description**: Description concise
- **Core Responsibilities**: Responsabilités clés
- **Decision Logic**: Logique de décision base_prompt (sans LLM)
- **Trigger Conditions**: Quand l'agent doit être activé
- **Input Requirements**: Contexte/données nécessaires
- **Output Format**: Format de sortie attendu
- **Escalation Criteria**: Quand escalader
- **Examples**: Exemples concrets
- **Memory Management**: Comment utiliser memory.json
- **Integration Points**: Agents upstream/downstream
- **Notes**: Notes additionnelles

### memory.json

Schéma standardisé:
```json
{
  "version": "1.0.0",
  "last_updated": "2025-10-17T12:00:00",
  "execution_history": [
    {
      "timestamp": "...",
      "request": "...",
      "success": true,
      "duration": 2.5,
      "cost": 0.01,
      "result_summary": "..."
    }
  ],
  "learned_patterns": {
    "pattern_name": {
      "first_detected": "...",
      "occurrences": 5,
      "last_detected": "...",
      "data": [...]
    }
  },
  "performance_metrics": {
    "total_executions": 10,
    "successful_executions": 9,
    "failed_executions": 1,
    "avg_execution_time": 2.3,
    "total_cost": 0.05
  },
  "state": {
    "key": "value"
  },
  "notes": []
}
```

## 📦 Départements

### 🔍 Intelligence Department
**Recherche, Analyse, Détection**

| Agent | Tier | Description |
|-------|------|-------------|
| GitWatcherAgent | NANO | Détecte et analyse changements Git |
| ContextAgent | DEEPSEEK | Prépare contexte pertinent |
| ToolerAgent | DEEPSEEK | Recherche outils/packages externes |

### 🔧 Maintenance Department
**Maintenance Système, Harmonisation**

| Agent | Tier | Description |
|-------|------|-------------|
| MaintenanceAgent | DEEPSEEK | Exécute plans d'harmonisation |
| HarmonizationAgent | GPT-5 | Génère plans d'harmonisation (planning uniquement) |
| ArchivistAgent | DEEPSEEK | Génère rapports et archives |

### 💬 Communication Department
**Communication, Routage**

| Agent | Tier | Description |
|-------|------|-------------|
| CommunicationsAgent | NANO | Résume workflows avec thinking transparent |
| TriageAgent | NANO | Routage initial des requêtes |
| SmartRouterAgent | NANO | Route vers départements appropriés |

### ⚡ Optimization Department
**Qualité, Tests, Performance**

| Agent | Tier | Description |
|-------|------|-------------|
| QualityControlAgent | DEEPSEEK | Évalue qualité et détecte problèmes |
| TesterAgent | DEEPSEEK | Analyse besoins tests (base_prompt logic) |

### 🎯 Execution Department
**Planification, Exécution Tâches**

| Agent | Tier | Description |
|-------|------|-------------|
| PlannerAgent | DEEPSEEK | Planifie décomposition de tâches |
| QuickActionsAgent | NANO | Exécute actions rapides/atomiques |

## 🧠 Système de Mémoire

### AgentMemory Class

Classe Python pour gérer la mémoire interne de chaque agent:

```python
from cortex.core.agent_memory import get_agent_memory

# Récupérer la mémoire d'un agent
memory = get_agent_memory('maintenance', 'maintenance')

# Enregistrer une exécution
memory.record_execution(
    request="Execute plan",
    result={'success': True},
    duration=2.5,
    cost=0.01
)

# Ajouter un pattern détecté
memory.add_pattern('frequent_error', {'type': 'import_error'})

# Mettre à jour l'état interne
memory.update_state({'last_plan': 'ADR-123', 'active': True})

# Récupérer métriques
metrics = memory.get_metrics()
print(f"Success rate: {metrics['successful_executions']/metrics['total_executions']*100:.1f}%")
```

### Méthodes Disponibles

- `record_execution(request, result, duration, cost)`: Enregistre une exécution
- `add_pattern(name, data)`: Enregistre un pattern détecté
- `get_pattern(name)`: Récupère un pattern
- `update_state(updates)`: Met à jour l'état interne
- `get_state(key=None)`: Récupère l'état
- `add_note(note)`: Ajoute une note textuelle
- `get_recent_executions(limit=10)`: Récupère N dernières exécutions
- `get_metrics()`: Récupère métriques de performance
- `clear_history()`: Efface historique (garde patterns/état)
- `reset()`: Reset complet de la mémoire

## 🎯 Philosophie

### Autonomie
Chaque agent est **autonome** avec:
- Son propre dossier
- Son prompt de base
- Sa mémoire interne
- Ses responsabilités claires

### Spécialisation
Agents regroupés par **spécialisation** dans départements logiques:
- Intelligence → Recherche et analyse
- Maintenance → Harmonisation système
- Communication → Interaction utilisateur
- Optimization → Qualité et tests
- Execution → Planification et exécution

### Traçabilité
Historique complet dans `memory.json`:
- Toutes les exécutions tracées
- Patterns détectés enregistrés
- Métriques de performance
- État interne persistant

### Évolution
Base prompt **évolutif**:
- Commence avec template générique
- Enrichi selon apprentissages
- Patterns détectés ajoutés à la logique
- Amélioration continue

## 🚀 Utilisation

### 1. Accéder à un Agent

```python
# Import depuis le département
from cortex.departments.maintenance.agents.maintenance import MaintenanceAgent

# Ou import traditionnel (toujours fonctionnel)
from cortex.agents.maintenance_agent import MaintenanceAgent
```

### 2. Utiliser la Mémoire

```python
from cortex.core.agent_memory import get_agent_memory

# Récupérer mémoire
memory = get_agent_memory('maintenance', 'harmonization')

# Lire l'état
state = memory.get_state()
print(f"Last plan: {state.get('last_plan_id')}")

# Consulter patterns
patterns = memory.get_patterns()
for name, pattern in patterns.items():
    print(f"{name}: {pattern['occurrences']} occurrences")
```

### 3. Enrichir base_prompt.md

Chaque agent peut avoir son `base_prompt.md` enrichi au fil du temps:
- Ajouter exemples réels d'exécutions réussies
- Documenter patterns fréquents détectés
- Affiner logique de décision base_prompt
- Noter limitations et améliorations futures

## 📝 Prochaines Étapes

1. **Enrichir base_prompt.md** de chaque agent avec:
   - Responsabilités détaillées
   - Logique base_prompt précise
   - Exemples réels
   - Critères d'escalation

2. **Intégrer AgentMemory** dans les agents existants:
   - Modifier agents pour utiliser `get_agent_memory()`
   - Enregistrer toutes exécutions
   - Tracker patterns détectés
   - Utiliser état interne

3. **Documentation patterns** détectés:
   - Analyser memory.json des agents actifs
   - Documenter patterns fréquents
   - Mettre à jour base_prompt.md avec insights

4. **Dashboard mémoire**:
   - Visualisation des métriques par agent
   - Comparaison performance entre agents
   - Trends d'apprentissage

## 🎉 Bénéfices

✅ **Organisation claire**: Agents regroupés logiquement par département
✅ **Autonomie complète**: Chaque agent a son dossier, prompt, mémoire
✅ **Traçabilité totale**: Historique complet des exécutions
✅ **Apprentissage continu**: Patterns détectés enregistrés
✅ **Évolutivité**: Base prompts enrichis au fil du temps
✅ **Maintenance facilitée**: Structure standardisée
✅ **Performance trackée**: Métriques par agent

---

*Documentation générée le 2025-10-17*
