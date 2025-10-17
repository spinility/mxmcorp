# Cortex UX Enhancements

## Overview

Cortex now features professional UX enhancements similar to Claude Code, making it more pleasant and efficient to use.

## Features

### 1. 🎯 Dynamic Loading Spinners

Beautiful animated spinners show real-time progress during operations.

**Where you'll see them:**
- ⏳ "Analyzing request type..." (Planning check)
- ⏳ "Triage Agent (gpt-4o-nano) analyzing..." (Triage)
- ⏳ "Loading context from codebase..." (Context Agent)
- ⏳ "🤖 gpt-4o-nano processing your request..." (LLM execution)

**Benefits:**
- Know exactly what Cortex is doing
- Visual feedback during long operations
- Professional, polished interface

---

### 2. 📝 Styled Markdown Rendering

Responses are now rendered with beautiful formatting using Rich.

**Features:**
- **Headers** with proper hierarchy
- **Code blocks** with syntax highlighting
- **Lists** (bulleted and numbered)
- **Bold** and *italic* text
- **Panels** and boxes
- **Colors** and styling

**Example:**

Before (plain text):
```
# Title
This is **bold** and this is *italic*
```

After (rich markdown):
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              Title                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

This is bold and this is italic
```

---

### 3. 📦 Collapsible Content System

Long outputs are automatically collapsed to prevent terminal overflow.

**How it works:**

1. **Auto-collapse:** Content > 20 lines is automatically truncated
2. **Hint displayed:** `... 40 more lines. Press Ctrl+E to expand (ID: 0)`
3. **Expand:** Type `expand 0` or `e 0` to see full content
4. **Re-collapse:** Type `expand 0` again to collapse

**Example:**

```bash
cortex ❯ task list all Python files

# Long output appears...
Line 1
Line 2
...
Line 20

... 80 more lines. Press Ctrl+E to expand (ID: 0)

cortex ❯ e 0

# Full content expands!
Line 1
Line 2
...
Line 100
```

**Where it's used:**
- Tool results with long data
- File contents
- Log outputs
- Any output > 20 lines

---

## Commands

### New Command: `expand`

**Usage:**
```bash
expand <content_id>
e <content_id>        # Shortcut
```

**Examples:**
```bash
cortex ❯ e 0          # Expand content ID 0
cortex ❯ expand 1     # Expand content ID 1
```

---

## Developer Guide

### Using Display Helpers in Custom Code

```python
from cortex.cli.display_helpers import (
    LoadingSpinner,
    render_markdown,
    display_collapsible
)

# 1. Loading spinner
with LoadingSpinner("Processing...") as spinner:
    # Do work
    result = do_something()
    spinner.update("Almost done...")
    finalize()

# 2. Render markdown
markdown_text = """
# Results
- Item 1
- Item 2
"""
render_markdown(markdown_text, title="Output")

# 3. Collapsible content
long_text = "\\n".join([f"Line {i}" for i in range(100)])
content_id = display_collapsible(long_text, max_lines=20)
print(f"Content collapsed with ID: {content_id}")
```

### Creating Custom Spinners

```python
from cortex.cli.display_helpers import LoadingSpinner

# Available spinner types:
# - "dots" (default)
# - "line"
# - "arc"
# - "circle"
# - "bounce"
# - "moon"

with LoadingSpinner("Loading...", spinner_type="arc"):
    do_work()
```

### Custom Collapsible Manager

```python
from cortex.cli.display_helpers import CollapsibleContent

manager = CollapsibleContent(max_lines=30)  # Custom limit

# Display with auto-collapse
content_id = manager.display(long_text, title="Results")

# Manual expand
manager.expand(content_id)

# Manual collapse
manager.collapse(content_id)

# Toggle
manager.toggle(content_id)
```

---

## Configuration

All display settings can be customized in `display_helpers.py`:

```python
# Default max lines before collapse
manager = CollapsibleContent(max_lines=20)

# Spinner refresh rate
live = Live(spinner, refresh_per_second=10)
```

---

## Benefits

### For Users:
✅ **Professional interface** - Looks and feels like Claude Code
✅ **Clear feedback** - Always know what's happening
✅ **No terminal overflow** - Long outputs are managed
✅ **Beautiful rendering** - Markdown looks great

### For Developers:
✅ **Easy to use** - Simple API with context managers
✅ **Reusable** - Global instances available
✅ **Flexible** - Customize spinners, collapse limits, etc.
✅ **Non-blocking** - Spinners don't interfere with logic

---

## Examples in Action

### Example 1: Task Execution

```bash
cortex ❯ task analyze the quality_control_agent.py file

⠋ Analyzing request type...                    # Spinner
→ Direct execution (planning confidence: 0.12)

⠋ Triage Agent (gpt-4o-nano) analyzing...     # Spinner
✓ Route: EXPERT (confidence: 0.85)

⠋ Loading context from codebase...            # Spinner
✓ Context loaded (2 files, 500 lines)

⠋ 🤖 gpt-4o-nano processing your request...   # Spinner

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 RESPONSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Quality Control Agent Analysis

## Overview
The QualityControlAgent analyzes...

## Key Features
• Heuristic scoring (0-100)
• Multi-dimensional evaluation
• Auto-saves recommendations

... (beautiful markdown rendering)
```

### Example 2: Long Output

```bash
cortex ❯ task read all log files

Tool: read_file
Status: SUCCESS
Data (150 lines):
     1. [2025-10-16] Starting Cortex...
     2. [2025-10-16] Loading agents...
     ...
     20. [2025-10-16] Agent initialized

... 130 more lines. Press Ctrl+E to expand (ID: 0)

cortex ❯ e 0

Expanded content (ID: 0):
     1. [2025-10-16] Starting Cortex...
     ...
     150. [2025-10-16] Shutdown complete
```

---

## Troubleshooting

### Spinner not showing?

Check that Rich is installed:
```bash
pip install rich
```

### Content not collapsing?

Content must be > 20 lines by default. Adjust:
```python
display_collapsible(text, max_lines=10)  # Lower threshold
```

### Markdown not rendering?

Ensure your text is valid markdown. Test with:
```python
from cortex.cli.display_helpers import render_markdown
render_markdown("# Test")
```

---

## 4. 🎨 Advanced Theme System

Beautiful, customizable themes for personalization.

**Available Themes:**
- **dark** (default) - Classic dark terminal theme
- **light** - Light, high contrast theme
- **matrix** - Green-on-black Matrix aesthetic
- **ocean** - Blue/cyan oceanic theme
- **sunset** - Warm orange/yellow sunset theme
- **cyberpunk** - Neon magenta/yellow cyberpunk aesthetic

**Usage:**
```bash
cortex ❯ theme              # Show current theme
cortex ❯ theme list         # List all themes
cortex ❯ theme matrix       # Switch to matrix theme
```

**Example:**
```bash
cortex ❯ theme list

🎨 Available Themes
──────────────────
  ● dark (current)
  ○ light
  ○ matrix
  ○ ocean
  ○ sunset
  ○ cyberpunk

cortex ❯ theme cyberpunk
✓ Theme changed to 'cyberpunk'

  Preview:
  [Shows colored examples of theme styles]
```

---

### 5. 🔔 Notification System

Track important events and system changes with notifications.

**Features:**
- Toast-style popup notifications
- Persistent notification history
- Unread notification counter
- Timestamped notification log
- Multiple notification types (info, success, warning, error, task_complete)

**Usage:**
```bash
cortex ❯ notifications      # View all notifications
cortex ❯ notifs             # Short alias
```

**Example:**
```bash
cortex ❯ notifications

📬 Notifications
───────────────

📬 3 unread notification(s)

┏━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ ID ┃ Type          ┃ Title         ┃ Message                  ┃ Time   ┃
┡━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ 2  │ success       │ Task Complete │ Analysis finished        │ 2m ago │
│ 1  │ info          │ Theme Changed │ Now using 'matrix'       │ 5m ago │
│ 0  │ info          │ System        │ Cortex initialized       │ 8m ago │
└────┴───────────────┴───────────────┴──────────────────────────┴────────┘
```

**Where notifications appear:**
- Theme changes
- Background task completion
- System events
- Optimization updates
- Warning/error alerts

---

### 6. 📊 Multi-step Progress Bars

Visual feedback for complex operations with multiple stages.

**Features:**
- Animated progress bars with spinner
- Per-step progress tracking
- Time remaining estimation
- Completion checkmarks
- Custom step descriptions

**Usage (programmatic):**
```python
from cortex.cli.advanced_ui import MultiStepProgress

with MultiStepProgress() as progress:
    # Step 1
    step1 = progress.add_step("Loading data", total=100)
    for i in range(100):
        progress.update(step1, i)
    progress.complete_step(step1)

    # Step 2
    step2 = progress.add_step("Processing", total=50)
    for i in range(50):
        progress.update(step2, i)
    progress.complete_step(step2)
```

**Example output:**
```
⠋ Loading data    ━━━━━━━━━━━━━━━━━━━━ 45% 0:00:12
⏸ Processing      ━━━━━━━━━━░░░░░░░░░░  0% 0:00:00
```

---

### 7. 🔍 Advanced Expansion Modes

Smart content expansion with multiple viewing modes.

**Modes:**
- **preview** - First N lines with expand hint
- **summary** - First + last few lines (great for logs)
- **full** - Complete content

**Usage:**
```bash
cortex ❯ expand 0              # Cycle through modes
cortex ❯ expand 0 preview      # Show preview
cortex ❯ expand 0 summary      # Show summary
cortex ❯ expand 0 full         # Show everything
cortex ❯ e 0                   # Short alias
```

**Example:**
```bash
# Preview mode
Line 1
Line 2
...
Line 10

... 90 more lines.
Commands:
  expand 0 or e 0 - Show full content
  summary 0 - Show summary

# Summary mode
Line 1
Line 2
Line 3

... omitted ...

Line 98
Line 99
Line 100
```

---

## Future Enhancements

Planned improvements:

- [ ] Keyboard shortcut `Ctrl+E` (requires prompt_toolkit integration)
- [ ] Real-time notification updates
- [ ] Interactive theme picker
- [ ] Custom color customization
- [ ] Exportable notification log
- [ ] Notification filtering/search

---

## Credits

Built with:
- **Rich** - Beautiful terminal formatting (https://github.com/Textualize/rich)
- **Python threading** - Non-blocking spinners
- **Claude Code** - Inspiration for UX design

---

Last updated: 2025-10-16
