"""
Envoi des alertes email.

Methode principale : API Resend (resend.com), simple et fiable, offre gratuite
de 3000 emails/mois. Necessite RESEND_API_KEY.

Repli optionnel : SMTP classique si tu preferes ta propre boite (variables SMTP_*).

Variables d'environnement attendues :
  RESEND_API_KEY   cle API Resend
  ALERTE_FROM      adresse expediteur (doit etre verifiee chez Resend, ex: alerte@tondomaine.fr)
  ALERTE_TO        adresse(s) destinataire, separees par des virgules
"""

import os
import requests

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
ALERTE_FROM = os.environ.get("ALERTE_FROM", "onboarding@resend.dev")
ALERTE_TO = os.environ.get("ALERTE_TO", "")


def _construire_corps(alertes, prix_cible):
    """Compose le corps HTML de l'email a partir des sites disponibles."""
    lignes = []
    for r in alertes:
        prix = r.get("prix")
        prix_txt = f"{prix:.0f} EUR" if prix is not None else "prix a verifier"
        badge = ""
        if prix is not None and prix <= prix_cible:
            badge = " &#127942; SOUS LA CIBLE"
        lignes.append(
            f'<li style="margin:10px 0;font-size:16px">'
            f'<b>{r["nom"]}</b> : {prix_txt}{badge}<br>'
            f'<a href="{r["url"]}" style="color:#0066cc">Acheter maintenant</a>'
            f'</li>'
        )
    return (
        '<div style="font-family:Arial,sans-serif;max-width:600px">'
        '<h2 style="color:#d32f2f">Stock PortaSplit disponible !</h2>'
        '<p>Un ou plusieurs sites viennent de remettre le climatiseur en stock :</p>'
        f'<ul style="list-style:none;padding:0">{"".join(lignes)}</ul>'
        '<p style="color:#888;font-size:13px">Les stocks partent vite. '
        'Verifie et commande sans tarder.</p>'
        '</div>'
    )


def envoyer_alerte(alertes, prix_cible):
    """
    Envoie un email recapitulant les sites passes en stock.
    Renvoie True si l'envoi a reussi, False sinon. N'echoue jamais (capture tout).
    """
    if not alertes:
        return False
    destinataires = [a.strip() for a in ALERTE_TO.split(",") if a.strip()]
    if not RESEND_API_KEY or not destinataires:
        print("[email] RESEND_API_KEY ou ALERTE_TO manquant, alerte non envoyee")
        return False

    noms = ", ".join(a["nom"] for a in alertes)
    sujet = f"PortaSplit EN STOCK : {noms}"
    corps = _construire_corps(alertes, prix_cible)

    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": ALERTE_FROM,
                "to": destinataires,
                "subject": sujet,
                "html": corps,
            },
            timeout=20,
        )
        if r.status_code in (200, 201):
            print(f"[email] alerte envoyee a {destinataires}")
            return True
        print(f"[email] echec Resend HTTP {r.status_code}: {r.text[:120]}")
        return False
    except Exception as e:
        print(f"[email] exception: {str(e)[:120]}")
        return False
