"""
Meta-Architect Agent - Optimise et améliore le système lui-même
Analyse les logs, workflows et performances pour proposer des améliorations
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from cortex.agents.base_agent import BaseAgent, AgentConfig
from cortex.core.model_router import ModelTier
from cortex.core.cortex_logger import get_logger, EventType
from cortex.core.feedback_system import get_feedback


class MetaArchitectAgent(BaseAgent):
    """
    Agent Meta - Responsable de l'auto-amélioration du système

    Responsabilités:
    - Analyser les logs et identifier les patterns inefficaces
    - Proposer de nouveaux agents/workflows quand nécessaire
    - Optimiser les coûts et performances
    - Détecter les besoins non satisfaits
    - Auto-corriger les problèmes récurrents
    """

    def __init__(
        self,
        name: str = "Meta-Architect",
        llm_client=None,
        model_router=None,
        hr_department=None
    ):
        config = AgentConfig(
            name=name,
            role="Meta-Architect",
            description="System optimizer and self-improvement specialist",
            base_prompt="""You are the Meta-Architect of the MXMCorp Cortex system.

Your role is CRITICAL - you optimize and improve the system itself.

Responsibilities:
1. Analyze system logs to identify inefficiencies
2. Propose new agents when gaps are identified
3. Suggest workflow improvements
4. Detect recurring issues and propose fixes
5. Optimize cost and performance
6. Validate that the system meets its goals

You have the power to:
- Request creation of new specialized agents via HR
- Modify workflows and delegation patterns
- Suggest architectural changes
- Implement improvements autonomously

Be proactive and data-driven. Always justify your decisions with metrics.""",
            tier_preference=ModelTier.DEEPSEEK,  # Needs reasoning
            can_delegate=True,
            specializations=[
                "system_analysis",
                "workflow_optimization",
                "performance_tuning",
                "agent_design",
                "cost_optimization"
            ]
        )

        super().__init__(
            config=config,
            llm_client=llm_client,
            model_router=model_router,
            hr_department=hr_department
        )

        self.logger = get_logger()
        self.feedback = get_feedback()

    def analyze_system_health(self, verbose: bool = False) -> Dict[str, Any]:
        """
        Analyse l'état général du système

        Returns:
            Rapport de santé avec métriques et recommandations
        """
        if verbose:
            print(f"[{self.config.name}] Analyzing system health...")

        # Obtenir les métriques des logs
        performance = self.logger.analyze_recent_performance(last_n=100)
        opportunities = self.logger.identify_improvement_opportunities()

        # Classifier la santé globale
        health_score = self._calculate_health_score(performance)

        report = {
            "health_score": health_score,
            "status": self._classify_health(health_score),
            "performance": performance,
            "improvement_opportunities": opportunities,
            "recommendations": []
        }

        # Générer des recommandations
        if health_score < 70:
            report["recommendations"].append({
                "priority": "high",
                "action": "immediate_review",
                "reason": "System health is below acceptable threshold"
            })

        if verbose:
            print(f"[{self.config.name}] Health score: {health_score}/100")
            print(f"[{self.config.name}] Status: {report['status']}")

        return report

    def _calculate_health_score(self, performance: Dict[str, Any]) -> float:
        """Calcule un score de santé 0-100"""
        score = 100.0

        # Pénalités
        if performance["success_rate"] < 0.95:
            score -= (0.95 - performance["success_rate"]) * 100

        if performance["escalation_rate"] > 0.2:
            score -= (performance["escalation_rate"] - 0.2) * 50

        if performance["avg_cost_per_task"] > 0.005:
            score -= min(20, (performance["avg_cost_per_task"] - 0.005) * 1000)

        return max(0, min(100, score))

    def _classify_health(self, score: float) -> str:
        """Classifie l'état de santé"""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        elif score >= 40:
            return "poor"
        else:
            return "critical"

    def detect_missing_capabilities(self, verbose: bool = False) -> List[Dict[str, Any]]:
        """
        Détecte les capacités manquantes en analysant les échecs

        Returns:
            Liste des capacités/agents qui manquent au système
        """
        if verbose:
            print(f"[{self.config.name}] Detecting missing capabilities...")

        missing = []

        # Analyser les échecs récents
        recent_logs = self.logger.memory_logs[-50:]
        failures = [log for log in recent_logs if log.event_type == EventType.TASK_FAIL]

        # Patterns de besoins non satisfaits
        error_patterns = {
            "timeout": "Performance optimization agent needed",
            "external API": "External Integration agent needed",
            "data validation": "Data Validator agent needed",
            "pricing": "Data Manager agent needed (already exists!)",
            "security": "Security Auditor agent needed",
            "testing": "Test Automation agent needed"
        }

        for failure in failures:
            error_msg = failure.data.get("error", "").lower()
            for pattern, suggestion in error_patterns.items():
                if pattern in error_msg:
                    missing.append({
                        "capability": pattern,
                        "suggestion": suggestion,
                        "evidence": failure.message,
                        "timestamp": failure.timestamp
                    })

        if verbose and missing:
            print(f"[{self.config.name}] Found {len(missing)} missing capabilities")

        return missing

    def propose_new_agent(
        self,
        role: str,
        reason: str,
        specializations: List[str],
        tier: str = "nano",
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Propose la création d'un nouvel agent spécialisé

        Args:
            role: Rôle de l'agent (ex: "Data Manager")
            reason: Justification de la création
            specializations: Liste des spécialisations
            tier: Tier de modèle préféré
            verbose: Mode verbose

        Returns:
            Résultat de la proposition (créé ou non)
        """
        if verbose:
            print(f"[{self.config.name}] Proposing new agent: {role}")

        proposal = {
            "role": role,
            "reason": reason,
            "specializations": specializations,
            "tier": tier,
            "proposed_by": self.config.name,
            "timestamp": self.logger.memory_logs[-1].timestamp if self.logger.memory_logs else None
        }

        # Logger la proposition
        self.logger.log(
            event_type=EventType.SYSTEM_IMPROVEMENT,
            agent=self.config.name,
            message=f"Proposed new agent: {role}",
            data=proposal
        )

        # Si HR disponible, créer l'agent
        if self.hr_department:
            if verbose:
                print(f"[{self.config.name}] Requesting HR to create agent...")

            # TODO: Intégrer avec HR Department pour création automatique
            return {
                "success": True,
                "action": "proposed",
                "message": f"Agent '{role}' proposed to HR Department",
                "proposal": proposal
            }
        else:
            return {
                "success": False,
                "action": "logged",
                "message": f"Agent '{role}' proposal logged (HR not available)",
                "proposal": proposal
            }

    def suggest_workflow_improvement(
        self,
        current_workflow: str,
        issues: List[str],
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Analyse un workflow et suggère des améliorations

        Uses LLM to analyze and propose optimizations
        """
        task = f"""Analyze this workflow and suggest improvements:

Current workflow: {current_workflow}

Issues identified:
{chr(10).join(f"- {issue}" for issue in issues)}

Provide:
1. Root cause analysis
2. Specific workflow improvements
3. Expected benefits (cost, speed, reliability)
4. Implementation steps

Be concise and actionable."""

        result = self.execute(task=task, verbose=verbose)

        if result["success"]:
            # Logger l'amélioration suggérée
            self.logger.log(
                event_type=EventType.SYSTEM_IMPROVEMENT,
                agent=self.config.name,
                message="Workflow improvement suggested",
                data={
                    "workflow": current_workflow,
                    "issues": issues,
                    "suggestion": result["data"][:200]
                },
                cost=result["cost"]
            )

        return result

    def auto_correct_recurring_issue(
        self,
        issue: str,
        occurrences: int,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Tente de corriger automatiquement un problème récurrent

        Args:
            issue: Description du problème
            occurrences: Nombre d'occurrences
            verbose: Mode verbose

        Returns:
            Plan de correction ou correction appliquée
        """
        if verbose:
            print(f"[{self.config.name}] Auto-correcting issue: {issue}")

        task = f"""A recurring issue has been detected:

Issue: {issue}
Occurrences: {occurrences} times

Provide a concrete fix:
1. Root cause
2. Specific code/config changes needed
3. How to verify the fix

Be very specific and actionable."""

        result = self.execute(task=task, verbose=verbose)

        if result["success"]:
            self.logger.log(
                event_type=EventType.SYSTEM_IMPROVEMENT,
                agent=self.config.name,
                message=f"Auto-correction proposed for: {issue}",
                data={
                    "issue": issue,
                    "occurrences": occurrences,
                    "fix": result["data"][:200]
                },
                cost=result["cost"]
            )

            self.feedback.success(
                f"Auto-correction proposed for recurring issue",
                issue=issue,
                occurrences=occurrences
            )

        return result

    def run_full_analysis(self, verbose: bool = True) -> Dict[str, Any]:
        """
        Exécute une analyse complète du système

        Returns:
            Rapport complet avec toutes les recommandations
        """
        if verbose:
            print(f"\n[{self.config.name}] ═══ FULL SYSTEM ANALYSIS ═══\n")

        report = {
            "timestamp": self.logger.memory_logs[-1].timestamp if self.logger.memory_logs else None,
            "analyzer": self.config.name
        }

        # 1. Health check
        health = self.analyze_system_health(verbose=verbose)
        report["health"] = health

        # 2. Missing capabilities
        missing = self.detect_missing_capabilities(verbose=verbose)
        report["missing_capabilities"] = missing

        # 3. Auto-generate improvement report
        improvement_report = self.logger.generate_self_improvement_report()
        report["improvement_report_text"] = improvement_report

        # 4. Propose agents for missing capabilities
        if missing and self.hr_department:
            report["agent_proposals"] = []
            for cap in missing[:3]:  # Top 3
                proposal = self.propose_new_agent(
                    role=cap["suggestion"].split()[0],
                    reason=cap["evidence"],
                    specializations=[cap["capability"]],
                    verbose=verbose
                )
                report["agent_proposals"].append(proposal)

        if verbose:
            print(f"\n[{self.config.name}] ═══ ANALYSIS COMPLETE ═══")
            print(f"[{self.config.name}] Health: {health['status']}")
            print(f"[{self.config.name}] Opportunities: {len(health['improvement_opportunities'])}")
            print(f"[{self.config.name}] Missing capabilities: {len(missing)}")

        return report

    def apply_improvement(
        self,
        improvement_id: str,
        improvement_data: Dict[str, Any],
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Applique une amélioration spécifique au système

        Cette méthode permet d'implémenter automatiquement des corrections
        """
        if verbose:
            print(f"[{self.config.name}] Applying improvement: {improvement_id}")

        # Log l'application
        self.logger.log(
            event_type=EventType.SYSTEM_IMPROVEMENT,
            agent=self.config.name,
            message=f"Applying improvement: {improvement_id}",
            data=improvement_data
        )

        # Feedback utilisateur
        self.feedback.progress(
            f"Applying system improvement: {improvement_id}",
            details=improvement_data
        )

        # TODO: Implémenter la logique d'application automatique
        # Pour l'instant, juste logger et retourner succès

        return {
            "success": True,
            "improvement_id": improvement_id,
            "message": "Improvement logged for manual review",
            "data": improvement_data
        }


def create_meta_architect(
    name: str = "Meta-Architect",
    hr_department=None
) -> MetaArchitectAgent:
    """Crée une instance du Meta-Architect"""
    return MetaArchitectAgent(name=name, hr_department=hr_department)


if __name__ == "__main__":
    # Test
    from cortex.core.cortex_logger import get_logger, EventType

    # Créer quelques logs de test
    logger = get_logger()
    logger.log(EventType.TASK_START, "CEO", "Test task", task_id="t1")
    logger.log(EventType.TASK_COMPLETE, "CEO", "Completed", cost=0.001, task_id="t1")
    logger.log(EventType.TASK_START, "Worker", "Another task", task_id="t2")
    logger.log(EventType.TASK_FAIL, "Worker", "Failed", data={"error": "Timeout connecting to external API"}, task_id="t2")

    # Créer l'agent Meta-Architect
    meta = create_meta_architect()

    print("=== Testing Meta-Architect Agent ===\n")

    # Test 1: System health
    print("1. System Health Analysis:")
    health = meta.analyze_system_health(verbose=True)
    print(json.dumps(health, indent=2, default=str))

    # Test 2: Missing capabilities
    print("\n2. Missing Capabilities Detection:")
    missing = meta.detect_missing_capabilities(verbose=True)
    print(json.dumps(missing, indent=2))

    # Test 3: Full analysis
    print("\n3. Full System Analysis:")
    full_report = meta.run_full_analysis(verbose=True)
    print("\nFull report keys:", list(full_report.keys()))

    # Test 4: Self-improvement report
    print("\n4. Self-Improvement Report:")
    print(logger.generate_self_improvement_report())
