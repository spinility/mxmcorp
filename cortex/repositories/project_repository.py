"""
Project Repository - Accès aux données des projets et roadmap

Encapsule tous les accès DB liés aux projets, milestones et roadmap.
"""

from typing import List, Dict, Any, Optional
from cortex.database import get_database_manager


class ProjectRepository:
    """Repository pour la gestion des projets"""

    def __init__(self):
        self.db = get_database_manager()

    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Récupère tous les projets"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name, description, priority, status,
                       progress_percent, target_date, created_at, updated_at
                FROM project
                ORDER BY priority ASC, created_at DESC
            """)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_active_projects(self) -> List[Dict[str, Any]]:
        """Récupère les projets actifs (non completed)"""
        return self.db.get_active_projects()

    def get_project_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Récupère un projet par son nom"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name, description, priority, status,
                       progress_percent, target_date, created_at, updated_at
                FROM project
                WHERE name = ?
            """, (name,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None

    def get_projects_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Récupère les projets par statut"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name, description, priority, status,
                       progress_percent, target_date, created_at
                FROM project
                WHERE status = ?
                ORDER BY priority ASC, target_date ASC
            """, (status,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_high_priority_projects(self, priority_threshold: int = 3) -> List[Dict[str, Any]]:
        """Récupère les projets haute priorité"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, name, description, priority, status,
                       progress_percent, target_date
                FROM project
                WHERE priority <= ? AND status != 'completed'
                ORDER BY priority ASC, target_date ASC
            """, (priority_threshold,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_overdue_projects(self) -> List[Dict[str, Any]]:
        """Récupère les projets en retard"""
        return self.db.get_overdue_projects()

    def get_blocked_projects(self) -> List[Dict[str, Any]]:
        """Récupère les projets bloqués"""
        return self.get_projects_by_status('blocked')

    def add_project(self, name: str, description: str,
                   priority: int = 5, target_date: Optional[str] = None) -> int:
        """Ajoute un nouveau projet"""
        return self.db.add_project(name, description, priority, target_date)

    def update_progress(self, project_name: str, progress_percent: float):
        """Met à jour la progression d'un projet"""
        self.db.update_project_progress(project_name, progress_percent)

    def update_status(self, project_name: str, new_status: str):
        """Met à jour le statut d'un projet"""
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE project
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE name = ?
            """, (new_status, project_name))
            conn.commit()

    def get_project_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques des projets"""
        with self.db.get_connection() as conn:
            # Total projets
            cursor = conn.execute("SELECT COUNT(*) FROM project")
            total = cursor.fetchone()[0]

            # Par statut
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM project
                GROUP BY status
            """)
            by_status = {row[0]: row[1] for row in cursor.fetchall()}

            # Progression moyenne
            cursor = conn.execute("""
                SELECT AVG(progress_percent)
                FROM project
                WHERE status != 'completed'
            """)
            avg_progress = cursor.fetchone()[0] or 0.0

            # En retard
            cursor = conn.execute("""
                SELECT COUNT(*)
                FROM project
                WHERE target_date < date('now')
                  AND status NOT IN ('completed', 'cancelled')
            """)
            overdue = cursor.fetchone()[0]

            return {
                'total': total,
                'by_status': by_status,
                'average_progress': avg_progress,
                'overdue_count': overdue,
                'completed': by_status.get('completed', 0),
                'in_progress': by_status.get('in_progress', 0),
                'planned': by_status.get('planned', 0),
                'blocked': by_status.get('blocked', 0)
            }

    def get_milestones_for_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Récupère les milestones d'un projet"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, project_id, name, description, target_date,
                       status, progress_percent, created_at
                FROM milestone
                WHERE project_id = ?
                ORDER BY target_date ASC
            """, (project_id,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


# Factory function
def get_project_repository() -> ProjectRepository:
    """Récupère une instance du repository"""
    return ProjectRepository()
