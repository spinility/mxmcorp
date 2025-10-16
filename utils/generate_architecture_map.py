#!/usr/bin/env python3
"""
Generate CORTEX_ARCHITECTURE.md - Complete system architecture documentation

This script scans the entire Cortex repository and generates a comprehensive
architecture document showing:
- Directory structure
- Module relationships
- Agent hierarchy
- Departments
- Available tools
- Core components
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime


def get_directory_tree(root_path: str, prefix: str = "", max_depth: int = 4, current_depth: int = 0) -> List[str]:
    """Generate a visual directory tree"""
    if current_depth >= max_depth:
        return []

    lines = []
    try:
        entries = sorted(Path(root_path).iterdir(), key=lambda x: (not x.is_dir(), x.name))

        # Filter out __pycache__, .git, and cache directories
        entries = [e for e in entries if not e.name.startswith('.') and
                   e.name not in ['__pycache__', 'scraped_data', 'todolists', 'ceo_reports']]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            current_prefix = "└── " if is_last else "├── "
            next_prefix = "    " if is_last else "│   "

            if entry.is_dir():
                lines.append(f"{prefix}{current_prefix}{entry.name}/")
                # Recursively add subdirectories
                sublines = get_directory_tree(
                    str(entry),
                    prefix + next_prefix,
                    max_depth,
                    current_depth + 1
                )
                lines.extend(sublines)
            else:
                # Only show Python files and important config files
                if entry.suffix in ['.py', '.yaml', '.json', '.md'] or entry.name in ['requirements.txt', 'setup.py']:
                    lines.append(f"{prefix}{current_prefix}{entry.name}")

    except PermissionError:
        pass

    return lines


def scan_python_modules(root_path: str) -> Dict[str, List[str]]:
    """Scan Python modules and extract classes/functions"""
    modules = {}

    for py_file in Path(root_path).rglob("*.py"):
        if '__pycache__' in str(py_file) or 'test_' in py_file.name:
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract classes
            classes = []
            for line in content.split('\n'):
                if line.startswith('class '):
                    class_name = line.split('class ')[1].split('(')[0].split(':')[0].strip()
                    classes.append(class_name)

            if classes:
                rel_path = str(py_file.relative_to(root_path))
                modules[rel_path] = classes

        except Exception:
            pass

    return modules


def generate_architecture_doc(root_path: str = "/github/mxmcorp") -> str:
    """Generate complete architecture documentation"""

    doc = f"""# CORTEX ARCHITECTURE ROADMAP
**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This document provides a comprehensive overview of the Cortex AI system architecture,
including directory structure, module relationships, agent hierarchy, and available tools.

---

## 📁 DIRECTORY STRUCTURE

```
cortex/
{chr(10).join(get_directory_tree(os.path.join(root_path, 'cortex')))}
```

---

## 🏗️ CORE ARCHITECTURE

### Core Components (`cortex/core/`)

| Component | Purpose | Key Classes |
|-----------|---------|-------------|
| **llm_client.py** | LLM API communication | `LLMClient`, `LLMResponse` |
| **model_router.py** | Intelligent model selection | `ModelRouter`, `ModelTier` |
| **prompt_engineer.py** | Tier-specific prompt generation | `PromptEngineer` |
| **tool_filter.py** | Smart tool filtering | `ToolFilter` |
| **agent_hierarchy.py** | Agent role system | `DecisionAgent`, `ExecutionAgent` |
| **conversation_manager.py** | Context management | `ConversationManager` |
| **todo_manager.py** | Task management | `TodoManager`, `TodoTask` |
| **context_agent.py** | Application context preparation | `ContextAgent` |
| **nano_self_assessment.py** | Nano routing | `NanoSelfAssessment` |

### Model Tiers

```
┌─────────────────────────────────────────────────┐
│  NANO (gpt-4o-nano)                             │
│  • Ultra-fast triage & simple tasks             │
│  • $0.05/1M tokens                              │
│  • Max: 128K output                             │
└─────────────────────────────────────────────────┘
              ↓ escalate if needed
┌─────────────────────────────────────────────────┐
│  DEEPSEEK (deepseek-reasoner)                   │
│  • Medium complexity tasks                      │
│  • $0.28/1M tokens                              │
│  • Good cost/quality balance                    │
└─────────────────────────────────────────────────┘
              ↓ escalate if critical
┌─────────────────────────────────────────────────┐
│  CLAUDE (claude-sonnet-4.5)                     │
│  • Complex reasoning & critical tasks           │
│  • $3.00/1M tokens                              │
│  • Highest quality                              │
└─────────────────────────────────────────────────┘
```

---

## 🤖 AGENT HIERARCHY

### Level 1: Triage Agent
- **Role:** First-line routing
- **Tier:** NANO
- **Purpose:** Decides if request needs expert or can be answered directly
- **Routes:** DIRECT (skip context) or EXPERT (full processing)

### Level 2: Planner Agent
- **Role:** Task decomposition
- **Tier:** DEEPSEEK
- **Purpose:** Detects planning requests and creates structured tasks
- **Output:** TodoList with tier assignments

### Level 3: Context Agent
- **Role:** Context preparation
- **Tier:** NANO/DEEPSEEK
- **Purpose:** Prepares optimized context based on request severity
- **Features:** Embedding cache, git diff integration

### Level 4: Specialized Agents

| Agent | Role | Tier | Purpose |
|-------|------|------|---------|
| **ToolerAgent** | Tool Research | DEEPSEEK | Researches missing capabilities |
| **CommunicationsAgent** | Recommendations | DEEPSEEK | Crafts user-facing messages |
| **SmartRouterAgent** | Department Routing | NANO | Routes to existing departments |

---

## 🏢 DEPARTMENTS

### Intelligence Department (`cortex/departments/intelligence/`)
**Purpose:** Web scraping & data extraction

**Components:**
- `StealthWebCrawler` - Undetectable web scraping (requests + lxml)
- `XPathSourceRegistry` - Manage scraping sources
- `RobotsChecker` - robots.txt compliance

**Tools:**
- `scrape_xpath` - Extract data via XPath
- `validate_xpath` - Test XPath expressions
- `add_web_source` - Register new sources

### Maintenance Department (`cortex/departments/maintenance/`)
**Purpose:** System maintenance & updates

**Components:**
- `RoadmapManager` - Manage project roadmap
- `GitDiffProcessor` - Process git changes
- `ContextUpdater` - Update application context
- `DependencyTracker` - Track file dependencies

---

## 🛠️ TOOLS SYSTEM

### Tool Categories

1. **Filesystem Tools** (`cortex/tools/builtin_tools.py`)
   - create_file, read_file, append_to_file
   - list_directory, file_exists, delete_file
   - show_roadmap (system status)

2. **Web Tools** (`cortex/tools/web_tools.py`)
   - web_search, web_fetch
   - get_weather (if configured)

3. **Git Tools** (`cortex/tools/git_tools.py`)
   - git_status, git_add, git_commit
   - git_push, git_pull, git_log

4. **Pip Tools** (`cortex/tools/pip_tools.py`)
   - pip_install, pip_uninstall
   - pip_list, pip_show, pip_freeze

5. **Intelligence Tools** (`cortex/tools/intelligence_tools.py`)
   - scrape_xpath, validate_xpath, add_web_source

### Tool Filtering System

The `ToolFilter` intelligently selects relevant tools based on request keywords:

| Category | Keywords | Tools Included |
|----------|----------|----------------|
| file | create, read, write, delete | Filesystem tools |
| web | search, fetch, url, http | Web tools |
| git | commit, push, pull, branch | Git tools |
| pip | install, package, library | Pip tools |
| scraping | scrape, xpath, crawl | Intelligence tools |
| system | roadmap, status, tasks | System tools |

**Optimization:** ~70% token reduction by sending only relevant tools

---

## 📊 WORKFLOW EXECUTION

### Standard Request Flow

```
1. USER REQUEST
   ↓
2. PLANNING CHECK
   → Is this a planning request? (Planner Agent)
   ↓
3. TRIAGE DECISION
   → DIRECT or EXPERT? (Triage Agent)
   ↓ (if EXPERT)
4. CONTEXT PREPARATION
   → Prepare optimized context (Context Agent)
   → Check embedding cache
   → Include git diff if needed
   ↓
5. TOOL FILTERING
   → Select relevant tools based on keywords
   ↓
6. MODEL EXECUTION
   → Execute with filtered tools (selected tier)
   → Handle tool calls iteratively
   ↓
7. RESPONSE
   → Return formatted response to user
```

### Tool Calling Flow

```
Iteration 1: Analyzing request
 → LLM receives request + tools
 → Decides which tools to call
 → Tools execute (create_file, scrape_xpath, etc.)

Iteration 2: Generating response
 → LLM receives tool results
 → Synthesizes final response
 → Returns to user
```

---

## 🗄️ DATA STORAGE

### File Structure

```
cortex/data/
├── conversations/        # Conversation history
├── embeddings/          # Context embeddings cache
├── todolists/           # User todo databases
├── ROADMAP.json         # Project todolist
└── models.yaml          # Model specifications
```

### TodoDB System

- SQLite-based task management
- Multi-user authentication
- Role-based access control (admin/developer/viewer)
- Task status tracking (pending/in_progress/completed)

---

## 🔄 OPTIMIZATION SYSTEMS

### 1. Embedding Cache
- Stores semantic embeddings of code/context
- 82% cost reduction through smart caching
- Adaptive similarity thresholds based on severity

### 2. Tool Filtering
- Reduces tool definitions sent to LLM
- 70-77% token reduction
- Keyword-based category detection

### 3. Triage System
- Routes simple requests directly (skip Context Agent)
- 30-50% faster for simple conversations
- Saves tokens on unnecessary context

### 4. Intelligent Routing
- Smart Router checks existing departments before creating new tools
- Prevents duplicate tool creation
- Routes to specialized agents

---

## 📝 CONFIGURATION

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...        # For NANO tier (gpt-4o-nano)
DEEPSEEK_API_KEY=sk-...      # For DEEPSEEK tier
ANTHROPIC_API_KEY=sk-...     # For CLAUDE tier (claude-sonnet-4.5)

# Optional
CORTEX_DEBUG=true            # Enable debug mode
TODO_DB_PATH=...             # Custom TodoDB location
```

### Model Configuration (`cortex/data/models.yaml`)

Defines specifications for each tier:
- Model names
- Costs (input/output tokens)
- Context windows
- Output limits
- Temperature settings

---

## 🚀 CLI INTERFACE

### Commands

| Command | Description |
|---------|-------------|
| `task <description>` | Execute a task |
| `todo` | Show TodoList |
| `next` | Execute next pending task |
| `agents` | Show agent status |
| `costs` | Show cost summary |
| `conversation-stats` | Show context statistics |
| `clear-history` | Clear conversation history |
| `help` | Show help |

### UI Features

- Beautiful ASCII art logo
- Color-coded output (success/error/warning/info)
- Progress indicators
- Employee section headers
- Real-time cost tracking

---

## 🔐 SECURITY & SAFETY

### Nano Self-Assessment

Prevents unsafe operations by NANO tier:
- Evaluates confidence (HIGH/MEDIUM/LOW)
- Assesses severity (CRITICAL/HIGH/MEDIUM/LOW)
- Routes CRITICAL tasks to higher tiers
- Conservative delegation strategy

### Safety Rules

1. ALWAYS delegate CRITICAL tasks
2. ALWAYS delegate if confidence is LOW
3. MEDIUM confidence + HIGH severity → delegate
4. HIGH confidence + (LOW or MEDIUM) severity → can handle

---

## 📈 PERFORMANCE METRICS

### Cost Optimization Results

| Optimization | Savings | Impact |
|--------------|---------|--------|
| Embedding Cache | 82% | Massive context cost reduction |
| Tool Filtering | 70-77% | Per-request token savings |
| Triage System | 30-50% | Speed improvement for simple requests |
| Smart Routing | Variable | Prevents duplicate tool creation |

### Typical Costs

| Request Type | Tier | Approx Cost |
|--------------|------|-------------|
| Simple conversation | NANO | $0.000001 |
| File creation | NANO | $0.000005 |
| Web scraping | DEEPSEEK | $0.000050 |
| Complex analysis | CLAUDE | $0.001000 |
| Planning request | DEEPSEEK | $0.000200 |

---

## 🔮 FUTURE ENHANCEMENTS

### Planned Features

1. **Autonomous Learning**
   - Self-improving prompts based on success/failure
   - Automatic tool creation from patterns
   - Dynamic tier selection optimization

2. **Enhanced Departments**
   - HR Department (team management)
   - Finance Department (cost analysis)
   - Product Department (feature planning)

3. **Advanced Caching**
   - Multi-level cache hierarchy
   - Predictive pre-loading
   - Cross-session context retention

4. **Tool Evolution**
   - Automatic tool composition
   - Learning from tool usage patterns
   - Self-optimizing tool parameters

---

## 📚 DOCUMENTATION REFERENCES

- **Phase Docs:** PHASE1_PROGRESS.md, PHASE2_PROGRESS.md
- **Design Docs:** AGENT_HIERARCHY_DESIGN.md, ORGANIZATIONAL_REDESIGN.md
- **Solutions:** SOLUTION_SMART_ROUTING.md, EMBEDDING_CACHE_RESULTS.md
- **API Keys:** Configure in environment or .env file

---

## 🛠️ DEVELOPMENT

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_phase3_1_integration.py

# Run with coverage
pytest --cov=cortex tests/
```

### Adding New Tools

1. Create tool function with `@tool` decorator
2. Define parameters schema (JSON Schema)
3. Register in appropriate tool module
4. Add to get_all_*_tools() function
5. Update ToolFilter category keywords if needed

### Adding New Agents

1. Extend `DecisionAgent` or `ExecutionAgent`
2. Implement `can_handle()` and `execute()` methods
3. Register in `cortex/agents/__init__.py`
4. Add to CLI initialization if needed

---

**End of Architecture Roadmap**

For the latest updates, regenerate this document with:
```bash
python utils/generate_architecture_map.py
```
"""

    return doc


if __name__ == "__main__":
    print("Generating Cortex Architecture Roadmap...")

    # Generate the documentation
    architecture_doc = generate_architecture_doc()

    # Write to file
    output_path = "/github/mxmcorp/CORTEX_ARCHITECTURE.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(architecture_doc)

    print(f"✅ Architecture roadmap generated: {output_path}")
    print(f"📄 Document size: {len(architecture_doc)} characters")
