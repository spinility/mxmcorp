"""
File Repository - Accès aux données des fichiers et dépendances

Encapsule tous les accès DB liés aux fichiers et leur graphe de dépendances.
"""

from typing import List, Dict, Any, Optional
from cortex.database import get_database_manager


class FileRepository:
    """Repository pour la gestion des fichiers et dépendances"""

    def __init__(self):
        self.db = get_database_manager()

    def get_all_files(self) -> List[Dict[str, Any]]:
        """Récupère tous les fichiers"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, path, type, complexity_score, owner_agent,
                       lines_of_code, last_modified, created_at
                FROM cortex_file
                ORDER BY path
            """)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_file_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Récupère un fichier par son chemin"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, path, type, complexity_score, owner_agent,
                       lines_of_code, last_modified, created_at, metadata
                FROM cortex_file
                WHERE path = ?
            """, (path,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None

    def add_file(self, path: str, file_type: str, complexity_score: float = 0.0,
                owner_agent: Optional[str] = None, lines_of_code: int = 0) -> int:
        """Ajoute un fichier"""
        return self.db.add_file(path, file_type, complexity_score,
                               owner_agent, lines_of_code)

    def get_dependencies(self, file_path: str,
                        direction: str = 'outgoing') -> List[Dict[str, Any]]:
        """Récupère les dépendances d'un fichier"""
        return self.db.get_file_dependencies(file_path, direction)

    def add_dependency(self, source_path: str, target_path: str,
                      dependency_type: str, strength: float = 1.0) -> int:
        """Ajoute une dépendance entre fichiers"""
        return self.db.add_dependency(source_path, target_path,
                                     dependency_type, strength)

    def get_critical_dependencies(self) -> List[Dict[str, Any]]:
        """Récupère les dépendances critiques"""
        return self.db.get_critical_dependencies()

    def get_files_by_type(self, file_type: str) -> List[Dict[str, Any]]:
        """Récupère les fichiers par type"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, path, complexity_score, owner_agent,
                       lines_of_code, last_modified
                FROM cortex_file
                WHERE type = ?
                ORDER BY complexity_score DESC
            """, (file_type,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_files_by_owner(self, owner_agent: str) -> List[Dict[str, Any]]:
        """Récupère les fichiers gérés par un agent"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, path, type, complexity_score,
                       lines_of_code, last_modified
                FROM cortex_file
                WHERE owner_agent = ?
                ORDER BY complexity_score DESC
            """, (owner_agent,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_most_complex_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupère les fichiers les plus complexes"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, path, type, complexity_score, owner_agent,
                       lines_of_code
                FROM cortex_file
                ORDER BY complexity_score DESC
                LIMIT ?
            """, (limit,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_dependency_graph(self) -> Dict[str, Any]:
        """Récupère le graphe complet des dépendances"""
        with self.db.get_connection() as conn:
            # Tous les fichiers
            cursor = conn.execute("""
                SELECT id, path, type, complexity_score
                FROM cortex_file
                ORDER BY path
            """)
            files_columns = [desc[0] for desc in cursor.description]
            files = [dict(zip(files_columns, row)) for row in cursor.fetchall()]

            # Toutes les dépendances
            cursor = conn.execute("""
                SELECT
                    cf1.path as source_path,
                    cf2.path as target_path,
                    fd.dependency_type,
                    fd.strength,
                    fd.is_critical
                FROM file_dependency fd
                JOIN cortex_file cf1 ON fd.source_file_id = cf1.id
                JOIN cortex_file cf2 ON fd.target_file_id = cf2.id
            """)
            deps_columns = [desc[0] for desc in cursor.description]
            dependencies = [dict(zip(deps_columns, row)) for row in cursor.fetchall()]

            return {
                'files': files,
                'dependencies': dependencies,
                'file_count': len(files),
                'dependency_count': len(dependencies)
            }

    def update_file_complexity(self, file_path: str, complexity_score: float):
        """Met à jour le score de complexité d'un fichier"""
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE cortex_file
                SET complexity_score = ?, last_modified = CURRENT_TIMESTAMP
                WHERE path = ?
            """, (complexity_score, file_path))
            conn.commit()

    def update_file_owner(self, file_path: str, owner_agent: str):
        """Met à jour l'agent propriétaire d'un fichier"""
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE cortex_file
                SET owner_agent = ?, last_modified = CURRENT_TIMESTAMP
                WHERE path = ?
            """, (owner_agent, file_path))
            conn.commit()


# Factory function
def get_file_repository() -> FileRepository:
    """Récupère une instance du repository"""
    return FileRepository()
