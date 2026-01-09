"""
Professional Flask app for Movie Recommendation System
SaaS-style interface with real-time search, genre filtering, and user management
"""

from flask import Flask, render_template_string, request, jsonify
import sys
import os
import json
import pandas as pd

app = Flask(__name__)

# Try to import recommender module
recommender_module = None
try:
    import recommender
    recommender_module = recommender
    
    # Load data if not loaded
    if recommender_module.df_movies is None or recommender_module.df_ratings is None:
        print("📦 Loading data...")
        try:
            recommender_module.load_data(timeout_seconds=30)
        except Exception as e:
            print(f"⚠️ Warning during data loading: {e}")
    
    if hasattr(recommender_module, 'df_movies') and recommender_module.df_movies is not None:
        movies_count = len(recommender_module.df_movies)
        ratings_count = len(recommender_module.df_ratings) if recommender_module.df_ratings is not None else 0
        print(f"✅ Recommender module loaded successfully")
        print(f"   Movies: {movies_count}, Ratings: {ratings_count}")
    else:
        print("⚠️ Warning: Recommender module loaded but data not available")
except Exception as e:
    import traceback
    print(f"⚠️ Warning: Could not import recommender module: {e}")
    traceback.print_exc()

def get_genres_from_movies():
    """Extract available genres from movies dataframe"""
    if recommender_module is None or recommender_module.df_movies is None:
        return []
    
    # Get genre columns (exclude movieId and title)
    genre_columns = [col for col in recommender_module.df_movies.columns 
                    if col not in ['movieId', 'title']]
    
    # Clean genre names (remove underscores, capitalize)
    genres = []
    for col in genre_columns:
        clean_name = col.replace('_', ' ').replace('no genres listed', '').strip()
        if clean_name:
            genres.append(clean_name.title())
    
    return sorted(set(genres))

def get_movie_image_url(movie_id, title):
    """Get movie poster image URL (using placeholder service)"""
    # Using placeholder service - in production, use TMDB API or similar
    return f"https://via.placeholder.com/300x450/0ea5e9/ffffff?text={title[:20]}"

# HTML Template with Professional SaaS Design
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MovieRec Pro - AI-Powered Movie Recommendations</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: rgba(14, 165, 233, 0.8);
            --primary-dark: rgba(14, 165, 233, 1);
            --sky-blue: rgba(135, 206, 235, 0.6);
            --sky-blue-light: rgba(135, 206, 235, 0.3);
            --white: #ffffff;
            --black: #000000;
            --light-gray: #f5f5f5;
            --gray: #808080;
            --gray-light: #e0e0e0;
            --gray-dark: #404040;
            --dark: #1a1a1a;
            --border: #d0d0d0;
            --shadow: rgba(0, 0, 0, 0.1);
        }
        
        * {
            transition: all 0.3s ease;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--white);
            min-height: 100vh;
            padding: 0;
            margin: 0;
            color: var(--black);
            display: flex;
        }
        
        /* Scroll Animation Classes */
        .fade-in {
            opacity: 0;
            transform: translateY(30px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }
        
        .fade-in.visible {
            opacity: 1;
            transform: translateY(0);
        }
        
        .slide-in-left {
            opacity: 0;
            transform: translateX(-50px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }
        
        .slide-in-left.visible {
            opacity: 1;
            transform: translateX(0);
        }
        
        .slide-in-right {
            opacity: 0;
            transform: translateX(50px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }
        
        .slide-in-right.visible {
            opacity: 1;
            transform: translateX(0);
        }
        
        .scale-in {
            opacity: 0;
            transform: scale(0.9);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }
        
        .scale-in.visible {
            opacity: 1;
            transform: scale(1);
        }
        
        /* Header Navigation */
        .header-nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 70px;
            background: var(--white);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            z-index: 1001;
            display: flex;
            align-items: center;
            padding: 0 2rem;
            border-bottom: 2px solid var(--gray-light);
        }
        
        .header-nav-content {
            width: 100%;
            max-width: 1600px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header-logo {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--black);
            letter-spacing: -0.5px;
        }
        
        .header-actions {
            display: flex;
            align-items: center;
            gap: 2rem;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            color: var(--gray-dark);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--primary);
            animation: pulse 2s infinite;
        }
        
        /* Hero Section - Vertical Layout */
        .hero {
            background: linear-gradient(135deg, var(--sky-blue) 0%, var(--sky-blue-light) 100%);
            padding: 4rem 2rem;
            color: var(--black);
            position: relative;
            overflow: hidden;
            margin-bottom: 2rem;
        }
        
        .hero-content {
            max-width: 1200px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }
        
        .hero-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            letter-spacing: -1px;
            line-height: 1.2;
            color: var(--black);
        }
        
        .hero-subtitle {
            font-size: 1.125rem;
            font-weight: 400;
            margin-bottom: 2rem;
            line-height: 1.6;
            color: var(--gray-dark);
        }
        
        .hero-stats {
            display: flex;
            gap: 3rem;
            flex-wrap: wrap;
        }
        
        .stat-item {
            display: flex;
            flex-direction: column;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
            color: var(--black);
        }
        
        .stat-label {
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--gray-dark);
        }
        
        /* Features Section - Vertical Layout */
        .features-section {
            padding: 3rem 2rem;
            background: var(--white);
            margin-bottom: 2rem;
        }
        
        .features-content {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .section-header {
            margin-bottom: 3rem;
        }
        
        .section-title {
            font-size: 2rem;
            font-weight: 700;
            color: var(--black);
            margin-bottom: 0.75rem;
            letter-spacing: -1px;
        }
        
        .section-subtitle {
            font-size: 1rem;
            color: var(--gray-dark);
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 2rem;
        }
        
        .feature-card {
            padding: 2rem;
            border-radius: 12px;
            border: 2px solid var(--gray-light);
            background: var(--white);
            transition: all 0.3s ease;
        }
        
        .feature-card:hover {
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            transform: translateY(-4px);
            border-color: var(--primary);
            background: rgba(135, 206, 235, 0.05);
        }
        
        .feature-icon {
            width: 48px;
            height: 48px;
            background: var(--sky-blue-light);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1.5rem;
            font-size: 1.5rem;
        }
        
        .feature-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--black);
            margin-bottom: 0.75rem;
        }
        
        .feature-description {
            font-size: 0.9375rem;
            color: var(--gray-dark);
            line-height: 1.6;
        }
        
        /* Header Navigation with Menu */
        .header-nav-menu {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        
        .header-nav-link {
            color: var(--black);
            text-decoration: none;
            font-weight: 500;
            font-size: 0.9375rem;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .header-nav-link:hover {
            background: var(--sky-blue-light);
            color: var(--black);
        }
        
        .header-nav-link.active {
            background: var(--sky-blue);
            color: var(--black);
        }
        
        .main-content {
            margin-left: 0;
            margin-top: 70px;
            flex: 1;
            padding: 0;
            animation: fadeIn 0.5s ease;
            background: var(--white);
            min-height: calc(100vh - 70px);
            display: flex;
            flex-direction: column;
            position: relative;
            z-index: 1;
            width: 100%;
            overflow-x: hidden;
        }
        
        .main-content-wrapper {
            flex: 1;
            display: flex;
            flex-direction: column;
            width: 100%;
            padding: 0;
            margin: 0;
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .card {
            background: var(--white);
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid var(--gray-light);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--gray-light);
        }
        
        .card-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--black);
        }
        
        .search-container {
            position: relative;
            margin-bottom: 1.5rem;
        }
        
        .search-input {
            width: 100%;
            padding: 1rem 1rem 1rem 3rem;
            border: 2px solid var(--gray-light);
            border-radius: 12px;
            font-size: 1rem;
            transition: all 0.3s;
            background: var(--white);
            color: var(--black);
        }
        
        .search-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--sky-blue-light);
        }
        
        .search-icon {
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--gray-dark);
        }
        
        .filters {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }
        
        .filter-group {
            flex: 1;
            min-width: 200px;
        }
        
        .filter-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--dark);
            font-size: 0.875rem;
        }
        
        select {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid var(--gray-light);
            border-radius: 8px;
            font-size: 0.875rem;
            background: var(--white);
            color: var(--black);
            cursor: pointer;
            transition: all 0.3s;
        }
        
        select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--sky-blue-light);
        }
        
        .movies-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }
        
        .movie-card {
            background: var(--white);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border: 1px solid var(--gray-light);
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .movie-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            border-color: var(--primary);
        }
        
        .movie-poster {
            width: 100%;
            height: 300px;
            object-fit: cover;
            background: linear-gradient(135deg, var(--sky-blue), var(--sky-blue-light));
        }
        
        .movie-info {
            padding: 1rem;
            background: var(--white);
        }
        
        .movie-title {
            font-weight: 600;
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
            color: var(--black);
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .movie-id {
            font-size: 0.75rem;
            color: var(--gray-dark);
        }
        
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.875rem;
        }
        
        .btn-primary {
            background: var(--primary);
            color: var(--white);
            border: 2px solid var(--primary);
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px var(--sky-blue);
            background: var(--primary-dark);
        }
        
        .btn-secondary {
            background: var(--white);
            color: var(--black);
            border: 2px solid var(--gray-light);
        }
        
        .btn-secondary:hover {
            background: var(--light-gray);
            border-color: var(--gray-dark);
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--dark);
            font-size: 0.875rem;
        }
        
        input[type="text"],
        input[type="number"],
        input[type="email"] {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid var(--gray-light);
            border-radius: 8px;
            font-size: 0.875rem;
            transition: all 0.3s;
            background: var(--white);
            color: var(--black);
        }
        
        input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--sky-blue-light);
        }
        
        .alert {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        .alert-success {
            background: var(--sky-blue-light);
            color: var(--black);
            border-left: 4px solid var(--primary);
        }
        
        .alert-warning {
            background: rgba(255, 193, 7, 0.1);
            color: var(--gray-dark);
            border-left: 4px solid #ffc107;
        }
        
        .alert-info {
            background: var(--sky-blue-light);
            color: var(--black);
            border-left: 4px solid var(--primary);
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: var(--gray);
        }
        
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: var(--gray);
        }
        
        .empty-state svg {
            width: 64px;
            height: 64px;
            margin: 0 auto 1rem;
            opacity: 0.5;
        }
        
        .tab-content {
            display: none;
            animation: fadeIn 0.3s ease;
        }
        
        .tab-content.active {
            display: block;
        }
        
        @media (max-width: 1024px) {
            .hero-content {
                flex-direction: column;
                gap: 2rem;
            }
            
            .features-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
            }
            
            .main-content {
                margin-left: 0;
            }
            
            .hero-title {
                font-size: 2rem;
            }
            
            .hero-subtitle {
                font-size: 1rem;
            }
            
            .hero-stats {
                gap: 2rem;
            }
            
            .stat-value {
                font-size: 2rem;
            }
            
            .section-title {
                font-size: 2rem;
            }
            
            .features-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <!-- Header Navigation -->
    <div class="header-nav">
        <div class="header-nav-content">
            <div class="header-logo">MovieRec Pro</div>
            <div class="header-actions">
                <div class="header-nav-menu">
                    <a href="#" class="header-nav-link active" onclick="switchTab('explore'); return false;">Explore Movies</a>
                    <a href="#" class="header-nav-link" onclick="switchTab('recommend'); return false;">Recommendations</a>
                    <a href="#" class="header-nav-link" onclick="switchTab('users'); return false;">Manage Users</a>
                    <a href="#" class="header-nav-link" onclick="switchTab('ratings'); return false;">Add Rating</a>
                </div>
                <div class="status-indicator">
                    <span class="status-dot"></span>
                    <span>System Ready</span>
                </div>
            </div>
        </div>
    </div>
    
    
    <!-- Main Content -->
    <div class="main-content" id="main-content">
        <div class="main-content-wrapper">
            <!-- Hero Section -->
            <div class="hero">
                <div class="hero-content">
                    <h1 class="hero-title">Enterprise Movie Recommendation Platform</h1>
                    <p class="hero-subtitle">Leverage advanced machine learning algorithms to deliver personalized movie recommendations at scale. Built for enterprises seeking intelligent content discovery solutions.</p>
                    <div class="hero-stats">
                        <div class="stat-item">
                            <div class="stat-value">10K+</div>
                            <div class="stat-label">Movies</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">100K+</div>
                            <div class="stat-label">Ratings</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">99.9%</div>
                            <div class="stat-label">Uptime</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Features Section -->
            <div class="features-section">
                <div class="features-content">
                    <div class="section-header">
                        <h2 class="section-title">Powerful Features</h2>
                        <p class="section-subtitle">Everything you need to deliver exceptional movie recommendations to your users</p>
                    </div>
                    <div class="features-grid">
                        <div class="feature-card">
                            <div class="feature-icon">🔍</div>
                            <h3 class="feature-title">Advanced Search</h3>
                            <p class="feature-description">Real-time movie search with intelligent filtering by genre, title, and metadata. Fast, accurate, and scalable.</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">🎯</div>
                            <h3 class="feature-title">AI Recommendations</h3>
                            <p class="feature-description">Hybrid recommendation engine combining collaborative filtering and content-based approaches for optimal results.</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">📊</div>
                            <h3 class="feature-title">Analytics Dashboard</h3>
                            <p class="feature-description">Comprehensive insights into user behavior, rating patterns, and recommendation performance metrics.</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">⚡</div>
                            <h3 class="feature-title">Real-time Updates</h3>
                            <p class="feature-description">Model retrains automatically with new ratings, ensuring recommendations stay current and relevant.</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">🔒</div>
                            <h3 class="feature-title">Enterprise Security</h3>
                            <p class="feature-description">Built on Google Cloud Platform with enterprise-grade security, compliance, and data protection.</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">📈</div>
                            <h3 class="feature-title">Scalable Infrastructure</h3>
                            <p class="feature-description">Handles millions of users and ratings with BigQuery integration for unlimited scalability.</p>
                        </div>
                    </div>
                </div>
            </div>
            
            {% if status_message %}
            <div class="card" style="margin: 2rem;">
                <div class="alert {{ status_type }}">
                    {{ status_message|safe }}
                </div>
            </div>
            {% endif %}
            
            <!-- App Content Section -->
            <div class="card" style="margin: 2rem;">
                <!-- Explore Movies Tab -->
                <div id="explore-tab" class="tab-content active">
                    <div class="card-header">
                        <h2 class="card-title" id="page-title">Explore Movies</h2>
                    </div>
                
                <div class="search-container">
                    <svg class="search-icon" width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>
                    <input type="text" id="movie-search" class="search-input" placeholder="Search movies by title..." autocomplete="off">
                </div>
                
                <div class="filters">
                    <div class="filter-group">
                        <label>Filter by Genre</label>
                        <select id="genre-filter">
                            <option value="">All Genres</option>
                            {% for genre in genres %}
                            <option value="{{ genre }}">{{ genre }}</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>
                
                <div id="movies-container">
                    <div class="empty-state">
                        <p>Start typing to search movies...</p>
                    </div>
                </div>
            </div>
            
            <!-- Recommendations Tab -->
            <div id="recommend-tab" class="tab-content">
                <div class="card-header">
                    <h2 class="card-title">Get Recommendations</h2>
                </div>
                
                <form id="recommend-form" onsubmit="getRecommendations(event); return false;">
                    <div class="form-group">
                        <label>User ID:</label>
                        <input type="number" id="recommend-user-id" placeholder="Enter user ID" value="1" required>
                    </div>
                    <div class="form-group">
                        <label>Number of Recommendations:</label>
                        <input type="number" id="recommend-top-n" min="5" max="50" value="10" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Get Recommendations 🎯</button>
                </form>
                
                <div id="recommendations-results" style="margin-top: 2rem;"></div>
            </div>
            
            <!-- Users Tab -->
            <div id="users-tab" class="tab-content">
                <div class="card-header">
                    <h2 class="card-title">User Management</h2>
                </div>
                
                <!-- Create New User Section -->
                <div style="margin-bottom: 3rem;">
                    <h3 style="margin-bottom: 1rem; color: var(--black); font-size: 1.25rem;">Create New User</h3>
                    <p style="color: var(--gray-dark); margin-bottom: 1.5rem;">Click the button below to generate a new user ID.</p>
                    <button onclick="createUser()" class="btn btn-primary">Create New User ID 👤</button>
                    <div id="user-created-message" style="margin-top: 1rem;"></div>
                </div>
                
                <!-- Users List Section -->
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                        <h3 style="color: var(--black); font-size: 1.25rem;">All Users</h3>
                        <button onclick="loadUsersList()" class="btn btn-secondary">Refresh 🔄</button>
                    </div>
                    <div id="users-list-container">
                        <div class="loading">Loading users...</div>
                    </div>
                </div>
            </div>
            
            <!-- Add Rating Tab -->
            <div id="ratings-tab" class="tab-content">
                <div class="card-header">
                    <h2 class="card-title">Add Rating</h2>
                </div>
                
                <!-- User Selection -->
                <div style="margin-bottom: 2rem;">
                    <div class="form-group">
                        <label style="font-weight: 600; color: var(--black); margin-bottom: 0.5rem; display: block;">Select User:</label>
                        <select id="rating-user-id" style="width: 100%; padding: 0.75rem; border: 2px solid var(--gray-light); border-radius: 8px; font-size: 1rem;" onchange="loadMoviesForRating()">
                            <option value="">Loading users...</option>
                        </select>
                    </div>
                </div>
                
                <!-- Movie Search and Filter -->
                <div id="movie-selection-section" style="display: none;">
                    <div style="margin-bottom: 1.5rem;">
                        <div class="form-group" style="margin-bottom: 1rem;">
                            <label style="font-weight: 600; color: var(--black); margin-bottom: 0.5rem; display: block;">Search Movies:</label>
                            <input type="text" id="rating-movie-search" placeholder="Type to search movies..." 
                                   style="width: 100%; padding: 0.75rem; border: 2px solid var(--gray-light); border-radius: 8px; font-size: 1rem;"
                                   oninput="searchMoviesForRating()">
                        </div>
                        <div class="form-group">
                            <label style="font-weight: 600; color: var(--black); margin-bottom: 0.5rem; display: block;">Filter by Genre:</label>
                            <select id="rating-genre-filter" style="width: 100%; padding: 0.75rem; border: 2px solid var(--gray-light); border-radius: 8px; font-size: 1rem;" onchange="searchMoviesForRating()">
                                <option value="">All Genres</option>
                            </select>
                        </div>
                    </div>
                    
                    <!-- Movies Grid -->
                    <div id="rating-movies-container" style="margin-bottom: 2rem;">
                        <div class="loading">Loading movies...</div>
                    </div>
                </div>
                
                <!-- Rating Form (hidden until movie selected) -->
                <div id="rating-form-section" style="display: none;">
                    <div style="background: var(--light-gray); padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem;">
                        <h3 style="color: var(--black); margin-bottom: 1rem;">Rate Selected Movie</h3>
                        <div id="selected-movie-info" style="margin-bottom: 1rem;"></div>
                        <div class="form-group">
                            <label style="font-weight: 600; color: var(--black); margin-bottom: 0.5rem; display: block;">Your Rating:</label>
                            <div style="display: flex; align-items: center; gap: 1rem;">
                                <input type="range" id="rating-value" min="0.5" max="5.0" step="0.5" value="3.0" 
                                       style="flex: 1;"
                                       oninput="updateRatingDisplay(this.value)">
                                <span id="rating-display" style="font-weight: 600; color: var(--sky-blue); font-size: 1.25rem; min-width: 60px;">3.0</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-top: 0.5rem; font-size: 0.75rem; color: var(--gray-dark);">
                                <span>0.5</span>
                                <span>5.0</span>
                            </div>
                        </div>
                        <button onclick="submitRating()" class="btn btn-primary" style="width: 100%; margin-top: 1rem;">Submit Rating ⭐</button>
                    </div>
                </div>
                
                <div id="rating-message" style="margin-top: 1rem;"></div>
            </div>
        </div>
    </div>
    
    <script>
        const basePath = (() => {
            const pathname = window.location.pathname;
            const match = pathname.match(/\/proxy\/\d+/);
            return match ? match[0] : '';
        })();
        
        // Set form actions
        const recommendForm = document.getElementById('recommend-form');
        const createUserForm = document.getElementById('create-user-form');
        const ratingForm = document.getElementById('rating-form');
        
        if (recommendForm) recommendForm.action = basePath + '/recommend';
        if (createUserForm) createUserForm.action = basePath + '/create-user';
        if (ratingForm) ratingForm.action = basePath + '/add-rating';
        
        // Tab switching with animations
        function switchTab(tabName) {
            // Update nav links
            document.querySelectorAll('.header-nav-link').forEach(link => {
                link.classList.remove('active');
            });
            if (event && event.target) {
                event.target.classList.add('active');
            }
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            const activeTab = document.getElementById(tabName + '-tab');
            if (activeTab) {
                activeTab.classList.add('active');
            }
            
            // Load users list when users tab is opened
            if (tabName === 'users') {
                setTimeout(() => {
                    loadUsersList();
                }, 300);
            }
            
            // Load users dropdown and genres when ratings tab is opened
            if (tabName === 'ratings') {
                setTimeout(() => {
                    loadUsersForRating();
                    loadGenresForRating();
                }, 300);
            }
            
            // Scroll to content smoothly
            setTimeout(() => {
                const mainContent = document.querySelector('.main-content');
                if (mainContent) {
                    mainContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
        }
        
        // Get Recommendations via AJAX (always uses hybrid method)
        function getRecommendations(event) {
            event.preventDefault();
            const userId = document.getElementById('recommend-user-id').value;
            const topN = document.getElementById('recommend-top-n').value;
            const resultsDiv = document.getElementById('recommendations-results');
            
            resultsDiv.innerHTML = '<div class="loading">Getting recommendations...</div>';
            
            const params = new URLSearchParams({
                user_id: userId,
                method: 'hybrid',  // Always use hybrid method
                top_n: topN
            });
            
            fetch(`${basePath}/api/recommend?${params.toString()}`)
                .then(response => response.json())
                .then(data => {
                    if (data.needs_genre_selection) {
                        // Show genre selection UI
                        displayGenreSelection(data.genres, userId, topN, resultsDiv);
                    } else if (data.success && data.recommendations && data.recommendations.length > 0) {
                        displayRecommendations(data.recommendations, resultsDiv);
                    } else {
                        resultsDiv.innerHTML = `<div class="alert alert-warning">${data.error || 'No recommendations found. Try a different user ID or method.'}</div>`;
                    }
                })
                .catch(error => {
                    console.error('Recommendation error:', error);
                    resultsDiv.innerHTML = '<div class="alert alert-warning">Error getting recommendations. Please try again.</div>';
                });
        }
        
        function displayRecommendations(recommendations, container) {
            const html = '<div class="movies-grid">' + 
                recommendations.map(rec => `
                    <div class="movie-card fade-in">
                        <img src="https://via.placeholder.com/300x450/87ceeb/000000?text=${encodeURIComponent(rec.title.substring(0, 20))}" 
                             alt="${rec.title}" class="movie-poster" 
                             onerror="this.src='https://via.placeholder.com/300x450/87ceeb/000000?text=Movie'">
                        <div class="movie-info">
                            <div class="movie-title">${rec.title}</div>
                            <div class="movie-id">ID: ${rec.movieId}</div>
                            ${rec.pred_rating ? `<div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--primary-dark); font-weight: 600;">Rating: ${rec.pred_rating.toFixed(2)}/5.0</div>` : ''}
                            ${rec.score ? `<div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--sky-blue); font-weight: 600;">Match Score: ${rec.score.toFixed(2)}</div>` : ''}
                            ${rec.genres && rec.genres.length > 0 ? `<div style="margin-top: 0.5rem; font-size: 0.7rem; color: var(--gray-dark);">${rec.genres.join(', ')}</div>` : ''}
                        </div>
                    </div>
                `).join('') + '</div>';
            container.innerHTML = html;
            
            // Observe new elements for animation
            container.querySelectorAll('.fade-in').forEach(el => {
                observer.observe(el);
            });
        }
        
        // Display genre selection cards
        let selectedGenres = [];
        function displayGenreSelection(genres, userId, topN, container) {
            selectedGenres = []; // Reset selected genres
            const html = `
                <div style="margin-bottom: 2rem;">
                    <h3 style="color: var(--black); margin-bottom: 1rem; font-size: 1.25rem;">Select Your Preferred Genres</h3>
                    <p style="color: var(--gray-dark); margin-bottom: 1.5rem;">This user has no ratings yet. Please select genres you like to get personalized recommendations.</p>
                    <div id="genre-selection-container" style="display: flex; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1.5rem;">
                        ${genres.map(genre => `
                            <button class="genre-card" 
                                    data-genre="${genre}" 
                                    onclick="toggleGenre(this)"
                                    style="padding: 0.75rem 1.5rem; border: 2px solid var(--gray-light); background: var(--white); color: var(--black); border-radius: 8px; cursor: pointer; transition: all 0.3s; font-weight: 500; font-size: 0.95rem;">
                                ${genre}
                            </button>
                        `).join('')}
                    </div>
                    <button onclick="getRecommendationsByGenres(${userId}, ${topN})" 
                            id="get-genre-recommendations-btn"
                            class="btn btn-primary"
                            disabled
                            style="opacity: 0.5; cursor: not-allowed;">
                        Get Recommendations Based on Selected Genres 🎯
                    </button>
                    <div id="genre-recommendations-results" style="margin-top: 2rem;"></div>
                </div>
            `;
            container.innerHTML = html;
        }
        
        // Toggle genre selection
        function toggleGenre(button) {
            const genre = button.getAttribute('data-genre');
            const index = selectedGenres.indexOf(genre);
            
            if (index > -1) {
                // Deselect
                selectedGenres.splice(index, 1);
                button.style.background = 'var(--white)';
                button.style.borderColor = 'var(--gray-light)';
                button.style.color = 'var(--black)';
            } else {
                // Select
                selectedGenres.push(genre);
                button.style.background = 'var(--sky-blue)';
                button.style.borderColor = 'var(--sky-blue)';
                button.style.color = 'var(--white)';
            }
            
            // Enable/disable recommendation button
            const btn = document.getElementById('get-genre-recommendations-btn');
            if (btn) {
                if (selectedGenres.length > 0) {
                    btn.disabled = false;
                    btn.style.opacity = '1';
                    btn.style.cursor = 'pointer';
                } else {
                    btn.disabled = true;
                    btn.style.opacity = '0.5';
                    btn.style.cursor = 'not-allowed';
                }
            }
        }
        
        // Get recommendations based on selected genres
        function getRecommendationsByGenres(userId, topN) {
            if (selectedGenres.length === 0) {
                alert('Please select at least one genre');
                return;
            }
            
            const resultsDiv = document.getElementById('genre-recommendations-results');
            if (!resultsDiv) return;
            
            resultsDiv.innerHTML = '<div class="loading">Getting recommendations based on your genre preferences...</div>';
            
            const params = new URLSearchParams({
                user_id: userId,
                top_n: topN,
                genres: selectedGenres.join(',')
            });
            
            fetch(`${basePath}/api/recommend-by-genres?${params.toString()}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.recommendations && data.recommendations.length > 0) {
                        displayRecommendations(data.recommendations, resultsDiv);
                    } else {
                        resultsDiv.innerHTML = `<div class="empty-state"><p>${data.error || 'No recommendations found for selected genres.'}</p></div>`;
                    }
                })
                .catch(error => {
                    console.error('Error getting genre-based recommendations:', error);
                    resultsDiv.innerHTML = '<div class="empty-state"><p>Error getting recommendations. Please try again.</p></div>';
                });
        }
        
        // Create User via AJAX
        function createUser() {
            const messageDiv = document.getElementById('user-created-message');
            
            messageDiv.innerHTML = '<div class="loading">Creating new user ID...</div>';
            
            fetch(`${basePath}/api/create-user`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        messageDiv.innerHTML = `<div class="alert alert-success">✅ New user created successfully!<br><strong>User ID: ${data.user_id}</strong></div>`;
                        // Reload users list
                        loadUsersList();
                    } else {
                        messageDiv.innerHTML = `<div class="alert alert-warning">⚠️ Error: ${data.error || 'Failed to create user'}</div>`;
                    }
                })
                .catch(error => {
                    console.error('Create user error:', error);
                    messageDiv.innerHTML = '<div class="alert alert-warning">Error creating user. Please try again.</div>';
                });
        }
        
        // Load Users List via AJAX
        function loadUsersList() {
            const container = document.getElementById('users-list-container');
            container.innerHTML = '<div class="loading">Loading users...</div>';
            
            fetch(`${basePath}/api/users`)
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.users && data.users.length > 0) {
                        displayUsersList(data.users, container);
                    } else {
                        container.innerHTML = '<div class="empty-state"><p>No users found. Create your first user above.</p></div>';
                    }
                })
                .catch(error => {
                    console.error('Load users error:', error);
                    container.innerHTML = '<div class="alert alert-warning">Error loading users. Please try again.</div>';
                });
        }
        
        function displayUsersList(users, container) {
            const html = `
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; background: var(--white); border-radius: 8px; overflow: hidden;">
                        <thead>
                            <tr style="background: var(--sky-blue-light);">
                                <th style="padding: 1rem; text-align: left; font-weight: 600; color: var(--black); border-bottom: 2px solid var(--gray-light);">User ID</th>
                                <th style="padding: 1rem; text-align: left; font-weight: 600; color: var(--black); border-bottom: 2px solid var(--gray-light);">Name</th>
                                <th style="padding: 1rem; text-align: left; font-weight: 600; color: var(--black); border-bottom: 2px solid var(--gray-light);">Email</th>
                                <th style="padding: 1rem; text-align: left; font-weight: 600; color: var(--black); border-bottom: 2px solid var(--gray-light);">Created At</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${users.map(user => `
                                <tr style="border-bottom: 1px solid var(--gray-light); transition: all 0.2s;">
                                    <td style="padding: 1rem; color: var(--black);">${user.userId}</td>
                                    <td style="padding: 1rem; color: var(--black); font-weight: 500;">${user.userName}</td>
                                    <td style="padding: 1rem; color: var(--gray-dark);">${user.userEmail || '-'}</td>
                                    <td style="padding: 1rem; color: var(--gray-dark); font-size: 0.875rem;">${user.createdAt ? new Date(user.createdAt).toLocaleDateString() : '-'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                    <div style="margin-top: 1rem; color: var(--gray-dark); font-size: 0.875rem;">Total: ${users.length} users</div>
                </div>
            `;
            container.innerHTML = html;
        }
        
        
        // Load users dropdown in ratings tab
        function loadUsersForRating() {
            const select = document.getElementById('rating-user-id');
            if (!select) return;
            
            fetch(`${basePath}/api/users`)
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.users && data.users.length > 0) {
                        select.innerHTML = '<option value="">Select a user...</option>' +
                            data.users.map(user => `<option value="${user.userId}">User ${user.userId}${user.userName && user.userName !== `User ${user.userId}` ? ' - ' + user.userName : ''}</option>`).join('');
                    } else {
                        select.innerHTML = '<option value="">No users found</option>';
                    }
                })
                .catch(error => {
                    console.error('Load users error:', error);
                    select.innerHTML = '<option value="">Error loading users</option>';
                });
        }
        
        // Load genres for rating filter
        function loadGenresForRating() {
            const select = document.getElementById('rating-genre-filter');
            if (!select) return;
            
            // Get genres from search API or use the genres from the main page
            fetch(`${basePath}/api/search?q=`)
                .then(response => response.json())
                .then(data => {
                    // Extract unique genres from movies
                    const genresSet = new Set();
                    if (data.movies) {
                        data.movies.forEach(movie => {
                            if (movie.genres) {
                                movie.genres.forEach(genre => genresSet.add(genre));
                            }
                        });
                    }
                    
                    const genres = Array.from(genresSet).sort();
                    select.innerHTML = '<option value="">All Genres</option>' +
                        genres.map(genre => `<option value="${genre}">${genre}</option>`).join('');
                })
                .catch(error => {
                    console.error('Load genres error:', error);
                    select.innerHTML = '<option value="">All Genres</option>';
                });
        }
        
        // Load movies for rating
        function loadMoviesForRating() {
            const userId = document.getElementById('rating-user-id').value;
            const movieSection = document.getElementById('movie-selection-section');
            const ratingFormSection = document.getElementById('rating-form-section');
            
            if (!userId) {
                movieSection.style.display = 'none';
                ratingFormSection.style.display = 'none';
                return;
            }
            
            movieSection.style.display = 'block';
            ratingFormSection.style.display = 'none';
            // Don't auto-load movies, wait for user to search
            const container = document.getElementById('rating-movies-container');
            if (container) {
                container.innerHTML = '<div class="empty-state"><p>Start typing to search movies or select a genre filter.</p></div>';
            }
        }
        
        // Search movies for rating
        let ratingSearchTimeout;
        function searchMoviesForRating() {
            clearTimeout(ratingSearchTimeout);
            ratingSearchTimeout = setTimeout(() => {
                const query = document.getElementById('rating-movie-search').value.trim();
                const genre = document.getElementById('rating-genre-filter').value;
                const container = document.getElementById('rating-movies-container');
                
                // Only search if there's a query or genre filter
                if (!query && !genre) {
                    container.innerHTML = '<div class="empty-state"><p>Start typing to search movies or select a genre filter.</p></div>';
                    return;
                }
                
                container.innerHTML = '<div class="loading">Loading movies...</div>';
                
                const params = new URLSearchParams({
                    q: query,
                    genre: genre
                });
                
                fetch(`${basePath}/api/search?${params.toString()}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.movies && data.movies.length > 0) {
                            displayMoviesForRating(data.movies, container);
                        } else {
                            container.innerHTML = '<div class="empty-state"><p>No movies found. Try a different search.</p></div>';
                        }
                    })
                    .catch(error => {
                        console.error('Search movies error:', error);
                        container.innerHTML = '<div class="empty-state"><p>Error loading movies. Please try again.</p></div>';
                    });
            }, 300);
        }
        
        // Display movies for rating selection
        let selectedMovieForRating = null;
        function displayMoviesForRating(movies, container) {
            const html = '<div class="movies-grid">' + 
                movies.map((movie, index) => `
                    <div class="movie-card fade-in" data-movie-id="${movie.movieId}" data-movie-title="${movie.title.replace(/"/g, '&quot;')}" data-movie-genres="${(movie.genres || []).join(',')}" 
                         style="cursor: pointer; transition: all 0.3s;" 
                         onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 8px 16px rgba(0,0,0,0.2)'" 
                         onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.1)'">
                        <img src="https://via.placeholder.com/300x450/87ceeb/000000?text=${encodeURIComponent(movie.title.substring(0, 20))}" 
                             alt="${movie.title.replace(/"/g, '&quot;')}" class="movie-poster" 
                             onerror="this.src='https://via.placeholder.com/300x450/87ceeb/000000?text=Movie'">
                        <div class="movie-info">
                            <div class="movie-title">${movie.title}</div>
                            <div class="movie-id">ID: ${movie.movieId}</div>
                            ${movie.genres && movie.genres.length > 0 ? `<div style="margin-top: 0.5rem; font-size: 0.7rem; color: var(--gray-dark);">${movie.genres.join(', ')}</div>` : ''}
                        </div>
                    </div>
                `).join('') + '</div>';
            container.innerHTML = html;
            
            // Add click event listeners to movie cards
            container.querySelectorAll('.movie-card').forEach(card => {
                card.addEventListener('click', function() {
                    const movieId = parseInt(this.getAttribute('data-movie-id'));
                    const title = this.getAttribute('data-movie-title');
                    const genresStr = this.getAttribute('data-movie-genres');
                    const genres = genresStr ? genresStr.split(',').filter(g => g.trim()) : [];
                    selectMovieForRating(movieId, title, genres);
                });
            });
            
            // Observe new elements for animation
            container.querySelectorAll('.fade-in').forEach(el => {
                observer.observe(el);
            });
        }
        
        // Select movie for rating
        function selectMovieForRating(movieId, title, genres) {
            console.log('Selecting movie:', movieId, title, genres);
            selectedMovieForRating = { movieId, title, genres: genres || [] };
            
            const ratingFormSection = document.getElementById('rating-form-section');
            const selectedMovieInfo = document.getElementById('selected-movie-info');
            
            if (!ratingFormSection || !selectedMovieInfo) {
                console.error('Rating form elements not found');
                alert('Error: Rating form not found. Please refresh the page.');
                return;
            }
            
            const genresDisplay = genres && genres.length > 0 ? genres.join(', ') : 'No genres';
            
            selectedMovieInfo.innerHTML = `
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <img src="https://via.placeholder.com/100x150/87ceeb/000000?text=${encodeURIComponent(title.substring(0, 15))}" 
                         style="border-radius: 8px; border: 2px solid var(--gray-light);"
                         onerror="this.src='https://via.placeholder.com/100x150/87ceeb/000000?text=Movie'">
                    <div>
                        <div style="font-weight: 600; color: var(--black); font-size: 1.1rem; margin-bottom: 0.25rem;">${title}</div>
                        <div style="color: var(--gray-dark); font-size: 0.875rem;">Movie ID: ${movieId}</div>
                        <div style="color: var(--gray-dark); font-size: 0.75rem; margin-top: 0.25rem;">${genresDisplay}</div>
                    </div>
                </div>
            `;
            
            ratingFormSection.style.display = 'block';
            
            // Scroll to rating form
            setTimeout(() => {
                ratingFormSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 100);
        }
        
        // Update rating display
        function updateRatingDisplay(value) {
            document.getElementById('rating-display').textContent = parseFloat(value).toFixed(1);
        }
        
        // Submit rating - prevent multiple submissions
        let isSubmittingRating = false;
        function submitRating() {
            // Prevent multiple simultaneous submissions
            if (isSubmittingRating) {
                console.log('Rating submission already in progress, ignoring duplicate click');
                return;
            }
            
            if (!selectedMovieForRating) {
                alert('Please select a movie first');
                return;
            }
            
            const userId = document.getElementById('rating-user-id').value;
            const rating = document.getElementById('rating-value').value;
            const messageDiv = document.getElementById('rating-message');
            const submitButton = document.querySelector('#rating-form-section button[onclick*="submitRating"]');
            
            if (!userId) {
                alert('Please select a user first');
                return;
            }
            
            // Set submitting flag and disable button
            isSubmittingRating = true;
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.style.opacity = '0.6';
                submitButton.style.cursor = 'not-allowed';
                submitButton.textContent = 'Submitting... ⏳';
            }
            
            messageDiv.innerHTML = '<div class="loading">Adding rating...</div>';
            
            const params = new URLSearchParams({
                user_id: userId,
                movie_id: selectedMovieForRating.movieId,
                rating: rating
            });
            
            fetch(`${basePath}/api/add-rating?${params.toString()}`)
                .then(response => response.json())
                .then(data => {
                    // Reset submitting flag and button
                    isSubmittingRating = false;
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.style.opacity = '1';
                        submitButton.style.cursor = 'pointer';
                        submitButton.textContent = 'Submit Rating ⭐';
                    }
                    
                    if (data.success) {
                        let message = `✅ Rating added successfully! User ${userId} rated "${selectedMovieForRating.title}" with ${rating} stars`;
                        if (data.rmse !== null && data.rmse !== undefined) {
                            message += `<br>🔄 Model retrained! RMSE: ${data.rmse.toFixed(4)}`;
                        }
                        messageDiv.innerHTML = `<div class="alert alert-success">${message}</div>`;
                        
                        // Reset form
                        selectedMovieForRating = null;
                        document.getElementById('rating-form-section').style.display = 'none';
                        document.getElementById('rating-value').value = '3.0';
                        document.getElementById('rating-display').textContent = '3.0';
                    } else {
                        messageDiv.innerHTML = `<div class="alert alert-warning">⚠️ Error: ${data.error || 'Failed to add rating'}</div>`;
                    }
                })
                .catch(error => {
                    // Reset submitting flag and button on error
                    isSubmittingRating = false;
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.style.opacity = '1';
                        submitButton.style.cursor = 'pointer';
                        submitButton.textContent = 'Submit Rating ⭐';
                    }
                    console.error('Add rating error:', error);
                    messageDiv.innerHTML = '<div class="alert alert-warning">Error adding rating. Please try again.</div>';
                });
        }
        
        // Scroll animation observer
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, observerOptions);
        
        // Observe all animated elements after page load
        setTimeout(() => {
            document.querySelectorAll('.fade-in, .slide-in-left, .slide-in-right, .scale-in').forEach(el => {
                observer.observe(el);
            });
        }, 100);
        
        // Real-time movie search
        let searchTimeout;
        const searchInput = document.getElementById('movie-search');
        const genreFilter = document.getElementById('genre-filter');
        const moviesContainer = document.getElementById('movies-container');
        
        function performSearch() {
            const query = searchInput.value.trim();
            const genre = genreFilter.value;
            
            if (query.length < 2 && !genre) {
                moviesContainer.innerHTML = '<div class="empty-state"><p>Start typing to search movies...</p></div>';
                return;
            }
            
            moviesContainer.innerHTML = '<div class="loading">Searching movies...</div>';
            
            const params = new URLSearchParams();
            if (query) params.append('q', query);
            if (genre) params.append('genre', genre);
            
            fetch(`${basePath}/api/search?${params.toString()}`)
                .then(response => response.json())
                .then(data => {
                    if (data.movies && data.movies.length > 0) {
                        displayMovies(data.movies);
                    } else {
                        moviesContainer.innerHTML = '<div class="empty-state"><p>No movies found. Try a different search.</p></div>';
                    }
                })
                .catch(error => {
                    console.error('Search error:', error);
                    moviesContainer.innerHTML = '<div class="empty-state"><p>Error searching movies. Please try again.</p></div>';
                });
        }
        
        function displayMovies(movies) {
            const html = '<div class="movies-grid">' + 
                movies.map(movie => `
                    <div class="movie-card" onclick="selectMovie(${movie.movieId}, '${movie.title.replace(/'/g, "\\'")}')">
                        <img src="https://via.placeholder.com/300x450/0ea5e9/ffffff?text=${encodeURIComponent(movie.title.substring(0, 20))}" 
                             alt="${movie.title}" class="movie-poster" 
                             onerror="this.src='https://via.placeholder.com/300x450/0ea5e9/ffffff?text=Movie'">
                        <div class="movie-info">
                            <div class="movie-title">${movie.title}</div>
                            <div class="movie-id">ID: ${movie.movieId}</div>
                            ${movie.genres ? '<div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--gray);">' + movie.genres.join(', ') + '</div>' : ''}
                        </div>
                    </div>
                `).join('') + '</div>';
            moviesContainer.innerHTML = html;
        }
        
        function selectMovie(movieId, title) {
            // Fill rating form with selected movie
            document.getElementById('ratings-tab').querySelector('input[name="movie_id"]').value = movieId;
            switchTab('ratings');
            document.querySelectorAll('.tab').forEach((t, i) => {
                if (t.textContent.includes('Add Rating')) t.classList.add('active');
                else t.classList.remove('active');
            });
        }
        
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(performSearch, 300);
        });
        
        genreFilter.addEventListener('change', performSearch);
    </script>
</body>
</html>
"""

def get_base_path():
    """Get the base path preserving proxy path from request URL"""
    full_url = request.url
    if '/proxy/' in full_url:
        parts = full_url.split('/proxy/')
        if len(parts) > 1:
            port_part = parts[1].split('/')[0]
            return '/proxy/' + port_part
    return ''

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path=''):
    """Main page"""
    base_path = get_base_path()
    
    if path == 'recommend':
        return recommend()
    elif path == 'add-rating':
        return add_rating()
    elif path == 'create-user':
        return create_user()
    
    status_message = None
    status_type = 'info'
    genres = get_genres_from_movies()
    user_created = False
    new_user_id = None
    
    if not recommender_module:
        status_message = '<strong>⚠️ Demo Mode:</strong> Recommender module not available.'
        status_type = 'warning'
    else:
        try:
            if recommender_module.df_movies is None or recommender_module.df_ratings is None:
                recommender_module.load_data(timeout_seconds=10)
            
            movies_count = len(recommender_module.df_movies) if recommender_module.df_movies is not None else 0
            ratings_count = len(recommender_module.df_ratings) if recommender_module.df_ratings is not None else 0
            mock_data = movies_count < 500 if movies_count > 0 else True
            
            status_message = f'<strong>✅ System Ready!</strong> {movies_count} movies, {ratings_count} ratings available.'
            if mock_data:
                status_message += '<br>⚠️ Using mock data (BigQuery not available)'
            else:
                status_message += '<br>✅ Using real data from BigQuery'
            status_type = 'success'
        except Exception as e:
            status_message = f'<strong>⚠️ Error:</strong> {str(e)}'
            status_type = 'warning'
    
    return render_template_string(HTML_TEMPLATE,
                                 status_message=status_message,
                                 status_type=status_type,
                                 genres=genres,
                                 user_created=user_created,
                                 new_user_id=new_user_id,
                                 get_movie_image_url=get_movie_image_url)

@app.route('/api/search')
def api_search():
    """API endpoint for real-time movie search"""
    if not recommender_module or recommender_module.df_movies is None:
        return jsonify({'movies': []})
    
    query = request.args.get('q', '').strip().lower()
    genre = request.args.get('genre', '').strip()
    
    df = recommender_module.df_movies.copy()
    
    # Filter by title
    if query:
        df = df[df['title'].str.lower().str.contains(query, na=False)]
    
    # Filter by genre
    if genre:
        genre_col = genre.replace(' ', '_').lower()
        if genre_col in df.columns:
            df = df[df[genre_col] == 1]
    
    # Get top 50 results
    results = df.head(50)
    
    # Extract genres for each movie
    movies = []
    genre_columns = [col for col in df.columns if col not in ['movieId', 'title']]
    
    for _, row in results.iterrows():
        movie_genres = []
        for col in genre_columns:
            if col in row and row[col] == 1:
                clean_genre = col.replace('_', ' ').title()
                if clean_genre and 'no genres listed' not in clean_genre.lower():
                    movie_genres.append(clean_genre)
        
        movies.append({
            'movieId': int(row['movieId']),
            'title': row['title'],
            'genres': movie_genres
        })
    
    return jsonify({'movies': movies})

@app.route('/api/recommend')
def api_recommend():
    """API endpoint for getting recommendations"""
    if not recommender_module:
        return jsonify({'success': False, 'error': 'Recommender module not available'})
    
    try:
        user_id = int(request.args.get('user_id', 1))
        method = request.args.get('method', 'hybrid')
        top_n = int(request.args.get('top_n', 10))
        
        if recommender_module.df_movies is None or recommender_module.df_ratings is None:
            recommender_module.load_data(timeout_seconds=10)
        
        # Check if user has any ratings (excluding NULL/NaN movieId entries)
        import pandas as pd
        user_ratings = recommender_module.df_ratings[
            (recommender_module.df_ratings['userId'] == user_id) & 
            (recommender_module.df_ratings['movieId'].notna())
        ]
        
        if len(user_ratings) == 0:
            # User has no ratings - return genre selection prompt
            genres = get_genres_from_movies()
            return jsonify({
                'success': False,
                'needs_genre_selection': True,
                'message': 'This user has no ratings yet. Please select your preferred genres to get recommendations.',
                'genres': genres
            })
        
        # User has ratings - proceed with normal recommendation
        if method == 'hybrid':
            recommendations_df = recommender_module.recommend_hybrid(user_id, top_n=top_n)
        elif method == 'content':
            recommendations_df = recommender_module.recommend_content_based(user_id, top_n=top_n)
        elif method == 'collaborative':
            if not getattr(recommender_module, 'SURPRISE_AVAILABLE', False):
                return jsonify({'success': False, 'error': 'Collaborative filtering requires surprise library'})
            recommendations_df = recommender_module.recommend_collaborative(user_id, top_n=top_n)
        else:
            return jsonify({'success': False, 'error': 'Invalid method'})
        
        recommendations = []
        for _, row in recommendations_df.iterrows():
            rec = {'movieId': int(row['movieId']), 'title': row['title']}
            if 'pred_rating' in row:
                rec['pred_rating'] = float(row['pred_rating'])
            if 'score' in row:
                rec['score'] = float(row['score'])
            recommendations.append(rec)
        
        return jsonify({'success': True, 'recommendations': recommendations})
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})

@app.route('/api/recommend-by-genres')
def api_recommend_by_genres():
    """API endpoint for getting recommendations based on selected genres"""
    if not recommender_module:
        return jsonify({'success': False, 'error': 'Recommender module not available'})
    
    try:
        user_id = int(request.args.get('user_id', 1))
        top_n = int(request.args.get('top_n', 10))
        genres_param = request.args.get('genres', '')
        
        if not genres_param:
            return jsonify({'success': False, 'error': 'No genres selected'})
        
        # Parse genres (comma-separated)
        selected_genres = [g.strip() for g in genres_param.split(',') if g.strip()]
        
        if recommender_module.df_movies is None or recommender_module.df_ratings is None:
            recommender_module.load_data(timeout_seconds=10)
        
        df = recommender_module.df_movies.copy()
        
        # Filter movies by selected genres
        # Convert genre names to column names (e.g., "Sci-Fi" -> "Sci_Fi")
        genre_columns = []
        for genre in selected_genres:
            genre_col = genre.replace(' ', '_').replace('-', '_').lower()
            # Try exact match first
            if genre_col in df.columns:
                genre_columns.append(genre_col)
            else:
                # Try case-insensitive match
                matching_cols = [col for col in df.columns if col.lower() == genre_col]
                if matching_cols:
                    genre_columns.extend(matching_cols)
        
        if not genre_columns:
            return jsonify({'success': False, 'error': 'No valid genres found'})
        
        # Filter movies that match at least one selected genre
        genre_mask = df[genre_columns].sum(axis=1) > 0
        filtered_movies = df[genre_mask].copy()
        
        # Exclude movies already rated by user (if any)
        if len(recommender_module.df_ratings) > 0:
            user_ratings = recommender_module.df_ratings[recommender_module.df_ratings['userId'] == user_id]
            if len(user_ratings) > 0:
                seen_movies = user_ratings['movieId'].tolist()
                filtered_movies = filtered_movies[~filtered_movies['movieId'].isin(seen_movies)]
        
        # Calculate score based on number of matching genres
        filtered_movies['score'] = filtered_movies[genre_columns].sum(axis=1)
        
        # Sort by score and get top N
        recommendations_df = filtered_movies.sort_values('score', ascending=False).head(top_n)
        
        recommendations = []
        for _, row in recommendations_df.iterrows():
            # Extract genres for display
            movie_genres = []
            all_genre_cols = [col for col in df.columns if col not in ['movieId', 'title', 'score']]
            for col in all_genre_cols:
                if col in row and row[col] == 1:
                    clean_genre = col.replace('_', ' ').replace('no genres listed', '').strip()
                    if clean_genre:
                        movie_genres.append(clean_genre.title())
            
            recommendations.append({
                'movieId': int(row['movieId']),
                'title': row['title'],
                'score': float(row['score']),
                'genres': movie_genres
            })
        
        return jsonify({'success': True, 'recommendations': recommendations})
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})

@app.route('/api/create-user')
def api_create_user():
    """API endpoint for creating users - generates a new user ID"""
    if not recommender_module:
        return jsonify({'success': False, 'error': 'Recommender module not available'})
    
    try:
        # Get next user ID from existing ratings
        if recommender_module.df_ratings is not None and len(recommender_module.df_ratings) > 0:
            new_user_id = int(recommender_module.df_ratings['userId'].max()) + 1
        else:
            # Check BigQuery for max user ID if available
            try:
                from google.cloud import bigquery
                client = bigquery.Client(project="students-group3")
                query_max = """
                SELECT MAX(userId) as max_id
                FROM `students-group3.MovieData.ratings_cleaned`
                """
                result = client.query(query_max).result()
                for row in result:
                    if row.max_id:
                        new_user_id = int(row.max_id) + 1
                    else:
                        new_user_id = 1
                    break
                else:
                    new_user_id = 1
            except:
                new_user_id = 1
        
        # Insert placeholder rating entry in BigQuery ratings_cleaned table
        # This ensures the user appears in queries immediately
        bigquery_saved = False
        try:
            from google.cloud import bigquery
            client = bigquery.Client(project="students-group3")
            
            # Insert userId with NULL movieId and NULL rating into ratings_cleaned
            # This ensures the user appears in queries immediately
            query_insert = f"""
            INSERT INTO `students-group3.MovieData.ratings_cleaned` (userId, movieId, rating)
            VALUES ({new_user_id}, NULL, NULL)
            """
            client.query(query_insert).result()
            print(f"✅ New user ID {new_user_id} added to BigQuery ratings_cleaned table (userId with NULL movieId and NULL rating)")
            bigquery_saved = True
            
            # Also update local df_ratings if available (use NaN for NULL)
            if recommender_module.df_ratings is not None:
                import numpy as np
                placeholder_rating = pd.DataFrame({
                    'userId': [new_user_id],
                    'movieId': [np.nan],
                    'rating': [np.nan]
                })
                recommender_module.df_ratings = pd.concat([recommender_module.df_ratings, placeholder_rating], ignore_index=True)
                print(f"✅ User added to local data")
        except Exception as e:
            print(f"⚠️ Could not insert into BigQuery: {e}")
            import traceback
            print(traceback.format_exc())
            # Still add to local data if available
            if recommender_module.df_ratings is not None:
                import numpy as np
                placeholder_rating = pd.DataFrame({
                    'userId': [new_user_id],
                    'movieId': [np.nan],
                    'rating': [np.nan]
                })
                recommender_module.df_ratings = pd.concat([recommender_module.df_ratings, placeholder_rating], ignore_index=True)
                print(f"✅ User added to local data only")
            print(f"✅ New user ID generated locally: {new_user_id}")
        
        if not bigquery_saved:
            return jsonify({
                'success': False,
                'error': f'Failed to add user ID {new_user_id} to BigQuery ratings_cleaned table. Please check your BigQuery connection.',
                'user_id': new_user_id
            })
        
        return jsonify({'success': True, 'user_id': new_user_id, 'message': 'User ID created successfully'})
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})

@app.route('/api/add-rating')
def api_add_rating():
    """API endpoint for adding ratings - saves to BigQuery"""
    if not recommender_module:
        return jsonify({'success': False, 'error': 'Recommender module not available'})
    
    try:
        user_id = int(request.args.get('user_id'))
        movie_id = int(request.args.get('movie_id'))
        rating = float(request.args.get('rating'))
        
        if recommender_module.df_movies is None or recommender_module.df_ratings is None:
            recommender_module.load_data(timeout_seconds=10)
        
        # Save rating to BigQuery - handle NULL placeholder or add new rating
        bigquery_saved = False
        bigquery_error = None
        has_null_entry = False
        try:
            from google.cloud import bigquery
            client = bigquery.Client(project="students-group3")
            
            # First, check if user has a NULL placeholder entry
            check_null_query = f"""
            SELECT COUNT(*) as count
            FROM `students-group3.MovieData.ratings_cleaned`
            WHERE userId = {user_id} AND movieId IS NULL
            """
            result = client.query(check_null_query).result()
            for row in result:
                has_null_entry = row.count > 0
                break
            
            if has_null_entry:
                # User has NULL placeholder - UPDATE it to real rating
                # Delete NULL entry and insert new rating
                query_delete_null = f"""
                DELETE FROM `students-group3.MovieData.ratings_cleaned`
                WHERE userId = {user_id} AND movieId IS NULL
                """
                client.query(query_delete_null).result()
                
                # Insert the new rating
                query_insert = f"""
                INSERT INTO `students-group3.MovieData.ratings_cleaned` (userId, movieId, rating)
                VALUES ({user_id}, {movie_id}, {rating})
                """
                client.query(query_insert).result()
                print(f"✅ Updated NULL placeholder to real rating in BigQuery: User {user_id}, Movie {movie_id}, Rating {rating}")
            else:
                # No NULL entry - use MERGE to handle insert/update of existing rating
                query_merge = f"""
                MERGE `students-group3.MovieData.ratings_cleaned` AS target
                USING (
                    SELECT {user_id} AS userId, {movie_id} AS movieId, {rating} AS rating
                ) AS source
                ON target.userId = source.userId AND target.movieId = source.movieId
                WHEN MATCHED THEN
                    UPDATE SET rating = source.rating
                WHEN NOT MATCHED THEN
                    INSERT (userId, movieId, rating) VALUES (source.userId, source.movieId, source.rating)
                """
                client.query(query_merge).result()
                print(f"✅ Added/updated rating in BigQuery: User {user_id}, Movie {movie_id}, Rating {rating}")
            
            bigquery_saved = True
        except Exception as e:
            bigquery_error = str(e)
            print(f"⚠️ Error saving to BigQuery: {e}")
            import traceback
            error_traceback = traceback.format_exc()
            print(error_traceback)
        
        if not bigquery_saved:
            # Still allow the rating to be saved locally even if BigQuery fails
            print(f"⚠️ BigQuery save failed, but continuing with local save...")
            # Don't return error immediately, allow local save to proceed
        
        # Reload from BigQuery and retrain model after saving rating
        rmse = None
        if bigquery_saved:
            try:
                # Reload ratings from BigQuery to sync with latest data
                # This ensures we have the most up-to-date ratings including the one we just saved
                print("🔄 Reloading ratings from BigQuery before retraining...")
                recommender_module.reload_ratings_from_bigquery()
                
                # Retrain the model with updated data
                print("🔄 Retraining model with updated ratings...")
                rmse = recommender_module.retrain_model()
                if rmse is not None:
                    print(f"✅ Model retrained successfully! RMSE: {rmse:.4f}")
                else:
                    print("ℹ️ Model retraining skipped (surprise not available or insufficient data)")
            except Exception as e:
                print(f"⚠️ Error during model retraining (non-critical): {e}")
                import traceback
                print(traceback.format_exc())
                # Continue - BigQuery save was successful
        else:
            # If BigQuery save failed, still try to update local data
            try:
                # Update local data efficiently - combine operations
                if recommender_module.df_ratings is not None:
                    import pandas as pd
                    # Remove both placeholder (NULL/NaN movieId) and existing rating in one operation
                    mask_to_remove = (
                        ((recommender_module.df_ratings['userId'] == user_id) & (recommender_module.df_ratings['movieId'].isna())) |
                        ((recommender_module.df_ratings['userId'] == user_id) & (recommender_module.df_ratings['movieId'] == movie_id))
                    )
                    if mask_to_remove.any():
                        recommender_module.df_ratings = recommender_module.df_ratings[~mask_to_remove]
                
                # Add the rating locally
                rmse = recommender_module.add_new_user_ratings(
                    user_id,
                    [{'movieId': movie_id, 'rating': rating}],
                    auto_retrain=True,
                    reload_from_bigquery=False
                )
            except Exception as e:
                print(f"⚠️ Error in local model update (non-critical): {e}")
                import traceback
                print(traceback.format_exc())
                # Continue - BigQuery save was successful
        
        if bigquery_saved:
            message = f'Rating saved successfully to BigQuery! User {user_id} rated Movie {movie_id} with {rating} stars'
        else:
            error_msg = bigquery_error if bigquery_error else "Unknown error"
            message = f'Rating saved locally (BigQuery save failed: {error_msg})! User {user_id} rated Movie {movie_id} with {rating} stars'
        
        return jsonify({
            'success': True,
            'message': message,
            'rmse': rmse,
            'bigquery_saved': bigquery_saved,
            'bigquery_error': bigquery_error if not bigquery_saved else None
        })
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})

@app.route('/api/users')
def api_get_users():
    """API endpoint for getting all users"""
    if not recommender_module:
        return jsonify({'success': False, 'error': 'Recommender module not available', 'users': []})
    
    try:
        users = []
        user_ids_set = set()
        
        # Get unique user IDs from BigQuery ratings_cleaned table only (including NULL movieId/rating entries)
        try:
            from google.cloud import bigquery
            client = bigquery.Client(project="students-group3")
            
            query = """
            SELECT DISTINCT userId
            FROM `students-group3.MovieData.ratings_cleaned`
            ORDER BY userId DESC
            LIMIT 1000
            """
            results = client.query(query).result()
            for row in results:
                user_id = int(row.userId)
                if user_id not in user_ids_set:
                    user_ids_set.add(user_id)
                    users.append({
                        'userId': user_id,
                        'userName': f'User {user_id}',
                        'userEmail': '',
                        'createdAt': ''
                    })
            print(f"✅ Loaded {len(users)} users from BigQuery ratings_cleaned table")
        except Exception as e:
            print(f"⚠️ Could not load users from BigQuery ratings_cleaned: {e}")
        
        # Also get unique user IDs from local ratings (including NULL/NaN entries)
        try:
            if recommender_module.df_ratings is not None and len(recommender_module.df_ratings) > 0:
                unique_user_ids = recommender_module.df_ratings['userId'].dropna().unique()
                for user_id in unique_user_ids:
                    user_id = int(user_id)
                    if user_id not in user_ids_set:
                        user_ids_set.add(user_id)
                        users.append({
                            'userId': user_id,
                            'userName': f'User {user_id}',
                            'userEmail': '',
                            'createdAt': ''
                        })
                print(f"✅ Added users from local ratings data")
        except Exception as e:
            print(f"⚠️ Could not load users from local ratings: {e}")
        
        # Sort by user ID descending
        users.sort(key=lambda x: x['userId'], reverse=True)
        
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'users': [], 'traceback': traceback.format_exc()})

def recommend():
    """Get recommendations"""
    base_path = get_base_path()
    
    if not recommender_module:
        return render_template_string(HTML_TEMPLATE,
                                    status_message='<strong>⚠️ Error:</strong> Recommender module not available.',
                                    status_type='warning',
                                    genres=get_genres_from_movies(),
                                    base_path=base_path)
    
    try:
        user_id = int(request.args.get('user_id', 1))
        method = request.args.get('method', 'hybrid')
        top_n = int(request.args.get('top_n', 10))
        
        if recommender_module.df_movies is None or recommender_module.df_ratings is None:
            recommender_module.load_data(timeout_seconds=10)
        
        if method == 'hybrid':
            recommendations_df = recommender_module.recommend_hybrid(user_id, top_n=top_n)
        elif method == 'content':
            recommendations_df = recommender_module.recommend_content_based(user_id, top_n=top_n)
        elif method == 'collaborative':
            if not getattr(recommender_module, 'SURPRISE_AVAILABLE', False):
                return render_template_string(HTML_TEMPLATE,
                                            status_message='<strong>⚠️ Error:</strong> Collaborative filtering requires surprise library.',
                                            status_type='warning',
                                            genres=get_genres_from_movies(),
                                            base_path=base_path)
            recommendations_df = recommender_module.recommend_collaborative(user_id, top_n=top_n)
        else:
            return render_template_string(HTML_TEMPLATE,
                                        status_message='<strong>⚠️ Error:</strong> Invalid method.',
                                        status_type='warning',
                                        genres=get_genres_from_movies(),
                                        base_path=base_path)
        
        recommendations = []
        for _, row in recommendations_df.iterrows():
            rec = {'movieId': int(row['movieId']), 'title': row['title']}
            if 'pred_rating' in row:
                rec['pred_rating'] = float(row['pred_rating'])
            if 'score' in row:
                rec['score'] = float(row['score'])
            recommendations.append(rec)
        
        return render_template_string(HTML_TEMPLATE,
                                     status_message='<strong>✅ Recommendations generated!</strong>',
                                     status_type='success',
                                     recommendations=recommendations,
                                     genres=get_genres_from_movies(),
                                     get_movie_image_url=get_movie_image_url,
                                     base_path=base_path)
    except Exception as e:
        import traceback
        return render_template_string(HTML_TEMPLATE,
                                    status_message=f'<strong>⚠️ Error:</strong> {str(e)}',
                                    status_type='warning',
                                    genres=get_genres_from_movies(),
                                    base_path=base_path)

def create_user():
    """Create new user in BigQuery"""
    base_path = get_base_path()
    
    if not recommender_module:
        return render_template_string(HTML_TEMPLATE,
                                    status_message='<strong>⚠️ Error:</strong> Recommender module not available.',
                                    status_type='warning',
                                    genres=get_genres_from_movies(),
                                    base_path=base_path)
    
    try:
        user_name = request.args.get('user_name', '').strip()
        user_email = request.args.get('user_email', '').strip()
        
        if not user_name:
            return render_template_string(HTML_TEMPLATE,
                                        status_message='<strong>⚠️ Error:</strong> User name is required.',
                                        status_type='warning',
                                        genres=get_genres_from_movies(),
                                        base_path=base_path)
        
        # Get next user ID from existing ratings
        if recommender_module.df_ratings is not None and len(recommender_module.df_ratings) > 0:
            new_user_id = int(recommender_module.df_ratings['userId'].max()) + 1
        else:
            # Check BigQuery for max user ID if available
            try:
                from google.cloud import bigquery
                client = bigquery.Client(project="students-group3")
                query_max = """
                SELECT MAX(userId) as max_id
                FROM `students-group3.MovieData.ratings_cleaned`
                """
                result = client.query(query_max).result()
                for row in result:
                    if row.max_id:
                        new_user_id = int(row.max_id) + 1
                    else:
                        new_user_id = 1
                    break
                else:
                    new_user_id = 1
            except:
                new_user_id = 1
        
        # Insert into BigQuery ratings_cleaned table with NULL values
        try:
            from google.cloud import bigquery
            client = bigquery.Client(project="students-group3")
            
            # Insert userId with NULL movieId and NULL rating into ratings_cleaned
            query_insert = f"""
            INSERT INTO `students-group3.MovieData.ratings_cleaned` (userId, movieId, rating)
            VALUES ({new_user_id}, NULL, NULL)
            """
            client.query(query_insert).result()
            print(f"✅ New user created in BigQuery ratings_cleaned: ID={new_user_id}")
        except Exception as e:
            print(f"⚠️ Could not insert into BigQuery (using local ID): {e}")
            print(f"✅ New user created locally: ID={new_user_id}")
        
        return render_template_string(HTML_TEMPLATE,
                                     status_message='<strong>✅ System Ready!</strong>',
                                     status_type='success',
                                     genres=get_genres_from_movies(),
                                     user_created=True,
                                     new_user_id=new_user_id,
                                     base_path=base_path)
    except Exception as e:
        import traceback
        return render_template_string(HTML_TEMPLATE,
                                    status_message='<strong>✅ System Ready!</strong>',
                                    status_type='success',
                                    genres=get_genres_from_movies(),
                                    base_path=base_path)

def add_rating():
    """Add rating"""
    base_path = get_base_path()
    
    if not recommender_module:
        return render_template_string(HTML_TEMPLATE,
                                    status_message='<strong>⚠️ Error:</strong> Recommender module not available.',
                                    status_type='warning',
                                    genres=get_genres_from_movies(),
                                    base_path=base_path)
    
    try:
        user_id = int(request.args.get('user_id'))
        movie_id = int(request.args.get('movie_id'))
        rating = float(request.args.get('rating'))
        
        if recommender_module.df_movies is None or recommender_module.df_ratings is None:
            recommender_module.load_data(timeout_seconds=10)
        
        rmse = recommender_module.add_new_user_ratings(
            user_id,
            [{'movieId': movie_id, 'rating': rating}],
            auto_retrain=True
        )
        
        success_msg = f'✅ Rating added successfully!<br>User {user_id} rated Movie {movie_id} with {rating} stars'
        if rmse is not None:
            success_msg += f'<br>🔄 Model retrained! RMSE: {rmse:.4f}'
        elif not getattr(recommender_module, 'SURPRISE_AVAILABLE', False):
            success_msg += '<br>ℹ️ Using content-based filtering (collaborative filtering not available)'
        else:
            success_msg += '<br>ℹ️ Model will use updated ratings for future recommendations'
        
        return render_template_string(HTML_TEMPLATE,
                                     status_message='<strong>✅ System Ready!</strong>',
                                     status_type='success',
                                     rating_message=success_msg,
                                     rating_message_type='success',
                                     genres=get_genres_from_movies(),
                                     base_path=base_path)
    except Exception as e:
        import traceback
        return render_template_string(HTML_TEMPLATE,
                                    status_message='<strong>✅ System Ready!</strong>',
                                    status_type='success',
                                    rating_message=f'⚠️ Error: {str(e)}',
                                    rating_message_type='warning',
                                    genres=get_genres_from_movies(),
                                    base_path=base_path)

if __name__ == '__main__':
    import os
    import socket
    
    def is_port_available(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return True
            except OSError:
                return False
    
    preferred_ports = [8501, 8080, 5000, 3000, 8888]
    port = None
    
    if 'PORT' in os.environ:
        port = int(os.environ.get('PORT'))
    else:
        for p in preferred_ports:
            if is_port_available(p):
                port = p
                break
        
        if port is None:
            import random
            for _ in range(10):
                p = random.randint(8000, 9000)
                if is_port_available(p):
                    port = p
                    break
    
    if port is None:
        print("❌ Error: Could not find an available port!")
        exit(1)
    
    print(f"\n{'='*60}")
    print(f"🚀 Starting Professional Flask app on port {port}")
    print(f"{'='*60}")
    if port == 8501:
        print(f"📱 For Google Cloud Notebooks, access via:")
        print(f"   https://YOUR-NOTEBOOK-URL/proxy/{port}/")
    else:
        print(f"📱 Access Flask at:")
        print(f"   http://localhost:{port}")
        print(f"   Or for GCP Notebooks: https://YOUR-NOTEBOOK-URL/proxy/{port}/")
    print(f"{'='*60}\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)

