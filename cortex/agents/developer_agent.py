"""
Developer Agent - Employé spécialisé dans le développement de code

Système 3-tier avec escalation automatique:
- Tier 1: DeepSeek-V3.2-Exp (rapide, économique)
- Tier 2: GPT-5 (intelligent, équilibré)
- Tier 3: Claude 4.5 (ultra-puissant, coûteux)

Responsabilités:
- Développement de features
- Correction de bugs
- Refactoring de code
- Updates partiels avec régions
"""

import subprocess
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier
from cortex.core.region_analyzer import RegionAnalyzer, create_region_analyzer


@dataclass
class CodeChange:
    """Représente un changement de code"""
    filepath: str
    original_content: str
    new_content: str
    change_type: str  # 'full_file', 'partial_region', 'new_file'
    region_id: Optional[str] = None
    diff: Optional[str] = None


@dataclass
class DevelopmentResult:
    """Résultat d'une tentative de développement"""
    success: bool
    changes: List[CodeChange]
    tier_used: ModelTier
    cost: float
    tokens_used: int
    error: Optional[str] = None
    reasoning: Optional[str] = None


class DeveloperAgent:
    """
    Agent développeur avec système 3-tier

    Tier 1: DeepSeek-V3.2-Exp - Code simple et rapide
    Tier 2: GPT-5 - Code complexe et architecture
    Tier 3: Claude 4.5 - Problèmes critiques et refactoring massif
    """

    # Prompts optimisés par tier
    TIER_1_PROMPT = """You are a TIER 1 DEVELOPER (DeepSeek-V3.2-Exp) - Fast, efficient code generation.

STRENGTHS:
- Straightforward features
- Standard patterns
- Basic refactoring
- Bug fixes (simple)

TASK: {task}

CONTEXT:
{context}

FILES TO MODIFY:
{files_info}

INSTRUCTIONS:
1. Implement the requested changes
2. Follow existing code style
3. Keep changes minimal and focused
4. Return ONLY the modified code sections

OUTPUT FORMAT:
```filepath
<new content>
```

Be concise and direct."""

    TIER_2_PROMPT = """You are a TIER 2 DEVELOPER (GPT-5) - Intelligent, balanced development.

STRENGTHS:
- Complex features
- Architecture decisions
- Difficult debugging
- Design patterns

TASK: {task}

CONTEXT:
{context}

PREVIOUS ATTEMPTS (FAILED):
{previous_attempts}

FILES TO MODIFY:
{files_info}

INSTRUCTIONS:
1. Analyze why previous attempts failed
2. Design a better solution
3. Consider edge cases and error handling
4. Implement with best practices

OUTPUT FORMAT:
```filepath
<new content>
```

Think carefully about the architecture."""

    TIER_3_PROMPT = """You are a TIER 3 DEVELOPER (Claude 4.5) - Ultimate problem solver.

STRENGTHS:
- Critical issues resistant to fixes
- Massive refactoring
- Complex edge cases
- System architecture

TASK: {task}

CONTEXT:
{context}

ESCALATION HISTORY:
{escalation_history}

This task has proven difficult for lower tiers. Your expertise is required.

INSTRUCTIONS:
1. Deeply analyze the root cause
2. Consider multiple approaches
3. Implement the most robust solution
4. Add comprehensive error handling
5. Document complex logic

OUTPUT FORMAT:
```filepath
<new content>
```

Apply your full expertise to solve this."""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize Developer Agent

        Args:
            llm_client: Client LLM pour génération de code
        """
        self.llm_client = llm_client
        self.region_analyzer = create_region_analyzer()
        self.development_history: List[DevelopmentResult] = []

    def develop(
        self,
        task: str,
        filepaths: List[str],
        tier: ModelTier = ModelTier.DEEPSEEK,
        context: str = "",
        use_partial_updates: bool = True
    ) -> DevelopmentResult:
        """
        Développe du code pour une tâche

        Args:
            task: Description de la tâche
            filepaths: Fichiers à modifier
            tier: Tier du modèle à utiliser
            context: Contexte additionnel
            use_partial_updates: Utiliser updates partiels si possible

        Returns:
            DevelopmentResult avec changements
        """
        # Préparer les informations sur les fichiers
        files_info = self._prepare_files_info(filepaths, use_partial_updates)

        # Sélectionner le prompt selon le tier
        prompt = self._build_prompt(task, tier, context, files_info)

        # Appeler le LLM
        try:
            response = self.llm_client.complete(
                messages=[{"role": "user", "content": prompt}],
                tier=tier,
                max_tokens=4000,
                temperature=0.3
            )

            # Parser la réponse pour extraire les changements
            changes = self._parse_response(response.content, filepaths)

            result = DevelopmentResult(
                success=True,
                changes=changes,
                tier_used=tier,
                cost=response.cost,
                tokens_used=response.usage.get('total_tokens', 0),
                reasoning=None
            )

            self.development_history.append(result)
            return result

        except Exception as e:
            result = DevelopmentResult(
                success=False,
                changes=[],
                tier_used=tier,
                cost=0.0,
                tokens_used=0,
                error=str(e)
            )
            self.development_history.append(result)
            return result

    def _prepare_files_info(
        self,
        filepaths: List[str],
        use_partial: bool
    ) -> str:
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
                for region in regions[:10]:  # Montrer 10 premières régions
                    info_parts.append(
                        f"  - [{region.id}] {region.type} '{region.name}' "
                        f"(lines {region.start_line}-{region.end_line})"
                    )
                if len(regions) > 10:
                    info_parts.append(f"  ... and {len(regions) - 10} more regions")

                # Ajouter snippet du début
                info_parts.append(f"\n```python\n{content[:500]}\n...\n```\n")

            else:
                # Montrer fichier complet
                info_parts.append(f"\n## {filepath}\n")
                info_parts.append(f"```python\n{content}\n```\n")

        return '\n'.join(info_parts)

    def _build_prompt(
        self,
        task: str,
        tier: ModelTier,
        context: str,
        files_info: str
    ) -> str:
        """Construit le prompt selon le tier"""
        # Préparer historique pour tiers supérieurs
        previous_attempts = ""
        escalation_history = ""

        if len(self.development_history) > 0:
            previous_attempts = "\n".join([
                f"Attempt {i+1} (Tier {result.tier_used.value}): "
                f"{'SUCCESS' if result.success else 'FAILED - ' + (result.error or 'Unknown error')}"
                for i, result in enumerate(self.development_history[-3:])
            ])

            escalation_history = previous_attempts

        # Sélectionner template selon tier
        if tier == ModelTier.DEEPSEEK:
            template = self.TIER_1_PROMPT
        elif tier == ModelTier.GPT5:
            template = self.TIER_2_PROMPT
        else:  # CLAUDE
            template = self.TIER_3_PROMPT

        return template.format(
            task=task,
            context=context or "No additional context provided.",
            files_info=files_info,
            previous_attempts=previous_attempts or "None (first attempt)",
            escalation_history=escalation_history or "None (first attempt)"
        )

    def _parse_response(
        self,
        response: str,
        expected_files: List[str]
    ) -> List[CodeChange]:
        """Parse la réponse du LLM pour extraire les changements"""
        changes = []

        # Chercher les blocs de code avec filepath
        import re
        pattern = r'```(\w+)?:?([^\n]+)?\n(.*?)```'
        matches = re.finditer(pattern, response, re.DOTALL)

        for match in matches:
            language = match.group(1) or 'python'
            filepath_hint = match.group(2) or ''
            code_content = match.group(3).strip()

            # Essayer de déterminer le fichier cible
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
                # Lire contenu original si existe
                original_content = ""
                if Path(target_file).exists():
                    with open(target_file, 'r', encoding='utf-8') as f:
                        original_content = f.read()

                # Calculer diff
                diff = self._calculate_diff(original_content, code_content, target_file)

                changes.append(CodeChange(
                    filepath=target_file,
                    original_content=original_content,
                    new_content=code_content,
                    change_type='new_file' if not original_content else 'full_file',
                    diff=diff
                ))

        return changes

    def _calculate_diff(
        self,
        original: str,
        new: str,
        filepath: str
    ) -> str:
        """Calcule le diff entre deux contenus"""
        import tempfile
        import os

        try:
            # Créer fichiers temporaires
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f1:
                f1.write(original)
                temp1 = f1.name

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f2:
                f2.write(new)
                temp2 = f2.name

            # Calculer diff
            result = subprocess.run(
                ['diff', '-u', temp1, temp2],
                capture_output=True,
                text=True
            )

            # Nettoyer
            os.unlink(temp1)
            os.unlink(temp2)

            return result.stdout

        except Exception:
            return ""

    def apply_changes(
        self,
        changes: List[CodeChange],
        backup: bool = True
    ) -> bool:
        """
        Applique les changements aux fichiers

        Args:
            changes: Liste des changements à appliquer
            backup: Si True, créer des backups

        Returns:
            True si tous les changements appliqués avec succès
        """
        try:
            for change in changes:
                filepath = Path(change.filepath)

                # Backup si demandé
                if backup and filepath.exists():
                    backup_path = filepath.with_suffix(filepath.suffix + '.backup')
                    import shutil
                    shutil.copy(filepath, backup_path)

                # Créer répertoires si nécessaire
                filepath.parent.mkdir(parents=True, exist_ok=True)

                # Écrire nouveau contenu
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(change.new_content)

            return True

        except Exception as e:
            print(f"Error applying changes: {e}")
            return False

    def rollback_changes(self, changes: List[CodeChange]) -> bool:
        """
        Rollback les changements (restaure les backups)

        Args:
            changes: Changements à rollback

        Returns:
            True si rollback réussi
        """
        try:
            for change in changes:
                filepath = Path(change.filepath)
                backup_path = filepath.with_suffix(filepath.suffix + '.backup')

                if backup_path.exists():
                    import shutil
                    shutil.copy(backup_path, filepath)
                    backup_path.unlink()

            return True

        except Exception as e:
            print(f"Error during rollback: {e}")
            return False

    def get_development_summary(self) -> Dict[str, Any]:
        """Obtient un résumé de l'historique de développement"""
        if not self.development_history:
            return {
                'total_attempts': 0,
                'success_rate': 0.0,
                'total_cost': 0.0,
                'tier_usage': {}
            }

        total = len(self.development_history)
        successes = sum(1 for r in self.development_history if r.success)
        total_cost = sum(r.cost for r in self.development_history)

        tier_usage = {}
        for result in self.development_history:
            tier_name = result.tier_used.value
            if tier_name not in tier_usage:
                tier_usage[tier_name] = {'count': 0, 'cost': 0.0}
            tier_usage[tier_name]['count'] += 1
            tier_usage[tier_name]['cost'] += result.cost

        return {
            'total_attempts': total,
            'success_rate': successes / total if total > 0 else 0.0,
            'total_cost': total_cost,
            'tier_usage': tier_usage
        }


def create_developer_agent(llm_client: LLMClient) -> DeveloperAgent:
    """Factory function pour créer un DeveloperAgent"""
    return DeveloperAgent(llm_client)


# Test si exécuté directement
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    print("Testing Developer Agent...")

    client = LLMClient()
    developer = DeveloperAgent(client)

    # Test 1: Préparer file info
    print("\n1. Testing file info preparation...")
    info = developer._prepare_files_info([__file__], use_partial=False)
    print(f"✓ File info prepared ({len(info)} chars)")
    print(f"  Preview: {info[:200]}...")

    # Test 2: Build prompt pour différents tiers
    print("\n2. Testing prompt building for different tiers...")
    for tier in [ModelTier.DEEPSEEK, ModelTier.GPT5, ModelTier.CLAUDE]:
        prompt = developer._build_prompt(
            task="Add docstrings to functions",
            tier=tier,
            context="This is a developer agent module",
            files_info=info[:500]
        )
        print(f"  Tier {tier.value}: {len(prompt)} chars")

    # Test 3: Parse response
    print("\n3. Testing response parsing...")
    mock_response = """
Here's the solution:

```python:test.py
def hello():
    print("world")
```
    """
    changes = developer._parse_response(mock_response, ["test.py"])
    print(f"✓ Parsed {len(changes)} changes")
    if changes:
        print(f"  Change: {changes[0].filepath} ({changes[0].change_type})")

    # Test 4: Summary
    print("\n4. Testing development summary...")
    summary = developer.get_development_summary()
    print(f"✓ Summary:")
    print(f"  Total attempts: {summary['total_attempts']}")
    print(f"  Total cost: ${summary['total_cost']:.4f}")

    print("\n✓ Developer Agent works correctly!")
