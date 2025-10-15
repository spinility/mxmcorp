"""
Environment Scanner - Scanne et valide l'environnement d'exécution de Cortex

Responsabilités:
- Vérifie l'accès au système de fichiers
- Détecte les packages Python installés
- Vérifie les API keys configurées
- Teste l'accès Git
- Identifie les limitations système
"""

import os
import sys
import subprocess
import importlib
import platform
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class EnvironmentInfo:
    """Informations complètes sur l'environnement"""
    # Système
    platform: str
    python_version: str
    os_version: str
    working_directory: str

    # Fichiers
    can_read_files: bool
    can_write_files: bool
    can_execute_scripts: bool
    accessible_directories: List[str]

    # Git
    is_git_repo: bool
    git_available: bool
    git_branch: Optional[str]
    can_commit: bool

    # Python
    installed_packages: Dict[str, str]  # package -> version
    missing_packages: List[str]

    # API Keys
    api_keys_status: Dict[str, bool]  # key_name -> present

    # Limitations
    limitations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "python_version": self.python_version,
            "os_version": self.os_version,
            "working_directory": self.working_directory,
            "can_read_files": self.can_read_files,
            "can_write_files": self.can_write_files,
            "can_execute_scripts": self.can_execute_scripts,
            "accessible_directories": self.accessible_directories,
            "is_git_repo": self.is_git_repo,
            "git_available": self.git_available,
            "git_branch": self.git_branch,
            "can_commit": self.can_commit,
            "installed_packages": self.installed_packages,
            "missing_packages": self.missing_packages,
            "api_keys_status": self.api_keys_status,
            "limitations": self.limitations
        }


class EnvironmentScanner:
    """
    Scanne l'environnement d'exécution pour déterminer
    ce que Cortex peut et ne peut pas faire
    """

    def __init__(self, cortex_root: str = "/github/mxmcorp"):
        self.cortex_root = Path(cortex_root)

    def scan_full_environment(self) -> EnvironmentInfo:
        """
        Scanne complet de l'environnement

        Returns:
            EnvironmentInfo avec tous les détails
        """
        print("🔍 Scanning environment...")

        # System info
        platform_name = platform.system()
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        os_version = platform.platform()
        working_dir = str(Path.cwd())

        # File system
        can_read = self._test_file_read()
        can_write = self._test_file_write()
        can_execute = self._test_script_execution()
        accessible_dirs = self._list_accessible_directories()

        # Git
        is_repo = self._is_git_repository()
        git_available = self._check_git_available()
        git_branch = self._get_git_branch() if is_repo else None
        can_commit = self._test_git_commit() if is_repo else False

        # Python packages
        installed = self._get_installed_packages()
        missing = self._check_missing_packages()

        # API keys
        api_keys = self._check_api_keys()

        # Limitations
        limitations = self._identify_limitations(can_write, can_execute, api_keys)

        env_info = EnvironmentInfo(
            platform=platform_name,
            python_version=python_version,
            os_version=os_version,
            working_directory=working_dir,
            can_read_files=can_read,
            can_write_files=can_write,
            can_execute_scripts=can_execute,
            accessible_directories=accessible_dirs,
            is_git_repo=is_repo,
            git_available=git_available,
            git_branch=git_branch,
            can_commit=can_commit,
            installed_packages=installed,
            missing_packages=missing,
            api_keys_status=api_keys,
            limitations=limitations
        )

        print("✓ Environment scan complete")
        return env_info

    def _test_file_read(self) -> bool:
        """Teste si on peut lire des fichiers"""
        try:
            test_file = self.cortex_root / "README.md"
            if test_file.exists():
                with open(test_file, 'r') as f:
                    f.read(100)
                return True
            return False
        except Exception:
            return False

    def _test_file_write(self) -> bool:
        """Teste si on peut écrire des fichiers"""
        try:
            test_file = self.cortex_root / "cortex" / "data" / ".test_write"
            test_file.parent.mkdir(parents=True, exist_ok=True)

            with open(test_file, 'w') as f:
                f.write("test")

            test_file.unlink()
            return True
        except Exception:
            return False

    def _test_script_execution(self) -> bool:
        """Teste si on peut exécuter des scripts"""
        try:
            result = subprocess.run(
                ["echo", "test"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _list_accessible_directories(self) -> List[str]:
        """Liste les répertoires accessibles"""
        accessible = []

        # Test répertoires importants
        important_dirs = [
            self.cortex_root,
            self.cortex_root / "cortex",
            self.cortex_root / "cortex" / "data",
            self.cortex_root / "tests",
            self.cortex_root / "docs"
        ]

        for dir_path in important_dirs:
            if dir_path.exists() and os.access(dir_path, os.R_OK):
                accessible.append(str(dir_path))

        return accessible

    def _is_git_repository(self) -> bool:
        """Vérifie si on est dans un repo Git"""
        git_dir = self.cortex_root / ".git"
        return git_dir.exists()

    def _check_git_available(self) -> bool:
        """Vérifie si git est disponible"""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_git_branch(self) -> Optional[str]:
        """Récupère la branche Git actuelle"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.cortex_root
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _test_git_commit(self) -> bool:
        """Teste si on peut faire des commits (config git OK)"""
        try:
            # Vérifier si user.name et user.email sont configurés
            result_name = subprocess.run(
                ["git", "config", "user.name"],
                capture_output=True,
                timeout=5,
                cwd=self.cortex_root
            )
            result_email = subprocess.run(
                ["git", "config", "user.email"],
                capture_output=True,
                timeout=5,
                cwd=self.cortex_root
            )

            return result_name.returncode == 0 and result_email.returncode == 0
        except Exception:
            return False

    def _get_installed_packages(self) -> Dict[str, str]:
        """Récupère les packages Python installés"""
        installed = {}

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                import json
                packages = json.loads(result.stdout)
                for pkg in packages:
                    installed[pkg["name"]] = pkg["version"]
        except Exception:
            pass

        return installed

    def _check_missing_packages(self) -> List[str]:
        """Vérifie les packages requis manquants"""
        required_packages = [
            "openai",
            "anthropic",
            "requests",
            "lxml",
            "python-dotenv"
        ]

        missing = []
        for package in required_packages:
            try:
                importlib.import_module(package.replace("-", "_"))
            except ImportError:
                missing.append(package)

        return missing

    def _check_api_keys(self) -> Dict[str, bool]:
        """Vérifie la présence des API keys"""
        keys_to_check = {
            "OPENAI_API_KEY": "OpenAI",
            "DEEPSEEK_API_KEY": "DeepSeek",
            "ANTHROPIC_API_KEY": "Anthropic"
        }

        status = {}
        for env_var, name in keys_to_check.items():
            status[name] = bool(os.getenv(env_var))

        return status

    def _identify_limitations(
        self,
        can_write: bool,
        can_execute: bool,
        api_keys: Dict[str, bool]
    ) -> List[str]:
        """Identifie les limitations de l'environnement"""
        limitations = []

        if not can_write:
            limitations.append("Cannot write files - read-only mode")

        if not can_execute:
            limitations.append("Cannot execute shell scripts")

        missing_keys = [name for name, present in api_keys.items() if not present]
        if missing_keys:
            limitations.append(f"Missing API keys: {', '.join(missing_keys)}")

        # Limitation basée sur plateforme
        if platform.system() == "Windows":
            limitations.append("Windows environment - some shell scripts may not work")

        return limitations

    def display_environment_info(self, env_info: EnvironmentInfo):
        """Affiche les infos environnement de manière lisible"""
        print(f"\n{'='*70}")
        print(f"CORTEX ENVIRONMENT INFO")
        print(f"{'='*70}\n")

        # System
        print(f"🖥️  System:")
        print(f"   Platform: {env_info.platform}")
        print(f"   Python: {env_info.python_version}")
        print(f"   OS: {env_info.os_version}")
        print(f"   Working dir: {env_info.working_directory}")

        # File system
        print(f"\n📁 File System:")
        print(f"   Read files: {'✅' if env_info.can_read_files else '❌'}")
        print(f"   Write files: {'✅' if env_info.can_write_files else '❌'}")
        print(f"   Execute scripts: {'✅' if env_info.can_execute_scripts else '❌'}")
        print(f"   Accessible dirs: {len(env_info.accessible_directories)}")

        # Git
        print(f"\n🔧 Git:")
        print(f"   Available: {'✅' if env_info.git_available else '❌'}")
        print(f"   Is repo: {'✅' if env_info.is_git_repo else '❌'}")
        if env_info.git_branch:
            print(f"   Branch: {env_info.git_branch}")
        print(f"   Can commit: {'✅' if env_info.can_commit else '❌'}")

        # Python packages
        print(f"\n🐍 Python Packages:")
        print(f"   Installed: {len(env_info.installed_packages)}")
        if env_info.missing_packages:
            print(f"   ⚠️  Missing: {', '.join(env_info.missing_packages)}")

        # API keys
        print(f"\n🔑 API Keys:")
        for key, present in env_info.api_keys_status.items():
            print(f"   {key}: {'✅' if present else '❌'}")

        # Limitations
        if env_info.limitations:
            print(f"\n⚠️  Limitations:")
            for limitation in env_info.limitations:
                print(f"   - {limitation}")

        print(f"\n{'='*70}\n")


def create_environment_scanner() -> EnvironmentScanner:
    """Factory function"""
    return EnvironmentScanner()


# Test
if __name__ == "__main__":
    print("Testing Environment Scanner...")

    scanner = EnvironmentScanner()

    # Test: Full scan
    print("\n1. Full environment scan...")
    env_info = scanner.scan_full_environment()

    # Test: Display
    print("\n2. Displaying environment info...")
    scanner.display_environment_info(env_info)

    print("\n✓ Environment Scanner works correctly!")
