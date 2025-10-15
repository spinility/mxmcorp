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


class CortexCLI:
    """Interactive CLI for Cortex"""

    def __init__(self):
        """Initialize CLI"""
        self.ui = TerminalUI()
        self.running = True
        self.history: List[str] = []

        # Mock data (replace with real system later)
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

    def run(self):
        """Main CLI loop"""
        # Show startup screen
        show_startup_screen(self.ui)

        # Welcome message
        self.ui.info(f"Welcome to {self.ui.color('Cortex', Color.CYAN, bold=True)}! Type {self.ui.color('help', Color.YELLOW)} for available commands.")
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

        elif cmd == "exit" or cmd == "quit":
            self.running = False

        elif cmd == "logo":
            self.cmd_logo()

        elif cmd == "demo":
            self.cmd_demo()

        else:
            self.ui.error(f"Unknown command: {cmd}")
            self.ui.info(f"Type {self.ui.color('help', Color.YELLOW)} for available commands")

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
        """Execute a task (mock)"""
        self.ui.header(f"Executing Task", level=2)
        print(f"Task: {self.ui.color(description, Color.CYAN)}")
        print()

        # Simulate task execution
        steps = [
            "Analyzing task with nano self-assessment",
            "Detected severity: MEDIUM",
            "Confidence: HIGH - nano can handle",
            "Building semantic context (900 tokens)",
            "Executing with nano model",
            "Validating output",
        ]

        for i, step in enumerate(steps, 1):
            bar = self.ui.progress_bar(i, len(steps), width=40, label=f"")
            print(f"{bar}  {step}")
            import time
            time.sleep(0.3)

        print()
        self.ui.success("Task completed successfully!")

        # Update mock data
        self.agents[0]["tasks_completed"] += 1
        self.costs["nano"] += 0.000123

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
