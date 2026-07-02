"""
Diagnostic TEMPORAIRE cible Rakuten (marketplace).

La page n'a pas de JSON-LD availability : on cherche un signal fiable
(bouton panier reel vs template, prix, nombre d'offres neuves).
A supprimer apres analyse.
"""

import re
from connectors import fetch_direct

URL = "https://fr.shopping.rakuten.com/offer/buy/13466164647/clim-reversible-optimea-mmcs-12hrn8-qrd0.html"


def contexte(html, phrase, n=3, width=110):
    low = html.lower()
    out, start = [], 0
    while len(out) < n:
        i = low.find(phrase.lower(), start)
        if i == -1:
            break
        out.append(re.sub(r"\s+", " ", html[max(0, i - width): i + len(phrase) + width]))
        start = i + len(phrase)
    return out


def main():
    html = fetch_direct(URL)
    print(f"taille HTML : {len(html)}", flush=True)

    # Signaux candidats specifiques Rakuten
    for p in ["addToCartBtn", "advertList", "buybox", "salePrice",
              "advertPrice", "\"price\"", "nbAdverts", "aucune offre",
              "voir les offres", "neuf des", "occasion des",
              "productBuyBox", "prdBuy", "isSoldOut", "soldout"]:
        occ = contexte(html, p)
        if occ:
            print(f"\n=== '{p}' x{len(occ)}+ ===", flush=True)
            for s in occ:
                print(f"   …{s}…", flush=True)


if __name__ == "__main__":
    main()
