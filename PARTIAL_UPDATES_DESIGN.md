# Intelligent Partial Updates System - Design Document

## Problème
Les LLMs réécrivent souvent des fichiers entiers même pour des changements mineurs, causant:
- Perte de qualité sur code non modifié
- Coût en tokens élevé
- Risques d'erreurs d'indentation
- Difficultés de review git

## Solution: Region-Based Partial Updates

### 1. Region Markers System

#### Marqueurs Automatiques
```python
# REGION: FunctionName [unique_id]
def function_name():
    # implementation
    pass
# END_REGION [unique_id]
```

#### Avantages
- ✅ Isolation claire des zones modifiables
- ✅ IDs uniques pour tracking
- ✅ Compatible avec tous les langages (via commentaires)
- ✅ Invisible pour l'exécution (commentaires)
- ✅ Facilite le diff git

### 2. Auto-Region Injection

Avant de demander une modification, analyser le fichier:

```python
class RegionAnalyzer:
    """Analyse et injecte des régions dans un fichier"""

    def analyze_file(self, filepath: str) -> List[CodeRegion]:
        """
        Détecte automatiquement les régions:
        - Fonctions (def, function, func, etc.)
        - Classes (class)
        - Méthodes
        - Blocs try/except
        - Sections logiques (commentaires de section)
        """

    def inject_regions(self, filepath: str) -> Dict[str, str]:
        """
        Injecte des markers de région
        Returns: {region_id: region_content}
        """

    def extract_region(self, filepath: str, region_id: str) -> str:
        """Extrait le contenu d'une région spécifique"""

    def replace_region(self, filepath: str, region_id: str, new_content: str):
        """Remplace le contenu d'une région en préservant le reste"""
```

### 3. Partial Update Instructions

Instructions injectées dans le prompt système:

```python
PARTIAL_UPDATE_SYSTEM_PROMPT = """
🎯 PARTIAL UPDATE MODE - CRITICAL RULES

You are modifying code in REGION-BASED UPDATE mode.

ABSOLUTE REQUIREMENTS:
1. Return ONLY the code inside the specified region
2. Do NOT include region markers (# REGION / # END_REGION) in your output
3. Do NOT modify or reference code outside the region
4. Do NOT add explanations, comments, or markdown formatting
5. Preserve exact indentation (match original)
6. If uncertain, return original content unchanged

REGION INFO:
- ID: {region_id}
- Description: {region_description}
- Lines: {start_line}-{end_line}

ORIGINAL REGION CONTENT:
```
{original_content}
```

YOUR SPECIFIC TASK:
{task_description}

OUTPUT FORMAT:
- Pure code only
- No markers
- No explanations
- Exact indentation match
"""
```

### 4. Quality Validation Pipeline

Après chaque update partiel:

```python
class UpdateValidator:
    """Valide la qualité d'un update partiel"""

    def validate_update(self, original: str, updated: str, region_id: str) -> ValidationResult:
        """
        Validations:
        1. Syntax check (AST parsing)
        2. Indentation consistency
        3. Only target region changed
        4. No corruption outside region
        5. Imports still valid
        6. No dangling references
        """

    def rollback_on_failure(self, filepath: str, region_id: str):
        """Rollback automatique si validation échoue"""

    def calculate_diff_score(self, original: str, updated: str) -> float:
        """
        Calcule un score de qualité:
        - 1.0 = parfait (seule région modifiée)
        - 0.5-0.9 = acceptable (quelques ajustements mineurs)
        - <0.5 = rejet (trop de changements)
        """
```

### 5. Multi-Region Updates

Pour des changements complexes touchant plusieurs fonctions:

```python
class MultiRegionUpdate:
    """Gère des updates sur plusieurs régions"""

    def plan_update(self, task: str, filepath: str) -> List[RegionUpdate]:
        """
        Analyse la tâche et identifie toutes les régions à modifier

        Example:
        Task: "Add authentication to API endpoints"
        Regions identified:
        - [auth_001]: add_user_endpoint
        - [auth_002]: login_endpoint
        - [auth_003]: verify_token_middleware
        """

    def execute_sequential(self, updates: List[RegionUpdate]) -> bool:
        """
        Exécute les updates séquentiellement avec validation:
        1. Update region 1
        2. Validate
        3. Update region 2
        4. Validate
        5. ...

        Si une validation échoue → rollback ALL
        """

    def create_dependency_graph(self, regions: List[str]) -> Graph:
        """
        Crée un graphe de dépendances entre régions
        Permet d'ordonnancer les updates intelligemment
        """
```

### 6. Integration avec LLM Client

```python
class PartialUpdateClient:
    """Client LLM spécialisé pour updates partiels"""

    def update_region(
        self,
        filepath: str,
        region_id: str,
        task_description: str,
        tier: ModelTier = ModelTier.DEEPSEEK
    ) -> UpdateResult:
        """
        1. Extract region content
        2. Build partial update prompt
        3. Call LLM
        4. Validate response
        5. Apply update
        6. Validate file integrity
        7. Return result with metrics
        """

    def suggest_regions(self, filepath: str, task: str) -> List[str]:
        """
        Utilise nano LLM pour suggérer quelles régions modifier

        Cost: ~$0.0001 (nano)
        Benefit: Évite de modifier tout le fichier
        """
```

## Exemple d'Utilisation

### Avant (Update Complet)
```python
# User request: "Add error handling to authenticate_user"

# LLM rewrites ENTIRE file (500 lines)
# Cost: 500 lines * 4 tokens/line * $0.001 = $2.00
# Risk: Corruption on lines 234-456 (unrelated code)
```

### Après (Update Partiel)
```python
# User request: "Add error handling to authenticate_user"

# 1. Identify region: [auth_001] authenticate_user (lines 45-67)
# 2. Extract region content (23 lines)
# 3. Send only region to LLM with partial update instructions
# 4. Receive updated region (27 lines, +4 lines error handling)
# 5. Validate: only [auth_001] changed ✓
# 6. Apply update
# 7. Validate file integrity ✓

# Cost: 27 lines * 4 tokens/line * $0.001 = $0.11
# Savings: 95% cost reduction
# Risk: ZERO corruption outside region
```

## Métriques de Succès

- **Cost Reduction**: 80-95% sur updates ciblés
- **Quality Preservation**: 100% du code non modifié intact
- **Accuracy**: >90% des updates appliqués correctement du premier coup
- **Safety**: Rollback automatique sur échec

## Limitations et Edge Cases

### Cas Complexes
1. **Refactoring multi-fichiers**: Nécessite coordination entre régions
2. **Renommage de variables globales**: Peut affecter plusieurs régions
3. **Changements de signature**: Doit propager aux appelants

### Solutions
- Détection automatique des impacts cross-region
- Mode "coordinated update" pour refactoring complexes
- Fallback au mode full-file si trop de régions impactées (>50% du fichier)

## Prochaines Étapes

1. ✅ Implémenter RegionAnalyzer
2. ✅ Créer PartialUpdateClient
3. ✅ Développer UpdateValidator
4. ✅ Intégrer dans PromptEngineer
5. ✅ Tests sur fichiers réels du projet
6. ✅ Mesurer cost savings et quality preservation
