"""
Smart Context Builder - Construit le context optimal pour chaque tâche

Utilise la Knowledge Base avec embeddings pour créer un context:
- Ultra-compact (< 1000 tokens)
- Pertinent pour la tâche
- Contenant toute l'information nécessaire
"""

from typing import Dict, Any, Optional
from pathlib import Path

from cortex.core.project_knowledge_base import ProjectKnowledgeBase


def count_tokens(text: str) -> int:
    """Estime le nombre de tokens (rough: 4 chars = 1 token)"""
    return len(text) // 4


class SmartContextBuilder:
    """
    Construit un context intelligent et compact pour chaque tâche
    """

    def __init__(self, project_root: Path, knowledge_base: Optional[ProjectKnowledgeBase] = None):
        """
        Args:
            project_root: Racine du projet
            knowledge_base: KB existante (optionnel)
        """
        self.project_root = project_root

        if knowledge_base:
            self.kb = knowledge_base
        else:
            # Créer avec embeddings locaux (gratuit pour dev)
            try:
                self.kb = ProjectKnowledgeBase(project_root, use_local_embeddings=True)
            except ImportError:
                print("⚠️  ChromaDB not available. Context will be basic.")
                self.kb = None

        self.token_budget = 1000

    def build_context(self, task: str, budget: int = 900) -> str:
        """
        Construit un context optimisé pour la tâche

        Args:
            task: Description de la tâche
            budget: Budget de tokens (default 900, laisse 100 pour system state)

        Returns:
            Context formaté, < budget tokens
        """
        if not self.kb:
            return self._build_basic_context()

        context_parts = []
        tokens_used = 0

        # 1. BASE CONTEXT (200 tokens) - Toujours inclus
        base = self._get_base_context()
        context_parts.append(base)
        tokens_used += count_tokens(base)

        # 2. SEMANTIC SEARCH (600 tokens max) - Dynamique
        remaining_budget = budget - tokens_used
        relevant = self._get_relevant_context(task, budget=remaining_budget)

        if relevant:
            context_parts.append(relevant)
            tokens_used += count_tokens(relevant)

        # 3. Optionnel: System state si espace restant
        remaining = budget - tokens_used
        if remaining > 100:
            state = self._get_system_state()
            context_parts.append(state)

        return "\n\n".join(context_parts)

    def _get_base_context(self) -> str:
        """Context de base du projet (200 tokens)"""
        return """[PROJECT CONTEXT]
Project: MXMCorp Cortex
Type: AI Agent System
Stack: Python 3.10+, FastAPI, PostgreSQL

Structure:
- cortex/agents/: Agent implementations (CEO, Directors, Workers)
- cortex/core/: Core systems (LLM client, routing, config)
- cortex/tools/: Reusable tools and registry
- cortex/models/: Data models

Conventions:
- Type hints required
- Docstrings for public methods
- Tests in tests/ directory
- Use nano model for simple tasks, escalate when needed"""

    def _get_relevant_context(self, task: str, budget: int = 600) -> str:
        """
        Récupère le context pertinent via semantic search

        Args:
            task: Description de la tâche
            budget: Budget de tokens

        Returns:
            Context pertinent formaté
        """
        if not self.kb:
            return ""

        # Recherche multi-type
        chunks = []
        current_tokens = 0

        # Priority order: code > workflow > structure
        for search_type in ["code", "workflow", "structure", "employee"]:
            try:
                results = self.kb.search(
                    query=task,
                    n_results=2,  # Top 2 per type
                    filter_type=search_type
                )

                # Ajouter les résultats pertinents
                if results and "documents" in results and results["documents"]:
                    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                        chunk_tokens = count_tokens(doc)

                        # Vérifier si on a le budget
                        if current_tokens + chunk_tokens <= budget:
                            chunks.append({
                                "type": search_type,
                                "content": doc,
                                "file": meta.get("file", "N/A")
                            })
                            current_tokens += chunk_tokens
                        else:
                            break  # Budget épuisé

            except Exception as e:
                print(f"⚠️  Search error for {search_type}: {e}")
                continue

            # Stop si budget épuisé
            if current_tokens >= budget * 0.9:  # 90% du budget
                break

        # Formater les chunks
        return self._format_chunks(chunks)

    def _format_chunks(self, chunks: list) -> str:
        """Formate les chunks pour le LLM"""
        if not chunks:
            return ""

        formatted = ["[RELEVANT CONTEXT]"]

        for chunk in chunks:
            formatted.append(f"\n[{chunk['type'].upper()}] {chunk['file']}")
            formatted.append(chunk['content'][:500])  # Max 500 chars per chunk

        return "\n".join(formatted)

    def _get_system_state(self) -> str:
        """État actuel du système (100 tokens)"""
        try:
            from cortex.core.global_context import get_global_context
            return get_global_context().get_context(compact=True)
        except:
            return "[SYSTEM STATE]\nMode: normal | Health: good"

    def _build_basic_context(self) -> str:
        """Context de base si KB pas disponible"""
        return self._get_base_context() + "\n\n" + self._get_system_state()

    def get_token_estimate(self, context: str) -> int:
        """Estime le nombre de tokens d'un context"""
        return count_tokens(context)


if __name__ == "__main__":
    # Test
    print("Testing Smart Context Builder...\n")

    builder = SmartContextBuilder(project_root=Path.cwd())

    # Test 1: Simple task
    print("=" * 70)
    print("TEST 1: Simple Task")
    print("=" * 70)
    task1 = "Add validation to User model"
    context1 = builder.build_context(task1)
    tokens1 = builder.get_token_estimate(context1)

    print(f"\nTask: {task1}")
    print(f"Context tokens: {tokens1}")
    print(f"\nContext preview:")
    print(context1[:500])
    print("...")

    # Test 2: Complex task
    print("\n" + "=" * 70)
    print("TEST 2: Complex Task")
    print("=" * 70)
    task2 = "Create a new agent for performance monitoring"
    context2 = builder.build_context(task2)
    tokens2 = builder.get_token_estimate(context2)

    print(f"\nTask: {task2}")
    print(f"Context tokens: {tokens2}")
    print(f"\nContext preview:")
    print(context2[:500])
    print("...")

    # Test 3: Budget check
    print("\n" + "=" * 70)
    print("TEST 3: Budget Verification")
    print("=" * 70)
    print(f"Token budget: 1000")
    print(f"Task 1 used: {tokens1} tokens ({tokens1/1000*100:.1f}%)")
    print(f"Task 2 used: {tokens2} tokens ({tokens2/1000*100:.1f}%)")

    if tokens1 < 1000 and tokens2 < 1000:
        print("\n✅ All contexts within budget!")
    else:
        print("\n❌ Some contexts exceed budget")

    print("\n✅ Smart Context Builder test complete!")
