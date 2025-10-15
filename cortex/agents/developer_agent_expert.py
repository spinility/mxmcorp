"""
Developer Agent Expert - Agent spécialisé dans l'analyse et le développement

ROLE: EXPERT (Analyse) - Niveau 2 de la hiérarchie
TIER: DeepSeek-V3.2-Exp pour code rapide et efficace

Responsabilités:
- Génération de code standard
- Refactoring localisé
- Bug fixes simples à modérés
- Analyse de code
"""

import subprocess
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier
from cortex.core.agent_hierarchy import AnalysisAgent, AgentRole, AgentResult, EscalationContext
from cortex.core.region_analyzer import RegionAnalyzer, create_region_analyzer


# Shared dataclasses (same as original DeveloperAgent)
@dataclass
class CodeChange:
    """Représente un changement de code"""
    filepath: str
    original_content: str
    new_content: str
    change_type: str  # 'full_file', 'partial_region', 'new_file'
    region_id: Optional[str] = None
    diff: Optional[str] = None


class DeveloperAgentExpert(AnalysisAgent):
    """
    Developer Agent Expert - Niveau EXPERT (Analyse) dans la hiérarchie

    Hérite d'AnalysisAgent pour intégration dans le système hiérarchique.
    Spécialisation: Développement de code standard et analyse.
    """

    # Prompt optimisé pour EXPERT (DeepSeek)
    EXPERT_PROMPT = """You are an EXPERT DEVELOPER (DeepSeek-V3.2-Exp) - Fast, efficient code generation.

STRENGTHS:
- Straightforward features
- Standard patterns
- Basic refactoring
- Bug fixes (simple to moderate)
- Code analysis

TASK: {task}

CONTEXT:
{context}

FILES TO MODIFY:
{files_info}

ESCALATION CONTEXT:
{escalation_context}

INSTRUCTIONS:
1. Implement the requested changes
2. Follow existing code style
3. Keep changes minimal and focused
4. Return ONLY the modified code sections
5. Use standard patterns and best practices

OUTPUT FORMAT:
```filepath
<new content>
```

Be concise and direct. Focus on clean, maintainable code."""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Developer Agent Expert

        Args:
            llm_client: Client LLM pour génération de code
        """
        # Initialiser AnalysisAgent avec spécialisation "development"
        super().__init__(llm_client, specialization="development")
        self.region_analyzer = create_region_analyzer()

    def can_handle(self, request: str, context: Optional[Dict] = None) -> float:
        """
        Évalue si l'Expert peut gérer la requête

        Override AnalysisAgent.can_handle() avec logique spécifique
        """
        # Patterns pour développement standard
        dev_patterns = [
            'implement', 'create', 'generate', 'add',
            'refactor', 'fix', 'debug', 'update',
            'modify', 'change', 'improve'
        ]

        request_lower = request.lower()
        matches = sum(1 for pattern in dev_patterns if pattern in request_lower)

        # Base confidence from matches
        confidence = min(matches / 2.0, 1.0)

        # Boost if context contains filepaths (work to do)
        if context and 'filepaths' in context:
            confidence = min(confidence + 0.2, 1.0)

        # Reduce if request seems too complex for Expert
        complex_indicators = ['architecture', 'design', 'strategy', 'decide', 'choose']
        if any(ind in request_lower for ind in complex_indicators):
            confidence *= 0.6  # Probably needs DIRECTEUR

        return confidence

    def execute(
        self,
        request: str,
        context: Optional[Dict] = None,
        escalation_context: Optional[EscalationContext] = None
    ) -> AgentResult:
        """
        Exécute le développement de code

        Override AnalysisAgent.execute() avec logique DeveloperAgent

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
Errors: {'; '.join(escalation_context.errors[:3])}"""

        # Construire le prompt
        prompt = self.EXPERT_PROMPT.format(
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
                max_tokens=4000,
                temperature=0.3
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
                    confidence=0.3,
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
                confidence=0.8,  # Expert level confidence
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


def create_developer_agent_expert(llm_client: LLMClient) -> DeveloperAgentExpert:
    """Factory function pour créer un DeveloperAgentExpert"""
    return DeveloperAgentExpert(llm_client)


# Test si exécuté directement
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    print("Testing Developer Agent Expert...")

    client = LLMClient()
    expert = DeveloperAgentExpert(client)

    # Test can_handle
    print("\n1. Testing can_handle...")
    requests = [
        "Implement authentication system",
        "Refactor this function",
        "Design the microservices architecture"  # Should be low (needs DIRECTEUR)
    ]

    for req in requests:
        score = expert.can_handle(req)
        print(f"  '{req}': {score:.2f}")

    print("\n✓ Developer Agent Expert works correctly!")
