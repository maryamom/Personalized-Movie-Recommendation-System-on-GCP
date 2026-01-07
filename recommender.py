"""
Système de recommandation de films
Encapsule la logique de Modeling.ipynb avec support pour l'ajout de nouveaux utilisateurs
et le re-entraînement du modèle.
"""

import pandas as pd
from surprise import Dataset, Reader, SVD, accuracy
from surprise.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict


# Initialisation (identique à Modeling.ipynb)
client = bigquery.Client(project="students-group3")

# Movies encodés
query_movies = """
SELECT *
FROM `students-group3.MovieData.movies_encoded`
"""
df_movies = client.query(query_movies).to_dataframe()

# Ratings
query_ratings = """
SELECT *
FROM `students-group3.MovieData.ratings_cleaned`
"""
df_ratings = client.query(query_ratings).to_dataframe()

# Collaborative Filtering (identique à Modeling.ipynb)
reader = Reader(rating_scale=(0.5, 5.0))
data = Dataset.load_from_df(df_ratings[['userId', 'movieId', 'rating']], reader)
trainset, testset = train_test_split(data, test_size=0.2, random_state=42)

model = SVD(n_factors=50, n_epochs=20, lr_all=0.005, reg_all=0.02)
model.fit(trainset)

predictions = model.test(testset)
rmse = accuracy.rmse(predictions)
print("Test RMSE:", rmse)


# Fonctions de recommandation (identiques à Modeling.ipynb)
def recommend_collaborative(user_id, top_n=10, df_movies=df_movies, df_ratings=df_ratings, model=model):
    # Films déjà notés
    rated_movies = df_ratings[df_ratings['userId'] == user_id]['movieId'].tolist()
    
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


def build_user_profile(user_id, df_ratings=df_ratings, df_movies=df_movies):
    # Récupérer les films notés par l'utilisateur
    user_ratings = df_ratings[df_ratings['userId'] == user_id].merge(df_movies, on='movieId')
    
    if user_ratings.empty:
        return None  # Nouvel utilisateur sans ratings
    
    # Colonnes des genres (Multi-Hot)
    genre_columns = [col for col in df_movies.columns if col not in ['movieId', 'title']]
    
    # Calculer la moyenne pondérée
    user_profile = (user_ratings[genre_columns].T @ user_ratings['rating']).T
    user_profile /= user_ratings['rating'].sum()
    
    return user_profile


def recommend_content_based(user_id, top_n=10, df_movies=df_movies, df_ratings=df_ratings):
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
    
    # Exclure films déjà vus
    seen_movies = df_ratings[df_ratings['userId'] == user_id]['movieId'].tolist()
    
    # Retourner les top N films non vus triés par score
    return df_movies_copy[~df_movies_copy['movieId'].isin(seen_movies)].sort_values('score', ascending=False).head(top_n)


def recommend_hybrid(user_id, top_n=10, df_movies=df_movies, df_ratings=df_ratings):
    n_ratings = df_ratings[df_ratings['userId'] == user_id].shape[0]

    if n_ratings == 0:
        # Cold start complet → Content-Based ou premiers films
        return recommend_content_based(user_id, top_n, df_movies, df_ratings)
    
    elif n_ratings < 10:
        # Peu de données → Content-Based
        return recommend_content_based(user_id, top_n, df_movies, df_ratings)
    
    else:
        # Utilisateur actif → SVD pur
        return recommend_collaborative(user_id, top_n, df_movies, df_ratings, model)


# Fonction pour ajouter de nouveaux ratings
def add_new_user_ratings(user_id: int, ratings: List[Dict[str, float]]):
    """
    Ajoute de nouveaux ratings pour un utilisateur (nouveau ou existant).
    
    Args:
        user_id: ID de l'utilisateur
        ratings: Liste de dictionnaires avec 'movieId' et 'rating'
                 Exemple: [{'movieId': 1, 'rating': 4.5}, {'movieId': 2, 'rating': 3.0}]
    """
    global df_ratings
    
    # Créer le DataFrame des nouveaux ratings
    new_ratings = pd.DataFrame(ratings)
    new_ratings['userId'] = user_id
    
    # Vérifier que les movieId existent
    valid_movies = new_ratings['movieId'].isin(df_movies['movieId'])
    if not valid_movies.all():
        invalid_movies = new_ratings[~valid_movies]['movieId'].tolist()
        print(f"Attention: Certains movieId n'existent pas: {invalid_movies}")
        new_ratings = new_ratings[valid_movies]
    
    # Vérifier les doublons (même utilisateur, même film)
    existing_mask = (
        (df_ratings['userId'] == user_id) & 
        (df_ratings['movieId'].isin(new_ratings['movieId']))
    )
    
    if existing_mask.any():
        # Mettre à jour les ratings existants
        existing_movie_ids = df_ratings[existing_mask]['movieId'].tolist()
        print(f"Mise à jour de {len(existing_movie_ids)} ratings existants")
        
        # Supprimer les anciens ratings
        df_ratings = df_ratings[~existing_mask]
        
        # Garder seulement les nouveaux ratings qui ne sont pas des mises à jour
        new_ratings = new_ratings[~new_ratings['movieId'].isin(existing_movie_ids)]
    
    # Ajouter les nouveaux ratings
    if not new_ratings.empty:
        df_ratings = pd.concat([df_ratings, new_ratings], ignore_index=True)
        print(f"Ajout de {len(new_ratings)} nouveaux ratings pour l'utilisateur {user_id}")


# Fonction pour re-entraîner le modèle
def retrain_model():
    """
    Re-entraîne le modèle avec les données mises à jour.
    
    Returns:
        RMSE du modèle re-entraîné
    """
    global model, trainset, testset, data
    
    # Recharger les données dans Surprise
    data = Dataset.load_from_df(df_ratings[['userId', 'movieId', 'rating']], reader)
    
    # Diviser en train/test
    trainset, testset = train_test_split(data, test_size=0.2, random_state=42)
    
    # Re-créer et entraîner le modèle
    model = SVD(n_factors=50, n_epochs=20, lr_all=0.005, reg_all=0.02)
    model.fit(trainset)
    
    # Tester sur le testset
    predictions = model.test(testset)
    rmse = accuracy.rmse(predictions)
    print("Test RMSE après re-entraînement:", rmse)
    
    return rmse

