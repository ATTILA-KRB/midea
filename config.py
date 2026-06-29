"""
Configuration centrale du moniteur de stock Midea PortaSplit.

Chaque site definit :
  - url        : page produit a surveiller
  - method     : 'direct' (requete simple) ou 'brightdata' (proxy anti-blocage)
  - parser     : nom de la fonction de lecture du stock (voir connectors.py)
  - enabled    : permet d'activer / desactiver un site sans toucher au code

Base etablie le 28/06/2026 par inspection reelle du HTML de chaque site.
"""

# Produit surveille
PRODUIT = "Midea PortaSplit MMCS-12HRN8-QRD0"

# Seuil de prix qui declenche une mention speciale dans l'alerte (en euros)
PRIX_CIBLE = 1000

SITES = [
    {
        # Revendeur officiel Midea en France (boutique WooCommerce).
        # Desactive : Cloudflare en mode "sous attaque" renvoie 503 meme via
        # Bright Data Web Unlocker (teste avec reessais). A reactiver si une
        # methode plus robuste (Scraping Browser, rendu JS) est mise en place.
        # NB : le meme produit est deja suivi via Leroy Merlin ("par Optimea").
        "nom": "Optimea",
        "url": "https://www.optimea.fr/product/climatiseur-split-mobile-midea/",
        "method": "brightdata",
        "parser": "parse_jsonld",
        "enabled": False,
    },
    {
        "nom": "Castorama",
        "url": "https://www.castorama.fr/climatiseur-portasplit-midea-reversible-3500w/8431312260509_CAFR.prd",
        "method": "direct",
        "parser": "parse_castorama",  # JSON-LD InStock code en dur : on lit l'etat du bouton panier
        "enabled": True,
    },
    {
        "nom": "Amazon",
        "url": "https://www.amazon.fr/dp/B0CY2YW8BT",
        "method": "brightdata",   # 200 en direct mais bannit vite : proxy recommande
        "parser": "parse_amazon",
        "enabled": True,
    },
    {
        "nom": "Leroy Merlin",
        "url": "https://www.leroymerlin.fr/produits/climatiseur-split-mobile-reversible-portasplit-midea-par-optimea-93857579.html",
        "method": "brightdata",   # 403 en direct
        "parser": "parse_jsonld",
        "enabled": True,
    },
    {
        "nom": "ManoMano",
        "url": "https://www.manomano.fr/p/midea-climatiseur-split-mobile-reversible-froid-chaud-3500w12000btu-wifi-deshumidificateur-ventilateur-jusqua-40m2-kit-fenetre-inclus-83810402",
        "method": "brightdata",   # 403 en direct
        "parser": "parse_jsonld",
        "enabled": True,
    },
    {
        "nom": "Darty",
        "url": "https://www.darty.com/nav/achat/gros_electromenager/chauffage_climatisation/climatiseur/midea_mmcs-12hrn8-qrd0.html",
        "method": "brightdata",   # 403 en direct + stock geolocalise
        "parser": "parse_darty",  # dispo en microdata itemprop, pas en JSON-LD
        "enabled": True,
    },
    {
        "nom": "Boulanger",
        "url": "https://www.boulanger.com/ref/1216685",
        "method": "brightdata",   # 400 en direct
        "parser": "parse_jsonld",
        "enabled": True,
    },
    {
        # Reference comme "Discontinued" le 28/06 : desactive par defaut.
        # A reactiver si Bricoman le reintroduit.
        "nom": "Bricoman",
        "url": "https://www.bricoman.fr/produits/climatiseur-mobile-reversible-portasplit-midea-25088072.html",
        "method": "direct",
        "parser": "parse_jsonld",
        "enabled": False,
    },
]
