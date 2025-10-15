# Code Execution Loop - Design Document

## Vision
Un système autonome qui développe, teste, et commit du code avec escalation intelligente entre tiers de modèles.

## Architecture Globale

```
┌─────────────────────────────────────────────────────────────┐
│                    CODE EXECUTION LOOP                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  User Request → Planner → Developer → Tester → Committer   │
│                               ↓          ↓                   │
│                            Success?   Failure?               │
│                               ↓          ↓                   │
│                          Commit+Push  Loop Detection        │
│                                          ↓                   │
│                                   Escalate Tier              │
│                                          ↓                   │
│                                   Retry or Report            │
└─────────────────────────────────────────────────────────────┘
```

## Composants

### 1. Developer Agent (Multi-Tier)

**Tier 1: DeepSeek-V3** (rapide, économique)
- Code simple et straightforward
- Refactoring basique
- Ajout de features standard

**Tier 2: Claude Sonnet 4.5** (intelligent, équilibré)
- Code complexe
- Architecture decisions
- Debugging difficile

**Tier 3: Claude Opus 4** (ultra-puissant, coûteux)
- Problèmes critiques résistants
- Refactoring massif
- Edge cases complexes

### 2. Tester Agent (Nano - Ultra-Optimisé)

**Responsabilités:**
- Exécuter tests unitaires
- Vérifier syntaxe (AST parsing)
- Analyse statique (optionnel)
- Détection d'erreurs de runtime
- Validation des imports

**Base Prompt (Excellence):**
```python
TESTER_AGENT_PROMPT = """
You are a NANO TESTER AGENT - Ultra-efficient code quality validator.

MISSION: Validate code changes with ZERO tolerance for errors.

CAPABILITIES:
1. Syntax Validation (AST parsing)
2. Import Resolution
3. Test Execution (pytest, unittest)
4. Runtime Error Detection
5. Performance Regression Detection

PROTOCOL:
1. Parse code with AST → Report syntax errors immediately
2. Verify all imports resolve → Report missing dependencies
3. Run existing tests → Report failures with exact line numbers
4. Check for obvious runtime errors (undefined vars, type mismatches)
5. Return structured result:

OUTPUT FORMAT (JSON only):
{
  "status": "pass" | "fail" | "warning",
  "syntax_errors": [],
  "import_errors": [],
  "test_failures": [
    {
      "test": "test_authenticate_user",
      "error": "AssertionError: Expected True, got False",
      "file": "tests/test_auth.py",
      "line": 42
    }
  ],
  "runtime_errors": [],
  "warnings": [],
  "confidence": 0.95,
  "recommendation": "pass_to_commit" | "fix_required" | "escalate_tier"
}

EFFICIENCY RULES:
- No explanations, only structured output
- Use fast checks first (syntax before tests)
- Fail fast on critical errors
- Max execution time: 30 seconds
- If timeout, return "warning" status

ESCALATION CRITERIA:
- 3+ syntax errors → escalate
- Same error 2x in a row → escalate
- Infinite loop detected → escalate
- Segfault/crash → escalate
"""
```

**Cost Analysis:**
- Nano tier: ~$0.0001 per test run
- Average loop: 2-3 test runs = $0.0003
- VS Manual testing time: priceless 💎

### 3. Loop Detection System

**Stratégies:**

#### A. Diff-Based Detection
```python
class LoopDetector:
    def __init__(self):
        self.history = []  # List[(git_diff, error_msg, tier)]

    def detect_loop(self, current_diff: str, current_error: str, tier: str) -> bool:
        """
        Détecte une boucle infinie:
        1. Même diff proposé 2x → LOOP
        2. Même erreur 3x de suite → LOOP
        3. Alternance entre 2 états (A→B→A→B) → LOOP
        4. Timeout global (30 min) → LOOP
        """
        # Check exact diff repetition
        if self.history and self.history[-1][0] == current_diff:
            return True  # Proposed same change twice

        # Check error repetition (3x threshold)
        recent_errors = [h[1] for h in self.history[-3:]]
        if len(recent_errors) == 3 and all(e == current_error for e in recent_errors):
            return True  # Same error 3 times

        # Check oscillation (A→B→A pattern)
        if len(self.history) >= 3:
            if (self.history[-3][0] == current_diff and
                self.history[-3][0] != self.history[-2][0]):
                return True  # Oscillating between states

        return False

    def add_attempt(self, diff: str, error: str, tier: str):
        """Enregistre une tentative"""
        self.history.append((diff, error, tier))
```

#### B. Semantic Similarity Detection
```python
class SemanticLoopDetector:
    def detect_semantic_loop(self, attempts: List[str]) -> bool:
        """
        Détecte des boucles sémantiques:
        - Modifications équivalentes mais différentes syntaxiquement
        - Utilise embeddings pour comparer similarité

        Example:
        Attempt 1: "def foo(x): return x + 1"
        Attempt 2: "def foo(x): return 1 + x"  # Same semantically
        → LOOP detected
        """
        if len(attempts) < 2:
            return False

        # Compare last 2 attempts via embedding similarity
        emb1 = create_embedding(attempts[-1])
        emb2 = create_embedding(attempts[-2])
        similarity = cosine_similarity(emb1, emb2)

        return similarity > 0.95  # 95% similar = likely same intent
```

### 4. Escalation System

**Workflow:**

```python
class EscalationSystem:
    TIERS = [
        ModelTier.DEEPSEEK,   # Tier 1: Fast & cheap
        ModelTier.CLAUDE,     # Tier 2: Smart & balanced
        # ModelTier.OPUS,     # Tier 3: Ultimate (si disponible)
    ]

    MAX_ATTEMPTS_PER_TIER = 3

    def execute_with_escalation(self, task: str) -> ExecutionResult:
        """
        Boucle principale avec escalation

        1. Start with Tier 1 (DeepSeek)
        2. Developer codes → Tester validates
        3. If success → Commit + Push
        4. If failure → Retry (max 3x)
        5. If loop detected → Escalate to Tier 2
        6. Repeat steps 2-5 for Tier 2
        7. If Tier 2 loops → Final report + last commit
        """
        for tier_idx, tier in enumerate(self.TIERS):
            print(f"🚀 Starting Tier {tier_idx + 1}: {tier.value}")

            for attempt in range(self.MAX_ATTEMPTS_PER_TIER):
                print(f"  Attempt {attempt + 1}/{self.MAX_ATTEMPTS_PER_TIER}")

                # Developer codes
                code_result = self.developer.code(task, tier=tier)

                # Tester validates
                test_result = self.tester.test(code_result.files)

                if test_result.status == "pass":
                    # SUCCESS! Commit and push
                    self.committer.commit_and_push(
                        files=code_result.files,
                        message=f"feat: {task} (Tier {tier.value}, attempt {attempt + 1})"
                    )
                    return ExecutionResult(success=True, tier=tier, attempts=attempt+1)

                # Check for loop
                if self.loop_detector.detect_loop(
                    current_diff=code_result.diff,
                    current_error=test_result.error,
                    tier=tier.value
                ):
                    print(f"  ⚠️  Loop detected on Tier {tier_idx + 1}")
                    break  # Escalate to next tier

            # Tier exhausted or loop detected → Escalate

        # All tiers exhausted
        return self.create_final_report()

    def create_final_report(self) -> ExecutionResult:
        """
        Génère un rapport final si tous les tiers échouent

        Contenu:
        - Historique de toutes les tentatives
        - Erreurs rencontrées
        - Diffs proposés
        - Recommandations pour intervention manuelle
        - Last commit (état partiel si applicable)
        """
        report = {
            "status": "failed_after_all_escalations",
            "total_attempts": len(self.loop_detector.history),
            "tiers_used": [h[2] for h in self.loop_detector.history],
            "unique_errors": list(set(h[1] for h in self.loop_detector.history)),
            "last_diff": self.loop_detector.history[-1][0],
            "recommendation": "Manual intervention required"
        }

        # Commit partial work if any
        if self.has_partial_progress():
            self.committer.commit_and_push(
                message=f"WIP: {task} (failed after escalation, needs manual review)"
            )

        return ExecutionResult(success=False, report=report)
```

### 5. Commit Strategy

**Options:**

#### Option A: Feature Branch (Recommandé pour safety)
```python
class FeatureBranchStrategy:
    def start_task(self, task: str):
        """Create feature branch for task"""
        branch_name = f"feature/{slugify(task)}"
        git.checkout("-b", branch_name)

    def commit_attempt(self, attempt: int, tier: str):
        """Commit each successful attempt"""
        git.add(".")
        git.commit("-m", f"feat: attempt {attempt} with {tier}")

    def finalize_success(self):
        """Merge back to main on success"""
        git.checkout("main")
        git.merge("--squash", self.branch_name)
        git.commit("-m", f"feat: {self.task}")
        git.push()

    def finalize_failure(self):
        """Keep branch for manual review"""
        git.push("-u", "origin", self.branch_name)
        # Create PR with report
```

#### Option B: Direct Commits (Plus rapide)
```python
class DirectCommitStrategy:
    def commit_on_success(self, tier: str, attempt: int):
        """Commit directly to main"""
        git.add(".")
        git.commit("-m", f"feat: {task} (Tier {tier}, attempt {attempt})")
        git.push()

    def commit_partial_on_failure(self):
        """Commit WIP if partial progress"""
        git.add(".")
        git.commit("-m", f"WIP: {task} (needs manual review)")
        git.push()
```

**Recommandation:** Option A pour production, Option B pour prototypage rapide

### 6. Tester Agent Implementation

**Tests à Exécuter:**

```python
class TesterAgent:
    """Nano agent pour validation ultra-rapide"""

    def test_syntax(self, filepath: str) -> TestResult:
        """Parse avec AST pour vérifier syntaxe"""
        try:
            with open(filepath) as f:
                ast.parse(f.read())
            return TestResult(passed=True)
        except SyntaxError as e:
            return TestResult(
                passed=False,
                error=f"Syntax error at line {e.lineno}: {e.msg}"
            )

    def test_imports(self, filepath: str) -> TestResult:
        """Vérifie que tous les imports se résolvent"""
        try:
            # Use importlib to check imports
            spec = importlib.util.spec_from_file_location("module", filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return TestResult(passed=True)
        except ImportError as e:
            return TestResult(
                passed=False,
                error=f"Import error: {e}"
            )

    def run_tests(self, test_files: List[str]) -> TestResult:
        """Exécute pytest sur les tests existants"""
        result = subprocess.run(
            ["pytest", "-v", "--tb=short"] + test_files,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return TestResult(passed=True)
        else:
            # Parse pytest output for failures
            failures = self._parse_pytest_output(result.stdout)
            return TestResult(
                passed=False,
                error="Tests failed",
                details=failures
            )

    def validate_code(self, filepaths: List[str]) -> ValidationReport:
        """
        Validation complète:
        1. Syntax check (fast)
        2. Import check (medium)
        3. Run tests (slower)
        """
        report = ValidationReport()

        # Fast checks first (fail fast)
        for filepath in filepaths:
            syntax_result = self.test_syntax(filepath)
            if not syntax_result.passed:
                report.add_error(syntax_result)
                return report  # Fail fast on syntax

            import_result = self.test_imports(filepath)
            if not import_result.passed:
                report.add_error(import_result)
                return report  # Fail fast on imports

        # Run full test suite
        test_result = self.run_tests(self._find_test_files(filepaths))
        if not test_result.passed:
            report.add_error(test_result)

        return report
```

## Réponses à Vos Questions

### Q: "Est-ce que ça fait du sens?"
**R: OUI, absolument! 🎯**

Votre architecture est:
- ✅ **Cost-effective**: Nano pour tests, escalation seulement si nécessaire
- ✅ **Safe**: Commits après validation, rollback possible
- ✅ **Intelligent**: Détection de boucles évite waste
- ✅ **Scalable**: Peut ajouter plus de tiers si besoin

### Q: "Des recommandations?"

1. **Start Simple**
   - Phase 1: DeepSeek → Nano Tester → Commit
   - Phase 2: Ajouter escalation Claude
   - Phase 3: Ajouter détection de boucles sémantiques

2. **Metrics to Track**
   - Success rate par tier (DeepSeek vs Claude)
   - Average attempts before success
   - Cost per successful task
   - Time saved vs manual coding

3. **Safety Nets**
   - Backup avant chaque modification
   - Branch protection sur main (require PR)
   - Max budget par tâche ($1.00 par exemple)
   - Timeout global (30 min)

4. **Testing Strategy**
   - Commencer avec tests simples (syntax only)
   - Ajouter tests unitaires progressivement
   - Éviter tests lents (>10s) dans la boucle

### Q: "Des doutes?"

1. **GPT-5 n'existe pas encore**
   - Utiliser GPT-4o ou DeepSeek-V3 comme Tier 1
   - Claude Sonnet 4.5 comme Tier 2
   - Claude Opus 4 comme Tier 3 (si critique)

2. **Définition de "Loop"**
   - À affiner avec des vraies expériences
   - Peut-être 3 essais au lieu de 2 pour éviter faux positifs

3. **Partial Work Commit**
   - Quand committer du travail partiel?
   - Risque de polluer l'historique git
   - Solution: Utiliser branches + tags "WIP"

4. **Tests Flaky**
   - Certains tests peuvent être non-déterministes
   - Stratégie: Re-run failed tests 1x avant de fail

## Exemple de Flow Complet

```python
# User Request
task = "Add rate limiting to API endpoints"

# Execution Loop starts
loop = CodeExecutionLoop()

# Tier 1: DeepSeek
developer = DeveloperAgent(tier=ModelTier.DEEPSEEK)
code = developer.code(task)
# → Modifie cortex/api/endpoints.py
# → Ajoute rate_limiter decorator

tester = TesterAgent(tier=ModelTier.NANO)
result = tester.test(["cortex/api/endpoints.py"])
# → Status: FAIL
# → Error: "ImportError: No module named 'ratelimit'"

# Attempt 2: Developer fixes import
code = developer.fix(result.error)
result = tester.test(["cortex/api/endpoints.py"])
# → Status: FAIL
# → Error: "Test test_rate_limit_exceeded failed"

# Attempt 3: Developer fixes test
code = developer.fix(result.error)
result = tester.test(["cortex/api/endpoints.py"])
# → Status: FAIL (same error)

# Loop detected! (same error 2x)
loop.escalate_tier()

# Tier 2: Claude Sonnet
developer = DeveloperAgent(tier=ModelTier.CLAUDE)
code = developer.code(task, context=loop.get_history())
# → Claude analyze previous attempts
# → Identifies root cause: logic error in rate limiter

result = tester.test(["cortex/api/endpoints.py"])
# → Status: PASS ✓

# Success! Commit and push
committer.commit_and_push(
    files=["cortex/api/endpoints.py", "tests/test_api.py"],
    message="feat: Add rate limiting to API endpoints"
)

# Execution Loop complete
# Total cost: $0.015 (3x DeepSeek + 1x Claude + 4x Nano)
# Total time: 2 minutes
# Result: ✓ Working feature committed
```

## Prochaines Étapes

1. ✅ Implémenter DeveloperAgent multi-tier
2. ✅ Créer TesterAgent avec nano prompt optimisé
3. ✅ Développer LoopDetector (diff-based + semantic)
4. ✅ Implémenter EscalationSystem
5. ✅ Créer CommitStrategy (feature branch vs direct)
6. ✅ Intégrer dans Cortex CLI
7. ✅ Tests sur vraies tâches du projet
8. ✅ Mesurer success rate et cost savings
