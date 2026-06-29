"""
Connecteurs : recuperation du HTML et lecture du stock pour chaque site.

Deux modes d'acces :
  - direct     : requete HTTP simple avec en-tetes navigateur
  - brightdata : passe par l'API Web Unlocker de Bright Data (contourne les blocages)

Deux parsers :
  - parse_jsonld : lit la balise schema.org JSON-LD (methode fiable, donnee propre)
  - parse_amazon : lit le marqueur de disponibilite specifique a Amazon FR

Chaque fonction renvoie un dict normalise :
  {"nom": str, "disponible": bool|None, "prix": float|None, "url": str, "erreur": str|None}
disponible=None signifie "etat indetermine" (erreur reseau, blocage) : on n'alerte jamais sur None.
"""

import os
import re
import json
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Identifiants Bright Data lus depuis les variables d'environnement (jamais en dur)
BRIGHTDATA_TOKEN = os.environ.get("BRIGHTDATA_TOKEN", "")
BRIGHTDATA_ZONE = os.environ.get("BRIGHTDATA_ZONE", "web_unlocker1")
TIMEOUT = 25


# --------------------------------------------------------------------------
# Recuperation du HTML
# --------------------------------------------------------------------------

def fetch_direct(url):
    """Requete HTTP simple. Leve une exception si le statut n'est pas 200."""
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")
    return r.text


def fetch_brightdata(url):
    """
    Recupere le HTML via l'API Bright Data Web Unlocker.
    Necessite BRIGHTDATA_TOKEN. Si absent, leve une exception explicite.
    """
    if not BRIGHTDATA_TOKEN:
        raise RuntimeError("BRIGHTDATA_TOKEN manquant")
    endpoint = "https://api.brightdata.com/request"
    payload = {
        "zone": BRIGHTDATA_ZONE,
        "url": url,
        "format": "raw",
        "country": "fr",
    }
    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_TOKEN}",
        "Content-Type": "application/json",
    }
    r = requests.post(endpoint, json=payload, headers=headers, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"BrightData HTTP {r.status_code}: {r.text[:120]}")
    return r.text


def get_html(site):
    """Choisit la methode d'acces selon la config du site."""
    if site["method"] == "brightdata":
        return fetch_brightdata(site["url"])
    return fetch_direct(site["url"])


# --------------------------------------------------------------------------
# Lecture du stock
# --------------------------------------------------------------------------

# Valeurs schema.org considerees comme "en stock"
_IN_STOCK = {
    "instock", "http://schema.org/instock", "https://schema.org/instock",
    "limitedavailability", "https://schema.org/limitedavailability",
    "preorder", "https://schema.org/preorder",
}
# Valeurs schema.org considerees comme "indisponible"
_OUT_STOCK = {
    "outofstock", "https://schema.org/outofstock", "http://schema.org/outofstock",
    "soldout", "https://schema.org/soldout",
    "discontinued", "https://schema.org/discontinued",
}


def _extract_jsonld_offers(html):
    """
    Parcourt tous les blocs JSON-LD et renvoie la premiere offre Product
    trouvee sous forme (availability_str, price_float) ou (None, None).
    Tolerant : tente le parse JSON complet, sinon repli regex.
    """
    blocks = re.findall(
        r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
        html, re.DOTALL,
    )
    for b in blocks:
        raw = b.strip()
        # Tentative de parse propre
        try:
            data = json.loads(raw)
            avail, price = _walk_jsonld(data)
            if avail is not None or price is not None:
                return avail, price
        except json.JSONDecodeError:
            # Repli regex si le JSON est malforme
            a = re.search(r'"availability"\s*:\s*"([^"]+)"', raw)
            p = re.search(r'"price"\s*:\s*"?([0-9]+[.,]?[0-9]*)"?', raw)
            if a or p:
                avail = a.group(1) if a else None
                price = _to_float(p.group(1)) if p else None
                return avail, price
    return None, None


def _walk_jsonld(node):
    """Cherche recursivement 'availability' et 'price' dans une structure JSON-LD."""
    avail, price = None, None
    if isinstance(node, dict):
        if "availability" in node and isinstance(node["availability"], str):
            avail = node["availability"]
        if "price" in node:
            price = _to_float(str(node["price"]))
        for v in node.values():
            a, p = _walk_jsonld(v)
            avail = avail or a
            price = price or p
    elif isinstance(node, list):
        for item in node:
            a, p = _walk_jsonld(item)
            avail = avail or a
            price = price or p
    return avail, price


def _to_float(s):
    try:
        return float(str(s).replace(",", ".").replace(" ", ""))
    except (ValueError, AttributeError):
        return None


def parse_jsonld(html, site):
    """Parser generique base sur schema.org JSON-LD."""
    avail, price = _extract_jsonld_offers(html)
    if avail is None:
        return {"disponible": None, "prix": price, "erreur": "availability absente du JSON-LD"}
    a = avail.lower().rstrip("/")
    if a in _IN_STOCK:
        return {"disponible": True, "prix": price, "erreur": None}
    if a in _OUT_STOCK:
        return {"disponible": False, "prix": price, "erreur": None}
    return {"disponible": None, "prix": price, "erreur": f"availability inconnue: {avail}"}


def parse_amazon(html, site):
    """
    Parser specifique Amazon FR.
    'actuellement indisponible' = rupture. Sinon, presence du bouton d'achat = dispo.
    """
    txt = html.lower()
    if "actuellement indisponible" in txt or "temporairement en rupture" in txt:
        return {"disponible": False, "prix": None, "erreur": None}
    # Prix Amazon : bloc a-price-whole
    price = None
    m = re.search(r'a-price-whole">([0-9\s.,]+)<', html)
    if m:
        price = _to_float(m.group(1).strip().rstrip(".,"))
    # Presence d'un bouton d'achat actif
    if "add-to-cart-button" in txt or "buy-now-button" in txt or "buybox" in txt:
        return {"disponible": True, "prix": price, "erreur": None}
    return {"disponible": None, "prix": price, "erreur": "etat Amazon indetermine"}


# Table de routage des parsers
PARSERS = {
    "parse_jsonld": parse_jsonld,
    "parse_amazon": parse_amazon,
}


def check_site(site):
    """
    Verifie un site de bout en bout : recupere le HTML, lit le stock,
    renvoie un resultat normalise. N'echoue jamais : capture toute exception.
    """
    result = {"nom": site["nom"], "url": site["url"],
              "disponible": None, "prix": None, "erreur": None}
    try:
        html = get_html(site)
        parser = PARSERS[site["parser"]]
        parsed = parser(html, site)
        result.update(parsed)
    except Exception as e:
        result["erreur"] = str(e)[:150]
    return result
