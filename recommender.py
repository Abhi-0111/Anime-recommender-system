import pandas as pd
from flask import Flask, jsonify, request
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from flask_cors import CORS
import random
import requests
import time
import re

# --- Initialization ---
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# --- Data Loading and Model Building ---
try:
    anime_df = pd.read_csv('anime.csv')
    anime_df['genre'] = anime_df['genre'].fillna('')
    anime_df['type'] = anime_df['type'].fillna('')
    
    # Create a 'features' column for the TF-IDF model
    anime_df['features'] = anime_df['genre'] + ' ' + anime_df['type']
    
    # Normalize names for easier matching
    anime_df['name_normalized'] = anime_df['name'].str.lower().str.strip()

    # TF-IDF Model
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(anime_df['features'])

    # Cosine Similarity Model
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

    # For mapping anime titles to their index
    indices = pd.Series(anime_df.index, index=anime_df['name_normalized']).drop_duplicates()

    # Create a flat, unique list of all genres
    all_genres = sorted(list(set(genre for sublist in anime_df['genre'].str.split(', ') for genre in sublist if genre)))

    print("✅ Recommender system loaded successfully.")

except FileNotFoundError:
    print("❌ ERROR: anime.csv not found. Please make sure the dataset is in the same directory.")
    anime_df = None # Set to None to handle errors in routes

# --- Image Fetching with Cache ---
image_cache = {}
JIKAN_API_URL = "https://api.jikan.moe/v4/anime"

def get_image_url(anime_name):
    normalized_name = anime_name.lower().strip()
    if normalized_name in image_cache:
        return image_cache[normalized_name]
    
    try:
        time.sleep(0.5) # Rate limit to be respectful to the API
        response = requests.get(JIKAN_API_URL, params={"q": anime_name, "limit": 1})
        response.raise_for_status()
        data = response.json()
        if data['data']:
            image_url = data['data'][0]['images']['jpg']['image_url']
            image_cache[normalized_name] = image_url
            return image_url
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch image for {anime_name}: {e}")
    
    return None

# --- Helper function to add image URLs to anime data ---
def add_images_to_list(anime_list):
    for anime in anime_list:
        anime['image_url'] = get_image_url(anime['name'])
    return anime_list

# --- API Endpoints ---
@app.route('/api/anime', methods=['GET'])
def get_all_anime():
    if anime_df is None: return jsonify({"error": "Dataset not loaded"}), 500
    
    genre = request.args.get('genre', '')
    if genre:
        filtered_df = anime_df[anime_df['genre'].str.contains(genre, case=False, na=False)]
    else:
        # Get top 100 by popularity/members as a default
        filtered_df = anime_df.sort_values('members', ascending=False).head(100)

    anime_list = filtered_df.to_dict(orient='records')
    anime_list_with_images = add_images_to_list(anime_list)
    return jsonify(anime_list_with_images)

@app.route('/api/genres', methods=['GET'])
def get_genres():
    if anime_df is None: return jsonify({"error": "Dataset not loaded"}), 500
    return jsonify(all_genres)

@app.route('/api/recommend', methods=['GET'])
def get_recommendations():
    if anime_df is None: return jsonify({"error": "Dataset not loaded"}), 500
    
    title = request.args.get('title', '').lower().strip()
    print(f"Received recommendation request for: '{title}'") # Debug print

    if title not in indices:
        return jsonify({"error": "Anime title not found in the dataset."}), 404
        
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:11] # Get top 10 similar, excluding itself
    anime_indices = [i[0] for i in sim_scores]
    
    recommended_anime = anime_df.iloc[anime_indices].to_dict(orient='records')
    recommended_anime_with_images = add_images_to_list(recommended_anime)
    return jsonify(recommended_anime_with_images)

@app.route('/api/search', methods=['GET'])
def search_anime():
    if anime_df is None: return jsonify({"error": "Dataset not loaded"}), 500

    query = request.args.get('q', '').lower().strip()
    if not query:
        return jsonify([])
    
    results_df = anime_df[anime_df['name_normalized'].str.contains(query, na=False)].head(20)
    search_results = results_df.to_dict(orient='records')
    search_results_with_images = add_images_to_list(search_results)
    return jsonify(search_results_with_images)
    
@app.route('/api/random', methods=['GET'])
def get_random_anime():
    if anime_df is None: return jsonify({"error": "Dataset not loaded"}), 500
    
    random_anime = anime_df.sample(1).to_dict(orient='records')[0]
    # No need to add image here, the modal will fetch recommendations which include images
    return jsonify(random_anime)

@app.route('/api/chatbot', methods=['POST'])
def handle_chatbot():
    if anime_df is None: return jsonify({"error": "Dataset not loaded"}), 500
    
    data = request.json
    message = data.get('message', '').lower()
    
    # Try to find a genre in the message
    found_genres = [g for g in all_genres if g.lower() in message]
    
    # Try to find "similar to" or "like" pattern
    similar_match = re.search(r'(similar to|like)\s+"?([^"]+)"?', message)

    if similar_match:
        anime_name = similar_match.group(2).strip()
        normalized_name = anime_name.lower()
        if normalized_name in indices:
            # Re-use recommendation logic
            idx = indices[normalized_name]
            sim_scores = sorted(list(enumerate(cosine_sim[idx])), key=lambda x: x[1], reverse=True)[1:6]
            anime_indices = [i[0] for i in sim_scores]
            anime_list = anime_df.iloc[anime_indices].to_dict(orient='records')
            anime_list_with_images = add_images_to_list(anime_list)
            return jsonify({
                "reply": f"Here are some anime similar to {anime_name}:",
                "anime_list": anime_list_with_images
            })
        else:
            return jsonify({"reply": f"Sorry, I couldn't find '{anime_name}' in my database."})

    elif found_genres:
        genre = found_genres[0]
        results_df = anime_df[anime_df['genre'].str.contains(genre, case=False, na=False)].sort_values('members', ascending=False).head(5)
        anime_list = results_df.to_dict(orient='records')
        anime_list_with_images = add_images_to_list(anime_list)
        return jsonify({
            "reply": f"Here are some popular {genre} anime:",
            "anime_list": anime_list_with_images
        })
        
    else:
        return jsonify({"reply": "I can help you find anime. Try asking for a genre (e.g., 'show me some action anime') or for recommendations (e.g., 'anime like Death Note')."})

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True)

