"""
Diagnostic TEMPORAIRE multi-sites : Fnac, Rakuten, hemmera.fr.

Pour chaque candidat :
  1. tente l'acces direct, sinon Bright Data Web Unlocker
  2. affiche les signaux de stock disponibles (JSON-LD, microdata, boutons, textes)

Objectif : choisir la methode d'acces et le parser pour chaque nouveau site.
A supprimer apres analyse.
"""

import re
from connectors import fetch_direct, fetch_brightdata

CANDIDATS = [
    {
        "nom": "Fnac",
        "url": "https://www.fnac.com/MIDEA-Climatiseur-Split-Mobile-Reversible-Froid-Chaud-3500W-12000BTU-WiFi-deshumidificateur-ventilateur-jusqu-a-40m2-kit-fenetre-inclus/a21457105/w-4",
    },
    {
        "nom": "Rakuten",
        "url": "https://fr.shopping.rakuten.com/offer/buy/13466164647/clim-reversible-optimea-mmcs-12hrn8-qrd0.html",
    },
    {
        "nom": "hemmera",
        "url": "https://www.hemmera.fr/climatiseur-portable-midea-mmcs-12hrn8-3-5-kw.-pompe-a-chaleur-r32-kit-inclus/",
    },
]

PHRASES = [
    "rupture", "indisponible", "epuise", "épuisé", "non disponible",
    "ajouter au panier", "add to cart", "acheter", "disabled",
    "outofstock", "out-of-stock", "out_of_stock", "instock", "in-stock",
    "en stock", "sold out", "victime de son succes", "précommande",
]


def inspecte(html, nom):
    print(f"  taille HTML : {len(html)}", flush=True)
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    print(f"  <title> : {(m.group(1).strip()[:130] if m else '(aucun)')}", flush=True)

    avails = re.findall(r'"availability"\s*:\s*"([^"]+)"', html)
    print(f"  availability JSON-LD ({len(avails)}) : {avails[:6]}", flush=True)

    micro = re.findall(r'<(?:link|meta)[^>]*itemprop="availability"[^>]*>', html, re.IGNORECASE)
    print(f"  microdata availability : {micro[:2]}", flush=True)

    low = html.lower()
    for p in PHRASES:
        c = low.count(p)
        if c:
            i = low.find(p)
            ctx = re.sub(r"\s+", " ", html[max(0, i - 55): i + len(p) + 55])
            print(f"  '{p}' x{c} : …{ctx}…", flush=True)


def main():
    for site in CANDIDATS:
        print(f"\n########## {site['nom']} ##########", flush=True)
        print(f"URL : {site['url']}", flush=True)
        html = None
        try:
            html = fetch_direct(site["url"])
            print("  acces : DIRECT OK", flush=True)
        except Exception as e:
            print(f"  direct echoue : {str(e)[:100]}", flush=True)
            try:
                html = fetch_brightdata(site["url"])
                print("  acces : BRIGHTDATA OK", flush=True)
            except Exception as e2:
                print(f"  brightdata echoue : {str(e2)[:140]}", flush=True)
        if html:
            inspecte(html, site["nom"])


if __name__ == "__main__":
    main()
