"""
Smart Router Agent - Route intelligemment les requêtes vers le bon département

Détecte automatiquement:
- Web scraping / XPath → Intelligence Department (StealthWebCrawler)
- Git operations → Maintenance Department (GitDiffProcessor)
- Optimizations → Optimization Department (PatternDetector)
- Communications → Communication Department (CEOAgent, Alerts)
- Unknown capabilities → Tooler Agent (research)

Évite de bloquer le système en routant directement vers les départements appropriés
plutôt que d'appeler le Tooler pour des capacités déjà existantes.
"""

from typing import Dict, Any, Optional, List
from cortex.core.llm_client import LLMClient, ModelTier


class SmartRouterAgent:
    """Agent responsable du routing intelligent vers les départements"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize Smart Router Agent

        Args:
            llm_client: Optional LLM client for complex routing decisions
        """
        self.llm_client = llm_client

        # Départements connus et leurs capacités
        self.departments = {
            "intelligence": {
                "keywords": ["web", "scrape", "xpath", "url", "website", "html", "dom", "browser", "page", "extract"],
                "description": "Web scraping, XPath extraction, dynamic content",
                "agents": ["StealthWebCrawler", "XPathSourceRegistry"],
                "confidence_threshold": 0.1  # Bas seuil car keywords très spécifiques
            },
            "maintenance": {
                "keywords": ["git", "diff", "commit", "branch", "repository", "roadmap", "context", "dependency"],
                "description": "Git operations, roadmap management, context updates",
                "agents": ["GitDiffProcessor", "RoadmapManager", "ContextUpdater"],
                "confidence_threshold": 0.1  # Bas seuil car keywords très spécifiques
            },
            "optimization": {
                "keywords": ["pattern", "learn", "improve", "optimize", "evolve", "analyze", "history"],
                "description": "Pattern detection, auto-evolution, learning",
                "agents": ["PatternDetector", "ToolEvolver", "AgentEvolver"],
                "confidence_threshold": 0.1
            },
            "communication": {
                "keywords": ["report", "alert", "notify", "ceo", "summary", "message"],
                "description": "Reports, alerts, notifications",
                "agents": ["CEOAgent", "AlertSystem"],
                "confidence_threshold": 0.1
            }
        }

    def route_request(self, user_request: str, available_tools: List[str]) -> Dict[str, Any]:
        """
        Route une requête vers le bon département ou vers le Tooler

        Args:
            user_request: Requête utilisateur
            available_tools: Liste des outils déjà disponibles

        Returns:
            Dict avec routing decision:
            {
                "route_to": "department_name" or "tooler" or "executor",
                "confidence": float,
                "department": str (if route_to == "department"),
                "agent_suggestion": str (specific agent to use),
                "reason": str
            }
        """
        request_lower = user_request.lower()

        # Step 1: Détection rapide par keywords (règles heuristiques)
        best_match = None
        best_score = 0.0

        for dept_name, dept_info in self.departments.items():
            # Compter combien de keywords matchent
            matches = sum(1 for keyword in dept_info["keywords"] if keyword in request_lower)
            score = matches / len(dept_info["keywords"])

            if score > best_score and score >= dept_info["confidence_threshold"]:
                best_score = score
                best_match = dept_name

        # Step 2: Si match clair → Router vers département
        # Seuil abaissé à 0.1 (10%) car même 1-2 keywords suffisent pour identifier le département
        if best_match and best_score > 0:
            return {
                "route_to": "department",
                "confidence": min(best_score * 2, 1.0),  # Boost confidence
                "department": best_match,
                "agent_suggestion": self.departments[best_match]["agents"][0],
                "reason": f"Detected {best_match} department keywords (score: {best_score:.2f})"
            }

        # Step 3: Si pas de match clair → Vérifier si outil existe
        # (laisser l'executor gérer avec tools disponibles)
        if any(tool_name in request_lower for tool_name in available_tools):
            return {
                "route_to": "executor",
                "confidence": 0.8,
                "department": None,
                "agent_suggestion": None,
                "reason": "Tool already available in executor"
            }

        # Step 4: Aucun match → Router vers Tooler pour recherche
        return {
            "route_to": "tooler",
            "confidence": 0.5,
            "department": None,
            "agent_suggestion": None,
            "reason": "No department match - requires tool research"
        }

    def get_department_info(self, department_name: str) -> Dict[str, Any]:
        """
        Récupère les informations sur un département

        Args:
            department_name: Nom du département

        Returns:
            Dict avec infos du département
        """
        return self.departments.get(department_name, {})

    def suggest_agent_for_task(self, department: str, task_description: str) -> str:
        """
        Suggère l'agent le plus approprié dans un département pour une tâche

        Args:
            department: Nom du département
            task_description: Description de la tâche

        Returns:
            Nom de l'agent suggéré
        """
        dept_info = self.departments.get(department)
        if not dept_info:
            return "Unknown"

        # Pour l'instant, retourner le premier agent (le plus générique)
        # Dans le futur, on pourrait utiliser LLM pour choisir plus finement
        return dept_info["agents"][0]

    def get_all_departments(self) -> Dict[str, Dict[str, Any]]:
        """Retourne tous les départements et leurs capacités"""
        return self.departments


def create_smart_router_agent(llm_client: Optional[LLMClient] = None) -> SmartRouterAgent:
    """Factory function to create a Smart Router Agent"""
    return SmartRouterAgent(llm_client)
