# Communication Department

Communication, Routage

## Agents

- **CommunicationsAgent** (NANO): Résume workflows avec thinking transparent pour l'utilisateur
- **TriageAgent** (NANO): Routage initial des requêtes utilisateur
- **SmartRouterAgent** (NANO): Route requêtes vers départements appropriés

## Structure

```
communication/
  agents/
    [agent_name]/
      base_prompt.md  # Prompt de base et logique
      memory.json     # Mémoire interne persistante
      __init__.py     # Import depuis cortex/agents/
```

## Philosophy

Chaque agent dans ce département a:
- **Autonomie**: Son propre dossier avec prompt et mémoire
- **Spécialisation**: Rôle clair dans le département
- **Traçabilité**: Historique d'exécutions dans memory.json
- **Évolution**: Base prompt évolutif selon apprentissages

## Memory System

La mémoire interne (`memory.json`) stocke:
- Historique des exécutions
- Patterns détectés au fil du temps
- Décisions antérieures et leur contexte
- Métriques de performance

Cette mémoire permet aux agents d'apprendre et de s'améliorer.
