"""
Configuration Loader pour Cortex MXMCorp
Charge et valide les configurations YAML
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


class ConfigLoader:
    """Charge et gère toutes les configurations du système"""

    def __init__(self, config_dir: str = None):
        """
        Initialise le loader

        Args:
            config_dir: Chemin vers le dossier config (défaut: cortex/config)
        """
        if config_dir is None:
            # Trouver le dossier config relatif à ce fichier
            current_file = Path(__file__)
            self.config_dir = current_file.parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)

        # Charger les variables d'environnement
        load_dotenv()

        # Configurations chargées
        self.config: Dict[str, Any] = {}
        self.models: Dict[str, Any] = {}

    def load_all(self):
        """Charge toutes les configurations"""
        self.config = self._load_yaml("config.yaml")
        self.models = self._load_yaml("models.yaml")

        # Remplacer les variables d'environnement
        self._substitute_env_vars(self.config)

        return self

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Charge un fichier YAML"""
        filepath = self.config_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _substitute_env_vars(self, config: Dict[str, Any]):
        """
        Remplace les variables ${VAR} par leur valeur d'environnement
        Parcours récursif du dictionnaire
        """
        for key, value in config.items():
            if isinstance(value, dict):
                self._substitute_env_vars(value)
            elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Extraire le nom de la variable
                var_name = value[2:-1]
                env_value = os.getenv(var_name)
                if env_value:
                    config[key] = env_value
                else:
                    # Garder la valeur par défaut si non définie
                    pass

    def get(self, path: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration via un chemin pointé

        Args:
            path: Chemin comme "system.name" ou "models.nano.cost_per_1m_input"
            default: Valeur par défaut si non trouvé

        Returns:
            La valeur trouvée ou default

        Example:
            >>> loader.get("system.name")
            "Cortex MXMCorp"
        """
        parts = path.split(".")

        # Déterminer si on cherche dans config ou models
        if parts[0] == "models":
            current = self.models
            parts = parts[1:]  # Retirer "models" du chemin
        else:
            current = self.config

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current

    def get_model_config(self, model_tier: str) -> Dict[str, Any]:
        """
        Récupère la configuration d'un modèle (nano, deepseek, claude)

        Args:
            model_tier: "nano", "deepseek", ou "claude"

        Returns:
            Dict avec toute la config du modèle
        """
        return self.models.get("models", {}).get(model_tier, {})

    def get_routing_rules(self) -> Dict[str, Any]:
        """Récupère les règles de routing des modèles"""
        return self.models.get("routing_rules", {})

    def get_optimization_config(self) -> Dict[str, Any]:
        """Récupère la config d'optimisation des coûts"""
        return self.models.get("cost_optimization", {})

    def get_model_pricing(self, model_tier: str) -> Dict[str, float]:
        """
        Récupère les prix d'un modèle

        Args:
            model_tier: "nano", "deepseek", ou "claude"

        Returns:
            Dict avec input et output pricing:
            {
                "input": 0.05,  # $ per 1M tokens
                "output": 0.40,  # $ per 1M tokens
                "provider": "openai",
                "name": "gpt-5-nano"
            }
        """
        model = self.get_model_config(model_tier)
        if not model:
            return {}

        return {
            "input": model.get("cost_per_1m_input", 0),
            "output": model.get("cost_per_1m_output", 0),
            "provider": model.get("provider", "unknown"),
            "name": model.get("name", "unknown")
        }

    def calculate_cost(self, model_tier: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calcule le coût d'un appel API

        Args:
            model_tier: "nano", "deepseek", ou "claude"
            input_tokens: Nombre de tokens d'entrée
            output_tokens: Nombre de tokens de sortie

        Returns:
            Coût en dollars
        """
        pricing = self.get_model_pricing(model_tier)
        if not pricing:
            return 0.0

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def validate(self) -> bool:
        """
        Valide que toutes les configurations essentielles sont présentes

        Returns:
            True si valide, raise ValueError sinon
        """
        # Vérifier les clés API
        required_keys = ["openai_key", "deepseek_key", "anthropic_key"]
        for key in required_keys:
            value = self.get(f"api_keys.{key}")
            if not value or value.startswith("${"):
                raise ValueError(
                    f"API key {key} not configured. "
                    f"Please set environment variable or update config.yaml"
                )

        # Vérifier que les modèles sont configurés
        if not self.models.get("models"):
            raise ValueError("No models configured in models.yaml")

        return True

    def __repr__(self):
        return f"<ConfigLoader config_dir={self.config_dir}>"


# Instance globale (singleton pattern)
_global_config: ConfigLoader = None


def get_config() -> ConfigLoader:
    """
    Récupère l'instance globale de configuration

    Returns:
        ConfigLoader instance
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigLoader()
        _global_config.load_all()
    return _global_config


if __name__ == "__main__":
    # Test
    config = ConfigLoader()
    config.load_all()

    print("System name:", config.get("system.name"))
    print("Nano model:", config.get_model_config("nano").get("name"))
    print("Daily cost limit:", config.get("metrics.targets.daily_cost_max"))
    print("\nConfiguration loaded successfully!")
