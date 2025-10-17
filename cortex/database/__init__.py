"""
Cortex Intelligence Database Package

Le système nerveux de Cortex - gère toutes les relations, états et dépendances.

Modules:
- database_manager: API principale pour interagir avec la DB
- schema.sql: Schéma SQL de la base de données

Usage:
    from cortex.database import get_database_manager

    db = get_database_manager()
    db.add_project("New Feature", priority=1)
    projects = db.get_active_projects()
"""

from cortex.database.database_manager import (
    DatabaseManager,
    get_database_manager
)

__all__ = [
    'DatabaseManager',
    'get_database_manager'
]
