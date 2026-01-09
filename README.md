# 🎬 Système de Recommandation de Films Personnalisé sur GCP

Un système complet de recommandation de films utilisant le filtrage collaboratif, le filtrage basé sur le contenu et un système hybride, déployé sur Google Cloud Platform.


## 🎯 Vue d'ensemble

Ce projet implémente un système de recommandation de films personnalisé qui :

- **Charge les données** depuis BigQuery (films et ratings)
- **Entraîne des modèles** de recommandation (Collaborative Filtering avec SVD, Content-Based, et Hybride)
- **Permet l'ajout** de nouveaux utilisateurs avec leurs ratings
- **Re-entraîne automatiquement** le modèle après l'ajout de nouveaux ratings
- **Fournit une interface web** intuitive avec Flask
- **S'adapte aux nouveaux utilisateurs** (gestion du cold start)

### Objectifs du Projet

- Démontrer l'intégration de BigQuery, Vertex AI, et Cloud Run sur GCP
- Implémenter un système de recommandation évolutif
- Montrer l'évolution des recommandations pour un nouvel utilisateur
- Fournir une API et une interface utilisateur fonctionnelles


### Flux de Données

1. **Chargement initial** : Les données sont chargées depuis BigQuery au démarrage
2. **Entraînement** : Le modèle SVD est entraîné sur les données de ratings
3. **Recommandation** : 
   - Nouveaux utilisateurs (< 10 ratings) → Content-Based
   - Utilisateurs actifs (≥ 10 ratings) → Collaborative Filtering
4. **Mise à jour** : Ajout de nouveaux ratings → Re-entraînement du modèle

## ✨ Fonctionnalités

### 1. Exploration des Films
- Recherche de films par titre
- Affichage de la liste complète des films
- Détails des films (genres, ID, titre)

### 2. Gestion des Ratings
- Ajout de ratings pour un nouvel utilisateur
- Visualisation des ratings ajoutés
- Mise à jour du système avec re-entraînement automatique
- Gestion des doublons et mises à jour

### 3. Système de Recommandation
- **Collaborative Filtering (SVD)** : Basé sur les similarités entre utilisateurs
- **Content-Based Filtering** : Basé sur les genres des films
- **Système Hybride** : Combine les deux méthodes selon le profil utilisateur

### 4. Gestion du Cold Start
- Nouveaux utilisateurs sans historique → Content-Based
- Utilisateurs avec peu de ratings (< 10) → Content-Based
- Utilisateurs actifs (≥ 10 ratings) → Collaborative Filtering

## 🛠️ Technologies Utilisées

### Backend & ML
- **Python 3.10**
- **scikit-surprise** : Implémentation SVD pour Collaborative Filtering
- **scikit-learn** : Similarité cosinus pour Content-Based
- **pandas** : Manipulation des données
- **numpy** : Calculs numériques

### Cloud & Infrastructure
- **Google Cloud BigQuery** : Stockage et requêtes des données
- **Google Cloud Run** : Déploiement du service
- **Docker** : Containerisation
- **flask** : Interface utilisateur web

### Data Processing
- **pandas-gbq** : Intégration pandas-BigQuery
- **google-cloud-bigquery** : Client BigQuery Python

## 📁 Structure du Projet

```
.
├── recommender.py              # Module principal de recommandation
├── app2.py                     # Interface 
├── Dockerfile                  # Configuration Docker
├── docker-compose.yml          # Configuration Docker Compose
├── .dockerignore               # Fichiers à exclure de Docker
│
├── Notebooks Jupyter:
│   ├── dataExploaration.ipynb  # Exploration des données
│   ├── data processing.ipynb   # Traitement et encodage des genres
│   └── Modeling.ipynb          # Modélisation et tests
│
└── Documentation:
    ├── README.md               
    
```

### Description des Fichiers Principaux

#### `recommender.py`
Module principal contenant :
- Chargement des données depuis BigQuery
- Entraînement du modèle SVD
- Fonctions de recommandation (Collaborative, Content-Based, Hybride)
- Gestion des nouveaux utilisateurs
- Re-entraînement du modèle

#### `app2.py`
Interface utilisateur avec 3 sections :
1. **Explorer les Films** : Recherche et affichage
2. **Ajouter des Ratings** : Gestion des nouveaux utilisateurs
3. **Obtenir des Recommandations** : Affichage des recommandations

## 🚀 Installation

### Prérequis

1. **Compte Google Cloud Platform** avec :
   - Projet GCP configuré
   - BigQuery activé
   - Cloud Run activé (pour le déploiement)
   - Credentials configurés

2. **Python 3.10+**

3. **Docker** (optionnel, pour le déploiement)

### Installation Locale

1. **Cloner ou télécharger le projet**

2. **Installer les dépendances** :
```bash
pip install -r requirements_streamlit.txt
```

3. **Configurer les credentials GCP** :
```bash
gcloud auth application-default login
```

4. **Vérifier la configuration BigQuery** :
   - Vérifier que les tables existent dans BigQuery
   - Vérifier les permissions d'accès

## 💻 Utilisation

### Mode Local (Streamlit)

1. **Lancer l'application** :
```bash
streamlit run streamlit_app.py
```

2. **Accéder à l'interface** :
   - URL locale : `http://localhost:8501`
   - L'application s'ouvre automatiquement dans le navigateur

3. **Utiliser l'interface** :
   - Naviguer entre les 3 sections via la sidebar
   - Explorer les films
   - Ajouter des ratings pour un nouvel utilisateur
   - Obtenir des recommandations

### Mode Docker (Local)

1. **Construire l'image** :
```bash
docker build -t movie-recommendation-streamlit .
```

2. **Lancer le conteneur** :
```bash
docker run -p 8501:8080 \
  -e GOOGLE_CLOUD_PROJECT=students-group3 \
  -v ~/.config/gcloud:/root/.config/gcloud:ro \
  movie-recommendation-streamlit
```

3. **Accéder à l'application** :
   - URL : `http://localhost:8501`

### Mode Docker Compose

```bash
docker-compose up --build
```

## ☁️ Déploiement

### Déploiement sur Google Cloud Run

#### Méthode Automatique

```bash
chmod +x deploy-cloud-run.sh
./deploy-cloud-run.sh [PROJECT_ID] [SERVICE_NAME] [REGION]
```

Exemple :
```bash
./deploy-cloud-run.sh students-group3 movie-recommendation-streamlit us-central1
```

#### Méthode Manuelle

1. **Construire et pousser l'image** :
```bash
gcloud builds submit --tag gcr.io/students-group3/movie-recommendation-streamlit
```


```

3. **Récupérer l'URL** :
```bash
gcloud run services describe movie-recommendation-streamlit \
  --region us-central1 \
  --format 'value(status.url)'
```



## 📖 Guide d'Utilisation

### 1. Explorer les Films

1. Cliquer sur **"📊 Explorer les Films"** dans la sidebar
2. Utiliser la barre de recherche pour trouver un film
3. Sélectionner un film dans la liste pour voir les détails
4. Ajuster le nombre de résultats avec le slider

### 2. Ajouter des Ratings pour un Nouvel Utilisateur

1. Cliquer sur **"⭐ Ajouter des Ratings"** dans la sidebar
2. Noter l'ID utilisateur généré automatiquement
3. Sélectionner un film dans la liste déroulante
4. Choisir une note (0.5 à 5.0)
5. Cliquer sur **"➕ Ajouter ce Rating"**
6. Répéter pour ajouter plusieurs ratings
7. Cliquer sur **"💾 Sauvegarder et Mettre à Jour le Système"**
   - ⚠️ Le re-entraînement peut prendre quelques minutes

### 3. Obtenir des Recommandations

1. Cliquer sur **"🎯 Obtenir des Recommandations"** dans la sidebar
2. Choisir le type d'utilisateur :
   - **Utilisateur existant** : Sélectionner un ID dans la liste
   - **Nouvel utilisateur** : Utiliser l'ID généré (si des ratings ont été ajoutés)
3. Sélectionner la méthode de recommandation :
   - **Hybride (recommandé)** : Adapte automatiquement la méthode
   - **Collaborative Filtering** : Basé sur les similarités utilisateurs
   - **Content-Based Filtering** : Basé sur les genres
4. Choisir le nombre de recommandations (5-50)
5. Cliquer sur **"🎯 Obtenir les Recommandations"**

### Exemple de Workflow Complet

1. **Explorer** quelques films pour se familiariser
2. **Ajouter 3-5 ratings** pour un nouvel utilisateur
3. **Obtenir des recommandations** avec la méthode Hybride
4. **Ajouter plus de ratings** (10+)
5. **Re-obtenir des recommandations** et observer la différence
   - Les recommandations devraient être plus précises avec plus de données
