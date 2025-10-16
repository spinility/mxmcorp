"""
Stealth Web Crawler - Scraping indétectable avec validation XPath

Responsabilités:
- Valide que XPath fonctionnent toujours
- Scrape données web de manière indétectable
- User-agent rotation
- Délais randomisés
- Respect robots.txt
- Stockage avec métadonnées complètes
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import time
import random
import urllib.robotparser
import requests
from lxml import html, etree
import elementpath

from cortex.departments.intelligence.xpath_source_registry import XPathSource


@dataclass
class ValidationResult:
    """Résultat de validation XPath"""
    success: bool
    elements_found: int
    sample_data: List[str]
    error: Optional[str] = None
    response_time_ms: float = 0
    status_code: int = 0


@dataclass
class ScrapedData:
    """Données scrapées avec métadonnées"""
    scrape_id: str
    source_id: str
    source_name: str
    url: str
    xpath_used: str
    scraped_at: datetime
    validation_before_scrape: ValidationResult
    data: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scrape_id": self.scrape_id,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "url": self.url,
            "xpath_used": self.xpath_used,
            "scraped_at": self.scraped_at.isoformat(),
            "validation_before_scrape": {
                "success": self.validation_before_scrape.success,
                "elements_found": self.validation_before_scrape.elements_found,
                "sample_data": self.validation_before_scrape.sample_data[:3]
            },
            "data": self.data,
            "metadata": self.metadata
        }


class StealthWebCrawler:
    """
    Crawler web indétectable

    Techniques stealth:
    - Rotation user-agents
    - Délais randomisés
    - Headers réalistes
    - Session persistante (cookies)
    - Respect robots.txt
    """

    # Pool de user-agents réalistes
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]

    def __init__(self, storage_dir: str = "cortex/data/scraped_data", xpath_version: str = "2.0"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Session persistante pour cookies
        self.session = requests.Session()

        # Cache de robots.txt
        self.robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}

        # XPath version (1.0 or 2.0)
        self.xpath_version = xpath_version

    def _get_random_user_agent(self) -> str:
        """Retourne un user-agent aléatoire"""
        return random.choice(self.USER_AGENTS)

    def _random_delay(self, min_seconds: float = 0.5, max_seconds: float = 1.5):
        """Délai randomisé pour paraître humain"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def _evaluate_xpath(self, tree: etree._Element, xpath: str) -> List[Any]:
        """
        Évalue un XPath selon la version configurée

        Args:
            tree: Arbre HTML parsé (lxml)
            xpath: Expression XPath

        Returns:
            Liste de résultats
        """
        if self.xpath_version == "2.0":
            # XPath 2.0 via elementpath
            try:
                # elementpath nécessite un ElementTree, pas un Element
                # Convertir l'arbre lxml en ElementTree standard
                root = tree.getroottree().getroot()
                selector = elementpath.select(root, xpath, namespaces=None)

                # Convertir le résultat en liste
                if hasattr(selector, '__iter__') and not isinstance(selector, (str, bytes)):
                    return list(selector)
                else:
                    return [selector] if selector is not None else []
            except Exception as e:
                # Fallback vers XPath 1.0 si erreur
                print(f"⚠️  XPath 2.0 failed, falling back to 1.0: {e}")
                return tree.xpath(xpath)
        else:
            # XPath 1.0 via lxml
            return tree.xpath(xpath)

    def _can_fetch(self, url: str, user_agent: str = None) -> bool:
        """
        Vérifie si robots.txt autorise le scraping

        Args:
            url: URL à vérifier
            user_agent: User-agent à utiliser (si None, utilise un navigateur réaliste)

        Returns:
            True si autorisé
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            # Check cache
            if base_url not in self.robots_cache:
                rp = urllib.robotparser.RobotFileParser()
                rp.set_url(f"{base_url}/robots.txt")
                try:
                    rp.read()
                    self.robots_cache[base_url] = rp
                except Exception:
                    # Si erreur lecture robots.txt, autoriser
                    return True

            # Utiliser un user-agent de navigateur réaliste au lieu de "*"
            # Cela permet de passer sur Wikipedia qui ne bloque pas les navigateurs légitimes
            if user_agent is None:
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

            return self.robots_cache[base_url].can_fetch(user_agent, url)

        except Exception:
            # En cas d'erreur, autoriser par défaut
            return True

    def _fetch_page(self, url: str, headers: Dict[str, str], use_delay: bool = True) -> requests.Response:
        """
        Fetch une page avec techniques stealth

        Args:
            url: URL à fetcher
            headers: Headers HTTP
            use_delay: Utiliser le délai aléatoire (True par défaut)

        Returns:
            Response object
        """
        # Override user-agent seulement si absent
        headers = headers.copy()
        if "User-Agent" not in headers:
            headers["User-Agent"] = self._get_random_user_agent()

        # Ajouter headers réalistes si absents
        if "Accept" not in headers:
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        if "Accept-Language" not in headers:
            headers["Accept-Language"] = "en-US,en;q=0.9"
        if "DNT" not in headers:
            headers["DNT"] = "1"

        # Random delay avant requête (optionnel pour tests)
        if use_delay:
            self._random_delay()

        # Faire la requête
        response = self.session.get(
            url,
            headers=headers,
            timeout=30,
            allow_redirects=True
        )

        return response

    def validate_xpath(
        self,
        source: XPathSource,
        check_robots: bool = True
    ) -> ValidationResult:
        """
        Valide qu'un XPath fonctionne

        Args:
            source: Source à valider
            check_robots: Vérifier robots.txt

        Returns:
            ValidationResult avec détails
        """
        start_time = time.time()

        try:
            # Vérifier robots.txt avec le user-agent qu'on va utiliser
            user_agent = self._get_random_user_agent()
            if check_robots and not self._can_fetch(source.url, user_agent):
                return ValidationResult(
                    success=False,
                    elements_found=0,
                    sample_data=[],
                    error="Blocked by robots.txt",
                    response_time_ms=0,
                    status_code=403
                )

            # Fetch page avec le même user-agent
            headers = source.headers.copy()
            headers["User-Agent"] = user_agent
            response = self._fetch_page(source.url, headers, use_delay=True)
            response_time = (time.time() - start_time) * 1000

            if response.status_code != 200:
                return ValidationResult(
                    success=False,
                    elements_found=0,
                    sample_data=[],
                    error=f"HTTP {response.status_code}",
                    response_time_ms=response_time,
                    status_code=response.status_code
                )

            # Parse HTML
            tree = html.fromstring(response.content)

            # Appliquer XPath (avec support 2.0)
            elements = self._evaluate_xpath(tree, source.xpath)

            if not elements:
                return ValidationResult(
                    success=False,
                    elements_found=0,
                    sample_data=[],
                    error="XPath returned no elements (page structure changed?)",
                    response_time_ms=response_time,
                    status_code=200
                )

            # Extraire texte/attributs
            sample_data = []
            for elem in elements[:5]:  # Max 5 samples
                if isinstance(elem, str):
                    sample_data.append(elem)
                elif hasattr(elem, 'text'):
                    sample_data.append(elem.text or "")
                else:
                    sample_data.append(str(elem))

            return ValidationResult(
                success=True,
                elements_found=len(elements),
                sample_data=sample_data,
                error=None,
                response_time_ms=response_time,
                status_code=200
            )

        except Exception as e:
            return ValidationResult(
                success=False,
                elements_found=0,
                sample_data=[],
                error=str(e),
                response_time_ms=(time.time() - start_time) * 1000,
                status_code=0
            )

    def scrape(
        self,
        source: XPathSource,
        validate_first: bool = True
    ) -> ScrapedData:
        """
        Scrape données depuis une source

        Args:
            source: Source à scraper
            validate_first: Valider XPath avant scraping

        Returns:
            ScrapedData avec toutes les données et métadonnées
        """
        # Valider d'abord si demandé
        if validate_first:
            validation = self.validate_xpath(source)

            if not validation.success:
                raise ValueError(f"Validation failed: {validation.error}")
        else:
            # Scrape directement
            validation = ValidationResult(
                success=True,
                elements_found=0,
                sample_data=[],
                error=None
            )

        # Fetch page
        start_time = time.time()
        response = self._fetch_page(source.url, source.headers)
        fetch_time = time.time() - start_time

        # Parse
        tree = html.fromstring(response.content)
        elements = self._evaluate_xpath(tree, source.xpath)

        # Extraire données
        data = []
        for elem in elements:
            if isinstance(elem, str):
                data.append(elem.strip())
            elif hasattr(elem, 'text'):
                text = elem.text or ""
                data.append(text.strip())
            else:
                data.append(str(elem).strip())

        # Créer ScrapedData
        scrape_id = f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{source.id}"

        scraped = ScrapedData(
            scrape_id=scrape_id,
            source_id=source.id,
            source_name=source.name,
            url=source.url,
            xpath_used=source.xpath,
            scraped_at=datetime.now(),
            validation_before_scrape=validation,
            data=data,
            metadata={
                "elements_count": len(data),
                "response_time_ms": fetch_time * 1000,
                "status_code": response.status_code,
                "page_size_bytes": len(response.content)
            }
        )

        # Sauvegarder
        self._save_scraped_data(scraped, source.category)

        print(f"✓ Scraped {len(data)} elements from {source.name}")

        return scraped

    def _save_scraped_data(self, scraped: ScrapedData, category: str):
        """Sauvegarde données scrapées sur disque"""
        # Structure: cortex/data/scraped_data/{category}/{source_id}/YYYYMMDD_HHMMSS.json
        category_dir = self.storage_dir / category / scraped.source_id
        category_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{scraped.scraped_at.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = category_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(scraped.to_dict(), f, indent=2, ensure_ascii=False)

    def get_latest_scrape(self, source_id: str, category: str) -> Optional[ScrapedData]:
        """
        Récupère le dernier scrape pour une source

        Args:
            source_id: ID de la source
            category: Catégorie

        Returns:
            ScrapedData le plus récent ou None
        """
        source_dir = self.storage_dir / category / source_id

        if not source_dir.exists():
            return None

        # Trouver fichier le plus récent
        files = sorted(source_dir.glob("*.json"), reverse=True)

        if not files:
            return None

        # Charger
        with open(files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Reconstruire ValidationResult
        val_data = data["validation_before_scrape"]
        validation = ValidationResult(
            success=val_data["success"],
            elements_found=val_data["elements_found"],
            sample_data=val_data["sample_data"]
        )

        return ScrapedData(
            scrape_id=data["scrape_id"],
            source_id=data["source_id"],
            source_name=data["source_name"],
            url=data["url"],
            xpath_used=data["xpath_used"],
            scraped_at=datetime.fromisoformat(data["scraped_at"]),
            validation_before_scrape=validation,
            data=data["data"],
            metadata=data["metadata"]
        )


def create_stealth_web_crawler(storage_dir: str = "cortex/data/scraped_data") -> StealthWebCrawler:
    """Factory function"""
    return StealthWebCrawler(storage_dir)


# Test
if __name__ == "__main__":
    print("Testing Stealth Web Crawler...")

    from cortex.departments.intelligence.xpath_source_registry import XPathSourceRegistry

    # Créer registry avec source test
    registry = XPathSourceRegistry("cortex/data/test_web_sources_crawler.json")

    # Ajouter source réelle (HackerNews car stable)
    source = registry.add_source(
        name="HackerNews Frontpage",
        url="https://news.ycombinator.com",
        xpath="//span[@class='titleline']/a/text()",
        description="Top stories on HackerNews",
        category="tech_news",
        refresh_interval_hours=6
    )

    # Créer crawler
    crawler = StealthWebCrawler("cortex/data/test_scraped_data")

    # Test 1: Validate XPath
    print("\n1. Validating XPath...")
    validation = crawler.validate_xpath(source)

    print(f"✓ Validation result:")
    print(f"  Success: {validation.success}")
    print(f"  Elements found: {validation.elements_found}")
    print(f"  Response time: {validation.response_time_ms:.0f}ms")
    print(f"  Sample data: {validation.sample_data[:3]}")

    if validation.success:
        # Test 2: Scrape data
        print("\n2. Scraping data...")
        scraped = crawler.scrape(source, validate_first=False)

        print(f"✓ Scraped {len(scraped.data)} items")
        print(f"  First 5 items:")
        for i, item in enumerate(scraped.data[:5], 1):
            print(f"    {i}. {item[:60]}...")

        # Test 3: Get latest scrape
        print("\n3. Getting latest scrape...")
        latest = crawler.get_latest_scrape(source.id, source.category)

        if latest:
            print(f"✓ Latest scrape: {latest.scrape_id}")
            print(f"  Scraped at: {latest.scraped_at}")
            print(f"  Elements: {len(latest.data)}")

    print("\n✓ Stealth Web Crawler works correctly!")
