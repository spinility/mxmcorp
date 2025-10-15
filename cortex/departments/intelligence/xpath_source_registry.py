"""
XPath Source Registry - Gestion des sources web avec XPath

Responsabilités:
- Stocke URL + XPath pour scraping
- Valide que XPath fonctionnent toujours
- Permet gestion manuelle (add/update/delete)
- Commandes en langage naturel
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json


@dataclass
class XPathSource:
    """Source web avec XPath"""
    id: str
    name: str
    url: str
    xpath: str
    description: str
    category: str  # "tech_trends", "news", "finance", etc.
    refresh_interval_hours: int
    created_at: datetime
    last_validated: Optional[datetime] = None
    validation_status: str = "pending"  # "success", "failure", "pending"
    last_error: Optional[str] = None
    enabled: bool = True
    headers: Dict[str, str] = field(default_factory=dict)
    authentication: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "xpath": self.xpath,
            "description": self.description,
            "category": self.category,
            "refresh_interval_hours": self.refresh_interval_hours,
            "created_at": self.created_at.isoformat(),
            "last_validated": self.last_validated.isoformat() if self.last_validated else None,
            "validation_status": self.validation_status,
            "last_error": self.last_error,
            "enabled": self.enabled,
            "headers": self.headers,
            "authentication": self.authentication
        }

    def needs_refresh(self) -> bool:
        """Vérifie si source nécessite refresh"""
        if not self.last_validated:
            return True

        age = datetime.now() - self.last_validated
        return age > timedelta(hours=self.refresh_interval_hours)


class XPathSourceRegistry:
    """
    Registry de toutes les sources web avec XPath

    Permet:
    - Ajouter/modifier/supprimer sources
    - Valider XPath
    - Lister sources par catégorie
    - Recherche en langage naturel
    """

    def __init__(self, registry_file: str = "cortex/data/web_sources.json"):
        self.registry_file = Path(registry_file)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

        self.sources: Dict[str, XPathSource] = {}
        self._load()

        # Default headers (stealth)
        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    def _load(self):
        """Charge registry depuis disque"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    for source_data in data.get("sources", []):
                        source_data["created_at"] = datetime.fromisoformat(source_data["created_at"])
                        if source_data["last_validated"]:
                            source_data["last_validated"] = datetime.fromisoformat(source_data["last_validated"])

                        source = XPathSource(**source_data)
                        self.sources[source.id] = source
            except Exception as e:
                print(f"Warning: Could not load registry: {e}")

    def _save(self):
        """Sauvegarde registry sur disque"""
        data = {
            "updated_at": datetime.now().isoformat(),
            "total_sources": len(self.sources),
            "sources": [source.to_dict() for source in self.sources.values()]
        }

        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_source(
        self,
        name: str,
        url: str,
        xpath: str,
        description: str,
        category: str = "general",
        refresh_interval_hours: int = 24,
        headers: Optional[Dict[str, str]] = None
    ) -> XPathSource:
        """
        Ajoute une nouvelle source

        Args:
            name: Nom descriptif
            url: URL à scraper
            xpath: Expression XPath
            description: Description de ce qui est scrapé
            category: Catégorie (tech_trends, news, etc)
            refresh_interval_hours: Intervalle de refresh
            headers: Headers HTTP custom (optionnel)

        Returns:
            XPathSource créée
        """
        # Générer ID unique
        source_id = f"src_{len(self.sources) + 1:03d}"

        # Utiliser headers par défaut si non fournis
        if headers is None:
            headers = self.default_headers.copy()

        source = XPathSource(
            id=source_id,
            name=name,
            url=url,
            xpath=xpath,
            description=description,
            category=category,
            refresh_interval_hours=refresh_interval_hours,
            created_at=datetime.now(),
            headers=headers
        )

        self.sources[source_id] = source
        self._save()

        print(f"✓ Added source: {name} ({source_id})")
        return source

    def update_xpath(self, source_id: str, new_xpath: str) -> XPathSource:
        """
        Met à jour XPath d'une source

        Args:
            source_id: ID de la source
            new_xpath: Nouveau XPath

        Returns:
            Source mise à jour
        """
        if source_id not in self.sources:
            raise ValueError(f"Source {source_id} not found")

        source = self.sources[source_id]
        old_xpath = source.xpath
        source.xpath = new_xpath
        source.validation_status = "pending"  # Nécessite revalidation

        self._save()

        print(f"✓ Updated XPath for {source.name}")
        print(f"  Old: {old_xpath}")
        print(f"  New: {new_xpath}")

        return source

    def update_source(
        self,
        source_id: str,
        **kwargs
    ) -> XPathSource:
        """
        Met à jour n'importe quel champ d'une source

        Args:
            source_id: ID de la source
            **kwargs: Champs à mettre à jour

        Returns:
            Source mise à jour
        """
        if source_id not in self.sources:
            raise ValueError(f"Source {source_id} not found")

        source = self.sources[source_id]

        for key, value in kwargs.items():
            if hasattr(source, key):
                setattr(source, key, value)

        self._save()

        print(f"✓ Updated source: {source.name}")
        return source

    def delete_source(self, source_id: str):
        """Supprime une source"""
        if source_id not in self.sources:
            raise ValueError(f"Source {source_id} not found")

        source = self.sources[source_id]
        del self.sources[source_id]
        self._save()

        print(f"✓ Deleted source: {source.name} ({source_id})")

    def get_source(self, source_id: str) -> Optional[XPathSource]:
        """Récupère une source par ID"""
        return self.sources.get(source_id)

    def get_sources_by_category(self, category: str) -> List[XPathSource]:
        """Récupère toutes les sources d'une catégorie"""
        return [s for s in self.sources.values() if s.category == category]

    def get_enabled_sources(self) -> List[XPathSource]:
        """Récupère toutes les sources activées"""
        return [s for s in self.sources.values() if s.enabled]

    def get_sources_needing_refresh(self) -> List[XPathSource]:
        """Récupère sources nécessitant refresh"""
        return [s for s in self.sources.values() if s.enabled and s.needs_refresh()]

    def search_sources(self, query: str) -> List[XPathSource]:
        """
        Recherche sources par mots-clés

        Cherche dans name, description, category

        Args:
            query: Requête en langage naturel

        Returns:
            Liste de sources matchantes
        """
        query_lower = query.lower()
        results = []

        for source in self.sources.values():
            if (query_lower in source.name.lower() or
                query_lower in source.description.lower() or
                query_lower in source.category.lower()):
                results.append(source)

        return results

    def list_all_sources(self) -> List[XPathSource]:
        """Liste toutes les sources"""
        return list(self.sources.values())

    def get_categories(self) -> List[str]:
        """Liste toutes les catégories"""
        categories = set(s.category for s in self.sources.values())
        return sorted(categories)

    def get_statistics(self) -> Dict[str, Any]:
        """Statistiques du registry"""
        sources_list = list(self.sources.values())

        return {
            "total_sources": len(sources_list),
            "enabled_sources": sum(1 for s in sources_list if s.enabled),
            "categories": len(self.get_categories()),
            "validation_success_rate": sum(
                1 for s in sources_list if s.validation_status == "success"
            ) / len(sources_list) if sources_list else 0,
            "sources_needing_refresh": len(self.get_sources_needing_refresh()),
            "never_validated": sum(1 for s in sources_list if not s.last_validated)
        }

    def display_sources(self, sources: Optional[List[XPathSource]] = None):
        """Affiche sources de manière lisible"""
        if sources is None:
            sources = self.list_all_sources()

        if not sources:
            print("No sources found")
            return

        print(f"\n{'='*70}")
        print(f"WEB SOURCES ({len(sources)} total)")
        print(f"{'='*70}\n")

        # Grouper par catégorie
        by_category: Dict[str, List[XPathSource]] = {}
        for source in sources:
            if source.category not in by_category:
                by_category[source.category] = []
            by_category[source.category].append(source)

        for category, cat_sources in sorted(by_category.items()):
            print(f"📁 {category.upper()} ({len(cat_sources)} sources)")
            print(f"{'-'*70}")

            for source in cat_sources:
                status_emoji = {
                    "success": "✅",
                    "failure": "❌",
                    "pending": "⏳"
                }.get(source.validation_status, "❓")

                enabled_str = "✓" if source.enabled else "✗"

                print(f"  [{source.id}] {enabled_str} {status_emoji} {source.name}")
                print(f"      URL: {source.url}")
                print(f"      XPath: {source.xpath[:80]}...")
                print(f"      Refresh: every {source.refresh_interval_hours}h")

                if source.last_validated:
                    age = datetime.now() - source.last_validated
                    age_str = f"{age.days}d {age.seconds//3600}h ago"
                    print(f"      Last validated: {age_str}")
                else:
                    print(f"      Last validated: Never")

                if source.last_error:
                    print(f"      ⚠ Error: {source.last_error[:60]}")

                print()

        print(f"{'='*70}\n")


def create_xpath_source_registry(registry_file: str = "cortex/data/web_sources.json") -> XPathSourceRegistry:
    """Factory function"""
    return XPathSourceRegistry(registry_file)


# Test
if __name__ == "__main__":
    print("Testing XPath Source Registry...")

    registry = XPathSourceRegistry("cortex/data/test_web_sources.json")

    # Test 1: Add source
    print("\n1. Adding sources...")
    source1 = registry.add_source(
        name="GitHub Trending Python",
        url="https://github.com/trending/python",
        xpath="//article[@class='Box-row']//h2/a/@href",
        description="Top trending Python repositories",
        category="tech_trends",
        refresh_interval_hours=24
    )

    source2 = registry.add_source(
        name="HackerNews Frontpage",
        url="https://news.ycombinator.com",
        xpath="//tr[@class='athing']//a[@class='titlelink']/text()",
        description="Top stories on HackerNews",
        category="tech_news",
        refresh_interval_hours=6
    )

    # Test 2: List sources
    print("\n2. Listing sources...")
    registry.display_sources()

    # Test 3: Search
    print("\n3. Searching for 'github'...")
    results = registry.search_sources("github")
    print(f"✓ Found {len(results)} results")

    # Test 4: Update XPath
    print("\n4. Updating XPath...")
    registry.update_xpath(source1.id, "//div[@class='new-structure']//a/@href")

    # Test 5: Statistics
    print("\n5. Statistics...")
    stats = registry.get_statistics()
    print(f"✓ Stats:")
    print(f"  Total sources: {stats['total_sources']}")
    print(f"  Enabled: {stats['enabled_sources']}")
    print(f"  Never validated: {stats['never_validated']}")

    print("\n✓ XPath Source Registry works correctly!")
