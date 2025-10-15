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


def scrape_xpath(url: str, xpath: str) -> Dict[str, Any]:
    """
    Extraire du texte d'une page web via XPath

    Args:
        url: URL de la page web
        xpath: Expression XPath pour extraire le texte

    Returns:
        Dict avec résultat du scraping
    """
    try:
        # Créer un crawler
        crawler = StealthWebCrawler()

        # Créer une source temporaire
        source = XPathSource(
            id=f"temp_{hash(url)}",
            name="Temporary Scrape",
            url=url,
            xpath=xpath,
            category="temporary",
            created_at="",
            last_scraped=None,
            last_status="pending"
        )

        # Scraper
        result = crawler.scrape(source)

        if result.success:
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
                "error": result.error,
                "url": url,
                "xpath": xpath,
                "message": f"Scraping failed: {result.error}"
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
        crawler = StealthWebCrawler()
        result = crawler.validate_xpath(url, xpath)

        return {
            "success": result.is_valid,
            "valid": result.is_valid,
            "sample_count": result.sample_count,
            "sample_data": result.sample_data[:3] if result.sample_data else [],
            "error": result.error,
            "message": result.message,
            "url": url,
            "xpath": xpath
        }

    except Exception as e:
        return {
            "success": False,
            "valid": False,
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
        source = registry.add_source(name, url, xpath, category)

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
            description="Extract text from a web page using XPath expression. Stealth crawler (undetectable).",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the web page to scrape"
                    },
                    "xpath": {
                        "type": "string",
                        "description": "The XPath expression to extract data (e.g., '//h1/text()' for all h1 text)"
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
