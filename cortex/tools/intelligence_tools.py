"""
Intelligence Tools - Outils pour le département d'Intelligence

Expose les capacités du département Intelligence via des tools standards:
- scrape_xpath: Extraire du texte d'une page web via XPath
- validate_xpath: Valider un XPath sur une URL
- add_web_source: Ajouter une source web au registry
"""

from typing import Dict, Any, List
from cortex.tools.standard_tool import StandardTool
from cortex.departments.intelligence import (
    StealthWebCrawler,
    XPathSourceRegistry,
    XPathSource
)


def scrape_xpath(url: str, xpath: str, check_robots: bool = False) -> Dict[str, Any]:
    """
    Extraire du texte d'une page web via XPath

    Args:
        url: URL de la page web
        xpath: Expression XPath pour extraire le texte
        check_robots: Vérifier robots.txt avant scraping (défaut: False pour compatibilité)

    Returns:
        Dict avec résultat du scraping
    """
    try:
        from datetime import datetime

        # Utiliser StealthWebCrawler (requests+lxml)
        crawler = StealthWebCrawler()

        # Créer une source temporaire avec TOUS les champs requis
        source = XPathSource(
            id=f"temp_{hash(url)}",
            name="Temporary Scrape",
            url=url,
            xpath=xpath,
            description="Temporary scrape for direct extraction",
            category="temporary",
            refresh_interval_hours=0,
            created_at=datetime.now(),
            last_validated=None,
            validation_status="pending",
            last_error=None,
            enabled=True
        )

        # Scraper avec validation et robots.txt
        if check_robots:
            # Mode strict: valider avec robots.txt
            result = crawler.scrape(source, validate_first=True)
        else:
            # Mode permissif: scraper directement sans validation robots.txt
            validation = crawler.validate_xpath(source, check_robots=False)

            if not validation.success:
                return {
                    "success": False,
                    "error": validation.error,
                    "url": url,
                    "xpath": xpath,
                    "message": f"XPath validation failed: {validation.error}"
                }

            # Scraper sans re-valider
            result = crawler.scrape(source, validate_first=False)

        # ScrapedData contient toujours des données, vérifier validation
        if result.validation_before_scrape.success or len(result.data) > 0:
            return {
                "success": True,
                "data": result.data,
                "count": len(result.data) if result.data else 0,
                "url": url,
                "xpath": xpath,
                "message": f"Extracted {len(result.data)} elements successfully"
            }
        else:
            return {
                "success": False,
                "error": result.validation_before_scrape.error,
                "url": url,
                "xpath": xpath,
                "message": f"Scraping failed: {result.validation_before_scrape.error}"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "url": url,
            "xpath": xpath,
            "message": f"Exception during scraping: {str(e)}"
        }


def validate_xpath(url: str, xpath: str) -> Dict[str, Any]:
    """
    Valider un XPath sur une URL

    Args:
        url: URL de la page web
        xpath: Expression XPath à valider

    Returns:
        Dict avec résultat de validation
    """
    try:
        from datetime import datetime

        crawler = StealthWebCrawler()

        # Créer une source temporaire pour validation
        source = XPathSource(
            id=f"temp_validate_{hash(url)}",
            name="Temporary Validation",
            url=url,
            xpath=xpath,
            description="Temporary source for XPath validation",
            category="temporary",
            refresh_interval_hours=0,
            created_at=datetime.now(),
            last_validated=None,
            validation_status="pending",
            last_error=None,
            enabled=True
        )

        result = crawler.validate_xpath(source)

        return {
            "success": result.success,
            "valid": result.success,
            "elements_found": result.elements_found,
            "sample_data": result.sample_data[:3] if result.sample_data else [],
            "error": result.error,
            "response_time_ms": result.response_time_ms,
            "status_code": result.status_code,
            "url": url,
            "xpath": xpath,
            "message": f"Found {result.elements_found} elements" if result.success else f"Validation failed: {result.error}"
        }

    except Exception as e:
        return {
            "success": False,
            "valid": False,
            "elements_found": 0,
            "error": str(e),
            "url": url,
            "xpath": xpath,
            "message": f"Validation exception: {str(e)}"
        }


def add_web_source(name: str, url: str, xpath: str, category: str = "general") -> Dict[str, Any]:
    """
    Ajouter une source web au registry

    Args:
        name: Nom de la source
        url: URL de la page web
        xpath: Expression XPath
        category: Catégorie (tech_news, docs, etc.)

    Returns:
        Dict avec résultat de l'ajout
    """
    try:
        registry = XPathSourceRegistry()

        # add_source requiert aussi une description
        source = registry.add_source(
            name=name,
            url=url,
            xpath=xpath,
            description=f"{name} - {category}",
            category=category,
            refresh_interval_hours=24
        )

        return {
            "success": True,
            "source_id": source.id,
            "name": source.name,
            "url": source.url,
            "xpath": source.xpath,
            "category": source.category,
            "message": f"Source '{name}' added successfully with ID {source.id}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to add source: {str(e)}"
        }


def get_all_intelligence_tools() -> List[StandardTool]:
    """
    Retourne tous les outils du département Intelligence

    Returns:
        Liste de StandardTool
    """
    return [
        StandardTool(
            name="scrape_xpath",
            description="Extract text from a web page using XPath expression. Stealth crawler (undetectable). Supports XPath 2.0 with string-join().",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the web page to scrape"
                    },
                    "xpath": {
                        "type": "string",
                        "description": "The XPath expression to extract data (e.g., '//h1/text()' for all h1 text, or 'string-join(//p//text(), \" \")' for XPath 2.0)"
                    },
                    "check_robots": {
                        "type": "boolean",
                        "description": "Check robots.txt before scraping (default: false). Set to true for strict compliance.",
                        "default": False
                    }
                },
                "required": ["url", "xpath"]
            },
            function=scrape_xpath,
            category="intelligence"
        ),
        StandardTool(
            name="validate_xpath",
            description="Validate an XPath expression on a URL before scraping",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to test the XPath on"
                    },
                    "xpath": {
                        "type": "string",
                        "description": "The XPath expression to validate"
                    }
                },
                "required": ["url", "xpath"]
            },
            function=validate_xpath,
            category="intelligence"
        ),
        StandardTool(
            name="add_web_source",
            description="Add a web source to the registry for periodic scraping",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "A descriptive name for the source"
                    },
                    "url": {
                        "type": "string",
                        "description": "The URL of the web page"
                    },
                    "xpath": {
                        "type": "string",
                        "description": "The XPath expression to extract data"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category (tech_news, docs, general, etc.)"
                    }
                },
                "required": ["name", "url", "xpath"]
            },
            function=add_web_source,
            category="intelligence"
        )
    ]
