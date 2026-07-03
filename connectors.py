"""
Connecteurs : recuperation du HTML et lecture du stock pour chaque site.

Deux modes d'acces :
  - direct     : requete HTTP simple avec en-tetes navigateur
  - brightdata : passe par le superproxy Web Unlocker de Bright Data (contourne les blocages)

Deux parsers :
  - parse_jsonld : lit la balise schema.org JSON-LD (methode fiable, donnee propre)
  - parse_amazon : lit le marqueur de disponibilite specifique a Amazon FR

Chaque fonction renvoie un dict normalise :
  {"nom": str, "disponible": bool|None, "prix": float|None, "url": str, "erreur": str|None}
disponible=None signifie "etat indetermine" (erreur reseau, blocage) : on n'alerte jamais sur None.
"""

import os
import re
import time
import json
import requests
import urllib3

# Bright Data (Web Unlocker) termine le TLS de son cote : on desactive donc
# la verification du certificat pour ces requetes (equivaut au -k de curl).
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Identifiants Bright Data lus depuis les variables d'environnement (jamais en dur)
#   BRIGHTDATA_CUSTOMER : identifiant de compte (ex: hl_xxxxxxxx)
#   BRIGHTDATA_ZONE     : nom de la zone Web Unlocker (ex: mcp_unlocker)
#   BRIGHTDATA_TOKEN    : mot de passe de la zone (champ "password" du superproxy)
BRIGHTDATA_CUSTOMER = os.environ.get("BRIGHTDATA_CUSTOMER", "")
BRIGHTDATA_TOKEN = os.environ.get("BRIGHTDATA_TOKEN", "")
BRIGHTDATA_ZONE = os.environ.get("BRIGHTDATA_ZONE", "")
BRIGHTDATA_SUPERPROXY = os.environ.get("BRIGHTDATA_SUPERPROXY", "brd.superproxy.io:33335")
TIMEOUT = 25
# Le superproxy Web Unlocker est plus lent (rendu JS / anti-bot) : timeout dedie plus large
BRIGHTDATA_TIMEOUT = int(os.environ.get("BRIGHTDATA_TIMEOUT", "90"))
# Nombre de tentatives Bright Data (sites a anti-bot agressif : 503 transitoire)
BRIGHTDATA_TENTATIVES = int(os.environ.get("BRIGHTDATA_TENTATIVES", "3"))

# Bright Data Browser API (Scraping Browser) : navigateur reel pilote par
# Playwright via CDP. Pour les sites a anti-bot tres agressif (Cloudflare "sous
# attaque") que le Web Unlocker ne franchit pas. Reutilise BRIGHTDATA_CUSTOMER.
#   BRIGHTDATA_BROWSER_ZONE  : nom de la zone Browser API (ex: mcp_browser)
#   BRIGHTDATA_BROWSER_TOKEN : mot de passe de cette zone
BRIGHTDATA_BROWSER_ZONE = os.environ.get("BRIGHTDATA_BROWSER_ZONE", "mcp_browser")
BRIGHTDATA_BROWSER_TOKEN = os.environ.get("BRIGHTDATA_BROWSER_TOKEN", "")
BRIGHTDATA_BROWSER_HOST = os.environ.get("BRIGHTDATA_BROWSER_HOST", "brd.superproxy.io:9222")


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
    Recupere le HTML via le superproxy Bright Data Web Unlocker (mode proxy).

    Construit l'identifiant proxy au format officiel :
      brd-customer-<CUSTOMER>-zone-<ZONE> : <PASSWORD>
    Necessite CUSTOMER + ZONE + TOKEN. Si l'un manque, leve une exception explicite.
    """
    if not (BRIGHTDATA_CUSTOMER and BRIGHTDATA_ZONE and BRIGHTDATA_TOKEN):
        manquants = [n for n, v in (
            ("BRIGHTDATA_CUSTOMER", BRIGHTDATA_CUSTOMER),
            ("BRIGHTDATA_ZONE", BRIGHTDATA_ZONE),
            ("BRIGHTDATA_TOKEN", BRIGHTDATA_TOKEN),
        ) if not v]
        raise RuntimeError(f"identifiants Bright Data manquants: {', '.join(manquants)}")

    proxy_user = f"brd-customer-{BRIGHTDATA_CUSTOMER}-zone-{BRIGHTDATA_ZONE}"
    proxy_url = f"http://{proxy_user}:{BRIGHTDATA_TOKEN}@{BRIGHTDATA_SUPERPROXY}"
    proxies = {"http": proxy_url, "https": proxy_url}

    # Quelques tentatives : sur les sites a anti-bot agressif (Cloudflare), le
    # Web Unlocker echoue parfois (503/timeout) avant de resoudre le challenge.
    derniere = "?"
    for tentative in range(BRIGHTDATA_TENTATIVES):
        try:
            # verify=False car Bright Data re-termine le TLS (cf. -k du curl officiel)
            r = requests.get(url, headers=HEADERS, proxies=proxies,
                             timeout=BRIGHTDATA_TIMEOUT, verify=False)
            if r.status_code == 200:
                return r.text
            derniere = f"HTTP {r.status_code}"
        except Exception as e:
            derniere = str(e)[:80]
        if tentative < BRIGHTDATA_TENTATIVES - 1:
            time.sleep(3 * (tentative + 1))  # backoff : 3s, 6s, ...
    raise RuntimeError(f"BrightData {derniere} (apres {BRIGHTDATA_TENTATIVES} tentatives)")


def fetch_scraping_browser(url):
    """
    Recupere le HTML via le Bright Data Scraping Browser (Browser API) :
    un vrai navigateur distant pilote par Playwright via CDP. Reservee aux sites
    a anti-bot tres agressif (Cloudflare "sous attaque") que le Web Unlocker ne
    franchit pas. Necessite le paquet playwright + CUSTOMER/BROWSER_ZONE/BROWSER_TOKEN.
    """
    if not (BRIGHTDATA_CUSTOMER and BRIGHTDATA_BROWSER_ZONE and BRIGHTDATA_BROWSER_TOKEN):
        raise RuntimeError("identifiants Bright Data Browser manquants "
                           "(CUSTOMER / BROWSER_ZONE / BROWSER_TOKEN)")
    from playwright.sync_api import sync_playwright  # import paresseux : seulement si utilise

    user = f"brd-customer-{BRIGHTDATA_CUSTOMER}-zone-{BRIGHTDATA_BROWSER_ZONE}"
    endpoint = f"wss://{user}:{BRIGHTDATA_BROWSER_TOKEN}@{BRIGHTDATA_BROWSER_HOST}"
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint, timeout=120000)
        try:
            page = browser.new_page()
            page.goto(url, timeout=120000, wait_until="domcontentloaded")
            # Laisser le challenge anti-bot se resoudre et le contenu se rendre
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            return page.content()
        finally:
            browser.close()


def get_html(site):
    """Choisit la methode d'acces selon la config du site."""
    methode = site["method"]
    if methode == "brightdata":
        return fetch_brightdata(site["url"])
    if methode == "scraping_browser":
        return fetch_scraping_browser(site["url"])
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


def parse_castorama(html, site):
    """
    Parser specifique Castorama.

    Le JSON-LD de Castorama laisse "availability": InStock code en dur, meme quand
    le produit est epuise : il est donc inexploitable pour le stock (mais bon pour le prix).
    Le vrai signal est le bouton d'ajout au panier du produit, rendu cote serveur :
      - bouton present et NON desactive  -> disponible
      - bouton present et "disabled"     -> indisponible
    On cible le <button> dont l'aria-label commence par "Ajouter au panier".
    """
    # Prix : le JSON-LD reste fiable pour ce champ
    _, price = _extract_jsonld_offers(html)

    # Bouton principal, identifie par son aria-label produit
    m = re.search(r'<button([^>]*aria-label="\s*ajouter au panier[^"]*"[^>]*)>',
                  html, re.IGNORECASE)
    attrs_list = [m.group(1)] if m else re.findall(
        r'<button([^>]*)>\s*ajouter au panier\s*</button>', html, re.IGNORECASE)

    if not attrs_list:
        return {"disponible": None, "prix": price,
                "erreur": "bouton panier introuvable"}

    # Disponible si au moins un bouton d'ajout n'est pas desactive
    dispo = any("disabled" not in a.lower() for a in attrs_list)
    return {"disponible": dispo, "prix": price, "erreur": None}


def parse_darty(html, site):
    """
    Parser specifique Darty.

    Darty n'expose pas la disponibilite en JSON-LD mais en microdata schema.org
    (balise <link itemprop="availability" href="https://schema.org/OutOfStock">).
    On lit ce champ ; repli sur le marqueur tagcommander 'product_stock'.
    """
    # Prix : JSON-LD generique sinon microdata itemprop="price"
    _, price = _extract_jsonld_offers(html)
    if price is None:
        mp = re.search(r'itemprop="price"[^>]*content="([0-9.,]+)"', html, re.IGNORECASE)
        if mp:
            price = _to_float(mp.group(1))

    # 1) Signal principal : microdata availability (ordre des attributs indifferent)
    tag = re.search(r'<(?:link|meta)[^>]*itemprop="availability"[^>]*>', html, re.IGNORECASE)
    if tag:
        val = re.search(r'schema\.org/(\w+)', tag.group(0))
        if val:
            v = val.group(1).lower()
            if v in _IN_STOCK:
                return {"disponible": True, "prix": price, "erreur": None}
            if v in _OUT_STOCK:
                return {"disponible": False, "prix": price, "erreur": None}

    # 2) Repli : meta tagcommander product_stock ("produit indisponible" / "en stock")
    mt = re.search(r'name="product_stock"[^>]*content="([^"]+)"', html, re.IGNORECASE)
    if mt:
        indispo = "indisponible" in mt.group(1).lower()
        return {"disponible": not indispo, "prix": price, "erreur": None}

    return {"disponible": None, "prix": price, "erreur": "disponibilite Darty introuvable"}


def parse_woocommerce(html, site):
    """
    Parser generique WooCommerce (utilise pour Optimea).

    Signaux par ordre de fiabilite (tous rendus cote serveur par WooCommerce) :
      1. <p class="stock out-of-stock|in-stock"> ...
      2. bouton 'single_add_to_cart_button' present et non desactive
      3. texte explicite "rupture de stock" / "stock epuise"
      4. availability microdata puis JSON-LD
    Prix : .woocommerce-Price-amount sinon JSON-LD.
    Renvoie None si aucun signal (ex: page de maintenance) -> jamais d'alerte.
    """
    low = html.lower()

    # Prix
    _, price = _extract_jsonld_offers(html)
    if price is None:
        mp = re.search(r'woocommerce-Price-amount[^>]*>[^0-9]*([0-9][0-9 ., ]*)', html)
        if mp:
            price = _to_float(re.sub(r"[^0-9.,]", "", mp.group(1)))

    # 1. Classes de stock WooCommerce
    if re.search(r'class="[^"]*\bout-of-stock\b[^"]*"', html, re.IGNORECASE):
        return {"disponible": False, "prix": price, "erreur": None}
    if re.search(r'class="[^"]*\bin-stock\b[^"]*"', html, re.IGNORECASE):
        return {"disponible": True, "prix": price, "erreur": None}

    # 2. Bouton d'ajout au panier WooCommerce
    btn = re.search(r'<button[^>]*single_add_to_cart_button[^>]*>', html, re.IGNORECASE)
    if btn:
        return {"disponible": "disabled" not in btn.group(0).lower(),
                "prix": price, "erreur": None}

    # 3. Texte explicite
    if "rupture de stock" in low or "stock epuise" in low or "stock épuisé" in low:
        return {"disponible": False, "prix": price, "erreur": None}

    # 4. Microdata puis JSON-LD availability
    av = None
    tag = re.search(r'<(?:link|meta)[^>]*itemprop="availability"[^>]*>', html, re.IGNORECASE)
    if tag:
        v = re.search(r'schema\.org/(\w+)', tag.group(0))
        av = v.group(1).lower() if v else None
    if av is None:
        a2, _ = _extract_jsonld_offers(html)
        if a2:
            av = a2.lower().rstrip("/").split("/")[-1]
    if av in _IN_STOCK:
        return {"disponible": True, "prix": price, "erreur": None}
    if av in _OUT_STOCK:
        return {"disponible": False, "prix": price, "erreur": None}

    return {"disponible": None, "prix": price,
            "erreur": "signal stock WooCommerce introuvable (maintenance ?)"}


def parse_hemmera(html, site):
    """
    Parser specifique hemmera.fr (boutique CS-Cart).

    Piege constate le 03/07 : le champ "En stock" (inventaire) peut etre a True
    alors que l'achat est bloque jusqu'a une date future. Le blocage est rendu
    cote serveur dans un bloc :
      <div class="ty-product-coming-soon">... Il sera disponible le <date></div>
      <!--add_to_cart_update_<id_produit>-->
    Regle : disponible UNIQUEMENT si pas de bloc coming-soon pour le produit
    principal ET champ stock "En stock".
    """
    _, price = _extract_jsonld_offers(html)

    # Identifiant CS-Cart du produit principal (premier champ de stock de la page)
    m = re.search(r'id="in_stock_info_(\d+)"', html)
    if not m:
        return {"disponible": None, "prix": price,
                "erreur": "champ stock hemmera introuvable"}
    pid = m.group(1)

    # Achat bloque jusqu'a une date (pre-commande) pour CE produit
    coming = re.search(
        r'ty-product-coming-soon[^>]*>(.*?)</div>\s*<!--add_to_cart_update_'
        + re.escape(pid) + r'-->',
        html, re.DOTALL,
    )
    if coming:
        return {"disponible": False, "prix": price, "erreur": None}

    # Sinon on lit le libelle du champ de stock du produit principal
    label = re.search(
        r'id="in_stock_info_' + re.escape(pid) + r'"[^>]*>(.*?)</span>',
        html, re.DOTALL,
    )
    if label:
        txt = label.group(1).lower()
        if "en stock" in txt:
            return {"disponible": True, "prix": price, "erreur": None}
        if "rupture" in txt or "puis" in txt:
            return {"disponible": False, "prix": price, "erreur": None}

    return {"disponible": None, "prix": price,
            "erreur": "etat hemmera indetermine"}


# Table de routage des parsers
PARSERS = {
    "parse_jsonld": parse_jsonld,
    "parse_amazon": parse_amazon,
    "parse_castorama": parse_castorama,
    "parse_darty": parse_darty,
    "parse_woocommerce": parse_woocommerce,
    "parse_hemmera": parse_hemmera,
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
