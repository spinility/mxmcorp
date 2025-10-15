# 🧠 Cortex MXMCorp

**Système agentique intelligent avec optimisation maximale des coûts**

Cortex MXMCorp est un système d'intelligence artificielle agentique conçu pour maximiser l'efficacité tout en minimisant les coûts. Il peut automatiquement créer des outils, gérer une hiérarchie d'agents, et s'améliorer continuellement.

## 🎯 Philosophie

**Maximum d'efficacité, Minimum de coûts**

- Sélection automatique du modèle le moins cher qui peut accomplir la tâche
- Updates partiels pour économiser 70-95% des tokens
- Cache multi-niveaux pour réutiliser les résultats
- Apprentissage continu pour améliorer les performances

## ✨ Fonctionnalités Principales

### 1. Routing Intelligent de Modèles

Le système sélectionne automatiquement le modèle optimal selon la complexité:

- **GPT-5-Nano** (~$0.0001/1M tokens) → Tâches simples (70% des cas)
- **DeepSeek V3.2** (~$0.15/1M tokens) → Tâches complexes (25% des cas)
- **Claude Sonnet 4.5** (~$3/1M tokens) → Décisions critiques (5% des cas)

### 2. Updates Partiels (Économie Massive)

Au lieu d'envoyer tout le contexte à chaque fois, envoie seulement ce qui change:

```python
# Au lieu de 2500 tokens
update_full(entire_file)  # ❌ Coûteux

# Seulement 160 tokens
update_partial(diff_only)  # ✅ Économise 93.6%
```

Méthodes supportées:
- Git-style diff (pour code)
- JSON Patch (pour données structurées)
- Incremental updates (pour texte)
- Context reuse (réutilisation contexte)

### 3. Système d'Agents Hiérarchique

```
CEO Agent (stratégie)
  ↓
Directors (domaines spécialisés)
  ↓
Managers (coordination)
  ↓
Workers (exécution)
```

Chaque agent:
- A sa propre mémoire
- Utilise le modèle optimal pour son rôle
- Apprend de ses expériences
- Peut créer des outils dynamiquement

### 4. Tool Factory

Génération dynamique d'outils selon les besoins:
- Analyse automatique du besoin
- Génération de code
- Tests automatiques
- Versioning et catalogue

### 5. Département des Communications

- Détecte les faiblesses dans vos requêtes
- Suggère des optimisations
- Forme l'utilisateur de façon proactive
- Améliore continuellement le système

## 🚀 Installation

### Prérequis

- Python 3.11+
- Clés API: OpenAI, DeepSeek, Anthropic

### Installation

```bash
# Cloner le repo
git clone https://github.com/votre-org/mxmcorp.git
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
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...
```

## 💻 Usage

### Lancer le CLI

```bash
python cortex.py
```

### Exemples de requêtes

```
mxm> Liste tous les fichiers Python dans le dossier actuel
mxm> Crée un outil pour extraire les emails d'un CSV
mxm> Analyse ce code et suggère des optimisations
mxm> Génère un rapport hebdomadaire de performance
```

### Commandes disponibles

- `help` - Afficher l'aide
- `stats` - Voir les statistiques (coûts, tokens)
- `clear` - Nettoyer l'écran
- `exit` - Quitter

## 📊 Optimisation des Coûts

### Objectifs de Performance

- Coût moyen par tâche: **$0.001**
- Cache hit rate: **80%+**
- Partial update rate: **70%+**
- Distribution modèles: 70% nano / 25% deepseek / 5% claude

### Stratégies d'Économie

1. **Cache Multi-Niveaux**
   - L1: Mémoire (requêtes identiques)
   - L2: Sémantique (requêtes similaires)
   - L3: Templates (patterns réutilisables)

2. **Compression de Contexte**
   - Extraction d'entités
   - Summarization hiérarchique
   - Encodage efficient
   - Réduction de 40-70%

3. **Code-First Approach**
   - Utiliser code direct si déterministe (coût $0)
   - LLM seulement si nécessaire

## 🏗️ Architecture

```
cortex/
├── core/                 # Moteur principal
│   ├── config_loader.py  # Configuration
│   ├── model_router.py   # Sélection modèles
│   └── partial_updater.py # Updates partiels
├── agents/               # Système agentique
│   ├── roles/           # CEO, Directors, Workers
│   └── prompts/         # Prompts par rôle
├── tools/               # Outils et factory
├── cache/               # Système de cache
├── communication/       # Formation utilisateur
└── cli/                 # Interface CLI
```

## 📈 Roadmap

### Phase 1: MVP (Actuelle)
- [x] Configuration système
- [x] Model Router
- [x] Partial Updater
- [x] CLI de base
- [ ] Intégration LLM APIs
- [ ] Cache L1 (mémoire)

### Phase 2: Optimisation
- [ ] Cache sémantique
- [ ] Compression contexte
- [ ] Métriques détaillées

### Phase 3: Agents
- [ ] Hiérarchie complète
- [ ] Communication inter-agents
- [ ] Mémoire distribuée

### Phase 4: Auto-Évolution
- [ ] Tool Factory
- [ ] Apprentissage continu
- [ ] Formation utilisateur

## 🔧 Configuration

### Fichiers de configuration

- `cortex/config/config.yaml` - Configuration principale
- `cortex/config/models.yaml` - Configuration modèles LLM
- `.env` - Clés API et secrets

### Personnalisation

Modifiez `models.yaml` pour ajuster:
- Thresholds de complexité
- Routing rules
- Budgets par agent
- Stratégies d'optimisation

## 🧪 Tests

```bash
# Tester le model router
python cortex/core/model_router.py

# Tester le partial updater
python cortex/core/partial_updater.py

# Tests unitaires
pytest tests/
```

## 📝 Développement

### Ajouter un nouvel agent

```python
from cortex.agents.base_agent import Agent

class CustomWorker(Agent):
    def __init__(self):
        super().__init__(
            role="Worker",
            specialization="custom"
        )
```

### Créer un nouvel outil

Les outils seront générés automatiquement, mais vous pouvez aussi les coder:

```python
from cortex.tools.base_tool import Tool

class MyTool(Tool):
    def execute(self, params):
        # Votre logique ici
        pass
```

## 💡 Tips d'Optimisation

1. **Formuler des requêtes claires**: Évite les retries coûteux
2. **Réutiliser les patterns**: Le cache fait le reste
3. **Privilégier tâches simples**: Nano est 30,000x moins cher que Claude
4. **Updates incrémentaux**: Ne jamais tout re-générer

## 🤝 Contribution

Contributions bienvenues! Voir [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 Licence

MIT License - Voir [LICENSE](LICENSE)

## 🙏 Remerciements

Inspiré par les meilleurs systèmes agentiques:
- AutoGPT
- CrewAI
- LangChain Agents

Mais optimisé pour **coûts minimaux** et **efficacité maximale**.

---

**MXMCorp** - Intelligence Artificielle Agentique Optimisée
