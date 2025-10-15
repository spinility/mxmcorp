"""
Cortex Logger - Système de logging léger pour auto-analyse et auto-correction
Conçu spécifiquement pour permettre au système de s'analyser et s'améliorer
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import json
from enum import Enum


class EventType(Enum):
    """Types d'événements loggés"""
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_FAIL = "task_fail"
    TOOL_CALL = "tool_call"
    DELEGATION = "delegation"
    ESCALATION = "escalation"
    MODEL_SWITCH = "model_switch"
    COST_ALERT = "cost_alert"
    QUALITY_CHECK = "quality_check"
    WORKFLOW_DECISION = "workflow_decision"
    AGENT_CREATION = "agent_creation"
    SYSTEM_IMPROVEMENT = "system_improvement"


@dataclass
class LogEntry:
    """Entrée de log structurée"""
    timestamp: str
    event_type: EventType
    agent: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    cost: float = 0.0
    success: bool = True
    parent_task_id: Optional[str] = None
    task_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        result = asdict(self)
        result["event_type"] = self.event_type.value
        return result


class CortexLogger:
    """
    Logger spécialisé pour le système Cortex
    Optimisé pour l'auto-analyse et l'apprentissage
    """

    def __init__(self, log_dir: Optional[Path] = None, max_memory_entries: int = 1000):
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "logs"

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Logs en mémoire pour analyse rapide
        self.memory_logs: List[LogEntry] = []
        self.max_memory_entries = max_memory_entries

        # Fichier de log actuel
        self.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = self.log_dir / f"session_{self.current_session}.jsonl"

        # Statistiques en temps réel
        self.stats = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_cost": 0.0,
            "total_escalations": 0,
            "total_delegations": 0,
            "agents_used": set()
        }

    def log(
        self,
        event_type: EventType,
        agent: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        cost: float = 0.0,
        success: bool = True,
        parent_task_id: Optional[str] = None,
        task_id: Optional[str] = None
    ):
        """
        Enregistre un événement

        Args:
            event_type: Type d'événement
            agent: Nom de l'agent qui génère le log
            message: Message descriptif
            data: Données additionnelles structurées
            cost: Coût de l'opération
            success: Si l'opération a réussi
            parent_task_id: ID de la tâche parente (pour traçabilité)
            task_id: ID de la tâche actuelle
        """
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            agent=agent,
            message=message,
            data=data or {},
            cost=cost,
            success=success,
            parent_task_id=parent_task_id,
            task_id=task_id
        )

        # Ajouter en mémoire
        self.memory_logs.append(entry)
        if len(self.memory_logs) > self.max_memory_entries:
            self.memory_logs.pop(0)

        # Écrire sur disque (JSONL pour parsing facile)
        with open(self.session_file, 'a') as f:
            f.write(json.dumps(entry.to_dict()) + '\n')

        # Mettre à jour les stats
        self._update_stats(entry)

    def _update_stats(self, entry: LogEntry):
        """Met à jour les statistiques en temps réel"""
        self.stats["agents_used"].add(entry.agent)
        self.stats["total_cost"] += entry.cost

        if entry.event_type == EventType.TASK_START:
            self.stats["total_tasks"] += 1
        elif entry.event_type == EventType.TASK_COMPLETE:
            self.stats["successful_tasks"] += 1
        elif entry.event_type == EventType.TASK_FAIL:
            self.stats["failed_tasks"] += 1
        elif entry.event_type == EventType.ESCALATION:
            self.stats["total_escalations"] += 1
        elif entry.event_type == EventType.DELEGATION:
            self.stats["total_delegations"] += 1

    def analyze_recent_performance(self, last_n: int = 50) -> Dict[str, Any]:
        """
        Analyse les N dernières entrées pour détecter des patterns

        Retourne:
            - Taux de succès
            - Coût moyen par tâche
            - Agents les plus utilisés
            - Taux d'escalation
            - Problèmes récurrents
        """
        recent = self.memory_logs[-last_n:]

        if not recent:
            return {"error": "No logs available"}

        # Calculer les métriques
        tasks = [e for e in recent if e.event_type in [EventType.TASK_START, EventType.TASK_COMPLETE, EventType.TASK_FAIL]]
        successes = [e for e in tasks if e.event_type == EventType.TASK_COMPLETE]
        failures = [e for e in tasks if e.event_type == EventType.TASK_FAIL]
        escalations = [e for e in recent if e.event_type == EventType.ESCALATION]

        # Agents utilisés
        agent_usage = {}
        for entry in recent:
            agent_usage[entry.agent] = agent_usage.get(entry.agent, 0) + 1

        # Coûts par agent
        agent_costs = {}
        for entry in recent:
            if entry.cost > 0:
                agent_costs[entry.agent] = agent_costs.get(entry.agent, 0.0) + entry.cost

        # Problèmes récurrents (basé sur failures)
        failure_reasons = {}
        for failure in failures:
            reason = failure.data.get("error", "unknown")
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

        total_cost = sum(e.cost for e in recent)

        return {
            "period": f"Last {len(recent)} events",
            "success_rate": len(successes) / len(tasks) if tasks else 0,
            "total_tasks": len(tasks),
            "successful_tasks": len(successes),
            "failed_tasks": len(failures),
            "escalation_rate": len(escalations) / len(tasks) if tasks else 0,
            "total_cost": total_cost,
            "avg_cost_per_task": total_cost / len(tasks) if tasks else 0,
            "most_used_agents": sorted(agent_usage.items(), key=lambda x: x[1], reverse=True)[:5],
            "costliest_agents": sorted(agent_costs.items(), key=lambda x: x[1], reverse=True)[:5],
            "recurring_issues": sorted(failure_reasons.items(), key=lambda x: x[1], reverse=True)[:5]
        }

    def identify_improvement_opportunities(self) -> List[Dict[str, Any]]:
        """
        Identifie des opportunités d'amélioration basées sur les logs

        Retourne une liste de suggestions concrètes
        """
        analysis = self.analyze_recent_performance(last_n=100)
        opportunities = []

        # Taux de succès faible
        if analysis["success_rate"] < 0.8:
            opportunities.append({
                "priority": "high",
                "category": "reliability",
                "issue": f"Success rate is low: {analysis['success_rate']:.1%}",
                "suggestion": "Consider adding more robust error handling or escalation paths",
                "data": {"success_rate": analysis["success_rate"]}
            })

        # Trop d'escalations
        if analysis["escalation_rate"] > 0.3:
            opportunities.append({
                "priority": "medium",
                "category": "efficiency",
                "issue": f"High escalation rate: {analysis['escalation_rate']:.1%}",
                "suggestion": "Review task routing - many tasks may be assigned to wrong tier initially",
                "data": {"escalation_rate": analysis["escalation_rate"]}
            })

        # Coûts élevés
        if analysis["avg_cost_per_task"] > 0.01:
            opportunities.append({
                "priority": "high",
                "category": "cost",
                "issue": f"Average cost per task is high: ${analysis['avg_cost_per_task']:.4f}",
                "suggestion": "Review model selection strategy - consider using lower tiers for simple tasks",
                "data": {"avg_cost": analysis["avg_cost_per_task"]}
            })

        # Agents sous-utilisés
        if analysis["most_used_agents"]:
            top_agent = analysis["most_used_agents"][0]
            if top_agent[1] > len(self.memory_logs[-100:]) * 0.5:
                opportunities.append({
                    "priority": "low",
                    "category": "load_balancing",
                    "issue": f"Agent '{top_agent[0]}' handles {top_agent[1]} tasks (overloaded)",
                    "suggestion": "Consider delegating more tasks to other agents or creating specialized sub-agents",
                    "data": {"agent": top_agent[0], "task_count": top_agent[1]}
                })

        # Problèmes récurrents
        if analysis["recurring_issues"]:
            for issue, count in analysis["recurring_issues"]:
                if count > 3:
                    opportunities.append({
                        "priority": "high",
                        "category": "reliability",
                        "issue": f"Recurring failure: '{issue}' ({count} times)",
                        "suggestion": f"Investigate and fix root cause of: {issue}",
                        "data": {"error": issue, "occurrences": count}
                    })

        return opportunities

    def generate_self_improvement_report(self) -> str:
        """
        Génère un rapport complet pour auto-amélioration
        Format conçu pour être lu par un LLM
        """
        analysis = self.analyze_recent_performance(last_n=100)
        opportunities = self.identify_improvement_opportunities()

        report_lines = [
            "=== CORTEX SELF-ANALYSIS REPORT ===",
            f"Generated: {datetime.now().isoformat()}",
            f"Session: {self.current_session}",
            "",
            "## Performance Metrics",
            f"Total Tasks: {analysis['total_tasks']}",
            f"Success Rate: {analysis['success_rate']:.1%}",
            f"Escalation Rate: {analysis['escalation_rate']:.1%}",
            f"Total Cost: ${analysis['total_cost']:.4f}",
            f"Avg Cost/Task: ${analysis['avg_cost_per_task']:.4f}",
            "",
            "## Agent Usage",
        ]

        for agent, count in analysis["most_used_agents"]:
            report_lines.append(f"  - {agent}: {count} events")

        report_lines.append("")
        report_lines.append("## Cost Analysis")
        for agent, cost in analysis["costliest_agents"]:
            report_lines.append(f"  - {agent}: ${cost:.4f}")

        if analysis["recurring_issues"]:
            report_lines.append("")
            report_lines.append("## Recurring Issues")
            for issue, count in analysis["recurring_issues"]:
                report_lines.append(f"  - {issue}: {count} occurrences")

        if opportunities:
            report_lines.append("")
            report_lines.append("## Improvement Opportunities")
            for i, opp in enumerate(opportunities, 1):
                report_lines.append(f"\n{i}. [{opp['priority'].upper()}] {opp['category']}")
                report_lines.append(f"   Issue: {opp['issue']}")
                report_lines.append(f"   Suggestion: {opp['suggestion']}")

        report_lines.append("")
        report_lines.append("## Recommendations")
        report_lines.append("Based on this analysis, the system should:")

        if opportunities:
            for opp in sorted(opportunities, key=lambda x: {"high": 0, "medium": 1, "low": 2}[opp["priority"]])[:3]:
                report_lines.append(f"  • {opp['suggestion']}")
        else:
            report_lines.append("  • Continue current operations - performance is optimal")

        return "\n".join(report_lines)

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques globales"""
        stats = self.stats.copy()
        stats["agents_used"] = list(stats["agents_used"])
        return stats


# Instance globale
_global_logger: Optional[CortexLogger] = None


def get_logger() -> CortexLogger:
    """Récupère l'instance globale du logger"""
    global _global_logger
    if _global_logger is None:
        _global_logger = CortexLogger()
    return _global_logger


if __name__ == "__main__":
    # Test
    logger = CortexLogger()

    # Simuler quelques événements
    logger.log(EventType.TASK_START, "CEO", "New task received", {"task": "analyze_data"}, task_id="task_001")
    logger.log(EventType.DELEGATION, "CEO", "Delegating to Data Director", {"to": "Data Director"}, task_id="task_001")
    logger.log(EventType.TASK_COMPLETE, "Data Director", "Task completed successfully", cost=0.002, task_id="task_001")

    logger.log(EventType.TASK_START, "CEO", "Complex task", {"task": "design_system"}, task_id="task_002")
    logger.log(EventType.ESCALATION, "CEO", "Escalating to Claude tier", {"from": "nano", "to": "claude"}, cost=0.015, task_id="task_002")
    logger.log(EventType.TASK_COMPLETE, "CEO", "Task completed with escalation", cost=0.015, task_id="task_002")

    logger.log(EventType.TASK_START, "Worker", "Simple task", task_id="task_003")
    logger.log(EventType.TASK_FAIL, "Worker", "Task failed", {"error": "Timeout"}, success=False, task_id="task_003")

    print("=== Performance Analysis ===")
    analysis = logger.analyze_recent_performance()
    print(json.dumps(analysis, indent=2, default=str))

    print("\n=== Improvement Opportunities ===")
    opportunities = logger.identify_improvement_opportunities()
    print(json.dumps(opportunities, indent=2))

    print("\n=== Self-Improvement Report ===")
    print(logger.generate_self_improvement_report())
