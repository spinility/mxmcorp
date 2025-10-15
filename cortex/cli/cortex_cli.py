#!/usr/bin/env python3
"""
Cortex CLI - Interactive command-line interface for MXMCorp Cortex

Beautiful, colorful, interactive terminal interface with:
- Startup screen with ASCII art
- Real-time agent status
- Task execution with progress indicators
- Cost tracking
- Command history
"""

import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cortex.cli.terminal_ui import (
    TerminalUI,
    Color,
    show_startup_screen,
    show_agent_status,
    show_cost_summary,
    show_help
)

# Cortex core components
from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelRouter
from cortex.core.prompt_engineer import PromptEngineer
from cortex.tools.tool_executor import ToolExecutor
from cortex.tools.builtin_tools import get_all_builtin_tools
from cortex.tools.web_tools import get_all_web_tools


class CortexCLI:
    """Interactive CLI for Cortex"""

    def __init__(self):
        """Initialize CLI"""
        self.ui = TerminalUI()
        self.running = True
        self.history: List[str] = []

        # Real LLM components
        self.llm_client = LLMClient()
        self.model_router = ModelRouter()
        self.prompt_engineer = PromptEngineer(self.llm_client)
        self.tool_executor = ToolExecutor(self.llm_client)

        # Register built-in tools
        self.available_tools = get_all_builtin_tools()

        # Register web tools (search, fetch, weather)
        web_tools = get_all_web_tools()
        self.available_tools.extend(web_tools)

        # Register all tools with executor
        for tool in self.available_tools:
            self.tool_executor.register_tool(tool)

        # Conversation history for context
        self.conversation_history: List[Dict[str, Any]] = []

        # Mock data for display (will be updated by real tasks)
        self.agents = [
            {"name": "CEO", "role": "Strategic Director", "status": "idle", "tasks_completed": 0},
            {"name": "CTO", "role": "Technical Director", "status": "idle", "tasks_completed": 0},
            {"name": "HR", "role": "HR Director", "status": "idle", "tasks_completed": 0},
            {"name": "Finance", "role": "Finance Director", "status": "idle", "tasks_completed": 0},
            {"name": "Product", "role": "Product Director", "status": "idle", "tasks_completed": 0},
        ]

        self.costs = {
            "nano": 0.0,
            "deepseek": 0.0,
            "claude": 0.0,
        }

        self.total_cost = 0.0
        self.total_tokens = 0

    def run(self):
        """Main CLI loop"""
        # Show startup screen
        show_startup_screen(self.ui)

        # Welcome message
        self.ui.info(f"Welcome to {self.ui.color('Cortex', Color.CYAN, bold=True)}! Type {self.ui.color('help', Color.YELLOW)} for available commands.")
        self.ui.info(f"You can also type natural language requests directly (e.g., {self.ui.color('create a file test.md', Color.GREEN)})")
        print()

        # Main loop
        while self.running:
            try:
                # Prompt
                prompt = f"{self.ui.color('cortex', Color.CYAN, bold=True)} {self.ui.color('❯', Color.BRIGHT_BLUE)} "
                command = input(prompt).strip()

                if not command:
                    continue

                # Add to history
                self.history.append(command)

                # Parse and execute
                self.execute_command(command)

            except KeyboardInterrupt:
                print()
                self.ui.warning("Use 'exit' to quit")
                print()

            except EOFError:
                print()
                break

        # Goodbye
        print()
        self.ui.success("Cortex shutdown complete. Goodbye!")
        print()

    def execute_command(self, command: str):
        """Execute a command"""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "help":
            self.cmd_help()

        elif cmd == "status":
            self.cmd_status()

        elif cmd == "agents":
            self.cmd_agents()

        elif cmd == "costs":
            self.cmd_costs()

        elif cmd == "task":
            if not args:
                self.ui.error("Usage: task <description>")
            else:
                self.cmd_task(args)

        elif cmd == "clear" or cmd == "cls":
            self.cmd_clear()

        elif cmd == "history":
            self.cmd_history()

        elif cmd == "clear-history":
            self.cmd_clear_history()

        elif cmd == "exit" or cmd == "quit":
            self.running = False

        elif cmd == "logo":
            self.cmd_logo()

        elif cmd == "demo":
            self.cmd_demo()

        else:
            # Not a recognized command - treat as natural language task
            self.ui.info("Treating input as natural language task...")
            print()
            self.cmd_task(command)

        print()

    def cmd_help(self):
        """Show help"""
        show_help(self.ui)

    def cmd_status(self):
        """Show system status"""
        self.ui.header("System Status", level=1)

        # System info
        info = f"""
Total Agents: {len(self.agents)}
Active: {sum(1 for a in self.agents if a['status'] == 'active')}
Idle: {sum(1 for a in self.agents if a['status'] == 'idle')}
Tasks Completed: {sum(a['tasks_completed'] for a in self.agents)}
Total Cost: ${sum(self.costs.values()):.6f}
        """.strip()

        print(self.ui.box(info, width=50, color=Color.GREEN, title="Overview"))
        print()

    def cmd_agents(self):
        """Show agent status"""
        show_agent_status(self.agents, self.ui)

    def cmd_costs(self):
        """Show cost summary"""
        if sum(self.costs.values()) == 0:
            self.ui.warning("No costs recorded yet")
            return

        show_cost_summary(self.costs, self.ui)

    def cmd_task(self, description: str):
        """Execute a task with real LLM and tools"""
        self.ui.header(f"Executing Task", level=2)

        # Display user message with VERY visible styling
        user_msg_box = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 👤 USER REQUEST                                                              ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ {description:<76s} ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
        """.strip()
        print(self.ui.color(user_msg_box, Color.BRIGHT_YELLOW, bold=True))
        print()

        try:
            # Step 1: Model selection
            print(f"{self.ui.color('→', Color.BRIGHT_BLUE)} Selecting optimal model...")
            selection = self.model_router.select_model(description)
            print(f"  Using {self.ui.color(selection.model_name, Color.GREEN)} (${selection.estimated_cost:.6f}/1M tokens)")
            print()

            # Step 2: Detect contradictions
            print(f"{self.ui.color('→', Color.BRIGHT_BLUE)} Analyzing request...")
            contradiction = self.prompt_engineer.detect_contradiction(
                description,
                self.available_tools
            )

            if contradiction:
                self.ui.warning(f"⚠️ {contradiction['message']}")
                print()

            # Step 3: Build optimized prompt
            print(f"{self.ui.color('→', Color.BRIGHT_BLUE)} Building optimized prompt for {selection.tier.value}...")
            system_prompt = self.prompt_engineer.build_agent_prompt(
                tier=selection.tier,
                user_request=description,
                available_tools=self.available_tools,
                contradiction=contradiction
            )

            # Build messages
            messages = [{"role": "system", "content": system_prompt}]

            # Add recent conversation history (last 5 exchanges)
            for exchange in self.conversation_history[-5:]:
                messages.append({"role": "user", "content": exchange["user"]})
                messages.append({"role": "assistant", "content": exchange["assistant"]})

            # Add current task
            messages.append({"role": "user", "content": description})
            print()

            # Step 4: Execute with tools
            print(f"{self.ui.color('→', Color.BRIGHT_BLUE)} Executing with {len(self.available_tools)} tools available...")
            print()

            response = self.tool_executor.execute_with_tools(
                messages=messages,
                tier=selection.tier,
                tools=self.available_tools,
                max_tokens=2048,
                temperature=1.0,
                verbose=True  # Activer verbose pour voir les étapes
            )

            # Step 4: Display results
            print()
            if response.tool_calls:
                self.ui.info(f"Tool calls executed: {len(response.tool_calls)}")
                for i, tc in enumerate(response.tool_calls, 1):
                    print(f"  {i}. {self.ui.color(tc.get('name', 'unknown'), Color.YELLOW)}")
                print()

            # Display response with colors
            print()
            if response.content and response.content.strip():
                # Afficher la réponse colorisée
                colored_response = self._colorize_response(response.content)
                print(colored_response)
                print()
            else:
                # Fallback: générer une réponse basique
                self.ui.warning("⚠️ LLM returned empty response - generating fallback")
                print()

                fallback_response = f"""🎯 **Résultat:** Je ne peux pas répondre à cette requête actuellement.

💭 **Confiance:** FAIBLE - Le modèle n'a pas généré de réponse.

⚠️ **Gravité si erreur:** MOYENNE - Requête non traitée.

🔧 **Actions:** Aucune - Réponse fallback générée."""

                if not any(tool in description.lower() for tool in ['météo', 'weather', 'température', 'temperature']):
                    fallback_response = f"""🎯 **Résultat:** Réponse non générée par le LLM.

💭 **Confiance:** FAIBLE - Problème technique avec le modèle.

⚠️ **Gravité si erreur:** MOYENNE - Service temporairement indisponible.

🔧 **Actions:** Aucune - Veuillez réessayer ou reformuler la requête."""
                else:
                    # Requête météo spécifique
                    fallback_response = f"""🎯 **Résultat:** Je n'ai pas d'outil météo actuellement. Je vais demander au Tools Department de créer un outil "get_weather" pour obtenir les données météo en temps réel.

💭 **Confiance:** MOYENNE - Tool manquant mais peut être créé.

⚠️ **Gravité si erreur:** FAIBLE - Information météo non critique.

🔧 **Actions:** Demande de création d'outil "get_weather" au Tools Department."""

                colored_fallback = self._colorize_response(fallback_response)
                print(colored_fallback)
                print()

            # Update costs
            tier_name = selection.tier.value.lower()
            if tier_name in self.costs:
                self.costs[tier_name] += response.cost
            self.total_cost += response.cost
            self.total_tokens += response.tokens_input + response.tokens_output

            # Update agent stats
            self.agents[0]["tasks_completed"] += 1

            # Save to history
            self.conversation_history.append({
                "user": description,
                "assistant": response.content,
                "model": response.model,
                "cost": response.cost,
                "tool_calls": len(response.tool_calls) if response.tool_calls else 0
            })

            # Success message
            self.ui.success(f"Task completed! Cost: ${response.cost:.6f} | Tokens: {response.tokens_input + response.tokens_output}")

        except Exception as e:
            print()
            error_msg = str(e)

            # Provide helpful error messages
            if "UTF-8" in error_msg or "surrogate" in error_msg:
                self.ui.error("Erreur d'encodage UTF-8 détectée")
                self.ui.info("💡 Astuce: L'historique de conversation contient des caractères invalides.")
                self.ui.info("💡 Solution: Redémarrez le Cortex pour nettoyer l'historique.")
            elif "API key" in error_msg or "authentication" in error_msg.lower():
                self.ui.error("Erreur d'authentification API")
                self.ui.info("💡 Vérifiez vos clés API dans le fichier de configuration.")
            elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                self.ui.error("Erreur de connexion réseau")
                self.ui.info("💡 Vérifiez votre connexion internet et réessayez.")
            else:
                self.ui.error(f"Task failed: {error_msg[:100]}")

            # Show full traceback only in debug mode
            import os
            if os.getenv("CORTEX_DEBUG", "false").lower() == "true":
                import traceback
                print()
                self.ui.warning("Debug traceback:")
                traceback.print_exc()

    def _colorize_response(self, response: str) -> str:
        """Colorize response with emoji-based sections"""
        import re

        lines = response.split('\n')
        colored_lines = []

        for line in lines:
            # Section headers with emojis
            if line.startswith('🎯'):
                colored_lines.append(self.ui.color(line, Color.BRIGHT_GREEN, bold=True))
            elif line.startswith('💭'):
                # Color confidence level
                if 'HAUTE' in line:
                    colored_lines.append(self.ui.color(line, Color.GREEN, bold=True))
                elif 'MOYENNE' in line:
                    colored_lines.append(self.ui.color(line, Color.YELLOW, bold=True))
                else:  # FAIBLE
                    colored_lines.append(self.ui.color(line, Color.RED, bold=True))
            elif line.startswith('⚠️'):
                # Color severity level
                if 'CRITIQUE' in line:
                    colored_lines.append(self.ui.color(line, Color.RED, bold=True))
                elif 'HAUTE' in line:
                    colored_lines.append(self.ui.color(line, Color.BRIGHT_RED, bold=True))
                elif 'MOYENNE' in line:
                    colored_lines.append(self.ui.color(line, Color.YELLOW, bold=True))
                else:  # FAIBLE
                    colored_lines.append(self.ui.color(line, Color.GREEN, bold=True))
            elif line.startswith('🔧'):
                colored_lines.append(self.ui.color(line, Color.CYAN, bold=True))
            elif line.strip().startswith('•'):
                # Bullet points
                colored_lines.append(self.ui.color(line, Color.BRIGHT_CYAN))
            elif line.strip().startswith('**') or '**' in line:
                # Bold text
                colored_lines.append(self.ui.color(line, Color.WHITE, bold=True))
            else:
                # Regular text
                colored_lines.append(line)

        return '\n'.join(colored_lines)

    def cmd_clear(self):
        """Clear screen"""
        print("\033[2J\033[H", end="")

    def cmd_history(self):
        """Show command history"""
        self.ui.header("Command History", level=2)

        if not self.history:
            self.ui.info("No commands in history")
            return

        for i, cmd in enumerate(self.history[-10:], 1):
            print(f"  {self.ui.color(f'{i:2d}', Color.BRIGHT_BLACK)} {cmd}")

    def cmd_clear_history(self):
        """Clear conversation history"""
        old_count = len(self.conversation_history)
        self.conversation_history.clear()

        self.ui.success(f"Conversation history cleared ({old_count} messages removed)")
        self.ui.info("💡 Context has been reset. Fresh start!")

    def cmd_logo(self):
        """Show logo"""
        from cortex.cli.terminal_ui import CORTEX_LOGO, CORTEX_TAGLINE

        print()
        for line in CORTEX_LOGO.split("\n"):
            if line.strip():
                print(self.ui.gradient(line, Color.CYAN, Color.MAGENTA))

        tagline = f"         {CORTEX_TAGLINE}         "
        print(self.ui.color(tagline, Color.BRIGHT_CYAN, bold=True))
        print()

    def cmd_demo(self):
        """Show demo of all features"""
        self.ui.header("Cortex Features Demo", level=1)

        # Colors
        self.ui.info("Color support:")
        print(f"  {self.ui.color('Success', Color.GREEN)} {self.ui.color('Error', Color.RED)} {self.ui.color('Warning', Color.YELLOW)} {self.ui.color('Info', Color.CYAN)}")
        print()

        # Box
        print(self.ui.box("This is a beautiful box\nWith multiple lines\nAnd colors!", width=50, color=Color.MAGENTA, title="Example"))
        print()

        # Table
        headers = ["Model", "Cost/1M", "Speed"]
        rows = [
            ["nano", "$0.05", "Fast"],
            ["deepseek", "$0.28", "Medium"],
            ["claude", "$3.00", "Slow"],
        ]
        print(self.ui.table(headers, rows))
        print()

        # Progress
        import time
        for i in range(1, 11):
            print(f"\r{self.ui.progress_bar(i, 10, width=50, label='Demo progress')}", end="", flush=True)
            time.sleep(0.1)
        print()
        print()

        self.ui.success("Demo complete!")


def main():
    """Main entry point"""
    try:
        cli = CortexCLI()
        cli.run()
    except Exception as e:
        print(f"\n{Color.RED.value}Error: {e}{Color.RESET.value}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
