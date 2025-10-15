# Phase 3.4 - Context & Dependency Tracking

## Vue d'ensemble

Complète le **département Maintenance** avec des systèmes automatiques qui maintiennent:
- **Context Cache**: Résumés de fichiers pour économiser tokens
- **Dependency Graph**: Graphe complet des dépendances entre fichiers
- **Documentation automatique**: SITEPLAN, DEPENDENCIES, CHANGELOG

## Déclenchement automatique

Après chaque `git diff` (détecté par Maintenance), le système:
1. Met à jour contextes des fichiers modifiés
2. Recalcule dépendances affectées
3. Régénère documentation impactée

## Composants

### 1. ContextUpdater

**Rôle**: Maintient cache de contextes pour réduire tokens

**Structure context**:
```python
{
    "file_path": "cortex/core/agent.py",
    "summary": "Agent base class with execute() method...",
    "exports": ["Agent", "create_agent"],
    "imports": ["typing", "datetime", "cortex.core.base"],
    "classes": ["Agent", "AgentConfig"],
    "functions": ["create_agent", "validate_agent"],
    "last_updated": "2025-10-15T16:00:00",
    "lines_of_code": 450,
    "complexity_score": 0.65
}
```

**Mise à jour automatique**:
- Si fichier modifié dans git diff → régénère contexte
- Si dépendances changées → met à jour imports/exports

### 2. DependencyTracker

**Rôle**: Maintient graphe complet des dépendances

**Graphe de dépendances**:
```python
{
    "cortex/core/agent.py": {
        "imports_from": [
            "cortex/core/base.py",
            "typing"
        ],
        "imported_by": [
            "cortex/agents/code_writer.py",
            "cortex/departments/development/__init__.py"
        ],
        "circular_dependencies": [],
        "depth": 2  # Distance depuis root
    }
}
```

**Détecte**:
- Dépendances circulaires
- Fichiers impactés par un changement
- Modules orphelins (non utilisés)

### 3. DocumentationUpdater

**Rôle**: Met à jour documentation automatiquement

**Documents maintenus**:

1. **SITEPLAN.md**: Architecture complète
2. **DEPENDENCIES.md**: Graphe de dépendances
3. **CHANGELOG.md**: Historique des changements

**Mise à jour SITEPLAN**:
- Ajoute nouveaux fichiers avec descriptions
- Met à jour structure si départements changés
- Régénère arbre de répertoires

**Mise à jour DEPENDENCIES**:
- Régénère graphe complet
- Marque dépendances circulaires
- Montre modules critiques (très utilisés)

**Mise à jour CHANGELOG**:
- Extrait de git log
- Groupe par type (feat/fix/docs/refactor)
- Ajoute liens vers commits

## Workflow complet

```
1. Code modifié → git commit
         ↓
2. Maintenance détecte via GitDiffProcessor
         ↓
3. ContextUpdater:
   - Parse fichiers modifiés
   - Extrait exports/imports/classes/functions
   - Génère summary
   - Cache contexte
         ↓
4. DependencyTracker:
   - Recalcule imports/exports
   - Met à jour graphe
   - Détecte circularités
         ↓
5. DocumentationUpdater:
   - SITEPLAN: Ajoute/met à jour fichiers
   - DEPENDENCIES: Régénère graphe
   - CHANGELOG: Ajoute commit
         ↓
6. RoadmapManager:
   - Marque tâches complétées
   - Génère nouvelles tâches
         ↓
7. CEOReporter:
   - Alerte si nécessaire
   - Inclut dans rapport quotidien
```

## Bénéfices

**Économie de tokens**:
- Context cache évite de lire fichiers complets
- Summary de 100 lignes au lieu de 5000 lignes
- **Réduction ~95% des tokens** pour analyse

**Détection proactive**:
- Dépendances circulaires détectées immédiatement
- Modules orphelins identifiés
- Impact des changements visible

**Documentation toujours à jour**:
- SITEPLAN reflète structure réelle
- DEPENDENCIES montre graphe actuel
- CHANGELOG auto-généré depuis git

## Implémentation

### Fichiers à créer:

```
cortex/departments/maintenance/
├── context_updater.py       # Cache de contextes
├── dependency_tracker.py    # Graphe dépendances
└── documentation_updater.py # Auto-doc

cortex/data/
├── context_cache.json       # Cache contextes
└── dependency_graph.json    # Graphe dépendances
```

## Exemple concret

**Scénario**: Modification de `cortex/core/agent.py`

```python
# Git diff détecté
files_modified = ["cortex/core/agent.py"]

# 1. ContextUpdater
context = {
    "file_path": "cortex/core/agent.py",
    "summary": "Base Agent class updated: added new validate() method",
    "exports": ["Agent", "create_agent", "validate_agent"],  # +1 export
    "classes": ["Agent", "AgentConfig"],
    "functions": ["create_agent", "validate_agent"],  # +1 function
    "last_updated": "2025-10-15T16:30:00"
}
# Saved to cache

# 2. DependencyTracker
affected_files = [
    "cortex/agents/code_writer.py",      # Importe Agent
    "cortex/departments/development/__init__.py"
]
# Ces fichiers pourraient être affectés

# 3. DocumentationUpdater
# SITEPLAN.md updated:
"""
### cortex/core/agent.py
Base Agent class with validation capabilities
- Classes: Agent, AgentConfig
- Functions: create_agent, validate_agent (NEW)
- Exports: Agent, create_agent, validate_agent
"""

# DEPENDENCIES.md updated:
"""
cortex/core/agent.py (MODIFIED)
  ← Imported by: 15 files
  → Imports: 3 files
  ⚠ Potential impact: HIGH (many importers)
"""

# CHANGELOG.md updated:
"""
## 2025-10-15

### Changed
- `cortex/core/agent.py`: Added validate_agent() method (commit 99ac02e)
"""
```

---

**Phase 3.4 permettra une maintenance automatique complète et une économie massive de tokens!**
