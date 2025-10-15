"""
Git Tools - Outils pour les opérations Git

Permet à Cortex d'effectuer des opérations Git courantes:
- git status, add, commit, push, pull
- git branch, checkout
- git log, diff
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from cortex.tools.standard_tool import tool


@tool(
    name="git_status",
    description="Show the working tree status. Displays which files are modified, staged, or untracked.",
    parameters={
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "Directory path. Default: current directory"
            }
        },
        "required": []
    },
    category="git",
    tags=["git", "status", "version-control"]
)
def git_status(directory: str = ".") -> Dict[str, Any]:
    """Get git status"""
    try:
        result = subprocess.run(
            ["git", "status"],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=10
        )

        return {
            "success": True,
            "data": {
                "output": result.stdout,
                "directory": str(Path(directory).absolute())
            }
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "Git not installed or not in PATH"}
    except Exception as e:
        return {"success": False, "error": f"Failed to run git status: {str(e)}"}


@tool(
    name="git_add",
    description="Add file contents to the staging area. Use '.' to add all files.",
    parameters={
        "type": "object",
        "properties": {
            "files": {
                "type": "string",
                "description": "Files to add (e.g., '.' for all, 'file.txt' for specific file)"
            },
            "directory": {
                "type": "string",
                "description": "Directory path. Default: current directory"
            }
        },
        "required": ["files"]
    },
    category="git",
    tags=["git", "add", "stage"]
)
def git_add(files: str, directory: str = ".") -> Dict[str, Any]:
    """Add files to staging area"""
    try:
        result = subprocess.run(
            ["git", "add", files],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"git add failed: {result.stderr}"
            }

        return {
            "success": True,
            "data": {
                "files_added": files,
                "message": f"Files added to staging area: {files}"
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to add files: {str(e)}"}


@tool(
    name="git_commit",
    description="Record changes to the repository with a commit message.",
    parameters={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Commit message describing the changes"
            },
            "directory": {
                "type": "string",
                "description": "Directory path. Default: current directory"
            }
        },
        "required": ["message"]
    },
    category="git",
    tags=["git", "commit", "save"]
)
def git_commit(message: str, directory: str = ".") -> Dict[str, Any]:
    """Create a git commit"""
    try:
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"git commit failed: {result.stderr}"
            }

        return {
            "success": True,
            "data": {
                "output": result.stdout,
                "message": "Commit created successfully"
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to commit: {str(e)}"}


@tool(
    name="git_push",
    description="Push local commits to remote repository. Updates the remote branch with local changes.",
    parameters={
        "type": "object",
        "properties": {
            "remote": {
                "type": "string",
                "description": "Remote name. Default: origin"
            },
            "branch": {
                "type": "string",
                "description": "Branch name. If not specified, pushes current branch"
            },
            "directory": {
                "type": "string",
                "description": "Directory path. Default: current directory"
            }
        },
        "required": []
    },
    category="git",
    tags=["git", "push", "remote", "sync"]
)
def git_push(remote: str = "origin", branch: Optional[str] = None, directory: str = ".") -> Dict[str, Any]:
    """Push commits to remote"""
    try:
        cmd = ["git", "push", remote]
        if branch:
            cmd.append(branch)

        result = subprocess.run(
            cmd,
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"git push failed: {result.stderr}"
            }

        return {
            "success": True,
            "data": {
                "output": result.stderr,  # Git push outputs to stderr
                "message": "Changes pushed successfully"
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to push: {str(e)}"}


@tool(
    name="git_pull",
    description="Fetch and integrate changes from remote repository to local branch.",
    parameters={
        "type": "object",
        "properties": {
            "remote": {
                "type": "string",
                "description": "Remote name. Default: origin"
            },
            "branch": {
                "type": "string",
                "description": "Branch name. If not specified, pulls current branch"
            },
            "directory": {
                "type": "string",
                "description": "Directory path. Default: current directory"
            }
        },
        "required": []
    },
    category="git",
    tags=["git", "pull", "remote", "sync"]
)
def git_pull(remote: str = "origin", branch: Optional[str] = None, directory: str = ".") -> Dict[str, Any]:
    """Pull changes from remote"""
    try:
        cmd = ["git", "pull", remote]
        if branch:
            cmd.append(branch)

        result = subprocess.run(
            cmd,
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"git pull failed: {result.stderr}"
            }

        return {
            "success": True,
            "data": {
                "output": result.stdout,
                "message": "Changes pulled successfully"
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to pull: {str(e)}"}


@tool(
    name="git_log",
    description="Show commit logs. Displays recent commit history with messages and authors.",
    parameters={
        "type": "object",
        "properties": {
            "max_count": {
                "type": "integer",
                "description": "Maximum number of commits to show. Default: 10"
            },
            "directory": {
                "type": "string",
                "description": "Directory path. Default: current directory"
            }
        },
        "required": []
    },
    category="git",
    tags=["git", "log", "history"]
)
def git_log(max_count: int = 10, directory: str = ".") -> Dict[str, Any]:
    """Show git commit log"""
    try:
        result = subprocess.run(
            ["git", "log", f"-{max_count}", "--oneline"],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=10
        )

        return {
            "success": True,
            "data": {
                "commits": result.stdout,
                "count": len(result.stdout.strip().split('\n')) if result.stdout else 0
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to get log: {str(e)}"}


def get_all_git_tools() -> List:
    """Get all git tools"""
    return [
        git_status,
        git_add,
        git_commit,
        git_push,
        git_pull,
        git_log
    ]


# Test if run directly
if __name__ == "__main__":
    print("Testing Git tools...")

    print("\n1. Testing git_status...")
    result = git_status.execute()
    print(f"Success: {result.get('success')}")

    print("\n✓ Git tools loaded successfully!")
