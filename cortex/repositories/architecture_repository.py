"""
Architecture Repository - Accès aux données des décisions architecturales

Encapsule tous les accès DB liés aux ADRs (Architecture Decision Records).
"""

from typing import List, Dict, Any, Optional
from cortex.database import get_database_manager


class ArchitectureRepository:
    """Repository pour la gestion des décisions architecturales"""

    def __init__(self):
        self.db = get_database_manager()

    def add_decision(self, title: str, context: str, decision: str,
                    consequences: str, alternatives: Optional[str] = None,
                    status: str = 'proposed', author: str = 'Cortex') -> int:
        """Ajoute une décision architecturale (ADR)"""
        return self.db.add_architectural_decision(
            title, context, decision, consequences,
            alternatives, status, author
        )

    def get_all_decisions(self) -> List[Dict[str, Any]]:
        """Récupère toutes les décisions"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, title, context, decision, consequences,
                       alternatives, status, author, created_at, decided_at
                FROM architectural_decision
                ORDER BY id DESC
            """)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_decision_by_id(self, decision_id: int) -> Optional[Dict[str, Any]]:
        """Récupère une décision par son ID"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, title, context, decision, consequences,
                       alternatives, status, author, created_at, decided_at
                FROM architectural_decision
                WHERE id = ?
            """, (decision_id,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None

    def get_decisions_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Récupère les décisions par statut"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, title, context, decision, consequences,
                       status, author, created_at
                FROM architectural_decision
                WHERE status = ?
                ORDER BY created_at DESC
            """, (status,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_active_decisions(self) -> List[Dict[str, Any]]:
        """Récupère les décisions acceptées (status='accepted')"""
        return self.get_decisions_by_status('accepted')

    def get_proposed_decisions(self) -> List[Dict[str, Any]]:
        """Récupère les décisions proposées en attente"""
        return self.get_decisions_by_status('proposed')

    def update_decision_status(self, decision_id: int, new_status: str):
        """Met à jour le statut d'une décision"""
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE architectural_decision
                SET status = ?,
                    decided_at = CASE WHEN ? IN ('accepted', 'rejected')
                                     THEN CURRENT_TIMESTAMP
                                     ELSE decided_at
                                END
                WHERE id = ?
            """, (new_status, new_status, decision_id))
            conn.commit()

    def search_decisions(self, search_term: str) -> List[Dict[str, Any]]:
        """Recherche dans les décisions architecturales"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, title, context, decision, consequences,
                       status, author, created_at
                FROM architectural_decision
                WHERE title LIKE ? OR context LIKE ? OR decision LIKE ?
                ORDER BY created_at DESC
            """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_decisions_by_author(self, author: str) -> List[Dict[str, Any]]:
        """Récupère les décisions par auteur"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, title, context, decision, status, created_at
                FROM architectural_decision
                WHERE author = ?
                ORDER BY created_at DESC
            """, (author,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_decision_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques des décisions"""
        with self.db.get_connection() as conn:
            # Total
            cursor = conn.execute("SELECT COUNT(*) FROM architectural_decision")
            total = cursor.fetchone()[0]

            # Par statut
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM architectural_decision
                GROUP BY status
            """)
            by_status = {row[0]: row[1] for row in cursor.fetchall()}

            # Par auteur
            cursor = conn.execute("""
                SELECT author, COUNT(*) as count
                FROM architectural_decision
                GROUP BY author
                ORDER BY count DESC
            """)
            by_author = {row[0]: row[1] for row in cursor.fetchall()}

            # Récentes (derniers 30 jours)
            cursor = conn.execute("""
                SELECT COUNT(*)
                FROM architectural_decision
                WHERE created_at >= datetime('now', '-30 days')
            """)
            last_30_days = cursor.fetchone()[0]

            return {
                'total': total,
                'by_status': by_status,
                'by_author': by_author,
                'last_30_days': last_30_days,
                'accepted': by_status.get('accepted', 0),
                'proposed': by_status.get('proposed', 0),
                'rejected': by_status.get('rejected', 0),
                'deprecated': by_status.get('deprecated', 0)
            }


# Factory function
def get_architecture_repository() -> ArchitectureRepository:
    """Récupère une instance du repository"""
    return ArchitectureRepository()
