#!/usr/bin/env python3
"""
Test simple Forbes avec timeout court et XPath 2.0
"""

from cortex.departments.intelligence import StealthWebCrawler
from cortex.departments.intelligence.stealth_web_crawler import XPathSource
from datetime import datetime
import requests

def test_forbes_quick():
    """Test rapide de la structure Forbes"""

    url = "https://www.forbes.com/real-time-billionaires/"

    print("=" * 80)
    print("Test rapide Forbes")
    print("=" * 80)
    print(f"URL: {url}")
    print()

    # D'abord, vérifier si on peut même atteindre la page
    print("1. Test de connexion basique...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)} bytes")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        print()

        # Afficher un extrait du HTML
        print("2. Extrait du HTML reçu (premiers 500 chars):")
        print("-" * 80)
        print(response.text[:500])
        print("-" * 80)
        print()

        # Chercher des indices de structure
        print("3. Analyse de la structure:")
        if "billionaire" in response.text.lower():
            print("   ✅ Le mot 'billionaire' est présent")
        else:
            print("   ❌ Le mot 'billionaire' n'est PAS présent")

        if "<table" in response.text:
            print("   ✅ Des tables HTML sont présentes")
            # Compter les tables
            table_count = response.text.count("<table")
            print(f"   Nombre de tables: {table_count}")
        else:
            print("   ❌ Aucune table HTML trouvée")

        if "react" in response.text.lower() or "vue" in response.text.lower():
            print("   ⚠️  Page utilise un framework JS (React/Vue)")
            print("   → Le contenu est chargé dynamiquement")

        if "window.__INITIAL_STATE__" in response.text or "window.__PRELOADED_STATE__" in response.text:
            print("   ✅ État initial JS trouvé - données peuvent être dans le JSON!")

        print()

    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        print()
        return

    # Maintenant tester avec le crawler
    print("4. Test avec StealthWebCrawler...")
    crawler = StealthWebCrawler()

    # XPaths simples à tester (XPath 1.0 compatible)
    test_xpaths = [
        "//title",
        "//h1",
        "//body",
        "/html/head/title",
        "/html/body//h1",
    ]

    for xpath in test_xpaths:
        print(f"   Testing: {xpath}")
        source = XPathSource(
            id=f"test_{hash(xpath)}",
            name="Test",
            url=url,
            xpath=xpath,
            description="Test",
            category="test",
            refresh_interval_hours=0,
            created_at=datetime.now(),
            last_validated=None,
            validation_status="pending",
            last_error=None,
            enabled=True
        )

        try:
            result = crawler.validate_xpath(source)
            if result.success and result.elements_found > 0:
                print(f"   ✅ SUCCESS: {result.elements_found} elements")
                if result.sample_data:
                    for sample in result.sample_data[:1]:
                        preview = sample[:100] if len(sample) > 100 else sample
                        print(f"      → {preview}")
            else:
                print(f"   ❌ FAILED: {result.error}")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        print()

if __name__ == "__main__":
    test_forbes_quick()
