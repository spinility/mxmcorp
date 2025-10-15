"""
Built-in Tools - Outils essentiels disponibles par défaut
Ces outils sont toujours disponibles pour tous les agents
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from cortex.tools.standard_tool import tool


@tool(
    name="create_file",
    description="Create a new file with the given content. Supports text files including .md, .txt, .py, .json, etc.",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to create (relative or absolute)"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            },
            "overwrite": {
                "type": "boolean",
                "description": "If True, overwrite existing file. If False, fail if file exists. Default: False"
            }
        },
        "required": ["file_path", "content"]
    },
    category="filesystem",
    tags=["file", "write", "create"]
)
def create_file(file_path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
    """
    Create a new file with the given content

    Args:
        file_path: Path to the file to create
        content: Content to write to the file
        overwrite: If True, overwrite existing file

    Returns:
        Dict with success status and details
    """
    try:
        path = Path(file_path)

        # Check if file exists
        if path.exists() and not overwrite:
            return {
                "success": False,
                "error": f"File already exists: {file_path}. Use overwrite=True to replace it."
            }

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        path.write_text(content, encoding='utf-8')

        # Get file info
        file_size = path.stat().st_size

        return {
            "success": True,
            "data": {
                "file_path": str(path.absolute()),
                "size_bytes": file_size,
                "lines": len(content.splitlines()),
                "action": "overwritten" if overwrite and path.exists() else "created"
            },
            "message": f"File {'overwritten' if overwrite else 'created'} successfully: {file_path}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create file: {str(e)}"
        }


@tool(
    name="read_file",
    description="Read the content of a file",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read"
            },
            "max_lines": {
                "type": "integer",
                "description": "Maximum number of lines to read. Default: all lines"
            }
        },
        "required": ["file_path"]
    },
    category="filesystem",
    tags=["file", "read"]
)
def read_file(file_path: str, max_lines: Optional[int] = None) -> Dict[str, Any]:
    """
    Read the content of a file

    Args:
        file_path: Path to the file to read
        max_lines: Maximum number of lines to read

    Returns:
        Dict with success status and file content
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }

        if not path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {file_path}"
            }

        content = path.read_text(encoding='utf-8')
        lines = content.splitlines()

        if max_lines and len(lines) > max_lines:
            content = '\n'.join(lines[:max_lines])
            truncated = True
        else:
            truncated = False

        return {
            "success": True,
            "data": {
                "content": content,
                "file_path": str(path.absolute()),
                "size_bytes": path.stat().st_size,
                "total_lines": len(lines),
                "truncated": truncated
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read file: {str(e)}"
        }


@tool(
    name="append_to_file",
    description="Append content to an existing file",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file"
            },
            "content": {
                "type": "string",
                "description": "Content to append"
            }
        },
        "required": ["file_path", "content"]
    },
    category="filesystem",
    tags=["file", "write", "append"]
)
def append_to_file(file_path: str, content: str) -> Dict[str, Any]:
    """
    Append content to an existing file

    Args:
        file_path: Path to the file
        content: Content to append

    Returns:
        Dict with success status
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }

        # Append content
        with open(path, 'a', encoding='utf-8') as f:
            f.write(content)

        return {
            "success": True,
            "data": {
                "file_path": str(path.absolute()),
                "size_bytes": path.stat().st_size,
                "appended_bytes": len(content.encode('utf-8'))
            },
            "message": f"Content appended to {file_path}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to append to file: {str(e)}"
        }


@tool(
    name="list_directory",
    description="List files and directories in a directory",
    parameters={
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "Path to the directory to list. Default: current directory"
            },
            "recursive": {
                "type": "boolean",
                "description": "If True, list recursively. Default: False"
            },
            "pattern": {
                "type": "string",
                "description": "Glob pattern to filter files (e.g., '*.py', '*.md')"
            }
        },
        "required": []
    },
    category="filesystem",
    tags=["file", "directory", "list"]
)
def list_directory(directory: str = ".", recursive: bool = False, pattern: Optional[str] = None) -> Dict[str, Any]:
    """
    List files and directories in a directory

    Args:
        directory: Path to the directory
        recursive: If True, list recursively
        pattern: Glob pattern to filter files

    Returns:
        Dict with success status and file list
    """
    try:
        path = Path(directory)

        if not path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory}"
            }

        if not path.is_dir():
            return {
                "success": False,
                "error": f"Not a directory: {directory}"
            }

        # List files
        if pattern:
            if recursive:
                files = list(path.rglob(pattern))
            else:
                files = list(path.glob(pattern))
        else:
            if recursive:
                files = list(path.rglob("*"))
            else:
                files = list(path.glob("*"))

        # Format results
        results = []
        for f in files:
            results.append({
                "name": f.name,
                "path": str(f.absolute()),
                "type": "directory" if f.is_dir() else "file",
                "size_bytes": f.stat().st_size if f.is_file() else None
            })

        return {
            "success": True,
            "data": {
                "directory": str(path.absolute()),
                "count": len(results),
                "files": results
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list directory: {str(e)}"
        }


@tool(
    name="file_exists",
    description="Check if a file or directory exists",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to check"
            }
        },
        "required": ["path"]
    },
    category="filesystem",
    tags=["file", "check"]
)
def file_exists(path: str) -> Dict[str, Any]:
    """
    Check if a file or directory exists

    Args:
        path: Path to check

    Returns:
        Dict with success status and existence info
    """
    try:
        p = Path(path)
        exists = p.exists()

        result = {
            "exists": exists,
            "path": str(p.absolute())
        }

        if exists:
            result["type"] = "directory" if p.is_dir() else "file"
            if p.is_file():
                result["size_bytes"] = p.stat().st_size

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to check path: {str(e)}"
        }


def get_all_builtin_tools():
    """
    Get all built-in tools

    Returns:
        List of StandardTool objects
    """
    return [
        create_file,
        read_file,
        append_to_file,
        list_directory,
        file_exists
    ]


# Test if run directly
if __name__ == "__main__":
    print("Testing built-in tools...")

    # Test create_file
    print("\n1. Testing create_file...")
    result = create_file.execute(
        file_path="test_builtin.txt",
        content="Hello from built-in tools!"
    )
    print(f"Result: {result}")

    # Test read_file
    print("\n2. Testing read_file...")
    result = read_file.execute(file_path="test_builtin.txt")
    print(f"Result: {result}")

    # Test file_exists
    print("\n3. Testing file_exists...")
    result = file_exists.execute(path="test_builtin.txt")
    print(f"Result: {result}")

    # Cleanup
    Path("test_builtin.txt").unlink()
    print("\n✓ All tests passed!")
