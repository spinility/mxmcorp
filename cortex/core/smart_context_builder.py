"""
Smart Context Builder - Construit le context optimal pour chaque tâche

Utilise la Knowledge Base avec embeddings pour créer un context:
- Ultra-compact (< 1000 tokens)
- Pertinent pour la tâche
- Contenant toute l'information nécessaire
- Filtrage par similarité adaptative selon la gravité
"""

from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from enum import Enum

from cortex.core.project_knowledge_base import ProjectKnowledgeBase


def count_tokens(text: str) -> int:
    """Estime le nombre de tokens (rough: 4 chars = 1 token)"""
    return len(text) // 4


class TaskSeverity(Enum):
    """Gravité d'une tâche - détermine le seuil de similarité requis"""
    CRITICAL = "critical"      # Production, sécurité, données critiques
    HIGH = "high"              # Fonctionnalités importantes, API publiques
    MEDIUM = "medium"          # Fonctionnalités standard
    LOW = "low"                # Refactoring, documentation, tests


class SimilarityThresholds:
    """
    Seuils de similarité adaptatifs selon la gravité

    ChromaDB utilise la distance L2 (Euclidean):
    - 0.0 = identique
    - Plus la distance est grande, moins c'est similaire
    - Seuils typiques: 0.0-0.8 = très pertinent, 0.8-1.2 = pertinent, >1.2 = peu pertinent
    """

    # Seuils maximum de distance par gravité (plus strict = plus petite distance acceptée)
    THRESHOLDS = {
        TaskSeverity.CRITICAL: 0.6,   # Très strict: seulement les matchs très similaires
        TaskSeverity.HIGH: 0.85,      # Strict: matchs assez similaires
        TaskSeverity.MEDIUM: 1.1,     # Standard: matchs pertinents
        TaskSeverity.LOW: 1.5         # Permissif: tous les matchs raisonnables
    }

    # Nombre minimum de résultats même si similarité faible
    MIN_RESULTS = {
        TaskSeverity.CRITICAL: 1,     # Au moins 1 résultat même si faible
        TaskSeverity.HIGH: 2,
        TaskSeverity.MEDIUM: 2,
        TaskSeverity.LOW: 3
    }

    @classmethod
    def get_threshold(cls, severity: TaskSeverity) -> float:
        """Retourne le seuil pour une gravité donnée"""
        return cls.THRESHOLDS[severity]

    @classmethod
    def get_min_results(cls, severity: TaskSeverity) -> int:
        """Retourne le nombre minimum de résultats"""
        return cls.MIN_RESULTS[severity]

    @classmethod
    def assess_quality(cls, distance: float, severity: TaskSeverity) -> str:
        """Évalue la qualité du match"""
        threshold = cls.get_threshold(severity)

        if distance <= threshold * 0.5:
            return "excellent"
        elif distance <= threshold * 0.75:
            return "good"
        elif distance <= threshold:
            return "acceptable"
        else:
            return "weak"


class SmartContextBuilder:
    """
    Construit un context intelligent et compact pour chaque tâche
    avec filtrage adaptatif selon la gravité
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
        self.context_quality_report: Optional[Dict[str, Any]] = None

    def build_context(
        self,
        task: str,
        budget: int = 900,
        severity: TaskSeverity = TaskSeverity.MEDIUM,
        include_quality_report: bool = False
    ) -> str:
        """
        Construit un context optimisé pour la tâche

        Args:
            task: Description de la tâche
            budget: Budget de tokens (default 900, laisse 100 pour system state)
            severity: Gravité de la tâche (affecte le seuil de similarité)
            include_quality_report: Si True, inclut un rapport de qualité dans le context

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

        # 2. SEMANTIC SEARCH (600 tokens max) - Dynamique avec filtrage adaptatif
        remaining_budget = budget - tokens_used
        relevant, quality_info = self._get_relevant_context(
            task,
            budget=remaining_budget,
            severity=severity
        )

        if relevant:
            context_parts.append(relevant)
            tokens_used += count_tokens(relevant)

        # Sauvegarder le rapport de qualité
        self.context_quality_report = quality_info

        # 3. Rapport de qualité si demandé
        if include_quality_report and quality_info:
            report = self._format_quality_report(quality_info, severity)
            context_parts.append(report)
            tokens_used += count_tokens(report)

        # 4. Optionnel: System state si espace restant
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

    def _get_relevant_context(
        self,
        task: str,
        budget: int = 600,
        severity: TaskSeverity = TaskSeverity.MEDIUM
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Récupère le context pertinent via semantic search avec filtrage adaptatif

        Args:
            task: Description de la tâche
            budget: Budget de tokens
            severity: Gravité de la tâche (affecte le seuil de similarité)

        Returns:
            Tuple (context formaté, rapport de qualité)
        """
        if not self.kb:
            return "", {"error": "Knowledge base not available"}

        # Recherche multi-type
        chunks = []
        current_tokens = 0
        quality_info = {
            "severity": severity.value,
            "threshold": SimilarityThresholds.get_threshold(severity),
            "results_by_type": {},
            "filtered_count": 0,
            "total_count": 0,
            "warnings": []
        }

        # Priority order: code > workflow > structure
        for search_type in ["code", "workflow", "structure", "employee"]:
            try:
                results = self.kb.search(
                    query=task,
                    n_results=5,  # Demander plus pour pouvoir filtrer
                    filter_type=search_type
                )

                type_quality = {
                    "found": 0,
                    "accepted": 0,
                    "rejected": 0,
                    "distances": []
                }

                # Ajouter les résultats pertinents avec filtrage par similarité
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0]
                    distances = results.get("distances", [[1.0] * len(docs)])[0]

                    threshold = SimilarityThresholds.get_threshold(severity)
                    min_results = SimilarityThresholds.get_min_results(severity)
                    accepted_in_type = 0

                    for doc, meta, distance in zip(docs, metas, distances):
                        type_quality["found"] += 1
                        quality_info["total_count"] += 1

                        # Filtrage par seuil de similarité
                        # Exception: toujours accepter au moins min_results même si faible
                        accept_result = (
                            distance <= threshold or
                            accepted_in_type < min_results
                        )

                        if accept_result:
                            chunk_tokens = count_tokens(doc)

                            # Vérifier si on a le budget
                            if current_tokens + chunk_tokens <= budget:
                                quality = SimilarityThresholds.assess_quality(distance, severity)

                                chunks.append({
                                    "type": search_type,
                                    "content": doc,
                                    "file": meta.get("file", "N/A"),
                                    "distance": distance,
                                    "quality": quality
                                })
                                current_tokens += chunk_tokens
                                accepted_in_type += 1
                                type_quality["accepted"] += 1
                                type_quality["distances"].append(distance)

                                # Warning si qualité faible mais accepté (min_results)
                                if distance > threshold:
                                    quality_info["warnings"].append(
                                        f"{search_type}: weak match (d={distance:.2f}) "
                                        f"accepted to meet minimum ({min_results})"
                                    )
                            else:
                                break  # Budget épuisé
                        else:
                            type_quality["rejected"] += 1
                            quality_info["filtered_count"] += 1

                quality_info["results_by_type"][search_type] = type_quality

            except Exception as e:
                print(f"⚠️  Search error for {search_type}: {e}")
                quality_info["warnings"].append(f"{search_type}: search error - {e}")
                continue

            # Stop si budget épuisé
            if current_tokens >= budget * 0.9:  # 90% du budget
                break

        # Formater les chunks
        formatted_context = self._format_chunks(chunks)
        return formatted_context, quality_info

    def _format_chunks(self, chunks: list) -> str:
        """Formate les chunks pour le LLM"""
        if not chunks:
            return ""

        formatted = ["[RELEVANT CONTEXT]"]

        for chunk in chunks:
            # Inclure la qualité si disponible
            quality_tag = ""
            if "quality" in chunk and "distance" in chunk:
                quality_tag = f" [similarity: {chunk['quality']}]"

            formatted.append(f"\n[{chunk['type'].upper()}] {chunk['file']}{quality_tag}")
            formatted.append(chunk['content'][:500])  # Max 500 chars per chunk

        return "\n".join(formatted)

    def _format_quality_report(self, quality_info: Dict[str, Any], severity: TaskSeverity) -> str:
        """Formate le rapport de qualité du context"""
        lines = ["[CONTEXT QUALITY REPORT]"]
        lines.append(f"Task Severity: {severity.value.upper()}")
        lines.append(f"Similarity Threshold: {quality_info['threshold']:.2f}")
        lines.append(f"Total Results Found: {quality_info['total_count']}")
        lines.append(f"Results Filtered Out: {quality_info['filtered_count']}")

        # Stats par type
        lines.append("\nResults by Type:")
        for search_type, stats in quality_info["results_by_type"].items():
            if stats["found"] > 0:
                avg_dist = sum(stats["distances"]) / len(stats["distances"]) if stats["distances"] else 0
                lines.append(
                    f"  {search_type}: {stats['accepted']}/{stats['found']} accepted "
                    f"(avg similarity: {avg_dist:.2f})"
                )

        # Warnings
        if quality_info["warnings"]:
            lines.append("\nWarnings:")
            for warning in quality_info["warnings"][:3]:  # Max 3 warnings
                lines.append(f"  ⚠️  {warning}")

        return "\n".join(lines)

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

    def get_last_quality_report(self) -> Optional[Dict[str, Any]]:
        """
        Retourne le rapport de qualité du dernier build_context()

        Returns:
            Rapport de qualité ou None si pas encore exécuté
        """
        return self.context_quality_report

    def detect_task_severity(self, task: str) -> TaskSeverity:
        """
        Détecte automatiquement la gravité d'une tâche basée sur des mots-clés

        Args:
            task: Description de la tâche

        Returns:
            Gravité détectée
        """
        task_lower = task.lower()

        # CRITICAL: production, sécurité, données sensibles
        critical_keywords = [
            "production", "security", "authentication", "authorization",
            "payment", "database migration", "critical", "urgent",
            "password", "encryption", "api key", "secret"
        ]

        # HIGH: fonctionnalités importantes, API publiques
        high_keywords = [
            "api", "endpoint", "public", "user-facing", "important",
            "core feature", "main", "primary"
        ]

        # LOW: refactoring, documentation, tests
        low_keywords = [
            "refactor", "documentation", "comment", "test", "rename",
            "format", "cleanup", "typo", "style"
        ]

        # Détection par ordre de priorité
        if any(keyword in task_lower for keyword in critical_keywords):
            return TaskSeverity.CRITICAL
        elif any(keyword in task_lower for keyword in high_keywords):
            return TaskSeverity.HIGH
        elif any(keyword in task_lower for keyword in low_keywords):
            return TaskSeverity.LOW
        else:
            return TaskSeverity.MEDIUM


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
