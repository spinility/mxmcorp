"""
Display Helpers - Enhanced UX for Cortex CLI

Provides:
1. Loading spinners during processing
2. Styled markdown rendering
3. Collapsible content for long outputs
"""

import sys
import threading
import time
from typing import Optional, List
from rich.console import Console
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.live import Live
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text


class LoadingSpinner:
    """
    Dynamic loading spinner like Claude Code

    Usage:
        with LoadingSpinner("Processing request..."):
            # Do work
            pass
    """

    def __init__(self, message: str, spinner_type: str = "dots"):
        """
        Initialize loading spinner

        Args:
            message: Message to display
            spinner_type: Type of spinner (dots, line, arc, etc.)
        """
        self.message = message
        self.spinner_type = spinner_type
        self.console = Console()
        self.live = None
        self._stop = False

    def __enter__(self):
        """Start spinner"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop spinner"""
        self.stop()

    def start(self):
        """Start the spinner"""
        spinner = Spinner(self.spinner_type, text=self.message, style="cyan")
        self.live = Live(spinner, console=self.console, refresh_per_second=10)
        self.live.start()

    def stop(self, final_message: Optional[str] = None):
        """
        Stop the spinner

        Args:
            final_message: Optional final message to display
        """
        if self.live:
            self.live.stop()
            if final_message:
                self.console.print(f"[green]✓[/green] {final_message}")

    def update(self, message: str):
        """
        Update spinner message

        Args:
            message: New message
        """
        if self.live:
            spinner = Spinner(self.spinner_type, text=message, style="cyan")
            self.live.update(spinner)


class MarkdownRenderer:
    """
    Styled markdown renderer using Rich

    Renders markdown with beautiful formatting, code highlighting, etc.
    """

    def __init__(self):
        """Initialize markdown renderer"""
        self.console = Console()

    def render(self, markdown_text: str, title: Optional[str] = None):
        """
        Render markdown text with styling

        Args:
            markdown_text: Markdown text to render
            title: Optional title for panel
        """
        md = Markdown(markdown_text)

        if title:
            panel = Panel(md, title=title, border_style="cyan", expand=False)
            self.console.print(panel)
        else:
            self.console.print(md)

    def render_code(self, code: str, language: str = "python", line_numbers: bool = True):
        """
        Render code with syntax highlighting

        Args:
            code: Code to render
            language: Programming language
            line_numbers: Show line numbers
        """
        syntax = Syntax(code, language, theme="monokai", line_numbers=line_numbers)
        self.console.print(syntax)


class CollapsibleContent:
    """
    Manages collapsible content for long outputs

    Usage:
        content_manager = CollapsibleContent()
        content_manager.display(long_text, max_lines=20)

        # Later, user presses Ctrl+E
        content_manager.toggle_expand(content_id)
    """

    def __init__(self, max_lines: int = 20):
        """
        Initialize collapsible content manager

        Args:
            max_lines: Maximum lines before collapsing
        """
        self.max_lines = max_lines
        self.console = Console()
        self.collapsed_contents = {}  # Store full content by ID
        self.next_id = 0

    def should_collapse(self, text: str) -> bool:
        """
        Check if content should be collapsed

        Args:
            text: Text to check

        Returns:
            True if text is longer than max_lines
        """
        return text.count('\n') > self.max_lines

    def display(self, text: str, title: Optional[str] = None, collapse: bool = True) -> Optional[int]:
        """
        Display text with automatic collapse if too long

        Args:
            text: Text to display
            title: Optional title
            collapse: Whether to auto-collapse long content

        Returns:
            Content ID if collapsed, None otherwise
        """
        lines = text.split('\n')

        if collapse and len(lines) > self.max_lines:
            # Store full content
            content_id = self.next_id
            self.next_id += 1
            self.collapsed_contents[content_id] = text

            # Display truncated version
            truncated = '\n'.join(lines[:self.max_lines])

            if title:
                self.console.print(f"\n[bold cyan]{title}[/bold cyan]")

            self.console.print(truncated)

            # Show expand hint
            remaining = len(lines) - self.max_lines
            hint = f"\n[dim]... {remaining} more lines. Press [bold]Ctrl+E[/bold] to expand (ID: {content_id})[/dim]"
            self.console.print(hint)

            return content_id
        else:
            # Display full content
            if title:
                self.console.print(f"\n[bold cyan]{title}[/bold cyan]")
            self.console.print(text)
            return None

    def expand(self, content_id: int):
        """
        Expand a collapsed content

        Args:
            content_id: ID of content to expand
        """
        if content_id in self.collapsed_contents:
            self.console.print(f"\n[bold green]Expanded content (ID: {content_id}):[/bold green]")
            self.console.print(self.collapsed_contents[content_id])
        else:
            self.console.print(f"[yellow]No collapsed content with ID {content_id}[/yellow]")

    def collapse(self, content_id: int):
        """
        Collapse an expanded content (re-truncate)

        Args:
            content_id: ID of content to collapse
        """
        if content_id in self.collapsed_contents:
            text = self.collapsed_contents[content_id]
            lines = text.split('\n')
            truncated = '\n'.join(lines[:self.max_lines])

            self.console.print(f"\n[bold yellow]Collapsed content (ID: {content_id}):[/bold yellow]")
            self.console.print(truncated)

            remaining = len(lines) - self.max_lines
            hint = f"\n[dim]... {remaining} more lines. Press [bold]Ctrl+E[/bold] to expand (ID: {content_id})[/dim]"
            self.console.print(hint)
        else:
            self.console.print(f"[yellow]No collapsed content with ID {content_id}[/yellow]")

    def toggle(self, content_id: int):
        """
        Toggle expand/collapse state

        Args:
            content_id: ID of content to toggle
        """
        # For simplicity, just expand (in real app, would track state)
        self.expand(content_id)

    def clear(self):
        """Clear all collapsed content cache"""
        self.collapsed_contents.clear()
        self.next_id = 0


# Global instances for easy access
_markdown_renderer = None
_collapsible_manager = None


def get_markdown_renderer() -> MarkdownRenderer:
    """Get global markdown renderer instance"""
    global _markdown_renderer
    if _markdown_renderer is None:
        _markdown_renderer = MarkdownRenderer()
    return _markdown_renderer


def get_collapsible_manager() -> CollapsibleContent:
    """Get global collapsible content manager instance"""
    global _collapsible_manager
    if _collapsible_manager is None:
        _collapsible_manager = CollapsibleContent()
    return _collapsible_manager


def render_markdown(text: str, title: Optional[str] = None):
    """
    Quick helper to render markdown

    Args:
        text: Markdown text
        title: Optional title
    """
    renderer = get_markdown_renderer()
    renderer.render(text, title)


def display_collapsible(text: str, title: Optional[str] = None, max_lines: int = 20) -> Optional[int]:
    """
    Quick helper to display collapsible content

    Args:
        text: Text to display
        title: Optional title
        max_lines: Max lines before collapse

    Returns:
        Content ID if collapsed
    """
    manager = get_collapsible_manager()
    manager.max_lines = max_lines
    return manager.display(text, title)


# Test
if __name__ == "__main__":
    print("Testing display helpers...\n")

    # Test 1: Loading spinner
    print("1. Testing loading spinner:")
    with LoadingSpinner("Processing...") as spinner:
        time.sleep(2)
        spinner.update("Almost done...")
        time.sleep(1)
    print("✓ Spinner works!\n")

    # Test 2: Markdown rendering
    print("2. Testing markdown rendering:")
    md_text = """
# Test Markdown

This is **bold** and this is *italic*.

## Code Example

```python
def hello():
    print("Hello, World!")
```

- Item 1
- Item 2
- Item 3
"""
    render_markdown(md_text, title="Example Document")
    print("✓ Markdown works!\n")

    # Test 3: Collapsible content
    print("3. Testing collapsible content:")
    long_text = "\n".join([f"Line {i}" for i in range(50)])
    content_id = display_collapsible(long_text, title="Long Content", max_lines=10)
    print(f"✓ Collapsed with ID: {content_id}\n")

    print("✓ All display helpers work correctly!")
