"""
Git Integration Workflow - Système complet d'harmonisation automatique

NOUVEAU WORKFLOW COMPLET:
1. GitWatcherAgent (NANO) → Détecte et analyse les changements
2. HarmonizationAgent (GPT-5) → Génère PLAN d'harmonisation (ne l'exécute pas)
3. MaintenanceAgent (DEEPSEEK) → EXÉCUTE le plan d'harmonisation
4. TesterAgent (DEEPSEEK) → Vérifie besoins en tests (base_prompt logic)
5. CommunicationsAgent (NANO) → Résume workflow avec thinking transparent
6. ArchivistAgent → Met à jour les rapports
7. Tout est logué dans la DB automatiquement

Philosophie:
- Séparation planning (GPT-5) vs exécution (DEEPSEEK/specialized agents)
- Thinking transparent pour feedback utilisateur
- Tests intelligents basés sur logique, pas sur LLM
- Logs filtrés pour pertinence

Usage:
    # Manuel
    from cortex.core.git_integration_workflow import run_git_integration
    result = run_git_integration()

    # Post-commit hook
    .git/hooks/post-commit → python -m cortex.core.git_integration_workflow
"""

import sys
from typing import Dict, Any
from datetime import datetime

from cortex.core.llm_client import LLMClient
from cortex.agents.git_watcher_agent import create_git_watcher_agent
from cortex.agents.harmonization_agent import create_harmonization_agent
from cortex.agents.maintenance_agent import create_maintenance_agent
from cortex.agents.tester_agent import create_tester_agent
from cortex.agents.communications_agent import create_communications_agent
from cortex.agents.archivist_agent import create_archivist_agent
from cortex.repositories.changelog_repository import get_changelog_repository


def run_git_integration(mode: str = 'post_commit') -> Dict[str, Any]:
    """
    Exécute le workflow complet d'intégration Git

    Args:
        mode: 'post_commit', 'watch', 'manual'

    Returns:
        Résultat complet du workflow
    """
    print("\n" + "="*70)
    print("🔄 GIT INTEGRATION WORKFLOW")
    print("="*70)
    print(f"Mode: {mode}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    try:
        session_start = datetime.now()

        # Initialize agents
        llm_client = LLMClient()
        git_watcher = create_git_watcher_agent(llm_client)
        harmonization = create_harmonization_agent(llm_client)
        maintenance = create_maintenance_agent(llm_client)
        tester = create_tester_agent(llm_client)
        communications = create_communications_agent(llm_client)
        archivist = create_archivist_agent(llm_client)

        # Step 1: Git Watcher - Analyze changes
        print("1️⃣  GitWatcherAgent (NANO) - Analyzing changes...")
        print("-" * 70)

        if mode == 'post_commit':
            git_result = git_watcher.execute_with_tracking(
                "analyze_last_commit"
            )
        else:
            git_result = git_watcher.execute_with_tracking(
                "watch git changes"
            )

        if not git_result.success:
            print(f"   ❌ Git analysis failed: {git_result.error}")
            return {
                'success': False,
                'step': 'git_watcher',
                'error': git_result.error
            }

        git_data = git_result.content
        print(f"   ✅ Analysis complete")
        print(f"      Files changed: {git_data.get('changed_files', []).__len__()}")
        print(f"      Impact level: {git_data.get('analysis', {}).get('impact_level', 'unknown')}")
        print()

        # Step 2: Harmonization Agent - Generate PLAN (GPT-5)
        needs_harmonization = git_data.get('needs_harmonization', False)
        harmonization_plan = None
        maintenance_result_data = None
        testing_result_data = None

        if needs_harmonization:
            print("2️⃣  HarmonizationAgent (GPT-5) - Generating harmonization plan...")
            print("-" * 70)

            # Generate plan (HarmonizationAgent now only generates plan, doesn't execute)
            plan = harmonization.generate_harmonization_plan(
                changed_files=git_data.get('changed_files', []),
                git_analysis=git_data.get('analysis', {}),
                conflicts=None,
                architecture=None
            )

            if plan:
                harmonization_plan = plan
                print(f"   ✅ Plan generated (ADR ID: {plan.get('adr_id')})")
                print(f"      Title: {plan.get('title', 'Untitled')}")
                print(f"      Actions: {len(plan.get('actions', []))}")
                print(f"      Testing required: {plan.get('testing_required', False)}")
                print()

                # Step 3: MaintenanceAgent - EXECUTE the plan
                print("3️⃣  MaintenanceAgent (DEEPSEEK) - Executing harmonization plan...")
                print("-" * 70)

                maintenance_result = maintenance.execute_harmonization_plan(plan)

                if maintenance_result['success']:
                    print(f"   ✅ Plan executed successfully")
                    print(f"      Executed: {maintenance_result['executed']}")
                    print(f"      Failed: {maintenance_result['failed']}")
                    print(f"      Success rate: {maintenance_result['success_rate']*100:.1f}%")
                    maintenance_result_data = maintenance_result
                else:
                    print(f"   ❌ Plan execution failed: {maintenance_result.get('error')}")
                print()

                # Step 4: TesterAgent - Verify test requirements (base_prompt logic)
                if plan.get('testing_required', False):
                    print("4️⃣  TesterAgent (DEEPSEEK) - Analyzing test requirements...")
                    print("-" * 70)

                    test_analysis = tester.analyze_test_requirements(
                        changed_files=git_data.get('changed_files', []),
                        plan=plan
                    )

                    if test_analysis['success']:
                        print(f"   ✅ Test analysis complete")
                        print(f"      Tests required: {len(test_analysis['required_tests'])}")
                        print(f"      Tests existing: {len(test_analysis['existing_tests'])}")
                        print(f"      Tests missing: {len(test_analysis['missing_tests'])}")
                        print(f"      Coverage status: {test_analysis['coverage_status']}")

                        # If tests are missing, request creation
                        if test_analysis['missing_tests']:
                            print(f"      📝 Requesting {len(test_analysis['test_requests'])} test creations...")
                            tester.request_test_creation(test_analysis['test_requests'])

                        testing_result_data = test_analysis
                    else:
                        print(f"   ❌ Test analysis failed: {test_analysis.get('error')}")
                    print()
                else:
                    print("4️⃣  TesterAgent - Skipped (no testing required)")
                    print()

            else:
                print(f"   ❌ Plan generation failed")
                print()
        else:
            print("2️⃣  HarmonizationAgent - Skipped (low impact changes)")
            print()
            print("3️⃣  MaintenanceAgent - Skipped")
            print()
            print("4️⃣  TesterAgent - Skipped")
            print()

        # Step 5: CommunicationsAgent - Summarize workflow thinking
        print("5️⃣  CommunicationsAgent (NANO) - Summarizing workflow thinking...")
        print("-" * 70)

        communication_summary = communications.summarize_workflow(
            context={
                'session_start': session_start,
                'agents_involved': ['GitWatcherAgent', 'HarmonizationAgent', 'MaintenanceAgent', 'TesterAgent'],
                'focus': 'all'
            }
        )

        if communication_summary['success']:
            print(f"   ✅ Workflow summary generated")
            print(f"      Logs analyzed: {communication_summary['logs_analyzed']}")
            print(f"      Key decisions: {len(communication_summary['decisions'])}")
            print(f"      Alternatives found: {len(communication_summary['alternatives'])}")
            print()
            print("   " + "="*66)
            print("   📋 WORKFLOW THINKING SUMMARY")
            print("   " + "="*66)
            print()
            # Print summary (indented)
            for line in communication_summary['summary'].split('\n'):
                print(f"   {line}")
            print()
            # Print feedback prompt
            if communication_summary['feedback_prompt']:
                for line in communication_summary['feedback_prompt'].split('\n'):
                    print(f"   {line}")
            print()
        else:
            print(f"   ❌ Summary generation failed: {communication_summary.get('error')}")
        print()

        # Step 6: Archivist Agent - Update reports
        print("6️⃣  ArchivistAgent - Updating reports...")
        print("-" * 70)

        archivist_result = archivist.execute_with_tracking(
            "full synchronization"
        )

        if not archivist_result.success:
            print(f"   ❌ Report update failed: {archivist_result.error}")
            archivist_data = None
        else:
            archivist_data = archivist_result.content
            print(f"   ✅ Reports updated")
            if archivist_data.get('dashboard_generation', {}).get('success'):
                print(f"      Dashboard: ✅")
            if archivist_data.get('agent_report', {}).get('success'):
                print(f"      Agent report: ✅")
            if archivist_data.get('roadmap_sync', {}).get('success'):
                print(f"      Roadmap sync: ✅")
            print()

        # Step 7: Log to change_log
        print("7️⃣  Logging workflow completion...")
        print("-" * 70)

        changelog_repo = get_changelog_repository()
        changelog_repo.log_change(
            change_type='git_integration',
            entity_type='system',
            author='GitIntegrationWorkflow',
            description=f"Complete git integration workflow with thinking transparency ({mode})",
            impact_level=git_data.get('analysis', {}).get('impact_level', 'low'),
            metadata={
                'mode': mode,
                'files_changed': len(git_data.get('changed_files', [])),
                'harmonization_needed': needs_harmonization,
                'plan_generated': harmonization_plan is not None,
                'plan_executed': maintenance_result_data is not None,
                'tests_analyzed': testing_result_data is not None,
                'workflow_summarized': communication_summary['success'] if communication_summary else False
            }
        )

        print("   ✅ Workflow logged to database")
        print()

        # Summary
        print("="*70)
        print("✅ GIT INTEGRATION WORKFLOW COMPLETE")
        print("="*70)
        print()
        print(f"📊 Summary:")
        print(f"   Files changed: {len(git_data.get('changed_files', []))}")
        print(f"   Impact level: {git_data.get('analysis', {}).get('impact_level', 'unknown')}")
        print(f"   Plan generated: {'✅' if harmonization_plan else '⊘'}")
        if maintenance_result_data:
            print(f"   Plan executed: ✅ ({maintenance_result_data['executed']} actions)")
        if testing_result_data:
            print(f"   Tests analyzed: ✅ ({len(testing_result_data['required_tests'])} required)")
        print(f"   Workflow summarized: {'✅' if communication_summary['success'] else '❌'}")
        print(f"   Reports updated: {'✅' if archivist_data else '❌'}")
        print()
        print("="*70)

        result = {
            'success': True,
            'mode': mode,
            'timestamp': datetime.now().isoformat(),
            'session_start': session_start.isoformat(),
            'git_analysis': git_data,
            'harmonization_plan': harmonization_plan,
            'maintenance_result': maintenance_result_data,
            'testing_result': testing_result_data,
            'communication_summary': communication_summary,
            'archivist': archivist_data,
            'summary': {
                'files_changed': len(git_data.get('changed_files', [])),
                'impact_level': git_data.get('analysis', {}).get('impact_level', 'unknown'),
                'harmonization_needed': needs_harmonization,
                'plan_generated': harmonization_plan is not None,
                'actions_executed': maintenance_result_data['executed'] if maintenance_result_data else 0,
                'tests_required': len(testing_result_data['required_tests']) if testing_result_data else 0,
                'tests_missing': len(testing_result_data['missing_tests']) if testing_result_data else 0,
                'thinking_summary_available': communication_summary['success'] if communication_summary else False,
                'reports_updated': archivist_data is not None
            }
        }

        return result

    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()

        return {
            'success': False,
            'error': str(e),
            'mode': mode
        }


def install_git_hook():
    """
    Installe le hook post-commit pour surveillance automatique

    Creates .git/hooks/post-commit that runs this workflow
    """
    import os
    from pathlib import Path

    hook_path = Path('.git/hooks/post-commit')

    if not hook_path.parent.exists():
        print("❌ Not in a git repository")
        return False

    hook_content = """#!/usr/bin/env python3
\"\"\"
Post-commit hook - Automatically runs Git Integration Workflow
Generated by Cortex
\"\"\"
import sys
import os

# Add project to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Run git integration workflow
try:
    from cortex.core.git_integration_workflow import run_git_integration
    result = run_git_integration(mode='post_commit')

    if not result['success']:
        print(f"⚠️  Git integration workflow had issues: {result.get('error', 'unknown')}")
        # Don't fail the commit
        sys.exit(0)
    else:
        print(f"✅ Git integration complete")
        sys.exit(0)

except Exception as e:
    print(f"⚠️  Git hook failed: {e}")
    # Don't fail the commit
    sys.exit(0)
"""

    try:
        hook_path.write_text(hook_content)
        hook_path.chmod(0o755)  # Make executable
        print(f"✅ Git hook installed at {hook_path}")
        print("   Workflow will run automatically after each commit")
        return True
    except Exception as e:
        print(f"❌ Failed to install git hook: {e}")
        return False


def uninstall_git_hook():
    """Désinstalle le hook post-commit"""
    from pathlib import Path

    hook_path = Path('.git/hooks/post-commit')

    if hook_path.exists():
        hook_path.unlink()
        print(f"✅ Git hook removed from {hook_path}")
        return True
    else:
        print("ℹ️  No git hook found")
        return False


# CLI Interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Git Integration Workflow')
    parser.add_argument('action', choices=['run', 'install', 'uninstall'],
                       help='Action to perform')
    parser.add_argument('--mode', choices=['post_commit', 'watch', 'manual'],
                       default='manual', help='Workflow mode')

    args = parser.parse_args()

    if args.action == 'run':
        result = run_git_integration(mode=args.mode)
        sys.exit(0 if result['success'] else 1)
    elif args.action == 'install':
        success = install_git_hook()
        sys.exit(0 if success else 1)
    elif args.action == 'uninstall':
        success = uninstall_git_hook()
        sys.exit(0 if success else 1)
