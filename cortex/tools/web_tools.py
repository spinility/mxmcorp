"""
Web Tools - Outils pour accéder au web en temps réel
"""

import requests
from typing import Dict, Any, Optional
from cortex.tools.standard_tool import tool


@tool(
    name="web_search",
    description="Search the web in real-time using DuckDuckGo. Returns search results with titles, URLs, and snippets.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 5)"
            }
        },
        "required": ["query"]
    },
    category="web",
    tags=["search", "web", "real-time"]
)
def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search the web using DuckDuckGo API

    Args:
        query: Search query
        max_results: Maximum results to return

    Returns:
        Dict with search results
    """
    try:
        # Utiliser l'API DuckDuckGo (gratuit, pas de clé nécessaire)
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extraire les résultats
        results = []

        # Abstract (réponse instantanée)
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", "Direct Answer"),
                "snippet": data.get("Abstract"),
                "url": data.get("AbstractURL", "")
            })

        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                    "snippet": topic.get("Text"),
                    "url": topic.get("FirstURL", "")
                })

        if not results:
            return {
                "success": False,
                "error": "No results found. Try a different search query."
            }

        return {
            "success": True,
            "data": {
                "query": query,
                "results": results[:max_results],
                "count": len(results[:max_results])
            }
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Web search failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


@tool(
    name="web_fetch",
    description="Fetch the content of a web page. Returns the text content of the page.",
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch"
            },
            "max_length": {
                "type": "integer",
                "description": "Maximum length of content to return in characters (default: 5000)"
            }
        },
        "required": ["url"]
    },
    category="web",
    tags=["fetch", "web", "content"]
)
def web_fetch(url: str, max_length: int = 5000) -> Dict[str, Any]:
    """
    Fetch content from a web page

    Args:
        url: URL to fetch
        max_length: Maximum content length

    Returns:
        Dict with page content
    """
    try:
        # Headers pour éviter les blocages
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        # Extraire le texte brut (simple, sans parsing HTML avancé)
        content = response.text

        # Limiter la longueur
        if len(content) > max_length:
            content = content[:max_length] + "... [truncated]"

        return {
            "success": True,
            "data": {
                "url": url,
                "content": content,
                "length": len(content),
                "status_code": response.status_code
            }
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Failed to fetch URL: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


@tool(
    name="get_weather",
    description="Get current weather information for a city. Returns temperature, conditions, and forecast.",
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name (e.g., 'Granby' or 'Granby, QC')"
            },
            "format": {
                "type": "string",
                "description": "Response format: 'short' or 'detailed' (default: 'short')"
            }
        },
        "required": ["city"]
    },
    category="weather",
    tags=["weather", "real-time", "temperature"]
)
def get_weather(city: str, format: str = "short") -> Dict[str, Any]:
    """
    Get weather information using wttr.in API (free, no key required)

    Args:
        city: City name
        format: 'short' or 'detailed'

    Returns:
        Dict with weather data
    """
    try:
        # Utiliser wttr.in API (gratuit, excellent pour le terminal)
        # Format: wttr.in/City?format=j1 pour JSON
        url = f"https://wttr.in/{city}"

        if format == "short":
            # Format court, très lisible
            params = {"format": "%C+%t+%w+%h"}  # Condition + Temp + Wind + Humidity
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            weather_text = response.text.strip()

            return {
                "success": True,
                "data": {
                    "city": city,
                    "weather": weather_text,
                    "format": "short"
                },
                "message": f"Météo à {city}: {weather_text}"
            }
        else:
            # Format détaillé avec JSON
            params = {"format": "j1"}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            current = data["current_condition"][0]

            weather_info = {
                "city": city,
                "temperature_c": current["temp_C"],
                "feels_like_c": current["FeelsLikeC"],
                "condition": current["weatherDesc"][0]["value"],
                "humidity": current["humidity"] + "%",
                "wind_kph": current["windspeedKmph"] + " km/h",
                "wind_dir": current["winddir16Point"]
            }

            return {
                "success": True,
                "data": weather_info,
                "message": f"Météo à {city}: {current['temp_C']}°C, {current['weatherDesc'][0]['value']}"
            }

    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Failed to get weather data: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def get_all_web_tools():
    """
    Get all web tools

    Returns:
        List of StandardTool objects
    """
    return [
        web_search,
        web_fetch,
        get_weather
    ]


# Test si exécuté directement
if __name__ == "__main__":
    print("Testing web tools...\n")

    # Test 1: Weather
    print("1. Testing get_weather...")
    result = get_weather.execute(city="Granby, QC", format="short")
    print(f"Result: {result}\n")

    # Test 2: Web search
    print("2. Testing web_search...")
    result = web_search.execute(query="python programming", max_results=3)
    print(f"Result: {result}\n")

    # Test 3: Web fetch
    print("3. Testing web_fetch...")
    result = web_fetch.execute(url="https://example.com", max_length=500)
    print(f"Result: {result}\n")

    print("✓ All tests completed!")
