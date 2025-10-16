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
from cortex.core.tool_filter import ToolFilter
from cortex.tools.tool_executor import ToolExecutor
from cortex.tools.builtin_tools import get_all_builtin_tools
from cortex.tools.web_tools import get_all_web_tools
from cortex.tools.git_tools import get_all_git_tools
from cortex.tools.pip_tools import get_all_pip_tools
from cortex.tools.intelligence_tools import get_all_intelligence_tools

# Cortex agents
from cortex.agents import create_triage_agent, create_tooler_agent, create_communications_agent, create_planner_agent
from cortex.agents.context_agent import create_context_agent
from cortex.agents.smart_router_agent import create_smart_router_agent

# Cortex managers
from cortex.core.todo_manager_wrapper import create_todo_manager, TaskStatus  # Using TodoDB backend
from cortex.core.conversation_manager import create_conversation_manager


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
        self.tool_filter = ToolFilter()
        self.tool_executor = ToolExecutor(self.llm_client)

        # Core managers
        self.todo_manager = create_todo_manager()
        self.conversation_manager = create_conversation_manager(self.llm_client)

        # Specialized agents
        self.triage_agent = create_triage_agent(self.llm_client)
        self.tooler_agent = create_tooler_agent(self.llm_client)
        self.communications_agent = create_communications_agent(self.llm_client)
        self.planner_agent = create_planner_agent(self.llm_client, self.todo_manager)
        self.context_agent = create_context_agent(self.llm_client)
        self.smart_router = create_smart_router_agent(self.llm_client)

        # Current employee handling requests
        self.current_employee = "Cortex"  # Default employee
        self.employee_stack = []  # Stack for nested employee calls

        # Register built-in tools
        self.available_tools = get_all_builtin_tools()

        # Register web tools (search, fetch, weather)
        web_tools = get_all_web_tools()
        self.available_tools.extend(web_tools)

        # Register git tools (status, add, commit, push, pull, log)
        git_tools = get_all_git_tools()
        self.available_tools.extend(git_tools)

        # Register pip tools (install, uninstall, list, show, freeze)
        pip_tools = get_all_pip_tools()
        self.available_tools.extend(pip_tools)

        # Register intelligence tools (scrape_xpath, validate_xpath, add_web_source)
        intelligence_tools = get_all_intelligence_tools()
        self.available_tools.extend(intelligence_tools)

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

        elif cmd == "todo" or cmd == "todos":
            self.cmd_show_todos()

        elif cmd == "next":
            self.cmd_execute_next_task()

        elif cmd == "conversation-stats":
            self.cmd_conversation_stats()

        elif cmd == "users":
            self.cmd_list_users()

        elif cmd == "whoami":
            self.cmd_whoami()

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

        # Add user message to conversation manager
        self.conversation_manager.add_message("user", description)

        try:
            # Step 0: Check if this is a planning request
            print(f"{self.ui.color('→', Color.BRIGHT_BLUE)} Checking if planning is needed...")
            is_planning, confidence = self.planner_agent.is_planning_request(description)

            if is_planning and confidence > 0.6:
                print(f"  {self.ui.color('Planning detected!', Color.GREEN)} (confidence: {confidence:.2f})")
                print()
                self._handle_planning_request(description)
                return

            print(f"  {self.ui.color('Direct execution', Color.CYAN)} (planning confidence: {confidence:.2f})")
            print()

            # Step 1: Model selection
            selection = self.model_router.select_model(description)

            # Step 2: Triage - Decide if we need Context Agent or can respond directly
            print(f"{self.ui.color('→', Color.BRIGHT_BLUE)} Triage Agent ({self.ui.color(selection.model_name, Color.GREEN)}) analyzing request...")
            triage_decision = self.triage_agent.triage_request(description)

            print(f"  Route: {self.ui.color(triage_decision['route'].upper(), Color.CYAN)} (confidence: {triage_decision['confidence']:.2f})")
            print(f"  Reason: {triage_decision['reason']}")
            print()

            # Update costs
            self.total_cost += triage_decision.get('cost', 0.0)

            # Step 3: Context Agent - Only if needed
            context_result = {'context': '', 'metadata': {'context_needed': {'needed': False, 'reason': 'Triage decided direct response', 'confidence': 1.0}, 'cache_hits': [], 'git_diff_included': False, 'total_cost': 0.0}}

            if triage_decision['route'] == 'expert' and triage_decision.get('needs_context', True):
                self._show_employee_section(f"Context Agent ({selection.model_name})", "Preparing optimized context...")
                print()

                context_result = self.context_agent.prepare_context_for_request(
                    user_request=description,
                    target_tier=selection.tier
                )

            # Display context preparation results (only if Context Agent was called)
            if triage_decision['route'] == 'expert' and triage_decision.get('needs_context', True):
                context_needed = context_result['metadata']['context_needed']
                print(f"  Context needed: {self.ui.color('YES' if context_needed['needed'] else 'NO', Color.GREEN if context_needed['needed'] else Color.YELLOW)}")
                print(f"  Reason: {context_needed['reason']}")
                print(f"  Confidence: {context_needed['confidence']:.0%}")

                if context_result['metadata']['cache_hits']:
                    print(f"  {self.ui.color('✓', Color.GREEN)} Cache hits: {len(context_result['metadata']['cache_hits'])}")
                    for hit in context_result['metadata']['cache_hits']:
                        print(f"    • {hit['id']} (similarity: {hit['similarity']:.2f})")

                if context_result['metadata']['git_diff_included']:
                    print(f"  {self.ui.color('✓', Color.GREEN)} Git diff included")
                print()

            # Step 2: Build optimized prompt with dynamic tool context
            print(f"{self.ui.color('→', Color.BRIGHT_BLUE)} Building optimized prompt for {selection.tier.value}...")
            system_prompt = self.prompt_engineer.build_agent_prompt(
                tier=selection.tier,
                user_request=description,
                available_tools=self.available_tools
            )

            # Build messages
            messages = [{"role": "system", "content": system_prompt}]

            # Add application context if provided
            if context_result['context']:
                messages.append({"role": "system", "content": f"APPLICATION CONTEXT:\n{context_result['context']}"})

            # Add recent conversation history (last 5 exchanges)
            for exchange in self.conversation_history[-5:]:
                messages.append({"role": "user", "content": exchange["user"]})
                messages.append({"role": "assistant", "content": exchange["assistant"]})

            # Add current task
            messages.append({"role": "user", "content": description})

            # Track context cost
            self.total_cost += context_result['metadata']['total_cost']

            print()

            # Step 3: Filter relevant tools to reduce token costs
            print(f"{self.ui.color('→', Color.BRIGHT_BLUE)} Filtering relevant tools...")
            filtered_tools = self.tool_filter.filter_tools(description, self.available_tools)
            print(f"  Selected {self.ui.color(str(len(filtered_tools)), Color.GREEN)} tools (from {len(self.available_tools)} total)")
            print(f"  Token reduction: {self.ui.color(f'~{100 - (len(filtered_tools) / len(self.available_tools) * 100):.0f}%', Color.BRIGHT_GREEN)}")
            print()

            # Step 4: Execute with filtered tools
            print(f"{self.ui.color('→', Color.BRIGHT_BLUE)} Calling LLM with filtered tools...")
            print()

            response = self.tool_executor.execute_with_tools(
                messages=messages,
                tier=selection.tier,
                tools=filtered_tools,
                max_tokens=None,  # Utilise les specs du modèle (128,000 pour nano)
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

                # Check if TOOLER is needed
                if "TOOLER_NEEDED:" in response.content:
                    self._handle_tooler_request(response.content, description)
            elif response.tool_calls and len(response.tool_calls) > 0:
                # Si pas de contenu mais des tool calls, afficher les résultats des tools
                self.ui.success("✓ Tool execution completed!")
                print()
                print(self.ui.color("Tool Results:", Color.CYAN, bold=True))
                print()

                for i, tc in enumerate(response.tool_calls, 1):
                    tool_name = tc.get('name', 'unknown')
                    tool_result = tc.get('result', {})

                    print(f"{i}. {self.ui.color(tool_name, Color.YELLOW, bold=True)}")

                    if isinstance(tool_result, dict):
                        # Afficher résultat structuré
                        success = tool_result.get('success', False)
                        message = tool_result.get('message', '')

                        status_icon = "✓" if success else "✗"
                        status_color = Color.GREEN if success else Color.RED

                        print(f"   {self.ui.color(status_icon, status_color)} Status: {self.ui.color('SUCCESS' if success else 'FAILED', status_color)}")

                        if message:
                            print(f"   Message: {message}")

                        # Afficher data si présent
                        if 'data' in tool_result and tool_result['data']:
                            data = tool_result['data']
                            if isinstance(data, list):
                                print(f"   Data ({len(data)} items):")
                                for j, item in enumerate(data[:5], 1):  # Max 5 items
                                    print(f"     {j}. {str(item)[:100]}")
                                if len(data) > 5:
                                    print(f"     ... and {len(data) - 5} more items")
                            else:
                                print(f"   Data: {str(data)[:200]}")

                        # Afficher error si présent
                        if 'error' in tool_result and tool_result['error']:
                            print(f"   {self.ui.color('Error:', Color.RED)} {tool_result['error']}")
                    else:
                        # Résultat non structuré
                        print(f"   Result: {str(tool_result)[:200]}")

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

    def _handle_tooler_request(self, response_content: str, user_request: str):
        """
        Handle automatic Tooler research when capability is missing
        AVEC Smart Routing vers départements existants d'abord!

        Args:
            response_content: Response from LLM containing TOOLER_NEEDED
            user_request: Original user request
        """
        # Extract what's needed from the response
        import re
        match = re.search(r'TOOLER_NEEDED:\s*(.+?)(?:\n|$)', response_content)

        if not match:
            return

        capability_needed = match.group(1).strip()

        print()
        self.ui.header("🔧 Smart Routing & Tooler Research", level=2)
        print()

        # Step 0: SMART ROUTING - Check if existing department can handle this
        print(f"{self.ui.color('→', Color.BRIGHT_BLUE)} Smart Router analyzing request...")
        print(f"  Capability needed: {self.ui.color(capability_needed, Color.YELLOW)}")
        print()

        tool_names = [tool.name for tool in self.available_tools]
        routing_decision = self.smart_router.route_request(
            user_request=user_request + " " + capability_needed,
            available_tools=tool_names
        )

        print(f"  Route decision: {self.ui.color(routing_decision['route_to'].upper(), Color.CYAN)}")
        print(f"  Confidence: {routing_decision['confidence']:.2f}")
        print(f"  Reason: {routing_decision['reason']}")
        print()

        # If department found, suggest using it directly
        if routing_decision['route_to'] == 'department':
            dept_name = routing_decision['department']
            agent_name = routing_decision['agent_suggestion']

            print(self.ui.color("━" * 80, Color.CYAN))
            print()
            print(self.ui.color(f"✨ EXISTING DEPARTMENT FOUND: {dept_name.upper()}", Color.BRIGHT_GREEN, bold=True))
            print()
            print(f"The {self.ui.color(dept_name.title(), Color.CYAN)} department already handles this!")
            print(f"Suggested agent: {self.ui.color(agent_name, Color.YELLOW)}")
            print()

            # Get department info
            dept_info = self.smart_router.get_department_info(dept_name)
            if dept_info:
                print(f"Description: {dept_info['description']}")
                print(f"Available agents: {', '.join(dept_info['agents'])}")
                print()

            # Check if tools are available
            dept_tools = [t.name for t in self.available_tools if t.category == dept_name]
            if dept_tools:
                print(f"{self.ui.color('✓', Color.GREEN)} Tools already registered: {', '.join(dept_tools)}")
                print()
                print(self.ui.color("💡 TIP:", Color.YELLOW, bold=True) + " The tools are ready to use! Try calling them directly.")
            else:
                print(f"{self.ui.color('⚠️', Color.YELLOW)} Tools not yet registered in executor.")
                print(f"{self.ui.color('💡 TIP:', Color.YELLOW, bold=True)} Tools may need to be imported or registered.")

            print()
            print(self.ui.color("━" * 80, Color.CYAN))
            print()

            # Don't call Tooler - we already have the capability!
            return

        elif routing_decision['route_to'] == 'executor':
            print(f"{self.ui.color('✓', Color.GREEN)} Tool already available in executor!")
            print(f"{self.ui.color('💡 TIP:', Color.YELLOW, bold=True)} Try calling the tool directly.")
            print()
            return

        # Step 1: Only call Tooler if no department matches
        print(f"{self.ui.color('→', Color.BRIGHT_BLUE)} No existing department found - calling Tooler...")
        print()

        try:
            research_results = self.tooler_agent.research_missing_capability(
                capability_description=capability_needed,
                user_request=user_request,
                available_tools=tool_names
            )

            print(f"{self.ui.color('✓', Color.GREEN)} Research complete!")
            print(f"  Model used: {research_results['model_used']}")
            print(f"  Cost: ${research_results['cost']:.6f}")
            print()

            # Step 2: Communications recommendation
            print(f"{self.ui.color('→', Color.BRIGHT_BLUE)} Communications crafting recommendation...")
            print()

            comm_request = self.tooler_agent.create_communication_request(research_results)
            recommendation = self.communications_agent.craft_recommendation(comm_request)

            # Display recommendation
            print(self.ui.color("━" * 80, Color.CYAN))
            print()
            print(self.ui.color("📢 RECOMMENDATION FROM COMMUNICATIONS", Color.BRIGHT_CYAN, bold=True))
            print()
            print(recommendation['message'])
            print()
            print(self.ui.color("━" * 80, Color.CYAN))
            print()

            # Update costs
            total_agent_cost = research_results['cost'] + recommendation['cost']
            self.total_cost += total_agent_cost
            print(self.ui.color(f"Agent workflow cost: ${total_agent_cost:.6f}", Color.BRIGHT_BLACK))
            print()

        except Exception as e:
            # Fallback si Tooler échoue (ex: DeepSeek pas configuré)
            print()
            self.ui.error(f"Tooler research failed: {str(e)[:100]}")
            print()
            print(f"{self.ui.color('💡 TIP:', Color.YELLOW, bold=True)} Check if DEEPSEEK_API_KEY is configured.")
            print(f"The Tooler agent uses DeepSeek for cost-effective research.")
            print()

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
                # Color confidence level (HIGH=Vert fluo, MEDIUM=Jaune, LOW=Rouge)
                if 'HIGH' in line or 'HAUTE' in line:
                    colored_lines.append(self.ui.color(line, Color.BRIGHT_GREEN, bold=True))
                elif 'MEDIUM' in line or 'MOYENNE' in line:
                    colored_lines.append(self.ui.color(line, Color.YELLOW, bold=True))
                else:  # LOW / FAIBLE
                    colored_lines.append(self.ui.color(line, Color.RED, bold=True))
            elif line.startswith('⚠️'):
                # Color severity level (HIGH=Rouge, MEDIUM=Jaune, LOW=Vert fluo)
                if 'CRITICAL' in line or 'CRITIQUE' in line or 'HIGH' in line or 'HAUTE' in line:
                    colored_lines.append(self.ui.color(line, Color.RED, bold=True))
                elif 'MEDIUM' in line or 'MOYENNE' in line:
                    colored_lines.append(self.ui.color(line, Color.YELLOW, bold=True))
                else:  # LOW / FAIBLE
                    colored_lines.append(self.ui.color(line, Color.BRIGHT_GREEN, bold=True))
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

    def _show_employee_section(self, employee_name: str, status: str = ""):
        """
        Display employee section like Tools Department style

        Args:
            employee_name: Name of the employee
            status: Optional status message
        """
        print(self.ui.color("━" * 80, Color.CYAN))
        print(f"{self.ui.color('👤 EMPLOYEE:', Color.BRIGHT_MAGENTA, bold=True)} {self.ui.color(employee_name, Color.CYAN, bold=True)}")
        if status:
            print(f"   {self.ui.color(status, Color.BRIGHT_BLACK)}")
        print(self.ui.color("━" * 80, Color.CYAN))

    def _handle_planning_request(self, description: str):
        """
        Handle planning request - delegates to Planner agent

        Args:
            description: Planning request from user
        """
        self._show_employee_section("Planner", "Creating structured plan...")
        print()

        # Get context from conversation manager
        context_messages = self.conversation_manager.get_context_for_llm(max_tokens=2000)
        context_text = "\n".join([f"{msg['role']}: {msg['content'][:200]}" for msg in context_messages])

        # Create plan
        print(f"{self.ui.color('→', Color.BRIGHT_BLUE)} Analyzing request and creating tasks...")
        plan_result = self.planner_agent.create_plan(description, context_text)

        if not plan_result['success']:
            self.ui.error(f"Planning failed: {plan_result['error']}")
            return

        # Display plan summary
        print()
        self.ui.header("📋 Plan Created", level=2)
        print()
        print(self.ui.color(plan_result['plan_summary'], Color.GREEN))
        print()
        print(f"{self.ui.color('Tasks created:', Color.CYAN)} {plan_result['tasks_created']}")
        print(f"{self.ui.color('Estimated time:', Color.CYAN)} {plan_result['estimated_time']}")
        print()

        # Display tasks
        for i, task in enumerate(plan_result['tasks'], 1):
            tier_color = Color.GREEN if task.min_tier == "nano" else (Color.YELLOW if task.min_tier == "deepseek" else Color.RED)
            print(f"  {i}. {self.ui.color(task.description, Color.WHITE)}")
            print(f"     {self.ui.color(f'Tier: {task.min_tier}', tier_color)} | {self.ui.color(f'Status: {task.status.value}', Color.BRIGHT_BLACK)}")
            print()

        # Update costs
        self.total_cost += plan_result['cost']

        self.ui.success(f"Plan created! Use 'next' to start execution. Cost: ${plan_result['cost']:.6f}")

    def cmd_show_todos(self):
        """Show TodoList"""
        self.ui.header("📋 TodoList", level=2)

        summary = self.todo_manager.get_tasks_summary()

        if summary['total'] == 0:
            self.ui.info("No tasks in the TodoList")
            print()
            self.ui.info("💡 Tip: Use planning requests to create tasks automatically")
            return

        # Show summary
        print(f"{self.ui.color('Total:', Color.CYAN)} {summary['total']} tasks")
        print(f"{self.ui.color('Pending:', Color.YELLOW)} {summary['pending']}")
        print(f"{self.ui.color('In Progress:', Color.BLUE)} {summary['in_progress']}")
        print(f"{self.ui.color('Completed:', Color.GREEN)} {summary['completed']}")
        print(f"{self.ui.color('Progress:', Color.MAGENTA)} {summary['progress_percent']:.1f}%")
        print()

        # Show tasks
        all_tasks = self.todo_manager.get_all_tasks()

        for task in all_tasks:
            status_icon = "⏳" if task.status == TaskStatus.PENDING else ("🔄" if task.status == TaskStatus.IN_PROGRESS else "✅")
            status_color = Color.YELLOW if task.status == TaskStatus.PENDING else (Color.BLUE if task.status == TaskStatus.IN_PROGRESS else Color.GREEN)
            tier_color = Color.GREEN if task.min_tier == "nano" else (Color.YELLOW if task.min_tier == "deepseek" else Color.RED)

            print(f"{status_icon} {self.ui.color(task.description, Color.WHITE, bold=(task.status == TaskStatus.IN_PROGRESS))}")
            print(f"   {self.ui.color(f'Tier: {task.min_tier}', tier_color)} | {self.ui.color(f'Status: {task.status.value}', status_color)}")
            print(f"   {self.ui.color(f'Context: {task.context[:80]}...', Color.BRIGHT_BLACK)}")
            print()

    def cmd_execute_next_task(self):
        """Execute next pending task from TodoList"""
        # Check if there's a task in progress
        current_task = self.todo_manager.get_current_task()
        if current_task:
            self.ui.warning(f"Task already in progress: {current_task.description}")
            print()
            self.ui.info("Complete current task before starting next one")
            return

        # Get next pending task
        next_task = self.todo_manager.get_next_pending_task()

        if not next_task:
            self.ui.info("No pending tasks in TodoList")
            return

        # Mark as in progress
        self.todo_manager.update_task_status(next_task.id, TaskStatus.IN_PROGRESS)

        # Execute the task
        print(f"{self.ui.color('→', Color.BRIGHT_BLUE)} Executing task: {next_task.description}")
        print()

        # Build task description with context
        full_description = f"{next_task.description}\n\nContext: {next_task.context}"

        # Execute
        self.cmd_task(full_description)

        # Check if the task used git commit - if so, mark as completed
        # This is a simplified check - in real scenario, we'd check tool_calls
        if "git" in next_task.description.lower() and "commit" in next_task.description.lower():
            self.todo_manager.update_task_status(next_task.id, TaskStatus.COMPLETED)
            print()
            self.ui.success(f"Task '{next_task.description}' marked as completed!")

            # Automatically start next task if available
            next_next_task = self.todo_manager.get_next_pending_task()
            if next_next_task:
                print()
                self.ui.info(f"Next task available: {next_next_task.description}")
                print()
                response = input(f"{self.ui.color('Execute next task automatically? (y/n):', Color.CYAN)} ").strip().lower()
                if response == 'y':
                    print()
                    self.cmd_execute_next_task()
        else:
            # Manual marking
            self.todo_manager.update_task_status(next_task.id, TaskStatus.COMPLETED)
            print()
            self.ui.success(f"Task '{next_task.description}' completed!")

    def cmd_conversation_stats(self):
        """Show conversation statistics"""
        self.ui.header("💬 Conversation Statistics", level=2)

        stats = self.conversation_manager.get_statistics()

        print(f"{self.ui.color('Total sections:', Color.CYAN)} {stats['total_sections']}")
        print(f"{self.ui.color('Current section messages:', Color.CYAN)} {stats['current_section_messages']}")
        print(f"{self.ui.color('Current section tokens:', Color.CYAN)} {stats['current_section_tokens']}")
        print(f"{self.ui.color('Total tokens:', Color.CYAN)} {stats['total_tokens']}")
        print(f"{self.ui.color('Has global summary:', Color.CYAN)} {'Yes' if stats['has_global_summary'] else 'No'}")
        print()
        print(f"{self.ui.color('Thresholds:', Color.MAGENTA)}")
        print(f"  Section: {stats['section_threshold']} tokens")
        print(f"  Global: {stats['global_threshold']} tokens")
        print()

        # Progress bar for current section
        progress = stats['current_section_tokens'] / stats['section_threshold']
        print(self.ui.progress_bar(
            int(progress * 100),
            100,
            width=50,
            label=f"Section progress ({stats['current_section_tokens']}/{stats['section_threshold']})"
        ))

    def cmd_list_users(self):
        """List all users in TodoDB"""
        self.ui.header("👥 TodoDB Users", level=2)

        # Access auth manager through todo_manager
        auth_manager = self.todo_manager.auth_manager
        users = auth_manager.list_users()

        if not users:
            self.ui.info("No users found")
            return

        print(f"{self.ui.color('Total users:', Color.CYAN)} {len(users)}")
        print()

        for user in users:
            role_color = Color.RED if user.role.value == 'admin' else (Color.GREEN if user.role.value == 'developer' else Color.YELLOW)
            print(f"{self.ui.color('•', role_color)} {self.ui.color(user.username, Color.WHITE, bold=True)}")
            print(f"  Role: {self.ui.color(user.role.value.upper(), role_color)}")
            print(f"  ID: {user.id}")
            print(f"  Created: {user.created_at[:10]}")
            if user.last_login:
                print(f"  Last login: {user.last_login[:19]}")
            print()

    def cmd_whoami(self):
        """Show current user info"""
        self.ui.header("👤 Current User", level=2)

        # Access auth manager and token
        auth_manager = self.todo_manager.auth_manager
        token = self.todo_manager.token

        # Verify token to get user info
        result = auth_manager.verify_token(token)

        if not result['success']:
            self.ui.error(f"Token verification failed: {result['error']}")
            return

        role_color = Color.RED if result['role'] == 'admin' else (Color.GREEN if result['role'] == 'developer' else Color.YELLOW)

        print(f"{self.ui.color('Username:', Color.CYAN)} {self.ui.color(result['username'], Color.WHITE, bold=True)}")
        print(f"{self.ui.color('Role:', Color.CYAN)} {self.ui.color(result['role'].upper(), role_color, bold=True)}")
        print(f"{self.ui.color('User ID:', Color.CYAN)} {result['user_id']}")
        print()

        # Show permissions based on role
        print(f"{self.ui.color('Permissions:', Color.MAGENTA)}")
        if result['role'] == 'admin':
            print(f"  {self.ui.color('✓', Color.GREEN)} Full access to all tasks")
            print(f"  {self.ui.color('✓', Color.GREEN)} Create/edit/delete any task")
            print(f"  {self.ui.color('✓', Color.GREEN)} Manage users")
        elif result['role'] == 'developer':
            print(f"  {self.ui.color('✓', Color.GREEN)} Create and edit own tasks")
            print(f"  {self.ui.color('✓', Color.GREEN)} View all tasks")
            print(f"  {self.ui.color('✗', Color.RED)} Cannot edit other users' tasks")
        else:  # viewer
            print(f"  {self.ui.color('✓', Color.GREEN)} View all tasks")
            print(f"  {self.ui.color('✗', Color.RED)} Cannot create or edit tasks")


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
