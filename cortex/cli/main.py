"""
CLI Principal pour Cortex MXMCorp
Interface conversationnelle style Claude Code
"""

import sys
import os
from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

# Imports locaux
try:
    from cortex.core.config_loader import get_config
    from cortex.core.model_router import ModelRouter
    from cortex.core.partial_updater import PartialUpdater
except ImportError:
    print("Error: Unable to import cortex modules")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


class CortexCLI:
    """Interface CLI conversationnelle pour Cortex"""

    def __init__(self):
        # Console pour output rich
        self.console = Console()

        # Charger configuration
        try:
            self.config = get_config()
            self.display_settings = self.config.get("cli.display", {})
        except Exception as e:
            self.console.print(f"[red]Error loading configuration: {e}[/red]")
            sys.exit(1)

        # Composants principaux
        self.model_router = ModelRouter()
        self.partial_updater = PartialUpdater()

        # Session prompt
        history_file = self.config.get("cli.history_file", ".mxm_history")
        self.session = PromptSession(
            history=FileHistory(history_file),
            auto_suggest=AutoSuggestFromHistory(),
        )

        # Style du prompt
        self.prompt_style = Style.from_dict({
            'prompt': '#00aa00 bold',
        })

        # Contexte de la conversation
        self.conversation_history = []
        self.total_cost = 0.0
        self.total_tokens = 0

    def run(self):
        """Lance la boucle principale du CLI"""
        self.print_welcome()

        while True:
            try:
                # Obtenir input utilisateur
                user_input = self.session.prompt(
                    [('class:prompt', 'mxm> ')],
                    style=self.prompt_style
                )

                # Commandes spéciales
                if user_input.lower() in ['exit', 'quit', 'q']:
                    self.print_goodbye()
                    break

                if user_input.lower() in ['help', 'h', '?']:
                    self.print_help()
                    continue

                if user_input.lower() in ['stats', 'status']:
                    self.print_stats()
                    continue

                if user_input.lower() == 'clear':
                    self.console.clear()
                    continue

                if not user_input.strip():
                    continue

                # Traiter la requête
                self.process_request(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'exit' to quit[/yellow]")
                continue

            except EOFError:
                self.print_goodbye()
                break

            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                if self.config.get("system.debug"):
                    import traceback
                    self.console.print(traceback.format_exc())

    def process_request(self, user_input: str):
        """
        Traite une requête utilisateur

        TODO: Intégration avec LLM réel
        Pour l'instant: démonstration du routing et cost tracking
        """
        # Sélectionner le modèle optimal
        selection = self.model_router.select_model(user_input)

        # Afficher la sélection (si verbose)
        if self.display_settings.get("show_model_used", True):
            self.console.print(
                f"[dim]→ Using {selection.model_name} "
                f"(${selection.estimated_cost:.6f}/1M tokens)[/dim]"
            )

        # TODO: Appel LLM réel ici
        # Pour l'instant, réponse de démonstration
        response = self._generate_demo_response(user_input, selection)

        # Afficher la réponse
        self.console.print()
        self.console.print(Panel(
            Markdown(response),
            title="Cortex Response",
            border_style="blue"
        ))

        # Estimer et afficher les coûts
        input_tokens = len(user_input.split()) * 1.3  # Approximation
        output_tokens = len(response.split()) * 1.3
        cost = self.model_router.estimate_cost(
            selection.tier,
            int(input_tokens),
            int(output_tokens)
        )

        self.total_cost += cost
        self.total_tokens += int(input_tokens + output_tokens)

        if self.display_settings.get("show_cost", True):
            self.console.print(
                f"[dim]💰 Cost: ${cost:.6f} | "
                f"Tokens: {int(input_tokens + output_tokens)} | "
                f"Session total: ${self.total_cost:.4f}[/dim]"
            )

        self.console.print()

    def _generate_demo_response(self, user_input: str, selection) -> str:
        """
        Génère une réponse de démonstration
        TODO: Remplacer par appel LLM réel
        """
        return f"""**Je suis Cortex MXMCorp** - Système agentique intelligent

Vous avez demandé: _{user_input}_

**Modèle sélectionné:** {selection.model_name}
**Raison:** {selection.reasoning}

---

**Note:** Ceci est une version de démonstration. Les fonctionnalités complètes incluront:

✓ Génération de code et outils automatiques
✓ Système d'agents hiérarchique (CEO → Directors → Managers → Workers)
✓ Cache multi-niveaux pour économiser des coûts
✓ Updates partiels (économie de 70-95% des tokens)
✓ Apprentissage continu et amélioration
✓ Formation proactive de l'utilisateur

**Prochaines étapes d'implémentation:**
1. Intégrer les APIs LLM (OpenAI, DeepSeek, Anthropic)
2. Implémenter le système de cache
3. Créer les agents Workers
4. Ajouter la Tool Factory
"""

    def print_welcome(self):
        """Affiche le message de bienvenue"""
        welcome_text = """
# 🧠 Cortex MXMCorp

Système agentique intelligent - Version 0.1.0

**Philosophie:** Maximum d'efficacité, minimum de coûts

Tapez votre requête ou 'help' pour l'aide.
        """
        self.console.print(Panel(
            Markdown(welcome_text),
            border_style="green"
        ))
        self.console.print()

    def print_goodbye(self):
        """Affiche le message de départ"""
        self.console.print()
        self.console.print(Panel(
            f"[green]Session terminée[/green]\n\n"
            f"💰 Coût total: ${self.total_cost:.4f}\n"
            f"🔢 Tokens total: {self.total_tokens}\n\n"
            f"À bientôt!",
            title="Cortex MXMCorp",
            border_style="yellow"
        ))

    def print_help(self):
        """Affiche l'aide"""
        help_text = """
**Commandes disponibles:**

- `help`, `h`, `?` - Afficher cette aide
- `stats`, `status` - Afficher les statistiques de session
- `clear` - Nettoyer l'écran
- `exit`, `quit`, `q` - Quitter

**Exemples de requêtes:**

- "Liste tous les fichiers Python dans le dossier actuel"
- "Crée un outil pour extraire les emails d'un fichier CSV"
- "Analyse ce code et suggère des optimisations"
- "Génère un rapport de performance hebdomadaire"

**Tips d'optimisation:**

💡 Les requêtes simples utilisent des modèles économiques (nano)
💡 Les requêtes complexes utilisent des modèles plus puissants (deepseek)
💡 Les décisions critiques utilisent le meilleur modèle (claude)
💡 Le cache peut économiser 80%+ des coûts sur requêtes similaires
        """
        self.console.print(Panel(
            Markdown(help_text),
            title="Aide",
            border_style="cyan"
        ))
        self.console.print()

    def print_stats(self):
        """Affiche les statistiques de la session"""
        table = Table(title="Session Statistics")

        table.add_column("Métrique", style="cyan")
        table.add_column("Valeur", style="green")

        table.add_row("Coût total", f"${self.total_cost:.6f}")
        table.add_row("Tokens total", str(self.total_tokens))
        table.add_row("Requêtes", str(len(self.conversation_history)))

        avg_cost = self.total_cost / len(self.conversation_history) if self.conversation_history else 0
        table.add_row("Coût moyen/requête", f"${avg_cost:.6f}")

        self.console.print()
        self.console.print(table)
        self.console.print()


def main():
    """Point d'entrée principal"""
    # Vérifier les dépendances
    try:
        import prompt_toolkit
        import rich
        import yaml
    except ImportError as e:
        print(f"Error: Missing dependency: {e}")
        print("\nPlease install dependencies:")
        print("pip install -r requirements.txt")
        sys.exit(1)

    # Vérifier la configuration
    config_path = Path("cortex/config/config.yaml")
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        print("\nPlease run from the project root directory")
        sys.exit(1)

    # Lancer le CLI
    cli = CortexCLI()
    cli.run()


if __name__ == "__main__":
    main()
