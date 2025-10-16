# Direct Scrape vs Cortex CLI - Pourquoi utiliser l'un ou l'autre?

## 🎯 Votre Question

> "Quand je passe par scrape_xpath, ça passe par l'API OpenAI? C'est absurde, on pourrait pomper l'URL directement sans LLM et aller chercher le texte avec une librairie locale. Pourquoi par l'API on peut pomper wiki mais pas avec un outil maison? Qu'est-ce qu'il manque?"

## ✅ Vous Aviez 100% Raison!

Le scraping **se fait déjà localement** avec `requests` + `lxml` + `elementpath`. L'API LLM n'est utilisée que pour:
1. Identifier quel tool appeler
2. Formatter la réponse en markdown

**C'est effectivement absurde de payer pour ça!**

## 📊 Comparaison: Cortex CLI vs direct_scrape

### Cortex CLI (via LLM)

```bash
python3 cortex.py
mxm> extraire le texte de https://en.wikipedia.org/wiki/Presidium xpath //h1/text()
```

**Flux d'exécution**:
```
User: "extraire texte de wikipedia..."
  ↓
LLM via OpenAI API ($$$) ← Analyse la requête, identifie le tool
  ↓
scrape_xpath() → requests + lxml (LOCAL, GRATUIT!)
  ↓
LLM via OpenAI API ($$$) ← Formatte la réponse
  ↓
Résultat affiché
```

**Coût**: ~$0.005 par scrape
**Temps**: 5-15 secondes
**Avantages**: Interface conversationnelle, langage naturel
**Inconvénients**: Coûteux, lent, difficile à scripter

### direct_scrape (100% local)

```bash
python3 -m cortex.tools.direct_scrape \
  "https://en.wikipedia.org/wiki/Presidium" \
  "//h1/text()"
```

**Flux d'exécution**:
```
User lance la commande
  ↓
scrape_xpath() → requests + lxml (LOCAL, GRATUIT!) ← PAS DE LLM!
  ↓
Résultat affiché
```

**Coût**: $0.00 (100% gratuit!)
**Temps**: 1-3 secondes
**Avantages**: Gratuit, rapide, facile à scripter
**Inconvénients**: Syntaxe XPath requise (pas de langage naturel)

## 📈 Tableau Comparatif Détaillé

| Aspect | Cortex CLI | direct_scrape | Gagnant |
|--------|------------|---------------|---------|
| **Coût** | ~$0.005/scrape | $0.00 | ✅ direct_scrape |
| **Vitesse** | 5-15s | 1-3s | ✅ direct_scrape |
| **API requise** | OpenAI/DeepSeek | Aucune | ✅ direct_scrape |
| **Langage naturel** | ✅ Oui | ❌ Non | ✅ Cortex CLI |
| **Scripting** | Difficile | Facile | ✅ direct_scrape |
| **XPath 2.0** | ✅ Oui | ✅ Oui | Égalité |
| **Stealth crawler** | ✅ Oui | ✅ Oui | Égalité |
| **robots.txt** | Configurable | Configurable | Égalité |
| **Formatting** | Markdown riche | JSON/Text/List | ✅ Cortex CLI |
| **Offline** | ❌ Non | ✅ Oui | ✅ direct_scrape |

## 🎓 Quand Utiliser Quoi?

### Utilisez **Cortex CLI** quand:

✅ Vous voulez utiliser le langage naturel
```
mxm> trouve-moi les titres de HackerNews
mxm> compare les prix sur cette page e-commerce
mxm> résume les 3 premiers paragraphes de Wikipedia
```

✅ Vous voulez une réponse formatée et contextualisée
```
mxm> analyse les tendances des titres HackerNews et identifie les sujets populaires
```

✅ Vous voulez combiner plusieurs outils
```
mxm> scrape wikipedia, extrait les sections, et crée un fichier markdown résumé
```

✅ Vous explorez et ne connaissez pas l'XPath exact
```
mxm> extraire les informations principales de cette page
```

### Utilisez **direct_scrape** quand:

✅ Vous connaissez l'XPath exact
```bash
python3 -m cortex.tools.direct_scrape URL "//h1/text()"
```

✅ Vous voulez économiser (gratuit vs $0.005)
```bash
# 1000 scrapes: $0 vs $5 avec Cortex CLI
for url in urls.txt; do
  python3 -m cortex.tools.direct_scrape "$url" "//title/text()"
done
```

✅ Vous voulez de la vitesse (1-3s vs 5-15s)
```bash
# Monitoring en temps réel
while true; do
  python3 -m cortex.tools.direct_scrape URL XPATH
  sleep 60
done
```

✅ Vous scriptez ou automatisez
```bash
# Cron job pour surveillance
*/5 * * * * python3 -m cortex.tools.direct_scrape URL XPATH -o /var/log/scrape.json
```

✅ Vous travaillez offline (pas de connexion API)
```bash
# Pas besoin d'internet (sauf pour l'URL à scraper)
python3 -m cortex.tools.direct_scrape "https://example.com" "//text()"
```

## 💡 Exemples Concrets

### Exemple 1: Exploration (Cortex CLI)

```bash
python3 cortex.py
mxm> analyse la page wikipedia presidium et dis-moi de quoi ça parle
```

**Résultat**:
- LLM scrape la page
- LLM analyse le contenu
- LLM génère un résumé contextualisé
- **Coût**: ~$0.01-0.05
- **Temps**: 10-20s

**Quand**: Vous découvrez un sujet et voulez une analyse rapide

### Exemple 2: Extraction Précise (direct_scrape)

```bash
python3 -m cortex.tools.direct_scrape \
  "https://en.wikipedia.org/wiki/Presidium" \
  "//h1[@id='firstHeading']/text()"
```

**Résultat**:
- Extraction directe du titre
- **Coût**: $0.00
- **Temps**: 1-2s

**Quand**: Vous savez exactement ce que vous voulez extraire

### Exemple 3: Monitoring (direct_scrape)

```bash
#!/bin/bash
# Surveiller les prix toutes les 5 minutes
while true; do
  python3 -m cortex.tools.direct_scrape \
    "https://example-shop.com/product" \
    "//span[@class='price']/text()" \
    -o price_$(date +%Y%m%d_%H%M%S).json
  sleep 300
done
```

**Avantages**:
- Gratuit (vs $288/jour avec Cortex CLI à 1 req/5min)
- Rapide
- Facilement automatisable

### Exemple 4: Batch Processing (direct_scrape)

```python
# scrape_batch.py
from cortex.tools.direct_scrape import batch_scrape

sources = [
    {"url": "https://site1.com", "xpath": "//title/text()", "name": "Site 1"},
    {"url": "https://site2.com", "xpath": "//h1/text()", "name": "Site 2"},
    {"url": "https://site3.com", "xpath": "//p[1]/text()", "name": "Site 3"},
]

results = batch_scrape(sources, xpath_version="2.0")

# Analyse les résultats
for result in results:
    if result["success"]:
        print(f"{result['source_name']}: {result['count']} elements")
    else:
        print(f"{result['source_name']}: FAILED - {result['error']}")
```

**Coût**: $0.00 (vs $0.015 avec Cortex CLI)

## 🔧 Guide d'Utilisation de direct_scrape

### Installation

Rien à installer - déjà inclus dans Cortex!

### Usage de Base

```bash
# Syntaxe
python3 -m cortex.tools.direct_scrape URL XPATH [OPTIONS]

# Exemple simple
python3 -m cortex.tools.direct_scrape \
  "https://example.com" \
  "//h1/text()"
```

### Options Disponibles

```bash
--xpath-version {1.0,2.0}  # Version XPath (default: 2.0)
--format {json,text,list}  # Format de sortie (default: json)
--check-robots             # Vérifier robots.txt (default: ignore)
-o, --output FILE          # Sauvegarder dans un fichier
```

### Exemples Avancés

#### XPath 2.0 avec string-join

```bash
python3 -m cortex.tools.direct_scrape \
  "https://en.wikipedia.org/wiki/Presidium" \
  "string-join(//p[position() <= 3]//text(), ' ')" \
  --xpath-version 2.0
```

#### Format texte brut

```bash
python3 -m cortex.tools.direct_scrape \
  "https://en.wikipedia.org/wiki/Presidium" \
  "//h1/text()" \
  --format text
```

#### Sauvegarder dans un fichier

```bash
python3 -m cortex.tools.direct_scrape \
  "https://example.com" \
  "//text()" \
  -o output.json
```

#### Mode strict avec robots.txt

```bash
python3 -m cortex.tools.direct_scrape \
  "https://example.com" \
  "//h1/text()" \
  --check-robots
```

## 📊 Analyse de Coûts Réels

### Scénario 1: Veille Quotidienne

**Tâche**: Scraper 100 URLs par jour

**Avec Cortex CLI**:
- Coût: 100 × $0.005 = **$0.50/jour**
- Mensuel: **$15/mois**
- Annuel: **$180/an**

**Avec direct_scrape**:
- Coût: 100 × $0.00 = **$0.00/jour**
- Mensuel: **$0/mois**
- Annuel: **$0/an**

**Économies**: **$180/an**

### Scénario 2: Monitoring Intensif

**Tâche**: Scraper 1 URL toutes les 5 minutes (288/jour)

**Avec Cortex CLI**:
- Coût: 288 × $0.005 = **$1.44/jour**
- Mensuel: **$43.20/mois**
- Annuel: **$518.40/an**

**Avec direct_scrape**:
- Coût: **$0/an**

**Économies**: **$518/an**

### Scénario 3: Batch Processing

**Tâche**: Scraper 10,000 URLs une fois

**Avec Cortex CLI**:
- Coût: 10,000 × $0.005 = **$50**
- Temps: 10,000 × 10s = ~28 heures

**Avec direct_scrape**:
- Coût: **$0**
- Temps: 10,000 × 2s = ~5.5 heures

**Économies**: **$50 + 22.5 heures**

## 🚀 Migration de Cortex CLI vers direct_scrape

Si vous utilisez déjà Cortex CLI et voulez économiser:

### Avant (Cortex CLI)

```bash
python3 cortex.py
mxm> extraire le texte de https://example.com xpath //h1/text()
```

### Après (direct_scrape)

```bash
python3 -m cortex.tools.direct_scrape \
  "https://example.com" \
  "//h1/text()"
```

### Script de Conversion

```bash
#!/bin/bash
# convert_to_direct_scrape.sh

# Remplacer vos appels Cortex CLI par direct_scrape
URL="$1"
XPATH="$2"

# Avant: echo "extraire texte de $URL xpath $XPATH" | python3 cortex.py
# Après:
python3 -m cortex.tools.direct_scrape "$URL" "$XPATH"
```

## ❓ FAQ

### Q: Le scraping était déjà local avec Cortex CLI?

**R**: OUI! Le scraping lui-même (requests + lxml) était déjà local. Mais Cortex CLI ajoute:
1. Appel LLM pour identifier le tool (~$0.002)
2. Appel LLM pour formater la réponse (~$0.003)
3. Total: ~$0.005

`direct_scrape` supprime ces deux appels LLM inutiles.

### Q: Pourquoi Cortex CLI passe par le LLM alors?

**R**: Pour permettre le **langage naturel**:
- "trouve les titres de cette page"
- "compare les prix"
- "résume les 3 premiers paragraphes"

Le LLM traduit ça en appels de tools. C'est pratique mais coûteux.

### Q: Peut-on utiliser les deux?

**R**: OUI! C'est même recommandé:
- **Cortex CLI**: Exploration, analyses complexes, langage naturel
- **direct_scrape**: Extraction précise, automatisation, économies

### Q: direct_scrape est plus limité?

**R**: Non! Il a les mêmes capacités de scraping:
- XPath 2.0 ✅
- Stealth crawler ✅
- robots.txt configurable ✅
- Formats multiples ✅

Il manque juste:
- Langage naturel ❌
- Formatage Markdown ❌
- Combinaison multi-tools ❌

### Q: Comment débugger mes XPaths?

**R**: Testez avec direct_scrape d'abord (gratuit et rapide):

```bash
# Test rapide
python3 -m cortex.tools.direct_scrape URL "//h1" --format text

# Si ça ne fonctionne pas
python3 -m cortex.tools.direct_scrape URL "//h1/text()" --format text

# XPath 2.0
python3 -m cortex.tools.direct_scrape URL "//h1[1]/text()" --xpath-version 2.0
```

Une fois l'XPath validé, utilisez-le dans Cortex CLI si besoin de langage naturel.

## 🎯 Conclusion

### TL;DR

| Si vous voulez... | Utilisez... |
|-------------------|-------------|
| Langage naturel | Cortex CLI |
| Économiser de l'argent | direct_scrape |
| Être rapide | direct_scrape |
| Explorer un site | Cortex CLI |
| Scripter/automatiser | direct_scrape |
| Analyses complexes | Cortex CLI |
| Extraction simple | direct_scrape |
| Travailler offline | direct_scrape |

### Le Meilleur des Deux Mondes

1. **Explorez avec Cortex CLI** (langage naturel)
   ```
   mxm> trouve les informations principales de cette page
   ```

2. **Notez l'XPath exact** que Cortex CLI a utilisé

3. **Automatisez avec direct_scrape** (gratuit)
   ```bash
   python3 -m cortex.tools.direct_scrape URL "XPATH_EXACT"
   ```

### Réponse Finale

**Ce qui manquait**: Un outil CLI direct qui ne passe pas par le LLM.

**Maintenant vous l'avez**: `direct_scrape` - 100% local, 100% gratuit, XPath 2.0!

---

**Dernière mise à jour**: 2025-10-15
**Version**: 1.0
**Auteur**: Cortex MXMCorp
