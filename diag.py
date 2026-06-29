"""
Script de diagnostic TEMPORAIRE.

Pour chaque site protege (methode brightdata), recupere le HTML via Bright Data
et affiche de quoi comprendre pourquoi le parser ne lit pas le stock :
  - taille du HTML recu
  - <title> de la page
  - presence de blocs JSON-LD et si "availability" y figure
  - marqueurs anti-bot / consentement eventuels

Ne fait AUCUNE alerte, ne touche pas a l'etat. A supprimer apres analyse.
"""

import re
from config import SITES
from connectors import get_html


def _title(html):
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    return (m.group(1).strip()[:120] if m else "(aucun <title>)")


def _flags(html):
    low = html.lower()
    marqueurs = ["captcha", "datadome", "px-captcha", "robot", "are you human",
                 "consent", "cookie", "access denied", "forbidden", "cloudflare"]
    return [m for m in marqueurs if m in low]


def diag(site):
    print(f"\n===== {site['nom']} ({site['method']}) =====", flush=True)
    print(f"URL: {site['url']}", flush=True)
    try:
        html = get_html(site)
    except Exception as e:
        print(f"  ERREUR fetch: {str(e)[:200]}", flush=True)
        return

    print(f"  taille HTML       : {len(html)} caracteres", flush=True)
    print(f"  <title>           : {_title(html)}", flush=True)

    blocks = re.findall(r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>",
                        html, re.DOTALL)
    print(f"  blocs JSON-LD     : {len(blocks)}", flush=True)
    print(f"  'availability'    : {'oui' if 'availability' in html else 'NON'}", flush=True)
    print(f"  'InStock'/'OutOf' : InStock={'InStock' in html} OutOfStock={'OutOfStock' in html}", flush=True)

    # Extrait la 1ere occurrence d'availability pour voir la forme exacte
    a = re.search(r'"availability"\s*:\s*"([^"]+)"', html)
    if a:
        print(f"  -> availability brut: {a.group(1)}", flush=True)

    flags = _flags(html)
    if flags:
        print(f"  ⚠ marqueurs detectes: {', '.join(flags)}", flush=True)

    # Apercu du tout debut du HTML (utile pour reperer une page d'erreur)
    apercu = re.sub(r"\s+", " ", html[:300]).strip()
    print(f"  debut HTML        : {apercu}", flush=True)


def main():
    for site in SITES:
        if site.get("method") == "brightdata" and site.get("enabled", True):
            diag(site)


if __name__ == "__main__":
    main()
