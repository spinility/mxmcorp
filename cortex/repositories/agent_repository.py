"""
Agent Repository - Accès aux données des agents

Encapsule tous les accès DB liés aux agents et leurs métriques.
"""

from typing import List, Dict, Any, Optional
from cortex.database import get_database_manager


class AgentRepository:
    """Repository pour la gestion des agents"""

    def __init__(self):
        self.db = get_database_manager()

    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Récupère tous les agents"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT name, type, role, tier, specialization, expertise_level,
                       total_executions, success_rate, total_cost, avg_response_time,
                       last_active, status
                FROM agent
                ORDER BY name
            """)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_agent_by_name(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Récupère un agent par son nom"""
        return self.db.get_agent_stats(agent_name)

    def get_active_agents(self) -> List[Dict[str, Any]]:
        """Récupère les agents actifs (status='active')"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT name, type, role, tier, specialization, expertise_level,
                       total_executions, success_rate, total_cost, avg_response_time
                FROM agent
                WHERE status = 'active'
                ORDER BY total_executions DESC
            """)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_top_performers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Récupère les agents les plus performants"""
        return self.db.get_top_performing_agents(limit)

    def update_metrics(self, agent_name: str, cost: float,
                      response_time: float, success: bool):
        """Met à jour les métriques d'un agent"""
        self.db.update_agent_metrics(agent_name, cost, response_time, success)

    def get_agents_by_tier(self, tier: str) -> List[Dict[str, Any]]:
        """Récupère les agents d'un tier spécifique"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT name, type, role, specialization, expertise_level,
                       total_executions, success_rate, total_cost
                FROM agent
                WHERE tier = ? AND status = 'active'
                ORDER BY success_rate DESC, total_cost ASC
            """, (tier,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_agents_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Récupère les agents par rôle métier"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT name, type, tier, specialization, expertise_level,
                       total_executions, success_rate, avg_response_time
                FROM agent
                WHERE role = ? AND status = 'active'
                ORDER BY expertise_level DESC
            """, (role,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_agent_metrics_history(self, agent_name: str,
                                   last_n_days: int = 30) -> List[Dict[str, Any]]:
        """Récupère l'historique des métriques d'un agent"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT am.metric_type, am.value, am.timestamp
                FROM agent_metric am
                JOIN agent a ON am.agent_id = a.id
                WHERE a.name = ?
                  AND am.timestamp >= datetime('now', '-' || ? || ' days')
                ORDER BY am.timestamp DESC
            """, (agent_name, last_n_days))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_total_cost(self) -> float:
        """Récupère le coût total de tous les agents"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT SUM(total_cost) FROM agent")
            result = cursor.fetchone()
            return result[0] if result[0] else 0.0

    def get_total_executions(self) -> int:
        """Récupère le nombre total d'exécutions"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT SUM(total_executions) FROM agent")
            result = cursor.fetchone()
            return result[0] if result[0] else 0

    def get_average_success_rate(self) -> float:
        """Récupère le taux de succès moyen"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT AVG(success_rate)
                FROM agent
                WHERE total_executions > 0
            """)
            result = cursor.fetchone()
            return result[0] if result[0] else 0.0


# Factory function
def get_agent_repository() -> AgentRepository:
    """Récupère une instance du repository"""
    return AgentRepository()
