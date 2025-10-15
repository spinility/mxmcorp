"""
Built-in Filesystem Tools
"""

from pathlib import Path
from typing import Tuple, Optional, List
from datetime import datetime
import os
import glob

from cortex.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class ListFilesTool(BaseTool):
    """Liste les fichiers dans un répertoire"""

    def __init__(self):
        metadata = ToolMetadata(
            name="ListFiles",
            description="Liste tous les fichiers dans un répertoire avec pattern optionnel",
            version="1.0.0",
            author="human",
            created_at=datetime.now(),
            category="filesystem",
            tags=["files", "directory", "list"],
            cost_estimate="free"
        )
        super().__init__(metadata)

    def validate_params(self, **kwargs) -> Tuple[bool, Optional[str]]:
        if "path" not in kwargs:
            return False, "Missing required parameter: path"
        return True, None

    def execute(self, path: str = ".", pattern: str = "*", **kwargs) -> ToolResult:
        try:
            path_obj = Path(path)

            if not path_obj.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Path does not exist: {path}"
                )

            # Lister les fichiers
            if path_obj.is_dir():
                files = list(path_obj.glob(pattern))
            else:
                files = [path_obj]

            # Formatter les résultats
            results = []
            for f in files:
                stat = f.stat()
                results.append({
                    "name": f.name,
                    "path": str(f),
                    "size": stat.st_size,
                    "is_dir": f.is_dir(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

            return ToolResult(
                success=True,
                data={
                    "path": str(path),
                    "count": len(results),
                    "files": results
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )


class ReadFileTool(BaseTool):
    """Lit le contenu d'un fichier"""

    def __init__(self):
        metadata = ToolMetadata(
            name="ReadFile",
            description="Lit le contenu d'un fichier texte",
            version="1.0.0",
            author="human",
            created_at=datetime.now(),
            category="filesystem",
            tags=["files", "read", "content"],
            cost_estimate="free"
        )
        super().__init__(metadata)

    def validate_params(self, **kwargs) -> Tuple[bool, Optional[str]]:
        if "filepath" not in kwargs:
            return False, "Missing required parameter: filepath"
        return True, None

    def execute(self, filepath: str, max_lines: int = None, **kwargs) -> ToolResult:
        try:
            path = Path(filepath)

            if not path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"File does not exist: {filepath}"
                )

            if not path.is_file():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Not a file: {filepath}"
                )

            # Lire le fichier
            content = path.read_text()

            # Limiter le nombre de lignes si demandé
            if max_lines:
                lines = content.split('\n')
                content = '\n'.join(lines[:max_lines])
                truncated = len(lines) > max_lines
            else:
                truncated = False

            return ToolResult(
                success=True,
                data={
                    "filepath": str(filepath),
                    "content": content,
                    "size": path.stat().st_size,
                    "lines": len(content.split('\n')),
                    "truncated": truncated
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )


class SearchFilesTool(BaseTool):
    """Recherche des fichiers par nom ou contenu"""

    def __init__(self):
        metadata = ToolMetadata(
            name="SearchFiles",
            description="Recherche des fichiers par nom ou dans leur contenu",
            version="1.0.0",
            author="human",
            created_at=datetime.now(),
            category="filesystem",
            tags=["files", "search", "grep"],
            cost_estimate="free"
        )
        super().__init__(metadata)

    def validate_params(self, **kwargs) -> Tuple[bool, Optional[str]]:
        if "query" not in kwargs:
            return False, "Missing required parameter: query"
        return True, None

    def execute(
        self,
        query: str,
        path: str = ".",
        search_content: bool = False,
        file_pattern: str = "*",
        **kwargs
    ) -> ToolResult:
        try:
            path_obj = Path(path)

            if not path_obj.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Path does not exist: {path}"
                )

            results = []

            # Rechercher dans les noms de fichiers
            for file in path_obj.rglob(file_pattern):
                if file.is_file():
                    # Match dans le nom
                    if query.lower() in file.name.lower():
                        results.append({
                            "filepath": str(file),
                            "match_type": "filename",
                            "match": file.name
                        })

                    # Rechercher dans le contenu si demandé
                    elif search_content:
                        try:
                            content = file.read_text()
                            if query.lower() in content.lower():
                                # Trouver la ligne
                                for i, line in enumerate(content.split('\n'), 1):
                                    if query.lower() in line.lower():
                                        results.append({
                                            "filepath": str(file),
                                            "match_type": "content",
                                            "line_number": i,
                                            "line": line.strip()
                                        })
                                        break  # Première occurrence seulement
                        except:
                            # Ignorer les fichiers binaires ou illisibles
                            pass

            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "path": str(path),
                    "count": len(results),
                    "results": results[:100]  # Limiter à 100 résultats
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
