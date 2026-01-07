"""
Interface Streamlit pour le système de recommandation de films
"""

import streamlit as st
import pandas as pd
import sys

# Configuration de la page (doit être en premier)
st.set_page_config(
    page_title="Système de Recommandation de Films",
    page_icon="🎬",
    layout="wide"
)

# Afficher un message de chargement
try:
    from recommender import (
        df_movies, df_ratings, 
        recommend_hybrid, recommend_collaborative, recommend_content_based,
        add_new_user_ratings, retrain_model, load_data
    )
    
    # Charger les données si elles ne sont pas déjà chargées
    if df_movies is None or df_ratings is None:
        with st.spinner("Chargement des données depuis BigQuery..."):
            load_data()
            # Recharger les références
            import recommender
            df_movies = recommender.df_movies
            df_ratings = recommender.df_ratings
    
    # Afficher un message de succès
    if df_movies is not None and df_ratings is not None:
        st.success(f"✅ Système chargé: {len(df_movies)} films, {len(df_ratings)} ratings")
        
except Exception as e:
    st.error(f"Erreur lors du chargement du système: {str(e)}")
    st.exception(e)
    st.info("Veuillez vérifier votre connexion à BigQuery et vos credentials GCP.")
    st.stop()

st.title("🎬 Système de Recommandation de Films")
st.markdown("---")

# Sidebar pour la navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choisir une section",
    ["📊 Explorer les Films", "⭐ Ajouter des Ratings", "🎯 Obtenir des Recommandations"]
)

# Initialiser les variables de session
if 'new_user_id' not in st.session_state:
    try:
        if df_ratings is not None and len(df_ratings) > 0:
            st.session_state.new_user_id = int(df_ratings['userId'].max() + 1)
        else:
            st.session_state.new_user_id = 1
    except Exception as e:
        st.session_state.new_user_id = 1
        st.warning(f"Erreur lors de l'initialisation de l'ID utilisateur: {e}")

if 'user_ratings' not in st.session_state:
    st.session_state.user_ratings = []

if 'model_updated' not in st.session_state:
    st.session_state.model_updated = False


# Page 1: Explorer les Films
if page == "📊 Explorer les Films":
    st.header("Explorer les Films")
    
    if df_movies is not None:
        st.info(f"Total de films disponibles: {len(df_movies)}")
        
        # Recherche de films
        search_term = st.text_input("🔍 Rechercher un film par titre", "")
        
        # Filtrage
        if search_term:
            filtered_movies = df_movies[df_movies['title'].str.contains(search_term, case=False, na=False)]
        else:
            filtered_movies = df_movies
        
        # Nombre de résultats à afficher
        num_results = st.slider("Nombre de films à afficher", 10, 100, 20)
        
        # Afficher les films
        if len(filtered_movies) > 0:
            st.subheader(f"Résultats ({len(filtered_movies)} films trouvés)")
            
            # Afficher sous forme de tableau
            display_cols = ['movieId', 'title']
            st.dataframe(
                filtered_movies[display_cols].head(num_results),
                use_container_width=True,
                hide_index=True
            )
            
            # Informations sur un film sélectionné
            st.subheader("Détails d'un film")
            movie_ids = filtered_movies['movieId'].tolist()
            selected_movie_id = st.selectbox(
                "Sélectionner un film pour voir les détails",
                movie_ids[:100],  # Limiter à 100 pour les performances
                format_func=lambda x: f"{x} - {filtered_movies[filtered_movies['movieId']==x]['title'].values[0]}"
            )
            
            if selected_movie_id:
                movie_info = df_movies[df_movies['movieId'] == selected_movie_id].iloc[0]
                st.write(f"**Titre:** {movie_info['title']}")
                st.write(f"**ID:** {movie_info['movieId']}")
                
                # Afficher les genres (colonnes qui ne sont pas movieId ou title)
                genre_cols = [col for col in df_movies.columns if col not in ['movieId', 'title']]
                genres = [col for col in genre_cols if movie_info[col] == 1]
                if genres:
                    st.write(f"**Genres:** {', '.join(genres)}")
        else:
            st.warning("Aucun film trouvé avec ce terme de recherche.")
    else:
        st.error("Les données des films ne sont pas disponibles.")


# Page 2: Ajouter des Ratings
elif page == "⭐ Ajouter des Ratings":
    st.header("Ajouter des Ratings pour un Nouvel Utilisateur")
    
    st.info(f"**ID Utilisateur:** {st.session_state.new_user_id}")
    
    # Section pour ajouter des ratings
    st.subheader("Ajouter un Rating")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Sélectionner un film
        if df_movies is not None:
            movie_options = df_movies[['movieId', 'title']].apply(
                lambda x: f"{x['movieId']} - {x['title']}", axis=1
            ).tolist()
            
            selected_movie = st.selectbox(
                "Sélectionner un film",
                movie_options
            )
            
            movie_id = int(selected_movie.split(" - ")[0])
        else:
            movie_id = st.number_input("ID du film", min_value=1, step=1)
    
    with col2:
        rating = st.slider(
            "Note (0.5 à 5.0)",
            min_value=0.5,
            max_value=5.0,
            step=0.5,
            value=3.0
        )
    
    # Bouton pour ajouter le rating
    if st.button("➕ Ajouter ce Rating", type="primary"):
        new_rating = {
            'movieId': movie_id,
            'rating': float(rating)
        }
        st.session_state.user_ratings.append(new_rating)
        st.success(f"Rating ajouté: Film {movie_id} = {rating} ⭐")
        st.rerun()
    
    # Afficher les ratings ajoutés
    if st.session_state.user_ratings:
        st.subheader("Ratings Ajoutés")
        ratings_df = pd.DataFrame(st.session_state.user_ratings)
        
        # Ajouter les titres des films
        if df_movies is not None:
            ratings_df = ratings_df.merge(
                df_movies[['movieId', 'title']],
                on='movieId',
                how='left'
            )
            display_cols = ['movieId', 'title', 'rating']
        else:
            display_cols = ['movieId', 'rating']
        
        st.dataframe(ratings_df[display_cols], use_container_width=True, hide_index=True)
        
        # Boutons d'action
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Sauvegarder et Mettre à Jour le Système", type="primary"):
                try:
                    # Ajouter les ratings au système
                    add_new_user_ratings(
                        st.session_state.new_user_id,
                        st.session_state.user_ratings
                    )
                    
                    # Re-entraîner le modèle
                    with st.spinner("Re-entraînement du modèle en cours..."):
                        rmse = retrain_model()
                    
                    st.session_state.model_updated = True
                    st.success(f"✅ Système mis à jour! RMSE: {rmse:.4f}")
                    st.info("Vous pouvez maintenant obtenir des recommandations pour cet utilisateur!")
                    
                except Exception as e:
                    st.error(f"Erreur lors de la mise à jour: {str(e)}")
        
        with col2:
            if st.button("🔄 Réinitialiser les Ratings"):
                st.session_state.user_ratings = []
                st.rerun()
        
        with col3:
            if st.button("🗑️ Supprimer le Dernier Rating"):
                if st.session_state.user_ratings:
                    st.session_state.user_ratings.pop()
                    st.rerun()


# Page 3: Obtenir des Recommandations
elif page == "🎯 Obtenir des Recommandations":
    st.header("Obtenir des Recommandations")
    
    # Sélection de l'utilisateur
    if df_ratings is not None:
        available_users = sorted(df_ratings['userId'].unique().tolist())
        
        col1, col2 = st.columns(2)
        
        with col1:
            user_choice = st.radio(
                "Type d'utilisateur",
                ["Utilisateur existant", "Nouvel utilisateur (avec ratings)"]
            )
        
        with col2:
            if user_choice == "Utilisateur existant":
                selected_user_id = st.selectbox(
                    "Sélectionner un utilisateur",
                    available_users[:1000]  # Limiter pour les performances
                )
            else:
                if st.session_state.user_ratings:
                    selected_user_id = st.session_state.new_user_id
                    st.info(f"Utilisateur: {selected_user_id} (avec {len(st.session_state.user_ratings)} ratings)")
                else:
                    st.warning("⚠️ Aucun rating ajouté. Veuillez d'abord ajouter des ratings dans la section 'Ajouter des Ratings'.")
                    selected_user_id = None
    else:
        st.error("Les données de ratings ne sont pas disponibles.")
        selected_user_id = None
    
    # Sélection de la méthode de recommandation
    if selected_user_id is not None:
        st.subheader("Méthode de Recommandation")
        method = st.selectbox(
            "Choisir la méthode",
            ["Hybride (recommandé)", "Collaborative Filtering", "Content-Based Filtering"]
        )
        
        # Nombre de recommandations
        top_n = st.slider("Nombre de recommandations", 5, 50, 10)
        
        # Bouton pour obtenir les recommandations
        if st.button("🎯 Obtenir les Recommandations", type="primary"):
            try:
                with st.spinner("Calcul des recommandations en cours..."):
                    if method == "Hybride (recommandé)":
                        recommendations = recommend_hybrid(selected_user_id, top_n=top_n)
                    elif method == "Collaborative Filtering":
                        recommendations = recommend_collaborative(selected_user_id, top_n=top_n)
                    else:  # Content-Based
                        recommendations = recommend_content_based(selected_user_id, top_n=top_n)
                
                if recommendations is not None and len(recommendations) > 0:
                    st.success(f"✅ {len(recommendations)} recommandations trouvées!")
                    
                    # Afficher les recommandations
                    st.subheader("🎬 Films Recommandés")
                    
                    # Déterminer la colonne de score
                    if 'pred_rating' in recommendations.columns:
                        score_col = 'pred_rating'
                        score_label = "Note Prédite"
                    elif 'score' in recommendations.columns:
                        score_col = 'score'
                        score_label = "Score de Similarité"
                    else:
                        score_col = None
                    
                    # Afficher sous forme de tableau
                    display_cols = ['movieId', 'title']
                    if score_col:
                        display_cols.append(score_col)
                    
                    recommendations_display = recommendations[display_cols].copy()
                    if score_col:
                        recommendations_display = recommendations_display.rename(
                            columns={score_col: score_label}
                        )
                    
                    st.dataframe(
                        recommendations_display,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Statistiques de l'utilisateur
                    if df_ratings is not None:
                        user_ratings_count = len(df_ratings[df_ratings['userId'] == selected_user_id])
                        if user_ratings_count > 0:
                            avg_rating = df_ratings[df_ratings['userId'] == selected_user_id]['rating'].mean()
                            st.info(
                                f"📊 Statistiques utilisateur {selected_user_id}: "
                                f"{user_ratings_count} ratings, moyenne: {avg_rating:.2f}"
                            )
                else:
                    st.warning("Aucune recommandation disponible pour cet utilisateur.")
                    
            except Exception as e:
                st.error(f"Erreur lors du calcul des recommandations: {str(e)}")
                st.exception(e)


# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Système de Recommandation de Films - GCP</div>",
    unsafe_allow_html=True
)

