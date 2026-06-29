# Image legere Python sur base Debian slim, ideale pour ton NAS UGREEN
FROM python:3.12-slim

# Fuseau horaire France pour des horodatages corrects dans les logs
ENV TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Installation des dependances (couche mise en cache tant que requirements.txt ne change pas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code de l'application
COPY config.py connectors.py state.py alert.py main.py run_loop.py ./

# L'etat persiste est ecrit dans /data, monte en volume depuis le NAS
VOLUME ["/data"]
ENV STATE_PATH=/data/state.json

# Lancement de la boucle continue
CMD ["python", "run_loop.py"]
