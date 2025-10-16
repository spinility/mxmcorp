"""
Tool Filter - Réduit les coûts en filtrant les tools pertinents

Objectif: Envoyer seulement les tools nécessaires au LLM au lieu de tous
Économie: ~2000 tokens par requête (passage de 2752 tokens à ~500 tokens)
"""

from typing import List, Set
from cortex.tools.standard_tool import StandardTool


class ToolFilter:
    """Filtre intelligemment les tools à envoyer au LLM"""

    def __init__(self):
        # Mots-clés pour chaque catégorie
        self.category_keywords = {
            "file": ["file", "create", "read", "write", "delete", "list", "directory", "folder", "save", "load"],
            "web": ["web", "search", "fetch", "url", "http", "website", "internet", "online", "weather"],
            "git": ["git", "commit", "push", "pull", "branch", "merge", "clone", "repository", "repo"],
            "pip": ["pip", "install", "uninstall", "package", "library", "module", "dependency"],
            "scraping": ["scrape", "xpath", "extract", "crawl", "parse", "html", "web page", "source"]
        }

    def filter_tools(self, user_request: str, all_tools: List[StandardTool]) -> List[StandardTool]:
        """
        Filtre les tools pertinents pour une requête

        Args:
            user_request: Requête de l'utilisateur
            all_tools: Tous les tools disponibles

        Returns:
            Liste réduite de tools pertinents
        """
        request_lower = user_request.lower()

        # Détecter les catégories nécessaires
        needed_categories = self._detect_categories(request_lower)

        # Si aucune catégorie détectée, inclure les basiques (file + general)
        if not needed_categories:
            needed_categories = {"file"}

        # Filtrer les tools
        filtered = []
        seen_names = set()  # Éviter les doublons

        for tool in all_tools:
            # Skip duplicates
            if tool.name in seen_names:
                continue

            # Check if tool belongs to needed category
            if self._tool_matches_categories(tool, needed_categories):
                filtered.append(tool)
                seen_names.add(tool.name)

        return filtered

    def _detect_categories(self, request_lower: str) -> Set[str]:
        """Détecte les catégories nécessaires dans la requête"""
        categories = set()

        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in request_lower:
                    categories.add(category)
                    break

        return categories

    def _tool_matches_categories(self, tool: StandardTool, categories: Set[str]) -> bool:
        """Vérifie si un tool appartient aux catégories nécessaires"""
        tool_name_lower = tool.name.lower()
        tool_desc_lower = tool.description.lower()
        tool_category = getattr(tool, 'category', '')

        for category in categories:
            keywords = self.category_keywords[category]

            # Check in tool category attribute
            if tool_category == category:
                return True

            # Check in tool name and description
            for keyword in keywords:
                if keyword in tool_name_lower or keyword in tool_desc_lower:
                    return True

        return False


# Test du filtre
if __name__ == "__main__":
    from cortex.tools.builtin_tools import get_all_builtin_tools
    from cortex.tools.web_tools import get_all_web_tools
    from cortex.tools.git_tools import get_all_git_tools
    from cortex.tools.pip_tools import get_all_pip_tools
    from cortex.tools.intelligence_tools import get_all_intelligence_tools
    import json

    # Charger tous les tools
    all_tools = []
    all_tools.extend(get_all_builtin_tools())
    all_tools.extend(get_all_web_tools())
    all_tools.extend(get_all_git_tools())
    all_tools.extend(get_all_pip_tools())
    all_tools.extend(get_all_intelligence_tools())

    # Créer le filtre
    tool_filter = ToolFilter()

    # Test 1: Requête web scraping
    print("=== Test 1: Web Scraping ===")
    request1 = "Extract the title from https://example.com using xpath //h1/text()"
    filtered1 = tool_filter.filter_tools(request1, all_tools)
    print(f"Request: {request1}")
    print(f"Tools selected: {len(filtered1)}/{len(all_tools)}")
    for t in filtered1:
        print(f"  - {t.name}")

    # Calculer économie
    size_all = sum(len(json.dumps(t.to_openai_format())) for t in all_tools)
    size_filtered = sum(len(json.dumps(t.to_openai_format())) for t in filtered1)
    print(f"Tokens: {size_filtered // 4} (vs {size_all // 4} sans filtre)")
    print(f"Économie: {100 - (size_filtered / size_all * 100):.0f}%")
    print()

    # Test 2: Requête git
    print("=== Test 2: Git Operations ===")
    request2 = "git commit and push my changes"
    filtered2 = tool_filter.filter_tools(request2, all_tools)
    print(f"Request: {request2}")
    print(f"Tools selected: {len(filtered2)}/{len(all_tools)}")
    for t in filtered2:
        print(f"  - {t.name}")

    size_filtered2 = sum(len(json.dumps(t.to_openai_format())) for t in filtered2)
    print(f"Tokens: {size_filtered2 // 4} (vs {size_all // 4} sans filtre)")
    print(f"Économie: {100 - (size_filtered2 / size_all * 100):.0f}%")
    print()

    # Test 3: Requête générale
    print("=== Test 3: General Request ===")
    request3 = "Hello, how are you?"
    filtered3 = tool_filter.filter_tools(request3, all_tools)
    print(f"Request: {request3}")
    print(f"Tools selected: {len(filtered3)}/{len(all_tools)}")
    for t in filtered3:
        print(f"  - {t.name}")

    size_filtered3 = sum(len(json.dumps(t.to_openai_format())) for t in filtered3)
    print(f"Tokens: {size_filtered3 // 4} (vs {size_all // 4} sans filtre)")
    print(f"Économie: {100 - (size_filtered3 / size_all * 100):.0f}%")
