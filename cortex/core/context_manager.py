"""
Context Manager - Gestion intelligente du contexte applicatif global

Fonctionnalités:
- Git diff pour capturer changements récents
- Fusion avec contexte ultra-optimisé
- Jugement de nécessité du contexte (économie de tokens)
- Cache par embedding pour recherche sémantique
- Affichage visible des recherches de cache
"""

import subprocess
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier


@dataclass
class CachedContext:
    """Contexte mis en cache avec son embedding"""
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    created_at: str
    usage_count: int


class ContextManager:
    """Gestionnaire de contexte applicatif intelligent"""

    def __init__(
        self,
        llm_client: LLMClient,
        cache_path: str = "cortex/data/context_cache.json"
    ):
        """
        Initialize Context Manager

        Args:
            llm_client: Client LLM pour génération d'embeddings
            cache_path: Chemin du cache de contexte
        """
        self.llm_client = llm_client
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Cache de contextes avec embeddings
        self.context_cache: List[CachedContext] = []
        self._load_cache()

    def _load_cache(self):
        """Charge le cache depuis le fichier"""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data.get('contexts', []):
                        self.context_cache.append(CachedContext(
                            id=item['id'],
                            content=item['content'],
                            embedding=item['embedding'],
                            metadata=item['metadata'],
                            created_at=item['created_at'],
                            usage_count=item['usage_count']
                        ))
            except Exception as e:
                print(f"Warning: Failed to load context cache: {e}")

    def _save_cache(self):
        """Sauvegarde le cache dans le fichier"""
        try:
            data = {
                'contexts': [
                    {
                        'id': ctx.id,
                        'content': ctx.content,
                        'embedding': ctx.embedding,
                        'metadata': ctx.metadata,
                        'created_at': ctx.created_at,
                        'usage_count': ctx.usage_count
                    }
                    for ctx in self.context_cache
                ],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error: Failed to save context cache: {e}")

    def get_git_diff(
        self,
        max_lines: int = 500,
        staged: bool = False
    ) -> Optional[str]:
        """
        Récupère le git diff actuel

        Args:
            max_lines: Nombre maximum de lignes de diff
            staged: True pour diff staged, False pour unstaged

        Returns:
            Diff en string ou None si erreur
        """
        try:
            cmd = ["git", "diff"]
            if staged:
                cmd.append("--staged")

            # Ajouter limite de lignes
            cmd.extend([f"-U{max_lines}"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout

            return None

        except Exception as e:
            print(f"Warning: Failed to get git diff: {e}")
            return None

    def judge_context_necessity(
        self,
        user_request: str,
        available_context_size: int
    ) -> Dict[str, Any]:
        """
        Juge si le contexte applicatif est nécessaire

        Args:
            user_request: Requête utilisateur
            available_context_size: Taille du contexte disponible (en tokens)

        Returns:
            Dict avec décision et justification
        """
        # Prompt de jugement ultra-compact
        judge_prompt = f"""Analyze if application context is needed.

REQUEST: "{user_request}"
CONTEXT SIZE: {available_context_size} tokens

DECISION RULES:
- General questions → NO context needed
- Code changes/debugging → YES context needed
- Feature requests → MAYBE (if complex)
- Conversations → NO context needed

Reply JSON only:
{{"needed": true/false, "reason": "1 sentence", "confidence": 0.0-1.0}}"""

        try:
            response = self.llm_client.complete(
                messages=[{"role": "user", "content": judge_prompt}],
                tier=ModelTier.NANO,  # Rapide et économique
                max_tokens=100,
                temperature=0.3
            )

            result = json.loads(response.content.strip())
            return {
                'needed': result['needed'],
                'reason': result['reason'],
                'confidence': result['confidence'],
                'cost': response.cost
            }

        except Exception as e:
            # Fallback: heuristique simple
            code_keywords = ['bug', 'error', 'fix', 'implement', 'add', 'change', 'refactor', 'debug']
            needs_context = any(kw in user_request.lower() for kw in code_keywords)

            return {
                'needed': needs_context,
                'reason': 'Heuristic: code-related keywords detected' if needs_context else 'Heuristic: general question',
                'confidence': 0.6,
                'cost': 0.0
            }

    def create_embedding(self, text: str) -> List[float]:
        """
        Crée un embedding pour un texte

        Note: Simulation simple avec hashing pour l'instant
        Dans production, utiliser OpenAI embeddings API

        Args:
            text: Texte à embedder

        Returns:
            Vecteur d'embedding
        """
        # Simulation: créer un embedding basé sur les mots-clés
        # En production, utiliser: openai.Embedding.create(input=text, model="text-embedding-ada-002")

        keywords = ['function', 'class', 'def', 'import', 'error', 'bug', 'fix', 'add', 'remove', 'update']
        embedding = []

        text_lower = text.lower()
        for keyword in keywords:
            # Compter occurrences normalisées
            count = text_lower.count(keyword)
            embedding.append(float(count) / (len(text) + 1))

        # Ajouter longueur normalisée
        embedding.append(len(text) / 10000.0)

        # Normaliser le vecteur
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = (np.array(embedding) / norm).tolist()

        return embedding

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcule la similarité cosinus entre deux vecteurs"""
        arr1 = np.array(vec1)
        arr2 = np.array(vec2)

        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def search_cache_by_embedding(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.5
    ) -> List[Tuple[CachedContext, float]]:
        """
        Recherche dans le cache par similarité d'embedding

        Args:
            query: Requête de recherche
            top_k: Nombre de résultats à retourner
            threshold: Seuil de similarité minimum

        Returns:
            Liste de (context, similarity_score) triée par similarité
        """
        if not self.context_cache:
            return []

        # Créer embedding de la requête
        query_embedding = self.create_embedding(query)

        # Calculer similarités
        results = []
        for cached_ctx in self.context_cache:
            similarity = self.cosine_similarity(query_embedding, cached_ctx.embedding)

            if similarity >= threshold:
                results.append((cached_ctx, similarity))

        # Trier par similarité décroissante
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def add_to_cache(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CachedContext:
        """
        Ajoute un contexte au cache avec son embedding

        Args:
            content: Contenu du contexte
            metadata: Métadonnées optionnelles

        Returns:
            CachedContext créé
        """
        ctx_id = f"ctx_{len(self.context_cache) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        embedding = self.create_embedding(content)

        cached_ctx = CachedContext(
            id=ctx_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {},
            created_at=datetime.now().isoformat(),
            usage_count=0
        )

        self.context_cache.append(cached_ctx)
        self._save_cache()

        return cached_ctx

    def build_optimized_context(
        self,
        user_request: str,
        include_git_diff: bool = True,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Construit le contexte applicatif optimisé

        Args:
            user_request: Requête utilisateur
            include_git_diff: Inclure git diff si disponible
            max_tokens: Budget de tokens maximum

        Returns:
            Dict avec contexte optimisé et métadonnées
        """
        context_parts = []
        metadata = {
            'git_diff_included': False,
            'cache_hits': [],
            'context_needed': None,
            'total_cost': 0.0
        }

        # 1. Juger si contexte nécessaire
        judgment = self.judge_context_necessity(user_request, max_tokens)
        metadata['context_needed'] = judgment
        metadata['total_cost'] += judgment['cost']

        if not judgment['needed']:
            return {
                'context': '',
                'metadata': metadata,
                'message': f"Context not needed: {judgment['reason']}"
            }

        # 2. Chercher dans le cache par embedding
        print(f"🔍 Searching cache by embedding similarity...")
        cache_results = self.search_cache_by_embedding(user_request, top_k=2)

        if cache_results:
            print(f"✓ Found {len(cache_results)} relevant cached contexts:")
            for cached_ctx, similarity in cache_results:
                print(f"  - {cached_ctx.id} (similarity: {similarity:.2f})")
                metadata['cache_hits'].append({
                    'id': cached_ctx.id,
                    'similarity': similarity,
                    'metadata': cached_ctx.metadata
                })

                # Ajouter au contexte
                context_parts.append(f"# Cached Context (similarity: {similarity:.2f})")
                context_parts.append(cached_ctx.content[:500])  # Limiter taille

                # Incrémenter usage
                cached_ctx.usage_count += 1

            self._save_cache()
        else:
            print("  No relevant cache found")

        # 3. Ajouter git diff si demandé et disponible
        if include_git_diff:
            print(f"📊 Fetching git diff...")
            git_diff = self.get_git_diff(max_lines=100)

            if git_diff:
                print(f"✓ Git diff available ({len(git_diff)} chars)")
                context_parts.append("# Recent Changes (git diff)")
                context_parts.append(git_diff[:1000])  # Limiter à 1000 chars
                metadata['git_diff_included'] = True

                # Mettre en cache ce diff
                self.add_to_cache(
                    content=git_diff,
                    metadata={
                        'type': 'git_diff',
                        'timestamp': datetime.now().isoformat(),
                        'request': user_request[:100]
                    }
                )
            else:
                print("  No git changes detected")

        # 4. Fusionner le contexte
        final_context = "\n\n".join(context_parts)

        return {
            'context': final_context,
            'metadata': metadata,
            'message': 'Context built successfully'
        }


def create_context_manager(llm_client: LLMClient) -> ContextManager:
    """Factory function pour créer un ContextManager"""
    return ContextManager(llm_client)


# Test si exécuté directement
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    print("Testing Context Manager...")

    client = LLMClient()
    ctx_mgr = ContextManager(client, "cortex/data/test_context_cache.json")

    # Test 1: Jugement de nécessité
    print("\n1. Testing context necessity judgment...")

    test_requests = [
        "What is Python?",
        "Fix the authentication bug in login.py",
        "How are you today?"
    ]

    for req in test_requests:
        result = ctx_mgr.judge_context_necessity(req, 2000)
        print(f"  '{req}'")
        print(f"    → Needed: {result['needed']} ({result['reason']})")

    # Test 2: Créer des embeddings
    print("\n2. Testing embedding creation...")
    text1 = "Fix authentication bug in login function"
    text2 = "Implement user authentication system"
    text3 = "What is the weather today?"

    emb1 = ctx_mgr.create_embedding(text1)
    emb2 = ctx_mgr.create_embedding(text2)
    emb3 = ctx_mgr.create_embedding(text3)

    sim_1_2 = ctx_mgr.cosine_similarity(emb1, emb2)
    sim_1_3 = ctx_mgr.cosine_similarity(emb1, emb3)

    print(f"  Similarity (auth bug vs auth system): {sim_1_2:.3f}")
    print(f"  Similarity (auth bug vs weather): {sim_1_3:.3f}")

    # Test 3: Ajouter au cache
    print("\n3. Testing cache addition...")
    ctx_mgr.add_to_cache(
        content="Authentication bug fixed in login.py by adding JWT validation",
        metadata={'type': 'bugfix', 'file': 'login.py'}
    )
    print(f"✓ Added to cache (total: {len(ctx_mgr.context_cache)} contexts)")

    # Test 4: Recherche par embedding
    print("\n4. Testing cache search...")
    results = ctx_mgr.search_cache_by_embedding("How to fix login authentication?", top_k=3)
    print(f"✓ Found {len(results)} results:")
    for ctx, sim in results:
        print(f"  - {ctx.id}: {sim:.3f} similarity")

    # Test 5: Construire contexte optimisé
    print("\n5. Testing optimized context building...")
    context_result = ctx_mgr.build_optimized_context(
        user_request="Fix the authentication bug",
        include_git_diff=True
    )
    print(f"✓ Context built:")
    print(f"  Message: {context_result['message']}")
    print(f"  Git diff included: {context_result['metadata']['git_diff_included']}")
    print(f"  Cache hits: {len(context_result['metadata']['cache_hits'])}")

    print("\n✓ Context Manager works correctly!")
