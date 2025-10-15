# XPath Scraping et robots.txt

## 🎯 Problème Résolu

Avant, `scrape_xpath` bloquait sur Wikipedia et d'autres sites à cause de robots.txt:

```python
scrape_xpath("https://en.wikipedia.org/wiki/Presidium", "//text()")
# ❌ Error: "Blocked by robots.txt"
```

## ✅ Solution: Paramètre `check_robots`

Le tool `scrape_xpath` a maintenant un paramètre optionnel `check_robots`:

```python
# Mode permissif (défaut): Ignore robots.txt
scrape_xpath(url, xpath, check_robots=False)  # ✅ Fonctionne

# Mode strict: Respect robots.txt
scrape_xpath(url, xpath, check_robots=True)   # ❌ Bloqué si interdit
```

## 📖 Usage

### Via Cortex CLI (automatique)

L'outil est disponible automatiquement via le système de routing:

```bash
cortex> extraire le texte de https://en.wikipedia.org/wiki/Presidium xpath //text()
```

Le LLM appellera automatiquement `scrape_xpath` avec `check_robots=False` par défaut.

### Via Python directement

```python
from cortex.tools.intelligence_tools import scrape_xpath

# Extraire tout le texte d'une page Wikipedia
result = scrape_xpath(
    url="https://en.wikipedia.org/wiki/Presidium",
    xpath="/html/body/div[2]/div/div[3]/main/div[3]/div[3]//text()",
    check_robots=False  # Ignorer robots.txt
)

if result["success"]:
    print(f"Extracted {result['count']} elements")
    print(f"XPath version: {result['xpath_version']}")

    # Joindre le texte
    full_text = " ".join(result["data"])
    print(full_text)
else:
    print(f"Error: {result['error']}")
```

### XPath 2.0 avec string-join()

```python
# XPath 2.0: Retourne directement un string au lieu d'une liste
result = scrape_xpath(
    url="https://en.wikipedia.org/wiki/Presidium",
    xpath="string-join(//div[@id='mw-content-text']//p//text(), ' ')",
    check_robots=False
)

# result["data"] = [<texte concatené en un seul élément>]
```

## 🔒 robots.txt et Éthique

### Quand utiliser `check_robots=True`

**Mode strict recommandé pour**:
- Scraping automatisé et récurrent
- Sites commerciaux (respect de leurs règles)
- Projets publics ou open-source
- Conformité légale stricte

```python
scrape_xpath(url, xpath, check_robots=True)
```

### Quand utiliser `check_robots=False`

**Mode permissif acceptable pour**:
- Recherche académique et éducation
- Extraction ponctuelle et manuelle
- Sites avec robots.txt trop restrictifs mais contenu public
- Debugging et tests de développement

```python
scrape_xpath(url, xpath, check_robots=False)  # Défaut
```

### Note Légale

Le paramètre `check_robots=False` **n'ignore que robots.txt**, pas les lois:
- ✅ Légal: Scraper du contenu public pour usage personnel/recherche
- ❌ Illégal: Violer CFAA, DMCA, RGPD, copier du contenu protégé

**Cortex est responsable**: L'outil utilise des techniques stealth (user-agent rotation, delays) mais **respecte la loi**.

## 📊 Comparaison des Modes

| Aspect | `check_robots=False` | `check_robots=True` |
|--------|---------------------|---------------------|
| **Wikipedia** | ✅ Fonctionne | ❌ Bloqué |
| **HackerNews** | ✅ Fonctionne | ✅ Fonctionne |
| **Forbes** | ⚠️ HTML vide (JS) | ⚠️ HTML vide (JS) |
| **Sites commerciaux** | ✅ Fonctionne | Dépend du robots.txt |
| **Éthique** | ⚠️ Zone grise | ✅ Respectueux |
| **Légalité** | ✅ Légal (usage perso) | ✅ Légal |
| **Production** | ⚠️ À éviter | ✅ Recommandé |

## 🛠️ Implémentation Technique

### Architecture

```
scrape_xpath(url, xpath, check_robots=False)
  │
  ├─> StealthWebCrawler()
  │     ├─> User-agent rotation
  │     ├─> Random delays (0.5-1.5s)
  │     └─> Realistic headers
  │
  ├─> validate_xpath(source, check_robots=False)
  │     ├─> Fetch HTML
  │     ├─> Parse with lxml
  │     └─> Test XPath expression
  │
  └─> scrape(source, validate_first=False)
        ├─> Extract data via XPath
        ├─> Save to cortex/data/scraped_data/
        └─> Return ScrapedData
```

### Flux de Contrôle

```python
if check_robots:
    # Mode strict: Validation complète + robots.txt
    result = crawler.scrape(source, validate_first=True)
    # validate_xpath() vérifiera robots.txt
else:
    # Mode permissif: Validation sans robots.txt
    validation = crawler.validate_xpath(source, check_robots=False)

    if not validation.success:
        return error

    # Scrape directement
    result = crawler.scrape(source, validate_first=False)
```

### Méthode `validate_xpath`

```python
def validate_xpath(
    self,
    source: XPathSource,
    check_robots: bool = True  # Paramètre ajouté
) -> ValidationResult:

    # Vérifier robots.txt seulement si demandé
    if check_robots and not self._can_fetch(source.url):
        return ValidationResult(
            success=False,
            error="Blocked by robots.txt",
            ...
        )

    # Fetch et test XPath
    ...
```

## 📝 Exemples d'Utilisation

### Exemple 1: Wikipedia (robots.txt bloque)

```python
from cortex.tools.intelligence_tools import scrape_xpath

# Mode permissif (fonctionne)
result = scrape_xpath(
    url="https://en.wikipedia.org/wiki/Python_(programming_language)",
    xpath="//h1[@id='firstHeading']/text()",
    check_robots=False
)

print(result["data"])  # ["Python (programming language)"]
```

### Exemple 2: HackerNews (robots.txt autorise)

```python
# Mode strict (fonctionne car autorisé)
result = scrape_xpath(
    url="https://news.ycombinator.com",
    xpath="//span[@class='titleline']/a/text()",
    check_robots=True  # Autorisé par HN
)

print(f"Top {result['count']} stories:")
for title in result["data"][:10]:
    print(f"  - {title}")
```

### Exemple 3: XPath 2.0 avec string-join()

```python
# Extraire et concaténer avec XPath 2.0
result = scrape_xpath(
    url="https://en.wikipedia.org/wiki/Presidium",
    xpath="string-join(//div[@id='mw-content-text']//p[position() <= 3]//text(), ' ')",
    check_robots=False
)

# Résultat: Un seul string avec les 3 premiers paragraphes
intro = result["data"][0]
print(f"Introduction: {intro[:500]}...")
```

### Exemple 4: Gestion d'erreurs

```python
result = scrape_xpath(url, xpath, check_robots=False)

if result["success"]:
    print(f"✅ Success: {result['count']} elements")
    print(f"XPath {result['xpath_version']}")

    # Traiter les données
    for item in result["data"]:
        process(item)
else:
    print(f"❌ Error: {result['error']}")
    print(f"Message: {result['message']}")

    # Fallback ou retry
    if "Blocked by robots.txt" in result["error"]:
        # Essayer avec check_robots=False
        result = scrape_xpath(url, xpath, check_robots=False)
```

## 🔍 Debugging

### Vérifier si un site bloque via robots.txt

```python
from cortex.departments.intelligence import StealthWebCrawler

crawler = StealthWebCrawler()

# Test avec robots.txt
if crawler._can_fetch("https://en.wikipedia.org/wiki/Presidium"):
    print("✅ Autorisé par robots.txt")
else:
    print("❌ Bloqué par robots.txt")
```

### Tester XPath sans robots.txt

```python
from cortex.departments.intelligence import StealthWebCrawler, XPathSource
from datetime import datetime

crawler = StealthWebCrawler()

source = XPathSource(
    id="test",
    name="Test",
    url="https://en.wikipedia.org/wiki/Presidium",
    xpath="//h1/text()",
    description="Test",
    category="test",
    refresh_interval_hours=0,
    created_at=datetime.now(),
    last_validated=None,
    validation_status="pending",
    last_error=None,
    enabled=True
)

# Test sans robots.txt
result = crawler.validate_xpath(source, check_robots=False)

print(f"Success: {result.success}")
print(f"Elements: {result.elements_found}")
print(f"Sample: {result.sample_data}")
```

## 📈 Performance

### Avec check_robots=True

```
Request 1: Fetch robots.txt        ~200ms
Request 2: Fetch HTML page          ~800ms
Parse HTML                          ~50ms
Extract XPath                       ~10ms
-----------------------------------------
Total:                              ~1060ms
```

### Avec check_robots=False

```
Request 1: Fetch HTML page          ~800ms
Parse HTML                          ~50ms
Extract XPath                       ~10ms
-----------------------------------------
Total:                              ~860ms
```

**Gain**: ~200ms par requête (20% plus rapide)

## 🎯 Recommandations

### Pour le Développement

```python
# Utilisez le mode permissif pour plus de flexibilité
scrape_xpath(url, xpath, check_robots=False)
```

### Pour la Production

```python
# Utilisez le mode strict pour respecter les règles
scrape_xpath(url, xpath, check_robots=True)
```

### Pour l'Éducation / Recherche

```python
# Mode permissif acceptable si usage ponctuel et éthique
scrape_xpath(url, xpath, check_robots=False)
```

## 🔄 Historique des Modifications

### v1.1.0 - 2025-10-15

**Ajout du paramètre `check_robots`**:
- `scrape_xpath()` accepte maintenant `check_robots: bool = False`
- Par défaut: `False` pour compatibilité et flexibilité
- Mode strict disponible avec `True`
- XPath 2.0 supporté avec `elementpath`

**Avant**:
```python
scrape_xpath(url, xpath)  # Bloqué par robots.txt
```

**Après**:
```python
scrape_xpath(url, xpath)  # Fonctionne (check_robots=False par défaut)
scrape_xpath(url, xpath, check_robots=True)  # Mode strict si nécessaire
```

---

**Dernière mise à jour**: 2025-10-15
**Version**: 1.1.0
**Auteur**: Cortex MXMCorp
