"""
Agent Memory System - Système de mémoire interne pour agents

Chaque agent a sa propre mémoire persistante dans:
cortex/departments/{department}/agents/{agent_name}/memory.json

La mémoire stocke:
- Historique d'exécutions
- Patterns détectés
- Décisions antérieures
- Métriques de performance
- État interne

Ce système permet aux agents d'apprendre et d'évoluer.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from threading import Lock


class AgentMemory:
    """Système de mémoire persistante pour un agent"""

    def __init__(self, department: str, agent_name: str):
        """
        Initialize agent memory

        Args:
            department: Nom du département (intelligence, maintenance, etc.)
            agent_name: Nom de l'agent (git_watcher, maintenance, etc.)
        """
        self.department = department
        self.agent_name = agent_name
        self.memory_path = Path(
            f'cortex/departments/{department}/agents/{agent_name}/memory.json'
        )
        self._lock = Lock()

        # Ensure memory file exists
        if not self.memory_path.exists():
            self._initialize_memory()

    def _initialize_memory(self):
        """Initialise le fichier mémoire avec le schéma de base"""
        memory_data = {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "execution_history": [],
            "learned_patterns": {},
            "performance_metrics": {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "avg_execution_time": 0.0,
                "total_cost": 0.0
            },
            "state": {},
            "notes": []
        }

        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_path, 'w') as f:
            json.dump(memory_data, f, indent=2)

    def load(self) -> Dict[str, Any]:
        """
        Charge la mémoire depuis le fichier

        Returns:
            Dict contenant toute la mémoire de l'agent
        """
        with self._lock:
            try:
                with open(self.memory_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load memory for {self.agent_name}: {e}")
                return self._get_empty_memory()

    def save(self, memory_data: Dict[str, Any]):
        """
        Sauvegarde la mémoire dans le fichier

        Args:
            memory_data: Données de mémoire à sauvegarder
        """
        with self._lock:
            try:
                memory_data['last_updated'] = datetime.now().isoformat()
                with open(self.memory_path, 'w') as f:
                    json.dump(memory_data, f, indent=2)
            except Exception as e:
                print(f"Error: Could not save memory for {self.agent_name}: {e}")

    def record_execution(
        self,
        request: str,
        result: Dict[str, Any],
        duration: float,
        cost: float = 0.0
    ):
        """
        Enregistre une exécution dans l'historique

        Args:
            request: Requête traitée
            result: Résultat de l'exécution
            duration: Durée en secondes
            cost: Coût LLM si applicable
        """
        memory = self.load()

        execution_record = {
            'timestamp': datetime.now().isoformat(),
            'request': request[:200],  # Limiter la taille
            'success': result.get('success', False),
            'duration': duration,
            'cost': cost,
            'result_summary': str(result)[:500]
        }

        memory['execution_history'].append(execution_record)

        # Limiter l'historique à 100 dernières exécutions
        if len(memory['execution_history']) > 100:
            memory['execution_history'] = memory['execution_history'][-100:]

        # Mettre à jour métriques
        metrics = memory['performance_metrics']
        metrics['total_executions'] += 1

        if result.get('success', False):
            metrics['successful_executions'] += 1
        else:
            metrics['failed_executions'] += 1

        # Moyenne mobile de la durée
        n = metrics['total_executions']
        old_avg = metrics['avg_execution_time']
        metrics['avg_execution_time'] = (old_avg * (n - 1) + duration) / n

        metrics['total_cost'] += cost

        self.save(memory)

    def add_pattern(self, pattern_name: str, pattern_data: Dict[str, Any]):
        """
        Enregistre un pattern détecté

        Args:
            pattern_name: Nom du pattern (ex: "frequent_error_type")
            pattern_data: Données du pattern détecté
        """
        memory = self.load()

        if pattern_name not in memory['learned_patterns']:
            memory['learned_patterns'][pattern_name] = {
                'first_detected': datetime.now().isoformat(),
                'occurrences': 0,
                'data': []
            }

        pattern = memory['learned_patterns'][pattern_name]
        pattern['occurrences'] += 1
        pattern['last_detected'] = datetime.now().isoformat()
        pattern['data'].append({
            'timestamp': datetime.now().isoformat(),
            'data': pattern_data
        })

        # Limiter les données à 50 occurrences
        if len(pattern['data']) > 50:
            pattern['data'] = pattern['data'][-50:]

        self.save(memory)

    def get_pattern(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un pattern enregistré

        Args:
            pattern_name: Nom du pattern

        Returns:
            Données du pattern ou None
        """
        memory = self.load()
        return memory['learned_patterns'].get(pattern_name)

    def get_patterns(self) -> Dict[str, Any]:
        """
        Récupère tous les patterns enregistrés

        Returns:
            Dict de tous les patterns
        """
        memory = self.load()
        return memory['learned_patterns']

    def update_state(self, state_updates: Dict[str, Any]):
        """
        Met à jour l'état interne de l'agent

        Args:
            state_updates: Dict de clés/valeurs à mettre à jour
        """
        memory = self.load()
        memory['state'].update(state_updates)
        self.save(memory)

    def get_state(self, key: Optional[str] = None) -> Any:
        """
        Récupère l'état interne

        Args:
            key: Clé spécifique (None = tout l'état)

        Returns:
            Valeur de l'état ou tout l'état
        """
        memory = self.load()
        if key:
            return memory['state'].get(key)
        return memory['state']

    def add_note(self, note: str):
        """
        Ajoute une note à la mémoire

        Args:
            note: Note textuelle
        """
        memory = self.load()
        memory['notes'].append({
            'timestamp': datetime.now().isoformat(),
            'note': note
        })

        # Limiter à 50 notes
        if len(memory['notes']) > 50:
            memory['notes'] = memory['notes'][-50:]

        self.save(memory)

    def get_recent_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère les N dernières exécutions

        Args:
            limit: Nombre d'exécutions à retourner

        Returns:
            Liste des exécutions récentes
        """
        memory = self.load()
        return memory['execution_history'][-limit:]

    def get_metrics(self) -> Dict[str, Any]:
        """
        Récupère les métriques de performance

        Returns:
            Dict des métriques
        """
        memory = self.load()
        return memory['performance_metrics']

    def clear_history(self):
        """Efface l'historique d'exécutions (garde patterns et état)"""
        memory = self.load()
        memory['execution_history'] = []
        self.save(memory)

    def reset(self):
        """Reset complet de la mémoire"""
        self._initialize_memory()

    def _get_empty_memory(self) -> Dict[str, Any]:
        """Retourne une mémoire vide"""
        return {
            "version": "1.0.0",
            "last_updated": None,
            "execution_history": [],
            "learned_patterns": {},
            "performance_metrics": {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "avg_execution_time": 0.0,
                "total_cost": 0.0
            },
            "state": {},
            "notes": []
        }

    def __repr__(self):
        metrics = self.get_metrics()
        return f"AgentMemory({self.department}/{self.agent_name}, executions={metrics['total_executions']})"


def get_agent_memory(department: str, agent_name: str) -> AgentMemory:
    """
    Factory function pour récupérer la mémoire d'un agent

    Args:
        department: Nom du département
        agent_name: Nom de l'agent

    Returns:
        Instance AgentMemory
    """
    return AgentMemory(department, agent_name)


# Test
if __name__ == '__main__':
    print("Testing Agent Memory System...\n")

    # Test 1: Créer une mémoire
    print("1. Creating memory for maintenance/maintenance agent...")
    memory = get_agent_memory('maintenance', 'maintenance')
    print(f"   {memory}")

    # Test 2: Enregistrer une exécution
    print("\n2. Recording execution...")
    memory.record_execution(
        request="Execute harmonization plan",
        result={'success': True, 'actions_executed': 5},
        duration=2.5,
        cost=0.01
    )
    print(f"   ✓ Execution recorded")

    # Test 3: Ajouter un pattern
    print("\n3. Adding learned pattern...")
    memory.add_pattern(
        'frequent_file_type',
        {'file_type': '.py', 'frequency': 'high'}
    )
    print(f"   ✓ Pattern added")

    # Test 4: Mettre à jour l'état
    print("\n4. Updating state...")
    memory.update_state({'last_plan_id': 'ADR-123', 'active': True})
    print(f"   ✓ State updated: {memory.get_state()}")

    # Test 5: Récupérer métriques
    print("\n5. Getting metrics...")
    metrics = memory.get_metrics()
    print(f"   Total executions: {metrics['total_executions']}")
    print(f"   Success rate: {metrics['successful_executions']/metrics['total_executions']*100:.1f}%")
    print(f"   Avg duration: {metrics['avg_execution_time']:.2f}s")
    print(f"   Total cost: ${metrics['total_cost']:.4f}")

    print("\n✓ Agent Memory System works correctly!")
