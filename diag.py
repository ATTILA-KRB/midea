"""
Script de diagnostic TEMPORAIRE (v2).

Interroge directement l'API Bright Data pour UN site et affiche tout :
  - statut HTTP exact
  - en-tetes de reponse (dont les en-tetes d'erreur Bright Data x-brd-*)
  - taille et apercu du corps

Objectif : comprendre pourquoi le corps revient vide. A supprimer apres analyse.
"""

import os
import json
import requests

TOKEN = os.environ.get("BRIGHTDATA_TOKEN", "")
ZONE = os.environ.get("BRIGHTDATA_ZONE", "")

URL_TEST = "https://www.amazon.fr/dp/B0CY2YW8BT"


def essai(payload, label):
    print(f"\n========== Essai : {label} ==========", flush=True)
    print(f"payload: {json.dumps({k: v for k, v in payload.items()})}", flush=True)
    try:
        r = requests.post(
            "https://api.brightdata.com/request",
            headers={"Authorization": f"Bearer {TOKEN}",
                     "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
    except Exception as e:
        print(f"  EXCEPTION: {str(e)[:200]}", flush=True)
        return
    print(f"  status_code : {r.status_code}", flush=True)
    print(f"  taille corps: {len(r.text)}", flush=True)
    # En-tetes utiles (erreurs Bright Data + content-type)
    interessants = {k: v for k, v in r.headers.items()
                    if k.lower().startswith("x-") or k.lower() in
                    ("content-type", "content-length", "content-encoding")}
    print(f"  en-tetes    : {json.dumps(interessants)}", flush=True)
    apercu = r.text[:500].replace("\n", " ")
    print(f"  apercu corps: {apercu}", flush=True)


def main():
    print(f"ZONE configuree (longueur): {len(ZONE)} | TOKEN present: {bool(TOKEN)}", flush=True)

    # 1. Tel que le code actuel l'envoie
    essai({"zone": ZONE, "url": URL_TEST, "format": "raw", "country": "fr"},
          "format=raw + country=fr (actuel)")

    # 2. Sans country
    essai({"zone": ZONE, "url": URL_TEST, "format": "raw"},
          "format=raw sans country")

    # 3. format json (Bright Data renvoie un objet avec le body dedans)
    essai({"zone": ZONE, "url": URL_TEST, "format": "json"},
          "format=json")

    # 4. Avec method GET explicite
    essai({"zone": ZONE, "url": URL_TEST, "format": "raw", "method": "GET"},
          "format=raw + method=GET")


if __name__ == "__main__":
    main()
