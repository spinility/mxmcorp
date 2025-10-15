"""
Terminal UI - Beautiful terminal interface for Cortex MXMCorp

Provides:
- ASCII art logo
- Colored output
- Progress bars
- Spinners
- Formatted tables
- Gradient effects
"""

import sys
import time
from typing import Optional, List, Dict, Any
from enum import Enum


class Color(Enum):
    """ANSI color codes"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Standard colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


class TerminalUI:
    """Beautiful terminal interface with colors and formatting"""

    def __init__(self, use_colors: bool = True):
        """
        Args:
            use_colors: Enable ANSI colors (disable for CI/CD)
        """
        self.use_colors = use_colors and sys.stdout.isatty()

    def color(self, text: str, color: Color, bold: bool = False) -> str:
        """Apply color to text"""
        if not self.use_colors:
            return text

        prefix = color.value
        if bold:
            prefix = Color.BOLD.value + prefix

        return f"{prefix}{text}{Color.RESET.value}"

    def gradient(self, text: str, start_color: Color, end_color: Color) -> str:
        """Create gradient effect (simplified version)"""
        if not self.use_colors or len(text) == 0:
            return text

        # Simple gradient: alternate between two colors
        result = []
        mid = len(text) // 2

        for i, char in enumerate(text):
            if i < mid:
                result.append(self.color(char, start_color))
            else:
                result.append(self.color(char, end_color))

        return "".join(result)

    def box(self, text: str, width: int = 70, color: Color = Color.CYAN, title: Optional[str] = None) -> str:
        """Create a box around text"""
        lines = text.split("\n")

        # Top border
        if title:
            title_str = f" {title} "
            padding = (width - len(title_str) - 2) // 2
            top = "╭" + "─" * padding + title_str + "─" * (width - padding - len(title_str) - 2) + "╮"
        else:
            top = "╭" + "─" * (width - 2) + "╮"

        # Content
        content = []
        for line in lines:
            # Pad or truncate line
            if len(line) > width - 4:
                line = line[:width - 7] + "..."
            padding = width - len(line) - 4
            content.append(f"│ {line}{' ' * padding} │")

        # Bottom border
        bottom = "╰" + "─" * (width - 2) + "╯"

        result = "\n".join([top] + content + [bottom])

        if self.use_colors:
            result = self.color(result, color)

        return result

    def spinner(self, text: str, duration: float = 1.0):
        """Show spinner animation"""
        if not self.use_colors:
            print(f"{text}...")
            time.sleep(duration)
            return

        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        end_time = time.time() + duration

        while time.time() < end_time:
            for frame in frames:
                if time.time() >= end_time:
                    break
                print(f"\r{self.color(frame, Color.CYAN)} {text}", end="", flush=True)
                time.sleep(0.08)

        print(f"\r{self.color('✓', Color.GREEN)} {text}")

    def progress_bar(self, current: int, total: int, width: int = 40, label: str = "") -> str:
        """Create a progress bar"""
        percentage = current / total if total > 0 else 0
        filled = int(width * percentage)
        bar = "█" * filled + "░" * (width - filled)

        if self.use_colors:
            if percentage < 0.5:
                color = Color.YELLOW
            elif percentage < 1.0:
                color = Color.CYAN
            else:
                color = Color.GREEN

            bar = self.color(bar, color)

        return f"{label} [{bar}] {percentage * 100:.0f}% ({current}/{total})"

    def table(self, headers: List[str], rows: List[List[str]], widths: Optional[List[int]] = None) -> str:
        """Create a formatted table"""
        if not rows:
            return ""

        # Calculate column widths
        if widths is None:
            widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]

        # Top border
        top = "┌" + "┬".join("─" * (w + 2) for w in widths) + "┐"

        # Header
        header_row = "│" + "│".join(f" {h:<{widths[i]}} " for i, h in enumerate(headers)) + "│"
        separator = "├" + "┼".join("─" * (w + 2) for w in widths) + "┤"

        # Rows
        data_rows = []
        for row in rows:
            data_rows.append("│" + "│".join(f" {str(cell):<{widths[i]}} " for i, cell in enumerate(row)) + "│")

        # Bottom border
        bottom = "└" + "┴".join("─" * (w + 2) for w in widths) + "┘"

        result = "\n".join([top, header_row, separator] + data_rows + [bottom])

        if self.use_colors:
            result = self.color(result, Color.CYAN)

        return result

    def success(self, text: str):
        """Print success message"""
        icon = self.color("✓", Color.GREEN, bold=True)
        print(f"{icon} {text}")

    def error(self, text: str):
        """Print error message"""
        icon = self.color("✗", Color.RED, bold=True)
        print(f"{icon} {text}")

    def warning(self, text: str):
        """Print warning message"""
        icon = self.color("⚠", Color.YELLOW, bold=True)
        print(f"{icon} {text}")

    def info(self, text: str):
        """Print info message"""
        icon = self.color("ℹ", Color.CYAN, bold=True)
        print(f"{icon} {text}")

    def header(self, text: str, level: int = 1):
        """Print header"""
        if level == 1:
            print(f"\n{self.color(text, Color.CYAN, bold=True)}")
            print(self.color("═" * len(text), Color.CYAN))
        elif level == 2:
            print(f"\n{self.color(text, Color.BLUE, bold=True)}")
            print(self.color("─" * len(text), Color.BLUE))
        else:
            print(f"\n{self.color(text, Color.MAGENTA)}")


# ASCII Logo - Cleaner and more readable
CORTEX_LOGO = """
   ███╗   ███╗██╗  ██╗███╗   ███╗     ██████╗ ██████╗ ██████╗ ██████╗
   ████╗ ████║╚██╗██╔╝████╗ ████║    ██╔════╝██╔═══██╗██╔══██╗██╔══██╗
   ██╔████╔██║ ╚███╔╝ ██╔████╔██║    ██║     ██║   ██║██████╔╝██████╔╝
   ██║╚██╔╝██║ ██╔██╗ ██║╚██╔╝██║    ██║     ██║   ██║██╔══██╗██╔═══╝
   ██║ ╚═╝ ██║██╔╝ ██╗██║ ╚═╝ ██║    ╚██████╗╚██████╔╝██║  ██║██║
   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝

    ██████╗ ██████╗ ██████╗ ████████╗███████╗██╗  ██╗
   ██╔════╝██╔═══██╗██╔══██╗╚══██╔══╝██╔════╝╚██╗██╔╝
   ██║     ██║   ██║██████╔╝   ██║   █████╗   ╚███╔╝
   ██║     ██║   ██║██╔══██╗   ██║   ██╔══╝   ██╔██╗
   ╚██████╗╚██████╔╝██║  ██║   ██║   ███████╗██╔╝ ██╗
    ╚═════╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
"""

CORTEX_TAGLINE = "AI Agent Orchestration System"


def show_startup_screen(ui: Optional[TerminalUI] = None, show_system_info: bool = True):
    """
    Display beautiful startup screen

    Args:
        ui: TerminalUI instance (creates one if None)
        show_system_info: Show system information
    """
    if ui is None:
        ui = TerminalUI()

    # Clear screen
    print("\033[2J\033[H", end="")

    # Logo with gradient effect - BRIGHT colors for better visibility
    print()
    for line in CORTEX_LOGO.split("\n"):
        if line.strip():
            print(ui.gradient(line, Color.BRIGHT_CYAN, Color.BRIGHT_WHITE))

    # Tagline
    tagline = f"         {CORTEX_TAGLINE}         "
    print(ui.color(tagline, Color.BRIGHT_CYAN, bold=True))
    print(ui.color("         " + "─" * len(CORTEX_TAGLINE) + "         ", Color.CYAN))
    print()

    # System info
    if show_system_info:
        import os
        from datetime import datetime

        info_box = f"""
Version: 4.2.2 (NANO Tool Calling Fix)
Environment: {os.getenv('ENV', 'development')}
Initialized: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

        print(ui.box(info_box, width=60, color=Color.BLUE, title="System Info"))
        print()

    # Loading animation
    ui.spinner("Initializing Cortex systems", duration=0.5)
    ui.spinner("Loading agent configurations", duration=0.4)
    ui.spinner("Establishing LLM connections", duration=0.4)
    ui.spinner("Indexing project knowledge base", duration=0.6)

    print()
    ui.success("Cortex is ready!")
    print()


def show_agent_status(agents: List[Dict[str, Any]], ui: Optional[TerminalUI] = None):
    """
    Display agent status table

    Args:
        agents: List of agent dicts with keys: name, role, status, tasks_completed
        ui: TerminalUI instance
    """
    if ui is None:
        ui = TerminalUI()

    ui.header("Agent Status", level=1)

    headers = ["Agent", "Role", "Status", "Tasks"]
    rows = []

    for agent in agents:
        status = agent.get("status", "unknown")

        # Color code status
        if status == "active":
            status_display = ui.color("● Active", Color.GREEN)
        elif status == "idle":
            status_display = ui.color("○ Idle", Color.YELLOW)
        elif status == "busy":
            status_display = ui.color("◉ Busy", Color.CYAN)
        else:
            status_display = ui.color("◌ Unknown", Color.BRIGHT_BLACK)

        rows.append([
            agent.get("name", "N/A"),
            agent.get("role", "N/A"),
            status_display,
            str(agent.get("tasks_completed", 0))
        ])

    print(ui.table(headers, rows))
    print()


def show_task_progress(task_name: str, steps: List[str], ui: Optional[TerminalUI] = None):
    """
    Display task progress with steps

    Args:
        task_name: Name of the task
        steps: List of step descriptions
        ui: TerminalUI instance
    """
    if ui is None:
        ui = TerminalUI()

    ui.header(f"Task: {task_name}", level=2)

    for i, step in enumerate(steps, 1):
        print(ui.progress_bar(i, len(steps), width=50, label=f"Step {i}/{len(steps)}"))
        print(f"  {ui.color('→', Color.CYAN)} {step}")
        time.sleep(0.3)  # Simulate work

    print()
    ui.success(f"Task '{task_name}' completed!")
    print()


def show_cost_summary(costs: Dict[str, float], ui: Optional[TerminalUI] = None):
    """
    Display cost summary

    Args:
        costs: Dict with model names and costs
        ui: TerminalUI instance
    """
    if ui is None:
        ui = TerminalUI()

    ui.header("Cost Summary", level=2)

    total = sum(costs.values())

    for model, cost in costs.items():
        percentage = (cost / total * 100) if total > 0 else 0
        bar_width = int(percentage / 2)  # Scale to 50 chars max
        bar = "█" * bar_width + "░" * (50 - bar_width)

        if model == "nano":
            color = Color.GREEN
        elif model == "deepseek":
            color = Color.CYAN
        else:
            color = Color.MAGENTA

        print(f"{model:10s} {ui.color(bar, color)} ${cost:.6f} ({percentage:.1f}%)")

    print()
    print(f"{'Total':10s} {ui.color('$', Color.YELLOW, bold=True)}{ui.color(f'{total:.6f}', Color.YELLOW, bold=True)}")
    print()


def show_help(ui: Optional[TerminalUI] = None):
    """Display help information"""
    if ui is None:
        ui = TerminalUI()

    ui.header("Cortex Commands", level=1)

    commands = [
        ("status", "Show system and agent status"),
        ("task <description>", "Execute a task with LLM and tools"),
        ("agents", "List all available agents"),
        ("costs", "Show cost breakdown"),
        ("history", "Show command history"),
        ("clear-history", "Clear conversation history (fix UTF-8 errors)"),
        ("clear", "Clear the screen"),
        ("help", "Show this help message"),
        ("exit", "Exit Cortex"),
    ]

    for cmd, desc in commands:
        print(f"  {ui.color(cmd, Color.CYAN, bold=True):30s} {desc}")

    print()

    ui.header("Natural Language Mode", level=2)
    print("  You can also type natural language requests directly!")
    print()
    print("  " + ui.color("Examples:", Color.YELLOW, bold=True))
    print(f"    {ui.color('→', Color.CYAN)} create a file test.md")
    print(f"    {ui.color('→', Color.CYAN)} list all Python files in the current directory")
    print(f"    {ui.color('→', Color.CYAN)} read the content of README.md")
    print()
    print("  " + ui.color("Available Tools:", Color.YELLOW, bold=True))
    print()
    print("  " + ui.color("File Operations:", Color.CYAN))
    print(f"    {ui.color('•', Color.GREEN)} create_file - Create files with content")
    print(f"    {ui.color('•', Color.GREEN)} read_file - Read file contents")
    print(f"    {ui.color('•', Color.GREEN)} append_to_file - Append to existing files")
    print(f"    {ui.color('•', Color.GREEN)} list_directory - List directory contents")
    print(f"    {ui.color('•', Color.GREEN)} file_exists - Check if files exist")
    print()
    print("  " + ui.color("Web & Real-Time:", Color.CYAN))
    print(f"    {ui.color('•', Color.BRIGHT_GREEN)} web_search - Search the web in real-time")
    print(f"    {ui.color('•', Color.BRIGHT_GREEN)} web_fetch - Fetch web page content")
    print(f"    {ui.color('•', Color.BRIGHT_GREEN)} get_weather - Get current weather data")
    print()
    print("  " + ui.color("Git Operations:", Color.CYAN))
    print(f"    {ui.color('•', Color.YELLOW)} git_status - Show working tree status")
    print(f"    {ui.color('•', Color.YELLOW)} git_add - Add files to staging area")
    print(f"    {ui.color('•', Color.YELLOW)} git_commit - Create commits")
    print(f"    {ui.color('•', Color.YELLOW)} git_push - Push to remote")
    print(f"    {ui.color('•', Color.YELLOW)} git_pull - Pull from remote")
    print(f"    {ui.color('•', Color.YELLOW)} git_log - Show commit history")
    print()
    print("  " + ui.color("Python Package Management:", Color.CYAN))
    print(f"    {ui.color('•', Color.MAGENTA)} pip_install - Install Python packages")
    print(f"    {ui.color('•', Color.MAGENTA)} pip_uninstall - Uninstall packages")
    print(f"    {ui.color('•', Color.MAGENTA)} pip_list - List installed packages")
    print(f"    {ui.color('•', Color.MAGENTA)} pip_show - Show package info")
    print(f"    {ui.color('•', Color.MAGENTA)} pip_freeze - Export requirements")
    print()


# Demo
if __name__ == "__main__":
    ui = TerminalUI()

    # Startup screen
    show_startup_screen(ui)

    input("Press Enter to see agent status demo...")
    print()

    # Agent status
    agents = [
        {"name": "CEO", "role": "Strategic Director", "status": "active", "tasks_completed": 15},
        {"name": "CTO", "role": "Technical Director", "status": "busy", "tasks_completed": 42},
        {"name": "HR", "role": "HR Director", "status": "idle", "tasks_completed": 8},
        {"name": "Finance", "role": "Finance Director", "status": "active", "tasks_completed": 23},
    ]

    show_agent_status(agents, ui)

    input("Press Enter to see task progress demo...")
    print()

    # Task progress
    steps = [
        "Analyzing task requirements",
        "Selecting appropriate agent",
        "Building semantic context",
        "Executing with nano model",
        "Validating results",
    ]

    show_task_progress("Add validation to User model", steps, ui)

    input("Press Enter to see cost summary demo...")
    print()

    # Cost summary
    costs = {
        "nano": 0.002145,
        "deepseek": 0.001234,
        "claude": 0.000567,
    }

    show_cost_summary(costs, ui)

    input("Press Enter to see help demo...")
    print()

    # Help
    show_help(ui)
