"""
Self Validator - Système d'auto-validation et correction
Valide les résultats, détecte les problèmes et applique des corrections automatiques
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from cortex.core.cortex_logger import get_logger, EventType
from cortex.core.feedback_system import get_feedback, FeedbackLevel


class ValidationStatus(Enum):
    """Statuts de validation"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class ValidationRule:
    """
    Règle de validation

    Une règle est une fonction qui prend un résultat et retourne si c'est valide
    """
    name: str
    description: str
    validator: Callable[[Dict[str, Any]], bool]
    severity: str = "error"  # error, warning, info
    auto_fix: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None


@dataclass
class ValidationResult:
    """Résultat d'une validation"""
    rule_name: str
    status: ValidationStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    fixed: bool = False
    fix_applied: Optional[str] = None


class SelfValidator:
    """
    Système de validation automatique

    Permet au système de valider ses propres résultats et de se corriger
    """

    def __init__(self):
        self.rules: List[ValidationRule] = []
        self.logger = get_logger()
        self.feedback = get_feedback()

        # Enregistrer les règles par défaut
        self._register_default_rules()

    def _register_default_rules(self):
        """Enregistre les règles de validation par défaut"""

        # Règle 1: Vérifier que le résultat contient les clés essentielles
        self.add_rule(ValidationRule(
            name="required_keys",
            description="Result must contain success and data keys",
            validator=lambda r: "success" in r and "data" in r,
            severity="error"
        ))

        # Règle 2: Vérifier que le coût n'est pas négatif
        self.add_rule(ValidationRule(
            name="valid_cost",
            description="Cost must be non-negative",
            validator=lambda r: r.get("cost", 0) >= 0,
            severity="error",
            auto_fix=lambda r: {**r, "cost": abs(r.get("cost", 0))}
        ))

        # Règle 3: Vérifier que les tokens ne sont pas négatifs
        self.add_rule(ValidationRule(
            name="valid_tokens",
            description="Token counts must be non-negative",
            validator=lambda r: (
                r.get("tokens_input", 0) >= 0 and
                r.get("tokens_output", 0) >= 0
            ),
            severity="error",
            auto_fix=lambda r: {
                **r,
                "tokens_input": max(0, r.get("tokens_input", 0)),
                "tokens_output": max(0, r.get("tokens_output", 0))
            }
        ))

        # Règle 4: Avertir si le coût est très élevé
        self.add_rule(ValidationRule(
            name="cost_threshold",
            description="Warn if cost exceeds threshold",
            validator=lambda r: r.get("cost", 0) < 0.10,
            severity="warning"
        ))

        # Règle 5: Vérifier que les données ne sont pas vides en cas de succès
        self.add_rule(ValidationRule(
            name="non_empty_data",
            description="Successful results should have non-empty data",
            validator=lambda r: not (r.get("success") and not r.get("data")),
            severity="warning"
        ))

        # Règle 6: Vérifier qu'un message d'erreur existe en cas d'échec
        self.add_rule(ValidationRule(
            name="error_message",
            description="Failed results must include error message",
            validator=lambda r: r.get("success") or "error" in r,
            severity="error"
        ))

    def add_rule(self, rule: ValidationRule):
        """Ajoute une règle de validation personnalisée"""
        self.rules.append(rule)

    def validate(
        self,
        result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        auto_fix: bool = True,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Valide un résultat

        Args:
            result: Résultat à valider
            context: Contexte additionnel (task, agent, etc.)
            auto_fix: Appliquer les corrections automatiques
            verbose: Mode verbose

        Returns:
            Dict avec validation_results et corrected_result si applicable
        """
        if verbose:
            print(f"[SelfValidator] Validating result...")

        validation_results: List[ValidationResult] = []
        corrected_result = result.copy()
        has_errors = False
        has_warnings = False

        # Appliquer chaque règle
        for rule in self.rules:
            try:
                is_valid = rule.validator(corrected_result)

                if is_valid:
                    validation_results.append(ValidationResult(
                        rule_name=rule.name,
                        status=ValidationStatus.PASS,
                        message=f"✓ {rule.description}"
                    ))
                else:
                    # Validation échouée
                    status = ValidationStatus.FAIL if rule.severity == "error" else ValidationStatus.WARNING

                    if rule.severity == "error":
                        has_errors = True
                    elif rule.severity == "warning":
                        has_warnings = True

                    # Tenter auto-fix si disponible et activé
                    fixed = False
                    fix_applied = None

                    if auto_fix and rule.auto_fix:
                        try:
                            fixed_result = rule.auto_fix(corrected_result)
                            corrected_result = fixed_result
                            fixed = True
                            fix_applied = f"Auto-fixed: {rule.name}"

                            if verbose:
                                print(f"[SelfValidator] ✓ Auto-fixed: {rule.name}")

                        except Exception as e:
                            if verbose:
                                print(f"[SelfValidator] ✗ Auto-fix failed for {rule.name}: {e}")

                    validation_results.append(ValidationResult(
                        rule_name=rule.name,
                        status=status,
                        message=f"✗ {rule.description}",
                        fixed=fixed,
                        fix_applied=fix_applied
                    ))

            except Exception as e:
                validation_results.append(ValidationResult(
                    rule_name=rule.name,
                    status=ValidationStatus.FAIL,
                    message=f"Validation error: {str(e)}",
                    details={"error": str(e)}
                ))
                has_errors = True

        # Logger la validation
        agent_name = context.get("agent", "Unknown") if context else "Unknown"

        self.logger.log(
            event_type=EventType.QUALITY_CHECK,
            agent="SelfValidator",
            message=f"Validated result from {agent_name}",
            data={
                "has_errors": has_errors,
                "has_warnings": has_warnings,
                "rules_passed": len([r for r in validation_results if r.status == ValidationStatus.PASS]),
                "rules_failed": len([r for r in validation_results if r.status == ValidationStatus.FAIL]),
                "auto_fixes_applied": len([r for r in validation_results if r.fixed])
            }
        )

        # Feedback utilisateur
        if has_errors:
            self.feedback.error(
                f"Validation failed for {agent_name}",
                errors=len([r for r in validation_results if r.status == ValidationStatus.FAIL])
            )
        elif has_warnings:
            self.feedback.warning(
                f"Validation passed with warnings for {agent_name}",
                warnings=len([r for r in validation_results if r.status == ValidationStatus.WARNING])
            )
        else:
            if verbose:
                self.feedback.success(f"Validation passed for {agent_name}")

        return {
            "valid": not has_errors,
            "has_warnings": has_warnings,
            "validation_results": [
                {
                    "rule": r.rule_name,
                    "status": r.status.value,
                    "message": r.message,
                    "fixed": r.fixed,
                    "fix_applied": r.fix_applied
                }
                for r in validation_results
            ],
            "original_result": result,
            "corrected_result": corrected_result if corrected_result != result else None
        }

    def validate_and_apply(
        self,
        result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Valide et applique automatiquement les corrections

        Returns:
            Le résultat corrigé ou l'original si pas de correction nécessaire
        """
        validation = self.validate(result, context, auto_fix=True, verbose=verbose)

        if validation["corrected_result"]:
            if verbose:
                print("[SelfValidator] Applied corrections")
            return validation["corrected_result"]

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de validation"""
        return {
            "total_rules": len(self.rules),
            "rules": [
                {
                    "name": rule.name,
                    "description": rule.description,
                    "severity": rule.severity,
                    "has_auto_fix": rule.auto_fix is not None
                }
                for rule in self.rules
            ]
        }


class WorkflowValidator:
    """
    Valide des workflows complets

    Un workflow est une séquence de tâches/agents
    """

    def __init__(self):
        self.logger = get_logger()
        self.feedback = get_feedback()

    def validate_workflow(
        self,
        workflow_steps: List[Dict[str, Any]],
        expected_outcome: Optional[Dict[str, Any]] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Valide un workflow complet

        Args:
            workflow_steps: Liste des étapes du workflow avec résultats
            expected_outcome: Résultat attendu (optionnel)
            verbose: Mode verbose

        Returns:
            Validation du workflow avec recommandations
        """
        if verbose:
            print(f"[WorkflowValidator] Validating workflow with {len(workflow_steps)} steps...")

        issues = []
        total_cost = sum(step.get("cost", 0) for step in workflow_steps)
        failed_steps = [step for step in workflow_steps if not step.get("success", True)]
        escalations = [step for step in workflow_steps if step.get("escalated", False)]

        # Vérifier les problèmes
        if failed_steps:
            issues.append({
                "severity": "error",
                "issue": f"{len(failed_steps)} steps failed",
                "recommendation": "Review error handling and retry logic"
            })

        if total_cost > 0.10:
            issues.append({
                "severity": "warning",
                "issue": f"High workflow cost: ${total_cost:.4f}",
                "recommendation": "Consider using lower-tier models or caching"
            })

        if len(escalations) > len(workflow_steps) * 0.3:
            issues.append({
                "severity": "warning",
                "issue": f"High escalation rate: {len(escalations)}/{len(workflow_steps)}",
                "recommendation": "Review initial task routing - tasks may be incorrectly assigned"
            })

        # Vérifier l'outcome si fourni
        outcome_match = None
        if expected_outcome:
            # Comparer le dernier résultat avec l'outcome attendu
            last_step = workflow_steps[-1] if workflow_steps else {}
            outcome_match = self._compare_outcomes(last_step, expected_outcome)

            if not outcome_match["matches"]:
                issues.append({
                    "severity": "error",
                    "issue": "Workflow outcome doesn't match expectations",
                    "recommendation": outcome_match["recommendation"]
                })

        # Logger
        self.logger.log(
            event_type=EventType.QUALITY_CHECK,
            agent="WorkflowValidator",
            message="Workflow validation complete",
            data={
                "steps": len(workflow_steps),
                "failed_steps": len(failed_steps),
                "total_cost": total_cost,
                "issues": len(issues)
            }
        )

        is_valid = not any(issue["severity"] == "error" for issue in issues)

        return {
            "valid": is_valid,
            "steps_analyzed": len(workflow_steps),
            "total_cost": total_cost,
            "failed_steps": len(failed_steps),
            "escalations": len(escalations),
            "issues": issues,
            "outcome_match": outcome_match
        }

    def _compare_outcomes(
        self,
        actual: Dict[str, Any],
        expected: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare le résultat réel avec l'attendu"""
        matches = True
        differences = []

        for key, expected_value in expected.items():
            actual_value = actual.get(key)

            if actual_value != expected_value:
                matches = False
                differences.append({
                    "key": key,
                    "expected": expected_value,
                    "actual": actual_value
                })

        recommendation = "Workflow produced expected outcome" if matches else \
            f"Review steps that produced: {', '.join([d['key'] for d in differences])}"

        return {
            "matches": matches,
            "differences": differences,
            "recommendation": recommendation
        }


# Instances globales
_global_validator: Optional[SelfValidator] = None
_global_workflow_validator: Optional[WorkflowValidator] = None


def get_validator() -> SelfValidator:
    """Récupère l'instance globale du validateur"""
    global _global_validator
    if _global_validator is None:
        _global_validator = SelfValidator()
    return _global_validator


def get_workflow_validator() -> WorkflowValidator:
    """Récupère l'instance globale du validateur de workflow"""
    global _global_workflow_validator
    if _global_workflow_validator is None:
        _global_workflow_validator = WorkflowValidator()
    return _global_workflow_validator


if __name__ == "__main__":
    import json

    # Test SelfValidator
    print("=== Testing SelfValidator ===\n")

    validator = SelfValidator()

    # Test 1: Résultat valide
    print("1. Valid result:")
    result1 = {
        "success": True,
        "data": "Hello world",
        "cost": 0.001,
        "tokens_input": 100,
        "tokens_output": 50
    }
    validation1 = validator.validate(result1, verbose=True)
    print(json.dumps(validation1, indent=2))

    # Test 2: Résultat avec erreurs corrigibles
    print("\n2. Result with fixable errors:")
    result2 = {
        "success": True,
        "data": "Data",
        "cost": -0.001,  # Coût négatif - devrait être corrigé
        "tokens_input": -50,  # Négatif - devrait être corrigé
        "tokens_output": 100
    }
    validation2 = validator.validate(result2, verbose=True)
    print(json.dumps(validation2, indent=2))

    # Test 3: Résultat avec warnings
    print("\n3. Result with warnings:")
    result3 = {
        "success": True,
        "data": "Data",
        "cost": 0.15,  # Coût élevé - warning
        "tokens_input": 10000,
        "tokens_output": 5000
    }
    validation3 = validator.validate(result3, verbose=True)
    print(json.dumps(validation3, indent=2))

    # Test WorkflowValidator
    print("\n\n=== Testing WorkflowValidator ===\n")

    workflow_validator = WorkflowValidator()

    workflow_steps = [
        {"success": True, "cost": 0.001, "agent": "Worker"},
        {"success": True, "cost": 0.002, "agent": "Manager", "escalated": True},
        {"success": False, "cost": 0.001, "agent": "Director", "error": "Timeout"}
    ]

    workflow_validation = workflow_validator.validate_workflow(workflow_steps, verbose=True)
    print(json.dumps(workflow_validation, indent=2))
