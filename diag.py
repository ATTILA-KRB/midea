"""
Diagnostic TEMPORAIRE Optimea : l'utilisateur voit 2 options achetables,
le moniteur lit "epuise". On inspecte la page principale ET la page
"Seconde vie" (URL distincte) via le Scraping Browser. A supprimer apres.
"""

import re
from connectors import fetch_scraping_browser, parse_woocommerce

PAGES = [
    ("PRINCIPALE", "https://www.optimea.fr/product/climatiseur-split-mobile-midea/"),
    ("SECONDE VIE", "https://www.optimea.fr/product/seconde-vie-climatiseur-split-mobile-midea-silencieux-reversible-sans-installation/"),
]


def inspecte(nom, url):
    print(f"\n########## {nom} ##########", flush=True)
    print(f"URL : {url}", flush=True)
    try:
        html = fetch_scraping_browser(url)
    except Exception as e:
        print(f"  fetch echoue : {str(e)[:180]}", flush=True)
        return

    print(f"  taille : {len(html)}", flush=True)
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    print(f"  titre : {(m.group(1).strip()[:120] if m else '?')}", flush=True)

    r = parse_woocommerce(html, {})
    print(f"  parse_woocommerce -> {r}", flush=True)

    # Signaux bruts
    for pat, label in [
        (r'class="[^"]*\bout-of-stock\b[^"]*"', "classe out-of-stock"),
        (r'class="[^"]*\bin-stock\b[^"]*"', "classe in-stock"),
        (r'single_add_to_cart_button', "bouton single_add_to_cart"),
        (r'variations_form', "formulaire de variantes"),
        (r'"availability"\s*:\s*"[^"]*"', "availability JSON-LD"),
    ]:
        occ = re.findall(pat, html)
        print(f"  {label} : x{len(occ)}", flush=True)

    # Prix affiches (5 premiers)
    prix = re.findall(r'woocommerce-Price-amount[^>]*>.*?([0-9][0-9 ., ]*)', html)[:5]
    print(f"  prix visibles : {prix}", flush=True)

    # Contexte des libelles de stock
    low = html.lower()
    for p in ["rupture de stock", "en stock", "ajouter au panier", "seconde vie", "options"]:
        c = low.count(p)
        if c:
            i = low.find(p)
            ctx = re.sub(r"\s+", " ", html[max(0, i - 70): i + len(p) + 70])
            print(f"  '{p}' x{c} : …{ctx[:170]}…", flush=True)


def main():
    for nom, url in PAGES:
        inspecte(nom, url)


if __name__ == "__main__":
    main()
