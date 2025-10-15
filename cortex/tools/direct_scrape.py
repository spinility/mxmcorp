#!/usr/bin/env python3
"""
Direct Scrape - Extraction XPath sans passer par le LLM

Utilise directement StealthWebCrawler avec XPath 2.0
✅ Aucun coût API LLM (100% GRATUIT!)
✅ Exécution instantanée (pas de latence LLM)
✅ XPath 2.0 supporté (string-join, functions, etc.)
✅ Stealth crawler (user-agent rotation, delays)

Usage:
    # Simple extraction
    python3 -m cortex.tools.direct_scrape \\
        "https://en.wikipedia.org/wiki/Presidium" \\
        "//h1/text()"

    # XPath 2.0 avec string-join
    python3 -m cortex.tools.direct_scrape \\
        "https://en.wikipedia.org/wiki/Presidium" \\
        "string-join(//p[position() <= 3]//text(), ' ')" \\
        --xpath-version 2.0

    # Format texte
    python3 -m cortex.tools.direct_scrape URL XPATH --format text

    # Sauvegarder dans un fichier
    python3 -m cortex.tools.direct_scrape URL XPATH -o output.json

Pourquoi utiliser cet outil plutôt que Cortex CLI?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
| Aspect          | Cortex CLI      | direct_scrape  |
|-----------------|-----------------|----------------|
| **Coût API**    | ~$0.005/scrape  | $0.00 (GRATUIT)|
| **Latence**     | 5-15s (LLM)     | 1-3s (direct)  |
| **Contrôle**    | Via LLM         | Direct XPath   |
| **Scripting**   | Difficile       | Facile         |
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Le problème avec Cortex CLI:
    User: "extraire texte wiki"
      ↓
    LLM (coûte $$$ via API OpenAI) ← Identifie tool
      ↓
    scrape_xpath() → local (GRATUIT)
      ↓
    LLM (coûte $$$ via API OpenAI) ← Formatte réponse
      ↓
    Résultat

Avec direct_scrape (cet outil):
    User lance commande
      ↓
    scrape_xpath() → local (GRATUIT) ← PAS DE LLM!
      ↓
    Résultat

C'EST ABSURDE de payer le LLM juste pour dire "appelle scrape_xpath"!
Utilisez cet outil pour scraper directement sans frais.
"""

from typing import Dict, Any, List
from cortex.departments.intelligence import StealthWebCrawler, XPathSource
from datetime import datetime
import json


def direct_scrape(
    url: str,
    xpath: str,
    xpath_version: str = "2.0",
    output_format: str = "json",
    check_robots: bool = False
) -> Dict[str, Any]:
    """
    Extraction XPath directe sans LLM

    Args:
        url: URL de la page web
        xpath: Expression XPath (1.0 ou 2.0)
        xpath_version: Version XPath à utiliser ("1.0" ou "2.0")
        output_format: Format de sortie ("json", "text", "list")
        check_robots: Vérifier robots.txt (default: False)

    Returns:
        Dict avec résultats de l'extraction
    """
    try:
        # Créer crawler avec version XPath spécifiée
        crawler = StealthWebCrawler(xpath_version=xpath_version)

        # Créer source temporaire
        source = XPathSource(
            id=f"direct_{hash(url)}_{hash(xpath)}",
            name="Direct Scrape",
            url=url,
            xpath=xpath,
            description=f"Direct extraction with XPath {xpath_version}",
            category="direct",
            refresh_interval_hours=0,
            created_at=datetime.now(),
            last_validated=None,
            validation_status="pending",
            last_error=None,
            enabled=True
        )

        # Valider sans robots.txt si check_robots=False
        if not check_robots:
            validation = crawler.validate_xpath(source, check_robots=False)
            if not validation.success:
                raise ValueError(f"XPath validation failed: {validation.error}")
            result = crawler.scrape(source, validate_first=False)
        else:
            # Mode strict avec robots.txt
            result = crawler.scrape(source, validate_first=True)

        # Formater selon output_format
        if output_format == "text":
            # Joindre avec newlines
            formatted_data = "\n".join(result.data)
        elif output_format == "list":
            # Liste brute
            formatted_data = result.data
        else:  # json
            # Données structurées avec métadonnées
            formatted_data = {
                "items": result.data,
                "metadata": result.metadata
            }

        return {
            "success": True,
            "xpath_version": xpath_version,
            "url": url,
            "xpath": xpath,
            "count": len(result.data),
            "data": formatted_data,
            "scrape_id": result.scrape_id,
            "scraped_at": result.scraped_at.isoformat(),
            "response_time_ms": result.metadata.get("response_time_ms"),
            "message": f"Extracted {len(result.data)} elements using XPath {xpath_version}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "xpath_version": xpath_version,
            "url": url,
            "xpath": xpath,
            "message": f"Direct scrape failed: {str(e)}"
        }


def batch_scrape(
    sources: List[Dict[str, str]],
    xpath_version: str = "2.0"
) -> List[Dict[str, Any]]:
    """
    Extraction batch de plusieurs sources

    Args:
        sources: Liste de dicts avec {url, xpath, name (optional)}
        xpath_version: Version XPath

    Returns:
        Liste de résultats
    """
    results = []

    for i, source_config in enumerate(sources, 1):
        url = source_config["url"]
        xpath = source_config["xpath"]
        name = source_config.get("name", f"Source {i}")

        print(f"[{i}/{len(sources)}] Scraping {name}...")

        result = direct_scrape(url, xpath, xpath_version, output_format="json")
        result["source_name"] = name

        results.append(result)

        if result["success"]:
            print(f"  ✅ Extracted {result['count']} elements")
        else:
            print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")

    return results


# CLI usage
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="Direct XPath scraping without LLM"
    )
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("xpath", help="XPath expression")
    parser.add_argument(
        "--xpath-version",
        choices=["1.0", "2.0"],
        default="2.0",
        help="XPath version to use"
    )
    parser.add_argument(
        "--format",
        choices=["json", "text", "list"],
        default="json",
        help="Output format"
    )
    parser.add_argument(
        "--check-robots",
        action="store_true",
        help="Check robots.txt (default: ignore for permissive scraping)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: stdout)"
    )

    args = parser.parse_args()

    # Exécuter scrape
    result = direct_scrape(
        url=args.url,
        xpath=args.xpath,
        xpath_version=args.xpath_version,
        output_format=args.format,
        check_robots=args.check_robots  # Default: False (permissive mode)
    )

    # Afficher ou sauvegarder
    output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✓ Saved to {args.output}")
    else:
        print(output)

    # Exit code selon succès
    sys.exit(0 if result["success"] else 1)
