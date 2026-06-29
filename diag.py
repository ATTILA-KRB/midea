"""
Diagnostic TEMPORAIRE cible Darty (via Bright Data).

Darty renvoie "availability absente du JSON-LD" : on inspecte sa page pour
trouver un signal fiable de disponibilite. A supprimer apres analyse.
"""

import re
import json
from config import SITES
from connectors import get_html

DARTY = next(s for s in SITES if s["nom"] == "Darty")

PHRASES = [
    "ajouter au panier", "indisponible", "rupture", "epuise", "épuisé",
    "non disponible", "plus disponible", "ajouter au panierprix",
    "add to cart", "disabled", "outofstock", "out_of_stock", "instock",
    "in_stock", "en stock", "produit non disponible", "victime de son succes",
]


def contexts(html, phrase, n=2, width=70):
    low = html.lower()
    out, start = [], 0
    while len(out) < n:
        i = low.find(phrase, start)
        if i == -1:
            break
        out.append(re.sub(r"\s+", " ", html[max(0, i - width): i + len(phrase) + width]))
        start = i + len(phrase)
    return out


def main():
    html = get_html(DARTY)
    print(f"taille HTML : {len(html)}", flush=True)

    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    print(f"<title> : {(m.group(1).strip()[:120] if m else '(aucun)')}", flush=True)

    avails = re.findall(r'"availability"\s*:\s*"([^"]+)"', html)
    print(f"availability JSON-LD ({len(avails)}) : {avails}", flush=True)

    blocks = re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
                        html, re.DOTALL)
    print(f"blocs JSON-LD : {len(blocks)}", flush=True)
    for i, b in enumerate(blocks):
        try:
            data = json.loads(b.strip())
            t = data.get("@type") if isinstance(data, dict) else type(data).__name__
            print(f"  [{i}] @type={t}", flush=True)
        except Exception:
            print(f"  [{i}] (JSON invalide)", flush=True)

    low = html.lower()
    for p in PHRASES:
        c = low.count(p)
        if c:
            print(f"\n=== '{p}' x{c} ===", flush=True)
            for s in contexts(html, p):
                print(f"   …{s}…", flush=True)


if __name__ == "__main__":
    main()
