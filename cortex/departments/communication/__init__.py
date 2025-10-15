"""
Département de COMMUNICATION

Rôle: Rapports CEO et communication interne/externe

Agents:
- CEOReporter (EXÉCUTANT) - Génère rapports quotidiens/hebdomadaires
- AlertManager (EXÉCUTANT) - Gère alertes temps réel
- ReportAnalyzer (EXPERT) - Analyse tendances (TODO)
- CommunicationDirector (DIRECTEUR) - Supervise communication (TODO)

Fonctionnalités:
- Rapports quotidiens automatiques
- Rapports hebdomadaires avec métriques
- Alertes temps réel (critical/warning/info/success)
- Archive complète de tous les rapports
"""

from cortex.departments.communication.ceo_reporter import CEOReporter

__all__ = [
    'CEOReporter'
]
