# Test: XPath sur Wikipedia - Résultats

## 🎯 Test Demandé

```
URL: https://en.wikipedia.org/wiki/Presidium
XPath: /html/body/div[2]/div/div[3]/main/div[3]/div[3]
```

## ✅ Résultats

### Test 1: XPath sans //text()
```xpath
/html/body/div[2]/div/div[3]/main/div[3]/div[3]
```

**Résultat**: ✅ Trouve 1 élément, mais **vide** (pas de texte extrait)

**Pourquoi?**: L'XPath pointe vers l'élément `<div>`, pas vers son texte. Pour extraire du texte, il faut utiliser `//text()` ou `string()`.

### Test 2: XPath avec //text()
```xpath
/html/body/div[2]/div/div[3]/main/div[3]/div[3]//text()
```

**Résultat**: ✅ **339 éléments de texte extraits**

**Contenu extrait**:
- **8,600 caractères**
- **~1,000 mots**
- **280 lignes de texte**

**Extrait du contenu**:
```
Type of governing body "Praesidium" redirects here. For the former Catholic
diocese, see Praesidium (bishopric). A presidium or praesidium is a council
of executive officers in some countries' political assemblies that collectively
administers its business, either alongside an individual president or in place
of one. The term is also sometimes used for the governing body of European
non-state organisations. Communist usage In Communist states the presidium is
the permanent committee of the legislative body...
```

### Test 3: XPath 2.0 avec string-join()
```xpath
string-join(/html/body/div[2]/div/div[3]/main/div[3]/div[3]//text(), " ")
```

**Résultat**: ✅ **Parfaitement fonctionnel!**

**Avantage**: Retourne un **string unique** au lieu d'une liste, plus facile à manipuler.

**Type retourné**: `<class 'str'>`

## 📊 Comparaison des Approches

| XPath | Résultat | Type | Utilité |
|-------|----------|------|---------|
| `/path/to/div` | ✅ 1 élément | Element | Obtenir l'élément DOM |
| `/path/to/div//text()` | ✅ 339 éléments | List[str] | Tous les textes séparés |
| `string-join(/path//text(), " ")` | ✅ String unique | str | Texte concaténé (XPath 2.0) |
| `/path/to/div/*` | ✅ 3 éléments | List[Element] | Enfants directs |
| `//h1[@id="firstHeading"]` | ✅ 1 élément | Element | Sélecteur intelligent |

## 🎓 Leçons Apprises

### 1. XPath de base vs XPath avec //text()

**Problème commun**:
```xpath
/html/body/div[2]/div[2]
```
☝️ Retourne l'élément `<div>`, mais **PAS son texte**!

**Solution**:
```xpath
/html/body/div[2]/div[2]//text()
```
☝️ Retourne **TOUT le texte** à l'intérieur du div et de ses descendants

### 2. XPath 2.0 string-join()

**Avantage**: Concatène automatiquement tous les textes en un seul string

```xpath
# XPath 1.0: Liste de strings
//div//text()  → ["Hello", " ", "World", "!"]

# XPath 2.0: String unique
string-join(//div//text(), " ")  → "Hello World !"
```

### 3. Wikipedia vs Forbes

| Site | Type | XPath fonctionne? | Raison |
|------|------|-------------------|--------|
| **Wikipedia** | HTML statique | ✅ Oui | Contenu dans le HTML initial |
| **Forbes** | JavaScript/SPA | ❌ Non | Contenu chargé après par JS |

## 🚀 Exemples d'Utilisation

### CLI Direct (sans LLM)

```bash
# XPath 1.0 - Liste de textes
python3 -m cortex.tools.direct_scrape \
  "https://en.wikipedia.org/wiki/Presidium" \
  "/html/body/div[2]/div/div[3]/main/div[3]/div[3]//text()" \
  --xpath-version 1.0

# XPath 2.0 - String unique
python3 -m cortex.tools.direct_scrape \
  "https://en.wikipedia.org/wiki/Presidium" \
  "string-join(/html/body/div[2]/div/div[3]/main/div[3]/div[3]//text(), ' ')" \
  --xpath-version 2.0
```

### Via Python

```python
from cortex.tools.intelligence_tools import scrape_xpath

# Extraire le texte
result = scrape_xpath(
    url="https://en.wikipedia.org/wiki/Presidium",
    xpath="/html/body/div[2]/div/div[3]/main/div[3]/div[3]//text()"
)

if result["success"]:
    print(f"Extracted {result['count']} text nodes")
    text = " ".join(result["data"])
    print(text)
```

### Via Cortex CLI (avec LLM)

```bash
cortex> extraire le texte de https://en.wikipedia.org/wiki/Presidium xpath //div[@id="mw-content-text"]//p
```

Le LLM appellera automatiquement `scrape_xpath` avec les bons paramètres.

## 💡 Recommandations

### Pour Wikipedia et sites statiques

✅ **Utilisez XPath** - C'est parfait!

**XPaths recommandés pour Wikipedia**:
```xpath
# Titre de la page
//h1[@id="firstHeading"]

# Premier paragraphe
//div[@id="mw-content-text"]//p[1]

# Tout le contenu principal
//div[@id="mw-content-text"]//text()

# Table des matières
//div[@id="toc"]//text()

# Infobox (si présente)
//table[@class="infobox"]//text()
```

### Pour sites JavaScript (Forbes, Twitter, etc.)

❌ **N'utilisez PAS XPath** - Cherchez l'API!

**Méthode**:
1. Ouvrir DevTools → Network tab
2. Filtrer par "XHR" ou "Fetch"
3. Recharger la page
4. Chercher les appels API JSON
5. Utiliser l'API directement

**Exemple Forbes**:
```bash
# Au lieu de XPath:
python3 -m cortex.tools.forbes_billionaires top -n 10
```

## 📈 Performance

### Wikipedia (XPath statique)

```
Test: /html/body/div[2]/div/div[3]/main/div[3]/div[3]//text()
✅ Success: True
⏱️  Response time: 1115ms
📊 Elements found: 339
📝 Total text: 8,600 characters (~1,000 words)
```

### Forbes (JavaScript)

```
Test: /html/body/div[2]/div[2]/div/...
❌ Success: False
⏱️  Response time: N/A
📊 Elements found: 0
💡 Solution: Use API (6.6MB JSON, 3,122 billionaires)
```

## 🔧 Debugging XPath

Si votre XPath ne fonctionne pas:

### 1. Vérifier la structure étape par étape

```python
# Test progressif
paths = [
    '/html/body',
    '/html/body/div',
    '/html/body/div[2]',
    '/html/body/div[2]/div',
]

for path in paths:
    elements = tree.xpath(path)
    print(f"{path}: {len(elements)} element(s)")
```

### 2. Chercher l'élément par ID ou classe

```xpath
# Au lieu de chemins absolus:
/html/body/div[2]/div[2]/div/div[2]...  ❌ Fragile

# Utilisez des sélecteurs robustes:
//div[@id="content"]  ✅ Stable
//div[@class="main-content"]  ✅ Stable
//article[@role="main"]  ✅ Sémantique
```

### 3. Tester dans le browser

1. Ouvrir DevTools (F12)
2. Console tab
3. Tester XPath:
   ```javascript
   $x("/html/body/div[2]//text()")
   ```

### 4. Utiliser des wildcards

```xpath
# Si la structure change souvent:
//div[contains(@class, "content")]//text()  # Flexible
//main//section[1]//p  # Premier paragraphe de toute section
//*[@id="main"]//text()  # N'importe quel élément avec id="main"
```

## ✅ Conclusion du Test

### Wikipedia: ✅ SUCCESS

- **XPath fonctionne parfaitement**
- **339 éléments extraits**
- **8,600 caractères de texte**
- **XPath 2.0 string-join() opérationnel**

### Pourquoi ça marche?

Wikipedia sert du **HTML statique complet**. Toutes les données sont présentes dans le HTML initial, pas besoin de JavaScript.

### Leçon principale

**Toujours vérifier**: Contenu statique ou dynamique?

```bash
curl -s URL | grep "votre_mot_clé"
```

- ✅ Trouvé → XPath fonctionne
- ❌ Pas trouvé → Chercher l'API

---

**Date**: 2025-10-15
**Status**: ✅ TEST RÉUSSI
**XPath Version**: 1.0 et 2.0 fonctionnels
