"""
Diagnostic TEMPORAIRE : verifier la fiabilite du "EN STOCK" de hemmera.

Extrait : nom exact du produit, prix, quantite en stock, etat du bouton
d'achat, et le JSON-LD complet de l'offre. A supprimer apres analyse.
"""

import re
import json
from config import SITES
from connectors import fetch_direct

HEMMERA = next(s for s in SITES if s["nom"] == "hemmera")


def contexte(html, phrase, n=2, width=130):
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

    # Nom exact du produit (h1)
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
    if h1:
        print(f"h1 produit : {re.sub(r'<[^>]+>', '', h1.group(1)).strip()[:160]}", flush=True)

    # JSON-LD complet des offres
    blocks = re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.DOTALL)
    for b in blocks:
        try:
            data = json.loads(b.strip())
            txt = json.dumps(data, ensure_ascii=False)
            if "availability" in txt or "price" in txt.lower():
                print(f"JSON-LD offre : {txt[:600]}", flush=True)
        except Exception:
            pass

    # Signaux CS-Cart : quantite, bouton, prix
    for p in ["ty-qty-in-stock", "in_stock_info", "ty-price-num", "buy_now",
              "add-to-cart", "En stock", "Rupture", "portasplit", "PortaSplit",
              "QRD0", "kit fenetre", "kit fenêtre", "unite exterieure", "unité extérieure"]:
        occ = contexte(html, p)
        if occ:
            print(f"\n=== '{p}' ===", flush=True)
            for s in occ:
                print(f"   …{s}…", flush=True)


if __name__ == "__main__":
    main()
