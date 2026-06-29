"""
Diagnostic TEMPORAIRE cible Castorama (v2) : contexte des marqueurs de stock.

La page contient a la fois "ajouter au panier" et "indisponible" : on extrait
le contexte de chaque occurrence pour trouver un marqueur fiable d'indisponibilite.
A supprimer apres analyse.
"""

import re
from config import SITES
from connectors import get_html

CASTO = next(s for s in SITES if s["nom"] == "Castorama")

PHRASES = [
    "non disponible", "indisponible", "rupture", "plus disponible",
    "n'est plus", "victime de son succes", "bientot de retour",
    "ajouter au panier", "ajouter au panierprix", "add to cart",
    "disabled", "out_of_stock", "outofstock", "instock", "in_stock",
]


def contexts(html, phrase, n=2, width=70):
    low = html.lower()
    out, start = [], 0
    while len(out) < n:
        i = low.find(phrase, start)
        if i == -1:
            break
        snippet = re.sub(r"\s+", " ", html[max(0, i - width): i + len(phrase) + width])
        out.append(snippet)
        start = i + len(phrase)
    return out


def main():
    html = get_html(CASTO)
    print(f"taille HTML : {len(html)}", flush=True)
    low = html.lower()
    for p in PHRASES:
        c = low.count(p)
        if c:
            print(f"\n=== '{p}' x{c} ===", flush=True)
            for s in contexts(html, p):
                print(f"   …{s}…", flush=True)


if __name__ == "__main__":
    main()
