"""
Département d'INTELLIGENCE

Rôle: Collecte et contextualise données web dynamiques

Agents:
- XPathSourceRegistry (EXÉCUTANT) - Gère sources web + XPath
- StealthWebCrawler (EXÉCUTANT) - Scrape web indétectable (TODO)
- DynamicContextManager (EXPERT) - Optimise données pour agents (TODO)
- ContextEnrichmentAgent (EXPERT) - Enrichit prompts entre agents (TODO)

Workflow:
1. Humain ajoute URL + XPath manuellement
2. Validation automatique des XPath
3. Scraping périodique des données
4. Contextualisation intelligente
5. Enrichissement des prompts inter-agents
"""

from cortex.departments.intelligence.xpath_source_registry import (
    XPathSourceRegistry,
    XPathSource
)

__all__ = [
    'XPathSourceRegistry',
    'XPathSource'
]
