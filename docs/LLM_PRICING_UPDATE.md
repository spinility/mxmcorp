# Mise à jour des prix LLM

## 🎯 Problème

Les prix des modèles LLM changent régulièrement. Sans mise à jour, Cortex:
- Calcule des coûts incorrects
- Fait de mauvaises décisions de routing
- Peut dépasser le budget sans le savoir

## ✅ Solution: Outil de mise à jour automatisé

**Fichier**: `cortex/tools/update_llm_pricing.py`

### Fonctionnalités

1. **Afficher les prix actuels**
2. **Comparer avec les prix officiels**
3. **Mettre à jour les prix** (avec backup automatique)
4. **Historique des changements**

## 📊 Configuration des prix

Les prix sont stockés dans: **`cortex/config/models.yaml`**

```yaml
models:
  nano:
    name: "gpt-5-nano"
    cost_per_1m_input: 0.50   # $/1M tokens
    cost_per_1m_output: 1.50

  deepseek:
    name: "deepseek-reasoner"
    cost_per_1m_input: 0.55
    cost_per_1m_output: 2.19

  claude:
    name: "claude-sonnet-4-5"
    cost_per_1m_input: 3.0
    cost_per_1m_output: 15.0
```

## 🚀 Utilisation

### 1. Afficher les prix actuels

```bash
python3 -m cortex.tools.update_llm_pricing show
```

**Output**:
```
NANO - gpt-5-nano
  Input:  $0.50 / 1M tokens
  Output: $1.50 / 1M tokens

DEEPSEEK - deepseek-reasoner
  Input:  $0.55 / 1M tokens
  Output: $2.19 / 1M tokens

CLAUDE - claude-sonnet-4-5
  Input:  $3.00 / 1M tokens
  Output: $15.00 / 1M tokens
```

### 2. Comparer avec les prix officiels

```bash
python3 -m cortex.tools.update_llm_pricing compare
```

**Output**:
```
NANO
  Actuel:   $0.05 / $0.40
  Officiel: $0.50 / $1.50
  ⚠️  DIFFÉRENCE DÉTECTÉE!
     Input:  +0.45
     Output: +1.10
```

### 3. Mettre à jour un prix

```bash
# Mettre à jour input et output
python3 -m cortex.tools.update_llm_pricing update nano --input 0.50 --output 1.50

# Mettre à jour seulement l'input
python3 -m cortex.tools.update_llm_pricing update deepseek --input 0.55

# Simulation (dry-run)
python3 -m cortex.tools.update_llm_pricing update claude --input 4.0 --dry-run
```

**Output**:
```
✓ Backup créé: cortex/config/models.yaml.backup.20251015_193024
✓ Configuration sauvegardée: cortex/config/models.yaml
✓ Historique sauvegardé: cortex/data/pricing_history.json

Modèle: gpt-5-nano
Anciens prix:
  Input:  $0.05
  Output: $0.40
Nouveaux prix:
  Input:  $0.50 (+900.0%)
  Output: $1.50 (+275.0%)

✅ Prix mis à jour avec succès!
```

### 4. Voir l'historique

```bash
# Tout l'historique (10 dernières entrées)
python3 -m cortex.tools.update_llm_pricing history

# Filtrer par modèle
python3 -m cortex.tools.update_llm_pricing history --model nano

# Plus d'entrées
python3 -m cortex.tools.update_llm_pricing history --limit 50
```

**Output**:
```
2025-10-15T19:30:24
  Modèle: nano
  Input:  $0.05 → $0.50 (+900.0%)
  Output: $0.40 → $1.50 (+275.0%)

2025-10-15T19:30:29
  Modèle: deepseek
  Input:  $0.28 → $0.55 (+96.4%)
  Output: $0.42 → $2.19 (+421.4%)
```

## 🔒 Sécurité

### Backups automatiques

À chaque mise à jour, un backup est créé:
```
cortex/config/models.yaml.backup.20251015_193024
```

### Restaurer un backup

```bash
# Lister les backups
ls cortex/config/models.yaml.backup.*

# Restaurer
cp cortex/config/models.yaml.backup.20251015_193024 cortex/config/models.yaml
```

### Historique JSON

Toutes les modifications sont enregistrées dans:
```
cortex/data/pricing_history.json
```

Format:
```json
[
  {
    "timestamp": "2025-10-15T19:30:24.842571",
    "model": "nano",
    "old_prices": {"input": 0.05, "output": 0.40},
    "new_prices": {"input": 0.50, "output": 1.50},
    "change_input": 0.45,
    "change_output": 1.10,
    "change_percent_input": 900.0,
    "change_percent_output": 275.0
  }
]
```

## 📅 Fréquence de mise à jour recommandée

### Mensuelle (minimum)
Vérifier les prix une fois par mois:
```bash
python3 -m cortex.tools.update_llm_pricing compare
```

### Après annonces majeures
Quand un provider annonce des changements de prix:
- OpenAI blog: https://openai.com/blog
- Anthropic news: https://www.anthropic.com/news
- DeepSeek updates: https://platform.deepseek.com

### Automatisation (optionnel)

Créer un cron job pour vérifier automatiquement:

```bash
# crontab -e
# Vérifier les prix le 1er de chaque mois à 9h
0 9 1 * * cd /path/to/mxmcorp && python3 -m cortex.tools.update_llm_pricing compare
```

## 🌐 Sources officielles

### OpenAI (NANO)
- **URL**: https://openai.com/api/pricing/
- **Modèle actuel**: gpt-3.5-turbo (fallback for gpt-5-nano)
- **Prix**: $0.50 / $1.50 per 1M tokens
- **Note**: gpt-5-nano n'existe pas officiellement

### DeepSeek
- **URL**: https://platform.deepseek.com/api-docs/pricing/
- **Modèle**: deepseek-reasoner (DeepSeek V3)
- **Prix**: $0.55 / $2.19 per 1M tokens (cache miss)
- **Prix avec cache**: $0.055 / $2.19 (90% moins cher input!)

### Anthropic (Claude)
- **URL**: https://www.anthropic.com/pricing
- **Modèle**: Claude Sonnet 4.5
- **Prix**: $3.00 / $15.00 per 1M tokens
- **Context**: 200K tokens

## 💡 Impact des changements de prix

### Exemple de calcul

**Scénario**: 1000 requêtes/jour, 500 tokens input, 200 tokens output

#### Avant (prix incorrects):
```
NANO:  ($0.05 * 0.5 + $0.40 * 0.2) / 1000 = $0.000105/requête
Total/jour: $0.105
```

#### Après (prix corrects):
```
NANO: ($0.50 * 0.5 + $1.50 * 0.2) / 1000 = $0.000550/requête
Total/jour: $0.55
```

**Différence**: +$0.445/jour = **+$13.35/mois** = **+$160/an**

### Routing impacté

Avec de mauvais prix, le router peut choisir le mauvais modèle:
- Penser que NANO coûte $0.05 → L'utiliser partout
- En réalité NANO coûte $0.50 → Devrait utiliser plus DeepSeek pour certaines tâches

## ⚙️ Intégration continue

### Workflow recommandé

1. **Vérification mensuelle**:
   ```bash
   python3 -m cortex.tools.update_llm_pricing compare
   ```

2. **Si différence détectée**:
   - Vérifier les prix sur les sites officiels
   - Tester avec `--dry-run` d'abord
   - Mettre à jour

3. **Après mise à jour**:
   - Vérifier l'historique
   - Recalculer les budgets si nécessaire
   - Ajuster les alertes de coûts

### Notifications

Pour être alerté des changements de prix:

```python
# À implémenter: Webhook vers Slack/Discord/Email
def notify_price_change(model, old_price, new_price):
    # Envoyer notification
    pass
```

## 📝 Notes importantes

### gpt-5-nano n'existe pas

Le modèle configuré "gpt-5-nano" est un **placeholder**.
En réalité, le code utilise probablement **gpt-3.5-turbo**.

**Action recommandée**: Vérifier `cortex/core/llm_client.py` pour voir quel modèle est réellement utilisé.

### Cache DeepSeek

DeepSeek offre 90% de réduction sur l'input avec cache:
- **Cache miss**: $0.55 / 1M
- **Cache hit**: $0.055 / 1M

Si Cortex utilise le cache, ajuster le prix dans les calculs!

### Prompt caching Claude

Claude Sonnet 4 offre aussi du caching:
- Cache write: $3.75 / 1M
- Cache read: $0.30 / 1M (90% moins cher!)

## 🔮 Améliorations futures

- [ ] Fetch automatique depuis APIs officielles
- [ ] Notifications par email/Slack
- [ ] Dashboard de tendances des prix
- [ ] Prédiction des coûts futurs
- [ ] Intégration avec budgets Cortex
- [ ] Alertes si dépassement budget prévu

---

**Dernière mise à jour**: 2025-10-15
**Version**: 1.0
**Auteur**: Cortex MXMCorp
