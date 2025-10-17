"""
Interactive Prompt - Keyboard shortcuts for Cortex CLI

Provides:
- Ctrl+E: Expand/collapse last collapsible content
- Ctrl+C: Interrupt (standard)
- Ctrl+D: Exit (standard)
"""

from typing import Optional, Callable
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import ANSI


class InteractivePrompt:
    """
    Interactive prompt with keyboard shortcuts

    Features:
    - Ctrl+E: Expand last collapsible content
    - Standard terminal controls
    """

    def __init__(self, expand_callback: Optional[Callable] = None):
        """
        Initialize interactive prompt

        Args:
            expand_callback: Function to call when Ctrl+E is pressed
        """
        self.expand_callback = expand_callback
        self.session = None
        self.last_collapsible_id = None
        self._setup_keybindings()

    def _setup_keybindings(self):
        """Setup keyboard shortcuts"""
        self.kb = KeyBindings()

        @self.kb.add('c-e')
        def _(event):
            """Handle Ctrl+E - Expand last collapsible content"""
            if self.expand_callback and self.last_collapsible_id is not None:
                # Cancel current input
                event.app.exit(result='__expand__')

    def set_last_collapsible_id(self, content_id: int):
        """
        Set the last collapsible content ID for Ctrl+E

        Args:
            content_id: ID of the last collapsed content
        """
        self.last_collapsible_id = content_id

    def prompt(self, message: str) -> str:
        """
        Show prompt and get user input

        Args:
            message: Prompt message

        Returns:
            User input string or special command
        """
        if self.session is None:
            self.session = PromptSession(key_bindings=self.kb)

        try:
            # Convert message to ANSI formatted text if it contains ANSI codes
            result = self.session.prompt(ANSI(message))
            return result
        except KeyboardInterrupt:
            return ''
        except EOFError:
            return 'exit'


# Test
if __name__ == "__main__":
    def test_expand():
        print("\n[Ctrl+E pressed - expanding content 0]")

    print("Testing Interactive Prompt...")
    print()
    print("Instructions:")
    print("- Type normal commands")
    print("- Press Ctrl+E to trigger expand (simulated)")
    print("- Press Ctrl+C to cancel")
    print("- Press Ctrl+D or type 'exit' to quit")
    print()

    prompt = InteractivePrompt(expand_callback=test_expand)
    prompt.set_last_collapsible_id(0)

    while True:
        try:
            user_input = prompt.prompt("test ❯ ")

            if user_input == 'exit':
                break
            elif user_input == '__expand__':
                test_expand()
            elif user_input:
                print(f"You typed: {user_input}")

        except KeyboardInterrupt:
            print("\n^C")
            continue
        except EOFError:
            break

    print("\n✓ Interactive prompt works!")
