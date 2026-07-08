"""
Test TEMPORAIRE complet apres remise en etat des cles.

1. Web Unlocker (cle API)   : recupere Amazon et lit le stock.
2. Scraping Browser         : connexion CDP + page simple.
3. Email Resend             : envoie une alerte de test.
A supprimer apres verification.
"""

from connectors import fetch_brightdata, fetch_scraping_browser, parse_amazon
from alert import envoyer_alerte
from config import PRIX_CIBLE


def main():
    print("--- 1. Web Unlocker (cle API) ---", flush=True)
    try:
        html = fetch_brightdata("https://www.amazon.fr/dp/B0CY2YW8BT")
        r = parse_amazon(html, {})
        print(f"  OK : {len(html)} caracteres, lecture stock = {r}", flush=True)
    except Exception as e:
        print(f"  ECHEC : {str(e)[:200]}", flush=True)

    print("--- 2. Scraping Browser ---", flush=True)
    try:
        html = fetch_scraping_browser("https://geo.brdtest.com/welcome.txt")
        print(f"  OK : {len(html)} caracteres", flush=True)
    except Exception as e:
        print(f"  ECHEC : {str(e)[:200]}", flush=True)

    print("--- 3. Email Resend ---", flush=True)
    faux = [{"nom": "TEST cles reparees (a ignorer)", "url": "https://www.example.com",
             "disponible": True, "prix": 999.0, "erreur": None}]
    ok = envoyer_alerte(faux, PRIX_CIBLE)
    print(f"  envoi email : {ok}", flush=True)


if __name__ == "__main__":
    main()
