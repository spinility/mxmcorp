"""
Developer Agent - Backward Compatibility Module

DEPRECATED: This module now re-exports from developer_agent_compat.py

The DeveloperAgent has been split into 3 specialized agents:
- DeveloperAgentExpert (EXPERT/DeepSeek) - Standard development
- DeveloperAgentDirecteur (DIRECTEUR/GPT5) - Architectural decisions
- DeveloperAgentCortex (CORTEX_CENTRAL/Claude) - Critical problems

For new code, use AgentFirstRouter with specialized agents.
For existing code, this module provides backward compatibility.
"""

# Re-export everything from the compatibility wrapper
from cortex.agents.developer_agent_compat import (
    DeveloperAgent,
    DeveloperAgentCompat,
    DevelopmentResult,
    CodeChange,
    create_developer_agent
)

# Keep old imports for compatibility
from cortex.core.llm_client import LLMClient
from cortex.core.model_router import ModelTier

# Note: All the old class code has been moved to:
# - cortex/agents/developer_agent_expert.py (EXPERT tier)
# - cortex/agents/developer_agent_directeur.py (DIRECTEUR tier)
# - cortex/agents/developer_agent_cortex.py (CORTEX tier)
# - cortex/agents/developer_agent_compat.py (Backward compat wrapper)

__all__ = [
    'DeveloperAgent',
    'DeveloperAgentCompat',
    'DevelopmentResult',
    'CodeChange',
    'create_developer_agent',
    'LLMClient',
    'ModelTier'
]
