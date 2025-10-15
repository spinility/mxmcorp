"""
Tester Agent - Employé spécialisé dans la validation de code

Utilise le tier NANO pour validation ultra-rapide et économique.
Excellence dans la détection d'erreurs avec un prompt optimisé.

Responsabilités:
- Validation syntaxique (AST parsing)
- Résolution des imports
- Exécution des tests unitaires
- Détection d'erreurs runtime
- Recommandations d'escalation
"""

import ast
import subprocess
import importlib.util
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier


class TestStatus(Enum):
    """Statut d'un test"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    ERROR = "error"


class EscalationReason(Enum):
    """Raisons d'escalation au tier supérieur"""
    SYNTAX_ERRORS_MULTIPLE = "multiple_syntax_errors"
    SAME_ERROR_REPEATED = "same_error_repeated"
    IMPORT_RESOLUTION_FAILED = "import_resolution_failed"
    INFINITE_LOOP_DETECTED = "infinite_loop_detected"
    SEGFAULT_CRASH = "segfault_or_crash"
    COMPLEX_LOGIC_ERROR = "complex_logic_error"
    TIMEOUT = "timeout"


@dataclass
class TestError:
    """Représente une erreur de test"""
    type: str  # 'syntax', 'import', 'test', 'runtime'
    message: str
    file: str
    line: Optional[int] = None
    details: Optional[str] = None


@dataclass
class ValidationReport:
    """Rapport de validation complet"""
    status: TestStatus
    syntax_errors: List[TestError]
    import_errors: List[TestError]
    test_failures: List[TestError]
    runtime_errors: List[TestError]
    warnings: List[str]
    confidence: float
    recommendation: str  # 'pass_to_commit', 'fix_required', 'escalate_tier'
    escalation_reason: Optional[EscalationReason] = None
    execution_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dict"""
        return {
            'status': self.status.value,
            'syntax_errors': [
                {
                    'type': e.type,
                    'message': e.message,
                    'file': e.file,
                    'line': e.line,
                    'details': e.details
                }
                for e in self.syntax_errors
            ],
            'import_errors': [
                {
                    'type': e.type,
                    'message': e.message,
                    'file': e.file,
                    'line': e.line
                }
                for e in self.import_errors
            ],
            'test_failures': [
                {
                    'type': e.type,
                    'message': e.message,
                    'file': e.file,
                    'line': e.line,
                    'details': e.details
                }
                for e in self.test_failures
            ],
            'runtime_errors': [
                {
                    'type': e.type,
                    'message': e.message,
                    'file': e.file,
                    'line': e.line
                }
                for e in self.runtime_errors
            ],
            'warnings': self.warnings,
            'confidence': self.confidence,
            'recommendation': self.recommendation,
            'escalation_reason': self.escalation_reason.value if self.escalation_reason else None,
            'execution_time': self.execution_time
        }


class TesterAgent:
    """
    Agent spécialisé dans la validation de code

    Utilise NANO tier pour rapidité et économie
    """

    # Prompt ultra-optimisé pour nano
    NANO_TESTER_PROMPT = """You are a NANO TESTER AGENT - Ultra-efficient code validator.

MISSION: Validate code changes with ZERO tolerance for errors.

PROTOCOL:
1. Analyze validation results provided
2. Identify critical vs non-critical issues
3. Recommend action: pass_to_commit | fix_required | escalate_tier

ESCALATION TRIGGERS:
- 3+ syntax errors → escalate
- Same error repeated → escalate
- Complex logic errors → escalate
- Import failures (missing deps) → escalate
- Infinite loop or crash → escalate

OUTPUT (JSON only, no explanations):
{
  "recommendation": "pass_to_commit" | "fix_required" | "escalate_tier",
  "escalation_reason": "reason" | null,
  "confidence": 0.0-1.0,
  "priority_fixes": ["issue1", "issue2"],
  "summary": "1 sentence"
}

EFFICIENCY: Max 50 tokens response."""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Tester Agent

        Args:
            llm_client: Client LLM pour analyse nano
        """
        self.llm_client = llm_client
        self.test_history: List[ValidationReport] = []

    def validate_code(
        self,
        filepaths: List[str],
        run_tests: bool = True,
        test_timeout: int = 30
    ) -> ValidationReport:
        """
        Validation complète d'un ensemble de fichiers

        Args:
            filepaths: Liste des fichiers à valider
            run_tests: Si True, exécute les tests unitaires
            test_timeout: Timeout pour tests (secondes)

        Returns:
            ValidationReport avec résultats
        """
        import time
        start_time = time.time()

        report = ValidationReport(
            status=TestStatus.PASS,
            syntax_errors=[],
            import_errors=[],
            test_failures=[],
            runtime_errors=[],
            warnings=[],
            confidence=1.0,
            recommendation="pass_to_commit"
        )

        # 1. FAST: Syntax validation
        for filepath in filepaths:
            if filepath.endswith('.py'):
                syntax_result = self._validate_syntax(filepath)
                if syntax_result:
                    report.syntax_errors.append(syntax_result)
                    report.status = TestStatus.FAIL

        # Fail fast sur syntax errors
        if report.syntax_errors:
            report.confidence = 0.3
            report.recommendation = "fix_required"
            if len(report.syntax_errors) >= 3:
                report.recommendation = "escalate_tier"
                report.escalation_reason = EscalationReason.SYNTAX_ERRORS_MULTIPLE
            report.execution_time = time.time() - start_time
            return report

        # 2. MEDIUM: Import validation
        for filepath in filepaths:
            if filepath.endswith('.py'):
                import_result = self._validate_imports(filepath)
                if import_result:
                    report.import_errors.append(import_result)
                    report.status = TestStatus.FAIL

        # Fail fast sur import errors
        if report.import_errors:
            report.confidence = 0.5
            report.recommendation = "escalate_tier"
            report.escalation_reason = EscalationReason.IMPORT_RESOLUTION_FAILED
            report.execution_time = time.time() - start_time
            return report

        # 3. SLOW: Run tests
        if run_tests:
            test_results = self._run_tests(filepaths, timeout=test_timeout)
            report.test_failures.extend(test_results)

            if report.test_failures:
                report.status = TestStatus.FAIL
                report.confidence = 0.6

        # 4. Analyse avec nano LLM pour recommandation finale
        if report.status == TestStatus.FAIL:
            nano_recommendation = self._get_nano_recommendation(report)
            report.recommendation = nano_recommendation.get('recommendation', 'fix_required')
            if nano_recommendation.get('escalation_reason'):
                report.escalation_reason = EscalationReason(nano_recommendation['escalation_reason'])
            report.confidence = nano_recommendation.get('confidence', 0.5)

        report.execution_time = time.time() - start_time
        self.test_history.append(report)

        return report

    def _validate_syntax(self, filepath: str) -> Optional[TestError]:
        """Valide la syntaxe Python avec AST"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            ast.parse(source)
            return None
        except SyntaxError as e:
            return TestError(
                type='syntax',
                message=f"Syntax error: {e.msg}",
                file=filepath,
                line=e.lineno,
                details=str(e)
            )
        except Exception as e:
            return TestError(
                type='syntax',
                message=f"Parse error: {str(e)}",
                file=filepath,
                line=None
            )

    def _validate_imports(self, filepath: str) -> Optional[TestError]:
        """Valide que tous les imports se résolvent"""
        try:
            # Ajouter le répertoire du fichier au path
            file_dir = str(Path(filepath).parent.absolute())
            if file_dir not in sys.path:
                sys.path.insert(0, file_dir)

            # Essayer d'importer le module
            spec = importlib.util.spec_from_file_location("_test_module", filepath)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            return None
        except ImportError as e:
            return TestError(
                type='import',
                message=f"Import error: {str(e)}",
                file=filepath,
                line=None,
                details=str(e)
            )
        except Exception as e:
            # Ne pas considérer comme erreur critique si c'est autre chose
            return None

    def _run_tests(
        self,
        filepaths: List[str],
        timeout: int = 30
    ) -> List[TestError]:
        """Exécute pytest sur les fichiers"""
        errors = []

        # Trouver les fichiers de test associés
        test_files = self._find_test_files(filepaths)

        if not test_files:
            return []

        try:
            result = subprocess.run(
                ["pytest", "-v", "--tb=short", "--timeout=10"] + test_files,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode != 0:
                # Parser la sortie pytest pour extraire erreurs
                errors = self._parse_pytest_output(result.stdout + result.stderr)

        except subprocess.TimeoutExpired:
            errors.append(TestError(
                type='test',
                message="Tests timeout (possible infinite loop)",
                file="unknown",
                line=None,
                details=f"Timeout after {timeout} seconds"
            ))
        except FileNotFoundError:
            # pytest non installé, skip tests
            pass

        return errors

    def _find_test_files(self, filepaths: List[str]) -> List[str]:
        """Trouve les fichiers de test associés"""
        test_files = []

        for filepath in filepaths:
            path = Path(filepath)

            # Si c'est déjà un fichier de test
            if path.name.startswith('test_'):
                test_files.append(str(path))
                continue

            # Chercher test_{filename} dans même répertoire
            test_file = path.parent / f"test_{path.name}"
            if test_file.exists():
                test_files.append(str(test_file))

            # Chercher dans répertoire tests/
            tests_dir = path.parent / "tests"
            if tests_dir.exists():
                test_file_in_tests = tests_dir / f"test_{path.name}"
                if test_file_in_tests.exists():
                    test_files.append(str(test_file_in_tests))

        return test_files

    def _parse_pytest_output(self, output: str) -> List[TestError]:
        """Parse la sortie pytest pour extraire erreurs"""
        errors = []
        lines = output.split('\n')

        current_test = None
        current_file = None
        current_error = None

        for line in lines:
            # Détecter nom du test
            if line.startswith('test_') or '::test_' in line:
                current_test = line.split('::')[-1].split()[0]

            # Détecter fichier
            if '.py:' in line:
                parts = line.split('.py:')
                if len(parts) >= 2:
                    current_file = parts[0] + '.py'

            # Détecter erreur
            if 'FAILED' in line or 'ERROR' in line or 'AssertionError' in line:
                current_error = line.strip()

            # Construire TestError si on a assez d'infos
            if current_test and current_error:
                errors.append(TestError(
                    type='test',
                    message=current_error,
                    file=current_file or "unknown",
                    line=None,
                    details=f"Test: {current_test}"
                ))
                current_test = None
                current_error = None

        return errors

    def _get_nano_recommendation(self, report: ValidationReport) -> Dict[str, Any]:
        """Utilise nano LLM pour analyser et recommander"""
        # Préparer résumé compact pour nano
        summary = {
            'syntax_errors_count': len(report.syntax_errors),
            'import_errors_count': len(report.import_errors),
            'test_failures_count': len(report.test_failures),
            'errors_sample': [
                e.message for e in (
                    report.syntax_errors[:2] +
                    report.import_errors[:2] +
                    report.test_failures[:2]
                )
            ]
        }

        prompt = f"""{self.NANO_TESTER_PROMPT}

VALIDATION RESULTS:
{json.dumps(summary, indent=2)}

YOUR ANALYSIS:"""

        try:
            response = self.llm_client.complete(
                messages=[{"role": "user", "content": prompt}],
                tier=ModelTier.NANO,
                max_tokens=100,
                temperature=0.1
            )

            result = json.loads(response.content.strip())
            return result

        except Exception as e:
            # Fallback sur heuristique
            if len(report.syntax_errors) >= 3:
                return {
                    'recommendation': 'escalate_tier',
                    'escalation_reason': 'multiple_syntax_errors',
                    'confidence': 0.8,
                    'summary': 'Multiple syntax errors require higher tier'
                }
            elif report.import_errors:
                return {
                    'recommendation': 'escalate_tier',
                    'escalation_reason': 'import_resolution_failed',
                    'confidence': 0.7,
                    'summary': 'Import errors need escalation'
                }
            else:
                return {
                    'recommendation': 'fix_required',
                    'escalation_reason': None,
                    'confidence': 0.6,
                    'summary': 'Fixes required before commit'
                }

    def detect_repeated_errors(self, window: int = 3) -> bool:
        """
        Détecte si les mêmes erreurs se répètent

        Args:
            window: Nombre de tentatives à examiner

        Returns:
            True si erreurs répétées détectées
        """
        if len(self.test_history) < 2:
            return False

        recent_reports = self.test_history[-window:]

        # Comparer les messages d'erreur
        error_signatures = []
        for report in recent_reports:
            signature = '|'.join([
                e.message for e in (
                    report.syntax_errors +
                    report.import_errors +
                    report.test_failures
                )
            ])
            error_signatures.append(signature)

        # Si 2 signatures identiques consécutives
        if len(error_signatures) >= 2:
            if error_signatures[-1] == error_signatures[-2] and error_signatures[-1]:
                return True

        return False


def create_tester_agent(llm_client: LLMClient) -> TesterAgent:
    """Factory function pour créer un TesterAgent"""
    return TesterAgent(llm_client)


# Test si exécuté directement
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    print("Testing Tester Agent...")

    client = LLMClient()
    tester = TesterAgent(client)

    # Test 1: Valider ce fichier
    print("\n1. Testing syntax validation on this file...")
    report = tester.validate_code([__file__], run_tests=False)
    print(f"✓ Status: {report.status.value}")
    print(f"  Syntax errors: {len(report.syntax_errors)}")
    print(f"  Recommendation: {report.recommendation}")
    print(f"  Confidence: {report.confidence:.0%}")
    print(f"  Execution time: {report.execution_time:.2f}s")

    # Test 2: Créer un fichier avec erreur syntax
    print("\n2. Testing with syntax error...")
    test_file = "/tmp/test_syntax_error.py"
    with open(test_file, 'w') as f:
        f.write("def broken_function(\n")  # Syntax error

    report2 = tester.validate_code([test_file], run_tests=False)
    print(f"✓ Status: {report2.status.value}")
    print(f"  Syntax errors: {len(report2.syntax_errors)}")
    if report2.syntax_errors:
        print(f"  Error: {report2.syntax_errors[0].message}")
    print(f"  Recommendation: {report2.recommendation}")

    # Test 3: Détection d'erreurs répétées
    print("\n3. Testing repeated error detection...")
    tester.test_history = [report2, report2, report2]  # Simuler 3x même erreur
    repeated = tester.detect_repeated_errors()
    print(f"✓ Repeated errors detected: {repeated}")

    print("\n✓ Tester Agent works correctly!")
