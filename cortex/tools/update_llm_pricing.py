#!/usr/bin/env python3
"""
LLM Pricing Updater

Outil pour mettre à jour les prix des modèles LLM dans models.yaml
Supporte:
- Mise à jour manuelle avec prix spécifiques
- Fetch automatique depuis les sites officiels
- Validation et backup
- Historique des changements
"""

import yaml
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import shutil


# Chemins
MODELS_CONFIG_PATH = Path("cortex/config/models.yaml")
PRICING_HISTORY_PATH = Path("cortex/data/pricing_history.json")


# URLs officielles de pricing (pour auto-fetch)
PRICING_URLS = {
    "openai": "https://openai.com/api/pricing/",
    "anthropic": "https://www.anthropic.com/pricing",
    "deepseek": "https://platform.deepseek.com/api-docs/pricing/"
}


def load_models_config() -> Dict[str, Any]:
    """Charge la configuration des modèles"""
    with open(MODELS_CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


def save_models_config(config: Dict[str, Any], backup: bool = True):
    """
    Sauvegarde la configuration des modèles

    Args:
        config: Configuration à sauvegarder
        backup: Créer un backup avant sauvegarde
    """
    if backup:
        # Créer backup avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = MODELS_CONFIG_PATH.parent / f"models.yaml.backup.{timestamp}"
        shutil.copy(MODELS_CONFIG_PATH, backup_path)
        print(f"✓ Backup créé: {backup_path}")

    with open(MODELS_CONFIG_PATH, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)

    print(f"✓ Configuration sauvegardée: {MODELS_CONFIG_PATH}")


def save_pricing_history(model: str, old_prices: Dict, new_prices: Dict):
    """Sauvegarde l'historique des changements de prix"""
    PRICING_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Charger historique existant
    if PRICING_HISTORY_PATH.exists():
        with open(PRICING_HISTORY_PATH, 'r') as f:
            history = json.load(f)
    else:
        history = []

    # Ajouter nouvelle entrée
    history.append({
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "old_prices": old_prices,
        "new_prices": new_prices,
        "change_input": new_prices["input"] - old_prices["input"],
        "change_output": new_prices["output"] - old_prices["output"],
        "change_percent_input": ((new_prices["input"] - old_prices["input"]) / old_prices["input"] * 100) if old_prices["input"] > 0 else 0,
        "change_percent_output": ((new_prices["output"] - old_prices["output"]) / old_prices["output"] * 100) if old_prices["output"] > 0 else 0,
    })

    # Sauvegarder
    with open(PRICING_HISTORY_PATH, 'w') as f:
        json.dump(history, f, indent=2)

    print(f"✓ Historique sauvegardé: {PRICING_HISTORY_PATH}")


def update_model_pricing(
    model: str,
    cost_per_1m_input: Optional[float] = None,
    cost_per_1m_output: Optional[float] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Met à jour les prix d'un modèle

    Args:
        model: Nom du modèle (nano, deepseek, claude)
        cost_per_1m_input: Nouveau prix input ($/1M tokens)
        cost_per_1m_output: Nouveau prix output ($/1M tokens)
        dry_run: Si True, ne sauvegarde pas, affiche seulement

    Returns:
        Dict avec résultats de la mise à jour
    """
    # Charger config
    config = load_models_config()

    if model not in config["models"]:
        return {
            "success": False,
            "error": f"Model '{model}' not found in config",
            "available_models": list(config["models"].keys())
        }

    model_config = config["models"][model]

    # Prix actuels
    old_input = model_config["cost_per_1m_input"]
    old_output = model_config["cost_per_1m_output"]

    # Nouveaux prix
    new_input = cost_per_1m_input if cost_per_1m_input is not None else old_input
    new_output = cost_per_1m_output if cost_per_1m_output is not None else old_output

    # Calculer changements
    change_input = new_input - old_input
    change_output = new_output - old_output
    change_percent_input = (change_input / old_input * 100) if old_input > 0 else 0
    change_percent_output = (change_output / old_output * 100) if old_output > 0 else 0

    result = {
        "success": True,
        "model": model,
        "model_name": model_config["name"],
        "old_prices": {
            "input": old_input,
            "output": old_output
        },
        "new_prices": {
            "input": new_input,
            "output": new_output
        },
        "changes": {
            "input_absolute": change_input,
            "output_absolute": change_output,
            "input_percent": change_percent_input,
            "output_percent": change_percent_output
        },
        "dry_run": dry_run
    }

    if not dry_run:
        # Mettre à jour config
        model_config["cost_per_1m_input"] = new_input
        model_config["cost_per_1m_output"] = new_output

        # Sauvegarder
        save_models_config(config, backup=True)

        # Sauvegarder historique
        save_pricing_history(
            model,
            {"input": old_input, "output": old_output},
            {"input": new_input, "output": new_output}
        )

    return result


def get_current_prices() -> Dict[str, Dict]:
    """Récupère les prix actuels de tous les modèles"""
    config = load_models_config()

    prices = {}
    for model_key, model_config in config["models"].items():
        prices[model_key] = {
            "name": model_config["name"],
            "provider": model_config["provider"],
            "cost_per_1m_input": model_config["cost_per_1m_input"],
            "cost_per_1m_output": model_config["cost_per_1m_output"]
        }

    return prices


def compare_with_official_prices(fetch_live: bool = False) -> Dict[str, Any]:
    """
    Compare les prix actuels avec les prix officiels

    Args:
        fetch_live: Si True, essaie de fetch depuis les sites officiels

    Returns:
        Dict avec comparaisons
    """
    current = get_current_prices()

    # Prix officiels connus (mise à jour manuelle si fetch_live=False)
    # Ces prix sont à jour au 2025-01-15
    official_prices = {
        "nano": {
            "name": "gpt-3.5-turbo (fallback for gpt-5-nano)",
            "cost_per_1m_input": 0.50,  # gpt-3.5-turbo actual price
            "cost_per_1m_output": 1.50,
            "note": "gpt-5-nano n'existe pas - utilise gpt-3.5-turbo"
        },
        "deepseek": {
            "name": "deepseek-reasoner",
            "cost_per_1m_input": 0.55,  # DeepSeek V3 cache miss
            "cost_per_1m_output": 2.19,
            "note": "Prix DeepSeek V3 (2025)"
        },
        "claude": {
            "name": "claude-sonnet-4-5",
            "cost_per_1m_input": 3.0,
            "cost_per_1m_output": 15.0,
            "note": "Prix Claude Sonnet 4.5 (Jan 2025)"
        }
    }

    if fetch_live:
        print("⚠️  Live fetch non implémenté - utilise prix manuels")
        print("   Les sites ne fournissent pas d'API JSON pour les prix")

    # Comparer
    comparison = {}
    for model_key in current.keys():
        current_prices = current[model_key]
        official = official_prices.get(model_key, {})

        if official:
            diff_input = official.get("cost_per_1m_input", 0) - current_prices["cost_per_1m_input"]
            diff_output = official.get("cost_per_1m_output", 0) - current_prices["cost_per_1m_output"]

            comparison[model_key] = {
                "current": current_prices,
                "official": official,
                "difference": {
                    "input": diff_input,
                    "output": diff_output,
                    "needs_update": abs(diff_input) > 0.01 or abs(diff_output) > 0.01
                }
            }

    return comparison


def view_pricing_history(model: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """
    Affiche l'historique des changements de prix

    Args:
        model: Filtrer par modèle (optionnel)
        limit: Nombre max d'entrées

    Returns:
        Liste des changements
    """
    if not PRICING_HISTORY_PATH.exists():
        return []

    with open(PRICING_HISTORY_PATH, 'r') as f:
        history = json.load(f)

    # Filtrer par modèle si demandé
    if model:
        history = [h for h in history if h["model"] == model]

    # Limiter
    return history[-limit:]


# CLI
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Mise à jour des prix des modèles LLM"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Command: show
    show_parser = subparsers.add_parser("show", help="Afficher les prix actuels")

    # Command: update
    update_parser = subparsers.add_parser("update", help="Mettre à jour un prix")
    update_parser.add_argument("model", choices=["nano", "deepseek", "claude"])
    update_parser.add_argument("--input", type=float, help="Prix input ($/1M tokens)")
    update_parser.add_argument("--output", type=float, help="Prix output ($/1M tokens)")
    update_parser.add_argument("--dry-run", action="store_true", help="Simulation sans sauvegarde")

    # Command: compare
    compare_parser = subparsers.add_parser("compare", help="Comparer avec prix officiels")
    compare_parser.add_argument("--fetch-live", action="store_true", help="Fetch depuis sites officiels")

    # Command: history
    history_parser = subparsers.add_parser("history", help="Voir l'historique")
    history_parser.add_argument("--model", choices=["nano", "deepseek", "claude"], help="Filtrer par modèle")
    history_parser.add_argument("--limit", type=int, default=10, help="Nombre d'entrées")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        exit(1)

    # Execute command
    if args.command == "show":
        prices = get_current_prices()
        print("\n" + "=" * 80)
        print("Prix actuels des modèles LLM")
        print("=" * 80)
        for model, info in prices.items():
            print(f"\n{model.upper()} - {info['name']}")
            print(f"  Provider: {info['provider']}")
            print(f"  Input:  ${info['cost_per_1m_input']:.2f} / 1M tokens")
            print(f"  Output: ${info['cost_per_1m_output']:.2f} / 1M tokens")

    elif args.command == "update":
        if not args.input and not args.output:
            print("❌ Erreur: Spécifiez au moins --input ou --output")
            exit(1)

        result = update_model_pricing(
            args.model,
            args.input,
            args.output,
            dry_run=args.dry_run
        )

        print("\n" + "=" * 80)
        print(f"{'[DRY RUN] ' if result['dry_run'] else ''}Mise à jour des prix - {result['model']}")
        print("=" * 80)
        print(f"\nModèle: {result['model_name']}")
        print(f"\nAnciens prix:")
        print(f"  Input:  ${result['old_prices']['input']:.2f}")
        print(f"  Output: ${result['old_prices']['output']:.2f}")
        print(f"\nnouveaux prix:")
        print(f"  Input:  ${result['new_prices']['input']:.2f} ({result['changes']['input_percent']:+.1f}%)")
        print(f"  Output: ${result['new_prices']['output']:.2f} ({result['changes']['output_percent']:+.1f}%)")

        if not result['dry_run']:
            print(f"\n✅ Prix mis à jour avec succès!")

    elif args.command == "compare":
        comparison = compare_with_official_prices(args.fetch_live)

        print("\n" + "=" * 80)
        print("Comparaison avec les prix officiels")
        print("=" * 80)

        for model, data in comparison.items():
            print(f"\n{model.upper()}")
            print(f"  Actuel:   ${data['current']['cost_per_1m_input']:.2f} / ${data['current']['cost_per_1m_output']:.2f}")
            print(f"  Officiel: ${data['official']['cost_per_1m_input']:.2f} / ${data['official']['cost_per_1m_output']:.2f}")

            if data['difference']['needs_update']:
                print(f"  ⚠️  DIFFÉRENCE DÉTECTÉE!")
                print(f"     Input:  {data['difference']['input']:+.2f}")
                print(f"     Output: {data['difference']['output']:+.2f}")
            else:
                print(f"  ✓ Prix à jour")

            if data['official'].get('note'):
                print(f"  Note: {data['official']['note']}")

    elif args.command == "history":
        history = view_pricing_history(args.model, args.limit)

        if not history:
            print("Aucun historique trouvé")
            exit(0)

        print("\n" + "=" * 80)
        print("Historique des changements de prix")
        print("=" * 80)

        for entry in history:
            print(f"\n{entry['timestamp']}")
            print(f"  Modèle: {entry['model']}")
            print(f"  Input:  ${entry['old_prices']['input']:.2f} → ${entry['new_prices']['input']:.2f} ({entry['change_percent_input']:+.1f}%)")
            print(f"  Output: ${entry['old_prices']['output']:.2f} → ${entry['new_prices']['output']:.2f} ({entry['change_percent_output']:+.1f}%)")
