"""
Tester Agent - Détermine intelligemment si des tests sont nécessaires

ROLE: QUALITY_ASSURANCE (Analyse + Validation) - Niveau 2 de la hiérarchie
TIER: DEEPSEEK pour analyse intelligente des besoins de tests

WORKFLOW:
1. Reçoit notification de changements (via MaintenanceAgent ou workflow)
2. Analyse avec base_prompt: détermine si tests nécessaires selon logique
3. Vérifie si tests requis existent déjà
4. Si manquants, requête ToolerAgent pour création
5. BONUS: Peut aussi valider/exécuter tests existants

Logique de décision (base_prompt):
- Nouvelle fonction/classe → Test requis
- Bug fix → Test de régression requis
- Refactoring → Vérifier tests existants
- Documentation → Pas de test requis
- Config/paramètres → Test d'intégration possible
- API endpoint → Test d'intégration requis
- Database schema → Test de migration requis

Déclenché:
- Par MaintenanceAgent après exécution de plan d'harmonisation
- Manuellement via CLI
- Par git_integration_workflow si testing_required=True
"""

import ast
import subprocess
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from cortex.core.llm_client import LLMClient, ModelTier
from cortex.core.agent_hierarchy import DecisionAgent, AgentRole, AgentResult, EscalationContext
from cortex.core.agent_memory import get_agent_memory
from cortex.repositories.changelog_repository import get_changelog_repository
from cortex.repositories.file_repository import get_file_repository


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


class TesterAgent(DecisionAgent):
    """
    Tester Agent - Niveau DECISION (Quality Assurance) dans la hiérarchie

    Hérite de DecisionAgent pour intégration dans le système hiérarchique.
    Spécialisation: Analyse des besoins en tests et validation.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Tester Agent

        Args:
            llm_client: Client LLM pour analyse (DEEPSEEK tier)
        """
        # Initialiser DecisionAgent avec spécialisation "testing"
        super().__init__(llm_client, specialization="testing")
        self.test_history: List[ValidationReport] = []
        self.memory = get_agent_memory('optimization', 'tester')

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """
        Évalue si le TesterAgent peut gérer la requête

        Override ExecutionAgent.can_handle() avec logique spécifique
        """
        # Patterns spécifiques aux tests
        test_patterns = [
            'test', 'validate', 'check', 'verify',
            'syntax', 'import', 'pytest', 'unittest'
        ]

        request_lower = request.lower()
        matches = sum(1 for pattern in test_patterns if pattern in request_lower)

        # Base confidence from matches
        confidence = min(matches / 2.0, 1.0)

        # Boost if context contains filepaths
        if context and 'filepaths' in context:
            confidence = min(confidence + 0.2, 1.0)

        return confidence

    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[EscalationContext] = None
    ) -> AgentResult:
        """
        Exécute l'analyse des besoins en tests

        Nouveau workflow:
        1. Analyser changed_files pour déterminer si tests nécessaires (base_prompt logic)
        2. Vérifier si tests existent
        3. Requêter ToolerAgent si tests manquants
        4. (Bonus) Peut aussi valider/exécuter tests existants

        Args:
            request: Requête utilisateur
            context: Dict avec 'changed_files' ou 'filepaths'
            escalation_context: Contexte si escalation

        Returns:
            AgentResult avec analyse des tests
        """
        # Extraire changed_files ou filepaths du contexte
        changed_files = context.get('changed_files', []) if context else []
        filepaths = context.get('filepaths', []) if context else []
        plan = context.get('harmonization_plan') if context else None
        run_validation = context.get('run_validation', False) if context else False

        # Convertir filepaths en changed_files format si nécessaire
        if not changed_files and filepaths:
            changed_files = [{'path': fp, 'change_type': 'modified'} for fp in filepaths]

        if not changed_files and not plan:
            return AgentResult(
                success=False,
                role=self.role,
                tier=self.tier,
                content={'error': 'No changed files or plan provided'},
                cost=0.0,
                confidence=0.0,
                should_escalate=False,
                error='Insufficient context for test analysis'
            )

        # Analyser les besoins en tests (base_prompt logic)
        analysis = self.analyze_test_requirements(changed_files, plan)

        # Si run_validation=True, exécuter aussi la validation
        if run_validation and analysis.get('existing_tests'):
            test_files = [t['expected_test_path'] for t in analysis['existing_tests']]
            validation_report = self.validate_code(test_files, run_tests=True, test_timeout=30)
            analysis['validation_report'] = validation_report.to_dict()

        return AgentResult(
            success=analysis['success'],
            role=self.role,
            tier=self.tier,
            content=analysis,
            cost=analysis.get('cost', 0.0),
            confidence=0.85,
            should_escalate=False,
            escalation_reason=None,
            error=analysis.get('error'),
            metadata={'test_analysis': analysis}
        )

    def analyze_test_requirements(
        self,
        changed_files: List[Dict[str, Any]],
        plan: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyse intelligente des besoins en tests basée sur base_prompt logic

        Args:
            changed_files: Liste des fichiers modifiés avec path et change_type
            plan: Plan d'harmonisation optionnel

        Returns:
            Dict avec:
                - tests_required: Boolean
                - required_tests: Liste des tests nécessaires
                - existing_tests: Liste des tests existants
                - missing_tests: Liste des tests manquants
                - test_requests: Requêtes pour ToolerAgent
        """
        start_time = time.time()

        try:
            changelog_repo = get_changelog_repository()

            print(f"\n{'='*70}")
            print(f"🧪 TESTER AGENT - Test Requirements Analysis")
            print(f"{'='*70}")
            print(f"Analyzing {len(changed_files)} changed files\n")

            required_tests = []
            existing_tests = []
            missing_tests = []
            test_requests = []

            # Analyser chaque fichier avec base_prompt logic
            for file_info in changed_files:
                file_path = file_info.get('path', file_info.get('file_path', ''))
                change_type = file_info.get('change_type', 'modified')

                print(f"Analyzing: {file_path} ({change_type})")

                # Base prompt logic: déterminer si test nécessaire
                test_needed = self._determine_test_needed(file_path, change_type, file_info)

                if test_needed['required']:
                    test_type = test_needed['test_type']
                    rationale = test_needed['rationale']

                    print(f"  → Test required: {test_type}")
                    print(f"     Rationale: {rationale}")

                    # Construire le chemin du test attendu
                    expected_test_path = self._get_expected_test_path(file_path)

                    required_test = {
                        'source_file': file_path,
                        'test_type': test_type,
                        'expected_test_path': expected_test_path,
                        'rationale': rationale,
                        'priority': test_needed.get('priority', 'medium')
                    }

                    required_tests.append(required_test)

                    # Vérifier si le test existe
                    if self._test_exists(expected_test_path):
                        existing_tests.append(required_test)
                        print(f"  ✓ Test exists: {expected_test_path}")
                    else:
                        missing_tests.append(required_test)
                        print(f"  ✗ Test missing: {expected_test_path}")

                        # Créer une requête pour ToolerAgent
                        test_request = {
                            'action': 'create_test',
                            'source_file': file_path,
                            'test_file': expected_test_path,
                            'test_type': test_type,
                            'rationale': rationale,
                            'priority': test_needed.get('priority', 'medium')
                        }
                        test_requests.append(test_request)

                else:
                    print(f"  → No test required: {test_needed['rationale']}")

            # Log l'analyse dans changelog
            changelog_repo.log_change(
                change_type='test_analysis',
                entity_type='test_requirements',
                author='TesterAgent',
                description=f"Analyzed {len(changed_files)} files: {len(required_tests)} tests required, {len(missing_tests)} missing",
                impact_level='medium',
                metadata={
                    'files_analyzed': len(changed_files),
                    'tests_required': len(required_tests),
                    'tests_existing': len(existing_tests),
                    'tests_missing': len(missing_tests)
                }
            )

            print(f"\n{'='*70}")
            print(f"Test Analysis Summary:")
            print(f"  Required: {len(required_tests)}")
            print(f"  Existing: {len(existing_tests)}")
            print(f"  Missing: {len(missing_tests)}")
            print(f"  Requests for ToolerAgent: {len(test_requests)}")
            print(f"{'='*70}\n")

            duration = time.time() - start_time

            result = {
                'success': True,
                'action': 'analyze_test_requirements',
                'tests_required': len(required_tests) > 0,
                'required_tests': required_tests,
                'existing_tests': existing_tests,
                'missing_tests': missing_tests,
                'test_requests': test_requests,
                'coverage_status': 'complete' if len(missing_tests) == 0 else 'incomplete',
                'cost': 0.0  # Base prompt logic, no LLM call
            }

            # Enregistrer dans la mémoire
            self.memory.record_execution(
                request=f"Analyze test requirements for {len(changed_files)} files",
                result=result,
                duration=duration,
                cost=0.0
            )

            # Mettre à jour l'état
            self.memory.update_state({
                'last_analysis_timestamp': datetime.now().isoformat(),
                'total_tests_required': len(required_tests),
                'total_tests_missing': len(missing_tests),
                'coverage_status': result['coverage_status']
            })

            # Détecter patterns dans les types de tests requis
            for test in required_tests:
                test_type = test.get('test_type')
                priority = test.get('priority')
                self.memory.add_pattern(
                    f'test_type_{test_type}',
                    {
                        'type': test_type,
                        'priority': priority,
                        'rationale': test.get('rationale')
                    }
                )

            return result

        except Exception as e:
            duration = time.time() - start_time

            error_result = {
                'success': False,
                'action': 'analyze_test_requirements',
                'error': f"Test analysis failed: {str(e)}",
                'cost': 0.0
            }

            # Enregistrer l'échec dans la mémoire
            self.memory.record_execution(
                request=f"Analyze test requirements (failed)",
                result=error_result,
                duration=duration,
                cost=0.0
            )

            return error_result

    def _determine_test_needed(
        self,
        file_path: str,
        change_type: str,
        file_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        BASE PROMPT LOGIC: Détermine si un test est nécessaire

        Cette logique est basée sur des règles claires et explicites,
        pas sur un appel LLM. C'est la "base_prompt" logic.

        Args:
            file_path: Chemin du fichier
            change_type: Type de changement (added, modified, deleted)
            file_info: Informations supplémentaires

        Returns:
            Dict avec:
                - required: Boolean
                - test_type: Type de test si requis
                - rationale: Explication
                - priority: 'high', 'medium', 'low'
        """
        # Test files themselves don't need tests
        if 'test_' in file_path or '/tests/' in file_path:
            return {
                'required': False,
                'test_type': None,
                'rationale': 'Test file - no test required',
                'priority': None
            }

        # Documentation files don't need tests
        if file_path.endswith(('.md', '.txt', '.rst', '.pdf')):
            return {
                'required': False,
                'test_type': None,
                'rationale': 'Documentation file - no test required',
                'priority': None
            }

        # Config files might need integration tests
        if file_path.endswith(('.yaml', '.yml', '.json', '.toml', '.ini', '.cfg')):
            return {
                'required': True,
                'test_type': 'integration',
                'rationale': 'Config file change - integration test recommended',
                'priority': 'low'
            }

        # Python files: check content type
        if file_path.endswith('.py'):
            # Agent files need tests
            if '/agents/' in file_path:
                return {
                    'required': True,
                    'test_type': 'unit',
                    'rationale': 'Agent implementation - unit tests required',
                    'priority': 'high'
                }

            # Core modules need tests
            if '/core/' in file_path:
                return {
                    'required': True,
                    'test_type': 'unit',
                    'rationale': 'Core module - unit tests required',
                    'priority': 'high'
                }

            # Repository layer needs tests
            if '/repositories/' in file_path:
                return {
                    'required': True,
                    'test_type': 'integration',
                    'rationale': 'Repository layer - integration tests required',
                    'priority': 'high'
                }

            # Tools need tests
            if '/tools/' in file_path:
                return {
                    'required': True,
                    'test_type': 'unit',
                    'rationale': 'Tool implementation - unit tests required',
                    'priority': 'medium'
                }

            # Utilities need tests
            if '/utils/' in file_path:
                return {
                    'required': True,
                    'test_type': 'unit',
                    'rationale': 'Utility function - unit tests required',
                    'priority': 'medium'
                }

            # Database-related files need tests
            if 'database' in file_path.lower() or 'db' in file_path.lower():
                return {
                    'required': True,
                    'test_type': 'integration',
                    'rationale': 'Database code - integration tests required',
                    'priority': 'high'
                }

            # API/endpoint files need tests
            if 'api' in file_path.lower() or 'endpoint' in file_path.lower():
                return {
                    'required': True,
                    'test_type': 'integration',
                    'rationale': 'API endpoint - integration tests required',
                    'priority': 'high'
                }

            # Generic Python file
            return {
                'required': True,
                'test_type': 'unit',
                'rationale': 'Python module - unit tests recommended',
                'priority': 'medium'
            }

        # SQL files need migration tests
        if file_path.endswith('.sql'):
            return {
                'required': True,
                'test_type': 'migration',
                'rationale': 'SQL script - migration test required',
                'priority': 'high'
            }

        # Default: no test required for other file types
        return {
            'required': False,
            'test_type': None,
            'rationale': f'File type {Path(file_path).suffix} - no test required',
            'priority': None
        }

    def _get_expected_test_path(self, source_file: str) -> str:
        """
        Détermine le chemin attendu du fichier de test

        Convention:
        - cortex/agents/foo.py → tests/agents/test_foo.py
        - cortex/core/bar.py → tests/core/test_bar.py
        """
        # Remplacer cortex/ par tests/
        if source_file.startswith('cortex/'):
            test_path = source_file.replace('cortex/', 'tests/', 1)
        else:
            test_path = f"tests/{source_file}"

        # Ajouter test_ prefix au nom du fichier
        path_parts = test_path.split('/')
        filename = path_parts[-1]

        if not filename.startswith('test_'):
            filename = f"test_{filename}"
            path_parts[-1] = filename

        return '/'.join(path_parts)

    def _test_exists(self, test_path: str) -> bool:
        """
        Vérifie si un fichier de test existe

        Args:
            test_path: Chemin du fichier de test

        Returns:
            True si le test existe
        """
        import os
        return os.path.exists(test_path)

    def request_test_creation(self, test_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Envoie des requêtes au ToolerAgent pour créer les tests manquants

        Args:
            test_requests: Liste des requêtes de création de tests

        Returns:
            Dict avec résultats des requêtes
        """
        try:
            print(f"\n{'='*70}")
            print(f"📝 TESTER AGENT - Requesting Test Creation")
            print(f"{'='*70}")
            print(f"Sending {len(test_requests)} requests to ToolerAgent\n")

            # TODO: Intégrer avec ToolerAgent quand il sera créé
            # Pour l'instant, on log les requêtes

            changelog_repo = get_changelog_repository()

            for idx, request in enumerate(test_requests, 1):
                print(f"[{idx}/{len(test_requests)}] Request test creation:")
                print(f"   Source: {request['source_file']}")
                print(f"   Test: {request['test_file']}")
                print(f"   Type: {request['test_type']}")
                print(f"   Priority: {request['priority']}")

                # Log la requête
                changelog_repo.log_change(
                    change_type='test_request',
                    entity_type='tooler_request',
                    author='TesterAgent',
                    description=f"Requested test creation for {request['source_file']}",
                    impact_level='medium',
                    metadata=request
                )

            print(f"\n✓ {len(test_requests)} test creation requests logged")
            print(f"{'='*70}\n")

            return {
                'success': True,
                'action': 'request_test_creation',
                'requests_sent': len(test_requests),
                'requests': test_requests,
                'note': 'Requests logged. ToolerAgent integration pending.'
            }

        except Exception as e:
            return {
                'success': False,
                'action': 'request_test_creation',
                'error': f"Request creation failed: {str(e)}"
            }

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
        """
        Analyse heuristique pour recommander une action

        Note: Utilise une logique heuristique simple au lieu d'un LLM call
        pour garder la validation rapide et économique.
        """
        # Logique heuristique simple
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
        elif len(report.test_failures) > 5:
            return {
                'recommendation': 'escalate_tier',
                'escalation_reason': 'complex_logic_error',
                'confidence': 0.7,
                'summary': 'Multiple test failures suggest complex issues'
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
