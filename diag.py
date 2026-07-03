"""
Diagnostic TEMPORAIRE : detecter le signal "pre-commande" sur hemmera.

Le site affiche "En stock" mais l'ajout au panier est bloque jusqu'au
26 aout 2026. On cherche ou cette date / ce blocage apparait dans le HTML.
A supprimer apres analyse.
"""

import re
from config import SITES
from connectors import fetch_direct

HEMMERA = next(s for s in SITES if s["nom"] == "hemmera")


def contexte(html, phrase, n=3, width=140):
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
    html = fetch_direct(HEMMERA["url"])
    print(f"taille HTML : {len(html)}", flush=True)

    for p in ["sera disponible", "disponible le", "avail_since", "avail-since",
              "2026", "Aoû", "aout", "août", "pre-commande", "précommande",
              "preorder", "pre-order", "buy_now", "ty-btn__add", "add_to_cart",
              "ne peut être ajouté", "ne peut etre ajoute", "coming-soon",
              "out-of-stock", "prochainement"]:
        occ = contexte(html, p)
        if occ:
            print(f"\n=== '{p}' x{len(occ)}+ ===", flush=True)
            for s in occ:
                print(f"   …{s}…", flush=True)


if __name__ == "__main__":
    main()
