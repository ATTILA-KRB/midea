"""
Diagnostic TEMPORAIRE : contre-epreuve du signal Amazon du 03/07 a 10h24.

Analyse la page Amazon ACTUELLE (produit epuise) pour verifier si les signaux
qui ont declenche l'alerte (mot 'buybox', prix 'a-price-whole') sont deja
presents sur une page indisponible -> si oui, l'alerte de 10h24 etait
probablement un faux positif de l'ancien parser. A supprimer apres analyse.
"""

import re
from connectors import fetch_brightdata

URL = "https://www.amazon.fr/dp/B0CY2YW8BT"

PHRASES_INDISPO = [
    "actuellement indisponible",
    "temporairement en rupture",
    "nous ne savons pas quand cet article sera de nouveau",
]


def main():
    html = fetch_brightdata(URL)
    low = html.lower()
    print(f"taille HTML : {len(html)}", flush=True)

    print("\n--- Phrases d'indisponibilite presentes ? ---", flush=True)
    for p in PHRASES_INDISPO:
        print(f"  '{p}' : {'OUI' if p in low else 'non'}", flush=True)

    print("\n--- Signaux positifs de l'ANCIEN parser ---", flush=True)
    for p in ["buybox", "add-to-cart-button", "buy-now-button"]:
        c = low.count(p)
        print(f"  substring '{p}' : x{c}", flush=True)

    print("\n--- Signaux positifs du NOUVEAU parser (id exact) ---", flush=True)
    for p in [r'id="add-to-cart-button"', r'id="buy-now-button"']:
        c = len(re.findall(p, html))
        print(f"  {p} : x{c}", flush=True)

    print("\n--- Prix a-price-whole presents sur la page (5 premiers) ---", flush=True)
    prix = re.findall(r'a-price-whole">([0-9\s.,]+)<', html)[:5]
    print(f"  {prix}", flush=True)

    # Contexte du premier prix pour voir a quel produit il appartient
    m = re.search(r'.{160}a-price-whole">[0-9\s.,]+<', html, re.DOTALL)
    if m:
        ctx = re.sub(r"\s+", " ", m.group(0))
        print(f"\n  contexte 1er prix : …{ctx}…", flush=True)


if __name__ == "__main__":
    main()
