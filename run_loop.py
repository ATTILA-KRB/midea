"""
Boucle d'execution continue.

Lance un cycle de verification toutes les INTERVALLE_MINUTES, indefiniment.
C'est le point d'entree du conteneur Docker (voir Dockerfile).

Un intervalle aleatoire est ajoute pour ne pas avoir un rythme trop mecanique
qui pourrait etre detecte comme un bot.

Variable d'environnement :
  INTERVALLE_MINUTES   periode entre deux cycles (defaut 15)
"""

import os
import time
import random
import traceback

from main import cycle

INTERVALLE = int(os.environ.get("INTERVALLE_MINUTES", "15"))


def run_loop():
    print(f"[boucle] demarrage, un cycle toutes les ~{INTERVALLE} min", flush=True)
    while True:
        try:
            cycle()
        except Exception:
            # On ne laisse jamais une erreur tuer la boucle
            print("[boucle] erreur durant le cycle :", flush=True)
            traceback.print_exc()
        # Intervalle de base + jitter aleatoire de +/- 20%
        base = INTERVALLE * 60
        jitter = base * random.uniform(-0.2, 0.2)
        attente = max(60, base + jitter)
        print(f"[boucle] prochain cycle dans {attente/60:.1f} min", flush=True)
        time.sleep(attente)


if __name__ == "__main__":
    run_loop()
