"""
Envoi des alertes email.

Methode : API Resend (resend.com), simple et fiable, offre gratuite
de 3000 emails/mois. Necessite RESEND_API_KEY.

Variables d'environnement attendues :
  RESEND_API_KEY   cle API Resend
  ALERTE_FROM      adresse expediteur (verifiee chez Resend, ex: alerte@tondomaine.fr)
  ALERTE_TO        adresse(s) destinataire, separees par des virgules
"""

import os
import requests
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Europe/Paris")
except Exception:  # pragma: no cover - repli si tz indisponible
    _TZ = None

from config import PRODUIT

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
ALERTE_FROM = os.environ.get("ALERTE_FROM", "onboarding@resend.dev")
ALERTE_TO = os.environ.get("ALERTE_TO", "")


def _maintenant():
    """Horodatage lisible en heure de Paris."""
    now = datetime.now(_TZ) if _TZ else datetime.now()
    return now.strftime("%d/%m/%Y a %H:%M")


def _prix_txt(prix):
    return f"{prix:.0f} EUR" if prix is not None else "prix a verifier"


def _trier(alertes, prix_cible):
    """Sites sous la cible d'abord, puis par prix croissant (prix inconnu en dernier)."""
    def cle(r):
        prix = r.get("prix")
        sous_cible = prix is not None and prix <= prix_cible
        return (not sous_cible, prix is None, prix if prix is not None else 0)
    return sorted(alertes, key=cle)


# --------------------------------------------------------------------------
# Rendu HTML
# --------------------------------------------------------------------------

def _carte(r, prix_cible):
    prix = r.get("prix")
    sous_cible = prix is not None and prix <= prix_cible
    badge = (
        f'<span style="display:inline-block;margin-left:8px;padding:2px 8px;'
        f'background:#e8f5e9;color:#2e7d32;border-radius:12px;font-size:12px;'
        f'font-weight:bold">&#10004; sous votre cible ({prix_cible:.0f} EUR)</span>'
        if sous_cible else ""
    )
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="margin:0 0 12px 0;border:1px solid #e0e0e0;border-radius:8px">'
        '<tr><td style="padding:16px">'
        f'<div style="font-size:17px;font-weight:bold;color:#222">{r["nom"]}{badge}</div>'
        f'<div style="font-size:22px;color:#d32f2f;margin:6px 0 12px">{_prix_txt(prix)}</div>'
        f'<a href="{r["url"]}" '
        'style="display:inline-block;background:#d32f2f;color:#fff;text-decoration:none;'
        'padding:10px 18px;border-radius:6px;font-size:15px;font-weight:bold">'
        'Voir l\'offre &rarr;</a>'
        '</td></tr></table>'
    )


def _construire_html(alertes, prix_cible):
    cartes = "".join(_carte(r, prix_cible) for r in alertes)
    pluriel = "s" if len(alertes) > 1 else ""
    return (
        '<div style="font-family:Arial,Helvetica,sans-serif;max-width:600px;'
        'margin:0 auto;color:#222">'
        '<div style="background:#d32f2f;color:#fff;padding:18px 20px;border-radius:8px 8px 0 0">'
        '<div style="font-size:20px;font-weight:bold">&#10024; De nouveau en stock !</div>'
        f'<div style="font-size:13px;opacity:.9;margin-top:4px">{PRODUIT}</div>'
        '</div>'
        '<div style="padding:20px;border:1px solid #e0e0e0;border-top:none;'
        'border-radius:0 0 8px 8px">'
        f'<p style="margin:0 0 16px;font-size:15px">'
        f'{len(alertes)} site{pluriel} vient{"" if len(alertes)>1 else ""} de remettre '
        'le climatiseur en stock :</p>'
        f'{cartes}'
        '<p style="color:#888;font-size:13px;margin-top:18px">'
        'Les stocks partent vite &mdash; verifie et commande sans tarder.</p>'
        f'<p style="color:#aaa;font-size:12px;margin-top:8px">'
        f'Detecte le {_maintenant()} (heure de Paris).</p>'
        '</div></div>'
    )


def _construire_texte(alertes, prix_cible):
    lignes = [f"De nouveau en stock : {PRODUIT}", ""]
    for r in alertes:
        prix = r.get("prix")
        marque = "  [SOUS LA CIBLE]" if (prix is not None and prix <= prix_cible) else ""
        lignes.append(f"- {r['nom']} : {_prix_txt(prix)}{marque}")
        lignes.append(f"  {r['url']}")
    lignes += ["", f"Detecte le {_maintenant()} (heure de Paris).",
               "Les stocks partent vite, commande sans tarder."]
    return "\n".join(lignes)


# --------------------------------------------------------------------------
# Envoi
# --------------------------------------------------------------------------

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

    alertes = _trier(alertes, prix_cible)
    noms = ", ".join(a["nom"] for a in alertes)
    # Si un site est sous la cible, on le signale des le sujet
    moins_cher = next((a["prix"] for a in alertes if a.get("prix") is not None), None)
    prefixe = f"{moins_cher:.0f} EUR" if moins_cher is not None else "en stock"
    sujet = f"\U0001F514 PortaSplit {prefixe} : {noms}"

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
                "html": _construire_html(alertes, prix_cible),
                "text": _construire_texte(alertes, prix_cible),
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
