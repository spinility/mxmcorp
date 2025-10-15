"""
Département d'INTELLIGENCE

Rôle: Collecte et contextualise données web dynamiques

Agents:
- XPathSourceRegistry (EXÉCUTANT) - Gère sources web + XPath
- StealthWebCrawler (EXÉCUTANT) - Scrape web indétectable
- DynamicContextManager (EXPERT) - Optimise données pour agents
- ContextEnrichmentAgent (EXPERT) - Enrichit prompts entre agents

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
from cortex.departments.intelligence.stealth_web_crawler import (
    StealthWebCrawler,
    ScrapedData,
    ValidationResult
)
from cortex.departments.intelligence.dynamic_context_manager import (
    DynamicContextManager,
    OptimizedContext
)
from cortex.departments.intelligence.context_enrichment_agent import (
    ContextEnrichmentAgent,
    AgentMessage,
    ContextRequest
)

__all__ = [
    'XPathSourceRegistry',
    'XPathSource',
    'StealthWebCrawler',
    'ScrapedData',
    'ValidationResult',
    'DynamicContextManager',
    'OptimizedContext',
    'ContextEnrichmentAgent',
    'AgentMessage',
    'ContextRequest'
]
