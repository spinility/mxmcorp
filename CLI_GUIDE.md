# Cortex CLI Guide

## Beautiful Terminal Interface 🎨

Cortex features a stunning terminal interface with:
- **ASCII Art Logo** - Eye-catching MXMCorp Cortex branding
- **Rich Colors** - Full ANSI color support
- **Progress Indicators** - Real-time spinners and progress bars
- **Formatted Tables** - Beautiful data presentation
- **Interactive Prompts** - Smooth command experience

## Quick Start

### Launch Cortex

```bash
python3 cortex_start.py
```

Or directly:

```bash
python3 -m cortex.cli.cortex_cli
```

### Startup Screen

When you launch Cortex, you'll see:

```
   ███╗   ███╗██╗  ██╗███╗   ███╗     ██████╗ ██████╗ ██████╗ ██████╗
   ████╗ ████║╚██╗██╔╝████╗ ████║    ██╔════╝██╔═══██╗██╔══██╗██╔══██╗
   ...
         AI Agent Orchestration System
         ─────────────────────────────
```

## Available Commands

### `help`
Show all available commands with descriptions

```
cortex ❯ help
```

### `status`
Display system overview with stats

```
cortex ❯ status

╭────────────── Overview ──────────────╮
│ Total Agents: 5                      │
│ Active: 2                            │
│ Idle: 3                              │
│ Tasks Completed: 47                  │
│ Total Cost: $0.003456                │
╰──────────────────────────────────────╯
```

### `agents`
Show detailed agent status table

```
cortex ❯ agents

┌──────────┬─────────────────────┬───────────┬───────┐
│ Agent    │ Role                │ Status    │ Tasks │
├──────────┼─────────────────────┼───────────┼───────┤
│ CEO      │ Strategic Director  │ ● Active  │ 15    │
│ CTO      │ Technical Director  │ ◉ Busy    │ 42    │
│ HR       │ HR Director         │ ○ Idle    │ 8     │
│ Finance  │ Finance Director    │ ● Active  │ 23    │
│ Product  │ Product Director    │ ○ Idle    │ 11    │
└──────────┴─────────────────────┴───────────┴───────┘
```

Status indicators:
- `● Active` (green) - Agent ready and working
- `◉ Busy` (cyan) - Agent currently processing
- `○ Idle` (yellow) - Agent waiting for tasks
- `◌ Unknown` (gray) - Status unavailable

### `costs`
Show cost breakdown by model

```
cortex ❯ costs

nano       ████████████████████░░░░ $0.002145 (54.2%)
deepseek   ███████░░░░░░░░░░░░░░░░░ $0.001234 (31.2%)
claude     ██░░░░░░░░░░░░░░░░░░░░░░ $0.000567 (14.3%)

Total      $0.003946
```

### `task <description>`
Execute a task with real-time progress

```
cortex ❯ task Add validation to User model

[████████████████████] 100% (6/6)  Validating output

✓ Task completed successfully!
```

Progress shows:
1. Analyzing task with nano self-assessment
2. Severity and confidence detection
3. Context building
4. Model execution
5. Output validation

### `clear` / `cls`
Clear the terminal screen

```
cortex ❯ clear
```

### `history`
Show recent command history

```
cortex ❯ history

  1  status
  2  agents
  3  task Add validation
  4  costs
```

### `logo`
Display the Cortex logo

```
cortex ❯ logo
```

### `demo`
Show all CLI features in action

```
cortex ❯ demo

✓ Color support
✓ Boxes
✓ Tables
✓ Progress bars
```

### `exit` / `quit`
Exit Cortex gracefully

```
cortex ❯ exit

✓ Cortex shutdown complete. Goodbye!
```

## Features in Detail

### Color Coding

Cortex uses colors to convey meaning:

- **Green (✓)** - Success, completion, active status
- **Red (✗)** - Errors, failures, critical issues
- **Yellow (⚠)** - Warnings, pending actions, idle status
- **Cyan (ℹ)** - Information, data, processing
- **Magenta** - Special highlights
- **Blue** - Headers, structure

### Progress Indicators

#### Spinners
Animated spinners for quick operations:
```
⠋ Loading agent configurations...
```

#### Progress Bars
Visual progress for multi-step tasks:
```
[████████████████████░░░░░░░░░░░] 60% (3/5)
```

### Box Formatting

Information displayed in beautiful boxes:

```
╭────────────── System Info ──────────────╮
│ Version: 1.0.0-alpha                    │
│ Environment: production                 │
│ Initialized: 2025-10-15 10:30:00        │
╰─────────────────────────────────────────╯
```

### Tables

Data presented in formatted tables:

```
┌──────────┬──────────┬────────┐
│ Model    │ Cost/1M  │ Speed  │
├──────────┼──────────┼────────┤
│ nano     │ $0.05    │ Fast   │
│ deepseek │ $0.28    │ Medium │
│ claude   │ $3.00    │ Slow   │
└──────────┴──────────┴────────┘
```

## Tips & Tricks

### Keyboard Shortcuts

- **Ctrl+C** - Interrupt current operation (returns to prompt)
- **Ctrl+D** or **Ctrl+Z** - Exit Cortex
- **↑/↓** - Navigate command history (if readline available)

### Command Aliases

Some commands have shorter versions:
- `cls` → `clear`
- `quit` → `exit`

### Piping Output

Cortex output can be piped to other tools:

```bash
python3 cortex_start.py < commands.txt > output.log
```

### Non-Interactive Mode

Run commands directly:

```bash
echo "status" | python3 cortex_start.py
```

### Disable Colors

For CI/CD or terminals without ANSI support:

```bash
NO_COLOR=1 python3 cortex_start.py
```

## Customization

### Modify Logo

Edit `cortex/cli/terminal_ui.py`:

```python
CORTEX_LOGO = """
Your custom ASCII art here
"""
```

### Change Colors

Modify color scheme in `TerminalUI` class:

```python
# Use different colors for status
if status == "active":
    status_display = ui.color("● Active", Color.BLUE)  # Changed to blue
```

### Add Custom Commands

Extend `CortexCLI` class:

```python
def cmd_mycustom(self, args: str):
    """My custom command"""
    self.ui.info("Custom command executed!")
```

Then register in `execute_command()`:

```python
elif cmd == "mycustom":
    self.cmd_mycustom(args)
```

## Troubleshooting

### Colors Not Showing

**Problem**: Terminal shows escape codes instead of colors

**Solution**:
- Check terminal supports ANSI colors
- Update terminal emulator
- Try different terminal (iTerm2, Windows Terminal, etc.)

### Permission Denied

**Problem**: `Permission denied` when running scripts

**Solution**:
```bash
chmod +x cortex_start.py
chmod +x cortex/cli/cortex_cli.py
```

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'cortex'`

**Solution**:
```bash
# Run from project root
cd /path/to/mxmcorp
python3 cortex_start.py

# Or add to PYTHONPATH
export PYTHONPATH=/path/to/mxmcorp:$PYTHONPATH
```

### Slow Startup

**Problem**: Startup screen takes long time

**Solution**:
- Disable animations by setting shorter durations
- Use `show_startup_screen(show_system_info=False)`

## Examples

### Daily Workflow

```bash
# Start Cortex
python3 cortex_start.py

# Check system status
cortex ❯ status

# View agents
cortex ❯ agents

# Execute some tasks
cortex ❯ task Refactor authentication module
cortex ❯ task Add tests for User model
cortex ❯ task Update documentation

# Check costs
cortex ❯ costs

# Exit when done
cortex ❯ exit
```

### Quick Status Check

```bash
# One-liner to check status
echo "status" | python3 cortex_start.py
```

### Batch Task Execution

```bash
# Create task file
cat > tasks.txt << EOF
task Add validation
task Fix bug in login
task Update dependencies
costs
EOF

# Run all tasks
python3 cortex_start.py < tasks.txt
```

## API Reference

### TerminalUI Class

```python
from cortex.cli import TerminalUI, Color

ui = TerminalUI()

# Basic colors
ui.color("text", Color.GREEN)
ui.color("bold text", Color.CYAN, bold=True)

# Gradient effect
ui.gradient("rainbow text", Color.CYAN, Color.MAGENTA)

# Messages
ui.success("Operation completed!")
ui.error("Something went wrong")
ui.warning("Please check configuration")
ui.info("Processing data...")

# Formatting
ui.box("content", width=50, color=Color.BLUE, title="Title")
ui.table(["Col1", "Col2"], [["a", "b"], ["c", "d"]])
ui.progress_bar(current=7, total=10, width=40, label="Progress")

# Interactive
ui.spinner("Loading...", duration=2.0)
```

### Helper Functions

```python
from cortex.cli import (
    show_startup_screen,
    show_agent_status,
    show_cost_summary,
    show_help
)

# Show startup
show_startup_screen()

# Show agent table
agents = [
    {"name": "CEO", "role": "Director", "status": "active", "tasks_completed": 10}
]
show_agent_status(agents)

# Show costs
costs = {"nano": 0.001, "deepseek": 0.002, "claude": 0.003}
show_cost_summary(costs)

# Show help
show_help()
```

## Contributing

Want to improve the CLI? Here's how:

1. **Add new visual elements** in `terminal_ui.py`
2. **Add new commands** in `cortex_cli.py`
3. **Test thoroughly** with different terminals
4. **Update this guide** with your changes

## Future Enhancements

Planned features:
- [ ] Real-time streaming output
- [ ] Interactive task selection menu
- [ ] Agent performance graphs
- [ ] Cost projections
- [ ] Command autocompletion
- [ ] Configuration wizard
- [ ] Export reports to file

## Credits

Inspired by:
- **Claude Code** - Beautiful TUI
- **Rich** - Python library for terminal formatting
- **Charm** - CLI toolkit inspiration

---

**Cortex CLI** - Making AI agent orchestration beautiful! 🎨✨
