"""
Diagnostic TEMPORAIRE Optimea via le Bright Data Scraping Browser.

Recupere la page rendue (navigateur reel) et cherche le signal de stock fiable.
A supprimer apres analyse.
"""

import re
from config import SITES
from connectors import fetch_scraping_browser

OPTIMEA = next(s for s in SITES if s["nom"] == "Optimea")
URL = OPTIMEA["url"]

PHRASES = [
    "rupture de stock", "rupture", "stock epuise", "épuisé", "indisponible",
    "ajouter au panier", "add-to-cart", "single_add_to_cart_button",
    "out-of-stock", "outofstock", "in-stock", "instock", "en stock",
    "disponible", "précommande", "sold out", "disabled",
]


def main():
    html = fetch_scraping_browser(URL)
    print(f"taille HTML : {len(html)}", flush=True)

    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    print(f"<title> : {(m.group(1).strip()[:140] if m else '(aucun)')}", flush=True)

    avails = re.findall(r'"availability"\s*:\s*"([^"]+)"', html)
    print(f"availability JSON-LD ({len(avails)}) : {avails}", flush=True)

    micro = re.findall(r'<(?:link|meta)[^>]*itemprop="availability"[^>]*>', html, re.IGNORECASE)
    print(f"microdata availability : {micro[:3]}", flush=True)

    # WooCommerce : <p class="stock in-stock">En stock</p> / <p class="stock out-of-stock">
    for mm in re.findall(r'<p[^>]*class="[^"]*stock[^"]*"[^>]*>.*?</p>', html, re.IGNORECASE | re.DOTALL)[:3]:
        bloc = re.sub(r"\s+", " ", mm)[:160]
        print(f"  bloc stock : {bloc}", flush=True)

    low = html.lower()
    for p in PHRASES:
        c = low.count(p)
        if c:
            i = low.find(p)
            ctx = re.sub(r"\s+", " ", html[max(0, i - 55): i + len(p) + 55])
            print(f"  '{p}' x{c} : …{ctx}…", flush=True)


if __name__ == "__main__":
    main()
