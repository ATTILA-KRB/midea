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


def interroger_sites(sites):
    """Interroge les sites donnes en parallele. Renvoie la liste des resultats."""
    if not sites:
        return []
    resultats = []
    with ThreadPoolExecutor(max_workers=min(8, len(sites))) as executor:
        futures = {}
        for site in sites:
            # Petit delai aleatoire pour ne pas frapper tous les sites en meme temps
            time.sleep(random.uniform(0.1, 0.5))
            futures[executor.submit(check_site, site)] = site["nom"]
        for fut in as_completed(futures):
            resultats.append(fut.result())
    # Tri par nom pour un affichage stable
    return sorted(resultats, key=lambda r: r["nom"])


def _sites_a_verifier(etat, maintenant):
    """
    Renvoie les sites actifs dont la cadence est echue.

    Chaque site peut definir 'intervalle' (minutes, defaut 2). La derniere
    verification est memorisee dans l'etat sous la cle speciale
    '_derniere_verif' pour que chaque site suive sa propre cadence :
    utile pour maitriser le cout Bright Data en boucle rapide.
    """
    verifs = etat.get("_derniere_verif", {})
    dus = []
    for site in SITES:
        if not site.get("enabled", True):
            continue
        intervalle = site.get("intervalle", 2) * 60
        derniere = verifs.get(site["nom"])
        if derniere is None:
            dus.append(site)
            continue
        try:
            ecoule = (maintenant - datetime.fromisoformat(derniere)).total_seconds()
        except ValueError:
            ecoule = intervalle
        if ecoule >= intervalle:
            dus.append(site)
    return dus


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
    """Execute un cycle de verification des sites dont la cadence est echue."""
    etat_precedent = charger_etat()
    maintenant = datetime.now()
    dus = _sites_a_verifier(etat_precedent, maintenant)
    if not dus:
        return []
    _log(f"--- Cycle de verification : {PRODUIT} ({len(dus)} site(s)) ---")
    resultats = interroger_sites(dus)
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

    # Memorise la date de verification des sites interroges (cadence par site)
    verifs = dict(etat_precedent.get("_derniere_verif", {}))
    for site in dus:
        verifs[site["nom"]] = maintenant.isoformat(timespec="seconds")
    nouvel_etat["_derniere_verif"] = verifs

    sauver_etat(nouvel_etat)
    _log("--- Fin du cycle ---")
    return resultats


def main():
    cycle()


if __name__ == "__main__":
    main()
