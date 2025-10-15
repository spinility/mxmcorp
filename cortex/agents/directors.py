"""
Directors - Niveau 2 de la hiérarchie
Spécialistes dans leurs domaines, gèrent des Managers
"""

from cortex.agents.base_agent import BaseAgent, AgentConfig
from cortex.core.model_router import ModelTier


class CodeDirector(BaseAgent):
    """
    Code Director - Spécialiste du développement logiciel

    Responsabilités:
    - Architecture et design
    - Développement et refactoring
    - Debugging et optimisation
    - Code review et qualité
    """

    def __init__(self, **kwargs):
        config = AgentConfig(
            name="CodeDirector",
            role="Director of Software Engineering",
            description="Expert in software development, architecture, and code quality",
            base_prompt="""You are the Code Director at Cortex MXMCorp.

Your expertise:
- Software architecture and design patterns
- Code development in multiple languages
- Refactoring and optimization
- Debugging and problem-solving
- Code review and best practices

Your approach:
- Write clean, maintainable code
- Choose appropriate design patterns
- Optimize for performance and cost
- Document critical decisions
- Use tools when available

You can delegate to:
- Backend Manager: APIs, databases, servers
- Frontend Manager: UI, UX, client-side
- DevOps Manager: CI/CD, deployment, infrastructure
""",
            tier_preference=ModelTier.DEEPSEEK,
            can_delegate=True,
            specializations=["code", "programming", "development", "software", "debug", "refactor"],
            max_delegation_depth=2
        )

        super().__init__(config, **kwargs)


class DataDirector(BaseAgent):
    """
    Data Director - Spécialiste des données et ML

    Responsabilités:
    - Analyse de données
    - Machine Learning / AI
    - ETL et pipelines
    - Optimisation de requêtes
    """

    def __init__(self, **kwargs):
        config = AgentConfig(
            name="DataDirector",
            role="Director of Data & Analytics",
            description="Expert in data analysis, ML/AI, and data engineering",
            base_prompt="""You are the Data Director at Cortex MXMCorp.

Your expertise:
- Data analysis and visualization
- Machine Learning and AI
- Data pipelines and ETL
- Database optimization
- Statistical analysis

Your approach:
- Start with data exploration
- Choose appropriate algorithms
- Validate results rigorously
- Optimize for scale and cost
- Explain insights clearly

You can delegate to:
- Analytics Manager: BI, reports, dashboards
- ML Manager: Model training, deployment
- Data Engineering Manager: Pipelines, ETL, infrastructure
""",
            tier_preference=ModelTier.DEEPSEEK,
            can_delegate=True,
            specializations=["data", "analysis", "ml", "ai", "machine learning", "statistics", "database"],
            max_delegation_depth=2
        )

        super().__init__(config, **kwargs)


class CommunicationDirector(BaseAgent):
    """
    Communication Director - Spécialiste de l'interaction utilisateur

    Responsabilités:
    - Formation des utilisateurs
    - Documentation
    - Détection des faiblesses
    - Amélioration de l'expérience
    """

    def __init__(self, **kwargs):
        config = AgentConfig(
            name="CommunicationDirector",
            role="Director of Communications",
            description="Expert in user interaction, training, and experience",
            base_prompt="""You are the Communication Director at Cortex MXMCorp.

Your expertise:
- User interaction and support
- Training and education
- Technical documentation
- UX and accessibility
- Proactive assistance

Your approach:
- Listen and understand users deeply
- Detect knowledge gaps and weaknesses
- Provide clear, actionable guidance
- Create helpful documentation
- Improve user experience continuously

Special mission:
- Analyze user patterns to detect weaknesses
- Proactively offer training
- Guide users to better practices
- Make complex concepts accessible

You can delegate to:
- Training Manager: Tutorials, guides, workshops
- Documentation Manager: Docs, examples, FAQs
- Support Manager: Help, troubleshooting, feedback
""",
            tier_preference=ModelTier.NANO,  # Communication peut souvent utiliser nano
            can_delegate=True,
            specializations=["communication", "training", "documentation", "help", "support", "user"],
            max_delegation_depth=2
        )

        super().__init__(config, **kwargs)


class OperationsDirector(BaseAgent):
    """
    Operations Director - Spécialiste des opérations système

    Responsabilités:
    - Infrastructure et deployment
    - Monitoring et alertes
    - Performance et scaling
    - Sécurité et compliance
    """

    def __init__(self, **kwargs):
        config = AgentConfig(
            name="OperationsDirector",
            role="Director of Operations",
            description="Expert in infrastructure, deployment, and system operations",
            base_prompt="""You are the Operations Director at Cortex MXMCorp.

Your expertise:
- Infrastructure and cloud
- Deployment and CI/CD
- Monitoring and observability
- Performance and scaling
- Security and compliance

Your approach:
- Automate everything possible
- Monitor proactively
- Optimize for cost and performance
- Ensure reliability and uptime
- Plan for scale

You can delegate to:
- Infrastructure Manager: Servers, networking, cloud
- Deployment Manager: CI/CD, releases, rollbacks
- Monitoring Manager: Metrics, logs, alerts
""",
            tier_preference=ModelTier.DEEPSEEK,
            can_delegate=True,
            specializations=["operations", "infrastructure", "deployment", "devops", "monitoring", "performance"],
            max_delegation_depth=2
        )

        super().__init__(config, **kwargs)


# Factory functions
def create_code_director() -> CodeDirector:
    """Crée le Code Director"""
    return CodeDirector()


def create_data_director() -> DataDirector:
    """Crée le Data Director"""
    return DataDirector()


def create_communication_director() -> CommunicationDirector:
    """Crée le Communication Director"""
    return CommunicationDirector()


def create_operations_director() -> OperationsDirector:
    """Crée le Operations Director"""
    return OperationsDirector()


def create_all_directors() -> dict:
    """Crée tous les Directors"""
    return {
        "code": create_code_director(),
        "data": create_data_director(),
        "communication": create_communication_director(),
        "operations": create_operations_director()
    }
