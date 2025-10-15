# Système Dynamique Cortex MXMCorp

## Vue d'ensemble

Le système Cortex a été transformé en une architecture entièrement dynamique où :

1. **Le Cortex (CEO) n'a AUCUNE compétence directe** - Il délègue TOUJOURS
2. **Si l'employé n'existe pas, les RH le créent** - Création dynamique à la demande
3. **Si un outil manque, le département Outils le fabrique** - Fabrication automatique
4. **Chaque employé peut demander des employés et des outils** - Système récursif

## Architecture

```
CORTEX MXMCORP
├── CEO (Orchestrateur pur - JAMAIS d'exécution directe)
│   ├── CodeDirector
│   ├── DataDirector
│   ├── CommunicationDirector
│   └── OperationsDirector
│
├── HR Department (Département des Ressources Humaines)
│   ├── Crée des employés spécialisés à la demande
│   ├── Utilise NANO tier pour analyser les besoins
│   ├── Génère la configuration optimale via LLM
│   └── Maintient un registre de tous les employés créés
│
└── Tools Department (Département des Outils)
    ├── Fabrique des outils personnalisés à la demande
    ├── Utilise DEEPSEEK tier pour générer du code
    ├── Crée des outils Python exécutables
    └── Maintient un catalogue d'outils disponibles
```

## Composants Principaux

### 1. CEO Agent (`cortex/agents/ceo_agent.py`)

**Philosophie:** TOUJOURS déléguer, JAMAIS exécuter

**Caractéristiques:**
- Tier: `NANO` (simple routing)
- Prompt système modifié pour interdire l'exécution directe
- Méthodes ajoutées:
  - `request_employee_creation()` - Demande un employé aux RH
  - `request_tool_creation()` - Demande un outil au département Outils
- `analyze_and_delegate()` - Délègue systématiquement aux Directors

### 2. HR Department (`cortex/agents/hr_department.py`)

**Responsabilités:**
- Analyser les demandes de création d'employés
- Générer des configurations d'agents optimales
- Créer et enregistrer de nouveaux employés
- Maintenir un registre des employés créés
- Donner accès aux départements aux employés créés

**Classe EmployeeRequest:**
```python
@dataclass
class EmployeeRequest:
    requested_by: str
    task_description: str
    required_skills: List[str]
    expected_tier: ModelTier
```

**Méthodes principales:**
- `create_employee(request)` - Crée un employé sur mesure
- `_generate_agent_config()` - Génère la config via LLM (NANO)
- `get_employee(name)` - Récupère un employé
- `list_employees()` - Liste tous les employés
- `get_stats()` - Statistiques du département

**Optimisation:**
- Utilise tier NANO pour générer les configs (économique)
- Fallback automatique si parsing JSON échoue
- Employés créés avec tier NANO par défaut

### 3. Tools Department (`cortex/agents/tools_department.py`)

**Responsabilités:**
- Analyser les demandes de création d'outils
- Générer du code d'outil fonctionnel via LLM
- Créer des outils Python exécutables
- Maintenir un catalogue d'outils disponibles
- Rendre les outils disponibles à tous

**Classe ToolRequest:**
```python
@dataclass
class ToolRequest:
    requested_by: str
    tool_purpose: str
    input_description: str
    output_description: str
    example_usage: Optional[str]
```

**Méthodes principales:**
- `create_tool(request)` - Fabrique un outil sur mesure
- `_generate_tool_code()` - Génère le code Python via LLM (DEEPSEEK)
- `_create_executable_tool()` - Compile le code en outil exécutable
- `get_tool(name)` - Récupère un outil
- `search_tools(query)` - Cherche des outils par mot-clé
- `get_stats()` - Statistiques du département

**Optimisation:**
- Utilise tier DEEPSEEK pour générer du code (bon rapport qualité/prix)
- Extraction automatique de code depuis réponses LLM
- Fallback automatique si compilation échoue
- Outils décorés avec `@tool` pour intégration native

### 4. BaseAgent Amélioré (`cortex/agents/base_agent.py`)

**Ajouts:**
- Références aux départements HR et Tools dans `__init__()`
- Méthode `request_employee()` - N'importe quel agent peut demander un employé
- Méthode `request_tool()` - N'importe quel agent peut demander un outil

**Impact:**
- TOUS les agents (CEO, Directors, Employés) peuvent créer des employés
- TOUS les agents peuvent créer des outils
- Système récursif et auto-extensible

### 5. AgentHierarchy Mise à Jour (`cortex/agents/hierarchy.py`)

**Changements:**
- Création des départements HR et Tools en premier
- HR créé avec référence à Tools (pour que les employés puissent demander des outils)
- Tous les Directors reçoivent accès aux départements
- Statistiques étendues incluant HR et Tools
- Affichage de hiérarchie étendu

**Calculs mis à jour:**
- `_calculate_total_cost()` - Inclut coûts HR et Tools
- `_calculate_total_tasks()` - Inclut tâches des employés dynamiques
- `print_hierarchy()` - Affiche départements et leurs stats

## Exemples d'Utilisation

### Exemple 1: CEO demande un employé

```python
from cortex.agents.hierarchy import get_hierarchy

hierarchy = get_hierarchy()

# Le CEO a besoin d'un employé pour une tâche spécifique
result = hierarchy.ceo.request_employee_creation(
    task_description="Parse CSV files and extract specific columns",
    required_skills=["csv", "parsing", "data extraction"],
    tier=ModelTier.NANO,
    verbose=True
)

if result["success"]:
    employee = result["agent"]
    # L'employé est automatiquement enregistré comme subordonné
    # Il peut maintenant être utilisé pour des tâches
```

### Exemple 2: Director demande un outil

```python
# Le Data Director a besoin d'un outil statistique
result = hierarchy.data_director.request_tool(
    tool_purpose="Calculate basic statistics (mean, median, std) for numbers",
    input_description="numbers: List[float] - List of numbers",
    output_description="dict with mean, median, std_dev",
    verbose=True
)

if result["success"]:
    tool = result["tool"]
    # L'outil est disponible pour le Director et ses subordonnés
```

### Exemple 3: Employé demande un autre employé

```python
# Un employé créé par HR peut aussi demander des employés
sql_worker = hierarchy.hr_department.get_employee("SqlOptimizationWorker")

# Cet employé demande un sous-employé pour les tests
sub_result = sql_worker.request_employee(
    task_description="Test database performance after optimization",
    required_skills=["database", "testing", "performance"],
    verbose=True
)

# Système récursif: employés peuvent créer d'autres employés
```

### Exemple 4: Workflow complet

```python
# 1. Code Director demande un employé
employee_result = hierarchy.code_director.request_employee(
    task_description="Optimize database queries and add indexes",
    required_skills=["sql", "database", "optimization"],
    tier=ModelTier.NANO
)

employee = employee_result["agent"]

# 2. L'employé demande un outil pour son travail
tool_result = employee.request_tool(
    tool_purpose="Analyze SQL query execution plan",
    input_description="query: str - SQL query to analyze",
    output_description="dict with execution_time, suggested_indexes"
)

# 3. L'employé demande un sous-employé pour tester
sub_employee_result = employee.request_employee(
    task_description="Test database performance",
    required_skills=["database", "testing"]
)

# Système entièrement autonome et auto-extensible
```

## Tests

### Test Structurel (Rapide)

```bash
python3 test_dynamic_simple.py
```

Ce test vérifie:
- ✓ Structure de base (CEO, Directors, Départements)
- ✓ Accès aux départements pour tous les agents
- ✓ Structure hiérarchique correcte
- ✓ Méthodes de demande disponibles
- ✓ Philosophie CEO (TOUJOURS déléguer)
- ✓ Statistiques et utilitaires

### Test Complet (Avec LLM)

```bash
python3 test_dynamic_system.py
```

Ce test vérifie avec appels LLM réels:
- Création d'employés par RH
- Création d'outils par département Outils
- Demandes par Directors
- Workflow complet multi-niveaux

## Optimisations des Coûts

### Stratégie de Tiers

1. **CEO**: `NANO` - Simple routing, pas de génération
2. **HR Department**: `NANO` - Génération de configs JSON simples
3. **Tools Department**: `DEEPSEEK` - Génération de code de qualité
4. **Employés créés**: `NANO` par défaut - Tâches spécialisées simples

### Économies Réalisées

- Employés créés à la demande (pas de structure fixe coûteuse)
- Tier NANO pour tâches simples (~14x moins cher que Claude)
- Réutilisation des employés créés (registre HR)
- Réutilisation des outils créés (catalogue Tools)
- Pas d'exécution directe par CEO (délégation systématique)

## Statistiques Disponibles

```python
stats = hierarchy.get_all_stats()

# Stats globales
stats['total_cost']  # Coût total incluant départements
stats['total_tasks']  # Tâches totales incluant employés dynamiques

# Stats CEO et Directors
stats['ceo']
stats['directors']['code']
stats['directors']['data']
stats['directors']['communication']
stats['directors']['operations']

# Stats départements
stats['departments']['hr']
# - employees_created
# - active_employees
# - total_employee_tasks
# - total_employee_cost

stats['departments']['tools']
# - tools_created
# - available_tools
# - total_usage
# - total_cost
```

## Fichiers Créés/Modifiés

### Nouveaux Fichiers

- `cortex/agents/hr_department.py` (276 lignes) - Département RH
- `cortex/agents/tools_department.py` (213 lignes) - Département Outils
- `test_dynamic_system.py` (320 lignes) - Tests complets
- `test_dynamic_simple.py` (156 lignes) - Tests structurels
- `DYNAMIC_SYSTEM.md` - Cette documentation

### Fichiers Modifiés

- `cortex/agents/ceo_agent.py` - Ajout request methods, philosophie TOUJOURS déléguer
- `cortex/agents/base_agent.py` - Ajout request_employee() et request_tool()
- `cortex/agents/hierarchy.py` - Intégration départements, stats étendues

## Avantages du Système

### 1. Auto-Extensible

Le système peut créer ses propres employés selon les besoins, sans limite de structure prédéfinie.

### 2. Auto-Outillé

Le système peut fabriquer ses propres outils quand nécessaire, sans dépendre d'une bibliothèque fixe.

### 3. Optimisé Coûts

- Création d'employés NANO à la demande
- Pas de structure fixe coûteuse
- Réutilisation des ressources créées

### 4. Récursif

- Employés peuvent créer d'autres employés
- Employés peuvent créer des outils
- Structure dynamique illimitée

### 5. Transparent

- Tous les employés enregistrés dans HR
- Tous les outils catalogués dans Tools
- Statistiques complètes disponibles

## Prochaines Évolutions Possibles

### 1. Persistance

- Sauvegarder employés créés sur disque
- Sauvegarder outils créés dans fichiers .py
- Réutilisation entre sessions

### 2. Apprentissage

- Suivre quels employés sont les plus efficaces
- Suivre quels outils sont les plus utilisés
- Optimiser les créations futures

### 3. Marché

- Partager des employés entre projets
- Partager des outils entre utilisateurs
- Bibliothèque communautaire

### 4. Validation

- Tester les outils générés automatiquement
- Valider la performance des employés
- Système de notation

### 5. Optimisation Avancée

- Créer des employés en cache avant besoin
- Pre-générer des outils courants
- Machine learning pour prédire les besoins

## Conclusion

Le système Cortex MXMCorp est maintenant **entièrement dynamique**, **auto-extensible**, et **auto-outillé**.

**Caractéristiques clés:**
- ✅ CEO n'a AUCUNE compétence, délègue TOUJOURS
- ✅ Employés créés à la demande par RH
- ✅ Outils fabriqués à la demande par département Outils
- ✅ Système récursif (employés créent employés et outils)
- ✅ Optimisé pour les coûts minimaux
- ✅ Transparent et traçable

Le système peut maintenant **créer sa propre main-d'œuvre** et **fabriquer ses propres outils** selon les besoins, sans limite structurelle.
