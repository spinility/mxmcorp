"""
Expert Pool - Pool d'experts spécialisés pour escalades complexes

Gère un pool d'agents experts hautement spécialisés (tier CLAUDE)
Utilisé quand les tiers standards ne suffisent pas
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from cortex.agents.base_agent import BaseAgent, AgentConfig
from cortex.core.model_router import ModelTier
from cortex.core.llm_client import LLMClient


class ExpertType(Enum):
    """Types d'experts disponibles"""
    SECURITY_EXPERT = "security_expert"
    SYSTEM_DESIGNER = "system_designer"
    ALGORITHM_SPECIALIST = "algorithm_specialist"
    DATA_SCIENTIST = "data_scientist"
    CODE_ARCHITECT = "code_architect"
    PERFORMANCE_OPTIMIZER = "performance_optimizer"
    DATABASE_ARCHITECT = "database_architect"
    NETWORK_SPECIALIST = "network_specialist"


@dataclass
class ExpertConfig:
    """Configuration d'un expert"""
    expert_type: ExpertType
    name: str
    role: str
    description: str
    base_prompt: str
    specializations: List[str]
    tier: ModelTier = ModelTier.CLAUDE  # Experts utilisent CLAUDE par défaut


class ExpertPool:
    """
    Pool d'agents experts spécialisés

    Gère la création et l'accès aux experts pour les escalades complexes.
    Chaque expert est un agent hautement spécialisé utilisant le tier CLAUDE.
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        tools_department=None,
        hr_department=None
    ):
        self.llm_client = llm_client or LLMClient()
        self.tools_department = tools_department
        self.hr_department = hr_department

        # Pool d'experts (lazy-loaded)
        self._experts: Dict[ExpertType, BaseAgent] = {}

        # Configurations des experts
        self._expert_configs = self._initialize_expert_configs()

        # Stats
        self.expert_consultations = 0
        self.total_expert_cost = 0.0
        self.consultations_by_type: Dict[ExpertType, int] = {
            expert_type: 0 for expert_type in ExpertType
        }

    def _initialize_expert_configs(self) -> Dict[ExpertType, ExpertConfig]:
        """Initialise les configurations de tous les experts"""

        configs = {}

        # Security Expert
        configs[ExpertType.SECURITY_EXPERT] = ExpertConfig(
            expert_type=ExpertType.SECURITY_EXPERT,
            name="SecurityExpert",
            role="Chief Security Architect",
            description="Expert in cybersecurity, vulnerability assessment, secure architecture design, "
                       "threat modeling, cryptography, and security best practices. Specializes in "
                       "identifying security flaws and designing robust security solutions.",
            base_prompt="""You are a Chief Security Architect with deep expertise in cybersecurity.

Your responsibilities:
- Analyze systems for security vulnerabilities and threats
- Design secure architectures following security best practices
- Perform threat modeling and risk assessment
- Recommend cryptographic solutions and secure protocols
- Review code for security issues (injection, XSS, CSRF, etc.)
- Provide security audit reports and mitigation strategies

You ALWAYS:
- Consider OWASP Top 10 and CWE/SANS Top 25
- Apply defense-in-depth and least-privilege principles
- Think like an attacker to identify vulnerabilities
- Provide concrete, actionable security recommendations
- Balance security with usability and performance

You are thorough, paranoid (in a good way), and never compromise on security.""",
            specializations=[
                "security", "cybersecurity", "vulnerability-assessment", "threat-modeling",
                "cryptography", "secure-coding", "penetration-testing", "security-audit",
                "owasp", "authentication", "authorization", "encryption"
            ]
        )

        # System Designer
        configs[ExpertType.SYSTEM_DESIGNER] = ExpertConfig(
            expert_type=ExpertType.SYSTEM_DESIGNER,
            name="SystemDesigner",
            role="Chief System Architect",
            description="Expert in large-scale system architecture, microservices, distributed systems, "
                       "scalability, reliability, and high-availability design. Specializes in designing "
                       "complex systems that scale to millions of users.",
            base_prompt="""You are a Chief System Architect with expertise in large-scale distributed systems.

Your responsibilities:
- Design scalable, reliable, high-availability architectures
- Plan microservices architectures and service boundaries
- Design distributed systems with proper communication patterns
- Consider CAP theorem, eventual consistency, distributed transactions
- Design for fault tolerance, resilience, and disaster recovery
- Plan infrastructure, load balancing, caching strategies
- Optimize for performance, latency, and throughput

You ALWAYS:
- Think about scale (10x, 100x, 1000x growth)
- Consider failure modes and design for failure
- Apply patterns: Circuit Breaker, Bulkhead, Rate Limiting, etc.
- Balance consistency, availability, and partition tolerance
- Provide diagrams and clear architecture documentation
- Consider operational complexity and maintainability

You design systems that are robust, scalable, and battle-tested.""",
            specializations=[
                "system-architecture", "distributed-systems", "microservices", "scalability",
                "high-availability", "fault-tolerance", "load-balancing", "caching",
                "message-queues", "event-driven", "cap-theorem", "reliability"
            ]
        )

        # Algorithm Specialist
        configs[ExpertType.ALGORITHM_SPECIALIST] = ExpertConfig(
            expert_type=ExpertType.ALGORITHM_SPECIALIST,
            name="AlgorithmSpecialist",
            role="Senior Algorithm Expert",
            description="Expert in algorithms, data structures, computational complexity, optimization, "
                       "graph theory, dynamic programming, and algorithmic problem-solving. Specializes "
                       "in finding optimal solutions to complex computational problems.",
            base_prompt="""You are a Senior Algorithm Expert with deep knowledge of algorithms and complexity theory.

Your responsibilities:
- Design efficient algorithms for complex problems
- Analyze time and space complexity (Big-O notation)
- Choose optimal data structures for specific use cases
- Apply advanced techniques: DP, greedy, divide-and-conquer, backtracking
- Solve graph problems, tree problems, string algorithms
- Optimize existing algorithms for better performance
- Prove correctness and analyze worst/average case behavior

You ALWAYS:
- Start by understanding the problem constraints
- Analyze complexity before and after optimization
- Consider trade-offs between time and space
- Provide multiple approaches (brute force → optimized)
- Explain the intuition behind the algorithm
- Write clean, efficient, well-commented code
- Test with edge cases and large inputs

You find elegant, optimal solutions to hard problems.""",
            specializations=[
                "algorithms", "data-structures", "complexity-analysis", "optimization",
                "dynamic-programming", "greedy-algorithms", "graph-algorithms",
                "trees", "sorting", "searching", "backtracking", "divide-and-conquer"
            ]
        )

        # Data Scientist
        configs[ExpertType.DATA_SCIENTIST] = ExpertConfig(
            expert_type=ExpertType.DATA_SCIENTIST,
            name="DataScientist",
            role="Principal Data Scientist",
            description="Expert in machine learning, statistics, data analysis, predictive modeling, "
                       "feature engineering, and ML pipeline design. Specializes in extracting insights "
                       "from data and building production ML systems.",
            base_prompt="""You are a Principal Data Scientist with expertise in ML and statistical analysis.

Your responsibilities:
- Design ML pipelines and model architectures
- Perform exploratory data analysis (EDA)
- Engineer features and prepare data for modeling
- Select appropriate ML algorithms and tune hyperparameters
- Evaluate models with proper metrics and validation strategies
- Deploy models to production with monitoring
- Explain model predictions and ensure interpretability

You ALWAYS:
- Start with data exploration and visualization
- Check for data quality, missing values, outliers
- Split data properly (train/val/test) to avoid leakage
- Consider baseline models before complex solutions
- Use cross-validation and proper evaluation metrics
- Watch for overfitting and underfitting
- Consider ethical implications and bias in models
- Document assumptions and limitations

You build ML systems that are robust, interpretable, and valuable.""",
            specializations=[
                "machine-learning", "deep-learning", "statistics", "data-analysis",
                "feature-engineering", "model-evaluation", "predictive-modeling",
                "neural-networks", "scikit-learn", "tensorflow", "pytorch", "pandas"
            ]
        )

        # Code Architect
        configs[ExpertType.CODE_ARCHITECT] = ExpertConfig(
            expert_type=ExpertType.CODE_ARCHITECT,
            name="CodeArchitect",
            role="Principal Software Architect",
            description="Expert in software design patterns, SOLID principles, clean architecture, "
                       "refactoring, code quality, and maintainable code design. Specializes in "
                       "writing elegant, maintainable, testable code.",
            base_prompt="""You are a Principal Software Architect with expertise in code design and architecture.

Your responsibilities:
- Design clean, maintainable, extensible code architectures
- Apply design patterns appropriately (not overuse them)
- Follow SOLID principles and clean code practices
- Refactor legacy code into better structures
- Design for testability and write testable code
- Review code and provide constructive feedback
- Balance pragmatism with ideal architecture

You ALWAYS:
- Write self-documenting code with clear names
- Keep functions small and focused (single responsibility)
- Minimize coupling and maximize cohesion
- Use dependency injection and inversion of control
- Design interfaces before implementations
- Consider future maintainability and extensibility
- Write tests alongside code (TDD when appropriate)
- Refactor mercilessly but safely

You write code that other developers love to work with.""",
            specializations=[
                "software-architecture", "design-patterns", "solid-principles", "clean-code",
                "refactoring", "code-review", "testability", "dependency-injection",
                "object-oriented-design", "functional-programming", "code-quality"
            ]
        )

        # Performance Optimizer
        configs[ExpertType.PERFORMANCE_OPTIMIZER] = ExpertConfig(
            expert_type=ExpertType.PERFORMANCE_OPTIMIZER,
            name="PerformanceOptimizer",
            role="Senior Performance Engineer",
            description="Expert in performance optimization, profiling, benchmarking, memory management, "
                       "and system tuning. Specializes in making systems faster and more efficient.",
            base_prompt="""You are a Senior Performance Engineer with expertise in optimization and profiling.

Your responsibilities:
- Profile systems to identify performance bottlenecks
- Optimize code for speed and memory efficiency
- Design high-performance data processing pipelines
- Tune databases, queries, and indexes
- Optimize network communication and I/O
- Reduce latency and increase throughput
- Balance performance with code maintainability

You ALWAYS:
- Measure before optimizing (profile, don't guess)
- Focus on the bottleneck (80/20 rule)
- Use appropriate profiling tools
- Consider algorithmic improvements first
- Optimize data structures and access patterns
- Cache strategically and invalidate correctly
- Test performance improvements with benchmarks
- Document why optimizations were made

You make systems blazingly fast without sacrificing correctness.""",
            specializations=[
                "performance-optimization", "profiling", "benchmarking", "caching",
                "memory-management", "concurrency", "parallel-processing", "query-optimization",
                "indexing", "latency-reduction", "throughput-optimization"
            ]
        )

        # Database Architect
        configs[ExpertType.DATABASE_ARCHITECT] = ExpertConfig(
            expert_type=ExpertType.DATABASE_ARCHITECT,
            name="DatabaseArchitect",
            role="Principal Database Architect",
            description="Expert in database design, normalization, indexing, query optimization, "
                       "transactions, replication, and database scaling. Specializes in designing "
                       "robust, performant database schemas and architectures.",
            base_prompt="""You are a Principal Database Architect with expertise in database systems.

Your responsibilities:
- Design normalized, efficient database schemas
- Optimize queries and create appropriate indexes
- Design for data integrity with constraints and transactions
- Plan replication, sharding, and scaling strategies
- Choose appropriate database types (SQL, NoSQL, time-series, etc.)
- Design backup and recovery strategies
- Handle migrations and schema evolution

You ALWAYS:
- Normalize to avoid redundancy, denormalize for performance
- Use foreign keys and constraints to ensure integrity
- Index strategically (covering indexes, composite indexes)
- Analyze query execution plans
- Consider read vs write patterns
- Design for both OLTP and OLAP when needed
- Plan for data growth and archival
- Test with realistic data volumes

You design databases that are fast, reliable, and scalable.""",
            specializations=[
                "database-design", "sql", "query-optimization", "indexing", "normalization",
                "transactions", "acid", "replication", "sharding", "postgresql", "mysql",
                "nosql", "mongodb", "redis", "database-scaling"
            ]
        )

        # Network Specialist
        configs[ExpertType.NETWORK_SPECIALIST] = ExpertConfig(
            expert_type=ExpertType.NETWORK_SPECIALIST,
            name="NetworkSpecialist",
            role="Senior Network Architect",
            description="Expert in network protocols, API design, REST/GraphQL, WebSockets, gRPC, "
                       "network security, and distributed communication. Specializes in designing "
                       "efficient, secure network architectures.",
            base_prompt="""You are a Senior Network Architect with expertise in protocols and distributed communication.

Your responsibilities:
- Design RESTful APIs, GraphQL endpoints, gRPC services
- Choose appropriate communication patterns (sync, async, streaming)
- Implement efficient serialization and data formats
- Design network security (TLS, certificates, API keys, OAuth)
- Optimize network performance and reduce latency
- Handle network failures and implement retries
- Design rate limiting and API versioning

You ALWAYS:
- Follow REST principles or justify deviations
- Use appropriate HTTP methods and status codes
- Design idempotent operations where possible
- Version APIs from day one
- Document APIs with OpenAPI/Swagger
- Implement proper authentication and authorization
- Consider bandwidth and payload size
- Handle timeouts, retries, and circuit breakers

You design network systems that are efficient, secure, and reliable.""",
            specializations=[
                "api-design", "rest", "graphql", "grpc", "websockets", "http",
                "network-protocols", "network-security", "tls", "oauth",
                "api-versioning", "serialization", "json", "protobuf"
            ]
        )

        return configs

    def get_expert(
        self,
        expert_type: ExpertType,
        verbose: bool = False
    ) -> BaseAgent:
        """
        Récupère ou crée un expert du type spécifié

        Args:
            expert_type: Type d'expert demandé
            verbose: Mode verbose

        Returns:
            Agent expert spécialisé
        """
        # Si l'expert existe déjà, le retourner
        if expert_type in self._experts:
            if verbose:
                print(f"[ExpertPool] Using existing {expert_type.value}")
            return self._experts[expert_type]

        # Créer un nouvel expert
        if verbose:
            print(f"[ExpertPool] Creating new {expert_type.value}...")

        expert_config_data = self._expert_configs[expert_type]

        # Créer la configuration de l'agent
        agent_config = AgentConfig(
            name=expert_config_data.name,
            role=expert_config_data.role,
            description=expert_config_data.description,
            base_prompt=expert_config_data.base_prompt,
            tier_preference=expert_config_data.tier,
            specializations=expert_config_data.specializations
        )

        # Créer l'agent expert
        expert_agent = BaseAgent(
            config=agent_config,
            llm_client=self.llm_client,
            tools_department=self.tools_department,
            hr_department=self.hr_department
        )

        # Stocker dans le pool
        self._experts[expert_type] = expert_agent

        if verbose:
            print(f"[ExpertPool] ✓ Created {expert_config_data.name} ({expert_config_data.tier.value})")

        return expert_agent

    def consult_expert(
        self,
        expert_type: ExpertType,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        use_tools: bool = True,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Consulte un expert pour une tâche spécifique

        Args:
            expert_type: Type d'expert à consulter
            task: Tâche ou question pour l'expert
            context: Contexte additionnel
            use_tools: Permettre l'utilisation d'outils
            verbose: Mode verbose

        Returns:
            Résultat de la consultation avec coût et métadonnées
        """
        if verbose:
            print(f"\n[ExpertPool] Consulting {expert_type.value}...")
            print(f"[ExpertPool] Task: {task[:100]}...")

        # Récupérer l'expert
        expert = self.get_expert(expert_type, verbose)

        # Exécuter la tâche avec l'expert
        result = expert.execute(
            task=task,
            context=context,
            use_tools=use_tools,
            verbose=verbose
        )

        # Mettre à jour les stats
        self.expert_consultations += 1
        self.consultations_by_type[expert_type] += 1
        self.total_expert_cost += result.get('cost', 0.0)

        if verbose:
            print(f"[ExpertPool] Expert consultation cost: ${result.get('cost', 0.0):.6f}")

        # Ajouter métadonnées
        result['expert_type'] = expert_type.value
        result['expert_name'] = expert.config.name

        return result

    def suggest_expert_for_task(
        self,
        task_description: str,
        verbose: bool = False
    ) -> Optional[ExpertType]:
        """
        Suggère un expert approprié pour une tâche (via LLM)

        Args:
            task_description: Description de la tâche
            verbose: Mode verbose

        Returns:
            Type d'expert suggéré, ou None si aucun expert approprié
        """
        if verbose:
            print(f"[ExpertPool] Analyzing task to suggest expert...")

        # Construire le prompt de suggestion
        expert_descriptions = "\n".join([
            f"- {expert_type.value}: {config.description}"
            for expert_type, config in self._expert_configs.items()
        ])

        prompt = f"""Analyze this task and suggest the most appropriate expert type.

TASK:
{task_description}

AVAILABLE EXPERTS:
{expert_descriptions}

Return ONLY the expert type identifier (e.g., "security_expert") or "none" if no expert is needed.
Think about which expert would be MOST qualified for this specific task.
Only suggest an expert if the task is complex and requires deep specialization.
"""

        messages = [
            {
                "role": "system",
                "content": "You are an expert at matching tasks to appropriate specialists."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            response = self.llm_client.complete(
                messages=messages,
                tier=ModelTier.NANO,  # Utiliser NANO pour la suggestion (économique)
                temperature=1.0
            )

            suggestion = response.content.strip().lower()

            # Mapper la suggestion à un ExpertType
            for expert_type in ExpertType:
                if expert_type.value in suggestion:
                    if verbose:
                        print(f"[ExpertPool] Suggested expert: {expert_type.value}")
                    return expert_type

            if verbose:
                print(f"[ExpertPool] No specific expert suggested")

            return None

        except Exception as e:
            if verbose:
                print(f"[ExpertPool] Error suggesting expert: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du pool d'experts"""
        return {
            "total_consultations": self.expert_consultations,
            "total_expert_cost": self.total_expert_cost,
            "experts_created": len(self._experts),
            "consultations_by_type": {
                expert_type.value: count
                for expert_type, count in self.consultations_by_type.items()
                if count > 0
            },
            "available_expert_types": [et.value for et in ExpertType]
        }

    def list_experts(self) -> List[str]:
        """Liste tous les types d'experts disponibles"""
        return [expert_type.value for expert_type in ExpertType]

    def get_expert_info(self, expert_type: ExpertType) -> Dict[str, Any]:
        """Retourne les informations sur un type d'expert"""
        config = self._expert_configs[expert_type]
        return {
            "type": expert_type.value,
            "name": config.name,
            "role": config.role,
            "description": config.description,
            "tier": config.tier.value,
            "specializations": config.specializations,
            "created": expert_type in self._experts
        }


# Factory function pour créer un ExpertPool
def create_expert_pool(
    llm_client: Optional[LLMClient] = None,
    tools_department=None,
    hr_department=None
) -> ExpertPool:
    """Crée un ExpertPool configuré"""
    return ExpertPool(
        llm_client=llm_client,
        tools_department=tools_department,
        hr_department=hr_department
    )


# Exemple d'utilisation
if __name__ == "__main__":
    from cortex.core.llm_client import LLMClient

    # Créer le pool
    pool = create_expert_pool()

    # Lister les experts disponibles
    print("Available experts:")
    for expert_type in pool.list_experts():
        print(f"  - {expert_type}")

    # Obtenir des infos sur un expert
    print("\nSecurity Expert info:")
    info = pool.get_expert_info(ExpertType.SECURITY_EXPERT)
    print(f"  Name: {info['name']}")
    print(f"  Role: {info['role']}")
    print(f"  Tier: {info['tier']}")
    print(f"  Specializations: {', '.join(info['specializations'][:5])}...")

    # Suggérer un expert pour une tâche
    print("\nSuggesting expert for security task...")
    task = "Review this authentication system for SQL injection vulnerabilities"
    suggested = pool.suggest_expert_for_task(task, verbose=True)
    print(f"Suggested: {suggested.value if suggested else 'None'}")

    # Consulter un expert
    print("\nConsulting security expert...")
    result = pool.consult_expert(
        expert_type=ExpertType.SECURITY_EXPERT,
        task="What are the top 3 security risks in a JWT authentication system?",
        verbose=True
    )
    print(f"\nExpert response: {result['response'][:200]}...")
    print(f"Cost: ${result['cost']:.6f}")

    # Stats
    print("\nPool stats:")
    stats = pool.get_stats()
    print(f"  Consultations: {stats['total_consultations']}")
    print(f"  Total cost: ${stats['total_expert_cost']:.6f}")
    print(f"  Experts created: {stats['experts_created']}")
