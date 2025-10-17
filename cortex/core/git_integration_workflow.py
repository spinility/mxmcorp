"""
Git Integration Workflow - Système complet d'harmonisation automatique

Ce module orchestre la surveillance Git et l'harmonisation automatique :
1. GitWatcherAgent → Détecte et analyse les changements
2. HarmonizationAgent → Valide et harmonise si nécessaire
3. ArchivistAgent → Met à jour les rapports
4. Tout est logué dans la DB automatiquement

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
        # Initialize agents
        llm_client = LLMClient()
        git_watcher = create_git_watcher_agent(llm_client)
        harmonization = create_harmonization_agent(llm_client)
        archivist = create_archivist_agent(llm_client)

        # Step 1: Git Watcher - Analyze changes
        print("1️⃣  GitWatcherAgent - Analyzing changes...")
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

        # Step 2: Harmonization Agent - Check consistency
        needs_harmonization = git_data.get('needs_harmonization', False)

        if needs_harmonization:
            print("2️⃣  HarmonizationAgent - Checking consistency...")
            print("-" * 70)

            harmonization_result = harmonization.execute_with_tracking(
                "harmonize changes",
                context={
                    'changed_files': git_data.get('changed_files', []),
                    'git_analysis': git_data.get('analysis', {}),
                    'commit_hash': git_data.get('commit', {}).get('hash')
                }
            )

            if not harmonization_result.success:
                print(f"   ❌ Harmonization failed: {harmonization_result.error}")
                harmonization_data = None
            else:
                harmonization_data = harmonization_result.content
                conflicts = harmonization_data.get('conflicts', {})

                print(f"   ✅ Harmonization complete")
                print(f"      Conflicts detected: {conflicts.get('conflict_count', 0)}")
                print(f"      Severity: {conflicts.get('severity', 'none')}")

                if harmonization_data.get('harmonization_plan'):
                    print(f"      🔧 Harmonization plan generated")
                    plan = harmonization_data['harmonization_plan']
                    if plan.get('actions'):
                        print(f"      Actions needed: {len(plan['actions'])}")

                if harmonization_data.get('needs_specialist'):
                    print(f"      ⚠️  Requires specialist agent review")

                print()
        else:
            print("2️⃣  HarmonizationAgent - Skipped (low impact changes)")
            print()
            harmonization_data = None

        # Step 3: Archivist Agent - Update reports
        print("3️⃣  ArchivistAgent - Updating reports...")
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

        # Step 4: Log to change_log
        print("4️⃣  Logging workflow completion...")
        print("-" * 70)

        changelog_repo = get_changelog_repository()
        changelog_repo.log_change(
            change_type='git_integration',
            entity_type='system',
            author='GitIntegrationWorkflow',
            description=f"Git integration workflow completed ({mode})",
            impact_level=git_data.get('analysis', {}).get('impact_level', 'low'),
            metadata={
                'mode': mode,
                'files_changed': len(git_data.get('changed_files', [])),
                'harmonization_needed': needs_harmonization,
                'conflicts_found': harmonization_data.get('conflicts', {}).get('conflict_count', 0) if harmonization_data else 0
            }
        )

        print("   ✅ Workflow logged to database")
        print()

        # Summary
        print("="*70)
        print("✅ GIT INTEGRATION WORKFLOW COMPLETE")
        print("="*70)

        result = {
            'success': True,
            'mode': mode,
            'timestamp': datetime.now().isoformat(),
            'git_analysis': git_data,
            'harmonization': harmonization_data,
            'archivist': archivist_data,
            'summary': {
                'files_changed': len(git_data.get('changed_files', [])),
                'impact_level': git_data.get('analysis', {}).get('impact_level', 'unknown'),
                'harmonization_needed': needs_harmonization,
                'conflicts_found': harmonization_data.get('conflicts', {}).get('conflict_count', 0) if harmonization_data else 0,
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
