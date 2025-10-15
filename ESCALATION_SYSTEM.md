# Système d'Escalade Automatique

## Vue d'ensemble

Le système d'escalade automatique permet à chaque agent d'optimiser ses coûts en commençant toujours par le modèle le moins cher (NANO) et en escaladant automatiquement vers des modèles plus puissants uniquement si la qualité est insuffisante.

**Objectif:** Minimiser les coûts tout en garantissant la qualité des réponses.

## Architecture

### Composants Principaux

```
┌──────────────────────────────────────────────────────┐
│                    BaseAgent                         │
│  ┌────────────────────────────────────────────────┐  │
│  │  execute_with_escalation()                     │  │
│  │  • Essaie tier actuel                          │  │
│  │  • Évalue qualité via LLM                      │  │
│  │  • Escalade si insuffisant                     │  │
│  └────────────────────────────────────────────────┘  │
│           │                       │                   │
│           ▼                       ▼                   │
│  ┌──────────────────┐   ┌────────────────────┐      │
│  │ QualityEvaluator │   │    ExpertPool      │      │
│  │ (LLM-based)      │   │  (8 experts)       │      │
│  └──────────────────┘   └────────────────────┘      │
└──────────────────────────────────────────────────────┘
```

### 1. QualityEvaluator

**Fichier:** `cortex/core/quality_evaluator.py`

**Rôle:** Évalue objectivement la qualité d'une réponse via un LLM (NANO).

**Caractéristiques:**
- Utilise un LLM pour évaluer (PAS d'heuristiques)
- Évalue sur 4 critères: Completeness, Correctness, Clarity, Usefulness
- Retourne un score 0-10
- Suggère escalade (tier supérieur) ou expert si nécessaire
- Tier d'évaluation: NANO (rapide et économique)

**Exemple d'évaluation:**

```python
from cortex.core.quality_evaluator import QualityEvaluator

evaluator = QualityEvaluator()

assessment = evaluator.evaluate(
    task="Write a function to sort a list",
    response="Here's a function...",
    tier_used=ModelTier.NANO,
    quality_threshold=6.0,
    verbose=True
)

print(f"Score: {assessment.score}/10")
print(f"Needs escalation: {assessment.needs_escalation}")
print(f"Suggested tier: {assessment.suggested_tier}")
print(f"Suggested expert: {assessment.suggested_expert}")
```

**Structure QualityAssessment:**

```python
@dataclass
class QualityAssessment:
    score: float              # 0-10
    confidence: float         # 0-1
    issues: List[str]         # Problèmes identifiés
    strengths: List[str]      # Points forts
    needs_escalation: bool    # True si escalade recommandée
    suggested_tier: Optional[ModelTier]    # Tier suggéré
    suggested_expert: Optional[str]        # Type d'expert
    reasoning: str            # Explication
    cost: float               # Coût de l'évaluation
```

### 2. execute_with_escalation()

**Fichier:** `cortex/agents/base_agent.py`

**Rôle:** Méthode principale d'exécution avec escalade automatique.

**Stratégie:**

1. **Essai avec tier préféré** (NANO par défaut)
2. **Évaluation de qualité** via QualityEvaluator
3. **Si qualité < threshold:**
   - Escalade vers tier supérieur (NANO → DEEPSEEK → CLAUDE)
   - Si CLAUDE insuffisant → Escalade vers Expert
4. **Retourne meilleur résultat** avec historique complet

**Paramètres:**

```python
def execute_with_escalation(
    self,
    task: str,                              # Tâche à exécuter
    max_tier: ModelTier = ModelTier.CLAUDE, # Tier max avant expert
    max_attempts: int = 3,                  # Nombre max de tentatives
    quality_threshold: float = 6.0,         # Score minimum (0-10)
    context: Optional[Dict] = None,         # Contexte additionnel
    use_tools: bool = True,                 # Utiliser les outils
    verbose: bool = False                   # Mode verbose
) -> Dict[str, Any]
```

**Exemple d'utilisation:**

```python
from cortex.agents.base_agent import BaseAgent, AgentConfig
from cortex.core.model_router import ModelTier

agent = BaseAgent(
    config=agent_config,
    expert_pool=expert_pool
)

result = agent.execute_with_escalation(
    task="Design a scalable microservices architecture",
    quality_threshold=7.0,  # Exigence élevée
    max_tier=ModelTier.CLAUDE,
    verbose=True
)

print(f"Success: {result['success']}")
print(f"Final tier: {result['final_tier']}")
print(f"Quality score: {result['quality_score']}/10")
print(f"Total cost: ${result['total_cost']:.6f}")
print(f"Escalated: {result['escalated']}")
print(f"Attempts: {result['attempts']}")

# Historique d'escalade
for attempt in result['escalation_history']:
    print(f"Attempt {attempt['attempt']}: {attempt['tier']} - Score: {attempt['quality_score']}")
```

**Résultat complet:**

```python
{
    "success": True,
    "data": "...",                    # Réponse finale
    "agent": "AgentName",
    "role": "Agent Role",
    "cost": 0.001234,                 # Coût total (exec + éval)
    "total_cost": 0.001234,
    "final_tier": "claude",           # Tier final utilisé
    "quality_score": 8.5,             # Score final
    "quality_confidence": 0.9,
    "escalation_history": [           # Historique complet
        {
            "attempt": 1,
            "tier": "nano",
            "quality_score": 4.5,
            "confidence": 0.7,
            "execution_cost": 0.0001,
            "evaluation_cost": 0.00001,
            "issues": ["Response too vague"],
            "strengths": ["Clear structure"]
        },
        {
            "attempt": 2,
            "tier": "deepseek",
            "quality_score": 6.8,
            ...
        },
        {
            "attempt": 3,
            "tier": "claude",
            "quality_score": 8.5,
            ...
        }
    ],
    "escalated": True,
    "attempts": 3,
    "tokens_input": 1500,
    "tokens_output": 800
}
```

### 3. ExpertPool

**Fichier:** `cortex/agents/expert_pool.py`

**Rôle:** Pool d'experts hautement spécialisés (tier CLAUDE) pour tâches ultra-complexes.

**8 Types d'experts disponibles:**

| Expert Type | Spécialisation |
|------------|----------------|
| **SecurityExpert** | Cybersécurité, vulnérabilités, threat modeling, OWASP |
| **SystemDesigner** | Architecture distribuée, microservices, scalabilité |
| **AlgorithmSpecialist** | Algorithmes, complexité, optimisation, data structures |
| **DataScientist** | ML, statistiques, feature engineering, modèles |
| **CodeArchitect** | Design patterns, SOLID, clean code, refactoring |
| **PerformanceOptimizer** | Profiling, benchmarking, optimisation performance |
| **DatabaseArchitect** | Schémas DB, indexation, query optimization |
| **NetworkSpecialist** | API design, REST, GraphQL, protocoles réseau |

**Exemple d'utilisation:**

```python
from cortex.agents.expert_pool import ExpertPool, ExpertType

pool = ExpertPool()

# Consulter un expert
result = pool.consult_expert(
    expert_type=ExpertType.SECURITY_EXPERT,
    task="Review this JWT authentication system for vulnerabilities",
    verbose=True
)

print(f"Expert: {result['expert_name']}")
print(f"Response: {result['data']}")
print(f"Cost: ${result['cost']:.6f}")

# Suggérer un expert via LLM
expert_type = pool.suggest_expert_for_task(
    task_description="Optimize database queries for 10M rows",
    verbose=True
)

print(f"Suggested expert: {expert_type.value}")

# Stats du pool
stats = pool.get_stats()
print(f"Total consultations: {stats['total_consultations']}")
print(f"Total cost: ${stats['total_expert_cost']:.6f}")
```

**Configuration d'un Expert:**

Chaque expert est créé avec:
- **name**: Nom professionnel (ex: "SecurityExpert")
- **role**: Titre officiel (ex: "Chief Security Architect")
- **description**: Bio professionnelle détaillée
- **base_prompt**: Prompt hautement spécialisé définissant:
  - Responsabilités précises
  - Standards et best practices
  - Approche méthodologique
  - Points de vigilance
- **tier**: CLAUDE (experts utilisent toujours le meilleur modèle)
- **specializations**: Liste de tags

## Workflow d'escalade

### Scénario 1: Escalade Simple (NANO → DEEPSEEK)

```
1. Agent reçoit tâche: "Optimize this SQL query"
2. execute_with_escalation() démarre avec NANO
   ├─ Exécution avec NANO: coût $0.0001
   ├─ QualityEvaluator analyse: score 4.5/10
   │  └─ Issues: "Missing index recommendations"
   └─ Escalade suggérée: DEEPSEEK

3. Tentative 2 avec DEEPSEEK
   ├─ Exécution avec DEEPSEEK: coût $0.002
   ├─ QualityEvaluator analyse: score 7.2/10
   │  └─ Strengths: "Detailed optimization strategy"
   └─ Qualité suffisante (> 6.0) ✓

4. Retour résultat DEEPSEEK
   Total cost: $0.002 + $0.00002 (évaluation) = $0.00202
   Escalated: True
   Attempts: 2
```

### Scénario 2: Escalade vers Expert

```
1. Agent reçoit tâche: "Design secure authentication for healthcare app"
2. execute_with_escalation() démarre avec NANO
   ├─ NANO: score 3.2/10
   │  └─ Issues: "Missing HIPAA compliance", "No threat model"
   └─ Escalade: DEEPSEEK

3. Tentative avec DEEPSEEK
   ├─ DEEPSEEK: score 5.5/10
   │  └─ Issues: "Security vulnerabilities not addressed"
   └─ Escalade: CLAUDE

4. Tentative avec CLAUDE
   ├─ CLAUDE: score 5.8/10
   │  └─ QualityEvaluator suggère: "security_expert"
   └─ Expert recommandé ✓

5. Escalade vers SecurityExpert
   ├─ Expert: SecurityExpert (Chief Security Architect)
   ├─ Utilise CLAUDE avec prompt ultra-spécialisé
   ├─ Résultat: score 9.5/10 (assumed)
   │  └─ Analyse complète: HIPAA, OWASP, threat model, encryption
   └─ Qualité suffisante ✓

6. Retour résultat Expert
   Total cost: ~$0.015 (NANO + DEEPSEEK + CLAUDE + Expert)
   Expert used: security_expert
   Final tier: expert
```

### Scénario 3: Pas d'escalade nécessaire

```
1. Agent reçoit tâche: "Format this date string"
2. execute_with_escalation() démarre avec NANO
   ├─ Exécution avec NANO: coût $0.00008
   ├─ QualityEvaluator analyse: score 8.5/10
   │  └─ Strengths: "Correct, clear, concise"
   └─ Qualité suffisante dès le premier essai ✓

3. Retour résultat NANO
   Total cost: $0.00008 + $0.00001 = $0.00009
   Escalated: False
   Attempts: 1

Économie réalisée: 99.4% vs CLAUDE direct
```

## Intégration dans la Hiérarchie

### Structure Mise à Jour

```
CEO
├── 4 Directors (Code, Data, Communication, Operations)
│   ├── Accès à HR Department
│   ├── Accès à Tools Department
│   └── Accès à ExpertPool ✓
├── HR Agent (ChiefRecruiter)
└── Dynamic Employees

Départements:
├── HR Department (création d'employés)
├── Tools Department (création d'outils)
└── Expert Pool ✓ (consultation d'experts)
```

### Initialisation

**Fichier:** `cortex/agents/hierarchy.py`

```python
class AgentHierarchy:
    def __init__(self):
        # 1. Créer départements
        self.tools_department = ToolsDepartment()
        self.hr_department = HRDepartment(tools_department=self.tools_department)

        # 2. Créer ExpertPool
        self.expert_pool = create_expert_pool(
            tools_department=self.tools_department,
            hr_department=self.hr_department
        )

        # 3. Créer CEO avec accès à ExpertPool
        self.ceo = create_ceo(
            hr_department=self.hr_department,
            tools_department=self.tools_department,
            hr_agent=self.hr_agent,
            expert_pool=self.expert_pool  # ✓
        )

        # 4. Donner accès à ExpertPool aux Directors
        for director in [self.code_director, self.data_director, ...]:
            director.expert_pool = self.expert_pool  # ✓
```

### Statistiques

```python
hierarchy = get_hierarchy()
stats = hierarchy.get_all_stats()

# Stats ExpertPool
expert_stats = stats['departments']['expert_pool']
print(f"Consultations: {expert_stats['total_consultations']}")
print(f"Experts créés: {expert_stats['experts_created']}")
print(f"Coût total: ${expert_stats['total_expert_cost']:.6f}")

# Consultations par type
for expert_type, count in expert_stats['consultations_by_type'].items():
    print(f"  {expert_type}: {count} consultations")
```

## Exemples d'Utilisation

### Exemple 1: Simple Execute avec Escalade

```python
from cortex.agents.hierarchy import get_hierarchy

hierarchy = get_hierarchy()

result = hierarchy.code_director.execute_with_escalation(
    task="Refactor this function to follow SOLID principles",
    quality_threshold=7.0,
    verbose=True
)

if result['success']:
    print(f"✓ Task completed with {result['final_tier']}")
    print(f"Quality: {result['quality_score']}/10")
    print(f"Cost: ${result['total_cost']:.6f}")

    if result['escalated']:
        print(f"Escalated from {result['escalation_history'][0]['tier']}")
```

### Exemple 2: Consultation Expert Directe

```python
from cortex.agents.expert_pool import ExpertType

hierarchy = get_hierarchy()

# Consulter expert directement (sans escalade progressive)
result = hierarchy.expert_pool.consult_expert(
    expert_type=ExpertType.ALGORITHM_SPECIALIST,
    task="Design an algorithm to find the shortest path in a weighted graph with negative edges",
    verbose=True
)

print(f"Expert: {result['expert_name']}")
print(f"Response: {result['data']}")
```

### Exemple 3: Suggestion d'Expert

```python
hierarchy = get_hierarchy()

# LLM suggère quel expert consulter
expert_type = hierarchy.expert_pool.suggest_expert_for_task(
    task_description="Design a sharded database architecture for 100M users",
    verbose=True
)

if expert_type:
    result = hierarchy.expert_pool.consult_expert(
        expert_type=expert_type,
        task="Design a sharded database architecture for 100M users",
        verbose=True
    )
```

## Optimisation des Coûts

### Tableau de Coûts (approximatifs)

| Tier | Coût par 1M tokens | Coût typique task |
|------|-------------------|-------------------|
| NANO | ~$0.0001 | $0.0001 - $0.001 |
| DEEPSEEK | ~$0.15 | $0.001 - $0.01 |
| CLAUDE | ~$3.00 | $0.01 - $0.10 |
| Expert (CLAUDE+) | ~$3.00+ | $0.02 - $0.15 |

### Économies Réalisées

**Sans escalade (toujours CLAUDE):**
- 100 tâches simples × $0.05 = **$5.00**

**Avec escalade (NANO → DEEPSEEK → CLAUDE):**
- 70 tâches sur NANO × $0.0005 = $0.035
- 20 tâches sur DEEPSEEK × $0.005 = $0.10
- 10 tâches sur CLAUDE × $0.05 = $0.50
- **Total: $0.635**

**Économie: 87.3%** ✓

### Best Practices

1. **Toujours utiliser execute_with_escalation()** au lieu de execute() pour les tâches de production

2. **Ajuster quality_threshold selon l'importance:**
   - 5.0: Acceptable pour prototypage rapide
   - 6.0: Défaut (bon équilibre)
   - 7.0: Haute qualité requise
   - 8.0: Mission critique

3. **Limiter max_tier pour contrôler les coûts:**
   ```python
   # Limiter à DEEPSEEK pour tâches non-critiques
   result = agent.execute_with_escalation(
       task=task,
       max_tier=ModelTier.DEEPSEEK,
       quality_threshold=6.0
   )
   ```

4. **Monitorer les escalations:**
   ```python
   agent_stats = agent.get_stats()
   print(f"Escalations: {agent_stats['escalation_count']}")
   print(f"Avg cost: ${agent_stats['avg_cost_per_task']:.6f}")
   ```

## Tests

### Test Structurel

```bash
python3 test_escalation_system.py
```

Vérifie:
- ✓ ExpertPool présent et configuré
- ✓ QualityEvaluator disponible
- ✓ execute_with_escalation() disponible
- ✓ 8 experts disponibles
- ✓ Statistiques complètes
- ✓ Intégration dans hiérarchie

### Test Réel (avec LLM)

Pour tester avec de vraies tâches et escalades:

```python
from cortex.agents.hierarchy import get_hierarchy

hierarchy = get_hierarchy()

# Test 1: Tâche simple (devrait rester sur NANO)
result = hierarchy.code_director.execute_with_escalation(
    task="Write a function to reverse a string",
    quality_threshold=6.0,
    verbose=True
)
print(f"Tier used: {result['final_tier']} (expected: nano)")

# Test 2: Tâche complexe (devrait escalader)
result = hierarchy.code_director.execute_with_escalation(
    task="Design a distributed consensus algorithm for Byzantine fault tolerance",
    quality_threshold=7.0,
    verbose=True
)
print(f"Tier used: {result['final_tier']} (expected: claude or expert)")
```

## Limites et Considérations

### Limites Actuelles

1. **Coût d'évaluation:** Chaque tentative nécessite une évaluation LLM (~$0.00001)
   - Pour 1000 tâches × 2 tentatives = $0.02 en évaluation
   - Reste négligeable vs économies réalisées

2. **Latence:** L'escalade ajoute de la latence
   - NANO: ~1s
   - DEEPSEEK: ~2-3s
   - CLAUDE: ~3-5s
   - Expert: ~4-6s
   - Total avec escalade complète: ~10-15s

3. **Dépendance à l'évaluation:** La qualité de l'escalade dépend de la qualité du QualityEvaluator

### Solutions

1. **Cache d'évaluation:** Mettre en cache les patterns de qualité par type de tâche

2. **Apprentissage:** Ajuster quality_threshold dynamiquement selon l'historique

3. **Parallélisation:** Pour tâches non-urgentes, essayer plusieurs tiers en parallèle

## Prochaines Améliorations

### Version 2.0 (Potentiel)

1. **Apprentissage automatique:**
   ```python
   # Prédire le tier optimal AVANT exécution
   predicted_tier = agent.predict_optimal_tier(task)
   ```

2. **Experts dynamiques:**
   ```python
   # Créer des experts sur mesure via HR
   expert = hr_department.create_expert(
       specialization="blockchain-security",
       based_on=ExpertType.SECURITY_EXPERT
   )
   ```

3. **Escalade parallèle:**
   ```python
   # Essayer plusieurs tiers simultanément
   result = agent.execute_with_parallel_escalation(
       task=task,
       tiers=[ModelTier.NANO, ModelTier.DEEPSEEK],
       return_first_sufficient=True
   )
   ```

4. **Cache intelligent:**
   ```python
   # Réutiliser les résultats similaires
   result = agent.execute_with_cache(
       task=task,
       similarity_threshold=0.85
   )
   ```

## Conclusion

Le système d'escalade automatique permet de:

✓ **Minimiser les coûts** (économies de 70-90%)
✓ **Garantir la qualité** (évaluation LLM objective)
✓ **Accéder aux experts** (8 spécialisations)
✓ **Tracer les décisions** (historique complet)
✓ **Optimiser automatiquement** (sans intervention manuelle)

Le système est maintenant **entièrement opérationnel** et prêt pour production!
