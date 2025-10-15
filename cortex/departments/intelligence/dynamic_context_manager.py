"""
Dynamic Context Manager - Optimise données scrapées pour agents

Responsabilités:
- Transforme données brutes → contexte optimisé pour agents
- Résume données si trop volumineuses
- Catégorise automatiquement
- Extrait insights et tendances
- Score de pertinence par rapport à requête
- Gère fraîcheur et confiance des données
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import json
import re

from cortex.departments.intelligence.stealth_web_crawler import ScrapedData


@dataclass
class OptimizedContext:
    """Contexte optimisé pour agents"""
    context_id: str
    source_name: str
    summary: str  # Résumé concis (300 chars max)
    key_items: List[str]  # Top 5-10 items
    insights: List[str]  # Tendances/patterns détectés
    categories: Dict[str, List[str]]  # Catégorisation automatique

    scraped_at: datetime
    freshness_score: float  # 0-1 (1 = très frais)
    confidence_score: float  # 0-1 (1 = haute confiance)
    relevance_score: float  # 0-1 (calculé par rapport à query)

    metadata: Dict[str, Any]

    def to_prompt_context(self, include_metadata: bool = False) -> str:
        """
        Transforme en contexte injecté dans prompt

        Returns:
            String formaté pour injection dans prompt
        """
        age = datetime.now() - self.scraped_at
        age_str = self._format_age(age)

        context = f"""[DYNAMIC CONTEXT - {self.source_name}]
Scraped: {age_str} ago
Freshness: {self.freshness_score:.0%} | Confidence: {self.confidence_score:.0%}

{self.summary}

Key Items:
"""

        for i, item in enumerate(self.key_items[:10], 1):
            context += f"{i}. {item}\n"

        if self.insights:
            context += f"\nInsights:\n"
            for insight in self.insights:
                context += f"- {insight}\n"

        if self.categories and len(self.categories) > 1:
            context += f"\nCategories:\n"
            for category, items in list(self.categories.items())[:3]:
                context += f"- {category}: {len(items)} items\n"

        if include_metadata:
            context += f"\nMetadata:\n"
            context += f"- Total items: {self.metadata.get('total_items', 0)}\n"
            context += f"- Source: {self.metadata.get('url', 'N/A')}\n"

        return context.strip()

    def _format_age(self, age: timedelta) -> str:
        """Formate âge de manière lisible"""
        if age.total_seconds() < 3600:
            minutes = int(age.total_seconds() / 60)
            return f"{minutes} min"
        elif age.total_seconds() < 86400:
            hours = int(age.total_seconds() / 3600)
            return f"{hours}h"
        else:
            days = age.days
            return f"{days}d"


class DynamicContextManager:
    """
    Gère transformation données scrapées → contextes optimisés

    Stratégies:
    1. Résumé automatique si > 20 items
    2. Catégorisation par similarité de mots-clés
    3. Extraction d'insights (patterns, tendances)
    4. Scoring de pertinence vs query
    5. Calcul de freshness basé sur refresh_interval
    """

    def __init__(self, storage_dir: str = "cortex/data/scraped_data"):
        self.storage_dir = Path(storage_dir)

        # Cache de contextes optimisés
        self.context_cache: Dict[str, OptimizedContext] = {}

    def optimize_scraped_data(
        self,
        scraped: ScrapedData,
        query: Optional[str] = None
    ) -> OptimizedContext:
        """
        Optimise données scrapées pour agents

        Args:
            scraped: Données brutes scrapées
            query: Requête optionnelle pour scoring de pertinence

        Returns:
            OptimizedContext prêt pour injection
        """
        # 1. Résumé
        summary = self._generate_summary(scraped)

        # 2. Top items (max 10)
        key_items = self._extract_key_items(scraped.data)

        # 3. Insights
        insights = self._extract_insights(scraped.data)

        # 4. Catégorisation
        categories = self._categorize_items(scraped.data)

        # 5. Freshness score
        freshness = self._calculate_freshness(scraped.scraped_at)

        # 6. Confidence score
        confidence = self._calculate_confidence(scraped)

        # 7. Relevance score (si query fournie)
        relevance = self._calculate_relevance(scraped.data, query) if query else 0.8

        context_id = f"ctx_{scraped.scrape_id}"

        optimized = OptimizedContext(
            context_id=context_id,
            source_name=scraped.source_name,
            summary=summary,
            key_items=key_items,
            insights=insights,
            categories=categories,
            scraped_at=scraped.scraped_at,
            freshness_score=freshness,
            confidence_score=confidence,
            relevance_score=relevance,
            metadata={
                "total_items": len(scraped.data),
                "url": scraped.url,
                "xpath": scraped.xpath_used,
                "validation_success": scraped.validation_before_scrape.success,
                "elements_found": scraped.validation_before_scrape.elements_found
            }
        )

        # Cache
        self.context_cache[context_id] = optimized

        return optimized

    def _generate_summary(self, scraped: ScrapedData) -> str:
        """
        Génère résumé concis (300 chars max)

        Args:
            scraped: Données scrapées

        Returns:
            Résumé concis
        """
        total = len(scraped.data)
        source = scraped.source_name

        # Extraire mots-clés communs
        keywords = self._extract_common_keywords(scraped.data)
        keywords_str = ", ".join(keywords[:5])

        summary = f"{source} - {total} items scraped. "

        if keywords:
            summary += f"Common themes: {keywords_str}. "

        # Ajouter sample si peu d'items
        if total <= 3:
            sample = " | ".join(scraped.data[:3])
            summary += f"Items: {sample}"
        else:
            summary += f"Top items include: {scraped.data[0][:50]}..."

        # Truncate à 300 chars
        if len(summary) > 300:
            summary = summary[:297] + "..."

        return summary

    def _extract_key_items(self, data: List[str], max_items: int = 10) -> List[str]:
        """
        Extrait top items (max 10)

        Args:
            data: Liste de données brutes
            max_items: Nombre max d'items

        Returns:
            Top items
        """
        # Nettoyer et limiter
        cleaned = []
        for item in data[:max_items]:
            # Strip whitespace
            item = item.strip()

            # Skip si vide
            if not item:
                continue

            # Truncate si trop long
            if len(item) > 100:
                item = item[:97] + "..."

            cleaned.append(item)

        return cleaned

    def _extract_insights(self, data: List[str]) -> List[str]:
        """
        Extrait insights/patterns des données

        Args:
            data: Données brutes

        Returns:
            Liste d'insights
        """
        insights = []

        # Insight 1: Volume
        if len(data) > 50:
            insights.append(f"High activity: {len(data)} items detected")

        # Insight 2: Mots-clés communs
        keywords = self._extract_common_keywords(data)
        if keywords:
            top_keyword = keywords[0]
            insights.append(f"Trending topic: '{top_keyword}' appears frequently")

        # Insight 3: Patterns dans les données
        # Détecter si beaucoup de liens GitHub
        github_count = sum(1 for item in data if "github" in item.lower() or "/" in item)
        if github_count > len(data) * 0.5:
            insights.append(f"Focus on code repositories ({github_count}/{len(data)} items)")

        # Détecter si URLs
        url_count = sum(1 for item in data if item.startswith("http"))
        if url_count > len(data) * 0.7:
            insights.append(f"Mostly URLs ({url_count}/{len(data)} items)")

        return insights[:5]  # Max 5 insights

    def _categorize_items(self, data: List[str]) -> Dict[str, List[str]]:
        """
        Catégorise items par similarité

        Args:
            data: Données brutes

        Returns:
            Dict category → items
        """
        categories: Dict[str, List[str]] = {}

        # Catégories basées sur mots-clés
        category_keywords = {
            "web_frameworks": ["flask", "django", "fastapi", "react", "vue", "angular"],
            "data_science": ["pandas", "numpy", "scikit", "tensorflow", "pytorch", "jupyter"],
            "devops": ["docker", "kubernetes", "k8s", "terraform", "ansible", "ci/cd"],
            "ai_ml": ["ai", "ml", "llm", "gpt", "model", "neural", "agent"],
            "security": ["security", "auth", "crypto", "vulnerability", "exploit"],
            "backend": ["api", "server", "database", "postgres", "mongo", "redis"],
            "other": []
        }

        # Classifier chaque item
        for item in data:
            item_lower = item.lower()
            categorized = False

            for category, keywords in category_keywords.items():
                if category == "other":
                    continue

                # Check si item contient keyword
                if any(kw in item_lower for kw in keywords):
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(item)
                    categorized = True
                    break

            # Si non catégorisé, mettre dans "other"
            if not categorized:
                if "other" not in categories:
                    categories["other"] = []
                categories["other"].append(item)

        # Retirer "other" si trop dominant
        if "other" in categories and len(categories["other"]) == len(data):
            del categories["other"]

        # Limiter items par catégorie
        for category in categories:
            categories[category] = categories[category][:10]

        return categories

    def _extract_common_keywords(self, data: List[str]) -> List[str]:
        """
        Extrait mots-clés communs

        Args:
            data: Données brutes

        Returns:
            Liste de mots-clés triés par fréquence
        """
        # Compter mots
        word_counts: Dict[str, int] = {}

        for item in data:
            # Extraire mots (alphanumeric seulement)
            words = re.findall(r'\b[a-zA-Z]{3,}\b', item.lower())

            for word in words:
                # Skip stop words
                if word in ["the", "and", "for", "with", "from", "that", "this", "have", "are", "was"]:
                    continue

                word_counts[word] = word_counts.get(word, 0) + 1

        # Trier par fréquence
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

        # Retourner top 10
        return [word for word, count in sorted_words[:10]]

    def _calculate_freshness(self, scraped_at: datetime) -> float:
        """
        Calcule freshness score (0-1)

        Plus c'est récent, plus le score est élevé

        Args:
            scraped_at: Timestamp du scraping

        Returns:
            Score 0-1
        """
        age = datetime.now() - scraped_at
        hours_old = age.total_seconds() / 3600

        # Freshness decay
        # 0-1h: 1.0
        # 1-6h: 0.9
        # 6-24h: 0.7
        # 24-72h: 0.5
        # 72h+: 0.3

        if hours_old < 1:
            return 1.0
        elif hours_old < 6:
            return 0.9
        elif hours_old < 24:
            return 0.7
        elif hours_old < 72:
            return 0.5
        else:
            return 0.3

    def _calculate_confidence(self, scraped: ScrapedData) -> float:
        """
        Calcule confidence score basé sur validation

        Args:
            scraped: Données scrapées

        Returns:
            Score 0-1
        """
        base_confidence = 0.8

        # Boost si validation réussie
        if scraped.validation_before_scrape.success:
            base_confidence += 0.1

        # Boost si beaucoup d'éléments trouvés
        elements_found = scraped.validation_before_scrape.elements_found
        if elements_found >= 20:
            base_confidence += 0.1

        # Cap à 1.0
        return min(base_confidence, 1.0)

    def _calculate_relevance(self, data: List[str], query: Optional[str]) -> float:
        """
        Calcule relevance score par rapport à query

        Args:
            data: Données scrapées
            query: Requête utilisateur

        Returns:
            Score 0-1
        """
        if not query:
            return 0.8  # Default relevance

        query_lower = query.lower()
        query_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', query_lower))

        # Compter combien d'items contiennent query words
        matching_items = 0

        for item in data:
            item_lower = item.lower()

            # Check si item contient au moins un mot de la query
            if any(word in item_lower for word in query_words):
                matching_items += 1

        # Score = ratio d'items matchants
        if len(data) == 0:
            return 0.5

        relevance = matching_items / len(data)

        # Boost si query exacte trouvée
        if any(query_lower in item.lower() for item in data):
            relevance = min(relevance + 0.2, 1.0)

        return relevance

    def get_context_by_id(self, context_id: str) -> Optional[OptimizedContext]:
        """
        Récupère contexte optimisé par ID

        Args:
            context_id: ID du contexte

        Returns:
            OptimizedContext ou None
        """
        return self.context_cache.get(context_id)

    def get_latest_context_for_source(
        self,
        source_id: str,
        category: str,
        query: Optional[str] = None
    ) -> Optional[OptimizedContext]:
        """
        Récupère dernier contexte optimisé pour une source

        Args:
            source_id: ID de la source
            category: Catégorie
            query: Requête optionnelle pour relevance scoring

        Returns:
            OptimizedContext ou None
        """
        # Charger dernier scrape
        source_dir = self.storage_dir / category / source_id

        if not source_dir.exists():
            return None

        # Trouver fichier le plus récent
        files = sorted(source_dir.glob("*.json"), reverse=True)

        if not files:
            return None

        # Charger et optimiser
        with open(files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Reconstruire ScrapedData
        from cortex.departments.intelligence.stealth_web_crawler import ValidationResult

        val_data = data["validation_before_scrape"]
        validation = ValidationResult(
            success=val_data["success"],
            elements_found=val_data["elements_found"],
            sample_data=val_data["sample_data"]
        )

        scraped = ScrapedData(
            scrape_id=data["scrape_id"],
            source_id=data["source_id"],
            source_name=data["source_name"],
            url=data["url"],
            xpath_used=data["xpath_used"],
            scraped_at=datetime.fromisoformat(data["scraped_at"]),
            validation_before_scrape=validation,
            data=data["data"],
            metadata=data["metadata"]
        )

        # Optimiser
        return self.optimize_scraped_data(scraped, query)

    def search_contexts(
        self,
        keywords: List[str],
        min_relevance: float = 0.5
    ) -> List[OptimizedContext]:
        """
        Recherche contextes par mots-clés

        Args:
            keywords: Mots-clés à rechercher
            min_relevance: Relevance minimale

        Returns:
            Contextes triés par relevance
        """
        results = []

        for context in self.context_cache.values():
            # Calculer relevance vs keywords
            query = " ".join(keywords)
            relevance = self._calculate_relevance(context.key_items, query)

            if relevance >= min_relevance:
                # Update relevance score
                context.relevance_score = relevance
                results.append(context)

        # Trier par relevance
        results.sort(key=lambda c: c.relevance_score, reverse=True)

        return results


def create_dynamic_context_manager(storage_dir: str = "cortex/data/scraped_data") -> DynamicContextManager:
    """Factory function"""
    return DynamicContextManager(storage_dir)


# Test
if __name__ == "__main__":
    print("Testing Dynamic Context Manager...")

    from cortex.departments.intelligence.xpath_source_registry import XPathSourceRegistry
    from cortex.departments.intelligence.stealth_web_crawler import StealthWebCrawler

    # Créer registry et crawler
    registry = XPathSourceRegistry("cortex/data/test_web_sources_contextmgr.json")
    crawler = StealthWebCrawler("cortex/data/test_scraped_data_contextmgr")

    # Ajouter source
    source = registry.add_source(
        name="HackerNews Frontpage",
        url="https://news.ycombinator.com",
        xpath="//span[@class='titleline']/a/text()",
        description="Top stories on HackerNews",
        category="tech_news",
        refresh_interval_hours=6
    )

    # Scrape
    print("\n1. Scraping data...")
    scraped = crawler.scrape(source)

    # Optimiser
    print("\n2. Optimizing context...")
    manager = DynamicContextManager("cortex/data/test_scraped_data_contextmgr")

    optimized = manager.optimize_scraped_data(scraped, query="python trends")

    print(f"✓ Context optimized:")
    print(f"  Context ID: {optimized.context_id}")
    print(f"  Summary: {optimized.summary}")
    print(f"  Key items: {len(optimized.key_items)}")
    print(f"  Insights: {optimized.insights}")
    print(f"  Categories: {list(optimized.categories.keys())}")
    print(f"  Freshness: {optimized.freshness_score:.0%}")
    print(f"  Confidence: {optimized.confidence_score:.0%}")
    print(f"  Relevance: {optimized.relevance_score:.0%}")

    # Test 3: Generate prompt context
    print("\n3. Generating prompt context...")
    prompt_context = optimized.to_prompt_context(include_metadata=True)
    print(f"✓ Prompt context ({len(prompt_context)} chars):")
    print(prompt_context)

    # Test 4: Get latest context
    print("\n4. Getting latest context...")
    latest = manager.get_latest_context_for_source(
        source.id,
        source.category,
        query="AI and machine learning"
    )

    if latest:
        print(f"✓ Latest context retrieved:")
        print(f"  Scraped: {latest.scraped_at}")
        print(f"  Relevance to 'AI': {latest.relevance_score:.0%}")

    print("\n✓ Dynamic Context Manager works correctly!")
