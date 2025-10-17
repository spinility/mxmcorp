"""
ChangeLog Repository - Accès aux données du journal des changements

Encapsule tous les accès DB liés au change log et à l'audit trail.
"""

from typing import List, Dict, Any, Optional
from cortex.database import get_database_manager


class ChangeLogRepository:
    """Repository pour la gestion du change log"""

    def __init__(self):
        self.db = get_database_manager()

    def log_change(self, change_type: str, entity_type: str,
                   author: str, description: str,
                   impact_level: str = 'low',
                   entity_id: Optional[int] = None,
                   commit_id: Optional[str] = None,
                   affected_files: Optional[List[str]] = None,
                   metadata: Optional[Dict] = None) -> int:
        """Enregistre un changement"""
        return self.db.log_change(
            change_type=change_type,
            entity_type=entity_type,
            author=author,
            description=description,
            impact_level=impact_level,
            entity_id=entity_id,
            commit_id=commit_id,
            affected_files=affected_files,
            metadata=metadata
        )

    def get_recent_changes(self, limit: int = 50,
                          min_impact: Optional[str] = None) -> List[Dict[str, Any]]:
        """Récupère les changements récents"""
        return self.db.get_recent_changes(limit, min_impact)

    def get_changes_by_author(self, author: str,
                             limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les changements par auteur"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, change_type, entity_type, author, description,
                       impact_level, timestamp
                FROM change_log
                WHERE author = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (author, limit))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_changes_by_entity_type(self, entity_type: str,
                                   limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les changements par type d'entité"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, change_type, entity_type, author, description,
                       impact_level, timestamp
                FROM change_log
                WHERE entity_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (entity_type, limit))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_high_impact_changes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les changements à fort impact"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, change_type, entity_type, author, description,
                       impact_level, timestamp
                FROM change_log
                WHERE impact_level IN ('high', 'critical')
                ORDER BY
                    CASE impact_level
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        ELSE 3
                    END,
                    timestamp DESC
                LIMIT ?
            """, (limit,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_changes_by_date_range(self, start_date: str,
                                  end_date: str) -> List[Dict[str, Any]]:
        """Récupère les changements dans une plage de dates"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, change_type, entity_type, author, description,
                       impact_level, timestamp
                FROM change_log
                WHERE date(timestamp) BETWEEN date(?) AND date(?)
                ORDER BY timestamp DESC
            """, (start_date, end_date))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_change_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques du change log"""
        with self.db.get_connection() as conn:
            # Total
            cursor = conn.execute("SELECT COUNT(*) FROM change_log")
            total = cursor.fetchone()[0]

            # Par type de changement
            cursor = conn.execute("""
                SELECT change_type, COUNT(*) as count
                FROM change_log
                GROUP BY change_type
                ORDER BY count DESC
            """)
            by_type = {row[0]: row[1] for row in cursor.fetchall()}

            # Par niveau d'impact
            cursor = conn.execute("""
                SELECT impact_level, COUNT(*) as count
                FROM change_log
                GROUP BY impact_level
                ORDER BY count DESC
            """)
            by_impact = {row[0]: row[1] for row in cursor.fetchall()}

            # Par auteur
            cursor = conn.execute("""
                SELECT author, COUNT(*) as count
                FROM change_log
                GROUP BY author
                ORDER BY count DESC
                LIMIT 10
            """)
            top_authors = {row[0]: row[1] for row in cursor.fetchall()}

            # Changements récents (dernières 24h)
            cursor = conn.execute("""
                SELECT COUNT(*)
                FROM change_log
                WHERE timestamp >= datetime('now', '-1 day')
            """)
            last_24h = cursor.fetchone()[0]

            return {
                'total': total,
                'by_type': by_type,
                'by_impact': by_impact,
                'top_authors': top_authors,
                'last_24h': last_24h
            }

    def search_changes(self, search_term: str,
                      limit: int = 50) -> List[Dict[str, Any]]:
        """Recherche dans les descriptions de changements"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, change_type, entity_type, author, description,
                       impact_level, timestamp
                FROM change_log
                WHERE description LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f'%{search_term}%', limit))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


# Factory function
def get_changelog_repository() -> ChangeLogRepository:
    """Récupère une instance du repository"""
    return ChangeLogRepository()
