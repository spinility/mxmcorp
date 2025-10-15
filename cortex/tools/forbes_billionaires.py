#!/usr/bin/env python3
"""
Forbes Billionaires API Tool

Accès direct à l'API Forbes Real-Time Billionaires
Pas besoin de XPath ou de scraping - données JSON structurées!

IMPORTANT: Forbes.com charge ses données via JavaScript (AngularJS).
Le scraping XPath ne fonctionne PAS car le HTML initial est vide.
Cette API accède directement aux données JSON que Forbes utilise.
"""

from typing import Dict, Any, List, Optional
import requests
import json
from cortex.tools.standard_tool import StandardTool


FORBES_API_URL = "https://www.forbes.com/forbesapi/person/rtb/0/position/true.json"


def get_all_billionaires(max_results: Optional[int] = None) -> Dict[str, Any]:
    """
    Récupère tous les billionaires depuis l'API Forbes

    Args:
        max_results: Limite le nombre de résultats (None = tous)

    Returns:
        Dict avec liste des billionaires
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.forbes.com/real-time-billionaires/'
        }

        response = requests.get(FORBES_API_URL, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        all_billionaires = data['personList']['personsLists']

        # Limiter si demandé
        if max_results:
            all_billionaires = all_billionaires[:max_results]

        return {
            "success": True,
            "count": len(all_billionaires),
            "total_available": len(data['personList']['personsLists']),
            "billionaires": all_billionaires,
            "message": f"Retrieved {len(all_billionaires)} billionaires"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to fetch billionaires: {str(e)}"
        }


def get_billionaire_by_rank(rank: int) -> Dict[str, Any]:
    """
    Récupère un billionaire par son rang

    Args:
        rank: Rang du billionaire (1 = le plus riche)

    Returns:
        Dict avec info du billionaire
    """
    try:
        result = get_all_billionaires(max_results=rank)

        if not result["success"]:
            return result

        if rank > len(result["billionaires"]):
            return {
                "success": False,
                "error": f"Rank {rank} exceeds total count {result['total_available']}",
                "message": f"Only {result['total_available']} billionaires available"
            }

        billionaire = result["billionaires"][rank - 1]

        return {
            "success": True,
            "rank": rank,
            "billionaire": billionaire,
            "message": f"Found billionaire at rank {rank}: {billionaire['personName']}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to fetch billionaire: {str(e)}"
        }


def search_billionaire(name: str, max_results: int = 10) -> Dict[str, Any]:
    """
    Cherche des billionaires par nom

    Args:
        name: Nom à chercher (partiel ok)
        max_results: Nombre max de résultats

    Returns:
        Dict avec liste des billionaires matchant
    """
    try:
        result = get_all_billionaires()

        if not result["success"]:
            return result

        name_lower = name.lower()
        matches = [
            b for b in result["billionaires"]
            if name_lower in b["personName"].lower()
        ]

        matches = matches[:max_results]

        return {
            "success": True,
            "count": len(matches),
            "search_term": name,
            "billionaires": matches,
            "message": f"Found {len(matches)} billionaires matching '{name}'"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Search failed: {str(e)}"
        }


def get_top_billionaires(n: int = 10) -> Dict[str, Any]:
    """
    Récupère les N billionaires les plus riches

    Args:
        n: Nombre de billionaires à récupérer

    Returns:
        Dict avec les top billionaires
    """
    try:
        result = get_all_billionaires(max_results=n)

        if not result["success"]:
            return result

        # Formater de manière plus lisible
        formatted = []
        for b in result["billionaires"]:
            formatted.append({
                "rank": b["rank"],
                "name": b["personName"],
                "net_worth_millions": b["finalWorth"],
                "net_worth_billions": round(b["finalWorth"] / 1000, 2),
                "source": b.get("source", "Unknown"),
                "country": b.get("countryOfCitizenship", "Unknown"),
                "industries": b.get("industries", []),
                "age": b.get("age"),
                "gender": b.get("gender"),
            })

        return {
            "success": True,
            "count": len(formatted),
            "billionaires": formatted,
            "message": f"Retrieved top {len(formatted)} billionaires"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to fetch top billionaires: {str(e)}"
        }


# CLI usage
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="Forbes Real-Time Billionaires API"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Top command
    top_parser = subparsers.add_parser("top", help="Get top N billionaires")
    top_parser.add_argument("-n", type=int, default=10, help="Number of billionaires")

    # Rank command
    rank_parser = subparsers.add_parser("rank", help="Get billionaire by rank")
    rank_parser.add_argument("rank", type=int, help="Rank (1 = richest)")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search billionaire by name")
    search_parser.add_argument("name", help="Name to search")
    search_parser.add_argument("-n", type=int, default=10, help="Max results")

    # All command
    all_parser = subparsers.add_parser("all", help="Get all billionaires")
    all_parser.add_argument("--limit", type=int, help="Limit results")
    all_parser.add_argument("-o", "--output", help="Output file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "top":
        result = get_top_billionaires(args.n)
    elif args.command == "rank":
        result = get_billionaire_by_rank(args.rank)
    elif args.command == "search":
        result = search_billionaire(args.name, args.n)
    elif args.command == "all":
        result = get_all_billionaires(args.limit)

        # Save to file if requested
        if args.output and result["success"]:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"✓ Saved {result['count']} billionaires to {args.output}")
            sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)

    # Display result
    print(json.dumps(result, indent=2))

    sys.exit(0 if result["success"] else 1)


def get_all_forbes_tools() -> List[StandardTool]:
    """
    Retourne tous les outils Forbes pour Cortex

    Returns:
        Liste de StandardTool
    """
    return [
        StandardTool(
            name="forbes_top_billionaires",
            description="Get the top N richest billionaires from Forbes Real-Time list. Use this instead of XPath scraping for Forbes!",
            parameters={
                "type": "object",
                "properties": {
                    "n": {
                        "type": "integer",
                        "description": "Number of billionaires to retrieve (default: 10)",
                        "default": 10
                    }
                },
                "required": []
            },
            function=lambda n=10: get_top_billionaires(n),
            category="data"
        ),
        StandardTool(
            name="forbes_get_billionaire_rank",
            description="Get a specific billionaire by their rank (1 = richest person)",
            parameters={
                "type": "object",
                "properties": {
                    "rank": {
                        "type": "integer",
                        "description": "The rank of the billionaire (1-3000+)"
                    }
                },
                "required": ["rank"]
            },
            function=get_billionaire_by_rank,
            category="data"
        ),
        StandardTool(
            name="forbes_search_billionaire",
            description="Search for billionaires by name (e.g., 'Musk', 'Bezos', 'Gates')",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name to search for (partial matches ok)"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["name"]
            },
            function=lambda name, max_results=10: search_billionaire(name, max_results),
            category="data"
        )
    ]
