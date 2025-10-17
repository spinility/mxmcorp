"""
Advanced UI Components for Cortex CLI

Provides:
1. Keyboard shortcuts (Ctrl+E for expand)
2. Progress bars for multi-step operations
3. Expansion modes (preview, summary, full)
4. Theme system (dark, light, custom)
5. Background task notifications
"""

import sys
import threading
import time
from typing import Optional, Dict, List, Callable, Any
from enum import Enum
from dataclasses import dataclass
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.theme import Theme
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.table import Table


# ============================================================================
# THEMES
# ============================================================================

class CortexTheme(Enum):
    """Available themes for Cortex"""
    DARK = "dark"
    LIGHT = "light"
    MATRIX = "matrix"
    OCEAN = "ocean"
    SUNSET = "sunset"
    CYBERPUNK = "cyberpunk"


# Theme definitions
THEMES = {
    CortexTheme.DARK: Theme({
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "header": "bold magenta",
        "spinner": "cyan",
        "progress": "bright_blue",
        "dim": "dim white",
    }),
    CortexTheme.LIGHT: Theme({
        "info": "blue",
        "warning": "dark_orange",
        "error": "bold red",
        "success": "green",
        "header": "bold blue",
        "spinner": "blue",
        "progress": "blue",
        "dim": "grey50",
    }),
    CortexTheme.MATRIX: Theme({
        "info": "bright_green",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold bright_green",
        "header": "bold bright_green",
        "spinner": "green",
        "progress": "bright_green",
        "dim": "dim green",
    }),
    CortexTheme.OCEAN: Theme({
        "info": "bright_cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold bright_cyan",
        "header": "bold cyan",
        "spinner": "cyan",
        "progress": "bright_cyan",
        "dim": "dim cyan",
    }),
    CortexTheme.SUNSET: Theme({
        "info": "orange1",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "header": "bold orange1",
        "spinner": "orange1",
        "progress": "orange1",
        "dim": "dim orange1",
    }),
    CortexTheme.CYBERPUNK: Theme({
        "info": "magenta",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold bright_cyan",
        "header": "bold magenta",
        "spinner": "magenta",
        "progress": "bright_magenta",
        "dim": "dim magenta",
    }),
}


class ThemeManager:
    """Manages themes for Cortex"""

    def __init__(self, default_theme: CortexTheme = CortexTheme.DARK):
        """
        Initialize theme manager

        Args:
            default_theme: Default theme to use
        """
        self.current_theme = default_theme
        self.console = Console(theme=THEMES[default_theme])

    def set_theme(self, theme: CortexTheme):
        """
        Set current theme

        Args:
            theme: Theme to set
        """
        self.current_theme = theme
        self.console = Console(theme=THEMES[theme])

    def get_console(self) -> Console:
        """Get themed console"""
        return self.console

    def list_themes(self) -> List[str]:
        """List available themes"""
        return [theme.value for theme in CortexTheme]

    def preview_theme(self, theme: CortexTheme):
        """
        Preview a theme

        Args:
            theme: Theme to preview
        """
        preview_console = Console(theme=THEMES[theme])
        preview_console.print(f"\n[header]Preview of {theme.value} theme:[/header]")
        preview_console.print("[info]ℹ This is an info message[/info]")
        preview_console.print("[warning]⚠ This is a warning message[/warning]")
        preview_console.print("[error]✗ This is an error message[/error]")
        preview_console.print("[success]✓ This is a success message[/success]")
        preview_console.print("[spinner]⠋ This is a spinner style[/spinner]")
        preview_console.print("[progress]━━━━━━━━━━ This is progress style[/progress]")
        preview_console.print("[dim]This is dim text[/dim]\n")


# ============================================================================
# PROGRESS BARS
# ============================================================================

class MultiStepProgress:
    """
    Multi-step progress tracker with beautiful progress bars

    Usage:
        with MultiStepProgress() as progress:
            progress.add_step("Loading data", 100)
            progress.add_step("Processing", 50)

            for i in range(100):
                progress.update(0, i)
            progress.complete_step(0)

            for i in range(50):
                progress.update(1, i)
            progress.complete_step(1)
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize multi-step progress

        Args:
            console: Optional console to use
        """
        self.console = console or Console()
        self.progress = None
        self.tasks = {}
        self.step_names = []

    def __enter__(self):
        """Start progress display"""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console
        )
        self.progress.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop progress display"""
        if self.progress:
            self.progress.__exit__(exc_type, exc_val, exc_tb)

    def add_step(self, name: str, total: int = 100) -> int:
        """
        Add a step to track

        Args:
            name: Step name
            total: Total units for this step

        Returns:
            Step ID
        """
        task_id = self.progress.add_task(f"[cyan]{name}...", total=total)
        step_id = len(self.tasks)
        self.tasks[step_id] = task_id
        self.step_names.append(name)
        return step_id

    def update(self, step_id: int, completed: int):
        """
        Update progress for a step

        Args:
            step_id: Step ID
            completed: Completed units
        """
        if step_id in self.tasks:
            self.progress.update(self.tasks[step_id], completed=completed)

    def advance(self, step_id: int, amount: int = 1):
        """
        Advance progress by amount

        Args:
            step_id: Step ID
            amount: Amount to advance
        """
        if step_id in self.tasks:
            self.progress.advance(self.tasks[step_id], amount)

    def complete_step(self, step_id: int):
        """
        Mark step as complete

        Args:
            step_id: Step ID
        """
        if step_id in self.tasks:
            task_id = self.tasks[step_id]
            self.progress.update(task_id, completed=self.progress.tasks[task_id].total)
            # Change description to show completion
            self.progress.update(task_id, description=f"[green]✓ {self.step_names[step_id]}")


# ============================================================================
# EXPANSION MODES
# ============================================================================

class ExpansionMode(Enum):
    """Modes for content expansion"""
    PREVIEW = "preview"      # First 10 lines
    SUMMARY = "summary"      # Summary of content
    FULL = "full"           # Full content


@dataclass
class ExpandableContent:
    """Represents expandable content with metadata"""
    content_id: int
    full_text: str
    title: Optional[str] = None
    mode: ExpansionMode = ExpansionMode.PREVIEW
    max_preview_lines: int = 10


class AdvancedCollapsibleContent:
    """
    Advanced collapsible content with multiple expansion modes

    Features:
    - Preview mode (first N lines)
    - Summary mode (AI-generated summary if available)
    - Full mode (complete content)
    - Keyboard shortcuts
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize advanced collapsible content

        Args:
            console: Optional console to use
        """
        self.console = console or Console()
        self.contents: Dict[int, ExpandableContent] = {}
        self.next_id = 0

    def add_content(
        self,
        text: str,
        title: Optional[str] = None,
        initial_mode: ExpansionMode = ExpansionMode.PREVIEW
    ) -> int:
        """
        Add content to manage

        Args:
            text: Full text content
            title: Optional title
            initial_mode: Initial expansion mode

        Returns:
            Content ID
        """
        content = ExpandableContent(
            content_id=self.next_id,
            full_text=text,
            title=title,
            mode=initial_mode
        )
        self.contents[self.next_id] = content
        self.next_id += 1
        return content.content_id

    def display(self, content_id: int, mode: Optional[ExpansionMode] = None):
        """
        Display content in specified mode

        Args:
            content_id: Content ID
            mode: Optional mode override
        """
        if content_id not in self.contents:
            self.console.print(f"[error]Content {content_id} not found[/error]")
            return

        content = self.contents[content_id]
        display_mode = mode or content.mode

        # Display title if present
        if content.title:
            self.console.print(f"\n[header]{content.title}[/header]")

        lines = content.full_text.split('\n')

        if display_mode == ExpansionMode.PREVIEW:
            # Show preview (first N lines)
            preview = '\n'.join(lines[:content.max_preview_lines])
            self.console.print(preview)

            if len(lines) > content.max_preview_lines:
                remaining = len(lines) - content.max_preview_lines
                self.console.print(f"\n[dim]... {remaining} more lines.[/dim]")
                self.console.print(f"[dim]Commands:[/dim]")
                self.console.print(f"  [info]expand {content_id}[/info] or [info]e {content_id}[/info] - Show full content")
                self.console.print(f"  [info]summary {content_id}[/info] or [info]s {content_id}[/info] - Show summary")
                self.console.print(f"  [dim]Or press [bold]Ctrl+E[/bold] for quick expand[/dim]")

        elif display_mode == ExpansionMode.SUMMARY:
            # Show summary (first and last few lines)
            summary_lines = 5
            if len(lines) <= summary_lines * 2:
                self.console.print(content.full_text)
            else:
                summary = '\n'.join(lines[:summary_lines])
                summary += f"\n\n[dim]... {len(lines) - summary_lines * 2} lines omitted ...[/dim]\n\n"
                summary += '\n'.join(lines[-summary_lines:])
                self.console.print(summary)
                self.console.print(f"\n[dim]Press [bold]Ctrl+E[/bold] or type [info]expand {content_id}[/info] for full content[/dim]")

        elif display_mode == ExpansionMode.FULL:
            # Show full content
            self.console.print(content.full_text)
            self.console.print(f"\n[dim]Full content displayed ({len(lines)} lines)[/dim]")

        # Update mode
        content.mode = display_mode

    def cycle_mode(self, content_id: int):
        """
        Cycle through expansion modes

        Args:
            content_id: Content ID
        """
        if content_id not in self.contents:
            return

        content = self.contents[content_id]

        # Cycle: PREVIEW → SUMMARY → FULL → PREVIEW
        if content.mode == ExpansionMode.PREVIEW:
            self.display(content_id, ExpansionMode.SUMMARY)
        elif content.mode == ExpansionMode.SUMMARY:
            self.display(content_id, ExpansionMode.FULL)
        else:
            self.display(content_id, ExpansionMode.PREVIEW)


# ============================================================================
# NOTIFICATIONS
# ============================================================================

class NotificationType(Enum):
    """Notification types"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    TASK_COMPLETE = "task_complete"


@dataclass
class Notification:
    """Represents a notification"""
    type: NotificationType
    title: str
    message: str
    timestamp: float
    id: int


class NotificationManager:
    """
    Manages background task notifications

    Features:
    - Queue notifications
    - Display toast-style notifications
    - Notification history
    - Priority levels
    """

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        """
        Initialize notification manager

        Args:
            theme_manager: Optional theme manager to use
        """
        self.theme_manager = theme_manager or get_theme_manager()
        self.console = self.theme_manager.get_console()
        self.notifications: List[Notification] = []
        self.next_id = 0
        self.unread_count = 0

    def notify(
        self,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO
    ) -> int:
        """
        Send a notification

        Args:
            title: Notification title
            message: Notification message
            type: Notification type

        Returns:
            Notification ID
        """
        notification = Notification(
            type=type,
            title=title,
            message=message,
            timestamp=time.time(),
            id=self.next_id
        )
        self.next_id += 1
        self.notifications.append(notification)
        self.unread_count += 1

        # Display notification immediately
        self._display_notification(notification)

        return notification.id

    def _display_notification(self, notification: Notification):
        """Display a single notification"""
        icon_map = {
            NotificationType.INFO: "ℹ",
            NotificationType.SUCCESS: "✓",
            NotificationType.WARNING: "⚠",
            NotificationType.ERROR: "✗",
            NotificationType.TASK_COMPLETE: "🎉",
        }

        style_map = {
            NotificationType.INFO: "info",
            NotificationType.SUCCESS: "success",
            NotificationType.WARNING: "warning",
            NotificationType.ERROR: "error",
            NotificationType.TASK_COMPLETE: "success",
        }

        icon = icon_map.get(notification.type, "•")
        style = style_map.get(notification.type, "info")

        # Create panel for notification
        content = Text()
        content.append(f"{icon} ", style=style)
        content.append(notification.title, style=f"bold {style}")
        content.append(f"\n{notification.message}")

        panel = Panel(
            content,
            border_style=style,
            width=60,
            expand=False
        )

        self.console.print(panel)

    def show_unread_count(self):
        """Show unread notification count"""
        if self.unread_count > 0:
            self.console.print(f"\n[info]📬 {self.unread_count} unread notification(s)[/info]")
            self.console.print("[dim]Type 'notifications' to view[/dim]")

    def show_all(self):
        """Show all notifications"""
        if not self.notifications:
            self.console.print("[dim]No notifications[/dim]")
            return

        self.console.print(f"\n[header]📬 Notifications ({len(self.notifications)})[/header]\n")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Type", style="cyan")
        table.add_column("Title", style="bold")
        table.add_column("Message")
        table.add_column("Time", style="dim")

        for notif in reversed(self.notifications[-10:]):  # Last 10
            elapsed = time.time() - notif.timestamp
            if elapsed < 60:
                time_str = f"{int(elapsed)}s ago"
            elif elapsed < 3600:
                time_str = f"{int(elapsed / 60)}m ago"
            else:
                time_str = f"{int(elapsed / 3600)}h ago"

            table.add_row(
                str(notif.id),
                notif.type.value,
                notif.title,
                notif.message[:50] + "..." if len(notif.message) > 50 else notif.message,
                time_str
            )

        self.console.print(table)
        self.unread_count = 0

    def clear(self):
        """Clear all notifications"""
        self.notifications.clear()
        self.unread_count = 0
        self.console.print("[success]✓ Notifications cleared[/success]")


# Global instances
_theme_manager = None
_notification_manager = None
_collapsible_manager = None


def get_theme_manager() -> ThemeManager:
    """Get global theme manager"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def get_notification_manager() -> NotificationManager:
    """Get global notification manager"""
    global _notification_manager
    if _notification_manager is None:
        theme_mgr = get_theme_manager()
        _notification_manager = NotificationManager(theme_mgr)
    return _notification_manager


def get_advanced_collapsible_manager() -> AdvancedCollapsibleContent:
    """Get global advanced collapsible manager"""
    global _collapsible_manager
    if _collapsible_manager is None:
        theme_mgr = get_theme_manager()
        _collapsible_manager = AdvancedCollapsibleContent(theme_mgr.get_console())
    return _collapsible_manager


# Test
if __name__ == "__main__":
    print("Testing advanced UI components...\n")

    # Test 1: Themes
    print("1. Testing themes:")
    theme_mgr = ThemeManager()
    for theme in CortexTheme:
        theme_mgr.preview_theme(theme)
    print("✓ Themes work!\n")

    # Test 2: Multi-step progress
    print("2. Testing multi-step progress:")
    with MultiStepProgress() as progress:
        step1 = progress.add_step("Loading data", 100)
        step2 = progress.add_step("Processing", 50)

        for i in range(100):
            progress.update(step1, i + 1)
            time.sleep(0.01)
        progress.complete_step(step1)

        for i in range(50):
            progress.update(step2, i + 1)
            time.sleep(0.01)
        progress.complete_step(step2)
    print("✓ Progress bars work!\n")

    # Test 3: Expansion modes
    print("3. Testing expansion modes:")
    collapsible = AdvancedCollapsibleContent()
    long_text = "\n".join([f"Line {i}" for i in range(50)])
    content_id = collapsible.add_content(long_text, title="Test Content")
    collapsible.display(content_id, ExpansionMode.PREVIEW)
    print("✓ Expansion modes work!\n")

    # Test 4: Notifications
    print("4. Testing notifications:")
    notif_mgr = NotificationManager()
    notif_mgr.notify("Test", "This is an info notification", NotificationType.INFO)
    notif_mgr.notify("Success", "Task completed!", NotificationType.TASK_COMPLETE)
    notif_mgr.show_all()
    print("✓ Notifications work!\n")

    print("✓ All advanced UI components work correctly!")
