#!/usr/bin/env python3
"""
Script pour créer la structure organisée des agents par département

Chaque agent aura:
- Son propre dossier dans son département
- base_prompt.md avec son prompt de base
- memory.json pour sa mémoire interne
- __init__.py qui importe l'agent depuis cortex/agents/
"""

import os
from pathlib import Path
import json

# Mapping agents → départements
AGENT_STRUCTURE = {
    'intelligence': {
        'description': 'Recherche, Analyse, Détection',
        'agents': {
            'git_watcher': {
                'name': 'GitWatcherAgent',
                'file': 'git_watcher_agent.py',
                'role': 'Git Change Detection & Analysis',
                'tier': 'NANO',
                'description': 'Détecte et analyse les changements Git pour déclencher workflows'
            },
            'context': {
                'name': 'ContextAgent',
                'file': 'context_agent.py',
                'role': 'Context Preparation',
                'tier': 'DEEPSEEK',
                'description': 'Prépare le contexte pertinent pour les agents'
            },
            'tooler': {
                'name': 'ToolerAgent',
                'file': 'tooler_agent.py',
                'role': 'Tool Research',
                'tier': 'DEEPSEEK',
                'description': 'Recherche outils, packages et solutions externes'
            }
        }
    },
    'maintenance': {
        'description': 'Maintenance Système, Harmonisation',
        'agents': {
            'maintenance': {
                'name': 'MaintenanceAgent',
                'file': 'maintenance_agent.py',
                'role': 'System Maintenance',
                'tier': 'DEEPSEEK',
                'description': 'Exécute plans d\'harmonisation et maintient le système'
            },
            'harmonization': {
                'name': 'HarmonizationAgent',
                'file': 'harmonization_agent.py',
                'role': 'Architecture Harmonization',
                'tier': 'GPT5',
                'description': 'Génère plans d\'harmonisation architecturale (planning uniquement)'
            },
            'archivist': {
                'name': 'ArchivistAgent',
                'file': 'archivist_agent.py',
                'role': 'Reports & Archives',
                'tier': 'DEEPSEEK',
                'description': 'Génère rapports et maintient archives système'
            }
        }
    },
    'communication': {
        'description': 'Communication, Routage',
        'agents': {
            'communications': {
                'name': 'CommunicationsAgent',
                'file': 'communications_agent.py',
                'role': 'User Communications',
                'tier': 'NANO',
                'description': 'Résume workflows avec thinking transparent pour l\'utilisateur'
            },
            'triage': {
                'name': 'TriageAgent',
                'file': 'triage_agent.py',
                'role': 'Request Routing',
                'tier': 'NANO',
                'description': 'Routage initial des requêtes utilisateur'
            },
            'smart_router': {
                'name': 'SmartRouterAgent',
                'file': 'smart_router_agent.py',
                'role': 'Department Routing',
                'tier': 'NANO',
                'description': 'Route requêtes vers départements appropriés'
            }
        }
    },
    'optimization': {
        'description': 'Qualité, Tests, Performance',
        'agents': {
            'quality_control': {
                'name': 'QualityControlAgent',
                'file': 'quality_control_agent.py',
                'role': 'Quality Evaluation',
                'tier': 'DEEPSEEK',
                'description': 'Évalue qualité des résultats et détecte problèmes'
            },
            'tester': {
                'name': 'TesterAgent',
                'file': 'tester_agent.py',
                'role': 'Test Analysis & Validation',
                'tier': 'DEEPSEEK',
                'description': 'Détermine besoins en tests (base_prompt logic) et valide code'
            }
        }
    },
    'execution': {
        'description': 'Planification, Exécution Tâches',
        'agents': {
            'planner': {
                'name': 'PlannerAgent',
                'file': 'planner_agent.py',
                'role': 'Task Planning',
                'tier': 'DEEPSEEK',
                'description': 'Planifie décomposition et exécution des tâches'
            },
            'quick_actions': {
                'name': 'QuickActionsAgent',
                'file': 'quick_actions_agent.py',
                'role': 'Atomic Operations',
                'tier': 'NANO',
                'description': 'Exécute actions rapides et atomiques'
            }
        }
    }
}


def create_base_prompt(agent_info):
    """Génère le base_prompt.md pour un agent"""
    return f"""# {agent_info['name']} - Base Prompt

## Role
**{agent_info['role']}**

## Tier
**{agent_info['tier']}**

## Description
{agent_info['description']}

## Core Responsibilities

[À définir: Listez les responsabilités clés de cet agent]

## Decision Logic (Base Prompt)

[À définir: Logique de décision de base sans LLM - règles explicites]

## Trigger Conditions

[À définir: Quand cet agent doit être activé]

## Input Requirements

[À définir: Quel contexte/données l'agent nécessite]

## Output Format

[À définir: Format de sortie attendu]

## Escalation Criteria

[À définir: Quand escalader vers tier supérieur]

## Examples

### Example 1
**Input:** [Description]
**Processing:** [Étapes]
**Output:** [Résultat]

### Example 2
**Input:** [Description]
**Processing:** [Étapes]
**Output:** [Résultat]

## Memory Management

Cet agent utilise `memory.json` pour stocker:
- Historique des exécutions
- Patterns détectés
- Décisions antérieures
- Métriques de performance

## Integration Points

- **Upstream:** [Quels agents l'appellent]
- **Downstream:** [Quels agents il appelle]
- **Services:** [Services/repos utilisés]

## Notes

[Notes additionnelles, limitations connues, améliorations futures]
"""


def create_memory_schema():
    """Schéma de base pour memory.json"""
    return {
        "version": "1.0.0",
        "last_updated": None,
        "execution_history": [],
        "learned_patterns": {},
        "performance_metrics": {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "avg_execution_time": 0.0,
            "total_cost": 0.0
        },
        "state": {},
        "notes": []
    }


def create_agent_init(agent_info):
    """Crée __init__.py qui importe l'agent"""
    return f'''"""
{agent_info['name']} - {agent_info['role']}

Auto-generated import from cortex.agents.{agent_info['file'].replace('.py', '')}
"""

from cortex.agents.{agent_info['file'].replace('.py', '')} import {agent_info['name']}, create_{agent_info['file'].replace('_agent.py', '_agent')}

__all__ = ['{agent_info['name']}', 'create_{agent_info['file'].replace('_agent.py', '_agent')}']
'''


def create_readme(department, dept_info):
    """Crée README.md pour le département"""
    agents_list = '\n'.join([
        f"- **{info['name']}** ({info['tier']}): {info['description']}"
        for info in dept_info['agents'].values()
    ])

    return f"""# {department.title()} Department

{dept_info['description']}

## Agents

{agents_list}

## Structure

```
{department}/
  agents/
    [agent_name]/
      base_prompt.md  # Prompt de base et logique
      memory.json     # Mémoire interne persistante
      __init__.py     # Import depuis cortex/agents/
```

## Philosophy

Chaque agent dans ce département a:
- **Autonomie**: Son propre dossier avec prompt et mémoire
- **Spécialisation**: Rôle clair dans le département
- **Traçabilité**: Historique d'exécutions dans memory.json
- **Évolution**: Base prompt évolutif selon apprentissages

## Memory System

La mémoire interne (`memory.json`) stocke:
- Historique des exécutions
- Patterns détectés au fil du temps
- Décisions antérieures et leur contexte
- Métriques de performance

Cette mémoire permet aux agents d'apprendre et de s'améliorer.
"""


def setup_structure():
    """Crée toute la structure des agents par département"""
    base_path = Path('cortex/departments')

    print("🏗️  Setting up agent structure by department...\n")

    for department, dept_info in AGENT_STRUCTURE.items():
        print(f"📁 {department.upper()} Department")
        print(f"   {dept_info['description']}")

        # Créer dossier département si n'existe pas
        dept_path = base_path / department
        dept_path.mkdir(parents=True, exist_ok=True)

        # Créer README du département
        readme_path = dept_path / 'README.md'
        readme_path.write_text(create_readme(department, dept_info))
        print(f"   ✓ {readme_path}")

        # Créer dossier agents
        agents_path = dept_path / 'agents'
        agents_path.mkdir(exist_ok=True)

        # Créer __init__.py pour agents/
        agents_init = agents_path / '__init__.py'
        agents_init.write_text(f'"""{department.title()} Department Agents"""\n')
        print(f"   ✓ {agents_init}")

        # Créer chaque agent
        for agent_name, agent_info in dept_info['agents'].items():
            agent_path = agents_path / agent_name
            agent_path.mkdir(exist_ok=True)

            # base_prompt.md
            prompt_path = agent_path / 'base_prompt.md'
            prompt_path.write_text(create_base_prompt(agent_info))
            print(f"   ✓ {prompt_path}")

            # memory.json
            memory_path = agent_path / 'memory.json'
            memory_path.write_text(json.dumps(create_memory_schema(), indent=2))
            print(f"   ✓ {memory_path}")

            # __init__.py
            init_path = agent_path / '__init__.py'
            init_path.write_text(create_agent_init(agent_info))
            print(f"   ✓ {init_path}")

        print()

    print("✅ Agent structure setup complete!")
    print("\n📊 Summary:")
    for department, dept_info in AGENT_STRUCTURE.items():
        print(f"   {department}: {len(dept_info['agents'])} agents")
    print(f"\n   Total: {sum(len(d['agents']) for d in AGENT_STRUCTURE.values())} agents across {len(AGENT_STRUCTURE)} departments")


if __name__ == '__main__':
    setup_structure()
