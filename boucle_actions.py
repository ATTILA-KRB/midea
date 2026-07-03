"""
Boucle de surveillance continue pour GitHub Actions.

GitHub n'honore pas les crons rapides (minimum 5 min, en pratique 1 a 3 h).
Strategie : un job long qui enchaine les cycles toutes les ~2 minutes pendant
DUREE_MINUTES, puis se termine ; le workflow se relance alors lui-meme
(etape d'auto-dispatch dans surveillance.yml), ce qui donne une surveillance
quasi continue.

La cadence PAR SITE est geree dans main.cycle() via le champ "intervalle" de
config.py : a chaque tick de 2 min, seuls les sites echus sont interroges
(les sites Bright Data moins souvent, pour maitriser le cout).

Variables d'environnement :
  DUREE_MINUTES   duree de vie de la boucle avant relance (defaut 58)
  TICK_SECONDES   pas entre deux ticks (defaut 120)
"""

import os
import time
import random
import traceback

from main import cycle

DUREE_MINUTES = int(os.environ.get("DUREE_MINUTES", "58"))
TICK_SECONDES = int(os.environ.get("TICK_SECONDES", "120"))


def run():
    print(f"[boucle-actions] demarrage : tick ~{TICK_SECONDES}s pendant {DUREE_MINUTES} min",
          flush=True)
    fin = time.monotonic() + DUREE_MINUTES * 60
    while True:
        debut = time.monotonic()
        try:
            cycle()
        except Exception:
            # Une erreur ne doit jamais tuer la boucle
            print("[boucle-actions] erreur durant le cycle :", flush=True)
            traceback.print_exc()
        # Tick regulier avec un peu de jitter pour ne pas etre trop mecanique
        ecoule = time.monotonic() - debut
        attente = max(5, TICK_SECONDES * random.uniform(0.85, 1.15) - ecoule)
        if time.monotonic() + attente >= fin:
            break
        time.sleep(attente)
    print("[boucle-actions] fin de la fenetre, relance par le workflow", flush=True)


if __name__ == "__main__":
    run()
