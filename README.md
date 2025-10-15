# 🧠 Cortex MXMCorp

**Version 4.2** - Système agentique auto-évolutif avec conscience de soi

Cortex MXMCorp est un système d'intelligence artificielle agentique avancé qui s'auto-améliore, gère ses capacités, et optimise continuellement ses coûts. Il peut découvrir automatiquement ses propres outils, créer de nouveaux agents, et maintenir une conscience complète de son environnement.

## 🎯 Philosophie

**Maximum d'efficacité, Minimum de coûts, Auto-amélioration continue**

- Sélection automatique du modèle le moins cher qui peut accomplir la tâche
- Système de cache multi-niveaux (95%+ économie de tokens)
- Découverte automatique des capacités (self-awareness)
- Auto-évolution basée sur les patterns détectés
- Web intelligence avec scraping indétectable

## ✨ Fonctionnalités Actuelles (v4.2)

### 🎯 Phase 1-2: Fondations (✅ COMPLÉTÉ)
- ✅ Configuration système avancée
- ✅ Model Router intelligent (3 tiers: NANO/DEEPSEEK/CLAUDE)
- ✅ LLM Client unifié (OpenAI, DeepSeek, Anthropic)
- ✅ Système de cache multi-niveaux
- ✅ CLI interactif avec rich interface

### 🤖 Phase 3: Système Organisationnel (✅ COMPLÉTÉ)

#### Phase 3.1: Départements & Hiérarchie
- ✅ 4 Départements: Communication, Intelligence, Maintenance, Optimization
- ✅ Hiérarchie d'agents (4 niveaux: AGENT → EXPERT → DECISION → DIRECTOR)
- ✅ TodoList Manager avec tracking temps réel
- ✅ Système de communication (CEO Reports, Alerts)

#### Phase 3.2: Workflow & Maintenance
- ✅ WorkflowEngine avec orchestration automatique
- ✅ Git Diff Processor pour suivi des changements
- ✅ Roadmap Manager auto-synchronisé
- ✅ Context Updater (95% économie tokens via AST parsing)
- ✅ Dependency Tracker avec détection de cycles

#### Phase 3.3: Auto-Évolution
- ✅ Pattern Detector (analyse historique des requêtes)
- ✅ Tool Evolver (génération automatique d'outils bash)
- ✅ Agent Evolver (génération automatique d'agents Python)
- ✅ Calcul ROI et priorisation automatique

### 🌐 Phase 4: Intelligence & Conscience (✅ COMPLÉTÉ)

#### Phase 4.1: Web Intelligence
- ✅ XPath Source Registry (gestion URL + XPath manuellement)
- ✅ Stealth Web Crawler (indétectable, rotation user-agents)
- ✅ Dynamic Context Manager (optimisation 94% tokens)
- ✅ Context Enrichment Agent (injection contexte inter-agents)
- ✅ Intégration WorkflowEngine avec context_requests

#### Phase 4.2: Self-Awareness System ⭐ NOUVEAU
- ✅ **Capability Registry**: Découverte auto de 25 capacités (4 départements, 10 agents, 11 outils)
- ✅ **Environment Scanner**: Validation complète (OS, Python, Git, API keys, permissions)
- ✅ **Self Introspection Agent**: Répond à "Que peux-tu faire?" avec rapport complet
- ✅ Détection automatique des limitations
- ✅ Génération de documentation à jour
- ✅ Visibilité coût/modèle avant et après chaque appel LLM
- ✅ Détection automatique de troncature (max_tokens insuffisant)

## 🚀 Installation

### Prérequis

- Python 3.10+
- Clés API: OpenAI (optionnel), DeepSeek (optionnel), Anthropic (recommandé)

### Installation

```bash
# Cloner le repo
git clone https://github.com/spinility/mxmcorp.git
cd mxmcorp

# Installer les dépendances
pip install -r requirements.txt

# Configurer les clés API
cp .env.example .env
# Éditer .env et ajouter vos clés
```

### Configuration des clés API

Éditez `.env`:

```bash
OPENAI_API_KEY=sk-...           # Pour GPT-5-Nano (optionnel)
DEEPSEEK_API_KEY=...            # Pour DeepSeek V3.2 (optionnel)
ANTHROPIC_API_KEY=sk-ant-...    # Pour Claude Sonnet 4.5 (recommandé)
```

## 💻 Usage

### Lancer Cortex

```bash
python cortex_start.py
```

### Commandes Principales

```bash
# Self-awareness
cortex> Que peux-tu faire?              # Rapport complet des capacités
cortex> Quelles sont tes limitations?   # Liste des contraintes actuelles

# Web Intelligence
cortex> Scrape les tendances GitHub Python
cortex> Valide ce XPath pour moi

# Auto-évolution
cortex> Analyse mes patterns de requêtes
cortex> Crée un outil pour [tâche répétitive]

# Maintenance
cortex> Mets à jour le roadmap
cortex> Quels fichiers ont changé?
cortex> Génère rapport CEO
```

## 📊 Statistiques Actuelles

### Capacités Découvertes (Auto-Discovery)
- **4 Départements**: Communication, Intelligence, Maintenance, Optimization
- **10 Agents**: CEOAgent, PlannerAgent, DeveloperAgent, HRAgent, etc.
- **11 Outils**: Web Tools, Git Tools, Factory, Tool Executor, etc.
- **0 Workflows** (en développement)

### Performance
- **Cache hit rate**: 80%+ (économie massive)
- **Token reduction**: 95% via context caching
- **Cost per task**: ~$0.001 (moyenne)
- **Auto-discovery**: 25 composants détectés automatiquement

### Environnement (Example)
- **Platform**: Linux/Windows/macOS
- **Python**: 3.10+ (187 packages installés)
- **Git**: ✅ Disponible, branch: main
- **API Keys**: Anthropic ✅, OpenAI ⚠️, DeepSeek ⚠️
- **Permissions**: Read ✅, Write ✅, Execute ✅

## 🏗️ Architecture

```
cortex/
├── core/                      # Moteur principal
│   ├── llm_client.py         # Client LLM unifié
│   ├── model_router.py       # Routing intelligent
│   ├── workflow_engine.py    # Orchestration
│   ├── capability_registry.py # Auto-discovery ⭐
│   ├── environment_scanner.py # Validation env ⭐
│   └── self_introspection_agent.py # Conscience ⭐
├── departments/              # Départements organisés
│   ├── communication/        # CEO Reports, Alerts
│   ├── intelligence/         # Web scraping, Context
│   ├── maintenance/          # Git diff, Roadmap
│   └── optimization/         # Patterns, Learning
├── agents/                   # Hiérarchie d'agents
│   ├── ceo_agent.py         # Orchestration
│   ├── planner_agent.py     # Planification
│   └── ...                   # 10 agents total
├── tools/                    # Outils et factory
│   ├── tool_executor.py     # Exécution automatique
│   └── generated/           # Outils auto-générés
├── cache/                    # Cache multi-niveaux
└── cli/                      # Interface CLI
```

## 🎯 Capacités par Domaine

### 📊 Data Collection
- ✅ Web scraping (StealthWebCrawler - indétectable)
- ✅ XPath validation automatique
- ✅ Dynamic context optimization
- ❌ Direct API calls (nécessite implémentation par API)

### 🔍 Analysis
- ✅ Code analysis (AST parsing)
- ✅ Dependency tracking avec détection cycles
- ✅ Pattern detection (auto-évolution)
- ✅ Context summarization (95% token reduction)
- ✅ Cost optimization

### 💻 Development
- ✅ Python code generation
- ✅ Bash script generation
- ✅ Tool auto-generation
- ✅ Agent auto-generation
- ❌ JavaScript/TypeScript (non implémenté)
- ❌ Frontend frameworks (non implémenté)

### 🧪 Testing
- ✅ Automated test generation
- ✅ Test execution
- ⚠️  Integration testing (limité)

### 📝 Documentation
- ✅ Auto-generated docs
- ✅ Capability reports (self-awareness)
- ✅ TODO management
- ✅ Roadmap synchronization

### 🔧 Maintenance
- ✅ Git diff analysis automatique
- ✅ Automatic context updates
- ✅ Breaking change detection
- ✅ Dependency graph tracking

### 🤝 Communication
- ✅ CEO reports (daily/weekly)
- ✅ Alert system
- ✅ Progress tracking
- ✅ Self-awareness reporting ⭐

## 🚧 Limitations Actuelles

### Environnement
- ⚠️  Ne peut pas accéder APIs externes sans credentials
- ⚠️  Ne peut pas exécuter processus >10 minutes
- ⚠️  Ne peut pas modifier fichiers hors projet
- ⚠️  Limité à opérations single-repository

### Langages & Frameworks
- ❌ JavaScript/TypeScript (non implémenté)
- ❌ Frontend frameworks (React, Vue, etc.)
- ❌ Mobile development
- ❌ Accès base de données direct (nécessite outils)

### APIs
- Configuration requise pour chaque API
- Pas de support générique pour toutes les APIs

## 📈 Roadmap Future

### Phase 5: Semantic Intelligence (Planifié)
- [ ] Recherche sémantique avancée
- [ ] Clustering automatique de patterns
- [ ] Embeddings-based similarity
- [ ] RAG (Retrieval-Augmented Generation)

### Phase 6: Multi-Agent Collaboration (Planifié)
- [ ] Communication inter-agents async
- [ ] Négociation et consensus
- [ ] Task delegation intelligente
- [ ] Shared memory pool

### Phase 7: Production Features (Planifié)
- [ ] API REST pour intégration externe
- [ ] Dashboard web de monitoring
- [ ] Alertes temps réel
- [ ] Métriques business

## 🧪 Tests

```bash
# Self-awareness integration test
PYTHONPATH=/github/mxmcorp python3 tests/test_self_awareness_integration.py

# Web intelligence E2E test
PYTHONPATH=/github/mxmcorp python3 tests/test_web_intelligence_e2e.py

# Phase 3 integration tests
PYTHONPATH=/github/mxmcorp python3 tests/test_phase3_1_integration.py
PYTHONPATH=/github/mxmcorp python3 tests/test_phase3_2_integration.py

# Tous les tests
pytest tests/
```

## 💡 Exemples d'Usage

### Self-Awareness
```python
from cortex.core import SelfIntrospectionAgent

agent = SelfIntrospectionAgent()

# Rapport complet
report = agent.generate_capability_report()
print(report)

# Question spécifique
result = agent.can_i_do("scrape a website")
if result['can_do']:
    print(f"Yes! Use: {result['how']}")
else:
    print(f"No. Suggestion: {result['suggestion']}")
```

### Web Intelligence
```python
from cortex.departments.intelligence import (
    XPathSourceRegistry,
    StealthWebCrawler,
    DynamicContextManager
)

# Add source
registry = XPathSourceRegistry()
source = registry.add_source(
    name="HackerNews",
    url="https://news.ycombinator.com",
    xpath="//span[@class='titleline']/a/text()",
    category="tech_news"
)

# Scrape
crawler = StealthWebCrawler()
data = crawler.scrape(source)

# Optimize
manager = DynamicContextManager()
context = manager.optimize_scraped_data(data)
```

### Cost Visibility
```python
from cortex.core import LLMClient, ModelTier

client = LLMClient()

# Voir coût avant et après
response = client.complete(
    messages=[{"role": "user", "content": "Hello"}],
    tier=ModelTier.NANO,
    max_tokens=100,
    verbose=True  # Affiche modèle, coût estimé, tokens, etc.
)
```

## 🤝 Contribution

Contributions bienvenues!

Le système peut maintenant s'auto-documenter via le Self-Awareness System.

## 📄 Licence

MIT License

## 🙏 Remerciements

Construit avec des concepts inspirés de:
- AutoGPT - Autonomie agentique
- CrewAI - Organisation hiérarchique
- LangChain - Outils et chains

Mais optimisé pour:
- **Coûts minimaux** (cache 95%+ économie)
- **Auto-amélioration** (évolution basée patterns)
- **Conscience de soi** (self-awareness complet)

---

**MXMCorp Cortex v4.2** - Intelligence Artificielle Agentique Auto-Évolutive

*Système qui se connaît, s'améliore, et optimise continuellement*

🤖 Découvert automatiquement: 25 capacités | 4 départements | 10 agents | 11 outils
