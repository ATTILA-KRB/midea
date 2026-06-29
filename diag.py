"""
Diagnostic TEMPORAIRE cible Optimea (revendeur officiel, WooCommerce).

Determine le bon mode d'acces (direct vs brightdata) et le bon signal de stock.
A supprimer apres analyse.
"""

import re
import json
from config import SITES
from connectors import fetch_direct, fetch_brightdata

OPTIMEA = next(s for s in SITES if s["nom"] == "Optimea")
URL = OPTIMEA["url"]

PHRASES = [
    "rupture de stock", "rupture", "stock epuise", "épuisé", "indisponible",
    "ajouter au panier", "add to cart", "out-of-stock", "outofstock",
    "in-stock", "instock", "en stock", "disponible", "précommande", "sold out",
]


def inspecte(html, source):
    print(f"\n########## {source} : {len(html)} caracteres ##########", flush=True)
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    print(f"<title> : {(m.group(1).strip()[:120] if m else '(aucun)')}", flush=True)

    avails = re.findall(r'"availability"\s*:\s*"([^"]+)"', html)
    print(f"availability JSON-LD ({len(avails)}) : {avails}", flush=True)

    micro = re.findall(r'<(?:link|meta)[^>]*itemprop="availability"[^>]*>', html, re.IGNORECASE)
    print(f"microdata availability : {micro[:2]}", flush=True)

    low = html.lower()
    for p in PHRASES:
        c = low.count(p)
        if c:
            i = low.find(p)
            ctx = re.sub(r"\s+", " ", html[max(0, i - 60): i + len(p) + 60])
            print(f"  '{p}' x{c} : …{ctx}…", flush=True)


def main():
    # 1) Essai direct
    try:
        html = fetch_direct(URL)
        inspecte(html, "DIRECT")
        return
    except Exception as e:
        print(f"DIRECT echoue : {str(e)[:120]}", flush=True)

    # 2) Repli Bright Data
    try:
        html = fetch_brightdata(URL)
        inspecte(html, "BRIGHTDATA")
    except Exception as e:
        print(f"BRIGHTDATA echoue : {str(e)[:160]}", flush=True)


if __name__ == "__main__":
    main()
