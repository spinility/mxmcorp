# Cortex MXMCorp - Agent Hierarchy System

## Overview

Système hiérarchique d'agents intelligents avec spécialisations, mémoire, et optimisation des coûts.

## Architecture

```
CEO (Chief Executive Officer)
├── Code Director (Software Engineering)
│   └── [Managers & Workers - À implémenter]
├── Data Director (Data & Analytics)
│   └── [Managers & Workers - À implémenter]
├── Communication Director (User Interaction)
│   └── [Managers & Workers - À implémenter]
└── Operations Director (Infrastructure)
    └── [Managers & Workers - À implémenter]
```

## Composants Implémentés

### 1. BaseAgent (`cortex/agents/base_agent.py`)

**Fonctionnalités:**
- Mémoire court terme (dernières 10 interactions)
- Mémoire long terme (connaissances persistantes)
- Intégration tools (via ToolExecutor)
- Système de délégation aux subordonnés
- Sélection automatique du tier LLM
- Tracking des coûts et statistiques

**Classe AgentMemory:**
- `short_term`: Liste des dernières interactions
- `long_term`: Dict de connaissances persistantes
- `get_context()`: Génère contexte pour le LLM

**Classe AgentConfig:**
- `name`, `role`, `description`
- `base_prompt`: Prompt système de l'agent
- `tier_preference`: Tier LLM préféré
- `can_delegate`: Capacité de délégation
- `specializations`: Liste de spécialisations

**Méthodes principales:**
- `execute(task)`: Exécute une tâche
- `delegate(task, to_agent)`: Délègue à un subordonné
- `register_tool(tool)`: Ajoute un tool
- `get_stats()`: Statistiques d'utilisation

### 2. CEOAgent (`cortex/agents/ceo_agent.py`)

**Rôle:** Orchestrateur stratégique principal

**Responsabilités:**
- Analyser les demandes utilisateur
- Décomposer en sous-tâches
- Déléguer aux Directors appropriés
- Synthétiser les résultats
- Optimiser les coûts globaux

**Tier préféré:** DEEPSEEK (équilibre coût/capacité stratégique)

**Subordonnés:** 4 Directors

### 3. Directors (`cortex/agents/directors.py`)

#### Code Director
**Spécialisations:** code, programming, development, software, debug, refactor

**Expertise:**
- Architecture et design patterns
- Développement multi-langages
- Refactoring et optimisation
- Debugging et problem-solving
- Code review et best practices

#### Data Director
**Spécialisations:** data, analysis, ml, ai, machine learning, statistics, database

**Expertise:**
- Analyse de données et visualisation
- Machine Learning et AI
- Data pipelines et ETL
- Optimisation de bases de données
- Analyse statistique

#### Communication Director
**Spécialisations:** communication, training, documentation, help, support, user

**Expertise:**
- Interaction et support utilisateur
- Formation et éducation
- Documentation technique
- UX et accessibilité
- Assistance proactive

**Tier préféré:** NANO (tâches souvent simples)

**Mission spéciale:**
- Détecter les faiblesses des utilisateurs
- Offrir formation proactive
- Guider vers de meilleures pratiques

#### Operations Director
**Spécialisations:** operations, infrastructure, deployment, devops, monitoring, performance

**Expertise:**
- Infrastructure et cloud
- Deployment et CI/CD
- Monitoring et observabilité
- Performance et scaling
- Sécurité et compliance

### 4. AgentHierarchy (`cortex/agents/hierarchy.py`)

**Gestionnaire central de la hiérarchie:**
- Création et connexion de tous les agents
- Point d'entrée principal (`process_request`)
- Statistiques globales
- Pattern Singleton

**Méthodes:**
- `process_request(user_request)`: Traite via CEO
- `get_agent(name)`: Récupère un agent
- `get_all_stats()`: Stats de tous les agents
- `print_hierarchy()`: Affiche structure

## Caractéristiques Clés

### Mémoire des Agents
Chaque agent maintient sa propre mémoire:
```python
# Mémoire court terme
memory.add_to_short_term({
    "task": "Fix bug",
    "summary": "Fixed Python syntax error",
    "cost": 0.000100
})

# Mémoire long terme
memory.add_to_long_term("user_language", "Python")
```

### Délégation Intelligente
```python
# Délégation automatique au meilleur subordonné
result = ceo.delegate("Fix this Python bug")

# Ou délégation ciblée
result = ceo.delegate("Fix bug", to_agent="CodeDirector")
```

### Optimisation des Coûts
- Chaque agent track son coût total
- Sélection automatique du tier le moins cher
- Model Router analyse la complexité
- Stats globales pour monitoring

## Exemples d'Utilisation

### Utilisation Simple
```python
from cortex.agents.hierarchy import get_hierarchy

# Récupérer la hiérarchie (singleton)
hierarchy = get_hierarchy()

# Traiter une requête
result = hierarchy.process_request("Write a Python function to reverse a string")

print(result['data'])  # Résultat
print(f"Cost: ${result['cost']:.6f}")
```

### Utilisation Directe d'un Agent
```python
# Utiliser directement un Director
hierarchy = get_hierarchy()
code_director = hierarchy.code_director

result = code_director.execute("Explain list comprehensions")
```

### Ajouter des Tools à un Agent
```python
from cortex.tools.standard_tool import tool

@tool(name="search", description="Search the web")
def search(query: str):
    return {"results": [...]}

hierarchy.ceo.register_tool(search)
```

## Statistiques

Chaque agent track:
- `task_count`: Nombre de tâches exécutées
- `delegation_count`: Nombre de délégations
- `total_cost`: Coût total accumulé
- `avg_cost_per_task`: Coût moyen par tâche

```python
stats = hierarchy.get_all_stats()
print(f"Total tasks: {stats['total_tasks']}")
print(f"Total cost: ${stats['total_cost']:.6f}")
```

## Configuration

### Créer un Agent Custom
```python
from cortex.agents.base_agent import BaseAgent, AgentConfig
from cortex.core.model_router import ModelTier

config = AgentConfig(
    name="SecurityDirector",
    role="Director of Security",
    description="Expert in cybersecurity",
    base_prompt="You are a security expert...",
    tier_preference=ModelTier.CLAUDE,  # Tier premium pour sécurité
    can_delegate=True,
    specializations=["security", "vulnerability", "pentest"],
    max_delegation_depth=2
)

security_director = BaseAgent(config)
```

## Prochaines Étapes

### Niveau 3: Managers (À implémenter)
- Backend Manager, Frontend Manager, DevOps Manager (sous Code Director)
- Analytics Manager, ML Manager, Data Eng Manager (sous Data Director)
- Training Manager, Documentation Manager, Support Manager (sous Communication Director)
- Infrastructure Manager, Deployment Manager, Monitoring Manager (sous Operations Director)

### Niveau 4: Workers (À implémenter)
- Agents spécialisés pour tâches très spécifiques
- Utilisation intensive du tier NANO
- Exécution parallèle possible

### Améliorations Futures
1. **Multi-agent collaboration:** Plusieurs agents travaillent ensemble
2. **Learning system:** Agents apprennent des succès/échecs
3. **Advanced delegation:** Routing basé sur ML
4. **Persistent memory:** Sauvegarde sur disque
5. **Agent marketplace:** Partage et import d'agents

## Tests

**Structure validée:**
```bash
python3 -c "from cortex.agents.hierarchy import get_hierarchy; get_hierarchy().print_hierarchy()"
```

Output:
```
CEO (Chief Executive Officer)
  Tasks: 0 | Cost: $0.000000
  ├── CodeDirector (Director of Software Engineering)
  ├── DataDirector (Director of Data & Analytics)
  ├── CommunicationDirector (Director of Communications)
  └── OperationsDirector (Director of Operations)
```

## Fichiers Créés

- `cortex/agents/__init__.py` - Package agents
- `cortex/agents/base_agent.py` (455 lignes) - BaseAgent, AgentMemory, AgentConfig
- `cortex/agents/ceo_agent.py` (97 lignes) - CEOAgent
- `cortex/agents/directors.py` (217 lignes) - 4 Directors
- `cortex/agents/hierarchy.py` (143 lignes) - AgentHierarchy
- `test_agents_hierarchy.py` (267 lignes) - Tests complets
- `test_agents_quick.py` (60 lignes) - Test rapide

## Conclusion

Le système d'agents Cortex MXMCorp est maintenant opérationnel avec:
- ✅ Architecture hiérarchique CEO + 4 Directors
- ✅ Mémoire individuelle par agent
- ✅ Système de délégation
- ✅ Intégration tools
- ✅ Optimisation des coûts
- ✅ Tracking et statistiques

Le système est extensible et prêt pour l'ajout des niveaux 3 (Managers) et 4 (Workers).
