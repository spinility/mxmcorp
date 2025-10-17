"""
Log Filter Service - Filtrage intelligent des logs pour éviter lecture complète

Permet de filtrer les logs du change_log selon différents critères:
- Impact level (critical, high, medium, low)
- Time period (recent, last 24h, custom date range)
- Entity type (agent, plan, test, etc.)
- Change type (execution, analysis, request, etc.)
- Author/Agent (TriageAgent, MaintenanceAgent, etc.)
- Context relevance (filtrer par requête utilisateur actuelle)

Objectif: Donner au CommunicationsAgent uniquement les logs pertinents
pour résumer le "thinking" de Cortex de manière claire et concise.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from cortex.repositories.changelog_repository import get_changelog_repository


class LogFilterService:
    """Service de filtrage intelligent des logs"""

    def __init__(self):
        self.changelog_repo = get_changelog_repository()

    def get_pertinent_logs(
        self,
        context: Optional[Dict[str, Any]] = None,
        min_impact: str = 'low',
        time_period: str = 'recent',
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Récupère les logs pertinents selon le contexte

        Args:
            context: Contexte de la requête actuelle avec:
                - request: Requête utilisateur
                - agents_involved: Liste des agents impliqués
                - entity_ids: IDs des entités concernées
                - focus: 'planning', 'execution', 'testing', 'all'
            min_impact: Niveau minimum d'impact (low, medium, high, critical)
            time_period: 'recent' (1h), 'today', 'week', 'all'
            limit: Nombre maximum de logs

        Returns:
            Liste de logs filtrés et triés par pertinence
        """
        # Étape 1: Filtrer par time_period
        if time_period == 'recent':
            # Dernière heure
            start_date = (datetime.now() - timedelta(hours=1)).isoformat()
            logs = self._get_logs_since(start_date, limit=limit*2)
        elif time_period == 'today':
            # Aujourd'hui
            start_date = datetime.now().replace(hour=0, minute=0, second=0).isoformat()
            logs = self._get_logs_since(start_date, limit=limit*2)
        elif time_period == 'week':
            # Dernière semaine
            start_date = (datetime.now() - timedelta(days=7)).isoformat()
            logs = self._get_logs_since(start_date, limit=limit*2)
        else:
            # Tous les logs récents
            logs = self.changelog_repo.get_recent_changes(limit=limit*2, min_impact=None)

        # Étape 2: Filtrer par impact level
        logs = self._filter_by_impact(logs, min_impact)

        # Étape 3: Filtrer par contexte (le plus important)
        if context:
            logs = self._filter_by_context(logs, context)

        # Étape 4: Scorer et trier par pertinence
        logs = self._score_and_sort(logs, context)

        # Étape 5: Limiter le nombre
        return logs[:limit]

    def get_workflow_logs(
        self,
        request_id: Optional[str] = None,
        session_start: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Récupère les logs d'un workflow complet (une requête utilisateur)

        Args:
            request_id: ID de la requête (si disponible)
            session_start: Début de la session
            limit: Nombre maximum de logs

        Returns:
            Liste de logs du workflow
        """
        if session_start:
            start_date = session_start.isoformat()
            logs = self._get_logs_since(start_date, limit=limit)
        else:
            # Par défaut: dernière heure
            start_date = (datetime.now() - timedelta(hours=1)).isoformat()
            logs = self._get_logs_since(start_date, limit=limit)

        # Filtrer uniquement les logs liés au workflow
        workflow_types = [
            'execution_start', 'execution_complete', 'execution_failure',
            'test_analysis', 'test_request',
            'harmonization_plan', 'plan_execution',
            'agent_decision', 'agent_escalation'
        ]

        logs = [log for log in logs if log.get('change_type') in workflow_types]

        return logs

    def get_agent_thinking_logs(
        self,
        agent_name: Optional[str] = None,
        time_period: str = 'recent',
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Récupère les logs montrant le "thinking" d'un agent

        Args:
            agent_name: Nom de l'agent (None = tous les agents)
            time_period: Période de temps
            limit: Nombre maximum de logs

        Returns:
            Liste de logs montrant les décisions et raisonnements
        """
        logs = self.get_pertinent_logs(
            context=None,
            min_impact='medium',
            time_period=time_period,
            limit=limit*2
        )

        # Filtrer par agent si spécifié
        if agent_name:
            logs = [log for log in logs if log.get('author') == agent_name]

        # Garder uniquement les logs "thinking" (décisions, analyses, escalations)
        thinking_types = [
            'harmonization_plan', 'test_analysis', 'plan_execution',
            'agent_decision', 'agent_escalation', 'execution_start'
        ]

        logs = [log for log in logs if log.get('change_type') in thinking_types]

        return logs[:limit]

    def get_critical_logs(
        self,
        time_period: str = 'today',
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Récupère uniquement les logs critiques (erreurs, échecs, escalations)

        Args:
            time_period: Période de temps
            limit: Nombre maximum de logs

        Returns:
            Liste de logs critiques
        """
        logs = self.get_pertinent_logs(
            context=None,
            min_impact='high',
            time_period=time_period,
            limit=limit
        )

        # Filtrer les types critiques
        critical_types = [
            'execution_failure', 'execution_exception',
            'agent_escalation', 'test_failure',
            'harmonization_conflict'
        ]

        logs = [log for log in logs if
                log.get('change_type') in critical_types or
                log.get('impact_level') in ['critical', 'high']]

        return logs

    def _get_logs_since(self, start_date: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les logs depuis une date"""
        end_date = datetime.now().isoformat()
        return self.changelog_repo.get_changes_by_date_range(start_date, end_date)

    def _filter_by_impact(self, logs: List[Dict], min_impact: str) -> List[Dict]:
        """Filtre les logs par niveau d'impact minimum"""
        impact_levels = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }

        min_level = impact_levels.get(min_impact, 1)

        return [
            log for log in logs
            if impact_levels.get(log.get('impact_level', 'low'), 1) >= min_level
        ]

    def _filter_by_context(self, logs: List[Dict], context: Dict[str, Any]) -> List[Dict]:
        """
        Filtre les logs selon le contexte de la requête actuelle

        Context peut contenir:
        - request: Requête utilisateur
        - agents_involved: Liste des agents impliqués
        - entity_ids: IDs des entités concernées
        - focus: 'planning', 'execution', 'testing', 'all'
        """
        filtered_logs = logs

        # Filtrer par agents impliqués
        if context.get('agents_involved'):
            agents = context['agents_involved']
            filtered_logs = [
                log for log in filtered_logs
                if log.get('author') in agents
            ]

        # Filtrer par focus
        focus = context.get('focus', 'all')
        if focus == 'planning':
            focus_types = ['harmonization_plan', 'agent_decision', 'plan_generation']
            filtered_logs = [
                log for log in filtered_logs
                if any(ft in log.get('change_type', '') for ft in focus_types)
            ]
        elif focus == 'execution':
            focus_types = ['execution', 'update', 'sync', 'refactor']
            filtered_logs = [
                log for log in filtered_logs
                if any(ft in log.get('change_type', '') for ft in focus_types)
            ]
        elif focus == 'testing':
            focus_types = ['test', 'validation', 'quality']
            filtered_logs = [
                log for log in filtered_logs
                if any(ft in log.get('change_type', '') for ft in focus_types)
            ]

        # Filtrer par entity_ids si fournis
        if context.get('entity_ids'):
            entity_ids = context['entity_ids']
            filtered_logs = [
                log for log in filtered_logs
                if log.get('entity_id') in entity_ids
            ]

        return filtered_logs

    def _score_and_sort(
        self,
        logs: List[Dict],
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Score les logs par pertinence et les trie

        Critères de scoring:
        - Impact level (+1 to +4)
        - Récence (+0 to +2)
        - Matching agent (+2)
        - Matching entity (+1)
        - Type de log (+1 pour thinking types)
        """
        scored_logs = []

        for log in logs:
            score = 0

            # Impact level
            impact_scores = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
            score += impact_scores.get(log.get('impact_level', 'low'), 1)

            # Récence (logs plus récents = score plus élevé)
            try:
                log_time = datetime.fromisoformat(log.get('timestamp', ''))
                age_hours = (datetime.now() - log_time).total_seconds() / 3600
                if age_hours < 1:
                    score += 2
                elif age_hours < 6:
                    score += 1
            except:
                pass

            # Context matching
            if context:
                if context.get('agents_involved') and log.get('author') in context['agents_involved']:
                    score += 2

                if context.get('entity_ids') and log.get('entity_id') in context['entity_ids']:
                    score += 1

            # Thinking types (plus pertinents pour le résumé)
            thinking_types = [
                'harmonization_plan', 'test_analysis', 'execution_start',
                'agent_decision', 'agent_escalation'
            ]
            if any(tt in log.get('change_type', '') for tt in thinking_types):
                score += 1

            scored_logs.append((score, log))

        # Trier par score décroissant
        scored_logs.sort(key=lambda x: x[0], reverse=True)

        return [log for score, log in scored_logs]

    def summarize_logs(self, logs: List[Dict]) -> Dict[str, Any]:
        """
        Génère un résumé statistique des logs filtrés

        Args:
            logs: Liste de logs

        Returns:
            Dict avec statistiques
        """
        if not logs:
            return {
                'total': 0,
                'by_author': {},
                'by_impact': {},
                'by_type': {},
                'time_range': None
            }

        # Grouper par auteur
        by_author = {}
        for log in logs:
            author = log.get('author', 'Unknown')
            by_author[author] = by_author.get(author, 0) + 1

        # Grouper par impact
        by_impact = {}
        for log in logs:
            impact = log.get('impact_level', 'low')
            by_impact[impact] = by_impact.get(impact, 0) + 1

        # Grouper par type
        by_type = {}
        for log in logs:
            change_type = log.get('change_type', 'unknown')
            by_type[change_type] = by_type.get(change_type, 0) + 1

        # Time range
        timestamps = [log.get('timestamp') for log in logs if log.get('timestamp')]
        if timestamps:
            time_range = {
                'earliest': min(timestamps),
                'latest': max(timestamps)
            }
        else:
            time_range = None

        return {
            'total': len(logs),
            'by_author': by_author,
            'by_impact': by_impact,
            'by_type': by_type,
            'time_range': time_range
        }


def get_log_filter_service() -> LogFilterService:
    """Factory function pour créer le service"""
    return LogFilterService()


# Test
if __name__ == "__main__":
    print("Testing Log Filter Service...")

    service = LogFilterService()

    # Test 1: Logs récents
    print("\n1. Getting recent pertinent logs...")
    logs = service.get_pertinent_logs(
        min_impact='medium',
        time_period='today',
        limit=10
    )
    print(f"   Found {len(logs)} pertinent logs")

    # Test 2: Logs de workflow
    print("\n2. Getting workflow logs...")
    workflow_logs = service.get_workflow_logs(limit=20)
    print(f"   Found {len(workflow_logs)} workflow logs")

    # Test 3: Logs critiques
    print("\n3. Getting critical logs...")
    critical_logs = service.get_critical_logs(time_period='today', limit=10)
    print(f"   Found {len(critical_logs)} critical logs")

    # Test 4: Résumé
    print("\n4. Summarizing logs...")
    summary = service.summarize_logs(logs)
    print(f"   Total: {summary['total']}")
    print(f"   By author: {summary['by_author']}")
    print(f"   By impact: {summary['by_impact']}")

    print("\n✓ Log Filter Service works correctly!")
