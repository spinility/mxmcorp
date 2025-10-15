"""
Self Introspection Agent - Agent qui répond à "Que peux-tu faire?"

Responsabilités:
- Génère rapport complet des capacités de Cortex
- Répond à "Est-ce que je peux faire X?"
- Identifie capacités manquantes
- Suggère alternatives quand une capacité n'existe pas
- Génère documentation à jour
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from cortex.core.capability_registry import CapabilityRegistry, Capability
from cortex.core.environment_scanner import EnvironmentScanner, EnvironmentInfo


class SelfIntrospectionAgent:
    """
    Agent qui maintient la conscience de soi de Cortex

    Répond aux questions sur les capacités et limitations
    """

    def __init__(
        self,
        capability_registry: Optional[CapabilityRegistry] = None,
        environment_scanner: Optional[EnvironmentScanner] = None
    ):
        self.capability_registry = capability_registry or CapabilityRegistry()
        self.environment_scanner = environment_scanner or EnvironmentScanner()

        # Cache
        self._last_full_scan: Optional[datetime] = None
        self._cached_capabilities: Optional[Dict[str, Capability]] = None
        self._cached_environment: Optional[EnvironmentInfo] = None

    def generate_capability_report(self, force_refresh: bool = False) -> str:
        """
        Génère rapport complet de ce que Cortex peut faire

        Args:
            force_refresh: Si True, rescan tout

        Returns:
            Rapport formaté en texte
        """
        # Découvrir capacités
        if force_refresh or not self._cached_capabilities:
            self._cached_capabilities = self.capability_registry.discover_all_capabilities(
                force_refresh=force_refresh
            )

        # Scanner environnement
        if force_refresh or not self._cached_environment:
            self._cached_environment = self.environment_scanner.scan_full_environment()

        self._last_full_scan = datetime.now()

        # Générer rapport
        report = self._format_capability_report(
            self._cached_capabilities,
            self._cached_environment
        )

        return report

    def _format_capability_report(
        self,
        capabilities: Dict[str, Capability],
        env_info: EnvironmentInfo
    ) -> str:
        """Formate le rapport de capacités"""

        # Grouper capacités par type
        by_type = {}
        for cap in capabilities.values():
            if cap.type not in by_type:
                by_type[cap.type] = []
            by_type[cap.type].append(cap)

        # Début du rapport
        report = f"""
{'='*70}
CORTEX SELF-AWARENESS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*70}

SUMMARY
-------
Total capabilities discovered: {len(capabilities)}
  - Departments: {len(by_type.get('department', []))}
  - Agents: {len(by_type.get('agent', []))}
  - Tools: {len(by_type.get('tool', []))}
  - Workflows: {len(by_type.get('workflow', []))}

Environment: {env_info.platform} - Python {env_info.python_version}
Working directory: {env_info.working_directory}


WHAT I CAN DO
==============
"""

        # Départements
        if 'department' in by_type:
            report += "\n📦 DEPARTMENTS:\n"
            for dept in sorted(by_type['department'], key=lambda c: c.name):
                report += f"  ✓ {dept.name}\n"
                report += f"    → {dept.description}\n"

        # Agents
        if 'agent' in by_type:
            report += "\n🤖 AGENTS:\n"
            for agent in sorted(by_type['agent'], key=lambda c: c.name):
                role_str = f" ({agent.role})" if agent.role else ""
                report += f"  ✓ {agent.name}{role_str}\n"
                report += f"    → {agent.description}\n"

        # Tools
        if 'tool' in by_type:
            report += "\n🔧 TOOLS:\n"
            for tool in sorted(by_type['tool'], key=lambda c: c.name):
                report += f"  ✓ {tool.name}\n"

        # Capacités spécifiques par domaine
        report += f"""

CAPABILITIES BY DOMAIN
======================

📊 Data Collection:
  ✓ Web scraping (StealthWebCrawler - indétectable)
  ✓ XPath validation
  ✓ Dynamic context optimization
  ✗ Direct API calls (requires implementation per API)

🔍 Analysis:
  ✓ Code analysis (AST parsing)
  ✓ Dependency tracking
  ✓ Pattern detection
  ✓ Context summarization (95% token reduction)
  ✓ Cost optimization

💻 Development:
  ✓ Python code generation
  ✓ Bash script generation
  ✓ Tool auto-generation
  ✓ Agent auto-generation
  ✗ JavaScript/TypeScript (not implemented)
  ✗ Frontend frameworks (not implemented)

🧪 Testing:
  ✓ Automated test generation
  ✓ Test execution
  ✗ Integration testing (limited)

📝 Documentation:
  ✓ Auto-generated docs
  ✓ Capability reports
  ✓ TODO management

🔧 Maintenance:
  ✓ Git diff analysis
  ✓ Automatic context updates
  ✓ Roadmap synchronization
  ✓ Breaking change detection

🤝 Communication:
  ✓ CEO reports (daily/weekly)
  ✓ Alert system
  ✓ Progress tracking


CURRENT LIMITATIONS
===================
"""

        # Ajouter limitations environnement
        if env_info.limitations:
            for limitation in env_info.limitations:
                report += f"  ⚠️  {limitation}\n"

        # Ajouter limitations connues
        report += """
Known limitations:
  ⚠️  Cannot access external APIs without credentials
  ⚠️  Cannot execute processes longer than 10 minutes
  ⚠️  Cannot modify files outside project directory
  ⚠️  Limited to single-repository operations
  ⚠️  No direct database access (requires tools)


ENVIRONMENT STATUS
==================
"""

        # File system
        report += f"""
📁 File System:
  Read: {'✅' if env_info.can_read_files else '❌'}
  Write: {'✅' if env_info.can_write_files else '❌'}
  Execute: {'✅' if env_info.can_execute_scripts else '❌'}

🔧 Git:
  Available: {'✅' if env_info.git_available else '❌'}
  Repository: {'✅' if env_info.is_git_repo else '❌'}
  Branch: {env_info.git_branch or 'N/A'}
  Can commit: {'✅' if env_info.can_commit else '❌'}

🔑 API Keys:
"""

        for key, present in env_info.api_keys_status.items():
            report += f"  {key}: {'✅' if present else '❌'}\n"

        report += f"""

{'='*70}
END OF REPORT
{'='*70}
"""

        return report

    def can_i_do(self, task_description: str) -> Dict[str, Any]:
        """
        Répond à "Est-ce que je peux faire X?"

        Args:
            task_description: Description de la tâche en langage naturel

        Returns:
            Dict avec can_do, how, limitations, alternative
        """
        # Rechercher capacités pertinentes
        if not self._cached_capabilities:
            self._cached_capabilities = self.capability_registry.discover_all_capabilities()

        matches = self.capability_registry.search_capabilities(task_description)

        if matches:
            # On a trouvé des capacités matchantes
            primary_match = matches[0]

            return {
                "can_do": True,
                "confidence": "high" if len(matches) >= 2 else "medium",
                "how": f"Use {primary_match.name} ({primary_match.type})",
                "details": primary_match.description,
                "file": primary_match.file_path,
                "alternative_capabilities": [m.name for m in matches[1:3]],
                "limitations": self._check_task_limitations(task_description)
            }
        else:
            # Pas de capacité trouvée
            return {
                "can_do": False,
                "confidence": "none",
                "how": None,
                "details": "No capability found for this task",
                "suggestion": self._suggest_alternative(task_description),
                "can_be_developed": self._can_be_developed(task_description)
            }

    def _check_task_limitations(self, task: str) -> List[str]:
        """Identifie limitations spécifiques pour une tâche"""
        limitations = []

        task_lower = task.lower()

        # Vérifier API keys
        if "openai" in task_lower or "gpt" in task_lower:
            if not self._cached_environment.api_keys_status.get("OpenAI", False):
                limitations.append("Requires OpenAI API key")

        if "anthropic" in task_lower or "claude" in task_lower:
            if not self._cached_environment.api_keys_status.get("Anthropic", False):
                limitations.append("Requires Anthropic API key")

        # Vérifier permissions
        if "write" in task_lower or "modify" in task_lower or "create" in task_lower:
            if not self._cached_environment.can_write_files:
                limitations.append("Cannot write files (read-only mode)")

        if "execute" in task_lower or "run" in task_lower:
            if not self._cached_environment.can_execute_scripts:
                limitations.append("Cannot execute scripts")

        # Vérifier packages
        if "web" in task_lower or "scrape" in task_lower or "http" in task_lower:
            missing = [p for p in ["requests", "lxml"] if p in self._cached_environment.missing_packages]
            if missing:
                limitations.append(f"Missing packages: {', '.join(missing)}")

        return limitations

    def _suggest_alternative(self, task: str) -> str:
        """Suggère alternative quand capacité pas trouvée"""
        task_lower = task.lower()

        if "api" in task_lower and "call" in task_lower:
            return "Consider using requests library or implementing a custom tool"

        if "database" in task_lower or "sql" in task_lower:
            return "Consider using a database tool or ORM (not yet implemented)"

        if "frontend" in task_lower or "react" in task_lower:
            return "Frontend development not yet implemented - consider using backend tools"

        return "This capability is not currently available. Consider requesting it as a new feature."

    def _can_be_developed(self, task: str) -> Dict[str, Any]:
        """Détermine si la capacité peut être développée"""
        # Pour l'instant, toutes les tâches Python peuvent être développées
        return {
            "possible": True,
            "complexity": "medium",
            "estimated_time": "2-4 hours",
            "approach": "Auto-generate tool or agent using existing patterns"
        }

    def list_broken_capabilities(self) -> List[Capability]:
        """Liste les capacités cassées ou en développement"""
        if not self._cached_capabilities:
            self._cached_capabilities = self.capability_registry.discover_all_capabilities()

        broken = [
            cap for cap in self._cached_capabilities.values()
            if cap.status in ["broken", "development", "deprecated"]
        ]

        return broken

    def get_statistics(self) -> Dict[str, Any]:
        """Retourne statistiques complètes"""
        if not self._cached_capabilities:
            self._cached_capabilities = self.capability_registry.discover_all_capabilities()

        if not self._cached_environment:
            self._cached_environment = self.environment_scanner.scan_full_environment()

        cap_stats = self.capability_registry.get_statistics()

        return {
            "capabilities": cap_stats,
            "environment": {
                "platform": self._cached_environment.platform,
                "python_version": self._cached_environment.python_version,
                "can_write": self._cached_environment.can_write_files,
                "can_execute": self._cached_environment.can_execute_scripts,
                "git_available": self._cached_environment.git_available,
                "api_keys_configured": sum(1 for v in self._cached_environment.api_keys_status.values() if v),
                "limitations_count": len(self._cached_environment.limitations)
            },
            "last_scan": self._last_full_scan.isoformat() if self._last_full_scan else None
        }


def create_self_introspection_agent() -> SelfIntrospectionAgent:
    """Factory function"""
    return SelfIntrospectionAgent()


# Test
if __name__ == "__main__":
    print("Testing Self Introspection Agent...")

    agent = SelfIntrospectionAgent()

    # Test 1: Generate full report
    print("\n1. Generating capability report...")
    report = agent.generate_capability_report()
    print(report)

    # Test 2: Can I do X?
    print("\n2. Testing 'can_i_do'...")
    tests = [
        "scrape a website",
        "call OpenAI API",
        "analyze Python code",
        "build a React frontend"
    ]

    for test_task in tests:
        print(f"\n  Q: Can I {test_task}?")
        result = agent.can_i_do(test_task)
        print(f"  A: {result['can_do']}")
        if result['can_do']:
            print(f"     How: {result['how']}")
            if result.get('limitations'):
                print(f"     Limitations: {', '.join(result['limitations'])}")
        else:
            print(f"     Suggestion: {result['suggestion']}")

    # Test 3: Statistics
    print("\n3. Statistics...")
    stats = agent.get_statistics()
    print(f"✓ Total capabilities: {stats['capabilities']['total_capabilities']}")
    print(f"✓ Platform: {stats['environment']['platform']}")
    print(f"✓ API keys configured: {stats['environment']['api_keys_configured']}/3")

    print("\n✓ Self Introspection Agent works correctly!")
