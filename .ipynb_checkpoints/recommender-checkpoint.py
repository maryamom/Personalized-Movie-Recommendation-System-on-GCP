"""
Système de recommandation de films
Encapsule la logique de Modeling.ipynb avec support pour l'ajout de nouveaux utilisateurs
et le re-entraînement du modèle.
"""

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict
import warnings

# Essayer d'importer surprise, mais continuer sans si non disponible
try:
    from surprise import Dataset, Reader, SVD, accuracy
    from surprise.model_selection import train_test_split
    SURPRISE_AVAILABLE = True
except ImportError:
    SURPRISE_AVAILABLE = False
    print("WARNING: Bibliotheque 'surprise' non disponible. Le filtrage collaboratif sera desactive.")
    print("   Pour l'installer, vous avez besoin de Microsoft Visual C++ Build Tools.")
    print("   L'interface fonctionnera avec le filtrage base sur le contenu uniquement.")

# Variables globales
df_movies = None
df_ratings = None
model = None
reader = None
data = None
trainset = None
testset = None


def generate_mock_data():
    """
    Génère des données mock pour tester l'interface sans accès cloud.
    """
    print("WARNING: Generation de donnees mock pour le test de l'interface...")
    
    # Générer des films mock avec genres
    num_movies = 200
    genres = ['Action', 'Comedy', 'Drama', 'Horror', 'Romance', 'Sci-Fi', 'Thriller', 'Adventure']
    
    movies_data = []
    for i in range(1, num_movies + 1):
        movie = {
            'movieId': i,
            'title': f'Movie {i}'
        }
        # Ajouter des genres aléatoires (multi-hot encoding)
        for genre in genres:
            movie[genre] = np.random.choice([0, 1], p=[0.7, 0.3])
        movies_data.append(movie)
    
    df_movies_mock = pd.DataFrame(movies_data)
    
    # Générer des ratings mock
    num_users = 50
    num_ratings = 500
    
    ratings_data = []
    for _ in range(num_ratings):
        ratings_data.append({
            'userId': np.random.randint(1, num_users + 1),
            'movieId': np.random.randint(1, num_movies + 1),
            'rating': np.random.choice([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0])
        })
    
    df_ratings_mock = pd.DataFrame(ratings_data)
    df_ratings_mock = df_ratings_mock.drop_duplicates(subset=['userId', 'movieId'])
    
    return df_movies_mock, df_ratings_mock


def load_data(timeout_seconds=None):
    """
    Charge les données depuis BigQuery ou génère des données mock si l'accès cloud n'est pas disponible.
    Filtre automatiquement les entrées avec movieId ou rating NULL.
    
    Args:
        timeout_seconds: Timeout pour les requêtes BigQuery (optionnel)
    """
    global df_movies, df_ratings, model, reader, data, trainset, testset
    
    try:
        from google.cloud import bigquery
        
        # Essayer de se connecter à BigQuery
        client = bigquery.Client(project="students-group3")
        
        # Movies encodés
        query_movies = """
        SELECT *
        FROM `students-group3.MovieData.movies_encoded`
        """
        df_movies = client.query(query_movies).to_dataframe()
        
        # Ratings - filtrer les NULL movieId et rating
        query_ratings = """
        SELECT userId, movieId, rating
        FROM `students-group3.MovieData.ratings_cleaned`
        WHERE movieId IS NOT NULL AND rating IS NOT NULL
        """
        df_ratings = client.query(query_ratings).to_dataframe()
        
        # Filtrer aussi les NaN au cas où
        if df_ratings is not None and len(df_ratings) > 0:
            df_ratings = df_ratings.dropna(subset=['movieId', 'rating'])
        
        print("OK: Donnees chargees depuis BigQuery")
        if df_ratings is not None:
            print(f"   Ratings charges: {len(df_ratings)} (NULL values filtrees)")
        
    except Exception as e:
        print(f"WARNING: Impossible de se connecter a BigQuery: {e}")
        print("INFO: Utilisation de donnees mock pour le test de l'interface...")
        df_movies, df_ratings = generate_mock_data()
    
    # Initialiser le modèle avec les données disponibles (seulement si surprise est disponible)
    if SURPRISE_AVAILABLE and df_ratings is not None and len(df_ratings) > 0:
        try:
            reader = Reader(rating_scale=(0.5, 5.0))
            data = Dataset.load_from_df(df_ratings[['userId', 'movieId', 'rating']], reader)
            
            # Si on a assez de données, diviser en train/test
            if len(df_ratings) > 10:
                trainset, testset = train_test_split(data, test_size=0.2, random_state=42)
            else:
                trainset = data.build_full_trainset()
                testset = trainset.build_testset()
            
            # Créer et entraîner le modèle
            model = SVD(n_factors=50, n_epochs=20, lr_all=0.005, reg_all=0.02)
            model.fit(trainset)
            
            # Tester le modèle si possible
            try:
                predictions = model.test(testset)
                rmse = accuracy.rmse(predictions, verbose=False)
                print(f"OK: Modele collaboratif entraine - Test RMSE: {rmse:.4f}")
            except Exception as e:
                print(f"WARNING: Erreur lors du test du modele: {e}")
                print("OK: Modele entraine (test ignore)")
        except Exception as e:
            print(f"WARNING: Erreur lors de l'initialisation du modele collaboratif: {e}")
            model = None
    else:
        if not SURPRISE_AVAILABLE:
            print("INFO: Mode filtrage base sur le contenu uniquement (surprise non disponible)")
        model = None


# Charger les données au démarrage
load_data()


# Fonctions de recommandation (identiques à Modeling.ipynb)
def recommend_collaborative(user_id, top_n=10, df_movies=None, df_ratings=None, model=None):
    # Utiliser les variables globales si non fournies
    if df_movies is None:
        df_movies = globals()['df_movies']
    if df_ratings is None:
        df_ratings = globals()['df_ratings']
    if model is None:
        model = globals()['model']
    
    if not SURPRISE_AVAILABLE:
        raise ValueError("Le filtrage collaboratif nécessite la bibliothèque 'surprise' qui n'est pas disponible.")
    
    if df_movies is None or df_ratings is None or model is None:
        raise ValueError("Les données ou le modèle ne sont pas initialisés. Appelez load_data() d'abord.")
    
    # Filtrer les NULL/NaN dans df_ratings
    df_ratings_clean = df_ratings.dropna(subset=['movieId', 'rating'])
    
    # Films déjà notés (exclure NULL)
    rated_movies = df_ratings_clean[df_ratings_clean['userId'] == user_id]['movieId'].tolist()
    
    # Films à prédire
    movies_to_predict = df_movies[~df_movies['movieId'].isin(rated_movies)]
    
    # Prédictions
    predictions = []
    for movie in movies_to_predict['movieId']:
        pred = model.predict(user_id, movie)
        predictions.append((movie, pred.est))
    
    # Créer DataFrame pour conserver ordre et score
    pred_df = pd.DataFrame(predictions, columns=['movieId', 'pred_rating'])
    
    # Fusionner avec titres
    pred_df = pred_df.merge(df_movies[['movieId', 'title']], on='movieId', how='left')
    
    # Retourner top_n trié par note prédite
    return pred_df.sort_values('pred_rating', ascending=False).head(top_n)


def build_user_profile(user_id, df_ratings=None, df_movies=None):
    # Utiliser les variables globales si non fournies
    if df_movies is None:
        df_movies = globals()['df_movies']
    if df_ratings is None:
        df_ratings = globals()['df_ratings']
    
    if df_movies is None or df_ratings is None:
        raise ValueError("Les données ne sont pas initialisées. Appelez load_data() d'abord.")
    
    # Filtrer les NULL/NaN dans df_ratings
    df_ratings_clean = df_ratings.dropna(subset=['movieId', 'rating'])
    
    # Récupérer les films notés par l'utilisateur (exclure NULL)
    user_ratings = df_ratings_clean[df_ratings_clean['userId'] == user_id].merge(df_movies, on='movieId')
    
    if user_ratings.empty:
        return None  # Nouvel utilisateur sans ratings
    
    # Colonnes des genres (Multi-Hot)
    genre_columns = [col for col in df_movies.columns if col not in ['movieId', 'title']]
    
    # Calculer la moyenne pondérée
    user_profile = (user_ratings[genre_columns].T @ user_ratings['rating']).T
    user_profile /= user_ratings['rating'].sum()
    
    return user_profile


def recommend_content_based(user_id, top_n=10, df_movies=None, df_ratings=None):
    # Utiliser les variables globales si non fournies
    if df_movies is None:
        df_movies = globals()['df_movies']
    if df_ratings is None:
        df_ratings = globals()['df_ratings']
    
    if df_movies is None or df_ratings is None:
        raise ValueError("Les données ne sont pas initialisées. Appelez load_data() d'abord.")
    
    profile = build_user_profile(user_id, df_ratings, df_movies)
    
    if profile is None:
        # Cold start complet → recommander films populaires ou au hasard
        return df_movies.head(top_n)[['movieId', 'title']]
    
    # Colonnes de genres
    genre_columns = [col for col in df_movies.columns if col not in ['movieId', 'title']]
    
    # Similarité cosine
    movie_vectors = df_movies[genre_columns]
    sim = cosine_similarity(profile.values.reshape(1, -1), movie_vectors)[0]
    
    # Copier le dataframe pour ajouter les scores
    df_movies_copy = df_movies.copy()
    df_movies_copy['score'] = sim
    
    # Filtrer les NULL/NaN dans df_ratings et exclure films déjà vus
    df_ratings_clean = df_ratings.dropna(subset=['movieId', 'rating'])
    seen_movies = df_ratings_clean[df_ratings_clean['userId'] == user_id]['movieId'].tolist()
    
    # Retourner les top N films non vus triés par score
    return df_movies_copy[~df_movies_copy['movieId'].isin(seen_movies)].sort_values('score', ascending=False).head(top_n)


def recommend_hybrid(user_id, top_n=10, df_movies=None, df_ratings=None):
    # Utiliser les variables globales si non fournies
    if df_movies is None:
        df_movies = globals()['df_movies']
    if df_ratings is None:
        df_ratings = globals()['df_ratings']
    
    if df_movies is None or df_ratings is None:
        raise ValueError("Les données ne sont pas initialisées. Appelez load_data() d'abord.")
    
    # Si surprise n'est pas disponible, utiliser uniquement content-based
    if not SURPRISE_AVAILABLE:
        return recommend_content_based(user_id, top_n, df_movies, df_ratings)
    
    # Filtrer les NULL/NaN dans df_ratings pour compter les ratings valides
    df_ratings_clean = df_ratings.dropna(subset=['movieId', 'rating'])
    n_ratings = df_ratings_clean[df_ratings_clean['userId'] == user_id].shape[0]

    if n_ratings == 0:
        # Cold start complet → Content-Based ou premiers films
        return recommend_content_based(user_id, top_n, df_movies, df_ratings)
    
    elif n_ratings < 10:
        # Peu de données → Content-Based
        return recommend_content_based(user_id, top_n, df_movies, df_ratings)
    
    else:
        # Utilisateur actif → SVD pur (si disponible)
        model = globals()['model']
        if model is not None:
            try:
                return recommend_collaborative(user_id, top_n, df_movies, df_ratings, model)
            except Exception:
                # Fallback sur content-based si collaborative échoue
                return recommend_content_based(user_id, top_n, df_movies, df_ratings)
        else:
            return recommend_content_based(user_id, top_n, df_movies, df_ratings)


def reload_ratings_from_bigquery():
    """
    Recharge les ratings depuis BigQuery (utile après avoir ajouté de nouveaux ratings).
    Filtre automatiquement les entrées avec movieId ou rating NULL.
    
    Returns:
        True si le rechargement a réussi, False sinon
    """
    global df_ratings
    
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project="students-group3")
        
        # Recharger les ratings depuis BigQuery (filtrer NULL)
        query_ratings = """
        SELECT userId, movieId, rating
        FROM `students-group3.MovieData.ratings_cleaned`
        WHERE movieId IS NOT NULL AND rating IS NOT NULL
        """
        df_ratings_new = client.query(query_ratings).to_dataframe()
        
        # Filtrer aussi les NaN au cas où
        if df_ratings_new is not None and len(df_ratings_new) > 0:
            df_ratings_new = df_ratings_new.dropna(subset=['movieId', 'rating'])
            df_ratings = df_ratings_new
            print(f"✅ Ratings recharges depuis BigQuery: {len(df_ratings)} ratings")
            return True
        else:
            print("⚠️ Aucun rating trouve dans BigQuery")
            return False
            
    except Exception as e:
        print(f"⚠️ Erreur lors du rechargement depuis BigQuery: {e}")
        return False


# Fonction pour ajouter de nouveaux ratings
def add_new_user_ratings(user_id: int, ratings: List[Dict[str, float]], auto_retrain: bool = True, reload_from_bigquery: bool = False):
    """
    Ajoute de nouveaux ratings pour un utilisateur (nouveau ou existant).
    Optionnellement re-entraîne le modèle après l'ajout.
    
    Args:
        user_id: ID de l'utilisateur
        ratings: Liste de dictionnaires avec 'movieId' et 'rating'
                 Exemple: [{'movieId': 1, 'rating': 4.5}, {'movieId': 2, 'rating': 3.0}]
        auto_retrain: Si True, re-entraîne automatiquement le modèle après l'ajout (défaut: True)
        reload_from_bigquery: Si True, recharge les données depuis BigQuery avant d'ajouter (défaut: False)
    
    Returns:
        RMSE du modèle re-entraîné (ou None si pas de re-entraînement ou surprise non disponible)
    """
    global df_ratings, df_movies
    
    # Recharger depuis BigQuery si demandé (utile après avoir sauvegardé dans BigQuery)
    if reload_from_bigquery:
        print("🔄 Rechargement des ratings depuis BigQuery...")
        reload_ratings_from_bigquery()
    
    if df_ratings is None or df_movies is None:
        raise ValueError("Les données ne sont pas initialisées. Appelez load_data() d'abord.")
    
    # Filtrer les NaN/NULL dans df_ratings existant pour éviter les problèmes
    if df_ratings is not None and len(df_ratings) > 0:
        df_ratings = df_ratings.dropna(subset=['movieId', 'rating'])
    
    # Créer le DataFrame des nouveaux ratings
    new_ratings = pd.DataFrame(ratings)
    new_ratings['userId'] = user_id
    
    # Filtrer les NaN dans les nouveaux ratings
    new_ratings = new_ratings.dropna(subset=['movieId', 'rating'])
    
    if new_ratings.empty:
        print("⚠️ Aucun rating valide a ajouter (tous les movieId/rating sont NULL)")
        return None
    
    # Vérifier que les movieId existent
    valid_movies = new_ratings['movieId'].isin(df_movies['movieId'])
    if not valid_movies.all():
        invalid_movies = new_ratings[~valid_movies]['movieId'].tolist()
        print(f"Attention: Certains movieId n'existent pas: {invalid_movies}")
        new_ratings = new_ratings[valid_movies]
    
    if new_ratings.empty:
        print("⚠️ Aucun rating valide apres verification des movieId")
        return None
    
    # Vérifier les doublons (même utilisateur, même film)
    existing_mask = (
        (df_ratings['userId'] == user_id) & 
        (df_ratings['movieId'].isin(new_ratings['movieId']))
    )
    
    if existing_mask.any():
        # Mettre à jour les ratings existants
        existing_movie_ids = df_ratings[existing_mask]['movieId'].tolist()
        print(f"Mise a jour de {len(existing_movie_ids)} ratings existants")
        
        # Supprimer les anciens ratings
        df_ratings = df_ratings[~existing_mask]
        
        # Garder seulement les nouveaux ratings qui ne sont pas des mises à jour
        new_ratings = new_ratings[~new_ratings['movieId'].isin(existing_movie_ids)]
    
    # Ajouter les nouveaux ratings
    if not new_ratings.empty:
        df_ratings = pd.concat([df_ratings, new_ratings], ignore_index=True)
        print(f"Ajout de {len(new_ratings)} nouveaux ratings pour l'utilisateur {user_id}")
    
    # Re-entraîner automatiquement si demandé
    rmse = None
    if auto_retrain:
        print("Re-entraînement automatique du modèle...")
        try:
            rmse = retrain_model()
            if rmse is not None:
                print(f"✅ Modèle re-entraîné avec succès! RMSE: {rmse:.4f}")
            else:
                print("ℹ️ Re-entraînement ignoré (surprise non disponible ou données insuffisantes)")
        except Exception as e:
            print(f"⚠️ Erreur lors du re-entraînement automatique: {e}")
            print("   Le système continuera avec le modèle existant ou utilisera le filtrage basé sur le contenu")
    
    return rmse


# Fonction pour re-entraîner le modèle
def retrain_model():
    """
    Re-entraîne le modèle avec les données mises à jour.
    Fonctionne avec les données réelles ou mock (fallback automatique).
    
    Returns:
        RMSE du modèle re-entraîné (ou None si surprise n'est pas disponible ou données insuffisantes)
    """
    global model, trainset, testset, data, reader, df_ratings
    
    if not SURPRISE_AVAILABLE:
        print("INFO: Re-entrainement impossible: bibliotheque 'surprise' non disponible")
        print("      Le système utilisera le filtrage basé sur le contenu uniquement")
        return None
    
    # Fallback: utiliser mock data si pas de données disponibles
    if df_ratings is None or len(df_ratings) == 0:
        print("WARNING: Les données de ratings ne sont pas disponibles")
        print("         Génération de données mock pour le re-entraînement...")
        try:
            df_movies_temp, df_ratings_temp = generate_mock_data()
            if df_ratings_temp is None or len(df_ratings_temp) == 0:
                raise ValueError("Impossible de générer des données mock")
            df_ratings = df_ratings_temp
            print("✅ Données mock générées pour le re-entraînement")
        except Exception as e:
            print(f"ERROR: Impossible de générer des données mock: {e}")
            return None
    
    try:
        # Vérifier qu'on a assez de données pour entraîner
        if len(df_ratings) < 10:
            print(f"WARNING: Pas assez de données pour re-entraîner ({len(df_ratings)} ratings)")
            print("         Le système utilisera le filtrage basé sur le contenu")
            return None
        
        # Filtrer les NULL/NaN avant de charger dans Surprise
        df_ratings_clean = df_ratings.dropna(subset=['movieId', 'rating'])
        
        if len(df_ratings_clean) == 0:
            print("WARNING: Aucun rating valide apres filtrage NULL")
            return None
        
        # Recharger les données dans Surprise
        reader = Reader(rating_scale=(0.5, 5.0))
        data = Dataset.load_from_df(df_ratings_clean[['userId', 'movieId', 'rating']], reader)
        
        # Diviser en train/test (ou utiliser toutes les données si peu de données)
        if len(df_ratings) > 10:
            trainset, testset = train_test_split(data, test_size=0.2, random_state=42)
        else:
            trainset = data.build_full_trainset()
            testset = trainset.build_testset()
        
        # Re-créer et entraîner le modèle
        print("🔄 Entraînement du modèle SVD...")
        model = SVD(n_factors=50, n_epochs=20, lr_all=0.005, reg_all=0.02)
        model.fit(trainset)
        
        # Tester sur le testset si possible
        try:
            predictions = model.test(testset)
            rmse = accuracy.rmse(predictions, verbose=False)
            print(f"✅ Modèle re-entraîné avec succès! RMSE: {rmse:.4f}")
            return rmse
        except Exception as e:
            print(f"⚠️ Erreur lors du test du modèle: {e}")
            print("✅ Modèle entraîné (test ignoré)")
            return None
        
    except Exception as e:
        print(f"WARNING: Erreur lors du re-entrainement: {e}")
        import traceback
        traceback.print_exc()
        print("⚠️ Le système continuera avec le modèle existant ou utilisera le filtrage basé sur le contenu")
        return None

