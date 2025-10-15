"""
Developer Agent Directeur - Agent spécialisé dans les décisions architecturales

ROLE: DIRECTEUR (Décision) - Niveau 3 de la hiérarchie
TIER: GPT5 pour décisions architecturales et code complexe

Responsabilités:
- Décisions architecturales
- Code complexe nécessitant réflexion
- Debugging difficile
- Choix de patterns et technologies
- Refactoring structurel
"""

import subprocess
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier
from cortex.core.agent_hierarchy import DecisionAgent, AgentRole, AgentResult, EscalationContext
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


class DeveloperAgentDirecteur(DecisionAgent):
    """
    Developer Agent Directeur - Niveau DIRECTEUR (Décision) dans la hiérarchie

    Hérite de DecisionAgent pour intégration dans le système hiérarchique.
    Spécialisation: Décisions architecturales et code complexe.
    """

    # Prompt optimisé pour DIRECTEUR (GPT5)
    DIRECTEUR_PROMPT = """You are a DIRECTEUR DEVELOPER (GPT-5) - Architectural decisions and complex code.

STRENGTHS:
- Architectural decisions
- Complex code requiring deep analysis
- Difficult debugging and edge cases
- Technology and pattern selection
- Structural refactoring
- System design

TASK: {task}

CONTEXT:
{context}

FILES TO MODIFY:
{files_info}

ESCALATION CONTEXT:
{escalation_context}

INSTRUCTIONS:
1. Analyze the architecture and design implications
2. Make informed decisions about patterns and approaches
3. Implement complex logic with clarity
4. Consider edge cases and error handling
5. Document critical decisions in code comments
6. Return modified code sections with explanations

OUTPUT FORMAT:
```filepath
<new content>
```

Think deeply about the problem. Provide well-reasoned solutions."""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Developer Agent Directeur

        Args:
            llm_client: Client LLM pour génération de code
        """
        # Initialiser DecisionAgent avec spécialisation "architecture"
        super().__init__(llm_client, specialization="architecture")
        self.region_analyzer = create_region_analyzer()

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """
        Évalue si le Directeur peut gérer la requête

        Override DecisionAgent.can_handle() avec logique spécifique
        """
        # Patterns pour décisions architecturales
        directeur_patterns = [
            'architecture', 'design', 'decide', 'choose', 'strategy',
            'complex', 'refactor', 'restructure', 'debug',
            'pattern', 'technology', 'approach'
        ]

        request_lower = request.lower()
        matches = sum(1 for pattern in directeur_patterns if pattern in request_lower)

        # Base confidence from matches
        confidence = min(matches / 2.5, 1.0)

        # Boost if context indicates complexity
        if context:
            if context.get('complexity') == 'high':
                confidence = min(confidence + 0.3, 1.0)
            if context.get('requires_decision'):
                confidence = min(confidence + 0.2, 1.0)

        # Reduce if request seems too critical/strategic (needs CORTEX)
        critical_indicators = ['critical', 'system-wide', 'strategic', 'innovative', 'research']
        if any(ind in request_lower for ind in critical_indicators):
            confidence *= 0.7  # Probably needs CORTEX

        return confidence

    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[EscalationContext] = None
    ) -> AgentResult:
        """
        Exécute le développement de code avec décisions architecturales

        Override DecisionAgent.execute() avec logique DeveloperAgent

        Args:
            request: Description de la tâche
            context: Dict avec 'filepaths', 'context_text', 'use_partial_updates'
            escalation_context: Contexte si escalation

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
                should_escalate=True,
                escalation_reason="No filepaths provided for development",
                error="Missing filepaths in context"
            )

        # Préparer les informations sur les fichiers
        files_info = self._prepare_files_info(filepaths, use_partial)

        # Préparer contexte d'escalation si disponible
        escalation_info = "None (first attempt)"
        if escalation_context:
            escalation_info = f"""Previous role: {escalation_context.previous_role.value}
Previous tier: {escalation_context.previous_tier.value}
Attempts: {escalation_context.attempts}
Errors: {'; '.join(escalation_context.errors[:3])}
Reason: {escalation_context.escalation_reason}"""

        # Construire le prompt
        prompt = self.DIRECTEUR_PROMPT.format(
            task=request,
            context=context_text or "No additional context provided.",
            files_info=files_info,
            escalation_context=escalation_info
        )

        # Appeler le LLM
        try:
            response = self.llm_client.complete(
                messages=[{"role": "user", "content": prompt}],
                tier=self.tier,
                max_tokens=6000,
                temperature=0.4
            )

            # Parser la réponse pour extraire les changements
            changes = self._parse_response(response.content, filepaths)

            if not changes:
                return AgentResult(
                    success=False,
                    role=self.role,
                    tier=self.tier,
                    content=None,
                    cost=response.cost,
                    confidence=0.4,
                    should_escalate=True,
                    escalation_reason="No code changes generated",
                    error="Failed to parse code changes from response"
                )

            return AgentResult(
                success=True,
                role=self.role,
                tier=self.tier,
                content={'changes': [self._change_to_dict(c) for c in changes]},
                cost=response.cost,
                confidence=0.85,  # Directeur level confidence
                should_escalate=False,
                escalation_reason=None,
                error=None,
                metadata={'changes_objects': changes}
            )

        except Exception as e:
            return AgentResult(
                success=False,
                role=self.role,
                tier=self.tier,
                content=None,
                cost=0.0,
                confidence=0.0,
                should_escalate=True,
                escalation_reason=f"Exception during development: {str(e)}",
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

            if use_partial and len(content) > 1000:
                # Utiliser régions pour gros fichiers
                regions = self.region_analyzer.analyze_file(filepath)

                info_parts.append(f"\n## {filepath} ({len(regions)} regions)\n")
                info_parts.append("Available regions:")
                for region in regions[:10]:
                    info_parts.append(
                        f"  - [{region.id}] {region.type} '{region.name}' "
                        f"(lines {region.start_line}-{region.end_line})"
                    )
                if len(regions) > 10:
                    info_parts.append(f"  ... and {len(regions) - 10} more regions")

                # Snippet du début
                info_parts.append(f"\n```python\n{content[:500]}\n...\n```\n")
            else:
                # Fichier complet
                info_parts.append(f"\n## {filepath}\n")
                info_parts.append(f"```python\n{content}\\n```\n")

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


def create_developer_agent_directeur(llm_client: LLMClient) -> DeveloperAgentDirecteur:
    """Factory function pour créer un DeveloperAgentDirecteur"""
    return DeveloperAgentDirecteur(llm_client)


# Test si exécuté directement
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    print("Testing Developer Agent Directeur...")

    client = LLMClient()
    directeur = DeveloperAgentDirecteur(client)

    # Test can_handle
    print("\n1. Testing can_handle...")
    requests = [
        "Design the microservices architecture",
        "Choose between REST and GraphQL for this API",
        "Debug this complex async race condition",
        "Implement simple CRUD endpoints"  # Should be lower (EXPERT can handle)
    ]

    for req in requests:
        score = directeur.can_handle(req)
        print(f"  '{req}': {score:.2f}")

    print("\n✓ Developer Agent Directeur works correctly!")
