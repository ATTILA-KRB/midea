"""
Diagnostic TEMPORAIRE : pourquoi hemmera renvoie "champ stock introuvable".

Affiche taille, titre et marqueurs cles de la page recue en direct.
A supprimer apres analyse.
"""

import re
from config import SITES
from connectors import fetch_direct

HEMMERA = next(s for s in SITES if s["nom"] == "hemmera")


def main():
    try:
        html = fetch_direct(HEMMERA["url"])
    except Exception as e:
        print(f"fetch echoue : {str(e)[:200]}", flush=True)
        return

    print(f"taille HTML : {len(html)}", flush=True)
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    print(f"<title> : {(m.group(1).strip()[:140] if m else '(aucun)')}", flush=True)

    low = html.lower()
    for p in ["in_stock_info", "ty-qty-in-stock", "midea", "portasplit",
              "captcha", "cloudflare", "access denied", "robot", "blocked",
              "maintenance", "404", "introuvable", "coming-soon"]:
        c = low.count(p)
        if c:
            i = low.find(p)
            ctx = re.sub(r"\s+", " ", html[max(0, i - 60): i + len(p) + 60])
            print(f"  '{p}' x{c} : …{ctx[:150]}…", flush=True)

    apercu = re.sub(r"\s+", " ", html[:400])
    print(f"\ndebut HTML : {apercu}", flush=True)


if __name__ == "__main__":
    main()
