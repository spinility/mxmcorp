# Phase 4.1 - Web Intelligence & Dynamic Context System

## Vue d'ensemble

Système permettant à Cortex de:
1. **Scraper automatiquement** des sources web via XPath
2. **Valider** que les XPath fonctionnent toujours
3. **Stocker** les données avec métadonnées complètes
4. **Contextualiser** les données dynamiques pour les agents
5. **Enrichir** les prompts entre agents avec contexte pertinent

## Architecture Complète

```
┌─────────────────────────────────────────────────────────────────┐
│                   Web Intelligence System                        │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼────┐      ┌──────▼──────┐     ┌──────▼──────┐
   │ XPath   │      │   Stealth   │     │  Dynamic    │
   │ Source  │──────│     Web     │────▶│  Context    │
   │ Registry│      │   Crawler   │     │  Manager    │
   └─────────┘      └─────────────┘     └──────┬──────┘
        │                   │                   │
        │                   │                   │
   Human adds         Validates XPath      Optimizes
   URL + XPath        Scrapes content      for agents
   manually           Returns data              │
                                                 │
                                          ┌──────▼──────┐
                                          │  Context    │
                                          │ Enrichment  │
                                          │   Agent     │
                                          └──────┬──────┘
                                                 │
                                          Enriches prompts
                                          between agents
```

## Composants Détaillés

### 1. XPathSource Registry

**Fichier**: `cortex/data/web_sources.json`

**Structure**:
```json
{
  "sources": [
    {
      "id": "src_001",
      "name": "GitHub Trending Python",
      "url": "https://github.com/trending/python",
      "xpath": "//article[@class='Box-row']//h2/a/@href",
      "description": "Top trending Python repos",
      "category": "tech_trends",
      "refresh_interval_hours": 24,
      "created_at": "2025-10-15T10:00:00",
      "last_validated": "2025-10-15T16:00:00",
      "validation_status": "success",
      "last_error": null,
      "enabled": true,
      "headers": {
        "User-Agent": "Mozilla/5.0...",
        "Accept-Language": "en-US"
      },
      "authentication": null
    }
  ]
}
```

**Gestion manuelle**:
```python
# Ajouter source
registry.add_source(
    name="GitHub Trending",
    url="https://github.com/trending/python",
    xpath="//article//h2/a/@href",
    category="tech_trends",
    refresh_interval_hours=24
)

# Modifier XPath
registry.update_xpath(
    source_id="src_001",
    new_xpath="//div[@class='repo-list']//a/@href"
)

# Valider manuellement
result = registry.validate_source("src_001")
# → Teste XPath, retourne success/failure
```

**Commande en langage naturel**:
```
User: "Cortex, valide tous les XPath des sources tech"
→ Agent trouve sources avec category="tech_trends"
→ Lance validation de chacune
→ Retourne rapport: "3/5 sources valides, 2 nécessitent update"
```

### 2. StealthWebCrawler

**Caractéristiques indétectables**:
```python
class StealthWebCrawler:
    """Crawler indétectable"""

    # Rotation User-Agents
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
        # ... pool de 50+ user agents
    ]

    # Délais randomisés
    def random_delay(self):
        time.sleep(random.uniform(2.0, 5.0))

    # Headers réalistes
    headers = {
        "Accept": "text/html,application/xhtml+xml...",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    # Session persistante (cookies)
    session = requests.Session()

    # Respect robots.txt
    def can_fetch(self, url):
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{url}/robots.txt")
        return rp.can_fetch("*", url)
```

**Validation XPath**:
```python
def validate_xpath(url: str, xpath: str) -> ValidationResult:
    """
    Valide qu'un XPath fonctionne toujours

    Returns:
        - success: bool
        - elements_found: int
        - sample_data: List[str]  # Premiers 3 résultats
        - error: Optional[str]
    """
    try:
        response = stealth_fetch(url)
        tree = lxml.html.fromstring(response.content)
        elements = tree.xpath(xpath)

        if not elements:
            return ValidationResult(
                success=False,
                elements_found=0,
                error="XPath returned no elements (page structure changed?)"
            )

        return ValidationResult(
            success=True,
            elements_found=len(elements),
            sample_data=elements[:3]
        )
    except Exception as e:
        return ValidationResult(
            success=False,
            error=str(e)
        )
```

### 3. ScrapedData Storage

**Fichier**: `cortex/data/scraped_data/{category}/{source_id}/YYYYMMDD_HHMMSS.json`

**Structure données scrapées**:
```json
{
  "scrape_id": "scrape_20251015_160000_src001",
  "source_id": "src_001",
  "source_name": "GitHub Trending Python",
  "url": "https://github.com/trending/python",
  "xpath_used": "//article//h2/a/@href",
  "scraped_at": "2025-10-15T16:00:00",
  "validation_before_scrape": {
    "status": "success",
    "elements_found": 25
  },
  "data": [
    "/owner/repo1",
    "/owner/repo2",
    "/owner/repo3"
  ],
  "metadata": {
    "elements_count": 25,
    "response_time_ms": 450,
    "status_code": 200,
    "page_size_bytes": 85340
  }
}
```

**Historique complet**:
- Chaque scrape sauvegardé avec timestamp
- Permet de voir évolution dans le temps
- Détection automatique de changements

### 4. DynamicContextManager

**Rôle**: Transforme données scrapées en contexte optimisé pour agents

**Exemple de transformation**:
```python
# Données brutes scrapées
raw_data = [
  "/python/cpython",
  "/pallets/flask",
  "/django/django"
]

# Contexte optimisé pour agents
optimized_context = """
GitHub Trending Python (as of 2025-10-15):
Top repositories:
1. python/cpython - Python language core
2. pallets/flask - Lightweight web framework
3. django/django - Full-stack web framework

Trend: Focus on web frameworks and language development
Relevance: High for Python development questions
Freshness: Updated 2 hours ago
"""
```

**Stratégies d'optimisation**:
```python
class ContextOptimization:
    """Stratégies pour optimiser contexte"""

    # 1. Résumé (si beaucoup de données)
    def summarize(data: List[str]) -> str:
        if len(data) > 20:
            return f"Top 10 items + {len(data)-10} more..."

    # 2. Catégorisation automatique
    def categorize(data: List[str]) -> Dict[str, List[str]]:
        # ML pour grouper par similarité
        return {"web_frameworks": [...], "data_science": [...]}

    # 3. Extraction d'insights
    def extract_insights(data: List[str]) -> List[str]:
        return ["Trend: Focus on AI", "Most active: web dev"]

    # 4. Pertinence scoring
    def score_relevance(data: str, query: str) -> float:
        # Similarité sémantique
        return cosine_similarity(embed(data), embed(query))
```

### 5. ContextEnrichmentAgent

**Rôle**: Agent qui enrichit les prompts entre agents

**Protocole de communication inter-agents**:
```python
class AgentMessage:
    """Message entre agents"""
    from_agent: str
    to_agent: str
    task: str
    context_requests: List[str]  # Contextes demandés
    metadata: Dict[str, Any]

# Exemple flow:
# Agent 1 (AnalysisAgent) → Agent 2 (CodeWriterAgent)

message = AgentMessage(
    from_agent="RequirementsAnalyzer",
    to_agent="CodeWriter",
    task="Implement web scraper for trending repos",
    context_requests=[
        "github_trending_data",  # Demande contexte dynamique
        "web_scraping_best_practices"
    ]
)

# ContextEnrichmentAgent intercepte
enriched = enrichment_agent.enrich_message(message)

# enriched.task devient:
"""
Implement web scraper for trending repos

[DYNAMIC CONTEXT - GitHub Trending (2h ago)]
Current trending Python repos:
- python/cpython
- pallets/flask
- django/django

[STATIC CONTEXT - Web Scraping Best Practices]
- Use stealth techniques (random delays, rotating user-agents)
- Respect robots.txt
- Handle rate limiting
"""
```

**Workflow complet**:
```
1. Agent A termine sa tâche
2. Agent A crée message pour Agent B avec context_requests
3. ContextEnrichmentAgent intercepte:
   ├─> Pour chaque context_request:
   │   ├─> Check DynamicContextManager (scraped data)
   │   ├─> Check StaticKnowledge (docs, patterns)
   │   └─> Score relevance
   └─> Enrichit le prompt avec top contexts
4. Agent B reçoit prompt enrichi
5. Agent B exécute avec contexte complet
```

### 6. Agent Communication Protocol

**Extension de WorkflowEngine**:
```python
class EnhancedWorkflowStep:
    """Step avec enrichissement automatique"""
    name: str
    action: Callable
    agent_name: str

    # NOUVEAU: Demandes de contexte
    context_requests: List[str] = []

    # NOUVEAU: Permet bonification
    allow_enrichment: bool = True

# Usage dans workflow:
steps = [
    EnhancedWorkflowStep(
        name="Analyze trending tech",
        action=analyze_trends,
        agent_name="TrendAnalyzer",
        context_requests=[
            "github_trending_python",
            "hackernews_frontpage",
            "tech_news_summary"
        ]
    ),
    EnhancedWorkflowStep(
        name="Write technical article",
        action=write_article,
        agent_name="ContentWriter",
        context_requests=[
            "previous_analysis_results",  # Du step précédent
            "writing_style_guide"
        ]
    )
]
```

## Cas d'Usage Complet

### Exemple: "Quelles sont les tendances Python actuelles?"

```python
# 1. User demande
user_query = "Quelles sont les tendances Python actuelles?"

# 2. RequestRouter identifie besoin de contexte dynamique
router.analyze(user_query)
# → detected_intent: "tech_trends_query"
# → required_contexts: ["github_trending_python", "pypi_popular_packages"]

# 3. Vérifier fraîcheur des données
for context in required_contexts:
    source = registry.get_source_for_context(context)

    if needs_refresh(source):
        # Crawler valide XPath
        validation = crawler.validate_xpath(source.url, source.xpath)

        if validation.success:
            # Scrape fresh data
            data = crawler.scrape(source)
            storage.save(data)
        else:
            # XPath cassé, alerte humain
            alert(f"XPath broken for {source.name}: {validation.error}")

# 4. DynamicContextManager optimise contexte
context = dynamic_context_manager.get_optimized_context(
    context_id="github_trending_python",
    query=user_query
)

# 5. ContextEnrichmentAgent enrichit prompt
enriched_prompt = f"""
{user_query}

[DYNAMIC CONTEXT]
{context.summary}

Freshness: {context.scraped_ago}
Confidence: {context.confidence}
"""

# 6. Agent analyse avec contexte enrichi
result = analysis_agent.analyze(enriched_prompt)

# 7. Résultat retourné à user avec sources
response = f"""
{result.analysis}

[Sources]
- GitHub Trending (updated 2h ago)
- Data validated at {context.validated_at}
"""
```

## Commandes Manuelles

```python
# Ajouter source
cortex.web.add_source(
    name="HackerNews Frontpage",
    url="https://news.ycombinator.com",
    xpath="//tr[@class='athing']//a[@class='titlelink']/text()",
    category="tech_news"
)

# Valider toutes les sources
cortex.web.validate_all()

# Forcer refresh d'une source
cortex.web.refresh("github_trending_python")

# Voir données scrapées
cortex.web.get_data("github_trending_python", hours_back=24)

# Modifier XPath cassé
cortex.web.update_xpath(
    source="github_trending",
    new_xpath="//div[@class='new-structure']//a/@href"
)
```

## Sécurité & Éthique

```python
class StealthConfig:
    """Configuration éthique du crawler"""

    # Limites strictes
    max_requests_per_minute = 10
    respect_robots_txt = True
    respect_rate_limits = True

    # User-Agent honnête (optionnel)
    identify_as_bot = False  # Si True: "CortexBot/1.0"

    # Pas de scraping agressif
    concurrent_requests = 1  # Séquentiel seulement

    # Cache agressif
    cache_duration_hours = 24  # Éviter re-scrapes
```

## Métriques

```python
{
    "total_sources": 15,
    "active_sources": 12,
    "validation_success_rate": 0.85,
    "average_scrape_time": 2.3,
    "data_freshness_avg_hours": 6.2,
    "context_enrichments_today": 45,
    "xpath_failures_this_week": 3
}
```

---

**Phase 4.1 permettra à Cortex d'avoir accès à des données web dynamiques et toujours fraîches, avec validation automatique et enrichissement intelligent des prompts!**
