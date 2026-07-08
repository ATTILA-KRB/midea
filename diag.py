"""
Test TEMPORAIRE des nouveaux identifiants Bright Data.

1. Web Unlocker : recupere la page Amazon et lit le stock.
2. Scraping Browser : connexion CDP + chargement d'une page simple.
A supprimer apres verification.
"""

from connectors import fetch_brightdata, fetch_scraping_browser, parse_amazon


def main():
    print("--- Test Web Unlocker (zone mcp_unlocker) ---", flush=True)
    try:
        html = fetch_brightdata("https://www.amazon.fr/dp/B0CY2YW8BT")
        r = parse_amazon(html, {})
        print(f"  OK : {len(html)} caracteres, lecture stock = {r}", flush=True)
    except Exception as e:
        print(f"  ECHEC : {str(e)[:200]}", flush=True)

    print("--- Test Scraping Browser (zone mcp_browser) ---", flush=True)
    try:
        html = fetch_scraping_browser("https://geo.brdtest.com/welcome.txt")
        apercu = html[:200].replace("\n", " ")
        print(f"  OK : {len(html)} caracteres, apercu = {apercu}", flush=True)
    except Exception as e:
        print(f"  ECHEC : {str(e)[:200]}", flush=True)


if __name__ == "__main__":
    main()
