"""
CEO Reporter - Génère rapports automatiques pour le CEO

Responsabilités:
- Rapports quotidiens (résumé des activités)
- Rapports hebdomadaires (métriques et tendances)
- Alertes temps réel (problèmes critiques)
- Notifications de succès importants
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json

from cortex.core.department_system import Department
from cortex.departments.maintenance.git_diff_processor import GitDiffAnalysis
from cortex.departments.maintenance.roadmap_manager import RoadmapManager


@dataclass
class Alert:
    """Alerte temps réel"""
    id: str
    severity: str  # "critical", "warning", "info", "success"
    title: str
    message: str
    source_department: str
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "source_department": self.source_department,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged
        }


@dataclass
class DailyReport:
    """Rapport quotidien"""
    date: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    git_changes: Dict[str, Any]  # Résumé git diff
    roadmap_updates: Dict[str, Any]  # Changements roadmap
    new_tasks_created: int
    tasks_completed: int
    departments_active: List[str]
    key_achievements: List[str]
    issues_encountered: List[str]
    optimization_insights: List[str]


@dataclass
class WeeklyReport:
    """Rapport hebdomadaire"""
    week_start: datetime
    week_end: datetime
    total_requests: int
    success_rate: float
    total_git_commits: int
    total_lines_added: int
    total_lines_removed: int
    tasks_completed: int
    tasks_created: int
    roadmap_progress: float  # Percentage
    top_performing_departments: List[Dict[str, Any]]
    top_success_patterns: List[str]
    top_issues: List[str]
    recommendations: List[str]


class CEOReporter:
    """
    Générateur de rapports pour le CEO

    Fonctionnalités:
    - Génère rapports quotidiens automatiquement
    - Compile rapports hebdomadaires
    - Envoie alertes temps réel
    - Archive tous les rapports
    """

    def __init__(self, reports_dir: str = "cortex/data/ceo_reports"):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.alerts_file = self.reports_dir / "active_alerts.json"
        self.alerts: List[Alert] = []
        self._load_alerts()

    def _load_alerts(self):
        """Charge les alertes actives"""
        if self.alerts_file.exists():
            with open(self.alerts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.alerts = [
                    Alert(
                        id=a["id"],
                        severity=a["severity"],
                        title=a["title"],
                        message=a["message"],
                        source_department=a["source_department"],
                        timestamp=datetime.fromisoformat(a["timestamp"]),
                        acknowledged=a["acknowledged"]
                    )
                    for a in data.get("alerts", [])
                ]

    def _save_alerts(self):
        """Sauvegarde les alertes"""
        data = {
            "updated_at": datetime.now().isoformat(),
            "alerts": [a.to_dict() for a in self.alerts]
        }

        with open(self.alerts_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "info",
        source_department: str = "unknown"
    ) -> Alert:
        """
        Envoie une alerte temps réel

        Args:
            title: Titre de l'alerte
            message: Message détaillé
            severity: Niveau (critical/warning/info/success)
            source_department: Département source

        Returns:
            Alert créée
        """
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        alert = Alert(
            id=alert_id,
            severity=severity,
            title=title,
            message=message,
            source_department=source_department
        )

        self.alerts.append(alert)
        self._save_alerts()

        # Afficher l'alerte immédiatement
        self._display_alert(alert)

        return alert

    def _display_alert(self, alert: Alert):
        """Affiche une alerte"""
        severity_emoji = {
            "critical": "🔴",
            "warning": "🟠",
            "info": "🔵",
            "success": "🟢"
        }.get(alert.severity, "⚪")

        print(f"\n{'='*70}")
        print(f"{severity_emoji} ALERT [{alert.severity.upper()}] - {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        print(f"From: {alert.source_department}")
        print(f"Title: {alert.title}")
        print(f"Message: {alert.message}")
        print(f"{'='*70}\n")

    def acknowledge_alert(self, alert_id: str):
        """Marque une alerte comme lue"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
        self._save_alerts()

    def get_active_alerts(self, severity: Optional[str] = None) -> List[Alert]:
        """Récupère les alertes non lues"""
        alerts = [a for a in self.alerts if not a.acknowledged]

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def generate_daily_report(
        self,
        roadmap_manager: RoadmapManager,
        git_analysis: Optional[GitDiffAnalysis] = None,
        optimization_insights: Optional[List[str]] = None
    ) -> DailyReport:
        """
        Génère le rapport quotidien

        Args:
            roadmap_manager: Manager du roadmap
            git_analysis: Analyse git du jour (optionnel)
            optimization_insights: Insights du département optimization

        Returns:
            DailyReport
        """
        today = datetime.now()

        # Récupérer statistiques roadmap
        roadmap_summary = roadmap_manager.get_roadmap_summary()

        # Git changes
        git_changes = {}
        if git_analysis:
            git_changes = {
                "total_files_changed": git_analysis.total_files_changed,
                "files_added": len(git_analysis.files_added),
                "files_modified": len(git_analysis.files_modified),
                "files_deleted": len(git_analysis.files_deleted),
                "lines_added": git_analysis.total_lines_added,
                "lines_removed": git_analysis.total_lines_removed
            }

        # Roadmap updates
        roadmap_updates = {
            "completion_percentage": roadmap_summary["completion_percentage"],
            "total_tasks": roadmap_summary["total_tasks"],
            "by_status": roadmap_summary["by_status"]
        }

        # Créer rapport
        report = DailyReport(
            date=today,
            total_requests=0,  # À remplir depuis optimization
            successful_requests=0,
            failed_requests=0,
            git_changes=git_changes,
            roadmap_updates=roadmap_updates,
            new_tasks_created=roadmap_summary["by_status"].get("pending", 0),
            tasks_completed=roadmap_summary["by_status"].get("completed", 0),
            departments_active=list(roadmap_summary["by_department"].keys()),
            key_achievements=[],  # À remplir
            issues_encountered=[],  # À remplir
            optimization_insights=optimization_insights or []
        )

        # Sauvegarder rapport
        self._save_daily_report(report)

        return report

    def _save_daily_report(self, report: DailyReport):
        """Sauvegarde le rapport quotidien"""
        filename = self.reports_dir / f"daily_{report.date.strftime('%Y%m%d')}.json"

        data = {
            "date": report.date.isoformat(),
            "total_requests": report.total_requests,
            "successful_requests": report.successful_requests,
            "failed_requests": report.failed_requests,
            "git_changes": report.git_changes,
            "roadmap_updates": report.roadmap_updates,
            "new_tasks_created": report.new_tasks_created,
            "tasks_completed": report.tasks_completed,
            "departments_active": report.departments_active,
            "key_achievements": report.key_achievements,
            "issues_encountered": report.issues_encountered,
            "optimization_insights": report.optimization_insights
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def generate_weekly_report(
        self,
        roadmap_manager: RoadmapManager,
        weeks_back: int = 0
    ) -> WeeklyReport:
        """
        Génère le rapport hebdomadaire

        Args:
            roadmap_manager: Manager du roadmap
            weeks_back: Nombre de semaines en arrière (0 = cette semaine)

        Returns:
            WeeklyReport
        """
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday() + 7 * weeks_back)
        week_end = week_start + timedelta(days=6)

        # Charger tous les rapports quotidiens de la semaine
        daily_reports = self._load_daily_reports_in_range(week_start, week_end)

        # Agréger statistiques
        total_requests = sum(r.get("total_requests", 0) for r in daily_reports)
        successful = sum(r.get("successful_requests", 0) for r in daily_reports)
        success_rate = (successful / total_requests * 100) if total_requests > 0 else 0

        total_lines_added = sum(
            r.get("git_changes", {}).get("lines_added", 0)
            for r in daily_reports
        )
        total_lines_removed = sum(
            r.get("git_changes", {}).get("lines_removed", 0)
            for r in daily_reports
        )

        tasks_completed = sum(r.get("tasks_completed", 0) for r in daily_reports)
        tasks_created = sum(r.get("new_tasks_created", 0) for r in daily_reports)

        # Roadmap progress
        roadmap_summary = roadmap_manager.get_roadmap_summary()

        report = WeeklyReport(
            week_start=week_start,
            week_end=week_end,
            total_requests=total_requests,
            success_rate=success_rate,
            total_git_commits=len(daily_reports),  # Approximation
            total_lines_added=total_lines_added,
            total_lines_removed=total_lines_removed,
            tasks_completed=tasks_completed,
            tasks_created=tasks_created,
            roadmap_progress=roadmap_summary["completion_percentage"],
            top_performing_departments=[],  # À calculer
            top_success_patterns=[],  # Depuis optimization
            top_issues=[],  # Agréger issues
            recommendations=[]  # Générer automatiquement
        )

        # Sauvegarder rapport
        self._save_weekly_report(report)

        return report

    def _load_daily_reports_in_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Charge tous les rapports quotidiens dans une période"""
        reports = []

        current = start_date
        while current <= end_date:
            filename = self.reports_dir / f"daily_{current.strftime('%Y%m%d')}.json"

            if filename.exists():
                with open(filename, 'r', encoding='utf-8') as f:
                    reports.append(json.load(f))

            current += timedelta(days=1)

        return reports

    def _save_weekly_report(self, report: WeeklyReport):
        """Sauvegarde le rapport hebdomadaire"""
        filename = self.reports_dir / f"weekly_{report.week_start.strftime('%Y%m%d')}.json"

        data = {
            "week_start": report.week_start.isoformat(),
            "week_end": report.week_end.isoformat(),
            "total_requests": report.total_requests,
            "success_rate": report.success_rate,
            "total_git_commits": report.total_git_commits,
            "total_lines_added": report.total_lines_added,
            "total_lines_removed": report.total_lines_removed,
            "tasks_completed": report.tasks_completed,
            "tasks_created": report.tasks_created,
            "roadmap_progress": report.roadmap_progress,
            "top_performing_departments": report.top_performing_departments,
            "top_success_patterns": report.top_success_patterns,
            "top_issues": report.top_issues,
            "recommendations": report.recommendations
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def display_daily_report(self, report: DailyReport):
        """Affiche le rapport quotidien de manière lisible"""
        print("\n" + "="*70)
        print(f"📊 DAILY REPORT - {report.date.strftime('%Y-%m-%d')}")
        print("="*70 + "\n")

        # Requests
        print("📈 REQUESTS")
        print(f"  Total: {report.total_requests}")
        print(f"  Successful: {report.successful_requests}")
        print(f"  Failed: {report.failed_requests}")
        print()

        # Git changes
        if report.git_changes:
            print("💻 CODE CHANGES")
            print(f"  Files changed: {report.git_changes.get('total_files_changed', 0)}")
            print(f"  Added: {report.git_changes.get('files_added', 0)}")
            print(f"  Modified: {report.git_changes.get('files_modified', 0)}")
            print(f"  Deleted: {report.git_changes.get('files_deleted', 0)}")
            print(f"  Lines: +{report.git_changes.get('lines_added', 0)} -{report.git_changes.get('lines_removed', 0)}")
            print()

        # Roadmap
        print("📋 ROADMAP")
        print(f"  Progress: {report.roadmap_updates.get('completion_percentage', 0):.1f}%")
        print(f"  Total tasks: {report.roadmap_updates.get('total_tasks', 0)}")
        print(f"  Completed today: {report.tasks_completed}")
        print(f"  New tasks: {report.new_tasks_created}")
        print()

        # Departments
        print("🏢 ACTIVE DEPARTMENTS")
        for dept in report.departments_active:
            print(f"  - {dept}")
        print()

        # Key achievements
        if report.key_achievements:
            print("🎯 KEY ACHIEVEMENTS")
            for achievement in report.key_achievements:
                print(f"  ✓ {achievement}")
            print()

        # Issues
        if report.issues_encountered:
            print("⚠️  ISSUES ENCOUNTERED")
            for issue in report.issues_encountered:
                print(f"  ! {issue}")
            print()

        # Optimization insights
        if report.optimization_insights:
            print("💡 OPTIMIZATION INSIGHTS")
            for insight in report.optimization_insights:
                print(f"  → {insight}")
            print()

        print("="*70 + "\n")

    def display_weekly_report(self, report: WeeklyReport):
        """Affiche le rapport hebdomadaire"""
        print("\n" + "="*70)
        print(f"📊 WEEKLY REPORT - Week of {report.week_start.strftime('%Y-%m-%d')}")
        print("="*70 + "\n")

        print("📈 OVERVIEW")
        print(f"  Total requests: {report.total_requests}")
        print(f"  Success rate: {report.success_rate:.1f}%")
        print(f"  Git commits: {report.total_git_commits}")
        print(f"  Code changes: +{report.total_lines_added} -{report.total_lines_removed}")
        print()

        print("📋 TASKS")
        print(f"  Completed: {report.tasks_completed}")
        print(f"  Created: {report.tasks_created}")
        print(f"  Roadmap progress: {report.roadmap_progress:.1f}%")
        print()

        if report.top_performing_departments:
            print("🏆 TOP PERFORMING DEPARTMENTS")
            for dept in report.top_performing_departments:
                print(f"  {dept}")
            print()

        if report.top_success_patterns:
            print("✅ SUCCESS PATTERNS")
            for pattern in report.top_success_patterns:
                print(f"  → {pattern}")
            print()

        if report.top_issues:
            print("⚠️  TOP ISSUES")
            for issue in report.top_issues:
                print(f"  ! {issue}")
            print()

        if report.recommendations:
            print("💡 RECOMMENDATIONS")
            for rec in report.recommendations:
                print(f"  → {rec}")
            print()

        print("="*70 + "\n")


def create_ceo_reporter(reports_dir: str = "cortex/data/ceo_reports") -> CEOReporter:
    """Factory function"""
    return CEOReporter(reports_dir)


# Test
if __name__ == "__main__":
    print("Testing CEO Reporter...")

    reporter = create_ceo_reporter("cortex/data/test_ceo_reports")

    # Test 1: Envoyer alertes
    print("\n1. Sending alerts...")

    reporter.send_alert(
        title="Phase 3.2 Implementation Complete",
        message="All Phase 3.2 components have been implemented and tested successfully.",
        severity="success",
        source_department="development"
    )

    reporter.send_alert(
        title="High Memory Usage Detected",
        message="System is using 85% of available memory. Consider optimization.",
        severity="warning",
        source_department="monitoring"
    )

    print(f"✓ Sent 2 alerts")

    # Test 2: Afficher alertes actives
    print("\n2. Getting active alerts...")
    active_alerts = reporter.get_active_alerts()
    print(f"✓ Active alerts: {len(active_alerts)}")

    # Test 3: Générer rapport quotidien
    print("\n3. Generating daily report...")
    from cortex.departments.maintenance.roadmap_manager import RoadmapManager
    from cortex.departments.maintenance.git_diff_processor import GitDiffAnalysis, FileChange

    roadmap = RoadmapManager("cortex/data/test_roadmap.json")

    # Ajouter quelques tâches
    roadmap.add_task(
        title="Test task 1",
        description="Test",
        priority="high",
        estimated_hours=2.0
    )

    # Mock git analysis
    mock_git = GitDiffAnalysis(
        total_files_changed=5,
        files_added=["file1.py", "file2.py"],
        files_modified=["file3.py"],
        files_deleted=[],
        files_renamed={},
        total_lines_added=250,
        total_lines_removed=30,
        file_changes=[],
        diff_raw=""
    )

    daily_report = reporter.generate_daily_report(
        roadmap_manager=roadmap,
        git_analysis=mock_git,
        optimization_insights=["Pattern 'test-driven' shows 95% success rate"]
    )

    reporter.display_daily_report(daily_report)
    print("✓ Daily report generated")

    # Test 4: Générer rapport hebdomadaire
    print("\n4. Generating weekly report...")
    weekly_report = reporter.generate_weekly_report(roadmap)
    reporter.display_weekly_report(weekly_report)
    print("✓ Weekly report generated")

    print("\n✓ CEO Reporter works correctly!")
