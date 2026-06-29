"""
Gestion de l'etat et detection des transitions.

L'interet du moniteur n'est pas de connaitre l'etat brut, mais de detecter
le moment exact ou un site passe de "indisponible" a "disponible".

L'etat est persiste dans un fichier JSON (state.json) pour survivre aux
redemarrages du conteneur. Le fichier est monte sur le NAS via un volume Docker.

Structure de state.json :
  { "Castorama": {"disponible": true,  "prix": 999.0, "vu_le": "2026-06-28T14:30:00"},
    "Amazon":    {"disponible": false, "prix": null,  "vu_le": "2026-06-28T14:30:00"} }
"""

import os
import json
from datetime import datetime

STATE_PATH = os.environ.get("STATE_PATH", "/data/state.json")


def charger_etat():
    """Lit l'etat precedent. Renvoie un dict vide si premier lancement."""
    if not os.path.exists(STATE_PATH):
        return {}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def sauver_etat(etat):
    """Ecrit l'etat courant de facon atomique (ecriture temp puis renommage)."""
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(etat, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_PATH)


def detecter_transitions(resultats, etat_precedent):
    """
    Compare les resultats courants a l'etat precedent.

    Renvoie deux listes :
      - alertes  : sites passes de indisponible/inconnu -> disponible
      - retours  : sites passes de disponible -> indisponible (info, pas d'alerte)

    Met aussi a jour l'etat (renvoye en 3e position) pour persistance.
    Regle : on n'alerte QUE sur une transition vers disponible confirmee (True).
    Un etat None (erreur reseau) ne modifie jamais l'etat memorise.
    """
    alertes, retours = [], []
    nouvel_etat = dict(etat_precedent)
    maintenant = datetime.now().isoformat(timespec="seconds")

    for r in resultats:
        nom = r["nom"]
        dispo = r["disponible"]

        # Etat indetermine : on ignore, on garde la memoire precedente
        if dispo is None:
            continue

        ancien = etat_precedent.get(nom, {})
        ancien_dispo = ancien.get("disponible")

        # Transition vers disponible
        if dispo is True and ancien_dispo is not True:
            alertes.append(r)
        # Transition vers indisponible
        elif dispo is False and ancien_dispo is True:
            retours.append(r)

        nouvel_etat[nom] = {
            "disponible": dispo,
            "prix": r.get("prix"),
            "vu_le": maintenant,
        }

    return alertes, retours, nouvel_etat
