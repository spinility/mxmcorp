"""
Quick Actions Agent - Opérations atomiques ultra-simples

ROLE: EXECUTOR (Exécution rapide) - Niveau 1.5 de la hiérarchie
TIER: NANO avec function calling

Responsabilités:
- Exécuter des opérations ATOMIQUES (1 seul outil maximum)
- Outils READ-ONLY ou vérifications (pas de modifications système)
- Réponse rapide et économique (<1s latence)
- Coût minimal (<$0.0001 par requête)

Outils autorisés:
- file_exists: Vérifier si fichier/dossier existe
- list_files: Lister fichiers d'un répertoire
- get_current_time: Obtenir heure/date actuelle
- read_env_var: Lire variable d'environnement
- file_stats: Obtenir stats d'un fichier (taille, date modif)

Prompt de base:
"Tu es un agent d'actions rapides. Tu as accès à des outils SIMPLES
pour des vérifications rapides. Utilise l'outil approprié et réponds
de manière CONCISE (1-2 phrases max)."

Design:
- Aucune analyse complexe
- Aucun contexte historique nécessaire
- Aucune escalade (si trop complexe, retourne error)
- Réponse directe basée sur résultat outil
"""

from typing import Dict, Any, Optional, List
import time
from datetime import datetime
from cortex.core.llm_client import LLMClient, ModelTier
from cortex.tools.standard_tool import StandardTool
from cortex.tools.tool_executor import ToolExecutor
from cortex.core.agent_memory import get_agent_memory


class QuickActionsAgent:
    """Agent pour actions atomiques rapides"""

    # Outils autorisés (READ-ONLY uniquement)
    ALLOWED_TOOLS = {
        'file_exists',
        'list_files',
        'get_current_time',
        'read_env_var',
        'file_stats',
        'search_files',  # Recherche lecture seule
    }

    def __init__(self, llm_client: LLMClient, all_tools: List[StandardTool]):
        """
        Initialize Quick Actions Agent

        Args:
            llm_client: Client LLM pour exécution
            all_tools: Liste complète des outils (on filtre pour garder seulement simples)
        """
        self.llm_client = llm_client
        self.tool_executor = ToolExecutor(llm_client)

        # Filtrer pour garder seulement les outils autorisés
        self.simple_tools = [
            tool for tool in all_tools
            if tool.name in self.ALLOWED_TOOLS
        ]

        # Enregistrer les outils
        for tool in self.simple_tools:
            self.tool_executor.register_tool(tool)

        # Stats
        self.executions = 0
        self.total_cost = 0.0

        # Memory
        self.memory = get_agent_memory('execution', 'quick_actions')

    def can_handle(self, request: str) -> bool:
        """
        Vérifie si cette requête est assez simple pour Quick Actions

        Critères:
        - Requête courte (<50 mots)
        - Mots-clés de vérification (existe, liste, heure, etc.)
        - Pas de mots-clés complexes (analyse, génère, crée, modifie)

        Returns:
            True si peut gérer, False sinon
        """
        request_lower = request.lower()
        word_count = len(request.split())

        # Trop long = complexe
        if word_count > 50:
            return False

        # Mots-clés simples (vérification)
        simple_keywords = [
            'existe', 'exists', 'fichier', 'file',
            'liste', 'list', 'ls', 'dir',
            'heure', 'time', 'date', 'now',
            'check', 'vérifie', 'verify',
            'cherche', 'find', 'search'
        ]

        # Mots-clés complexes (exclusion)
        complex_keywords = [
            'analyse', 'analyze', 'génère', 'generate',
            'crée', 'create', 'modifie', 'modify', 'edit',
            'supprime', 'delete', 'remove',
            'commit', 'push', 'pull',
            'explique', 'explain', 'pourquoi', 'why'
        ]

        has_simple = any(kw in request_lower for kw in simple_keywords)
        has_complex = any(kw in request_lower for kw in complex_keywords)

        return has_simple and not has_complex

    def execute(self, request: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Exécute une action rapide

        Args:
            request: Requête utilisateur
            context: Contexte optionnel (ignoré pour quick actions)

        Returns:
            Dict avec success, content, cost, tool_used
        """
        start_time = time.time()
        self.executions += 1

        # Vérifier si on peut gérer
        if not self.can_handle(request):
            duration = time.time() - start_time
            result = {
                'success': False,
                'error': 'Request too complex for Quick Actions Agent',
                'should_escalate': True,
                'cost': 0.0
            }

            # Record rejection to memory
            self.memory.record_execution(
                request=f"Quick action rejected: {request[:100]}",
                result=result,
                duration=duration,
                cost=0.0
            )

            return result

        # Prompt minimaliste pour NANO
        system_prompt = """Tu es un agent d'actions RAPIDES. Règles:

1. Utilise UN SEUL outil (pas plus)
2. Réponds en 1-2 phrases MAXIMUM
3. Sois DIRECT (pas d'intro, pas de conclusion)
4. Format: "[Résultat] [1 phrase explicative]"

Exemples:
User: "fichier config.json existe?"
Assistant: [file_exists] → "Non, le fichier config.json n'existe pas."

User: "quelle heure?"
Assistant: [get_current_time] → "Il est 14:32:15."

User: "liste fichiers ici"
Assistant: [list_files] → "3 fichiers: main.py, test.py, README.md"

IMPORTANT: Si requête trop complexe, réponds "ESCALATE: [raison]"."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request}
        ]

        try:
            # Exécuter avec NANO + outils simples
            response = self.tool_executor.execute_with_tools(
                messages=messages,
                tier=ModelTier.NANO,
                tools=self.simple_tools,
                max_tokens=200,  # Réponse courte
                temperature=0.3,  # Déterministe
                verbose=False
            )

            self.total_cost += response.cost

            # Vérifier si demande escalade
            if response.content and 'ESCALATE:' in response.content:
                duration = time.time() - start_time
                result = {
                    'success': False,
                    'error': response.content.split('ESCALATE:')[1].strip(),
                    'should_escalate': True,
                    'cost': response.cost
                }

                # Record escalation to memory
                self.memory.record_execution(
                    request=f"Quick action escalated: {request[:100]}",
                    result=result,
                    duration=duration,
                    cost=response.cost
                )

                return result

            # Extraire outil utilisé
            tool_used = None
            if response.tool_calls and len(response.tool_calls) > 0:
                tool_used = response.tool_calls[0].get('name')

            result = {
                'success': True,
                'content': response.content,
                'tool_used': tool_used,
                'tool_calls': response.tool_calls,
                'cost': response.cost,
                'tokens_input': response.tokens_input,
                'tokens_output': response.tokens_output,
                'model': response.model
            }

            # Record success to memory
            duration = time.time() - start_time
            self.memory.record_execution(
                request=f"Quick action: {request[:100]}",
                result=result,
                duration=duration,
                cost=response.cost
            )

            # Update state
            self.memory.update_state({
                'last_execution_timestamp': datetime.now().isoformat(),
                'last_tool_used': tool_used,
                'total_executions': self.executions,
                'total_cost': self.total_cost
            })

            # Detect patterns in tool usage
            if tool_used:
                self.memory.add_pattern(
                    f'tool_used_{tool_used}',
                    {
                        'tool': tool_used,
                        'request_type': request[:50],
                        'success': True
                    }
                )

            return result

        except Exception as e:
            duration = time.time() - start_time
            result = {
                'success': False,
                'error': f'Quick action failed: {str(e)}',
                'should_escalate': True,
                'cost': 0.0
            }

            # Record failure to memory
            self.memory.record_execution(
                request=f"Quick action failed: {request[:100]}",
                result=result,
                duration=duration,
                cost=0.0
            )

            return result

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques"""
        return {
            'agent': 'QuickActionsAgent',
            'executions': self.executions,
            'total_cost': self.total_cost,
            'avg_cost': self.total_cost / self.executions if self.executions > 0 else 0.0,
            'tools_available': len(self.simple_tools)
        }


def create_quick_actions_agent(llm_client: LLMClient, all_tools: List[StandardTool]) -> QuickActionsAgent:
    """Factory function pour créer QuickActionsAgent"""
    return QuickActionsAgent(llm_client, all_tools)
