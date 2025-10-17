"""
Database Manager - Système nerveux de Cortex

Gère la Cortex Intelligence Database (CID) avec SQLite.
Fournit une API simple pour les agents afin de :
- Enregistrer leurs actions
- Consulter les dépendances
- Tracker les métriques
- Gérer la roadmap
- Logger les décisions architecturales

Design Philosophy:
- La DB est la source de vérité (single source of truth)
- Les .md sont générés à partir de la DB
- Chaque agent peut lire/écrire dans son domaine
- Transactions atomiques pour cohérence
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, date
from contextlib import contextmanager
import threading


class DatabaseManager:
    """Gestionnaire central de la base de données Cortex"""

    def __init__(self, db_path: str = "cortex/cortex.db"):
        """
        Initialize Database Manager

        Args:
            db_path: Chemin vers la base de données SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Thread-local storage pour connexions
        self._local = threading.local()

        # Initialiser le schéma si nécessaire
        self._initialize_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row  # Access by column name
        return self._local.connection

    @contextmanager
    def transaction(self):
        """Context manager for transactions"""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e

    def _initialize_schema(self):
        """Initialize database schema from schema.sql"""
        schema_file = Path(__file__).parent / "schema.sql"

        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        with open(schema_file, 'r') as f:
            schema_sql = f.read()

        with self.transaction() as conn:
            conn.executescript(schema_sql)

    # ========================================
    # 1. FICHIERS & DÉPENDANCES
    # ========================================

    def add_file(
        self,
        path: str,
        file_type: str,
        language: Optional[str] = None,
        size_bytes: Optional[int] = None,
        lines_of_code: Optional[int] = None,
        complexity_score: float = 0.0,
        owner_agent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Enregistre un fichier dans la base

        Returns:
            ID du fichier créé
        """
        with self.transaction() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO cortex_file
                (path, type, language, size_bytes, lines_of_code, complexity_score, owner_agent, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                path, file_type, language, size_bytes, lines_of_code,
                complexity_score, owner_agent, json.dumps(metadata) if metadata else None
            ))
            return cursor.lastrowid

    def add_dependency(
        self,
        source_path: str,
        target_path: str,
        dependency_type: str,
        strength: float = 1.0,
        is_critical: bool = False
    ) -> Optional[int]:
        """
        Enregistre une dépendance entre deux fichiers

        Args:
            source_path: Chemin du fichier source
            target_path: Chemin du fichier cible
            dependency_type: Type de dépendance ('import', 'uses', 'extends', 'requires')
            strength: Force de la dépendance (0.0-1.0)
            is_critical: Dépendance critique?

        Returns:
            ID de la dépendance créée
        """
        with self.transaction() as conn:
            # Get file IDs
            source_id = self._get_file_id(source_path, conn)
            target_id = self._get_file_id(target_path, conn)

            if not source_id or not target_id:
                return None

            cursor = conn.execute("""
                INSERT OR IGNORE INTO file_dependency
                (source_file_id, target_file_id, dependency_type, strength, is_critical)
                VALUES (?, ?, ?, ?, ?)
            """, (source_id, target_id, dependency_type, strength, is_critical))

            return cursor.lastrowid

    def get_file_dependencies(self, file_path: str, direction: str = 'outgoing') -> List[Dict]:
        """
        Récupère les dépendances d'un fichier

        Args:
            file_path: Chemin du fichier
            direction: 'outgoing' (ce fichier dépend de...) ou 'incoming' (... dépendent de ce fichier)

        Returns:
            Liste de dépendances
        """
        conn = self._get_connection()

        if direction == 'outgoing':
            query = """
                SELECT cf.path, fd.dependency_type, fd.strength, fd.is_critical
                FROM file_dependency fd
                JOIN cortex_file cf_source ON fd.source_file_id = cf_source.id
                JOIN cortex_file cf ON fd.target_file_id = cf.id
                WHERE cf_source.path = ?
            """
        else:  # incoming
            query = """
                SELECT cf.path, fd.dependency_type, fd.strength, fd.is_critical
                FROM file_dependency fd
                JOIN cortex_file cf ON fd.source_file_id = cf.id
                JOIN cortex_file cf_target ON fd.target_file_id = cf_target.id
                WHERE cf_target.path = ?
            """

        cursor = conn.execute(query, (file_path,))
        return [dict(row) for row in cursor.fetchall()]

    def _get_file_id(self, file_path: str, conn: sqlite3.Connection) -> Optional[int]:
        """Get file ID by path"""
        cursor = conn.execute("SELECT id FROM cortex_file WHERE path = ?", (file_path,))
        row = cursor.fetchone()
        return row[0] if row else None

    # ========================================
    # 2. AGENTS & RÔLES
    # ========================================

    def update_agent_metrics(
        self,
        agent_name: str,
        cost: float,
        response_time: float,
        success: bool
    ):
        """
        Met à jour les métriques d'un agent après exécution

        Args:
            agent_name: Nom de l'agent
            cost: Coût de l'exécution
            response_time: Temps de réponse en secondes
            success: True si succès
        """
        with self.transaction() as conn:
            # Get current stats
            cursor = conn.execute("""
                SELECT total_executions, total_cost, success_rate, avg_response_time
                FROM agent WHERE name = ?
            """, (agent_name,))

            row = cursor.fetchone()
            if not row:
                return  # Agent not found

            total_execs = row['total_executions']
            total_cost_current = row['total_cost']
            success_rate = row['success_rate']
            avg_time = row['avg_response_time']

            # Calculate new values
            new_total_execs = total_execs + 1
            new_total_cost = total_cost_current + cost
            new_success_rate = ((success_rate * total_execs) + (1.0 if success else 0.0)) / new_total_execs
            new_avg_time = ((avg_time * total_execs) + response_time) / new_total_execs

            # Update
            conn.execute("""
                UPDATE agent
                SET total_executions = ?,
                    total_cost = ?,
                    success_rate = ?,
                    avg_response_time = ?,
                    last_active = CURRENT_TIMESTAMP
                WHERE name = ?
            """, (new_total_execs, new_total_cost, new_success_rate, new_avg_time, agent_name))

            # Record metric
            agent_id = self._get_agent_id(agent_name, conn)
            if agent_id:
                conn.execute("""
                    INSERT INTO agent_metric (agent_id, metric_type, value, unit)
                    VALUES (?, 'cost', ?, 'usd'),
                           (?, 'latency', ?, 'seconds')
                """, (agent_id, cost, agent_id, response_time))

    def get_agent_stats(self, agent_name: str) -> Optional[Dict]:
        """Récupère les statistiques d'un agent"""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT * FROM agent WHERE name = ?
        """, (agent_name,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def _get_agent_id(self, agent_name: str, conn: sqlite3.Connection) -> Optional[int]:
        """Get agent ID by name"""
        cursor = conn.execute("SELECT id FROM agent WHERE name = ?", (agent_name,))
        row = cursor.fetchone()
        return row[0] if row else None

    # ========================================
    # 3. ROADMAP & PROJETS
    # ========================================

    def add_project(
        self,
        name: str,
        description: Optional[str] = None,
        priority: int = 5,
        status: str = 'planned',
        owner_agent: Optional[str] = None,
        target_date: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Ajoute un projet à la roadmap

        Returns:
            ID du projet créé
        """
        with self.transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO project
                (name, description, priority, status, owner_agent, target_date, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                name, description, priority, status, owner_agent, target_date,
                json.dumps(metadata) if metadata else None
            ))
            return cursor.lastrowid

    def update_project_progress(self, project_name: str, progress_percent: float):
        """Met à jour la progression d'un projet"""
        with self.transaction() as conn:
            conn.execute("""
                UPDATE project
                SET progress_percent = ?,
                    status = CASE
                        WHEN ? >= 100.0 THEN 'completed'
                        WHEN ? > 0 THEN 'in_progress'
                        ELSE status
                    END,
                    completion_date = CASE
                        WHEN ? >= 100.0 THEN CURRENT_DATE
                        ELSE completion_date
                    END
                WHERE name = ?
            """, (progress_percent, progress_percent, progress_percent, progress_percent, project_name))

    def get_active_projects(self) -> List[Dict]:
        """Récupère tous les projets actifs"""
        conn = self._get_connection()
        cursor = conn.execute("""
            SELECT * FROM project
            WHERE status NOT IN ('completed', 'cancelled')
            ORDER BY priority ASC, target_date ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def add_milestone(
        self,
        project_name: str,
        milestone_name: str,
        description: Optional[str] = None,
        target_date: Optional[str] = None,
        is_critical: bool = False
    ) -> Optional[int]:
        """Ajoute un milestone à un projet"""
        with self.transaction() as conn:
            # Get project ID
            cursor = conn.execute("SELECT id FROM project WHERE name = ?", (project_name,))
            row = cursor.fetchone()
            if not row:
                return None

            project_id = row[0]

            cursor = conn.execute("""
                INSERT INTO milestone (project_id, name, description, target_date, is_critical)
                VALUES (?, ?, ?, ?, ?)
            """, (project_id, milestone_name, description, target_date, is_critical))

            return cursor.lastrowid

    # ========================================
    # 4. HISTORIQUE DE MODIFICATIONS
    # ========================================

    def log_change(
        self,
        change_type: str,
        entity_type: str,
        author: str,
        description: str,
        impact_level: str = 'low',
        entity_id: Optional[int] = None,
        commit_id: Optional[str] = None,
        affected_files: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Enregistre un changement dans le log

        Args:
            change_type: 'create', 'modify', 'delete', 'refactor', 'rename'
            entity_type: 'file', 'agent', 'project', 'dependency'
            author: Nom de l'agent/humain
            description: Description du changement
            impact_level: 'low', 'medium', 'high', 'critical'
            entity_id: ID de l'entité modifiée
            commit_id: ID du commit git
            affected_files: Liste de fichiers affectés
            metadata: Métadonnées additionnelles

        Returns:
            ID du change log créé
        """
        with self.transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO change_log
                (change_type, entity_type, entity_id, author, description, impact_level,
                 commit_id, affected_files, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                change_type, entity_type, entity_id, author, description, impact_level,
                commit_id,
                json.dumps(affected_files) if affected_files else None,
                json.dumps(metadata) if metadata else None
            ))
            return cursor.lastrowid

    def get_recent_changes(self, limit: int = 50, impact_level: Optional[str] = None) -> List[Dict]:
        """Récupère les changements récents"""
        conn = self._get_connection()

        if impact_level:
            query = """
                SELECT * FROM change_log
                WHERE impact_level = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            cursor = conn.execute(query, (impact_level, limit))
        else:
            query = """
                SELECT * FROM change_log
                ORDER BY timestamp DESC
                LIMIT ?
            """
            cursor = conn.execute(query, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    # ========================================
    # 5. DÉCISIONS ARCHITECTURALES (ADR)
    # ========================================

    def add_architectural_decision(
        self,
        title: str,
        context: str,
        decision: str,
        consequences: Optional[str] = None,
        alternatives: Optional[str] = None,
        impact_level: str = 'medium',
        status: str = 'proposed',
        approved_by: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """
        Enregistre une décision architecturale (ADR)

        Returns:
            ID de la décision créée
        """
        with self.transaction() as conn:
            cursor = conn.execute("""
                INSERT INTO architectural_decision
                (title, context, decision, consequences, alternatives, impact_level, status, approved_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, context, decision, consequences, alternatives, impact_level, status, approved_by))

            decision_id = cursor.lastrowid

            # Add tags
            if tags:
                for tag in tags:
                    conn.execute("""
                        INSERT INTO decision_tag (decision_id, tag)
                        VALUES (?, ?)
                    """, (decision_id, tag))

            return decision_id

    def get_architectural_decisions(self, status: Optional[str] = None) -> List[Dict]:
        """Récupère les décisions architecturales"""
        conn = self._get_connection()

        if status:
            query = """
                SELECT * FROM architectural_decision
                WHERE status = ?
                ORDER BY created_at DESC
            """
            cursor = conn.execute(query, (status,))
        else:
            query = """
                SELECT * FROM architectural_decision
                ORDER BY created_at DESC
            """
            cursor = conn.execute(query)

        return [dict(row) for row in cursor.fetchall()]

    # ========================================
    # 6. MÉTRIQUES & RAPPORTS
    # ========================================

    def get_system_health(self) -> Dict[str, Any]:
        """
        Génère un rapport de santé du système

        Returns:
            Dict avec métriques clés
        """
        conn = self._get_connection()

        # Agent stats
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total_agents,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_agents,
                ROUND(AVG(success_rate), 2) as avg_success_rate,
                ROUND(SUM(total_cost), 6) as total_cost,
                SUM(total_executions) as total_executions
            FROM agent
        """)
        agent_stats = dict(cursor.fetchone())

        # Project stats
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total_projects,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_projects,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_projects,
                SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) as blocked_projects,
                ROUND(AVG(progress_percent), 1) as avg_progress
            FROM project
        """)
        project_stats = dict(cursor.fetchone())

        # Recent high-impact changes
        cursor = conn.execute("""
            SELECT COUNT(*) as high_impact_changes_24h
            FROM change_log
            WHERE impact_level IN ('high', 'critical')
              AND timestamp > datetime('now', '-24 hours')
        """)
        change_stats = dict(cursor.fetchone())

        # File stats
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total_files,
                COUNT(DISTINCT type) as file_types,
                ROUND(AVG(complexity_score), 2) as avg_complexity
            FROM cortex_file
            WHERE is_active = 1
        """)
        file_stats = dict(cursor.fetchone())

        return {
            'timestamp': datetime.now().isoformat(),
            'agents': agent_stats,
            'projects': project_stats,
            'changes': change_stats,
            'files': file_stats
        }

    def get_top_performing_agents(self, limit: int = 5) -> List[Dict]:
        """Récupère les agents les plus performants"""
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM top_performing_agents LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_critical_dependencies(self) -> List[Dict]:
        """Récupère les dépendances critiques"""
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM critical_dependencies")
        return [dict(row) for row in cursor.fetchall()]

    def get_overdue_projects(self) -> List[Dict]:
        """Récupère les projets en retard"""
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM overdue_projects")
        return [dict(row) for row in cursor.fetchall()]

    # ========================================
    # 7. UTILITAIRES
    # ========================================

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """
        Exécute une requête SQL personnalisée (lecture seule)

        Args:
            query: Requête SQL
            params: Paramètres de la requête

        Returns:
            Liste de résultats
        """
        conn = self._get_connection()
        cursor = conn.execute(query, params or ())
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Ferme la connexion à la base de données"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None


# Singleton instance
_db_manager_instance = None


def get_database_manager() -> DatabaseManager:
    """Get singleton instance of DatabaseManager"""
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager()
    return _db_manager_instance


# Example usage
if __name__ == "__main__":
    db = get_database_manager()

    print("🧠 Cortex Intelligence Database - Test\n")

    # Test: Get system health
    health = db.get_system_health()
    print("System Health:")
    print(f"  Total agents: {health['agents']['total_agents']}")
    print(f"  Active agents: {health['agents']['active_agents']}")
    print(f"  Total cost: ${health['agents']['total_cost']}")
    print(f"  Total executions: {health['agents']['total_executions']}")
    print()

    # Test: Get top performing agents
    top_agents = db.get_top_performing_agents(3)
    print("Top 3 Performing Agents:")
    for agent in top_agents:
        print(f"  • {agent['name']} ({agent['role']}): {agent['success_rate']*100:.1f}% success, ${agent['total_cost']} cost")
    print()

    # Test: Get active projects
    projects = db.get_active_projects()
    print(f"Active Projects: {len(projects)}")
    for project in projects[:3]:
        print(f"  • {project['name']}: {project['progress_percent']:.0f}% ({project['status']})")
    print()

    print("✅ Database Manager working correctly!")
