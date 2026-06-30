"""
Test ponctuel d'envoi d'email (TEMPORAIRE).

Envoie une fausse alerte via le vrai chemin (Resend) pour verifier la
delivrabilite de bout en bout. A supprimer apres verification.
"""

from config import PRIX_CIBLE
from alert import envoyer_alerte

faux = [{
    "nom": "TEST (a ignorer)",
    "url": "https://www.example.com",
    "disponible": True,
    "prix": 999.0,
    "erreur": None,
}]

ok = envoyer_alerte(faux, PRIX_CIBLE)
print(f"RESULTAT ENVOI : {ok}")
