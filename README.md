# Moniteur de stock Midea PortaSplit

Surveille la disponibilite du climatiseur **Midea PortaSplit MMCS-12HRN8-QRD0**
sur 7 enseignes francaises et envoie un email des qu'un site repasse en stock.

La detection se fait sur la **transition** (epuise vers disponible), pas sur l'etat
brut : tu reçois une alerte au moment precis ou le stock revient, et une seule fois.

---

## Ce que fait le moniteur

A chaque cycle (toutes les 15 min par defaut) :
1. interroge les 7 sites en parallele,
2. lit le stock et le prix via les donnees structurees schema.org (methode fiable),
3. compare a l'etat precedent,
4. envoie un email si un site vient de repasser en stock,
5. memorise le nouvel etat sur le NAS.

### Sites surveilles et methode d'acces

| Site         | Acces        | Etat verifie le 28/06/2026     |
|--------------|--------------|--------------------------------|
| Castorama    | direct       | EN STOCK a 999 EUR             |
| Amazon       | Bright Data  | epuise                         |
| Leroy Merlin | Bright Data  | bloque sans proxy              |
| ManoMano     | Bright Data  | bloque sans proxy              |
| Darty        | Bright Data  | bloque sans proxy              |
| Boulanger    | Bright Data  | bloque sans proxy              |
| Bricoman     | direct       | desactive (reference abandonnee)|

Castorama fonctionne sans aucune cle : tu peux tester immediatement.
Les 5 sites "Bright Data" necessitent ta cle API pour etre debloques.

---

## Installation sur le NAS UGREEN (Debian + Docker)

### 1. Copier le projet sur le NAS

Place le dossier `portasplit-monitor` dans un repertoire de ton NAS,
par exemple `/volume1/docker/portasplit-monitor`.

### 2. Configurer les cles

Copie le modele et remplis tes valeurs :

```bash
cd portasplit-monitor
cp .env.example .env
nano .env
```

A minima, pour activer l'email, renseigne `RESEND_API_KEY` et `ALERTE_TO`.
Pour debloquer les 5 sites proteges, renseigne `BRIGHTDATA_TOKEN`.

Sans aucune cle, le moniteur tourne quand meme et surveille Castorama.

### 3. Lancer

```bash
docker compose up -d --build
```

Le conteneur demarre et tourne en continu. `restart: unless-stopped`
garantit qu'il redemarre tout seul apres un redemarrage du NAS.

### 4. Verifier que ça tourne

```bash
docker compose logs -f
```

Tu dois voir un cycle s'executer avec la ligne Castorama "EN STOCK".

---

## Obtenir les cles

### Bright Data (pour les sites proteges)
1. Cree un compte sur brightdata.com
2. Dans le tableau de bord, cree une zone de type **Web Unlocker**
3. Note le **nom de la zone** (ex: `web_unlocker1`) et ta **cle API**
4. Reporte-les dans `.env` (`BRIGHTDATA_ZONE` et `BRIGHTDATA_TOKEN`)

Un credit d'essai gratuit suffit pour valider. Volume tres faible ici
(5 sites x 4 fois par heure), donc cout reel minime ensuite.

### Resend (pour l'email)
1. Cree un compte sur resend.com
2. Genere une cle API
3. Pour tester vite : laisse `ALERTE_FROM=onboarding@resend.dev`
4. Pour un usage durable : verifie ton domaine et mets `alerte@tondomaine.fr`

---

## Reglages utiles

Tout se regle dans `.env` ou `docker-compose.yml` :

- **Frequence** : `INTERVALLE_MINUTES` (defaut 15). Ne descends pas sous 10
  pour eviter de te faire reperer.
- **Activer/desactiver un site** : champ `enabled` dans `config.py`.
- **Seuil de prix** : `PRIX_CIBLE` dans `config.py`. Les sites sous ce prix
  reçoivent un badge special dans l'email.

---

## Maintenance

Le point fragile de tout moniteur de ce type : les sites changent leur structure.
Si un site cesse de remonter le stock, c'est probablement que son JSON-LD a evolue.
Il suffit alors d'inspecter la nouvelle page et d'ajuster son parser dans `connectors.py`.

Les enseignes utilisant le standard schema.org (la majorite), le parser generique
`parse_jsonld` resiste bien dans le temps. Seul Amazon a un parser dedie.

---

## Architecture des fichiers

```
portasplit-monitor/
├── config.py          # liste des sites, methode d'acces, marqueurs
├── connectors.py      # recuperation HTML (direct + Bright Data) et lecture du stock
├── state.py           # persistance et detection des transitions
├── alert.py           # envoi email via Resend
├── main.py            # un cycle complet
├── run_loop.py        # boucle continue (point d'entree Docker)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example       # modele de configuration
└── README.md
```
