"""
Diagnostic TEMPORAIRE cible Castorama.

Le moniteur affiche "EN STOCK" alors que le produit est en realite indisponible :
on inspecte la page pour comprendre ce que le parser lit a tort.

Affiche :
  - toutes les valeurs "availability" trouvees dans le JSON-LD
  - le nombre de blocs JSON-LD et un apercu de chacun
  - la presence de marqueurs texte de stock (rupture / indisponible / panier ...)

A supprimer apres analyse.
"""

import re
import json
from config import SITES
from connectors import get_html

CASTO = next(s for s in SITES if s["nom"] == "Castorama")


def main():
    html = get_html(CASTO)
    print(f"taille HTML : {len(html)}", flush=True)

    # Tous les availability bruts
    avails = re.findall(r'"availability"\s*:\s*"([^"]+)"', html)
    print(f"availability trouves ({len(avails)}) : {avails}", flush=True)

    # Marqueurs texte
    low = html.lower()
    for m in ["rupture", "indisponible", "epuise", "épuisé", "ajouter au panier",
              "retrait en magasin", "click & collect", "livraison",
              "out of stock", "in stock", "non disponible", "stock epuise"]:
        if m in low:
            print(f"  marqueur present : '{m}'", flush=True)

    # Apercu des blocs JSON-LD (tronques) pour voir la structure
    blocks = re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
                        html, re.DOTALL)
    print(f"\nblocs JSON-LD : {len(blocks)}", flush=True)
    for i, b in enumerate(blocks):
        raw = b.strip()
        try:
            data = json.loads(raw)
            t = data.get("@type") if isinstance(data, dict) else type(data).__name__
            offers = json.dumps(data.get("offers")) if isinstance(data, dict) else ""
            print(f"  [{i}] @type={t} offers={offers[:300]}", flush=True)
        except Exception as e:
            print(f"  [{i}] (JSON invalide: {str(e)[:60]}) apercu={raw[:200]}", flush=True)


if __name__ == "__main__":
    main()
