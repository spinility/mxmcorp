"""
Archivist Agent - Pont entre DB et fichiers .md

ROLE: ORCHESTRATOR (Synchronisation) - Niveau 2.5 de la hiérarchie
TIER: NANO pour génération rapide

Responsabilités:
- Synchroniser roadmap.md <-> project table
- Générer rapports .md à partir de la DB
- Détecter modifications dans .md et mettre à jour DB
- Maintenir cohérence entre "vérité DB" et "narration MD"

Philosophy:
- La DB est la source de vérité (single source of truth)
- Les .md sont des vues générées (views)
- Synchronisation bidirectionnelle quand nécessaire
- Logs de tous les syncs pour auditabilité
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import re

from cortex.core.llm_client import LLMClient, ModelTier
from cortex.core.agent_hierarchy import CoordinationAgent, AgentRole, AgentResult
from cortex.database.database_manager import get_database_manager


class ArchivistAgent(CoordinationAgent):
    """Agent de synchronisation DB <-> MD"""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Archivist Agent

        Args:
            llm_client: Client LLM pour génération de texte
        """
        super().__init__(llm_client, specialization="archiving")
        self.db = get_database_manager()
        self.tier = ModelTier.NANO  # Rapide et économique

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """
        Évalue si l'Archiviste peut gérer la requête

        Keywords: sync, generate report, roadmap, archive, markdown
        """
        request_lower = request.lower()

        archivist_keywords = [
            'sync', 'synchronize', 'generate report', 'roadmap',
            'archive', 'markdown', 'update md', 'export', 'dashboard'
        ]

        if any(kw in request_lower for kw in archivist_keywords):
            return 0.9

        return 0.0

    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[Any] = None
    ) -> AgentResult:
        """
        Exécute une tâche d'archivage/synchronisation

        Args:
            request: Requête utilisateur
            context: Contexte optionnel
            escalation_context: Contexte si escalation

        Returns:
            AgentResult avec résultat de l'opération
        """
        # Parse request
        action = self._parse_archivist_request(request)

        result = {}
        cost = 0.0

        if action == 'sync_roadmap':
            result = self.sync_roadmap_md_to_db()
        elif action == 'generate_roadmap':
            result = self.generate_roadmap_md_from_db()
        elif action == 'generate_dashboard':
            result = self.generate_dashboard_report()
        elif action == 'generate_agent_report':
            result = self.generate_agent_performance_report()
        elif action == 'full_sync':
            result = self.full_synchronization()
        else:
            result = {
                'success': False,
                'error': f'Unknown archivist action: {action}'
            }

        return AgentResult(
            success=result.get('success', False),
            role=self.role,
            tier=self.tier,
            content=result,
            cost=cost,
            confidence=0.9,
            should_escalate=False,
            escalation_reason=None,
            error=result.get('error'),
            metadata={'action': action}
        )

    def _parse_archivist_request(self, request: str) -> str:
        """
        Parse la requête pour déterminer l'action

        Returns:
            Action: sync_roadmap, generate_roadmap, generate_dashboard, etc.
        """
        request_lower = request.lower()

        if 'sync' in request_lower and 'roadmap' in request_lower:
            return 'sync_roadmap'
        elif 'generate' in request_lower and 'roadmap' in request_lower:
            return 'generate_roadmap'
        elif 'dashboard' in request_lower or 'report' in request_lower:
            if 'agent' in request_lower:
                return 'generate_agent_report'
            else:
                return 'generate_dashboard'
        elif 'full' in request_lower and 'sync' in request_lower:
            return 'full_sync'
        else:
            return 'generate_dashboard'  # Default

    # ========================================
    # ROADMAP SYNCHRONIZATION
    # ========================================

    def sync_roadmap_md_to_db(self) -> Dict[str, Any]:
        """
        Lit roadmap.md et met à jour la DB

        Returns:
            Dict avec résultat de la synchronisation
        """
        try:
            roadmap_file = Path("roadmap.md")

            if not roadmap_file.exists():
                return {
                    'success': False,
                    'error': 'roadmap.md not found'
                }

            # Parse roadmap.md
            with open(roadmap_file, 'r') as f:
                content = f.read()

            projects = self._parse_roadmap_md(content)

            # Update DB
            synced = 0
            for project in projects:
                try:
                    self.db.add_project(
                        name=project['name'],
                        description=project.get('description'),
                        priority=project.get('priority', 5),
                        status=project.get('status', 'planned'),
                        target_date=project.get('target_date'),
                        metadata=project.get('metadata')
                    )
                    synced += 1
                except Exception as e:
                    print(f"Warning: Could not sync project {project['name']}: {e}")

            # Log change
            self.db.log_change(
                change_type='modify',
                entity_type='project',
                author='ArchivistAgent',
                description=f'Synchronized {synced} projects from roadmap.md to DB',
                impact_level='medium'
            )

            return {
                'success': True,
                'projects_synced': synced,
                'message': f'Successfully synced {synced} projects from roadmap.md'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Sync failed: {str(e)}'
            }

    def _parse_roadmap_md(self, content: str) -> List[Dict]:
        """
        Parse roadmap.md pour extraire les projets

        Format attendu:
        ## Project Name
        **Status:** in_progress
        **Priority:** 3
        **Target:** 2025-12-31

        Description du projet...

        Returns:
            Liste de projets
        """
        projects = []

        # Split by headers (##)
        sections = re.split(r'^## (.+)$', content, flags=re.MULTILINE)

        for i in range(1, len(sections), 2):
            if i+1 >= len(sections):
                break

            name = sections[i].strip()
            body = sections[i+1].strip()

            # Extract metadata
            status_match = re.search(r'\*\*Status:\*\*\s*(\w+)', body)
            priority_match = re.search(r'\*\*Priority:\*\*\s*(\d+)', body)
            target_match = re.search(r'\*\*Target:\*\*\s*(\d{4}-\d{2}-\d{2})', body)

            # Extract description (first paragraph after metadata)
            description_match = re.search(r'\n\n([^\n]+)', body)

            projects.append({
                'name': name,
                'description': description_match.group(1) if description_match else None,
                'status': status_match.group(1) if status_match else 'planned',
                'priority': int(priority_match.group(1)) if priority_match else 5,
                'target_date': target_match.group(1) if target_match else None,
                'metadata': {'source': 'roadmap.md'}
            })

        return projects

    def generate_roadmap_md_from_db(self) -> Dict[str, Any]:
        """
        Génère roadmap.md à partir de la DB

        Returns:
            Dict avec résultat de la génération
        """
        try:
            # Get all projects from DB
            projects = self.db.get_active_projects()

            # Generate markdown
            md_content = self._generate_roadmap_markdown(projects)

            # Write to file
            roadmap_file = Path("roadmap.md")
            with open(roadmap_file, 'w') as f:
                f.write(md_content)

            # Log change
            self.db.log_change(
                change_type='create',
                entity_type='project',
                author='ArchivistAgent',
                description=f'Generated roadmap.md from DB ({len(projects)} projects)',
                impact_level='low'
            )

            return {
                'success': True,
                'projects_exported': len(projects),
                'file': str(roadmap_file),
                'message': f'Successfully generated roadmap.md with {len(projects)} projects'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Generation failed: {str(e)}'
            }

    def _generate_roadmap_markdown(self, projects: List[Dict]) -> str:
        """
        Génère le contenu markdown de la roadmap

        Args:
            projects: Liste de projets de la DB

        Returns:
            Contenu markdown
        """
        md = "# Cortex Roadmap\n\n"
        md += f"*Generated by ArchivistAgent on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        md += "---\n\n"

        # Group by status
        statuses = {}
        for project in projects:
            status = project['status']
            if status not in statuses:
                statuses[status] = []
            statuses[status].append(project)

        # Sort statuses
        status_order = ['in_progress', 'planned', 'blocked', 'completed']

        for status in status_order:
            if status not in statuses:
                continue

            md += f"## {status.replace('_', ' ').title()}\n\n"

            for project in sorted(statuses[status], key=lambda p: p['priority']):
                md += f"### {project['name']}\n\n"
                md += f"**Priority:** {project['priority']}/10\n"
                md += f"**Status:** {project['status']}\n"
                md += f"**Progress:** {project['progress_percent']:.0f}%\n"

                if project.get('owner_agent'):
                    md += f"**Owner:** {project['owner_agent']}\n"

                if project.get('target_date'):
                    md += f"**Target:** {project['target_date']}\n"

                if project.get('description'):
                    md += f"\n{project['description']}\n"

                md += "\n---\n\n"

        return md

    # ========================================
    # DASHBOARD & REPORTS
    # ========================================

    def generate_dashboard_report(self) -> Dict[str, Any]:
        """
        Génère un dashboard complet avec métriques système

        Returns:
            Dict avec résultat de la génération
        """
        try:
            health = self.db.get_system_health()
            top_agents = self.db.get_top_performing_agents(5)
            overdue = self.db.get_overdue_projects()
            critical_deps = self.db.get_critical_dependencies()
            recent_changes = self.db.get_recent_changes(20, 'high')

            # Generate markdown
            md_content = self._generate_dashboard_markdown(
                health, top_agents, overdue, critical_deps, recent_changes
            )

            # Write to file
            report_file = Path("cortex/reports/dashboard.md")
            report_file.parent.mkdir(parents=True, exist_ok=True)

            with open(report_file, 'w') as f:
                f.write(md_content)

            return {
                'success': True,
                'file': str(report_file),
                'message': f'Dashboard generated at {report_file}'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Dashboard generation failed: {str(e)}'
            }

    def _generate_dashboard_markdown(
        self,
        health: Dict,
        top_agents: List[Dict],
        overdue: List[Dict],
        critical_deps: List[Dict],
        recent_changes: List[Dict]
    ) -> str:
        """Génère le markdown du dashboard"""

        md = "# Cortex Intelligence Dashboard\n\n"
        md += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        md += "---\n\n"

        # System Health
        md += "## 🧠 System Health\n\n"
        md += f"- **Total Agents:** {health['agents']['total_agents']} ({health['agents']['active_agents']} active)\n"
        avg_sr = health['agents'].get('avg_success_rate') or 0.0
        md += f"- **Success Rate:** {avg_sr*100:.1f}%\n"
        md += f"- **Total Cost:** ${health['agents']['total_cost']:.6f}\n"
        md += f"- **Total Executions:** {health['agents']['total_executions']:,}\n\n"

        # Projects
        md += "## 📋 Projects\n\n"
        md += f"- **Total:** {health['projects']['total_projects']}\n"
        md += f"- **Completed:** {health['projects']['completed_projects']}\n"
        md += f"- **In Progress:** {health['projects']['in_progress_projects']}\n"
        md += f"- **Blocked:** {health['projects']['blocked_projects']}\n"
        md += f"- **Average Progress:** {health['projects']['avg_progress']:.1f}%\n\n"

        # Top Performing Agents
        md += "## 🏆 Top Performing Agents\n\n"
        for agent in top_agents:
            md += f"### {agent['name']} ({agent['role']})\n"
            md += f"- **Tier:** {agent['tier']}\n"
            md += f"- **Success Rate:** {agent['success_rate']*100:.1f}%\n"
            md += f"- **Total Executions:** {agent['total_executions']:,}\n"
            md += f"- **Total Cost:** ${agent['total_cost']:.6f}\n"
            md += f"- **Avg Response Time:** {agent['avg_response_time']:.2f}s\n\n"

        # Overdue Projects
        if overdue:
            md += "## ⚠️ Overdue Projects\n\n"
            for project in overdue:
                md += f"### {project['name']}\n"
                md += f"- **Priority:** {project['priority']}/10\n"
                md += f"- **Progress:** {project['progress_percent']:.0f}%\n"
                md += f"- **Days Overdue:** {project['days_overdue']:.0f}\n"
                md += f"- **Owner:** {project['owner_agent'] or 'Unassigned'}\n\n"

        # Critical Dependencies
        if critical_deps:
            md += "## 🔗 Critical Dependencies\n\n"
            for dep in critical_deps[:10]:
                md += f"- `{dep['source_file']}` → `{dep['target_file']}` ({dep['dependency_type']})\n"
            md += "\n"

        # Recent High-Impact Changes
        if recent_changes:
            md += "## 📝 Recent High-Impact Changes\n\n"
            for change in recent_changes[:10]:
                md += f"### {change['description']}\n"
                md += f"- **Type:** {change['change_type']} ({change['entity_type']})\n"
                md += f"- **Author:** {change['author']}\n"
                md += f"- **Impact:** {change['impact_level']}\n"
                md += f"- **Date:** {change['timestamp']}\n\n"

        md += "---\n\n"
        md += "*This dashboard is auto-generated from the Cortex Intelligence Database.*\n"

        return md

    def generate_agent_performance_report(self) -> Dict[str, Any]:
        """
        Génère un rapport détaillé des performances des agents

        Returns:
            Dict avec résultat de la génération
        """
        try:
            # Get all agents stats
            agents = self.db.execute_query("""
                SELECT * FROM agent
                WHERE status = 'active'
                ORDER BY success_rate DESC, total_cost ASC
            """)

            # Generate markdown
            md_content = self._generate_agent_report_markdown(agents)

            # Write to file
            report_file = Path("cortex/reports/agent_performance.md")
            report_file.parent.mkdir(parents=True, exist_ok=True)

            with open(report_file, 'w') as f:
                f.write(md_content)

            return {
                'success': True,
                'file': str(report_file),
                'agents_analyzed': len(agents),
                'message': f'Agent performance report generated with {len(agents)} agents'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Report generation failed: {str(e)}'
            }

    def _generate_agent_report_markdown(self, agents: List[Dict]) -> str:
        """Génère le markdown du rapport agents"""

        md = "# Cortex Agent Performance Report\n\n"
        md += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        md += "---\n\n"

        for agent in agents:
            md += f"## {agent['name']}\n\n"
            md += f"**Role:** {agent['role']}\n"
            md += f"**Type:** {agent['type']}\n"
            md += f"**Tier:** {agent['tier']}\n"
            md += f"**Specialization:** {agent['specialization'] or 'N/A'}\n"
            md += f"**Expertise Level:** {agent['expertise_level']}/10\n\n"

            md += "### Performance Metrics\n\n"
            md += f"- **Total Executions:** {agent['total_executions']:,}\n"
            md += f"- **Success Rate:** {agent['success_rate']*100:.1f}%\n"
            md += f"- **Total Cost:** ${agent['total_cost']:.6f}\n"
            md += f"- **Avg Cost per Execution:** ${(agent['total_cost'] / agent['total_executions']) if agent['total_executions'] > 0 else 0:.6f}\n"
            md += f"- **Avg Response Time:** {agent['avg_response_time']:.2f}s\n"
            md += f"- **Last Active:** {agent['last_active'] or 'Never'}\n\n"

            # Performance grade
            grade = self._calculate_agent_grade(agent)
            md += f"**Performance Grade:** {grade}\n\n"

            md += "---\n\n"

        return md

    def _calculate_agent_grade(self, agent: Dict) -> str:
        """Calcule le grade de performance d'un agent"""
        success_rate = agent['success_rate']
        executions = agent['total_executions']

        if executions < 10:
            return "N/A (insufficient data)"

        if success_rate >= 0.95:
            return "A+ (Excellent)"
        elif success_rate >= 0.90:
            return "A (Very Good)"
        elif success_rate >= 0.80:
            return "B (Good)"
        elif success_rate >= 0.70:
            return "C (Acceptable)"
        else:
            return "D (Needs Improvement)"

    # ========================================
    # FULL SYNCHRONIZATION
    # ========================================

    def full_synchronization(self) -> Dict[str, Any]:
        """
        Synchronisation complète de tous les domaines

        Returns:
            Dict avec résultats de la synchronisation
        """
        results = {
            'roadmap_sync': self.sync_roadmap_md_to_db(),
            'dashboard_generation': self.generate_dashboard_report(),
            'agent_report': self.generate_agent_performance_report()
        }

        success = all(r.get('success', False) for r in results.values())

        return {
            'success': success,
            'results': results,
            'message': 'Full synchronization complete' if success else 'Some operations failed'
        }


def create_archivist_agent(llm_client: LLMClient) -> ArchivistAgent:
    """Factory function pour créer un ArchivistAgent"""
    return ArchivistAgent(llm_client)


# Test
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    print("📚 Testing Archivist Agent...\n")

    client = LLMClient()
    agent = ArchivistAgent(client)

    # Test dashboard generation
    result = agent.generate_dashboard_report()

    if result['success']:
        print(f"✅ Dashboard generated: {result['file']}")
    else:
        print(f"❌ Failed: {result.get('error')}")
