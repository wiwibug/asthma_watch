FROM python:3.9

# Met à jour le système et installe les dépendances GDAL
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev

# Définir les variables d'environnement pour GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /app

# Copier le fichier requirements.txt en premier pour optimiser le cache
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste de l'application
COPY . .

# Exposer le port utilisé par ton dashboard
EXPOSE 8050

# Commande de lancement (ici, avec gunicorn)
CMD ["gunicorn", "-c", "deployment/gunicorn_config.py", "app.app:server"]
