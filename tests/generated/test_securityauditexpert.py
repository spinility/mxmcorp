"""
Tests for auto-generated agent: SecurityAuditExpert
"""

import pytest
from cortex.agents.generated.securityauditexpert import SecurityAuditExpert, create_securityauditexpert


def test_securityauditexpert_creation():
    """Test agent creation"""
    agent = create_securityauditexpert()

    assert agent is not None
    assert agent.role == "EXÉCUTANT"
    assert agent.executions == 0


def test_securityauditexpert_execute():
    """Test agent execution"""
    agent = create_securityauditexpert()

    task = {"input": "test_data"}
    result = agent.execute(task)

    assert "success" in result
    assert "agent" in result
    assert result["agent"] == "SecurityAuditExpert"


def test_securityauditexpert_stats():
    """Test stats tracking"""
    agent = create_securityauditexpert()

    # Execute some tasks
    agent.execute({"input": "test1"})
    agent.execute({"input": "test2"})

    stats = agent.get_stats()

    assert stats["executions"] == 2
    assert "success_rate" in stats
