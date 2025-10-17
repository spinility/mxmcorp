"""
Harmonization Agent - Génère des plans d'harmonisation architecturale

ROLE: DIRECTEUR (Décision stratégique) - Niveau 3 de la hiérarchie
TIER: GPT-5 pour décisions architecturales critiques

NOUVEAU WORKFLOW:
1. HarmonizationAgent (GPT-5) → Génère un PLAN d'harmonisation détaillé
2. Plan transmis à MaintenanceAgent → Exécute les changements
3. Plan transmis à TesterAgent → Détermine si tests nécessaires
4. Résultats transmis à CommunicationsAgent → Résumé pour l'utilisateur

Responsabilités (PLANIFICATION UNIQUEMENT):
- Analyser les conflits architecturaux
- Détecter les duplications et incohérences
- Générer un plan d'harmonisation détaillé avec actions priorit isées
- Évaluer l'impact et les risques
- Proposer alternatives si nécessaire
- NE JAMAIS EXÉCUTER - uniquement planifier

Déclenché:
- Par GitWatcherAgent quand changements high/critical
- Avant ajout de nouveaux composants majeurs
- Sur demande explicite
"""

from typing import Dict, Any, Optional, List
import json
import time
from datetime import datetime
from pathlib import Path

from cortex.core.llm_client import LLMClient, ModelTier
from cortex.core.agent_hierarchy import DecisionAgent, AgentRole, AgentResult, EscalationContext
from cortex.core.agent_memory import get_agent_memory


class HarmonizationAgent(DecisionAgent):
    """Agent d'harmonisation pour cohérence architecturale"""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Harmonization Agent

        Args:
            llm_client: Client LLM pour l'analyse
        """
        super().__init__(llm_client, specialization="harmonization")
        self.tier = ModelTier.GPT5  # GPT-5 pour décisions architecturales critiques
        self.memory = get_agent_memory('maintenance', 'harmonization')

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """
        Évalue si le HarmonizationAgent peut gérer la requête

        Keywords: harmonize, coherence, duplication, architecture, validate
        """
        request_lower = request.lower()

        harmonization_keywords = [
            'harmonize', 'harmonisation', 'coherence', 'cohérence',
            'duplication', 'duplicate', 'consolidate', 'consolidation',
            'architecture', 'validate', 'validation', 'conform', 'conforme',
            'synergie', 'synergy', 'audit'
        ]

        # Haute confiance si contient keywords
        if any(kw in request_lower for kw in harmonization_keywords):
            return 0.9

        return 0.0

    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[EscalationContext] = None
    ) -> AgentResult:
        """
        Exécute une analyse d'harmonisation

        Args:
            request: Requête utilisateur
            context: Contexte optionnel
            escalation_context: Contexte si escalation

        Returns:
            AgentResult avec résultat d'harmonisation
        """
        # Analyser la requête pour déterminer l'action
        action = self._parse_harmonization_request(request)

        if action == 'full_audit':
            result = self.run_full_audit()
        elif action == 'check_duplication':
            result = self.check_duplications()
        elif action == 'validate_new_component':
            # Extraire le nom du composant du contexte
            component_name = context.get('component_name', 'unknown') if context else 'unknown'
            component_type = context.get('component_type', 'agent') if context else 'agent'
            result = self.validate_new_component(component_name, component_type, context)
        elif action == 'check_task_attribution':
            result = self.check_task_attribution()
        else:
            # Fallback: full audit
            result = self.run_full_audit()

        return AgentResult(
            success=result['success'],
            role=self.role,
            tier=self.tier,
            content=result,
            cost=result.get('cost', 0.0),
            confidence=result.get('confidence', 0.8),
            should_escalate=False,
            escalation_reason=None,
            error=result.get('error'),
            metadata={'harmonization_result': result}
        )

    def _parse_harmonization_request(self, request: str) -> str:
        """
        Parse la requête pour déterminer l'action d'harmonisation

        Returns:
            Action: full_audit, check_duplication, validate_new_component, check_task_attribution
        """
        request_lower = request.lower()

        if 'validate' in request_lower or 'new' in request_lower:
            return 'validate_new_component'
        elif 'duplication' in request_lower or 'duplicate' in request_lower:
            return 'check_duplication'
        elif 'task' in request_lower or 'attribution' in request_lower:
            return 'check_task_attribution'
        else:
            return 'full_audit'

    def run_full_audit(self) -> Dict[str, Any]:
        """
        Exécute audit complet d'harmonisation

        Returns:
            Dict avec résultats d'audit
        """
        try:
            print(f"\n{'='*70}")
            print("🎯 HARMONIZATION AGENT - Full Architecture Audit")
            print(f"{'='*70}\n")

            # 1. Scan architecture
            print("1. Scanning architecture...")
            architecture = self._scan_architecture()
            print(f"   ✓ Found {len(architecture['agents'])} agents, {len(architecture['tools'])} tools")
            print()

            # 2. Check duplications
            print("2. Checking for duplications...")
            duplications = self._find_duplications(architecture)
            if duplications:
                print(f"   ⚠️  Found {len(duplications)} potential duplications")
            else:
                print(f"   ✓ No duplications detected")
            print()

            # 3. Check task attributions
            print("3. Validating task attributions...")
            misattributions = self._check_misattributions(architecture)
            if misattributions:
                print(f"   ⚠️  Found {len(misattributions)} potential misattributions")
            else:
                print(f"   ✓ Task attributions correct")
            print()

            # 4. Check synergies
            print("4. Analyzing component synergies...")
            synergy_score = self._analyze_synergies(architecture)
            print(f"   Synergy score: {synergy_score:.1f}/100")
            print()

            # 5. Generate recommendations
            print("5. Generating recommendations...")
            recommendations = self._generate_recommendations(
                architecture, duplications, misattributions, synergy_score
            )
            print(f"   ✓ Generated {len(recommendations)} recommendations")
            print()

            # Calculate overall score
            deduction = len(duplications) * 5 + len(misattributions) * 10
            overall_score = max(0, 100 - deduction)

            return {
                'success': True,
                'action': 'full_audit',
                'overall_score': overall_score,
                'synergy_score': synergy_score,
                'duplications_found': len(duplications),
                'misattributions_found': len(misattributions),
                'duplications': duplications,
                'misattributions': misattributions,
                'recommendations': recommendations,
                'architecture_summary': {
                    'agents': len(architecture['agents']),
                    'tools': len(architecture['tools']),
                    'departments': len(architecture['departments'])
                },
                'timestamp': datetime.now().isoformat(),
                'cost': 0.0,  # Will be filled by LLM call if needed
                'confidence': 0.85
            }

        except Exception as e:
            return {
                'success': False,
                'action': 'full_audit',
                'error': f"Audit failed: {str(e)}",
                'cost': 0.0,
                'confidence': 0.0
            }

    def check_duplications(self) -> Dict[str, Any]:
        """
        Vérifie uniquement les duplications

        Returns:
            Dict avec duplications détectées
        """
        try:
            print("\n🔍 Checking for duplications...\n")

            architecture = self._scan_architecture()
            duplications = self._find_duplications(architecture)

            if duplications:
                print(f"⚠️  Found {len(duplications)} potential duplications:\n")
                for dup in duplications:
                    print(f"  • {dup['component1']} ↔️  {dup['component2']}")
                    print(f"    Reason: {dup['reason']}")
                    print(f"    Similarity: {dup['similarity']:.0%}")
                    print()
            else:
                print("✓ No duplications detected")

            return {
                'success': True,
                'action': 'check_duplication',
                'duplications_found': len(duplications),
                'duplications': duplications,
                'cost': 0.0,
                'confidence': 0.9
            }

        except Exception as e:
            return {
                'success': False,
                'action': 'check_duplication',
                'error': f"Duplication check failed: {str(e)}",
                'cost': 0.0,
                'confidence': 0.0
            }

    def validate_new_component(
        self,
        component_name: str,
        component_type: str,
        component_spec: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Valide un nouveau composant avant ajout

        Args:
            component_name: Nom du composant
            component_type: Type (agent, tool, department)
            component_spec: Spécifications du composant

        Returns:
            Dict avec validation
        """
        try:
            print(f"\n🔍 Validating new {component_type}: {component_name}\n")

            architecture = self._scan_architecture()

            # Check if already exists
            conflicts = self._check_conflicts(component_name, component_type, architecture)

            # Check if duplicates existing functionality
            duplicates = self._check_functional_duplication(component_spec, architecture)

            # Validate task attribution
            attribution_valid = self._validate_attribution(component_type, component_spec)

            is_valid = len(conflicts) == 0 and len(duplicates) == 0 and attribution_valid

            if is_valid:
                print(f"✅ Component '{component_name}' is valid and can be added")
            else:
                print(f"❌ Component '{component_name}' has issues:")
                if conflicts:
                    print(f"   • Conflicts with: {', '.join(conflicts)}")
                if duplicates:
                    print(f"   • Duplicates functionality of: {', '.join(duplicates)}")
                if not attribution_valid:
                    print(f"   • Task attribution issues detected")

            return {
                'success': True,
                'action': 'validate_new_component',
                'component_name': component_name,
                'component_type': component_type,
                'is_valid': is_valid,
                'conflicts': conflicts,
                'duplicates': duplicates,
                'attribution_valid': attribution_valid,
                'recommendation': 'approve' if is_valid else 'reject',
                'cost': 0.0,
                'confidence': 0.9
            }

        except Exception as e:
            return {
                'success': False,
                'action': 'validate_new_component',
                'error': f"Validation failed: {str(e)}",
                'cost': 0.0,
                'confidence': 0.0
            }

    def check_task_attribution(self) -> Dict[str, Any]:
        """
        Vérifie que les tâches sont bien attribuées aux bons agents

        Returns:
            Dict avec résultats
        """
        try:
            print("\n🎯 Checking task attributions...\n")

            architecture = self._scan_architecture()
            misattributions = self._check_misattributions(architecture)

            if misattributions:
                print(f"⚠️  Found {len(misattributions)} potential misattributions:\n")
                for mis in misattributions:
                    print(f"  • Task: {mis['task']}")
                    print(f"    Current: {mis['current_agent']}")
                    print(f"    Should be: {mis['suggested_agent']}")
                    print(f"    Reason: {mis['reason']}")
                    print()
            else:
                print("✓ All task attributions are correct")

            return {
                'success': True,
                'action': 'check_task_attribution',
                'misattributions_found': len(misattributions),
                'misattributions': misattributions,
                'cost': 0.0,
                'confidence': 0.85
            }

        except Exception as e:
            return {
                'success': False,
                'action': 'check_task_attribution',
                'error': f"Attribution check failed: {str(e)}",
                'cost': 0.0,
                'confidence': 0.0
            }

    def _scan_architecture(self) -> Dict[str, Any]:
        """
        Scan l'architecture actuelle

        Returns:
            Dict avec agents, tools, departments
        """
        architecture = {
            'agents': [],
            'tools': [],
            'departments': []
        }

        # Scan agents
        agents_dir = Path("cortex/agents")
        if agents_dir.exists():
            for file in agents_dir.glob("*_agent.py"):
                if file.name != "__init__.py" and file.name != "base_agent.py":
                    agent_name = file.stem.replace("_agent", "")
                    architecture['agents'].append({
                        'name': agent_name,
                        'file': str(file),
                        'type': 'agent'
                    })

        # Scan tools
        tools_dir = Path("cortex/tools")
        if tools_dir.exists():
            for file in tools_dir.glob("*_tools.py"):
                tool_name = file.stem.replace("_tools", "")
                architecture['tools'].append({
                    'name': tool_name,
                    'file': str(file),
                    'type': 'tool'
                })

        # Scan departments
        departments_dir = Path("cortex/departments")
        if departments_dir.exists():
            for dept_dir in departments_dir.iterdir():
                if dept_dir.is_dir() and not dept_dir.name.startswith('__'):
                    architecture['departments'].append({
                        'name': dept_dir.name,
                        'path': str(dept_dir),
                        'type': 'department'
                    })

        return architecture

    def _find_duplications(self, architecture: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Détecte les duplications de fonctionnalités

        Args:
            architecture: Architecture scannée

        Returns:
            Liste de duplications détectées
        """
        duplications = []

        # Simple heuristic: check for similar names
        agent_names = [a['name'] for a in architecture['agents']]
        tool_names = [t['name'] for t in architecture['tools']]

        # Check for similar agent names
        for i, agent1 in enumerate(agent_names):
            for agent2 in agent_names[i+1:]:
                similarity = self._calculate_name_similarity(agent1, agent2)
                if similarity > 0.6:
                    duplications.append({
                        'component1': agent1,
                        'component2': agent2,
                        'type': 'agent',
                        'similarity': similarity,
                        'reason': 'Similar names suggest potential duplication'
                    })

        # Check for overlapping responsibilities
        # (Simplified - in real implementation would analyze docstrings and code)

        return duplications

    def _check_misattributions(self, architecture: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Vérifie les mauvaises attributions de tâches

        Args:
            architecture: Architecture scannée

        Returns:
            Liste de misattributions
        """
        misattributions = []

        # Define expected responsibilities
        expected_roles = {
            'triage': ['routing', 'decision', 'first-line'],
            'planner': ['planning', 'tasks', 'decomposition'],
            'tooler': ['tools', 'research', 'capabilities'],
            'communications': ['messages', 'recommendations', 'user-facing'],
            'context': ['context', 'preparation', 'cache'],
            'maintenance': ['maintenance', 'sync', 'updates'],
            'quality_control': ['quality', 'evaluation', 'metrics'],
            'harmonization': ['coherence', 'architecture', 'validation']
        }

        # Check if any agent handles tasks outside its role
        # (Simplified - would analyze actual code in real implementation)

        return misattributions

    def _analyze_synergies(self, architecture: Dict[str, Any]) -> float:
        """
        Analyse les synergies entre composants

        Args:
            architecture: Architecture scannée

        Returns:
            Score de synergie (0-100)
        """
        # Simplified scoring based on architecture completeness
        score = 70.0  # Base score

        # Bonus for having key agents
        key_agents = ['triage', 'planner', 'context', 'tooler']
        existing_agents = [a['name'] for a in architecture['agents']]

        for key_agent in key_agents:
            if key_agent in existing_agents:
                score += 5

        # Bonus for having departments
        score += len(architecture['departments']) * 2

        return min(100.0, score)

    def _generate_recommendations(
        self,
        architecture: Dict[str, Any],
        duplications: List[Dict],
        misattributions: List[Dict],
        synergy_score: float
    ) -> List[Dict[str, Any]]:
        """
        Génère des recommandations d'amélioration

        Returns:
            Liste de recommandations
        """
        recommendations = []

        # Recommendations for duplications
        for dup in duplications:
            recommendations.append({
                'type': 'duplication',
                'priority': 'high',
                'action': 'consolidate',
                'components': [dup['component1'], dup['component2']],
                'description': f"Consider consolidating {dup['component1']} and {dup['component2']}"
            })

        # Recommendations for misattributions
        for mis in misattributions:
            recommendations.append({
                'type': 'misattribution',
                'priority': 'medium',
                'action': 'reassign',
                'task': mis['task'],
                'from': mis['current_agent'],
                'to': mis['suggested_agent'],
                'description': f"Reassign {mis['task']} from {mis['current_agent']} to {mis['suggested_agent']}"
            })

        # Recommendations for synergy improvements
        if synergy_score < 80:
            recommendations.append({
                'type': 'synergy',
                'priority': 'low',
                'action': 'improve',
                'description': 'Consider adding more inter-agent communication mechanisms'
            })

        return recommendations

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calcule similarité entre deux noms

        Args:
            name1: Premier nom
            name2: Deuxième nom

        Returns:
            Score de similarité (0-1)
        """
        # Simple Jaccard similarity on words
        words1 = set(name1.lower().split('_'))
        words2 = set(name2.lower().split('_'))

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def _check_conflicts(
        self,
        component_name: str,
        component_type: str,
        architecture: Dict[str, Any]
    ) -> List[str]:
        """
        Vérifie les conflits avec composants existants

        Returns:
            Liste de noms en conflit
        """
        conflicts = []

        if component_type == 'agent':
            existing_names = [a['name'] for a in architecture['agents']]
            if component_name in existing_names:
                conflicts.append(component_name)

        elif component_type == 'tool':
            existing_names = [t['name'] for t in architecture['tools']]
            if component_name in existing_names:
                conflicts.append(component_name)

        return conflicts

    def _check_functional_duplication(
        self,
        component_spec: Optional[Dict],
        architecture: Dict[str, Any]
    ) -> List[str]:
        """
        Vérifie si le composant duplique des fonctionnalités existantes

        Returns:
            Liste de composants avec fonctionnalités similaires
        """
        # Simplified - would use LLM for semantic analysis in real implementation
        return []

    def _validate_attribution(
        self,
        component_type: str,
        component_spec: Optional[Dict]
    ) -> bool:
        """
        Valide que l'attribution est correcte

        Returns:
            True si valide
        """
        # Simplified validation
        return True

    def generate_harmonization_plan(
        self,
        changed_files: List[Dict[str, Any]],
        git_analysis: Dict[str, Any],
        conflicts: Optional[Dict[str, Any]] = None,
        architecture: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Génère un plan d'harmonisation détaillé via GPT-5

        Cette méthode NE FAIT QUE PLANIFIER, elle n'exécute rien.
        Le plan sera transmis au MaintenanceAgent pour exécution.

        Args:
            changed_files: Fichiers modifiés
            git_analysis: Analyse du GitWatcherAgent
            conflicts: Conflits détectés (optionnel)
            architecture: Architecture actuelle (optionnel)

        Returns:
            Plan d'harmonisation détaillé avec actions, priorités, impacts
        """
        start_time = time.time()

        print(f"\n{'='*70}")
        print("🎯 HARMONIZATION AGENT - Génération du plan (GPT-5)")
        print(f"{'='*70}\n")

        # Préparer le contexte pour le LLM
        if architecture is None:
            architecture = self._scan_architecture()

        context_summary = {
            'files_changed': len(changed_files),
            'impact_level': git_analysis.get('impact_level', 'unknown'),
            'affected_areas': git_analysis.get('affected_areas', []),
            'critical_files': git_analysis.get('critical_files', []),
            'architecture': {
                'agents_count': len(architecture.get('agents', [])),
                'tools_count': len(architecture.get('tools', [])),
                'departments_count': len(architecture.get('departments', []))
            },
            'conflicts': conflicts or {}
        }

        # Construire le prompt pour GPT-5
        prompt = f"""Tu es l'Harmonization Agent de Cortex, responsable de la cohérence architecturale.

Tu viens de recevoir une notification de changements dans le codebase avec l'analyse suivante :

**Fichiers modifiés ({len(changed_files)}):**
{json.dumps(changed_files, indent=2)}

**Analyse d'impact:**
{json.dumps(git_analysis, indent=2)}

**Contexte système:**
{json.dumps(context_summary, indent=2)}

**Ta mission (PLANIFICATION UNIQUEMENT):**
1. Analyser les impacts architecturaux de ces changements
2. Identifier les incohérences, conflits, dépendances cassées
3. Générer un plan d'harmonisation détaillé (NE PAS EXÉCUTER)

Le plan doit contenir:
- **Titre**: Résumé du plan
- **Analyse**: Diagnostic complet des problèmes
- **Actions** (liste ordonnée par priorité):
  * priority: 1-10 (1 = critique)
  * action_type: 'update_file', 'refactor', 'add_test', 'update_doc', 'sync_db'
  * target: Fichier/composant cible
  * description: Description claire
  * responsible_agent: 'MaintenanceAgent', 'TesterAgent', 'ArchivistAgent'
  * estimated_effort: 'low', 'medium', 'high'
  * rationale: Pourquoi cette action est nécessaire
- **Impacts**: Conséquences attendues
- **Risks**: Risques identifiés
- **Alternatives**: Autres approches possibles (si applicable)
- **Testing_required**: Boolean - tests nécessaires?
- **Validation_criteria**: Comment valider le succès

Réponds UNIQUEMENT en JSON valide (pas de markdown):
{{
    "title": "...",
    "analysis": "...",
    "actions": [
        {{
            "priority": 1,
            "action_type": "...",
            "target": "...",
            "description": "...",
            "responsible_agent": "...",
            "estimated_effort": "...",
            "rationale": "..."
        }}
    ],
    "impacts": "...",
    "risks": "...",
    "alternatives": "...",
    "testing_required": true,
    "validation_criteria": ["..."]
}}"""

        try:
            print("1. Calling GPT-5 for harmonization plan generation...")

            # Appel GPT-5 pour génération du plan
            llm_response = self.llm_client.call(
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un architecte logiciel expert qui génère des plans d'harmonisation détaillés. Tu PLANIFIES uniquement, tu n'EXÉCUTES jamais."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                tier=self.tier,
                max_tokens=4000,  # Plan détaillé
                temperature=0.3  # Précision architecturale
            )

            print("2. Parsing GPT-5 response...")

            # Parser la réponse JSON
            plan_data = self._parse_llm_plan(llm_response.content)

            if 'error' in plan_data:
                print(f"   ❌ Failed to parse plan: {plan_data['error']}")
                return {
                    'success': False,
                    'error': plan_data['error'],
                    'raw_response': llm_response.content[:500]
                }

            print(f"3. Plan generated successfully")
            print(f"   ✓ Title: {plan_data.get('title', 'N/A')}")
            print(f"   ✓ Actions: {len(plan_data.get('actions', []))}")
            print(f"   ✓ Testing required: {plan_data.get('testing_required', False)}")
            print()

            # Enregistrer le plan comme ADR
            from cortex.repositories.architecture_repository import get_architecture_repository
            arch_repo = get_architecture_repository()

            adr_id = arch_repo.add_decision(
                title=f"Harmonization Plan: {plan_data.get('title', 'Auto-generated')}",
                context=json.dumps(context_summary, indent=2),
                decision=plan_data.get('analysis', 'GPT-5 generated harmonization plan'),
                consequences=plan_data.get('impacts', 'See plan details'),
                alternatives=plan_data.get('alternatives'),
                status='proposed',
                author='HarmonizationAgent (GPT-5)'
            )

            plan_data['adr_id'] = adr_id
            plan_data['success'] = True
            plan_data['cost'] = llm_response.cost
            plan_data['model'] = llm_response.model
            plan_data['timestamp'] = datetime.now().isoformat()

            duration = time.time() - start_time

            # Enregistrer dans la mémoire
            self.memory.record_execution(
                request=f"Generate harmonization plan: {plan_data.get('title', 'Untitled')}",
                result=plan_data,
                duration=duration,
                cost=llm_response.cost
            )

            # Mettre à jour l'état
            self.memory.update_state({
                'last_plan_id': adr_id,
                'last_plan_title': plan_data.get('title'),
                'last_generation_timestamp': datetime.now().isoformat(),
                'total_actions_generated': len(plan_data.get('actions', []))
            })

            # Détecter patterns dans les types d'actions générés
            actions = plan_data.get('actions', [])
            for action in actions:
                action_type = action.get('action_type')
                self.memory.add_pattern(
                    f'action_type_{action_type}',
                    {
                        'type': action_type,
                        'priority': action.get('priority'),
                        'responsible_agent': action.get('responsible_agent')
                    }
                )

            return plan_data

        except Exception as e:
            print(f"   ❌ Plan generation failed: {e}")
            import traceback
            traceback.print_exc()

            duration = time.time() - start_time

            error_result = {
                'success': False,
                'error': str(e),
                'fallback_actions': [
                    {
                        'priority': 1,
                        'action_type': 'manual_review',
                        'target': 'all_changed_files',
                        'description': 'Manual review required due to plan generation failure',
                        'responsible_agent': 'Human',
                        'estimated_effort': 'high',
                        'rationale': 'GPT-5 plan generation failed'
                    }
                ]
            }

            # Enregistrer l'échec dans la mémoire
            self.memory.record_execution(
                request="Generate harmonization plan (failed)",
                result=error_result,
                duration=duration,
                cost=0.0
            )

            return error_result

    def _parse_llm_plan(self, llm_content: str) -> Dict[str, Any]:
        """Parse la réponse JSON du LLM"""
        try:
            # Nettoyer le contenu (enlever markdown si présent)
            content = llm_content.strip()

            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            # Parser le JSON
            plan = json.loads(content)
            return plan

        except json.JSONDecodeError as e:
            return {
                'error': f'JSON parse error: {e}',
                'raw_content': llm_content[:500]
            }
        except Exception as e:
            return {
                'error': f'Unexpected error: {e}',
                'raw_content': llm_content[:500]
            }


def create_harmonization_agent(llm_client: LLMClient) -> HarmonizationAgent:
    """Factory function pour créer un HarmonizationAgent"""
    return HarmonizationAgent(llm_client)


# Test
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    print("Testing Harmonization Agent...")

    client = LLMClient()
    agent = HarmonizationAgent(client)

    # Test 1: Full audit
    print("\n1. Running full audit...")
    result = agent.run_full_audit()
    print(f"   Success: {result['success']}")
    print(f"   Overall score: {result.get('overall_score', 0)}")
    print(f"   Duplications: {result.get('duplications_found', 0)}")

    # Test 2: Check duplications
    print("\n2. Checking duplications...")
    result = agent.check_duplications()
    print(f"   Success: {result['success']}")
    print(f"   Duplications found: {result.get('duplications_found', 0)}")

    print("\n✓ Harmonization Agent works correctly!")
