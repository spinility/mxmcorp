#!/usr/bin/env python3
"""
Test du PromptEngineer - Détection de contradictions et génération de prompts
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from cortex.core.llm_client import LLMClient, ModelTier
from cortex.core.prompt_engineer import PromptEngineer
from cortex.tools.builtin_tools import get_all_builtin_tools

def test_contradiction_detection():
    """Test la détection de contradictions"""
    print("=" * 80)
    print("TEST: Détection de Contradictions")
    print("=" * 80)

    llm_client = LLMClient()
    prompt_engineer = PromptEngineer(llm_client)
    tools = get_all_builtin_tools()

    # Test 1: Demande de créer delete_file (existe déjà)
    print("\n1. Test: 'Implémente l'outil pour effacer des fichiers'")
    contradiction = prompt_engineer.detect_contradiction(
        "Implémente l'outil pour effacer des fichiers",
        tools
    )

    if contradiction:
        print(f"   ✓ Contradiction détectée!")
        print(f"   Type: {contradiction['type']}")
        print(f"   Tool: {contradiction['tool_name']}")
        print(f"   Message: {contradiction['message']}")
    else:
        print("   ✗ Aucune contradiction détectée (ERREUR)")

    # Test 2: Demande de créer create_file (existe déjà)
    print("\n2. Test: 'Crée un tool pour créer des fichiers'")
    contradiction = prompt_engineer.detect_contradiction(
        "Crée un tool pour créer des fichiers",
        tools
    )

    if contradiction:
        print(f"   ✓ Contradiction détectée!")
        print(f"   Tool: {contradiction['tool_name']}")
    else:
        print("   ✗ Aucune contradiction détectée (ERREUR)")

    # Test 3: Demande normale (pas de contradiction)
    print("\n3. Test: 'Crée un fichier test.txt'")
    contradiction = prompt_engineer.detect_contradiction(
        "Crée un fichier test.txt",
        tools
    )

    if contradiction:
        print(f"   ✗ Contradiction détectée à tort (ERREUR)")
    else:
        print("   ✓ Aucune contradiction (correct)")

    # Test 4: Demande d'un outil inexistant
    print("\n4. Test: 'Implémente un tool pour traduire du texte'")
    contradiction = prompt_engineer.detect_contradiction(
        "Implémente un tool pour traduire du texte",
        tools
    )

    if contradiction:
        print(f"   ✗ Contradiction détectée à tort (ERREUR)")
    else:
        print("   ✓ Aucune contradiction (correct)")

    print()

def test_prompt_generation():
    """Test la génération de prompts selon les tiers"""
    print("=" * 80)
    print("TEST: Génération de Prompts")
    print("=" * 80)

    llm_client = LLMClient()
    prompt_engineer = PromptEngineer(llm_client)
    tools = get_all_builtin_tools()

    request = "Crée un fichier test.md"

    # Test 1: Prompt pour NANO
    print("\n1. Prompt pour NANO (court et direct):")
    print("-" * 80)
    prompt = prompt_engineer.build_agent_prompt(
        ModelTier.NANO,
        request,
        tools,
        contradiction=None
    )
    print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
    print(f"\nLongueur: {len(prompt)} caractères")

    # Test 2: Prompt pour DEEPSEEK
    print("\n2. Prompt pour DEEPSEEK (structuré avec exemples):")
    print("-" * 80)
    prompt = prompt_engineer.build_agent_prompt(
        ModelTier.DEEPSEEK,
        request,
        tools,
        contradiction=None
    )
    print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
    print(f"\nLongueur: {len(prompt)} caractères")

    # Test 3: Prompt pour CLAUDE
    print("\n3. Prompt pour CLAUDE (détaillé):")
    print("-" * 80)
    prompt = prompt_engineer.build_agent_prompt(
        ModelTier.CLAUDE,
        request,
        tools,
        contradiction=None
    )
    print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
    print(f"\nLongueur: {len(prompt)} caractères")

    print()

def test_contradiction_prompt():
    """Test le prompt de contradiction"""
    print("=" * 80)
    print("TEST: Prompt de Contradiction")
    print("=" * 80)

    llm_client = LLMClient()
    prompt_engineer = PromptEngineer(llm_client)
    tools = get_all_builtin_tools()

    request = "Implémente l'outil delete_file"

    # Détecter la contradiction
    contradiction = prompt_engineer.detect_contradiction(request, tools)

    if not contradiction:
        print("ERREUR: Contradiction non détectée!")
        return

    # Générer le prompt de contradiction pour NANO
    print("\n1. Prompt de contradiction pour NANO:")
    print("-" * 80)
    prompt = prompt_engineer.build_agent_prompt(
        ModelTier.NANO,
        request,
        tools,
        contradiction=contradiction
    )
    print(prompt)

    print("\n2. Prompt de contradiction pour DEEPSEEK:")
    print("-" * 80)
    prompt = prompt_engineer.build_agent_prompt(
        ModelTier.DEEPSEEK,
        request,
        tools,
        contradiction=contradiction
    )
    print(prompt)

    print()

if __name__ == "__main__":
    test_contradiction_detection()
    test_prompt_generation()
    test_contradiction_prompt()

    print("=" * 80)
    print("✓ Tous les tests terminés!")
    print("=" * 80)
