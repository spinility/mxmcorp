"""
Cortex Core - Modules centraux du système

Exports principaux:
- LLMClient: Client unifié pour tous les LLMs
- ModelRouter: Routage intelligent par tier
- AgentHierarchy: Système hiérarchique des agents
- WorkflowEngine: Orchestrateur central
- Self-Awareness: Système de conscience des capacités
"""

# LLM & Models
from cortex.core.llm_client import LLMClient, LLMResponse
from cortex.core.model_router import ModelTier, ModelRouter

# Agent System
from cortex.core.agent_hierarchy import (
    AgentRole,
    BaseAgent,
    ExecutionAgent,
    AnalysisAgent,
    DecisionAgent,
    CoordinationAgent
)

# Workflow & Todo
from cortex.core.workflow_engine import WorkflowEngine, WorkflowStep, WorkflowResult
from cortex.core.todo_manager import TodoManager, TodoTask

# Self-Awareness System (Phase 4.2)
from cortex.core.capability_registry import CapabilityRegistry, Capability
from cortex.core.environment_scanner import EnvironmentScanner, EnvironmentInfo
from cortex.core.self_introspection_agent import SelfIntrospectionAgent

__all__ = [
    # LLM & Models
    'LLMClient',
    'LLMResponse',
    'ModelTier',
    'ModelRouter',

    # Agent System
    'AgentRole',
    'BaseAgent',
    'ExecutionAgent',
    'AnalysisAgent',
    'DecisionAgent',
    'CoordinationAgent',

    # Workflow & Todo
    'WorkflowEngine',
    'WorkflowStep',
    'WorkflowResult',
    'TodoManager',
    'TodoTask',

    # Self-Awareness System
    'CapabilityRegistry',
    'Capability',
    'EnvironmentScanner',
    'EnvironmentInfo',
    'SelfIntrospectionAgent',
]
