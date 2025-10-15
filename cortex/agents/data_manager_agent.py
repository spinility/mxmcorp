"""
Data Manager Agent - Maintient les données importantes du système
Responsable de la mise à jour des prix, configurations et autres données variables
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import yaml
from pathlib import Path

from cortex.agents.base_agent import BaseAgent, AgentConfig
from cortex.core.model_router import ModelTier


class DataManagerAgent(BaseAgent):
    """
    Agent responsable de la maintenance des données du système
    - Vérifie et met à jour les prix des modèles LLM
    - Maintient les informations qui changent dans le temps
    - Peut faire des recherches web pour obtenir des données à jour
    """

    def __init__(
        self,
        name: str = "Data Manager",
        llm_client=None,
        model_router=None
    ):
        # Configuration de l'agent
        config = AgentConfig(
            name=name,
            role="Data Manager",
            description="Maintains critical system data like model pricing and configurations",
            base_prompt="""You are the Data Manager for the MXMCorp Cortex system.

Your responsibilities:
- Monitor and update LLM model pricing
- Maintain system configurations
- Validate data integrity
- Provide accurate, up-to-date information to other agents

You have access to configuration files and can update them when needed.
Always verify data accuracy before making changes.""",
            tier_preference=ModelTier.NANO,  # Simple tâches de maintenance
            can_delegate=False,
            specializations=[
                "pricing",
                "configuration",
                "data_validation",
                "system_maintenance"
            ]
        )

        super().__init__(
            config=config,
            llm_client=llm_client,
            model_router=model_router
        )

        # Chemins des fichiers de configuration
        self.config_dir = Path(__file__).parent.parent / "config"
        self.models_config_path = self.config_dir / "models.yaml"
        self.pricing_log_path = self.config_dir / "pricing_history.json"

        # Données de prix actuelles
        self.current_prices: Dict[str, Dict[str, float]] = {}
        self.last_update: Optional[datetime] = None

    def execute_data_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute une tâche de gestion de données

        Tâches supportées:
        - update_pricing: Met à jour les prix des modèles
        - verify_pricing: Vérifie si les prix sont à jour
        - get_current_prices: Retourne les prix actuels
        - search_web: Recherche d'informations sur le web
        """
        task_type = task.get("type")

        if task_type == "update_pricing":
            return self._update_pricing(task.get("prices"))
        elif task_type == "verify_pricing":
            return self._verify_pricing()
        elif task_type == "get_current_prices":
            return self._get_current_prices()
        elif task_type == "search_web":
            return self._search_web(task.get("query"))
        else:
            return {
                "success": False,
                "error": f"Unknown task type: {task_type}"
            }

    def _update_pricing(self, new_prices: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Met à jour les prix des modèles dans models.yaml

        Args:
            new_prices: Dict avec structure:
                {
                    "nano": {"input": 0.05, "output": 0.40},
                    "deepseek": {"input": 0.28, "output": 0.42},
                    "claude": {"input": 3.0, "output": 15.0}
                }

        Returns:
            Résultat de l'opération avec détails des changements
        """
        try:
            # Charger la configuration actuelle
            with open(self.models_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            changes = []

            # Mettre à jour les prix
            for model_name, prices in new_prices.items():
                if model_name in config["models"]:
                    old_input = config["models"][model_name]["cost_per_1m_input"]
                    old_output = config["models"][model_name]["cost_per_1m_output"]

                    new_input = prices["input"]
                    new_output = prices["output"]

                    if old_input != new_input or old_output != new_output:
                        config["models"][model_name]["cost_per_1m_input"] = new_input
                        config["models"][model_name]["cost_per_1m_output"] = new_output

                        changes.append({
                            "model": model_name,
                            "old_input": old_input,
                            "new_input": new_input,
                            "old_output": old_output,
                            "new_output": new_output,
                            "timestamp": datetime.now().isoformat()
                        })

            if changes:
                # Sauvegarder la configuration mise à jour
                with open(self.models_config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

                # Logger les changements
                self._log_pricing_changes(changes)

                self.last_update = datetime.now()

                return {
                    "success": True,
                    "changes": changes,
                    "message": f"Updated pricing for {len(changes)} model(s)"
                }
            else:
                return {
                    "success": True,
                    "changes": [],
                    "message": "No pricing changes needed"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _verify_pricing(self) -> Dict[str, Any]:
        """
        Vérifie si les prix actuels sont à jour
        Lit models.yaml et retourne les prix actuels
        """
        try:
            with open(self.models_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            current_prices = {}
            for model_name, model_config in config["models"].items():
                current_prices[model_name] = {
                    "input": model_config["cost_per_1m_input"],
                    "output": model_config["cost_per_1m_output"],
                    "name": model_config["name"],
                    "provider": model_config["provider"]
                }

            self.current_prices = current_prices

            return {
                "success": True,
                "prices": current_prices,
                "last_modified": datetime.fromtimestamp(
                    self.models_config_path.stat().st_mtime
                ).isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _get_current_prices(self) -> Dict[str, Any]:
        """Retourne les prix actuellement en mémoire ou charge depuis le fichier"""
        if not self.current_prices:
            return self._verify_pricing()

        return {
            "success": True,
            "prices": self.current_prices,
            "cached": True
        }

    def _search_web(self, query: str) -> Dict[str, Any]:
        """
        Recherche d'informations sur le web
        Peut être étendu pour utiliser des APIs de recherche

        Pour l'instant, retourne un template pour recherche manuelle
        """
        # Liste des sources officielles pour les prix
        sources = {
            "openai": "https://openai.com/api/pricing/",
            "deepseek": "https://platform.deepseek.com/api-docs/pricing/",
            "anthropic": "https://www.anthropic.com/pricing"
        }

        return {
            "success": True,
            "query": query,
            "suggested_sources": sources,
            "message": "For accurate pricing, check official sources listed above"
        }

    def _log_pricing_changes(self, changes: List[Dict[str, Any]]):
        """
        Enregistre l'historique des changements de prix
        """
        try:
            # Charger l'historique existant
            if self.pricing_log_path.exists():
                with open(self.pricing_log_path, 'r') as f:
                    history = json.load(f)
            else:
                history = {"changes": []}

            # Ajouter les nouveaux changements
            history["changes"].extend(changes)

            # Sauvegarder
            with open(self.pricing_log_path, 'w') as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not log pricing changes: {e}")

    def get_pricing_history(self) -> List[Dict[str, Any]]:
        """Retourne l'historique des changements de prix"""
        try:
            if self.pricing_log_path.exists():
                with open(self.pricing_log_path, 'r') as f:
                    history = json.load(f)
                return history.get("changes", [])
            return []
        except Exception as e:
            return []

    def generate_pricing_report(self) -> str:
        """
        Génère un rapport sur les prix actuels et l'historique
        """
        report_lines = [
            "=== PRICING REPORT ===",
            f"Generated: {datetime.now().isoformat()}",
            ""
        ]

        # Prix actuels
        current = self._verify_pricing()
        if current["success"]:
            report_lines.append("Current Pricing (per 1M tokens):")
            for model, prices in current["prices"].items():
                report_lines.append(
                    f"  {model} ({prices['name']}):"
                )
                report_lines.append(f"    Input:  ${prices['input']:.2f}")
                report_lines.append(f"    Output: ${prices['output']:.2f}")
            report_lines.append("")

        # Historique récent
        history = self.get_pricing_history()
        if history:
            report_lines.append("Recent Changes:")
            for change in history[-5:]:  # 5 derniers changements
                report_lines.append(
                    f"  {change['timestamp']}: {change['model']} - "
                    f"Input: ${change['old_input']:.2f} -> ${change['new_input']:.2f}, "
                    f"Output: ${change['old_output']:.2f} -> ${change['new_output']:.2f}"
                )

        return "\n".join(report_lines)


# Fonction helper pour créer une instance
def create_data_manager(name: str = "Data Manager") -> DataManagerAgent:
    """Crée une instance du Data Manager Agent"""
    return DataManagerAgent(name=name)


if __name__ == "__main__":
    # Test de l'agent
    agent = create_data_manager()

    print("Testing Data Manager Agent...")
    print("\n1. Verify current pricing:")
    result = agent.execute_data_task({"type": "verify_pricing"})
    print(json.dumps(result, indent=2))

    print("\n2. Generate pricing report:")
    report = agent.generate_pricing_report()
    print(report)

    print("\n3. Search web sources:")
    result = agent.execute_data_task({"type": "search_web", "query": "LLM pricing 2025"})
    print(json.dumps(result, indent=2))

    print("\n4. Test with base agent execute:")
    result = agent.execute(
        task="What are the current prices for all models?",
        verbose=True
    )
    print(json.dumps(result, indent=2, default=str))
