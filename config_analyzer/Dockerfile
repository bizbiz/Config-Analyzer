# Utilisez une image de base appropriée
FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de requirements et installer les dépendances
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copier le contenu du projet
COPY . .

# Définir le PYTHONPATH pour inclure le répertoire de votre projet
ENV PYTHONPATH "${PYTHONPATH}:/app/config_analyzer"

# Exposer le port de l'application
EXPOSE 5000

# Commande pour démarrer l'application Flask
CMD ["sh", "-c", "flask db upgrade && flask run --host=0.0.0.0 --port=5000 --app config_analyzer.app:app"]