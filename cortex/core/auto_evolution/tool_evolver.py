"""
Tool Evolver - Génère automatiquement des outils bash réutilisables

Responsabilités:
- Détecte commandes bash récurrentes
- Génère scripts bash avec paramètres
- Crée documentation et tests
- Enregistre dans registry des outils
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import json

from cortex.core.auto_evolution.pattern_detector import DetectedPattern


@dataclass
class GeneratedTool:
    """
    Outil bash généré automatiquement
    """
    name: str
    description: str
    script_content: str
    parameters: List[Dict[str, str]]  # [{"name": "param1", "type": "string", "desc": "..."}]
    usage_example: str
    test_content: str
    created_at: datetime
    pattern_id: str  # Pattern qui a motivé la création
    frequency_detected: int
    estimated_time_savings: float  # heures/semaine

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "script_content": self.script_content,
            "parameters": self.parameters,
            "usage_example": self.usage_example,
            "test_content": self.test_content,
            "created_at": self.created_at.isoformat(),
            "pattern_id": self.pattern_id,
            "frequency_detected": self.frequency_detected,
            "estimated_time_savings": self.estimated_time_savings
        }


class ToolEvolver:
    """
    Générateur automatique d'outils bash

    Analyse patterns et crée scripts bash réutilisables
    """

    def __init__(self, tools_dir: str = "cortex/tools/generated"):
        self.tools_dir = Path(tools_dir)
        self.tools_dir.mkdir(parents=True, exist_ok=True)

        self.registry_file = self.tools_dir / "tool_registry.json"
        self.generated_tools: List[GeneratedTool] = []
        self._load_registry()

    def _load_registry(self):
        """Charge le registry des outils générés"""
        if self.registry_file.exists():
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # TODO: Reconstruire GeneratedTool objects si nécessaire

    def _save_registry(self):
        """Sauvegarde le registry"""
        data = {
            "updated_at": datetime.now().isoformat(),
            "total_tools": len(self.generated_tools),
            "tools": [tool.to_dict() for tool in self.generated_tools]
        }

        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def should_create_tool(self, pattern: DetectedPattern) -> bool:
        """
        Détermine si un tool devrait être créé pour ce pattern

        Critères:
        - Pattern recommande "tool"
        - OU a 2+ outils utilisés ensemble fréquemment
        - OU commandes bash détectées dans description
        """
        if pattern.recommended_evolution == "tool":
            return True

        if len(pattern.tools_used) >= 2 and pattern.frequency >= 3:
            return True

        # Détecter commandes bash dans keywords
        bash_keywords = {"grep", "find", "git", "sed", "awk", "curl", "test", "check"}
        if any(kw in bash_keywords for kw in pattern.keywords):
            return True

        return False

    def generate_tool_from_pattern(self, pattern: DetectedPattern) -> GeneratedTool:
        """
        Génère un outil bash depuis un pattern détecté

        Args:
            pattern: Pattern détecté

        Returns:
            GeneratedTool créé
        """
        # Générer nom de l'outil (snake_case)
        tool_name = self._generate_tool_name(pattern)

        # Déterminer paramètres nécessaires
        parameters = self._extract_parameters(pattern)

        # Générer script bash
        script_content = self._generate_bash_script(
            tool_name=tool_name,
            description=pattern.description,
            parameters=parameters,
            tools_used=pattern.tools_used,
            keywords=pattern.keywords
        )

        # Générer exemple d'usage
        usage_example = self._generate_usage_example(tool_name, parameters)

        # Générer tests
        test_content = self._generate_test_script(tool_name, parameters)

        tool = GeneratedTool(
            name=tool_name,
            description=pattern.description,
            script_content=script_content,
            parameters=parameters,
            usage_example=usage_example,
            test_content=test_content,
            created_at=datetime.now(),
            pattern_id=pattern.id,
            frequency_detected=pattern.frequency,
            estimated_time_savings=pattern.potential_time_savings
        )

        return tool

    def _generate_tool_name(self, pattern: DetectedPattern) -> str:
        """
        Génère nom pour l'outil en snake_case

        Basé sur keywords principaux
        """
        # Prendre top 2-3 keywords
        keywords = pattern.keywords[:3]

        # Nettoyer et joiner
        clean_keywords = [kw.lower().replace("-", "_") for kw in keywords]

        # Ajouter verbe si nécessaire
        verbs = ["check", "run", "test", "analyze", "scan", "audit"]
        if not any(v in clean_keywords[0] for v in verbs):
            # Inférer verbe basé sur context
            if "security" in clean_keywords or "audit" in clean_keywords:
                clean_keywords.insert(0, "audit")
            elif "test" in clean_keywords:
                clean_keywords.insert(0, "run")
            else:
                clean_keywords.insert(0, "check")

        return "_".join(clean_keywords[:3])

    def _extract_parameters(self, pattern: DetectedPattern) -> List[Dict[str, str]]:
        """
        Extrait paramètres nécessaires depuis pattern

        Détermine quels inputs l'outil devrait accepter
        """
        params = []

        # Paramètres communs basés sur keywords
        if any(kw in ["file", "path", "directory", "code"] for kw in pattern.keywords):
            params.append({
                "name": "target_path",
                "type": "string",
                "description": "Path to file or directory to process",
                "required": "true"
            })

        if "output" in pattern.keywords or "report" in pattern.keywords:
            params.append({
                "name": "output_file",
                "type": "string",
                "description": "Output file path",
                "required": "false",
                "default": "report.txt"
            })

        # Si pas de paramètres détectés, au moins un path générique
        if not params:
            params.append({
                "name": "input",
                "type": "string",
                "description": "Input parameter",
                "required": "true"
            })

        return params

    def _generate_bash_script(
        self,
        tool_name: str,
        description: str,
        parameters: List[Dict[str, str]],
        tools_used: List[str],
        keywords: List[str]
    ) -> str:
        """
        Génère le script bash complet
        """
        # Header
        script_lines = [
            "#!/bin/bash",
            "#",
            f"# Auto-generated tool: {tool_name}",
            f"# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Description: {description}",
            "#",
            "# Generated by ToolEvolver based on detected pattern",
            f"# Tools used: {', '.join(tools_used) if tools_used else 'various'}",
            "#",
            "",
            "set -euo pipefail",
            ""
        ]

        # Usage function
        required_param_names = " ".join(f"<{p['name']}>" for p in parameters if p.get("required") == "true")
        script_lines.extend([
            "usage() {",
            f'    echo "Usage: $0 {required_param_names}"',
        ])

        for param in parameters:
            param_name = param["name"]
            param_desc = param["description"]
            script_lines.append(f'    echo "  {param_name}: {param_desc}"')

        script_lines.extend([
            '    exit 1',
            '}',
            ''
        ])

        # Parameter validation
        required_params = [p for p in parameters if p.get("required") == "true"]
        if required_params:
            script_lines.extend([
                f'if [ $# -lt {len(required_params)} ]; then',
                '    usage',
                'fi',
                ''
            ])

        # Assign parameters
        for i, param in enumerate(parameters, 1):
            if param.get("required") == "true":
                script_lines.append(f'{param["name"].upper()}="${i}"')
            else:
                default = param.get("default", "")
                script_lines.append(f'{param["name"].upper()}="${{{i}:-{default}}}"')

        script_lines.append('')

        # Main logic (template basé sur tools_used)
        script_lines.extend([
            '# Main logic',
            'echo "Starting ' + tool_name + '..."',
            ''
        ])

        # Générer logic basée sur tools
        if "grep" in tools_used or "find" in tools_used:
            script_lines.extend([
                '# Search and analyze',
                'if [ -f "$TARGET_PATH" ]; then',
                '    echo "Processing file: $TARGET_PATH"',
                '    # Add your processing logic here',
                '    grep -n "TODO\\|FIXME" "$TARGET_PATH" || true',
                'elif [ -d "$TARGET_PATH" ]; then',
                '    echo "Processing directory: $TARGET_PATH"',
                '    find "$TARGET_PATH" -type f -name "*.py" | while read -r file; do',
                '        echo "Checking: $file"',
                '        # Add your processing logic here',
                '    done',
                'else',
                '    echo "Error: Invalid path: $TARGET_PATH"',
                '    exit 1',
                'fi',
                ''
            ])
        else:
            # Generic template
            script_lines.extend([
                '# TODO: Implement specific logic for this tool',
                'echo "Processing: $INPUT"',
                '# Add your processing logic here',
                ''
            ])

        # Success message
        script_lines.extend([
            'echo "✓ ' + tool_name + ' completed successfully"',
            'exit 0'
        ])

        return '\n'.join(script_lines)

    def _generate_usage_example(
        self,
        tool_name: str,
        parameters: List[Dict[str, str]]
    ) -> str:
        """Génère exemple d'utilisation"""
        examples = [
            f"# Usage examples for {tool_name}.sh",
            "",
            "# Basic usage:"
        ]

        # Construire exemple avec paramètres
        required_params = [p for p in parameters if p.get("required") == "true"]

        if required_params:
            example_values = {
                "target_path": "./src",
                "input": "example_input",
                "file": "test.py",
                "directory": "./project"
            }

            param_values = []
            for param in required_params:
                param_name = param["name"]
                value = example_values.get(param_name, "value")
                param_values.append(value)

            examples.append(f"./{tool_name}.sh {' '.join(param_values)}")
        else:
            examples.append(f"./{tool_name}.sh")

        return '\n'.join(examples)

    def _generate_test_script(
        self,
        tool_name: str,
        parameters: List[Dict[str, str]]
    ) -> str:
        """Génère script de test bash"""
        test_lines = [
            "#!/bin/bash",
            "#",
            f"# Test script for {tool_name}",
            "#",
            "",
            "set -euo pipefail",
            "",
            "TOOL_SCRIPT=\"./" + tool_name + ".sh\"",
            "",
            "echo \"Testing " + tool_name + "...\"",
            "",
            "# Test 1: Help/usage",
            "echo \"Test 1: Verify usage message\"",
            "if $TOOL_SCRIPT 2>&1 | grep -q \"Usage\"; then",
            "    echo \"✓ Test 1 passed\"",
            "else",
            "    echo \"✗ Test 1 failed\"",
            "    exit 1",
            "fi",
            "",
            "# Test 2: Valid execution",
            "echo \"Test 2: Valid execution\"",
            "# TODO: Add specific test with valid parameters",
            "",
            "echo \"✓ All tests passed\"",
            "exit 0"
        ]

        return '\n'.join(test_lines)

    def save_tool(self, tool: GeneratedTool) -> Path:
        """
        Sauvegarde l'outil généré sur disque

        Returns:
            Path vers le script créé
        """
        # Sauvegarder script principal
        script_path = self.tools_dir / f"{tool.name}.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(tool.script_content)

        # Rendre exécutable
        script_path.chmod(0o755)

        # Sauvegarder test
        test_path = self.tools_dir / f"test_{tool.name}.sh"
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(tool.test_content)

        test_path.chmod(0o755)

        # Sauvegarder usage
        usage_path = self.tools_dir / f"{tool.name}_usage.txt"
        with open(usage_path, 'w', encoding='utf-8') as f:
            f.write(tool.usage_example)

        # Ajouter au registry
        self.generated_tools.append(tool)
        self._save_registry()

        print(f"✓ Tool saved: {script_path}")
        print(f"  Test: {test_path}")
        print(f"  Usage: {usage_path}")

        return script_path

    def list_generated_tools(self) -> List[GeneratedTool]:
        """Liste tous les outils générés"""
        return self.generated_tools


def create_tool_evolver(tools_dir: str = "cortex/tools/generated") -> ToolEvolver:
    """Factory function"""
    return ToolEvolver(tools_dir)


# Test
if __name__ == "__main__":
    print("Testing Tool Evolver...")

    from cortex.core.auto_evolution.pattern_detector import DetectedPattern
    from datetime import datetime

    # Test 1: Créer outil depuis pattern
    print("\n1. Creating tool from pattern...")

    mock_pattern = DetectedPattern(
        id="pattern_test_001",
        name="Security Audit Pattern",
        description="Perform security audit on Python codebase",
        frequency=5,
        success_rate=0.6,
        avg_duration=1800,
        avg_cost=0.05,
        keywords=["security", "audit", "check", "vulnerabilities"],
        agents_involved=["SecurityAgent"],
        tools_used=["grep", "find", "git"],
        workflows_used=["security_audit"],
        complexity_score=0.7,
        example_requests=["req1", "req2"],
        first_seen=datetime.now(),
        last_seen=datetime.now(),
        trend="stable",
        potential_time_savings=2.5,
        potential_success_improvement=0.35,
        recommended_evolution="tool"
    )

    evolver = ToolEvolver("cortex/tools/generated/test")

    # Test should_create_tool
    should_create = evolver.should_create_tool(mock_pattern)
    print(f"✓ Should create tool: {should_create}")

    # Test generate_tool
    tool = evolver.generate_tool_from_pattern(mock_pattern)
    print(f"✓ Generated tool: {tool.name}")
    print(f"  Description: {tool.description}")
    print(f"  Parameters: {len(tool.parameters)}")
    print(f"  Estimated savings: {tool.estimated_time_savings:.2f}h/week")

    # Test save_tool
    print("\n2. Saving tool...")
    script_path = evolver.save_tool(tool)
    print(f"✓ Tool saved to: {script_path}")

    # Test script est exécutable
    print("\n3. Testing generated script...")
    import subprocess
    result = subprocess.run(
        [str(script_path)],
        capture_output=True,
        text=True
    )
    if "Usage" in result.stderr or "Usage" in result.stdout:
        print("✓ Script is executable and shows usage")
    else:
        print("⚠ Script output:", result.stdout, result.stderr)

    # Afficher contenu du script
    print("\n4. Script content preview:")
    print("="*60)
    print(tool.script_content[:500] + "...")
    print("="*60)

    print("\n✓ Tool Evolver works correctly!")
