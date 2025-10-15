# Nano Self-Assessment & Intelligent Routing

## Concept

Nano évalue d'abord:
1. **Sa propre confiance** - Peut-il répondre avec haute confiance?
2. **La sévérité** - Quelle est la gravité de la tâche?
3. **Le meilleur employé** - Qui est le plus qualifié?

**Flow de décision:**
```
Task arrive → Nano évalue →
  ├─ Haute confiance + faible sévérité → Nano répond directement
  └─ Faible confiance OU haute sévérité → Route vers employé qualifié
```

## Architecture

### Phase 1: Self-Assessment (Nano uniquement)

Nano reçoit un prompt spécial qui lui demande:

```python
SELF_ASSESSMENT_PROMPT = """
You are a task evaluator. Analyze this task and provide a structured assessment.

Task: {task}

Evaluate:
1. CONFIDENCE: Can you handle this task safely with HIGH confidence?
   - HIGH: Simple, routine task within your expertise
   - MEDIUM: Doable but requires careful attention
   - LOW: Complex, risky, or outside expertise

2. SEVERITY: What's the severity level?
   - CRITICAL: Production, security, payments, auth, data migration
   - HIGH: Public APIs, core features, important functionality
   - MEDIUM: Standard features, general work
   - LOW: Refactoring, docs, tests, cleanup

3. BEST_EMPLOYEE: If you cannot handle with HIGH confidence, who should?
   - ceo: Strategic decisions, company-wide changes
   - cto: Technical architecture, system design
   - hr: Hiring, employee management, team structure
   - finance: Budget, pricing, cost analysis
   - product: Features, roadmap, user experience
   - [worker_name]: Specific implementation task

4. REASONING: Brief explanation (1-2 sentences)

Respond ONLY in this JSON format:
{
  "confidence": "HIGH|MEDIUM|LOW",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "can_handle_safely": true|false,
  "best_employee": "nano|ceo|cto|hr|finance|product|[worker]",
  "reasoning": "brief explanation"
}
"""
```

### Phase 2: Decision Tree

```python
assessment = nano.evaluate(task)

if assessment["confidence"] == "HIGH" and assessment["severity"] in ["LOW", "MEDIUM"]:
    # Nano peut gérer
    result = nano.execute(task)

elif assessment["can_handle_safely"] == False:
    # Route vers meilleur employé
    employee = get_employee(assessment["best_employee"])
    result = employee.execute(
        task=task,
        severity=assessment["severity"],
        context_budget=adjust_by_severity(assessment["severity"])
    )

else:
    # Escalade prudente
    result = escalate_to_supervisor(task, assessment)
```

## Règles de Décision

### Nano Peut Gérer (Exécute Directement)

✅ **HIGH confidence + LOW severity**
- Exemples: "Add a comment", "Rename variable", "Format code"

✅ **HIGH confidence + MEDIUM severity**
- Exemples: "Create simple function", "Add validation", "Update config"

### Nano Doit Router (Délègue)

❌ **Toute tâche CRITICAL**
- Raison: Risque trop élevé pour nano seul

❌ **LOW confidence (quelle que soit la sévérité)**
- Raison: Nano pas sûr → déléguer

❌ **MEDIUM confidence + HIGH severity**
- Raison: Combinaison risquée

## Exemples

### Exemple 1: Nano Peut Gérer

```
Task: "Add validation to check if email is not empty"

Nano Assessment:
{
  "confidence": "HIGH",
  "severity": "MEDIUM",
  "can_handle_safely": true,
  "best_employee": "nano",
  "reasoning": "Simple validation, straightforward implementation"
}

→ Nano exécute directement
```

### Exemple 2: Nano Route vers CTO

```
Task: "Redesign the authentication system architecture"

Nano Assessment:
{
  "confidence": "LOW",
  "severity": "CRITICAL",
  "can_handle_safely": false,
  "best_employee": "cto",
  "reasoning": "Complex architecture change affecting security"
}

→ Route vers CTO avec contexte CRITICAL (seuil 0.6)
```

### Exemple 3: Nano Route vers Worker Spécialisé

```
Task: "Implement OAuth2 authentication flow"

Nano Assessment:
{
  "confidence": "MEDIUM",
  "severity": "HIGH",
  "can_handle_safely": false,
  "best_employee": "security_worker",
  "reasoning": "Security-critical implementation requiring expertise"
}

→ Route vers security_worker avec contexte HIGH (seuil 0.85)
```

### Exemple 4: Nano Gère Simple Task

```
Task: "Add docstring to calculate_total function"

Nano Assessment:
{
  "confidence": "HIGH",
  "severity": "LOW",
  "can_handle_safely": true,
  "best_employee": "nano",
  "reasoning": "Simple documentation task"
}

→ Nano exécute directement
```

## Avantages

### 1. Sécurité Maximale
- Nano ne prend pas de risques sur tâches critiques
- Toujours escalade si incertain
- Double vérification: confidence ET severity

### 2. Efficacité
- Nano gère les tâches simples (80% des cas)
- Pas de surcharge inutile pour tâches triviales
- Délègue intelligemment les 20% complexes

### 3. Coût Optimisé
```
Simple task → Nano ($0.05/1M)
Complex task → Director ($0.28/1M) ou Claude ($3/1M)

Au lieu de:
Toute task → Claude ($3/1M)
```

### 4. Contexte Adaptatif
```python
severity_to_budget = {
    "CRITICAL": ("critical", 600),  # Moins de tokens, qualité max
    "HIGH": ("high", 800),
    "MEDIUM": ("medium", 900),
    "LOW": ("low", 900)
}

employee.execute(
    task=task,
    context_severity=severity_to_budget[assessment["severity"]][0],
    context_budget=severity_to_budget[assessment["severity"]][1]
)
```

## Implémentation

### Classe NanoSelfAssessment

```python
class NanoSelfAssessment:
    """Nano évalue sa capacité à gérer une tâche"""

    def __init__(self, llm_client):
        self.llm = llm_client
        self.nano_model = "nano"

    def evaluate(self, task: str) -> Dict[str, Any]:
        """
        Évalue la tâche et décide si nano peut gérer

        Returns:
            {
                "confidence": "HIGH|MEDIUM|LOW",
                "severity": "CRITICAL|HIGH|MEDIUM|LOW",
                "can_handle_safely": bool,
                "best_employee": str,
                "reasoning": str
            }
        """
        prompt = SELF_ASSESSMENT_PROMPT.format(task=task)

        response = self.llm.chat(
            model=self.nano_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.1  # Très déterministe
        )

        # Parse JSON
        assessment = json.loads(response)

        # Validation: nano doit être conservateur
        if assessment["severity"] == "CRITICAL":
            assessment["can_handle_safely"] = False

        if assessment["confidence"] == "LOW":
            assessment["can_handle_safely"] = False

        return assessment
```

### Intégration dans Router

```python
class IntelligentRouter:
    """Route les tâches selon l'évaluation de nano"""

    def __init__(self, nano_assessment, employee_registry):
        self.nano_assessment = nano_assessment
        self.employees = employee_registry

    def route_task(self, task: str) -> Tuple[Agent, Dict]:
        """
        Route la tâche vers le bon employé

        Returns:
            (employee, execution_params)
        """
        # Phase 1: Nano évalue
        assessment = self.nano_assessment.evaluate(task)

        # Log l'évaluation
        log.info(f"Nano assessment: {assessment}")

        # Phase 2: Décision
        if assessment["can_handle_safely"]:
            # Nano peut gérer
            return (
                self.employees["nano"],
                {
                    "severity": TaskSeverity[assessment["severity"]],
                    "context_budget": 900,
                    "assessment": assessment
                }
            )

        else:
            # Déléguer au meilleur employé
            best = assessment["best_employee"]

            if best not in self.employees:
                # Fallback: escalade au CEO
                best = "ceo"

            # Ajuster le budget selon sévérité
            budget = self._get_budget_for_severity(assessment["severity"])

            return (
                self.employees[best],
                {
                    "severity": TaskSeverity[assessment["severity"]],
                    "context_budget": budget,
                    "assessment": assessment,
                    "delegated_from": "nano"
                }
            )

    def _get_budget_for_severity(self, severity: str) -> int:
        """Ajuste le budget de contexte selon sévérité"""
        budgets = {
            "CRITICAL": 600,  # Très strict, peu de tokens
            "HIGH": 800,
            "MEDIUM": 900,
            "LOW": 900
        }
        return budgets.get(severity, 900)
```

## Métriques de Succès

### Taux de Routing

```python
metrics = {
    "total_tasks": 100,
    "nano_handled": 75,      # 75% gérés par nano
    "delegated": 25,         # 25% délégués

    "nano_success_rate": 98%, # 98% de succès quand nano gère
    "delegate_success_rate": 95%, # 95% de succès quand délégué

    "avg_cost_nano": "$0.0001",
    "avg_cost_delegate": "$0.0015",
    "total_cost_saved": "$0.035"  # vs. tout au Claude
}
```

### Précision d'Évaluation

```python
# Vérifier si nano évalue correctement
validation = {
    "correct_self_handle": 72/75,  # 96% correct de garder
    "correct_delegate": 24/25,      # 96% correct de déléguer
    "false_positive": 3,            # Nano a gardé alors qu'il fallait déléguer
    "false_negative": 1             # Nano a délégué alors qu'il pouvait gérer
}
```

## Tests

### Test 1: Tâches Simples
```python
simple_tasks = [
    "Add a comment to function",
    "Rename variable x to count",
    "Format code according to PEP8"
]

for task in simple_tasks:
    assessment = nano.evaluate(task)
    assert assessment["can_handle_safely"] == True
    assert assessment["confidence"] == "HIGH"
```

### Test 2: Tâches Critiques
```python
critical_tasks = [
    "Fix authentication vulnerability",
    "Update payment processing",
    "Migrate database schema"
]

for task in critical_tasks:
    assessment = nano.evaluate(task)
    assert assessment["can_handle_safely"] == False
    assert assessment["severity"] == "CRITICAL"
```

### Test 3: Routing Correct
```python
task = "Redesign system architecture"
employee, params = router.route_task(task)

assert employee.name == "cto"
assert params["severity"] == TaskSeverity.CRITICAL
assert params["delegated_from"] == "nano"
```

## Prompt Optimal pour Nano

```
SYSTEM:
You are a fast, efficient AI assistant (nano model). Your role is to:
1. FIRST: Evaluate if you can handle the task SAFELY with HIGH confidence
2. If YES and task is LOW/MEDIUM severity: Execute it
3. If NO or HIGH/CRITICAL severity: Identify best qualified employee

Be CONSERVATIVE. When in doubt, delegate.

EVALUATION CRITERIA:

HIGH Confidence (you can handle):
- Simple CRUD operations
- Adding comments/documentation
- Basic validation
- Code formatting
- Simple configurations

LOW Confidence (must delegate):
- System architecture changes
- Security implementations
- Complex algorithms
- Database migrations
- Production deployments

SEVERITY Detection:
- CRITICAL: production, security, auth, payment, database migration
- HIGH: public API, core feature, user-facing
- MEDIUM: standard features, improvements
- LOW: refactoring, docs, tests

OUTPUT FORMAT (JSON only):
{
  "confidence": "HIGH|MEDIUM|LOW",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "can_handle_safely": true|false,
  "best_employee": "nano|ceo|cto|[role]",
  "reasoning": "brief explanation"
}

Remember: Better to delegate than to make a mistake on critical tasks.
```

## Conclusion

Ce système permet à nano de:
- ✅ **S'auto-évaluer** avant d'agir
- ✅ **Détecter la sévérité** automatiquement
- ✅ **Router intelligemment** vers le bon employé
- ✅ **Être conservateur** sur tâches critiques
- ✅ **Optimiser les coûts** (nano pour 75% des tâches)

**Résultat**: Système sûr, efficace et économique! 🚀
