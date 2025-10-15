"""
Cache Manager - Système de cache multi-niveaux
Objectif: Économiser 80%+ des coûts LLM via réutilisation intelligente

Niveaux:
- L1: Mémoire/Redis (exact match) - 100% économies
- L2: Vector DB (semantic match) - 100% économies
- L3: Templates (pattern match) - 70-90% économies
"""

import hashlib
import json
import time
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Imports optionnels
try:
    import diskcache
except ImportError:
    diskcache = None

try:
    import redis
except ImportError:
    redis = None

from cortex.core.config_loader import get_config


class CacheLevel(Enum):
    """Niveaux de cache"""
    L1_EXACT = "l1_exact"           # Match exact
    L2_SEMANTIC = "l2_semantic"     # Match sémantique
    L3_TEMPLATE = "l3_template"     # Match de pattern
    MISS = "miss"                    # Pas de cache


@dataclass
class CacheResult:
    """Résultat d'une recherche dans le cache"""
    hit: bool
    level: CacheLevel
    content: Optional[str]
    tokens_saved: int
    cost_saved: float
    similarity: float  # 0-1


class CacheManager:
    """
    Gestionnaire de cache multi-niveaux
    Maximise les économies en cherchant du plus rapide au plus lent
    """

    def __init__(self):
        self.config = get_config()

        # Configuration du cache
        self.cache_config = self.config.get("optimization.cache", {})

        # Statistiques
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "misses": 0,
            "total_tokens_saved": 0,
            "total_cost_saved": 0.0
        }

        # Initialiser les backends
        self._init_l1_cache()
        self._init_l2_cache()
        self._init_l3_cache()

    def _init_l1_cache(self):
        """Initialise le cache L1 (mémoire/Redis)"""
        l1_config = self.cache_config.get("l1_memory", {})

        if not l1_config.get("enabled", True):
            self.l1_cache = None
            return

        # Essayer Redis d'abord
        redis_url = self.config.get("databases.cache.redis_url")
        if redis and redis_url:
            try:
                self.l1_cache = redis.from_url(
                    redis_url,
                    decode_responses=True
                )
                self.l1_cache.ping()  # Test connexion
                self.l1_backend = "redis"
                return
            except:
                pass  # Fallback à diskcache

        # Fallback: diskcache (file-based)
        if diskcache:
            cache_path = self.config.get("databases.cache.path", "data/cache")
            self.l1_cache = diskcache.Cache(cache_path)
            self.l1_backend = "disk"
        else:
            # Fallback ultime: dict en mémoire
            self.l1_cache = {}
            self.l1_backend = "memory"

    def _init_l2_cache(self):
        """Initialise le cache L2 (sémantique)"""
        l2_config = self.cache_config.get("l2_semantic", {})

        if not l2_config.get("enabled", True):
            self.l2_cache = None
            return

        # TODO: Implémenter avec ChromaDB
        # Pour l'instant: désactivé
        self.l2_cache = None

    def _init_l3_cache(self):
        """Initialise le cache L3 (templates)"""
        l3_config = self.cache_config.get("l3_templates", {})

        if not l3_config.get("enabled", True):
            self.l3_cache = None
            return

        # Template cache: dict simple pour patterns
        self.l3_cache = {}

    def get(
        self,
        messages: list,
        model_tier: str,
        max_tokens: int = 2048
    ) -> CacheResult:
        """
        Recherche dans tous les niveaux de cache

        Args:
            messages: Messages de la requête
            model_tier: Tier du modèle (pour calculer économies)
            max_tokens: Tokens max (pour estimer économies)

        Returns:
            CacheResult avec hit/miss et économies
        """
        # Générer une clé de cache
        cache_key = self._generate_key(messages, model_tier)

        # L1: Exact match (le plus rapide)
        result = self._check_l1(cache_key)
        if result.hit:
            self.stats["l1_hits"] += 1
            self.stats["total_tokens_saved"] += result.tokens_saved
            self.stats["total_cost_saved"] += result.cost_saved
            return result

        # L2: Semantic match (si disponible)
        if self.l2_cache:
            result = self._check_l2(messages, model_tier)
            if result.hit:
                self.stats["l2_hits"] += 1
                self.stats["total_tokens_saved"] += result.tokens_saved
                self.stats["total_cost_saved"] += result.cost_saved
                return result

        # L3: Template match (patterns)
        if self.l3_cache:
            result = self._check_l3(messages, model_tier)
            if result.hit:
                self.stats["l3_hits"] += 1
                self.stats["total_tokens_saved"] += result.tokens_saved
                self.stats["total_cost_saved"] += result.cost_saved
                return result

        # Cache miss
        self.stats["misses"] += 1
        return CacheResult(
            hit=False,
            level=CacheLevel.MISS,
            content=None,
            tokens_saved=0,
            cost_saved=0.0,
            similarity=0.0
        )

    def set(
        self,
        messages: list,
        model_tier: str,
        response_content: str,
        tokens_used: int,
        cost: float
    ):
        """
        Sauvegarde dans tous les caches appropriés

        Args:
            messages: Messages de la requête
            model_tier: Tier du modèle
            response_content: Réponse du LLM
            tokens_used: Tokens utilisés
            cost: Coût de l'appel
        """
        cache_key = self._generate_key(messages, model_tier)

        # Préparer la valeur à cacher
        cache_value = {
            "content": response_content,
            "tokens": tokens_used,
            "cost": cost,
            "timestamp": time.time(),
            "model_tier": model_tier
        }

        # L1: Toujours sauvegarder
        self._set_l1(cache_key, cache_value)

        # L2: Sauvegarder pour recherche sémantique (si disponible)
        if self.l2_cache:
            self._set_l2(messages, cache_value)

        # L3: Extraire et sauvegarder le pattern (si pattern détecté)
        if self.l3_cache:
            self._set_l3(messages, cache_value)

    def _generate_key(self, messages: list, model_tier: str) -> str:
        """Génère une clé de cache unique"""
        # Créer une représentation stable des messages
        messages_str = json.dumps(messages, sort_keys=True)
        key_str = f"{messages_str}:{model_tier}"

        # Hash pour clé courte
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _check_l1(self, cache_key: str) -> CacheResult:
        """Vérifie le cache L1 (exact match)"""
        if self.l1_cache is None:
            return CacheResult(False, CacheLevel.MISS, None, 0, 0.0, 0.0)

        try:
            if self.l1_backend == "redis":
                value_json = self.l1_cache.get(cache_key)
                if value_json:
                    value = json.loads(value_json)
                else:
                    return CacheResult(False, CacheLevel.MISS, None, 0, 0.0, 0.0)

            elif self.l1_backend == "disk":
                value = self.l1_cache.get(cache_key)
                if value is None:
                    return CacheResult(False, CacheLevel.MISS, None, 0, 0.0, 0.0)

            else:  # memory
                value = self.l1_cache.get(cache_key)
                if value is None:
                    return CacheResult(False, CacheLevel.MISS, None, 0, 0.0, 0.0)

            # Vérifier TTL
            ttl_minutes = self.cache_config.get("l1_memory", {}).get("ttl_minutes", 60)
            age_minutes = (time.time() - value["timestamp"]) / 60

            if age_minutes > ttl_minutes:
                # Expiré, retirer du cache
                self._delete_l1(cache_key)
                return CacheResult(False, CacheLevel.MISS, None, 0, 0.0, 0.0)

            # Cache hit!
            return CacheResult(
                hit=True,
                level=CacheLevel.L1_EXACT,
                content=value["content"],
                tokens_saved=value["tokens"],
                cost_saved=value["cost"],
                similarity=1.0  # Exact match
            )

        except Exception as e:
            # En cas d'erreur, retourner miss
            return CacheResult(False, CacheLevel.MISS, None, 0, 0.0, 0.0)

    def _set_l1(self, cache_key: str, value: Dict):
        """Sauvegarde dans le cache L1"""
        if self.l1_cache is None:
            return

        try:
            if self.l1_backend == "redis":
                ttl_seconds = self.cache_config.get("l1_memory", {}).get("ttl_minutes", 60) * 60
                self.l1_cache.setex(
                    cache_key,
                    ttl_seconds,
                    json.dumps(value)
                )

            elif self.l1_backend == "disk":
                ttl_seconds = self.cache_config.get("l1_memory", {}).get("ttl_minutes", 60) * 60
                self.l1_cache.set(cache_key, value, expire=ttl_seconds)

            else:  # memory
                self.l1_cache[cache_key] = value

        except Exception as e:
            # Log error for debugging
            print(f"Cache set error: {e}")
            import traceback
            traceback.print_exc()

    def _delete_l1(self, cache_key: str):
        """Supprime du cache L1"""
        if self.l1_cache is None:
            return

        try:
            if self.l1_backend == "redis":
                self.l1_cache.delete(cache_key)
            elif self.l1_backend == "disk":
                self.l1_cache.delete(cache_key)
            else:  # memory
                self.l1_cache.pop(cache_key, None)
        except:
            pass

    def _check_l2(self, messages: list, model_tier: str) -> CacheResult:
        """Vérifie le cache L2 (semantic match)"""
        # TODO: Implémenter avec ChromaDB
        return CacheResult(False, CacheLevel.MISS, None, 0, 0.0, 0.0)

    def _set_l2(self, messages: list, value: Dict):
        """Sauvegarde dans le cache L2"""
        # TODO: Implémenter avec ChromaDB
        pass

    def _check_l3(self, messages: list, model_tier: str) -> CacheResult:
        """Vérifie le cache L3 (template match)"""
        # TODO: Implémenter pattern matching
        return CacheResult(False, CacheLevel.MISS, None, 0, 0.0, 0.0)

    def _set_l3(self, messages: list, value: Dict):
        """Sauvegarde dans le cache L3"""
        # TODO: Implémenter template extraction
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques du cache"""
        total_requests = sum([
            self.stats["l1_hits"],
            self.stats["l2_hits"],
            self.stats["l3_hits"],
            self.stats["misses"]
        ])

        hit_rate = 0.0
        if total_requests > 0:
            total_hits = self.stats["l1_hits"] + self.stats["l2_hits"] + self.stats["l3_hits"]
            hit_rate = total_hits / total_requests

        return {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "backend": self.l1_backend if self.l1_cache is not None else "none"
        }

    def clear(self):
        """Vide tous les caches"""
        if self.l1_cache is not None:
            if self.l1_backend == "redis":
                self.l1_cache.flushdb()
            elif self.l1_backend == "disk":
                self.l1_cache.clear()
            else:  # memory
                self.l1_cache.clear()

        if self.l2_cache:
            # TODO: Clear L2
            pass

        if self.l3_cache:
            self.l3_cache.clear()


# Test du cache
if __name__ == "__main__":
    cache = CacheManager()

    print("Cache initialized")
    print(f"Backend: {cache.l1_backend}")

    # Test write
    messages = [{"role": "user", "content": "Hello, world!"}]
    cache.set(messages, "nano", "Hi there!", 10, 0.00001)
    print("\nCached response for 'Hello, world!'")

    # Test read (hit)
    result = cache.get(messages, "nano")
    print(f"\nCache check:")
    print(f"  Hit: {result.hit}")
    print(f"  Level: {result.level.value if result.hit else 'miss'}")
    print(f"  Content: {result.content}")
    print(f"  Tokens saved: {result.tokens_saved}")
    print(f"  Cost saved: ${result.cost_saved:.6f}")

    # Test read (miss)
    messages2 = [{"role": "user", "content": "Different message"}]
    result2 = cache.get(messages2, "nano")
    print(f"\nCache check (different message):")
    print(f"  Hit: {result2.hit}")

    # Stats
    print(f"\nCache stats:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
