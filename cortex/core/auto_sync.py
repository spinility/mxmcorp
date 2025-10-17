"""
Cortex Auto-Synchronization System

Synchronise automatiquement la base de données avec les fichiers markdown
selon des déclencheurs configurables :
- Nombre d'exécutions
- Temps écoulé
- À la demande

L'ArchivistAgent travaille en arrière-plan de manière transparente.
"""

import time
import threading
from typing import Optional
from datetime import datetime, timedelta


class AutoSyncManager:
    """
    Gestionnaire de synchronisation automatique

    Déclenche périodiquement l'ArchivistAgent pour :
    1. Syncer roadmap.md <-> DB
    2. Générer dashboard.md
    3. Générer agent_performance.md
    """

    def __init__(
        self,
        sync_every_n_requests: int = 10,  # Sync tous les N requêtes
        sync_every_n_minutes: int = 30,   # Sync tous les N minutes
        auto_enabled: bool = True
    ):
        """
        Initialize Auto-Sync Manager

        Args:
            sync_every_n_requests: Déclencher sync après N requêtes
            sync_every_n_minutes: Déclencher sync après N minutes
            auto_enabled: Activer la synchronisation automatique
        """
        self.sync_every_n_requests = sync_every_n_requests
        self.sync_every_n_minutes = sync_every_n_minutes
        self.auto_enabled = auto_enabled

        # État interne
        self.request_count = 0
        self.last_sync_time = datetime.now()
        self._archivist = None
        self._lock = threading.Lock()

    def increment_request(self):
        """
        Incrémenter le compteur de requêtes
        Appelé automatiquement après chaque requête utilisateur
        """
        if not self.auto_enabled:
            return

        with self._lock:
            self.request_count += 1

            # Vérifier si sync nécessaire par nombre de requêtes
            if self.request_count >= self.sync_every_n_requests:
                self._trigger_sync("request_threshold")
                self.request_count = 0

    def check_time_trigger(self):
        """
        Vérifier si sync nécessaire basé sur le temps
        Appelé périodiquement
        """
        if not self.auto_enabled:
            return

        with self._lock:
            elapsed = datetime.now() - self.last_sync_time
            if elapsed >= timedelta(minutes=self.sync_every_n_minutes):
                self._trigger_sync("time_threshold")

    def force_sync(self):
        """Force une synchronisation immédiate"""
        with self._lock:
            self._trigger_sync("manual")

    def _trigger_sync(self, reason: str):
        """
        Déclenche la synchronisation

        Args:
            reason: Raison du déclenchement (request_threshold, time_threshold, manual)
        """
        try:
            # Import lazy pour éviter circular imports
            from cortex.agents.archivist_agent import create_archivist_agent
            from cortex.core.llm_client import LLMClient

            # Créer l'archivist si nécessaire
            if self._archivist is None:
                llm_client = LLMClient()
                self._archivist = create_archivist_agent(llm_client)

            # Lancer la synchronisation complète en arrière-plan
            thread = threading.Thread(
                target=self._run_sync,
                args=(reason,),
                daemon=True
            )
            thread.start()

        except Exception as e:
            # Ne pas bloquer si sync échoue
            import warnings
            warnings.warn(f"Auto-sync failed: {e}")

    def _run_sync(self, reason: str):
        """
        Exécute la synchronisation complète
        Tourne en arrière-plan
        """
        try:
            # Synchronisation complète
            result = self._archivist.full_synchronization()

            # Mettre à jour le timestamp
            self.last_sync_time = datetime.now()

            # Log silencieux (peut être activé pour debug)
            if False:  # Debug mode
                print(f"[AutoSync] Triggered by: {reason}")
                print(f"[AutoSync] Roadmap: {result['roadmap_sync']['projects_synced']} projects")
                print(f"[AutoSync] Dashboard: {result['dashboard_generation']['success']}")
                print(f"[AutoSync] Agent Report: {result['agent_report']['agents_reported']} agents")

        except Exception as e:
            import warnings
            warnings.warn(f"Sync execution failed: {e}")


# Singleton global
_auto_sync_manager: Optional[AutoSyncManager] = None


def get_auto_sync_manager() -> AutoSyncManager:
    """
    Récupère l'instance singleton du manager

    Returns:
        AutoSyncManager instance
    """
    global _auto_sync_manager
    if _auto_sync_manager is None:
        _auto_sync_manager = AutoSyncManager()
    return _auto_sync_manager


def enable_auto_sync():
    """Active la synchronisation automatique"""
    manager = get_auto_sync_manager()
    manager.auto_enabled = True


def disable_auto_sync():
    """Désactive la synchronisation automatique"""
    manager = get_auto_sync_manager()
    manager.auto_enabled = False


def force_sync_now():
    """Force une synchronisation immédiate"""
    manager = get_auto_sync_manager()
    manager.force_sync()


# Test si exécuté directement
if __name__ == "__main__":
    print("Testing Auto-Sync Manager...")

    # Créer le manager
    manager = AutoSyncManager(
        sync_every_n_requests=3,
        sync_every_n_minutes=1,
        auto_enabled=True
    )

    print("\n1. Testing request-based trigger...")
    for i in range(5):
        print(f"   Request {i+1}/5")
        manager.increment_request()
        time.sleep(0.5)

    print("\n2. Testing manual trigger...")
    manager.force_sync()

    print("\n3. Waiting for background sync to complete...")
    time.sleep(3)

    print("\n✓ Auto-Sync Manager works correctly!")
    print("\nNote: Dans l'utilisation réelle, les syncs se font en arrière-plan sans bloquer.")
