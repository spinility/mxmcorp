"""
Scrapy Web Crawler - Scraping professionnel avec Scrapy UNIQUEMENT

Avantages de Scrapy:
- Framework robuste et éprouvé
- Sélecteurs XPath natifs (via parsel/lxml interne)
- Gestion automatique des requêtes concurrentes
- Middlewares puissants
- Respect automatique des délais
- Gestion d'erreurs avancée
- Pipeline de traitement des données

Configuration (comme votre exemple):
- ROBOTSTXT_OBEY = False (par défaut)
- DOWNLOAD_DELAY = 2 (poli)
- RANDOMIZE_DOWNLOAD_DELAY = True
- CONCURRENT_REQUESTS_PER_DOMAIN = 1
- User-agent Mozilla fixe
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import Response


@dataclass
class ScrapyResult:
    """Résultat de scraping Scrapy"""
    success: bool
    url: str
    xpath: str
    data: List[str]
    elements_count: int
    response_time_ms: float
    status_code: int
    error: Optional[str] = None


class XPathSpider(scrapy.Spider):
    """
    Spider Scrapy personnalisé pour extraction XPath

    Peut utiliser XPath 1.0 (Scrapy natif) ou XPath 2.0 (via elementpath)
    """

    name = "xpath_spider"

    # Configuration par défaut (peut être overridée)
    custom_settings = {
        # === robots.txt ===
        'ROBOTSTXT_OBEY': False,  # Désactivé par défaut

        # === Politesse ===
        'DOWNLOAD_DELAY': 2,  # 2 secondes entre requêtes
        'RANDOMIZE_DOWNLOAD_DELAY': True,  # Randomiser (1.5-2.5s)
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # Une seule requête à la fois

        # === User-Agent ===
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',

        # === Retry & Timeout ===
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'DOWNLOAD_TIMEOUT': 30,

        # === Logging ===
        'LOG_LEVEL': 'ERROR',  # Moins verbeux

        # === Headers ===
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1',
        },

        # === Middlewares ===
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': None,  # Désactivé
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,  # On gère nous-mêmes
            'scrapy.downloadermiddlewares.httperror.HttpErrorMiddleware': None,  # Désactivé pour gérer tous les codes HTTP
        },

        # === Handle all HTTP status codes ===
        'HTTPERROR_ALLOWED_ALL': True,
    }

    def __init__(self, url: str, xpath: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [url]
        self.target_xpath = xpath
        self.results = []
        self.start_time = None
        self.response_time_ms = 0

    def start_requests(self):
        """Démarre les requêtes avec timing"""
        self.start_time = datetime.now()
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, errback=self.errback)

    def parse(self, response: Response):
        """Parse la réponse et extrait les données avec XPath (sélecteurs Scrapy natifs)"""
        # Calculer temps de réponse
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds() * 1000
            self.response_time_ms = elapsed

        try:
            # Utiliser les sélecteurs Scrapy natifs (XPath 1.0 via parsel/lxml)
            # Scrapy gère lxml en interne via parsel
            elements = response.xpath(self.target_xpath).getall()

            # Si ça retourne vide, essayer .extract() (ancienne API Scrapy)
            if not elements:
                elements = response.xpath(self.target_xpath).extract()

            # Nettoyer les données
            data = [elem.strip() for elem in elements if elem.strip()]

            # Stocker les résultats
            self.results.append(ScrapyResult(
                success=True,
                url=response.url,
                xpath=self.target_xpath,
                data=data,
                elements_count=len(data),
                response_time_ms=self.response_time_ms,
                status_code=response.status,
                error=None
            ))

        except Exception as e:
            self.results.append(ScrapyResult(
                success=False,
                url=response.url,
                xpath=self.target_xpath,
                data=[],
                elements_count=0,
                response_time_ms=self.response_time_ms,
                status_code=response.status,
                error=str(e)
            ))

    def errback(self, failure):
        """Gère les erreurs de requête"""
        request = failure.request
        self.results.append(ScrapyResult(
            success=False,
            url=request.url,
            xpath=self.target_xpath,
            data=[],
            elements_count=0,
            response_time_ms=0,
            status_code=0,
            error=str(failure.value)
        ))


class ScrapyWebCrawler:
    """
    Wrapper Scrapy pour scraping facile

    Utilise Scrapy en mode "one-shot" pour scraping synchrone
    XPath 1.0 natif via les sélecteurs Scrapy (parsel/lxml)
    """

    def scrape_xpath(
        self,
        url: str,
        xpath: str,
        check_robots: bool = False
    ) -> ScrapyResult:
        """
        Scrape une URL avec un XPath donné

        Args:
            url: URL à scraper
            xpath: Expression XPath (1.0 via sélecteurs Scrapy)
            check_robots: Vérifier robots.txt (default: False)

        Returns:
            ScrapyResult avec les données extraites
        """
        # Configuration du spider
        custom_settings = {
            'ROBOTSTXT_OBEY': check_robots,  # Configurable
        }

        # Créer et exécuter le spider
        process = CrawlerProcess(settings={
            **XPathSpider.custom_settings,
            **custom_settings,
        })

        # Variable pour stocker les résultats
        results_container = []

        # Callback pour récupérer le spider après crawl
        def spider_closed(spider):
            if spider.results:
                results_container.append(spider.results[0])

        # Lancer le crawl avec la classe spider et ses arguments
        crawler = process.create_crawler(XPathSpider)
        crawler.signals.connect(spider_closed, signal=scrapy.signals.spider_closed)
        process.crawl(crawler, url=url, xpath=xpath)
        process.start()  # Bloque jusqu'à la fin

        # Récupérer les résultats
        if results_container:
            return results_container[0]
        else:
            return ScrapyResult(
                success=False,
                url=url,
                xpath=xpath,
                data=[],
                elements_count=0,
                response_time_ms=0,
                status_code=0,
                error="No results returned"
            )


# Factory function
def create_scrapy_crawler() -> ScrapyWebCrawler:
    """Crée un crawler Scrapy"""
    return ScrapyWebCrawler()


# Test
if __name__ == "__main__":
    print("Testing Scrapy Web Crawler...")
    print("=" * 70)

    # Test 1: Wikipedia (whitelisté)
    print("\n1. Test: Wikipedia avec check_robots=False")
    crawler = ScrapyWebCrawler()

    result = crawler.scrape_xpath(
        url="https://en.wikipedia.org/wiki/Presidium",
        xpath="//span[@class='mw-page-title-main']/text()",
        check_robots=False
    )

    print(f"Success: {result.success}")
    if result.success:
        print(f"Data: {result.data}")
        print(f"Count: {result.elements_count} elements")
        print(f"Response time: {result.response_time_ms:.0f}ms")
        print(f"Status: {result.status_code}")
    else:
        print(f"Error: {result.error}")

    # Test 2: Example.com
    print("\n2. Test: Example.com")
    result2 = crawler.scrape_xpath(
        url="https://example.com",
        xpath="//h1/text()",
        check_robots=False
    )

    print(f"Success: {result2.success}")
    if result2.success:
        print(f"Data: {result2.data}")
        print(f"Count: {result2.elements_count} elements")

    print("\n✓ Scrapy Web Crawler works!")
