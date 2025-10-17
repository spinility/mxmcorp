"""
Codebase Repository - Accès aux données de la structure du code

Encapsule tous les accès DB liés à la structure du codebase :
modules, classes, fonctions, imports, relations.
"""

from typing import List, Dict, Any, Optional
import json
from cortex.database import get_database_manager


class CodebaseRepository:
    """Repository pour la gestion de la structure du code"""

    def __init__(self):
        self.db = get_database_manager()

    # ========================================
    # MODULES
    # ========================================

    def add_module(self, file_id: int, name: str, is_package: bool = False,
                  docstring: Optional[str] = None, lines_of_code: int = 0) -> int:
        """Ajoute un module"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO code_module (file_id, name, is_package, docstring, lines_of_code)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(file_id, name) DO UPDATE SET
                    is_package = excluded.is_package,
                    docstring = excluded.docstring,
                    lines_of_code = excluded.lines_of_code,
                    updated_at = CURRENT_TIMESTAMP
            """, (file_id, name, is_package, docstring, lines_of_code))
            conn.commit()
            return cursor.lastrowid

    def get_module_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Récupère un module par son nom"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.*, f.path as file_path
                FROM code_module m
                JOIN cortex_file f ON m.file_id = f.id
                WHERE m.name = ?
            """, (name,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None

    def get_all_modules(self) -> List[Dict[str, Any]]:
        """Récupère tous les modules"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.*, f.path as file_path
                FROM code_module m
                JOIN cortex_file f ON m.file_id = f.id
                ORDER BY m.name
            """)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # ========================================
    # CLASSES
    # ========================================

    def add_class(self, module_id: int, name: str, full_name: str,
                 base_classes: Optional[List[str]] = None, docstring: Optional[str] = None,
                 is_abstract: bool = False, decorators: Optional[List[str]] = None,
                 line_start: int = 0, line_end: int = 0,
                 complexity_score: float = 0.0) -> int:
        """Ajoute une classe"""
        base_json = json.dumps(base_classes) if base_classes else None
        dec_json = json.dumps(decorators) if decorators else None

        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO code_class (
                    module_id, name, full_name, base_classes, docstring,
                    is_abstract, decorators, line_start, line_end, complexity_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(module_id, name) DO UPDATE SET
                    full_name = excluded.full_name,
                    base_classes = excluded.base_classes,
                    docstring = excluded.docstring,
                    is_abstract = excluded.is_abstract,
                    decorators = excluded.decorators,
                    line_start = excluded.line_start,
                    line_end = excluded.line_end,
                    complexity_score = excluded.complexity_score,
                    updated_at = CURRENT_TIMESTAMP
            """, (module_id, name, full_name, base_json, docstring,
                  is_abstract, dec_json, line_start, line_end, complexity_score))
            conn.commit()
            return cursor.lastrowid

    def get_class_by_full_name(self, full_name: str) -> Optional[Dict[str, Any]]:
        """Récupère une classe par son nom complet"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT c.*, m.name as module_name, f.path as file_path
                FROM code_class c
                JOIN code_module m ON c.module_id = m.id
                JOIN cortex_file f ON m.file_id = f.id
                WHERE c.full_name = ?
            """, (full_name,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            if row:
                result = dict(zip(columns, row))
                # Parse JSON fields
                if result.get('base_classes'):
                    result['base_classes'] = json.loads(result['base_classes'])
                if result.get('decorators'):
                    result['decorators'] = json.loads(result['decorators'])
                return result
            return None

    def get_classes_in_module(self, module_name: str) -> List[Dict[str, Any]]:
        """Récupère toutes les classes d'un module"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT c.*, m.name as module_name
                FROM code_class c
                JOIN code_module m ON c.module_id = m.id
                WHERE m.name = ?
                ORDER BY c.name
            """, (module_name,))
            columns = [desc[0] for desc in cursor.description]
            results = []
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                if result.get('base_classes'):
                    result['base_classes'] = json.loads(result['base_classes'])
                results.append(result)
            return results

    def get_complex_classes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Récupère les classes les plus complexes"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM complex_classes LIMIT ?
            """, (limit,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # ========================================
    # FUNCTIONS
    # ========================================

    def add_function(self, name: str, full_name: str, signature: Optional[str] = None,
                    module_id: Optional[int] = None, class_id: Optional[int] = None,
                    docstring: Optional[str] = None, return_type: Optional[str] = None,
                    is_async: bool = False, is_static: bool = False,
                    is_classmethod: bool = False, is_property: bool = False,
                    decorators: Optional[List[str]] = None,
                    line_start: int = 0, line_end: int = 0,
                    complexity_score: float = 0.0,
                    parameters: Optional[List[Dict]] = None) -> int:
        """Ajoute une fonction ou méthode"""
        dec_json = json.dumps(decorators) if decorators else None
        params_json = json.dumps(parameters) if parameters else None

        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO code_function (
                    module_id, class_id, name, full_name, signature, return_type,
                    docstring, is_async, is_static, is_classmethod, is_property,
                    decorators, line_start, line_end, complexity_score, parameters
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (module_id, class_id, name, full_name, signature, return_type,
                  docstring, is_async, is_static, is_classmethod, is_property,
                  dec_json, line_start, line_end, complexity_score, params_json))
            conn.commit()
            return cursor.lastrowid

    def get_function_by_full_name(self, full_name: str) -> Optional[Dict[str, Any]]:
        """Récupère une fonction par son nom complet"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT f.*, m.name as module_name, c.name as class_name
                FROM code_function f
                LEFT JOIN code_module m ON f.module_id = m.id
                LEFT JOIN code_class c ON f.class_id = c.id
                WHERE f.full_name = ?
            """, (full_name,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            if row:
                result = dict(zip(columns, row))
                if result.get('decorators'):
                    result['decorators'] = json.loads(result['decorators'])
                if result.get('parameters'):
                    result['parameters'] = json.loads(result['parameters'])
                return result
            return None

    def get_functions_in_module(self, module_name: str) -> List[Dict[str, Any]]:
        """Récupère toutes les fonctions d'un module"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT f.*
                FROM code_function f
                JOIN code_module m ON f.module_id = m.id
                WHERE m.name = ? AND f.class_id IS NULL
                ORDER BY f.name
            """, (module_name,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_methods_in_class(self, class_full_name: str) -> List[Dict[str, Any]]:
        """Récupère toutes les méthodes d'une classe"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT f.*
                FROM code_function f
                JOIN code_class c ON f.class_id = c.id
                WHERE c.full_name = ?
                ORDER BY f.line_start
            """, (class_full_name,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_complex_functions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Récupère les fonctions les plus complexes"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM complex_functions LIMIT ?
            """, (limit,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # ========================================
    # IMPORTS
    # ========================================

    def add_import(self, source_module_id: int, imported_module: str,
                  import_type: str, alias: Optional[str] = None,
                  is_external: bool = False, line_number: int = 0) -> int:
        """Ajoute un import"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO code_import (
                    source_module_id, imported_module, import_type,
                    alias, is_external, line_number
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (source_module_id, imported_module, import_type,
                  alias, is_external, line_number))
            conn.commit()
            return cursor.lastrowid

    def get_imports_for_module(self, module_name: str) -> List[Dict[str, Any]]:
        """Récupère tous les imports d'un module"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT i.*
                FROM code_import i
                JOIN code_module m ON i.source_module_id = m.id
                WHERE m.name = ?
                ORDER BY i.line_number
            """, (module_name,))
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_import_graph(self) -> Dict[str, Any]:
        """Récupère le graphe complet des imports"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM import_graph")
            columns = [desc[0] for desc in cursor.description]
            imports = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return {
                'imports': imports,
                'import_count': len(imports)
            }

    # ========================================
    # RELATIONS
    # ========================================

    def add_relation(self, source_type: str, source_id: int,
                    target_type: str, target_id: int,
                    relation_type: str, confidence: float = 1.0) -> int:
        """Ajoute une relation entre entités"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO code_relation (
                    source_type, source_id, target_type, target_id,
                    relation_type, confidence
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (source_type, source_id, target_type, target_id,
                  relation_type, confidence))
            conn.commit()
            return cursor.lastrowid

    def get_relations_for_entity(self, entity_type: str, entity_id: int,
                                 direction: str = 'outgoing') -> List[Dict[str, Any]]:
        """Récupère les relations d'une entité"""
        with self.db.get_connection() as conn:
            if direction == 'outgoing':
                cursor = conn.execute("""
                    SELECT * FROM code_relation
                    WHERE source_type = ? AND source_id = ?
                """, (entity_type, entity_id))
            else:
                cursor = conn.execute("""
                    SELECT * FROM code_relation
                    WHERE target_type = ? AND target_id = ?
                """, (entity_type, entity_id))

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # ========================================
    # STATISTIQUES
    # ========================================

    def get_codebase_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques globales du codebase"""
        with self.db.get_connection() as conn:
            # Modules
            cursor = conn.execute("SELECT COUNT(*) FROM code_module")
            module_count = cursor.fetchone()[0]

            # Classes
            cursor = conn.execute("SELECT COUNT(*) FROM code_class")
            class_count = cursor.fetchone()[0]

            # Functions
            cursor = conn.execute("SELECT COUNT(*) FROM code_function")
            function_count = cursor.fetchone()[0]

            # Imports
            cursor = conn.execute("SELECT COUNT(*) FROM code_import")
            import_count = cursor.fetchone()[0]

            # Relations
            cursor = conn.execute("SELECT COUNT(*) FROM code_relation")
            relation_count = cursor.fetchone()[0]

            # Total LOC
            cursor = conn.execute("SELECT SUM(lines_of_code) FROM code_module")
            total_loc = cursor.fetchone()[0] or 0

            # Complexité moyenne
            cursor = conn.execute("""
                SELECT AVG(complexity_score)
                FROM code_function
                WHERE complexity_score > 0
            """)
            avg_complexity = cursor.fetchone()[0] or 0.0

            return {
                'module_count': module_count,
                'class_count': class_count,
                'function_count': function_count,
                'import_count': import_count,
                'relation_count': relation_count,
                'total_lines_of_code': total_loc,
                'average_complexity': avg_complexity
            }

    def search_code_entities(self, search_term: str) -> Dict[str, Any]:
        """Recherche dans les entités du code"""
        search_pattern = f'%{search_term}%'

        with self.db.get_connection() as conn:
            # Modules
            cursor = conn.execute("""
                SELECT 'module' as type, name, docstring
                FROM code_module
                WHERE name LIKE ? OR docstring LIKE ?
                LIMIT 10
            """, (search_pattern, search_pattern))
            modules = [dict(zip([d[0] for d in cursor.description], row))
                      for row in cursor.fetchall()]

            # Classes
            cursor = conn.execute("""
                SELECT 'class' as type, full_name as name, docstring
                FROM code_class
                WHERE name LIKE ? OR full_name LIKE ? OR docstring LIKE ?
                LIMIT 10
            """, (search_pattern, search_pattern, search_pattern))
            classes = [dict(zip([d[0] for d in cursor.description], row))
                      for row in cursor.fetchall()]

            # Functions
            cursor = conn.execute("""
                SELECT 'function' as type, full_name as name, docstring
                FROM code_function
                WHERE name LIKE ? OR full_name LIKE ? OR docstring LIKE ?
                LIMIT 10
            """, (search_pattern, search_pattern, search_pattern))
            functions = [dict(zip([d[0] for d in cursor.description], row))
                        for row in cursor.fetchall()]

            return {
                'modules': modules,
                'classes': classes,
                'functions': functions,
                'total_results': len(modules) + len(classes) + len(functions)
            }


# Factory function
def get_codebase_repository() -> CodebaseRepository:
    """Récupère une instance du repository"""
    return CodebaseRepository()
