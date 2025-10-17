"""
Database Migration 001 - Add ML Training & Analytics Fields

Adds comprehensive fields for:
- ML training data collection
- Execution metrics tracking
- Subtask relationships
- Task analytics and insights
"""

import sqlite3
from pathlib import Path
from datetime import datetime


def migrate(db_path: str = "cortex/data/todo_pool.db"):
    """
    Apply migration to add ML and analytics fields

    Args:
        db_path: Path to TodoDB database
    """
    db_path = Path(db_path)

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return False

    print("🔄 Running migration 001: Add ML fields...")
    print()

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check if migration already applied
            cursor.execute("PRAGMA table_info(tasks)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'execution_duration_seconds' in columns:
                print("⚠️  Migration already applied!")
                return True

            # Add new columns to tasks table
            print("  📝 Adding ML tracking fields to tasks table...")

            new_columns = [
                # Identification
                ("parent_task_id", "INTEGER"),
                ("source_file", "TEXT"),
                ("source_line", "INTEGER"),

                # Execution
                ("priority", "INTEGER DEFAULT 5"),
                ("assigned_model", "TEXT"),

                # Timestamps
                ("started_at", "TIMESTAMP"),

                # Metrics
                ("execution_duration_seconds", "REAL"),
                ("total_tokens", "INTEGER"),
                ("prompt_tokens", "INTEGER"),
                ("completion_tokens", "INTEGER"),
                ("estimated_cost_usd", "REAL"),

                # Quality
                ("success_score", "REAL"),
                ("retry_count", "INTEGER DEFAULT 0"),
                ("error_log", "TEXT"),

                # Context ML
                ("context_files_loaded", "TEXT"),
                ("context_embeddings_used", "TEXT"),
                ("context_tokens_count", "INTEGER"),

                # Tool usage
                ("tools_called", "TEXT"),
                ("tool_call_sequence", "TEXT"),
                ("tool_success_rate", "REAL"),

                # Conversation
                ("full_conversation_json", "TEXT"),
                ("user_feedback", "TEXT"),

                # Analytics
                ("tags", "TEXT"),
                ("category", "TEXT"),
            ]

            for col_name, col_type in new_columns:
                try:
                    cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}")
                    print(f"    ✓ Added: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower():
                        print(f"    ⚠️  Already exists: {col_name}")
                    else:
                        raise

            print()
            print("  📝 Creating new tables...")

            # Task relationships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_id INTEGER NOT NULL,
                    child_id INTEGER NOT NULL,
                    relationship_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES tasks(id),
                    FOREIGN KEY (child_id) REFERENCES tasks(id)
                )
            """)
            print("    ✓ Created: task_relationships")

            # Task dependencies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    depends_on_task_id INTEGER NOT NULL,
                    dependency_type TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks(id),
                    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id)
                )
            """)
            print("    ✓ Created: task_dependencies")

            # Task analytics cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    total_tasks_created INTEGER,
                    total_tasks_completed INTEGER,
                    total_tasks_failed INTEGER,
                    avg_execution_time REAL,
                    total_tokens_used INTEGER,
                    total_cost_usd REAL,
                    success_rate REAL,
                    most_used_model TEXT,
                    most_common_category TEXT,
                    UNIQUE(date)
                )
            """)
            print("    ✓ Created: task_analytics")

            print()
            print("  📊 Creating indexes...")

            # Create indexes
            indexes = [
                ("idx_status", "CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)"),
                ("idx_priority", "CREATE INDEX IF NOT EXISTS idx_priority ON tasks(priority, status)"),
                ("idx_parent", "CREATE INDEX IF NOT EXISTS idx_parent ON tasks(parent_task_id)"),
                ("idx_created", "CREATE INDEX IF NOT EXISTS idx_created ON tasks(created_at)"),
                ("idx_category", "CREATE INDEX IF NOT EXISTS idx_category ON tasks(category)"),
            ]

            for idx_name, idx_sql in indexes:
                cursor.execute(idx_sql)
                print(f"    ✓ Created: {idx_name}")

            conn.commit()

            print()
            print("✅ Migration 001 completed successfully!")
            print()

            # Show stats
            cursor.execute("SELECT COUNT(*) FROM tasks")
            task_count = cursor.fetchone()[0]
            print(f"  📊 Total tasks in database: {task_count}")

            return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def rollback(db_path: str = "cortex/data/todo_pool.db"):
    """
    Rollback migration (note: SQLite doesn't support DROP COLUMN easily)

    This is for reference - manual rollback may be needed
    """
    print("⚠️  SQLite doesn't support DROP COLUMN easily.")
    print("To rollback, restore from backup or recreate database.")
    return False


if __name__ == "__main__":
    print("=" * 60)
    print("TodoDB Migration Tool")
    print("=" * 60)
    print()

    # Run migration
    success = migrate()

    if success:
        print()
        print("🎉 Database is now ready for ML training and analytics!")
    else:
        print()
        print("❌ Migration failed. Check errors above.")
