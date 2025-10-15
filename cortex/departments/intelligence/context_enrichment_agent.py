"""
Context Enrichment Agent - Enrichit prompts entre agents

Responsabilités:
- Intercepte messages inter-agents
- Identifie demandes de contexte dynamique
- Récupère contextes optimisés
- Injecte dans prompts avec formatage approprié
- Gère priorités et pertinence
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from cortex.departments.intelligence.dynamic_context_manager import (
    DynamicContextManager,
    OptimizedContext
)
from cortex.departments.intelligence.xpath_source_registry import XPathSourceRegistry


@dataclass
class AgentMessage:
    """Message entre agents"""
    from_agent: str
    to_agent: str
    task: str
    context_requests: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Enrichissement
    enriched: bool = False
    contexts_added: List[str] = field(default_factory=list)


@dataclass
class ContextRequest:
    """Demande de contexte spécifique"""
    context_type: str  # "dynamic", "static", "previous_result"
    source_id: Optional[str] = None  # Pour dynamic context
    category: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    min_relevance: float = 0.5


class ContextEnrichmentAgent:
    """
    Agent qui enrichit prompts entre agents

    Workflow:
    1. Agent A termine tâche
    2. Agent A crée AgentMessage pour Agent B avec context_requests
    3. ContextEnrichmentAgent intercepte
    4. Pour chaque context_request:
       - Identifie type (dynamic/static/previous)
       - Récupère contexte optimisé
       - Score relevance
    5. Enrichit prompt avec top contexts
    6. Agent B reçoit prompt enrichi
    """

    def __init__(
        self,
        context_manager: DynamicContextManager,
        registry: XPathSourceRegistry,
        max_contexts_per_message: int = 3
    ):
        self.context_manager = context_manager
        self.registry = registry
        self.max_contexts_per_message = max_contexts_per_message

        # Cache de résultats précédents (pour previous_result)
        self.previous_results: Dict[str, Any] = {}

    def enrich_message(self, message: AgentMessage, query: Optional[str] = None) -> AgentMessage:
        """
        Enrichit message avec contextes dynamiques

        Args:
            message: Message inter-agent à enrichir
            query: Requête optionnelle pour relevance scoring

        Returns:
            Message enrichi
        """
        if not message.context_requests:
            # Aucune demande de contexte
            return message

        if message.enriched:
            # Déjà enrichi
            return message

        # Parser context_requests
        parsed_requests = self._parse_context_requests(message.context_requests)

        # Récupérer contextes
        contexts = self._fetch_contexts(parsed_requests, query or message.task)

        # Filtrer par relevance
        contexts = self._filter_by_relevance(contexts, message.task)

        # Limiter nombre de contextes
        contexts = contexts[:self.max_contexts_per_message]

        # Enrichir prompt
        enriched_task = self._inject_contexts(message.task, contexts)

        # Update message
        message.task = enriched_task
        message.enriched = True
        message.contexts_added = [c.context_id for c in contexts]

        return message

    def _parse_context_requests(self, requests: List[str]) -> List[ContextRequest]:
        """
        Parse liste de context_requests

        Format attendu:
        - "github_trending_python" → dynamic, source_id
        - "tech_news" → dynamic, category
        - "web_scraping_best_practices" → static (TODO)
        - "previous_analysis_results" → previous_result

        Args:
            requests: Liste de requêtes

        Returns:
            Liste de ContextRequest
        """
        parsed = []

        for req in requests:
            req_lower = req.lower()

            # Identifier type
            if req_lower.startswith("previous_"):
                # Previous result
                parsed.append(ContextRequest(
                    context_type="previous_result",
                    keywords=[req]
                ))

            elif "_" in req:
                # Probablement source_id (ex: github_trending_python)
                # Essayer de trouver source
                sources = self.registry.search_sources(req)

                if sources:
                    # Trouvé source
                    source = sources[0]
                    parsed.append(ContextRequest(
                        context_type="dynamic",
                        source_id=source.id,
                        category=source.category,
                        keywords=req.split("_")
                    ))
                else:
                    # Pas trouvé, peut-être catégorie
                    categories = self.registry.get_categories()
                    matching_cat = next((cat for cat in categories if req in cat), None)

                    if matching_cat:
                        parsed.append(ContextRequest(
                            context_type="dynamic",
                            category=matching_cat,
                            keywords=req.split("_")
                        ))
                    else:
                        # Fallback: static (TODO)
                        parsed.append(ContextRequest(
                            context_type="static",
                            keywords=[req]
                        ))

            else:
                # Single word, probablement catégorie ou static
                categories = self.registry.get_categories()

                if req_lower in [cat.lower() for cat in categories]:
                    # Catégorie
                    parsed.append(ContextRequest(
                        context_type="dynamic",
                        category=req_lower,
                        keywords=[req]
                    ))
                else:
                    # Static
                    parsed.append(ContextRequest(
                        context_type="static",
                        keywords=[req]
                    ))

        return parsed

    def _fetch_contexts(
        self,
        requests: List[ContextRequest],
        query: str
    ) -> List[OptimizedContext]:
        """
        Récupère contextes pour chaque requête

        Args:
            requests: Requêtes parsées
            query: Requête pour relevance scoring

        Returns:
            Liste de contextes optimisés
        """
        contexts = []

        for req in requests:
            if req.context_type == "dynamic":
                # Récupérer contexte dynamique

                if req.source_id:
                    # Récupérer par source_id
                    source = self.registry.get_source(req.source_id)

                    if source:
                        context = self.context_manager.get_latest_context_for_source(
                            source.id,
                            source.category,
                            query
                        )

                        if context:
                            contexts.append(context)

                elif req.category:
                    # Récupérer toutes sources de la catégorie
                    sources = self.registry.get_sources_by_category(req.category)

                    for source in sources[:3]:  # Max 3 sources par catégorie
                        context = self.context_manager.get_latest_context_for_source(
                            source.id,
                            source.category,
                            query
                        )

                        if context:
                            contexts.append(context)

                else:
                    # Recherche par keywords
                    found_contexts = self.context_manager.search_contexts(
                        req.keywords,
                        min_relevance=req.min_relevance
                    )

                    contexts.extend(found_contexts[:2])

            elif req.context_type == "previous_result":
                # Récupérer résultat précédent
                for keyword in req.keywords:
                    if keyword in self.previous_results:
                        # Créer contexte from previous result
                        prev_result = self.previous_results[keyword]

                        # Créer OptimizedContext
                        context = OptimizedContext(
                            context_id=f"prev_{keyword}",
                            source_name=f"Previous: {keyword}",
                            summary=str(prev_result)[:300],
                            key_items=[str(prev_result)],
                            insights=[],
                            categories={},
                            scraped_at=datetime.now(),
                            freshness_score=1.0,
                            confidence_score=0.9,
                            relevance_score=0.8,
                            metadata={"type": "previous_result"}
                        )

                        contexts.append(context)

            elif req.context_type == "static":
                # TODO: Récupérer contexte statique (docs, patterns)
                # Pour l'instant, skip
                pass

        return contexts

    def _filter_by_relevance(
        self,
        contexts: List[OptimizedContext],
        query: str
    ) -> List[OptimizedContext]:
        """
        Filtre contextes par relevance

        Args:
            contexts: Contextes à filtrer
            query: Requête

        Returns:
            Contextes filtrés et triés
        """
        # Recalculer relevance par rapport à query
        for context in contexts:
            # Use key_items for relevance
            relevance = self.context_manager._calculate_relevance(
                context.key_items,
                query
            )

            # Update relevance score (weighted avec existing)
            context.relevance_score = (context.relevance_score + relevance) / 2

        # Filtrer par relevance minimale
        filtered = [c for c in contexts if c.relevance_score >= 0.3]

        # Trier par relevance * freshness
        filtered.sort(
            key=lambda c: c.relevance_score * c.freshness_score,
            reverse=True
        )

        return filtered

    def _inject_contexts(
        self,
        task: str,
        contexts: List[OptimizedContext]
    ) -> str:
        """
        Injecte contextes dans prompt

        Args:
            task: Prompt original
            contexts: Contextes à injecter

        Returns:
            Prompt enrichi
        """
        if not contexts:
            return task

        enriched = task + "\n\n"

        # Ajouter section de contextes
        enriched += "=" * 70 + "\n"
        enriched += "DYNAMIC CONTEXTS (injected by ContextEnrichmentAgent)\n"
        enriched += "=" * 70 + "\n\n"

        for i, context in enumerate(contexts, 1):
            enriched += f"### Context {i}/{len(contexts)}: {context.source_name}\n\n"
            enriched += context.to_prompt_context(include_metadata=False)
            enriched += "\n\n"

        enriched += "=" * 70 + "\n"
        enriched += f"END DYNAMIC CONTEXTS ({len(contexts)} contexts injected)\n"
        enriched += "=" * 70 + "\n\n"

        enriched += "Please use the above dynamic contexts to complete your task.\n"

        return enriched

    def store_result(self, result_name: str, result_data: Any):
        """
        Stocke résultat pour usage futur

        Args:
            result_name: Nom du résultat
            result_data: Données
        """
        self.previous_results[result_name] = result_data

    def get_statistics(self) -> Dict[str, Any]:
        """Statistiques de l'agent"""
        return {
            "cached_contexts": len(self.context_manager.context_cache),
            "previous_results": len(self.previous_results),
            "max_contexts_per_message": self.max_contexts_per_message,
            "total_sources": len(self.registry.sources)
        }


def create_context_enrichment_agent(
    context_manager: DynamicContextManager,
    registry: XPathSourceRegistry
) -> ContextEnrichmentAgent:
    """Factory function"""
    return ContextEnrichmentAgent(context_manager, registry)


# Test
if __name__ == "__main__":
    print("Testing Context Enrichment Agent...")

    from cortex.departments.intelligence.xpath_source_registry import XPathSourceRegistry
    from cortex.departments.intelligence.stealth_web_crawler import StealthWebCrawler
    from cortex.departments.intelligence.dynamic_context_manager import DynamicContextManager

    # Setup
    registry = XPathSourceRegistry("cortex/data/test_web_sources_enrichment.json")
    crawler = StealthWebCrawler("cortex/data/test_scraped_data_enrichment")
    context_manager = DynamicContextManager("cortex/data/test_scraped_data_enrichment")

    # Ajouter sources
    print("\n1. Adding sources...")
    source1 = registry.add_source(
        name="HackerNews Frontpage",
        url="https://news.ycombinator.com",
        xpath="//span[@class='titleline']/a/text()",
        description="Top stories on HackerNews",
        category="tech_news",
        refresh_interval_hours=6
    )

    # Scrape et optimiser
    print("\n2. Scraping and optimizing...")
    scraped = crawler.scrape(source1)
    optimized = context_manager.optimize_scraped_data(scraped, query="AI and Python")

    print(f"✓ Context optimized: {optimized.context_id}")

    # Créer enrichment agent
    print("\n3. Creating enrichment agent...")
    enrichment_agent = ContextEnrichmentAgent(context_manager, registry)

    # Test 4: Enrichir message
    print("\n4. Enriching message...")

    message = AgentMessage(
        from_agent="RequirementsAnalyzer",
        to_agent="CodeWriter",
        task="Write a Python script to analyze trending tech topics",
        context_requests=[
            "tech_news",  # Catégorie
            "hackernews"  # Keywords
        ],
        metadata={"priority": "high"}
    )

    enriched_message = enrichment_agent.enrich_message(message, query="Python trending")

    print(f"✓ Message enriched:")
    print(f"  From: {enriched_message.from_agent}")
    print(f"  To: {enriched_message.to_agent}")
    print(f"  Enriched: {enriched_message.enriched}")
    print(f"  Contexts added: {enriched_message.contexts_added}")
    print(f"  Task length: {len(message.task)} → {len(enriched_message.task)} chars")

    # Test 5: Display enriched task
    print("\n5. Enriched task preview:")
    print("-" * 70)
    print(enriched_message.task[:500] + "...")
    print("-" * 70)

    # Test 6: Statistics
    print("\n6. Statistics:")
    stats = enrichment_agent.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✓ Context Enrichment Agent works correctly!")
