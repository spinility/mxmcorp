"""
Pip Tools - Outils pour la gestion des packages Python

Permet à Cortex d'installer, désinstaller et gérer des packages Python:
- pip install, uninstall, list
- pip show, search
"""

import subprocess
import sys
from typing import Dict, Any, List, Optional
from cortex.tools.standard_tool import tool


@tool(
    name="pip_install",
    description="Install Python packages using pip. Can install single or multiple packages.",
    parameters={
        "type": "object",
        "properties": {
            "package": {
                "type": "string",
                "description": "Package name(s) to install. Can specify version (e.g., 'requests==2.28.0')"
            },
            "upgrade": {
                "type": "boolean",
                "description": "Upgrade if already installed. Default: False"
            }
        },
        "required": ["package"]
    },
    category="python",
    tags=["pip", "install", "package", "dependency"]
)
def pip_install(package: str, upgrade: bool = False) -> Dict[str, Any]:
    """Install a Python package"""
    try:
        cmd = [sys.executable, "-m", "pip", "install"]

        if upgrade:
            cmd.append("--upgrade")

        cmd.append(package)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes for large packages
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"pip install failed: {result.stderr}"
            }

        return {
            "success": True,
            "data": {
                "package": package,
                "output": result.stdout,
                "message": f"Package '{package}' installed successfully"
            }
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Installation of '{package}' timed out (>5 minutes)"
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to install package: {str(e)}"}


@tool(
    name="pip_uninstall",
    description="Uninstall Python packages using pip. Removes the specified package.",
    parameters={
        "type": "object",
        "properties": {
            "package": {
                "type": "string",
                "description": "Package name to uninstall"
            }
        },
        "required": ["package"]
    },
    category="python",
    tags=["pip", "uninstall", "remove", "package"]
)
def pip_uninstall(package: str) -> Dict[str, Any]:
    """Uninstall a Python package"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", package],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"pip uninstall failed: {result.stderr}"
            }

        return {
            "success": True,
            "data": {
                "package": package,
                "message": f"Package '{package}' uninstalled successfully"
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to uninstall package: {str(e)}"}


@tool(
    name="pip_list",
    description="List installed Python packages. Shows all packages in the current environment.",
    parameters={
        "type": "object",
        "properties": {
            "outdated": {
                "type": "boolean",
                "description": "Show only outdated packages. Default: False"
            }
        },
        "required": []
    },
    category="python",
    tags=["pip", "list", "packages", "installed"]
)
def pip_list(outdated: bool = False) -> Dict[str, Any]:
    """List installed packages"""
    try:
        cmd = [sys.executable, "-m", "pip", "list"]

        if outdated:
            cmd.append("--outdated")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        lines = result.stdout.strip().split('\n')
        # Skip header lines
        package_lines = [line for line in lines[2:] if line.strip()]

        return {
            "success": True,
            "data": {
                "packages": result.stdout,
                "count": len(package_lines),
                "outdated": outdated
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to list packages: {str(e)}"}


@tool(
    name="pip_show",
    description="Show detailed information about an installed package (version, location, dependencies, etc.).",
    parameters={
        "type": "object",
        "properties": {
            "package": {
                "type": "string",
                "description": "Package name to show information for"
            }
        },
        "required": ["package"]
    },
    category="python",
    tags=["pip", "show", "info", "package"]
)
def pip_show(package: str) -> Dict[str, Any]:
    """Show package information"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Package '{package}' not found"
            }

        return {
            "success": True,
            "data": {
                "package": package,
                "info": result.stdout
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to show package info: {str(e)}"}


@tool(
    name="pip_freeze",
    description="Output installed packages in requirements format. Useful for creating requirements.txt.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    category="python",
    tags=["pip", "freeze", "requirements", "export"]
)
def pip_freeze() -> Dict[str, Any]:
    """Export installed packages in requirements format"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            timeout=30
        )

        packages = result.stdout.strip().split('\n')

        return {
            "success": True,
            "data": {
                "requirements": result.stdout,
                "count": len(packages),
                "message": "Package list in requirements format"
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to freeze packages: {str(e)}"}


def get_all_pip_tools() -> List:
    """Get all pip tools"""
    return [
        pip_install,
        pip_uninstall,
        pip_list,
        pip_show,
        pip_freeze
    ]


# Test if run directly
if __name__ == "__main__":
    print("Testing Pip tools...")

    print("\n1. Testing pip_list...")
    result = pip_list.execute()
    print(f"Success: {result.get('success')}")
    print(f"Packages count: {result.get('data', {}).get('count', 0)}")

    print("\n✓ Pip tools loaded successfully!")
