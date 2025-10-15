# Cortex Self-Improvement System

## Vue d'ensemble

Le système Cortex dispose maintenant d'une **boucle d'auto-amélioration complète** qui lui permet de :
- Détecter ses propres lacunes
- Proposer des solutions (nouveaux agents, workflows, etc.)
- Se valider et se corriger automatiquement
- Apprendre de ses erreurs

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER REQUEST                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  FEEDBACK SYSTEM                             │
│  • Real-time user visibility                                 │
│  • Progress updates                                          │
│  • Success/warning/error notifications                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  AGENT EXECUTION                             │
│  • Tools execution                                           │
│  • Task delegation                                           │
│  • Model selection & escalation                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  VALIDATION SYSTEM                           │
│  • Auto-validate results                                     │
│  • Auto-correct common errors                                │
│  • Ensure data integrity                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  LOGGING SYSTEM                              │
│  • Structured event logging                                  │
│  • Performance metrics                                       │
│  • Pattern detection                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  META-ARCHITECT                              │
│  • Analyzes logs & patterns                                  │
│  • Detects missing capabilities                              │
│  • Proposes new agents/workflows                             │
│  • Implements improvements                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              SYSTEM IMPROVEMENT APPLIED                      │
└─────────────────────────────────────────────────────────────┘
```

## Composants

### 1. Feedback System (`cortex/core/feedback_system.py`)

**Objectif** : Donner une visibilité temps réel à l'utilisateur sur ce qui se passe.

```python
from cortex.core.feedback_system import get_feedback

feedback = get_feedback()
feedback.success("Tool 'read_file' executed successfully", file="data.csv", lines=1000)
feedback.warning("Cache miss - computing from scratch", fallback="recompute")
feedback.error("Failed to connect to database", error="Connection timeout")
```

**Pourquoi c'est crucial** :
- L'utilisateur voit immédiatement si un tool a fonctionné
- Pas besoin de deviner ce qui se passe en arrière-plan
- Messages clairs et structurés

### 2. Logging System (`cortex/core/cortex_logger.py`)

**Objectif** : Enregistrer TOUT pour permettre l'auto-analyse.

```python
from cortex.core.cortex_logger import get_logger, EventType

logger = get_logger()
logger.log(
    event_type=EventType.TASK_START,
    agent="CEO",
    message="New task received",
    data={"task": "analyze_data"},
    task_id="task_001"
)
```

**Capacités d'analyse** :
- `analyze_recent_performance()` - Métriques de performance
- `identify_improvement_opportunities()` - Détecte les problèmes
- `generate_self_improvement_report()` - Rapport complet pour LLM

**Exemple de sortie** :
```
Success Rate: 87.5%
Escalation Rate: 12.3%
Avg Cost/Task: $0.0023
Recurring Issue: "Timeout" (5 occurrences)
→ Suggestion: Create Performance Optimization Agent
```

### 3. Self Validator (`cortex/core/self_validator.py`)

**Objectif** : Valider et corriger automatiquement les résultats.

```python
from cortex.core.self_validator import get_validator

validator = get_validator()
result = {"success": True, "cost": -0.001}  # Coût négatif - erreur!

validated = validator.validate(result, auto_fix=True)
# → Corrige automatiquement: cost = 0.001
```

**Règles de validation** :
- ✓ Vérifier les clés requises
- ✓ Corriger les valeurs invalides (négatifs, nulls, etc.)
- ✓ Détecter les coûts anormalement élevés
- ✓ Valider la cohérence des données

**Workflow Validator** :
```python
from cortex.core.self_validator import get_workflow_validator

workflow_validator = get_workflow_validator()
validation = workflow_validator.validate_workflow(steps)

# Détecte:
# - Trop d'escalations
# - Coûts élevés
# - Échecs récurrents
# - Patterns inefficaces
```

### 4. Meta-Architect Agent (`cortex/agents/meta_architect_agent.py`)

**Objectif** : L'agent qui améliore le système lui-même.

```python
from cortex.agents.meta_architect_agent import create_meta_architect

meta = create_meta_architect()

# Analyse complète du système
report = meta.run_full_analysis(verbose=True)

# Détecte les capacités manquantes
missing = meta.detect_missing_capabilities()
# → ["External Integration Agent needed", "Data Validator needed"]

# Propose la création d'un nouvel agent
meta.propose_new_agent(
    role="Data Manager",
    reason="Recurring failures in data validation tasks",
    specializations=["pricing", "data_validation"]
)

# Suggère des améliorations de workflow
meta.suggest_workflow_improvement(
    current_workflow="CEO → Worker → Store",
    issues=["High failure rate on Store step"]
)

# Auto-corrige un problème récurrent
meta.auto_correct_recurring_issue(
    issue="Database timeout",
    occurrences=5
)
```

**Le Meta-Architect peut** :
- ✓ Analyser les logs et identifier les patterns
- ✓ Calculer un "health score" du système
- ✓ Détecter quand un agent manque au système
- ✓ Proposer des nouveaux agents via HR Department
- ✓ Suggérer des optimisations de workflow
- ✓ Générer des plans de correction automatiques

### 5. Data Manager Agent (`cortex/agents/data_manager_agent.py`)

**Objectif** : Maintenir les données critiques (comme les prix des modèles).

```python
from cortex.agents.data_manager_agent import create_data_manager

manager = create_data_manager()

# Vérifier les prix actuels
manager.execute_data_task({"type": "verify_pricing"})

# Mettre à jour les prix
manager.execute_data_task({
    "type": "update_pricing",
    "prices": {
        "nano": {"input": 0.05, "output": 0.40},
        "deepseek": {"input": 0.28, "output": 0.42},
        "claude": {"input": 3.0, "output": 15.0}
    }
})

# Générer un rapport
report = manager.generate_pricing_report()
```

## Cycle d'auto-amélioration

```
1. EXECUTION
   └→ Les agents exécutent des tâches
   └→ Feedback temps réel à l'utilisateur
   └→ Tous les événements sont loggés

2. VALIDATION
   └→ Les résultats sont automatiquement validés
   └→ Les erreurs sont corrigées automatiquement
   └→ Les workflows sont analysés

3. ANALYSE
   └→ Le Meta-Architect analyse les logs
   └→ Identifie les patterns inefficaces
   └→ Détecte les capacités manquantes
   └→ Calcule un health score

4. PROPOSITION
   └→ Suggère des nouveaux agents
   └→ Propose des optimisations de workflow
   └→ Génère des plans de correction
   └→ Identifie les besoins récurrents

5. APPLICATION
   └→ Crée automatiquement de nouveaux agents (via HR)
   └→ Applique les corrections
   └→ Optimise les coûts et performances
   └→ Retour à l'étape 1
```

## Exemple concret : Comment le système s'est amélioré

### Problème initial
L'utilisateur crée test2.md et ne reçoit **aucun feedback** sur le succès/échec.

### Le système détecte le problème
```python
# Meta-Architect analyse les logs
report = meta_architect.run_full_analysis()

# Identifie:
# - Absence de feedback utilisateur sur les tools
# - Pas de système de logging pour auto-analyse
# - Pas d'agent pour maintenir les prix des modèles
```

### Le système propose des solutions
```
Missing Capability: "User feedback on tool execution"
→ Create: Feedback System

Missing Capability: "System self-analysis"
→ Create: Logging System + Meta-Architect Agent

Missing Capability: "Dynamic data management"
→ Create: Data Manager Agent

Workflow Issue: "No validation of results"
→ Create: Self Validator
```

### Le système s'améliore
1. **Feedback System** créé → L'utilisateur voit maintenant tout
2. **Logger** créé → Le système peut s'analyser
3. **Meta-Architect** créé → Propose des améliorations
4. **Self Validator** créé → Corrige automatiquement les erreurs
5. **Data Manager** créé → Maintient les prix à jour

## Utilisation pratique

### Pour l'utilisateur (simple)
Le système est maintenant **transparent** :
```
✓ read_file tool executed (file: data.csv, 1000 lines)
→ Processing data...
⚠ Cache miss - computing from scratch
✓ Analysis complete (cost: $0.002, duration: 3.2s)
```

### Pour le système (auto-amélioration)
Le système s'analyse en continu :
```python
# Chaque nuit (ou sur demande)
meta = create_meta_architect()
report = meta.run_full_analysis()

# Si des problèmes détectés:
if report["health"]["health_score"] < 70:
    # Auto-créer des agents manquants
    for capability in report["missing_capabilities"]:
        hr_department.create_agent(capability["suggestion"])

    # Appliquer des optimisations
    for improvement in report["health"]["improvement_opportunities"]:
        meta.apply_improvement(improvement)
```

## Intégration avec les agents existants

### BaseAgent amélioré
Tous les agents héritent maintenant de ces capacités :
```python
class MyAgent(BaseAgent):
    def execute(self, task, verbose=False):
        # 1. Feedback utilisateur
        feedback.progress(f"Starting {task}")

        # 2. Logger l'événement
        logger.log(EventType.TASK_START, self.name, task)

        # 3. Exécuter
        result = super().execute(task, verbose)

        # 4. Valider
        result = validator.validate_and_apply(result)

        # 5. Logger la complétion
        logger.log(EventType.TASK_COMPLETE, self.name, "Done", cost=result["cost"])

        # 6. Feedback final
        feedback.success(f"Task completed", cost=result["cost"])

        return result
```

## Métriques de succès

Le système mesure maintenant :
- **Success Rate** : % de tâches réussies
- **Escalation Rate** : % de tâches nécessitant escalade
- **Avg Cost/Task** : Coût moyen par tâche
- **Health Score** : Score global 0-100
- **Agent Efficiency** : Utilisation et coûts par agent
- **Recurring Issues** : Problèmes qui reviennent souvent

## Tests

Exécuter le test complet :
```bash
python3 test_self_improvement_system.py
```

Ce test démontre :
1. ✓ Feedback temps réel
2. ✓ Logging et analyse
3. ✓ Auto-validation et correction
4. ✓ Détection de workflows inefficaces
5. ✓ Meta-Architect proposant des améliorations
6. ✓ Workflow complet intégré

## Prochaines étapes

Le système peut maintenant :
1. **Auto-détecter** qu'il lui manque un agent
2. **Proposer** la création de cet agent au HR Department
3. **Générer** la spécification de l'agent
4. **Créer** l'agent automatiquement
5. **Valider** que l'agent fonctionne
6. **Optimiser** l'agent basé sur les métriques

C'est un véritable **système auto-évolutif**.

## Conclusion

Le système Cortex dispose maintenant d'une **conscience** de lui-même :
- Il sait quand il échoue
- Il comprend pourquoi
- Il propose des solutions
- Il s'améliore automatiquement

L'utilisateur, lui, a juste besoin de faire sa demande et reçoit un **feedback clair** sur ce qui se passe, pendant que le système s'optimise en arrière-plan.

**Le système n'attend plus qu'on lui dise ce qui manque - il le détecte et le propose lui-même.**
