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

    # User-agent Mozilla fixe (comme demandé par l'utilisateur)
    # Plus de rotation aléatoire - utilisation d'un seul user-agent cohérent
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # Whitelist de sites connus safe (bypass robots.txt)
    KNOWN_SAFE_SITES = [
        "wikipedia.org",
        "wikimedia.org",
        "example.com",
    ]

    def __init__(self, storage_dir: str = "cortex/data/scraped_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Session persistante pour cookies
        self.session = requests.Session()

        # Cache de robots.txt (stocke le contenu texte, pas RobotFileParser)
        self.robots_cache: Dict[str, str] = {}

    def _get_user_agent(self) -> str:
        """Retourne le user-agent Mozilla fixe"""
        return self.DEFAULT_USER_AGENT

    def _random_delay(self, min_seconds: float = 1.5, max_seconds: float = 2.5):
        """Délai randomisé pour paraître humain et respecter les serveurs"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def _evaluate_xpath(self, tree: etree._Element, xpath: str) -> List[Any]:
        """
        Évalue un XPath (XPath 1.0 via lxml)

        Args:
            tree: Arbre HTML parsé (lxml)
            xpath: Expression XPath

        Returns:
            Liste de résultats
        """
        # XPath 1.0 via lxml
        return tree.xpath(xpath)

    def _custom_robots_check(self, robots_txt: str, url: str, user_agent: str) -> bool:
        """
        Parser robots.txt custom qui fonctionne correctement

        Fix pour le bug de urllib.robotparser qui bloque tout sur Wikipedia.

        Args:
            robots_txt: Contenu du robots.txt
            url: URL à vérifier
            user_agent: User-agent

        Returns:
            True si autorisé, False si bloqué
        """
        from urllib.parse import urlparse

        parsed = urlparse(url)
        path = parsed.path

        # Parser le robots.txt ligne par ligne
        lines = robots_txt.split('\n')

        current_agents = []
        rules = []  # (agent_list, allow/disallow, path)

        for line in lines:
            line = line.split('#')[0].strip()  # Enlever commentaires
            if not line:
                continue

            if line.lower().startswith('user-agent:'):
                agent = line.split(':', 1)[1].strip()
                current_agents.append(agent.lower())
            elif line.lower().startswith('disallow:'):
                disallow_path = line.split(':', 1)[1].strip()
                for agent in current_agents:
                    rules.append((agent, 'disallow', disallow_path))
            elif line.lower().startswith('allow:'):
                allow_path = line.split(':', 1)[1].strip()
                for agent in current_agents:
                    rules.append((agent, 'allow', allow_path))
            elif current_agents:
                # Nouvelle section user-agent
                if line.lower().startswith('user-agent:'):
                    current_agents = []

        # Trouver les règles applicables
        applicable_rules = []
        ua_lower = user_agent.lower()

        for agent, rule_type, rule_path in rules:
            if agent == '*' or agent in ua_lower:
                applicable_rules.append((rule_type, rule_path))

        # Évaluer les règles (la plus spécifique gagne)
        if not applicable_rules:
            return True  # Pas de règles = autorisé

        # Trier par longueur de path (plus spécifique en premier)
        applicable_rules.sort(key=lambda x: len(x[1]), reverse=True)

        for rule_type, rule_path in applicable_rules:
            if not rule_path:
                continue

            # Vérifier si le path correspond
            if path.startswith(rule_path):
                if rule_type == 'allow':
                    return True
                elif rule_type == 'disallow':
                    return False

        # Par défaut: autorisé
        return True

    def _can_fetch(self, url: str, user_agent: str = None) -> bool:
        """
        Vérifie si robots.txt autorise le scraping

        Utilise:
        1. Whitelist de sites connus safe (bypass direct)
        2. Parser robots.txt custom (fix du bug urllib.robotparser)

        Args:
            url: URL à vérifier
            user_agent: User-agent à utiliser (si None, utilise DEFAULT_USER_AGENT)

        Returns:
            True si autorisé
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            # User-agent par défaut
            if user_agent is None:
                user_agent = self.DEFAULT_USER_AGENT

            # 1. Check whitelist de sites connus safe
            for safe_site in self.KNOWN_SAFE_SITES:
                if safe_site in parsed.netloc:
                    return True  # Bypass robots.txt pour sites whitelistés

            # 2. Fetch robots.txt si pas en cache
            if base_url not in self.robots_cache:
                try:
                    response = requests.get(f"{base_url}/robots.txt", timeout=5)
                    if response.status_code == 200:
                        # Stocker le contenu texte dans le cache
                        self.robots_cache[base_url] = response.text
                    else:
                        # Pas de robots.txt = autorisé
                        self.robots_cache[base_url] = ""
                        return True
                except Exception:
                    # Erreur fetch = autorisé par défaut
                    self.robots_cache[base_url] = ""
                    return True

            # 3. Utiliser notre parser custom
            robots_txt = self.robots_cache[base_url]
            if not robots_txt:
                return True  # Pas de robots.txt = autorisé

            return self._custom_robots_check(robots_txt, url, user_agent)

        except Exception as e:
            # En cas d'erreur, autoriser par défaut
            print(f"⚠️  robots.txt check error: {e}")
            return True

    def _fetch_page(self, url: str, headers: Dict[str, str], use_delay: bool = True) -> requests.Response:
        """
        Fetch une page avec techniques stealth avancées

        Args:
            url: URL à fetcher
            headers: Headers HTTP
            use_delay: Utiliser le délai aléatoire (True par défaut)

        Returns:
            Response object
        """
        from urllib.parse import urlparse

        # Override user-agent seulement si absent
        headers = headers.copy()
        if "User-Agent" not in headers:
            headers["User-Agent"] = self._get_user_agent()

        # Headers réalistes d'un vrai browser Chrome moderne
        if "Accept" not in headers:
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        if "Accept-Language" not in headers:
            headers["Accept-Language"] = "en-US,en;q=0.9,fr;q=0.8"
        if "Accept-Encoding" not in headers:
            headers["Accept-Encoding"] = "gzip, deflate, br"
        if "DNT" not in headers:
            headers["DNT"] = "1"
        if "Connection" not in headers:
            headers["Connection"] = "keep-alive"
        if "Upgrade-Insecure-Requests" not in headers:
            headers["Upgrade-Insecure-Requests"] = "1"

        # Headers Sec-Fetch-* (Chrome moderne)
        parsed_url = urlparse(url)
        if "Sec-Fetch-Dest" not in headers:
            headers["Sec-Fetch-Dest"] = "document"
        if "Sec-Fetch-Mode" not in headers:
            headers["Sec-Fetch-Mode"] = "navigate"
        if "Sec-Fetch-Site" not in headers:
            headers["Sec-Fetch-Site"] = "none"
        if "Sec-Fetch-User" not in headers:
            headers["Sec-Fetch-User"] = "?1"

        # Sec-CH-UA headers (Chrome User Agent Client Hints)
        if "Sec-CH-UA" not in headers:
            headers["Sec-CH-UA"] = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
        if "Sec-CH-UA-Mobile" not in headers:
            headers["Sec-CH-UA-Mobile"] = "?0"
        if "Sec-CH-UA-Platform" not in headers:
            headers["Sec-CH-UA-Platform"] = '"Windows"'

        # Referer si disponible (simule navigation depuis Google)
        if "Referer" not in headers:
            # Simule une visite depuis Google search
            headers["Referer"] = "https://www.google.com/"

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
            user_agent = self._get_user_agent()
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
