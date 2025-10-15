#!/usr/bin/env python3
"""
Test pour trouver l'API Forbes des billionaires
"""

import requests
import json

# URLs potentielles de l'API Forbes
api_urls = [
    "https://www.forbes.com/forbesapi/person/rtb/0/position/true.json",
    "https://www.forbes.com/ajax/list/data?year=2024&uri=billionaires",
    "https://www.forbes.com/billionaires/api/",
    "https://www.forbes.com/real-time-billionaires/api/data",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.forbes.com/real-time-billionaires/'
}

print("=" * 80)
print("Searching for Forbes Billionaires API")
print("=" * 80)
print()

for url in api_urls:
    print(f"Testing: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            print(f"  ✅ SUCCESS!")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
            print(f"  Content length: {len(response.text)} bytes")

            # Essayer de parser le JSON
            try:
                data = response.json()
                print(f"  JSON structure:")
                if isinstance(data, dict):
                    print(f"    Keys: {list(data.keys())[:10]}")
                elif isinstance(data, list):
                    print(f"    Array length: {len(data)}")
                    if len(data) > 0:
                        print(f"    First item keys: {list(data[0].keys())[:10]}")

                # Sauvegarder un échantillon
                print(f"  Sample data (first 500 chars):")
                print(f"  {json.dumps(data, indent=2)[:500]}...")
                print()

                # Sauvegarder la réponse complète
                with open('forbes_api_response.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"  💾 Full response saved to forbes_api_response.json")

            except json.JSONDecodeError as e:
                print(f"  ⚠️  Not valid JSON: {e}")
                print(f"  Content preview: {response.text[:200]}")
        else:
            print(f"  ❌ HTTP {response.status_code}")

    except requests.Timeout:
        print(f"  ⏱️  Timeout")
    except requests.RequestException as e:
        print(f"  ❌ Error: {e}")

    print()

print()
print("=" * 80)
print("Additional attempt: Check Network tab patterns")
print("=" * 80)
print()
print("The Forbes page uses AngularJS which likely calls an API endpoint.")
print("To find it:")
print("1. Open https://www.forbes.com/real-time-billionaires/ in browser")
print("2. Open DevTools (F12) → Network tab")
print("3. Filter by 'XHR' or 'Fetch'")
print("4. Reload the page")
print("5. Look for API calls with 'billionaire', 'rtb', or 'person' in URL")
print()
print("Common Forbes API patterns:")
print("  - /forbesapi/person/rtb/...")
print("  - /ajax/list/data...")
print("  - /api/...")
