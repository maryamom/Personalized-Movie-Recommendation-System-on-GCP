# Utiliser l'image Python officielle
FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements_streamlit.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements_streamlit.txt

# Copier le code de l'application
COPY recommender.py .
COPY streamlit_app.py .
COPY start.sh .

# Rendre le script exécutable
RUN chmod +x start.sh

# Exposer le port (Cloud Run utilise la variable d'environnement PORT)
EXPOSE 8080

# Variable d'environnement pour le port
ENV PORT=8080

# Commande pour lancer l'application
CMD ["./start.sh"]

