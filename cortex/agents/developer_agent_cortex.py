"""
Developer Agent Cortex - Agent spécialisé dans les problèmes critiques et stratégiques

ROLE: CORTEX_CENTRAL (Coordination) - Niveau 4 de la hiérarchie
TIER: Claude 4.5 pour problèmes critiques et coordination système

Responsabilités:
- Problèmes critiques résistants
- Refactoring massif multi-fichiers
- Edge cases complexes
- Innovation et recherche de solutions
- Coordination de changements système
- Décisions stratégiques sur le code
"""

import subprocess
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier
from cortex.core.agent_hierarchy import CoordinationAgent, AgentRole, AgentResult, EscalationContext
from cortex.core.region_analyzer import RegionAnalyzer, create_region_analyzer


# Shared dataclasses (same as other DeveloperAgent variants)
@dataclass
class CodeChange:
    """Représente un changement de code"""
    filepath: str
    original_content: str
    new_content: str
    change_type: str  # 'full_file', 'partial_region', 'new_file'
    region_id: Optional[str] = None
    diff: Optional[str] = None


class DeveloperAgentCortex(CoordinationAgent):
    """
    Developer Agent Cortex - Niveau CORTEX_CENTRAL (Coordination) dans la hiérarchie

    Hérite de CoordinationAgent pour intégration dans le système hiérarchique.
    Spécialisation: Problèmes critiques et coordination système.
    """

    # Prompt optimisé pour CORTEX (Claude 4.5)
    CORTEX_PROMPT = """You are CORTEX CENTRAL DEVELOPER (Claude 4.5) - System coordination and critical problem solving.

ROLE: You are the highest level of development expertise, called upon for:
- Critical problems that have resisted other tiers
- Massive refactoring affecting multiple files
- Complex edge cases and subtle bugs
- System-wide architectural changes
- Innovative solutions requiring deep reasoning
- Strategic code decisions with long-term implications

TASK: {task}

CONTEXT:
{context}

FILES TO MODIFY:
{files_info}

ESCALATION CONTEXT:
{escalation_context}

PREVIOUS ATTEMPTS (if any):
The problem has been escalated to you because previous tiers could not resolve it.
Carefully analyze what went wrong and apply your advanced reasoning capabilities.

INSTRUCTIONS:
1. Deeply analyze the root cause of the problem
2. Consider system-wide implications and side effects
3. Design robust solutions that handle edge cases
4. Provide clear explanations for complex decisions
5. Coordinate changes across multiple files if needed
6. Document critical insights and reasoning
7. Return complete, production-ready code

OUTPUT FORMAT:
```filepath
<new content>
```

REASONING:
<Explain your approach and key decisions>

You are the last line of defense. Be thorough, innovative, and precise."""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Developer Agent Cortex

        Args:
            llm_client: Client LLM pour génération de code
        """
        # Initialiser CoordinationAgent avec spécialisation "critical_problems"
        super().__init__(llm_client, specialization="critical_problems")
        self.region_analyzer = create_region_analyzer()

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """
        Évalue si Cortex peut gérer la requête

        Override CoordinationAgent.can_handle() avec logique spécifique
        """
        # Patterns pour problèmes critiques et stratégiques
        cortex_patterns = [
            'critical', 'strategic', 'system-wide', 'innovative',
            'research', 'complex edge', 'resistant', 'failed',
            'massive refactor', 'coordination', 'multi-file'
        ]

        request_lower = request.lower()
        matches = sum(1 for pattern in cortex_patterns if pattern in request_lower)

        # Base confidence from matches
        confidence = min(matches / 2.0, 1.0)

        # Boost significantly if escalated (this IS the final tier)
        if context:
            if context.get('is_escalation'):
                confidence = min(confidence + 0.4, 1.0)
            if context.get('previous_failures', 0) > 0:
                confidence = min(confidence + 0.3, 1.0)
            if context.get('criticality') == 'high':
                confidence = min(confidence + 0.2, 1.0)

        # Cortex can handle anything, but prefer to let lower tiers try first
        # So base confidence is moderate unless explicitly escalated
        if not context or not context.get('is_escalation'):
            confidence *= 0.7

        return confidence

    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[EscalationContext] = None
    ) -> AgentResult:
        """
        Exécute le développement de code avec résolution de problèmes critiques

        Override CoordinationAgent.execute() avec logique DeveloperAgent

        Args:
            request: Description de la tâche
            context: Dict avec 'filepaths', 'context_text', 'use_partial_updates'
            escalation_context: Contexte si escalation (très probable à ce niveau)

        Returns:
            AgentResult avec changements de code
        """
        # Extraire paramètres du contexte
        filepaths = context.get('filepaths', []) if context else []
        context_text = context.get('context_text', '') if context else ''
        use_partial = context.get('use_partial_updates', True) if context else True

        if not filepaths:
            return AgentResult(
                success=False,
                role=self.role,
                tier=self.tier,
                content=None,
                cost=0.0,
                confidence=0.0,
                should_escalate=False,  # Cortex is the final tier, no further escalation
                escalation_reason="No filepaths provided for development",
                error="Missing filepaths in context"
            )

        # Préparer les informations sur les fichiers
        files_info = self._prepare_files_info(filepaths, use_partial)

        # Préparer contexte d'escalation si disponible (crucial pour Cortex)
        escalation_info = "None (direct request to Cortex)"
        if escalation_context:
            escalation_info = f"""Previous role: {escalation_context.previous_role.value}
Previous tier: {escalation_context.previous_tier.value}
Total attempts: {escalation_context.attempts}
Previous errors:
{chr(10).join('  - ' + err for err in escalation_context.errors[:5])}
Escalation reason: {escalation_context.escalation_reason}

ANALYSIS: This problem has been escalated to you after {escalation_context.attempts} attempts by lower tiers.
Use your advanced capabilities to identify what went wrong and provide a robust solution."""

        # Construire le prompt
        prompt = self.CORTEX_PROMPT.format(
            task=request,
            context=context_text or "No additional context provided.",
            files_info=files_info,
            escalation_context=escalation_info
        )

        # Appeler le LLM (Claude 4.5 - le plus puissant)
        try:
            response = self.llm_client.complete(
                messages=[{"role": "user", "content": prompt}],
                tier=self.tier,
                max_tokens=8000,
                temperature=0.5
            )

            # Parser la réponse pour extraire les changements
            changes = self._parse_response(response.content, filepaths)

            if not changes:
                # Même Cortex a échoué - c'est critique
                return AgentResult(
                    success=False,
                    role=self.role,
                    tier=self.tier,
                    content=None,
                    cost=response.cost,
                    confidence=0.3,
                    should_escalate=False,  # No escalation possible
                    escalation_reason="Cortex Central could not generate code changes - problem may be unsolvable",
                    error="Failed to parse code changes from response after Cortex analysis"
                )

            return AgentResult(
                success=True,
                role=self.role,
                tier=self.tier,
                content={'changes': [self._change_to_dict(c) for c in changes]},
                cost=response.cost,
                confidence=0.95,  # Cortex level confidence (highest)
                should_escalate=False,  # Cortex is the final tier
                escalation_reason=None,
                error=None,
                metadata={'changes_objects': changes}
            )

        except Exception as e:
            # Even Cortex can fail due to technical issues
            return AgentResult(
                success=False,
                role=self.role,
                tier=self.tier,
                content=None,
                cost=0.0,
                confidence=0.0,
                should_escalate=False,  # No further escalation possible
                escalation_reason=f"Cortex Central encountered exception: {str(e)}",
                error=str(e)
            )

    def _prepare_files_info(self, filepaths: List[str], use_partial: bool) -> str:
        """Prépare les informations sur les fichiers"""
        info_parts = []

        for filepath in filepaths:
            path = Path(filepath)

            if not path.exists():
                info_parts.append(f"\n## {filepath} (NEW FILE)\n")
                info_parts.append("This file will be created.")
                continue

            # Lire le contenu
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            if use_partial and len(content) > 1500:
                # Utiliser régions pour gros fichiers
                regions = self.region_analyzer.analyze_file(filepath)

                info_parts.append(f"\n## {filepath} ({len(regions)} regions)\n")
                info_parts.append("Available regions:")
                for region in regions[:15]:  # Cortex peut traiter plus de régions
                    info_parts.append(
                        f"  - [{region.id}] {region.type} '{region.name}' "
                        f"(lines {region.start_line}-{region.end_line})"
                    )
                if len(regions) > 15:
                    info_parts.append(f"  ... and {len(regions) - 15} more regions")

                # Snippet plus large pour Cortex
                info_parts.append(f"\n```python\n{content[:800]}\n...\n```\n")
            else:
                # Fichier complet
                info_parts.append(f"\n## {filepath}\n")
                info_parts.append(f"```python\n{content}\n```\n")

        return '\n'.join(info_parts)

    def _parse_response(self, response: str, expected_files: List[str]) -> List[CodeChange]:
        """Parse la réponse du LLM pour extraire les changements"""
        changes = []
        import re

        pattern = r'```(\w+)?:?([^\n]+)?\n(.*?)```'
        matches = re.finditer(pattern, response, re.DOTALL)

        for match in matches:
            language = match.group(1) or 'python'
            filepath_hint = match.group(2) or ''
            code_content = match.group(3).strip()

            target_file = None

            # Si filepath dans le marker
            if filepath_hint and any(f in filepath_hint for f in expected_files):
                for f in expected_files:
                    if f in filepath_hint:
                        target_file = f
                        break

            # Si un seul fichier attendu
            if not target_file and len(expected_files) == 1:
                target_file = expected_files[0]

            if target_file:
                original_content = ""
                if Path(target_file).exists():
                    with open(target_file, 'r', encoding='utf-8') as f:
                        original_content = f.read()

                changes.append(CodeChange(
                    filepath=target_file,
                    original_content=original_content,
                    new_content=code_content,
                    change_type='new_file' if not original_content else 'full_file',
                    diff=None  # Peut être calculé plus tard si nécessaire
                ))

        return changes

    def _change_to_dict(self, change: CodeChange) -> Dict[str, Any]:
        """Convertit CodeChange en dict"""
        return {
            'filepath': change.filepath,
            'change_type': change.change_type,
            'original_length': len(change.original_content),
            'new_length': len(change.new_content),
            'region_id': change.region_id
        }


def create_developer_agent_cortex(llm_client: LLMClient) -> DeveloperAgentCortex:
    """Factory function pour créer un DeveloperAgentCortex"""
    return DeveloperAgentCortex(llm_client)


# Test si exécuté directement
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    print("Testing Developer Agent Cortex...")

    client = LLMClient()
    cortex = DeveloperAgentCortex(client)

    # Test can_handle
    print("\n1. Testing can_handle...")
    requests = [
        "Critical bug causing data loss in production",
        "Massive refactoring of core architecture across 10 files",
        "Complex race condition that DeepSeek and GPT-5 couldn't solve",
        "Simple feature addition"  # Should be lower (not for Cortex)
    ]

    for req in requests:
        score = cortex.can_handle(req)
        print(f"  '{req}': {score:.2f}")

    # Test with escalation context
    print("\n2. Testing can_handle with escalation context...")
    escalation_req = "Fix authentication bug"
    escalation_context = {'is_escalation': True, 'previous_failures': 2}
    score_escalated = cortex.can_handle(escalation_req, escalation_context)
    print(f"  '{escalation_req}' (escalated): {score_escalated:.2f}")

    print("\n✓ Developer Agent Cortex works correctly!")
