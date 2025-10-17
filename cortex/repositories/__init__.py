"""
Cortex Repository Layer

Couche d'accès aux données - encapsule tous les accès à la base de données.
Pattern Repository pour séparer la logique métier de l'accès aux données.

Repositories disponibles:
- AgentRepository: CRUD agents et métriques
- ProjectRepository: CRUD projets et roadmap
- FileRepository: CRUD fichiers et dépendances (graphe)
- ChangeLogRepository: Audit trail et historique
- ArchitectureRepository: ADRs et décisions
- CodebaseRepository: Structure du code (classes, fonctions, relations)
"""

from cortex.repositories.agent_repository import AgentRepository
from cortex.repositories.project_repository import ProjectRepository
from cortex.repositories.file_repository import FileRepository
from cortex.repositories.changelog_repository import ChangeLogRepository
from cortex.repositories.architecture_repository import ArchitectureRepository
from cortex.repositories.codebase_repository import CodebaseRepository

__all__ = [
    'AgentRepository',
    'ProjectRepository',
    'FileRepository',
    'ChangeLogRepository',
    'ArchitectureRepository',
    'CodebaseRepository'
]
