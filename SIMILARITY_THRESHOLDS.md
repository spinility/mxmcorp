# Système de Seuils de Similarité Adaptatifs

## Vue d'ensemble

Le système de seuils de similarité adaptatifs filtre intelligemment les résultats de recherche sémantique basé sur la **gravité de la tâche**. Plus une tâche est critique, plus les seuils sont stricts pour garantir que seul le contexte le plus pertinent est inclus.

## Motivation

**Problème**: Dans un système d'embeddings, tous les résultats de recherche ne sont pas également pertinents. Utiliser du contexte peu pertinent peut:
- Diluer l'information importante
- Conduire à des erreurs dans les tâches critiques
- Gaspiller le budget de tokens

**Solution**: Ajuster dynamiquement le seuil de similarité selon la gravité de la tâche.

## Niveaux de Gravité

### 🔴 CRITICAL (Critique)
**Seuil**: 0.60 (très strict)
**Min résultats**: 1

**Utilisation**:
- Production deployments
- Sécurité (authentication, authorization, encryption)
- Données sensibles (passwords, API keys, secrets)
- Migrations de base de données
- Paiements

**Comportement**:
- Seulement les matchs très similaires (distance ≤ 0.60)
- Rejette les résultats moyennement pertinents
- Garantit au moins 1 résultat même si faible

**Exemple**:
```python
context = builder.build_context(
    "Fix authentication vulnerability in production",
    severity=TaskSeverity.CRITICAL
)
```

### 🟠 HIGH (Élevée)
**Seuil**: 0.85 (strict)
**Min résultats**: 2

**Utilisation**:
- APIs publiques
- Fonctionnalités user-facing
- Core features
- Fonctionnalités importantes

**Comportement**:
- Accepte les matchs assez similaires (distance ≤ 0.85)
- Balance qualité et couverture
- Garantit au moins 2 résultats

**Exemple**:
```python
context = builder.build_context(
    "Add new public API endpoint for users",
    severity=TaskSeverity.HIGH
)
```

### 🟡 MEDIUM (Moyenne) - **Défaut**
**Seuil**: 1.10 (standard)
**Min résultats**: 2

**Utilisation**:
- Fonctionnalités standard
- Nouvelles features
- Améliorations
- Tâches générales

**Comportement**:
- Accepte les matchs pertinents (distance ≤ 1.10)
- Équilibre standard entre qualité et quantité
- Défaut pour la plupart des tâches

**Exemple**:
```python
# Utilise MEDIUM par défaut
context = builder.build_context("Create new dashboard feature")
```

### 🟢 LOW (Faible)
**Seuil**: 1.50 (permissif)
**Min résultats**: 3

**Utilisation**:
- Refactoring
- Documentation
- Tests
- Cleanup
- Commentaires
- Formatting

**Comportement**:
- Accepte tous les matchs raisonnables (distance ≤ 1.50)
- Maximise la couverture
- Garantit au moins 3 résultats

**Exemple**:
```python
context = builder.build_context(
    "Refactor code and add comments",
    severity=TaskSeverity.LOW
)
```

## Comment ça marche

### 1. Distance de Similarité

ChromaDB utilise la distance L2 (Euclidean) entre embeddings:
- **0.0** = Identique
- **0.0 - 0.8** = Très pertinent
- **0.8 - 1.2** = Pertinent
- **> 1.2** = Peu pertinent

Plus la distance est **petite**, plus c'est similaire.

### 2. Filtrage par Seuil

Pour chaque résultat de recherche:
```python
if distance <= threshold:
    # Accepter le résultat
else:
    # Rejeter le résultat (sauf si < min_results)
```

### 3. Garantie Minimale

Même si tous les résultats sont au-dessus du seuil, le système garantit un minimum de résultats:
- CRITICAL: Au moins 1
- HIGH: Au moins 2
- MEDIUM: Au moins 2
- LOW: Au moins 3

Ceci évite d'avoir un contexte vide sur des tâches nouvelles.

### 4. Évaluation de Qualité

Chaque résultat accepté reçoit une évaluation:
- **excellent**: distance ≤ threshold × 0.5
- **good**: distance ≤ threshold × 0.75
- **acceptable**: distance ≤ threshold
- **weak**: distance > threshold (accepté pour min_results)

## Usage

### Détection Automatique

Le système peut détecter automatiquement la gravité basée sur des mots-clés:

```python
from cortex.core.smart_context_builder import SmartContextBuilder

builder = SmartContextBuilder(project_root=Path.cwd())

# Détecte automatiquement CRITICAL
task = "Fix authentication vulnerability in production"
severity = builder.detect_task_severity(task)
# -> TaskSeverity.CRITICAL

context = builder.build_context(task, severity=severity)
```

**Mots-clés par gravité**:
- **CRITICAL**: production, security, authentication, password, encryption, api key, secret, critical, urgent
- **HIGH**: api, endpoint, public, user-facing, important, core feature, main, primary
- **LOW**: refactor, documentation, comment, test, rename, format, cleanup, typo, style
- **MEDIUM**: Tout le reste (défaut)

### Spécification Manuelle

Pour un contrôle total:

```python
from cortex.core.smart_context_builder import SmartContextBuilder, TaskSeverity

builder = SmartContextBuilder(project_root=Path.cwd())

# Forcer CRITICAL
context = builder.build_context(
    task="Update payment processing",
    severity=TaskSeverity.CRITICAL
)
```

### Avec Rapport de Qualité

Pour inclure les métriques dans le contexte:

```python
context = builder.build_context(
    task="Fix authentication bug",
    severity=TaskSeverity.CRITICAL,
    include_quality_report=True
)

# Le contexte inclut maintenant:
# [CONTEXT QUALITY REPORT]
# Task Severity: CRITICAL
# Similarity Threshold: 0.60
# Total Results Found: 8
# Results Filtered Out: 5
# ...
```

### Obtenir le Rapport Après

Pour analyser la qualité sans l'inclure dans le contexte:

```python
context = builder.build_context(task, severity=TaskSeverity.HIGH)

# Obtenir le rapport
quality = builder.get_last_quality_report()

print(f"Threshold: {quality['threshold']}")
print(f"Total found: {quality['total_count']}")
print(f"Filtered out: {quality['filtered_count']}")
print(f"Acceptance rate: {(quality['total_count'] - quality['filtered_count']) / quality['total_count'] * 100:.1f}%")

# Par type
for search_type, stats in quality['results_by_type'].items():
    if stats['found'] > 0:
        avg_dist = sum(stats['distances']) / len(stats['distances'])
        print(f"{search_type}: {stats['accepted']}/{stats['found']} (avg: {avg_dist:.2f})")

# Warnings
for warning in quality['warnings']:
    print(f"⚠️  {warning}")
```

## Exemple Complet

```python
from pathlib import Path
from cortex.core.smart_context_builder import SmartContextBuilder, TaskSeverity

# Initialize
builder = SmartContextBuilder(project_root=Path.cwd())

# Tâche critique
task = "Fix critical security bug in authentication system"

# Option 1: Auto-detect
severity = builder.detect_task_severity(task)  # -> CRITICAL

# Option 2: Manual
severity = TaskSeverity.CRITICAL

# Build context avec seuils stricts
context = builder.build_context(
    task=task,
    budget=900,
    severity=severity,
    include_quality_report=False
)

# Analyser la qualité
quality = builder.get_last_quality_report()

print(f"🔍 Context Quality Analysis:")
print(f"   Severity: {severity.value}")
print(f"   Threshold: {quality['threshold']:.2f}")
print(f"   Results: {quality['total_count'] - quality['filtered_count']}/{quality['total_count']}")

if quality['filtered_count'] > 0:
    print(f"   ⚠️  {quality['filtered_count']} results filtered (too dissimilar)")

if quality['warnings']:
    print(f"   ⚠️  {len(quality['warnings'])} warnings")
    for w in quality['warnings'][:3]:
        print(f"      - {w}")

# Utiliser le contexte avec nano
# nano peut maintenant travailler avec un contexte de haute qualité!
```

## Impact sur les Coûts

Le filtrage améliore la qualité sans augmenter les coûts:

### Sans Filtrage
```
Total results: 20
All accepted: 20
Context tokens: 1200
Quality: Mixed (some irrelevant)
```

### Avec Filtrage (CRITICAL)
```
Total results: 20
Accepted: 8 (threshold 0.60)
Filtered: 12 (too dissimilar)
Context tokens: 480
Quality: High (only relevant)
```

**Bénéfices**:
- ✅ Meilleure qualité de contexte
- ✅ Moins de tokens (60% reduction)
- ✅ Moins de coûts
- ✅ Moins d'erreurs sur tâches critiques

## Ajustement des Seuils

Les seuils par défaut peuvent être modifiés dans `SimilarityThresholds`:

```python
class SimilarityThresholds:
    THRESHOLDS = {
        TaskSeverity.CRITICAL: 0.60,   # Modifier ici
        TaskSeverity.HIGH: 0.85,
        TaskSeverity.MEDIUM: 1.1,
        TaskSeverity.LOW: 1.5
    }
```

**Guide d'ajustement**:
- **Plus strict** (< 0.60): Moins de résultats, qualité maximale
- **Plus permissif** (> 0.60): Plus de résultats, qualité variable
- **Recommandé**: Garder les valeurs par défaut et ajuster via severity

## Tests

Exécuter les tests:
```bash
python3 test_similarity_thresholds.py
```

**Tests inclus**:
1. Configuration des seuils
2. Détection automatique de gravité
3. Construction de contexte avec différentes gravités
4. Rapport de qualité complet
5. Comparaison des taux de filtrage
6. Évaluation de qualité

## Métriques de Qualité

### Acceptance Rate (Taux d'acceptation)
```
acceptance_rate = (total - filtered) / total × 100%
```

**Interprétation**:
- **90-100%**: Excellente similarité, peu de filtrage
- **60-90%**: Bonne similarité, filtrage modéré
- **30-60%**: Similarité moyenne, filtrage important
- **< 30%**: Faible similarité, tâche très spécifique

### Average Distance (Distance moyenne)
```
avg_distance = sum(distances) / len(distances)
```

**Interprétation**:
- **< 0.5**: Excellent match
- **0.5 - 0.8**: Bon match
- **0.8 - 1.2**: Match acceptable
- **> 1.2**: Match faible

## Meilleures Pratiques

### 1. Utiliser la Détection Auto pour la Plupart des Tâches
```python
severity = builder.detect_task_severity(task)
context = builder.build_context(task, severity=severity)
```

### 2. Forcer CRITICAL pour Tâches Sensibles
```python
# Même si auto-detect donne MEDIUM, forcer CRITICAL
if "production" in task or "security" in task:
    severity = TaskSeverity.CRITICAL
```

### 3. Monitorer les Warnings
```python
quality = builder.get_last_quality_report()
if quality['warnings']:
    log.warning(f"Context quality issues: {len(quality['warnings'])} warnings")
```

### 4. Analyser les Taux de Filtrage
```python
filtered_rate = quality['filtered_count'] / quality['total_count']
if filtered_rate > 0.7:  # 70% filtered
    log.info("High filtering rate - task may be very specific")
```

### 5. Utiliser LOW pour Tests/Docs
```python
# Pour refactoring, permettre plus de contexte
context = builder.build_context(
    "Refactor and document module",
    severity=TaskSeverity.LOW
)
```

## Comparaison avec l'Ancien Système

### Avant (Sans Seuils)
```python
# Accepte tous les résultats
results = kb.search(task, n_results=5)
# -> Peut inclure du contexte peu pertinent
```

### Après (Avec Seuils Adaptatifs)
```python
# Filtre selon gravité
context = builder.build_context(task, severity=TaskSeverity.CRITICAL)
# -> Seulement contexte très pertinent (distance ≤ 0.60)
```

**Différences**:
| Aspect | Sans Seuils | Avec Seuils |
|--------|-------------|-------------|
| Qualité | Variable | Contrôlée |
| Pertinence | Mixte | Garantie |
| Tokens | Fixes | Optimisés |
| Erreurs critiques | Possibles | Réduites |
| Flexibilité | Aucune | 4 niveaux |

## Conclusion

Le système de seuils adaptatifs offre:
- ✅ **Qualité contrôlée** selon la gravité
- ✅ **Flexibilité** (4 niveaux + auto-detect)
- ✅ **Sécurité** (seuils stricts pour tâches critiques)
- ✅ **Transparence** (rapports de qualité détaillés)
- ✅ **Efficacité** (moins de tokens, meilleure qualité)

**Résultat**: Nano peut maintenant travailler avec un contexte de haute qualité adapté à chaque tâche! 🚀
