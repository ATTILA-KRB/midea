"""
Orchestrateur principal du moniteur PortaSplit.

Un appel a main() = un cycle complet :
  1. interroge tous les sites actifs (en parallele)
  2. detecte les transitions de stock
  3. envoie un email si un site repasse en stock
  4. persiste le nouvel etat

Conçu pour etre lance periodiquement, soit par la boucle interne (run_loop.py),
soit par un cron externe (le planificateur du NAS).

Usage :
  python main.py          # un seul cycle
  python main.py --once   # idem, explicite
"""

import sys
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from config import SITES, PRIX_CIBLE, PRODUIT
from connectors import check_site
from state import charger_etat, sauver_etat, detecter_transitions
from alert import envoyer_alerte


def _log(msg):
    horodatage = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{horodatage}] {msg}", flush=True)


def interroger_sites():
    """Lance tous les sites actifs en parallele. Renvoie la liste des resultats."""
    actifs = [s for s in SITES if s.get("enabled", True)]
    resultats = []
    with ThreadPoolExecutor(max_workers=min(8, len(actifs))) as executor:
        futures = {}
        for site in actifs:
            # Petit delai aleatoire pour ne pas frapper tous les sites en meme temps
            time.sleep(random.uniform(0.1, 0.5))
            futures[executor.submit(check_site, site)] = site["nom"]
        for fut in as_completed(futures):
            resultats.append(fut.result())
    # Tri par nom pour un affichage stable
    return sorted(resultats, key=lambda r: r["nom"])


def afficher_resultats(resultats):
    """Affiche un tableau lisible de l'etat courant."""
    for r in resultats:
        if r["disponible"] is True:
            etat = "EN STOCK"
        elif r["disponible"] is False:
            etat = "epuise"
        else:
            etat = "indetermine"
        prix = f"{r['prix']:.0f} EUR" if r.get("prix") else "-"
        err = f"  ({r['erreur']})" if r.get("erreur") else ""
        _log(f"  {r['nom']:14} {etat:12} {prix:>10}{err}")


def cycle():
    """Execute un cycle complet de verification."""
    _log(f"--- Cycle de verification : {PRODUIT} ---")
    etat_precedent = charger_etat()
    resultats = interroger_sites()
    afficher_resultats(resultats)

    alertes, retours, nouvel_etat = detecter_transitions(resultats, etat_precedent)

    for r in retours:
        _log(f"  ! {r['nom']} repasse en rupture")

    if alertes:
        noms = ", ".join(a["nom"] for a in alertes)
        _log(f">>> TRANSITION EN STOCK detectee : {noms}")
        envoyer_alerte(alertes, PRIX_CIBLE)
    else:
        _log("  aucune nouvelle disponibilite")

    sauver_etat(nouvel_etat)
    _log("--- Fin du cycle ---")
    return resultats


def main():
    cycle()


if __name__ == "__main__":
    main()
