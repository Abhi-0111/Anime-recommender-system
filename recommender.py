import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import requests
import time
import re

# --- Jikan API Integration & Caching ---
image_cache = {}
JIKAN_API_URL = "https://api.jikan.moe/v4/anime"

def get_image_url(anime_name):
    if anime_name in image_cache:
        return image_cache[anime_name]
    try:
        time.sleep(0.5)
        params = {'q': anime_name, 'limit': 1}
        response = requests.get(JIKAN_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if data['data']:
            image_url = data['data'][0]['images']['jpg']['image_url']
            image_cache[anime_name] = image_url
            return image_url
        else:
            image_cache[anime_name] = None
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image for '{anime_name}': {e}")
        image_cache[anime_name] = None
        return None

# --- ML Model & Data Setup ---
anime_df = None
cosine_sim = None
indices = None
all_genres = []

def load_data_and_build_model():
    global anime_df, cosine_sim, indices, all_genres
    try:
        anime_df = pd.read_csv('anime.csv')
        anime_df['genre'] = anime_df['genre'].fillna('')
        anime_df['name_normalized'] = anime_df['name'].str.lower().str.strip()
        anime_df.dropna(subset=['rating', 'name'], inplace=True)
        anime_df['features'] = anime_df['genre'] + ' ' + anime_df['type']
        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(anime_df['features'])
        cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
        indices = pd.Series(anime_df.index, index=anime_df['name_normalized']).drop_duplicates()
        genres_set = set()
        for s in anime_df['genre']:
            genres_set.update(g.strip() for g in s.split(','))
        all_genres = sorted([g for g in genres_set if g])
        print("✅ Recommender system loaded successfully.")
        return True
    except FileNotFoundError:
        print("❌ ERROR: `anime.csv` not found.")
        return False
    except Exception as e:
        print(f"❌ An error occurred during model setup: {e}")
        return False

# --- Refactored Logic for Reusability ---

def get_recommendations_logic(title):
    title_norm = title.lower().strip()
    if title_norm not in indices: return []
    idx = indices[title_norm]
    sim_scores = sorted(list(enumerate(cosine_sim[idx])), key=lambda x: x[1], reverse=True)[1:6] # Top 5
    anime_indices = [i[0] for i in sim_scores]
    recs_df = anime_df.iloc[anime_indices][['name', 'genre', 'rating']]
    recs_list = recs_df.to_dict(orient='records')
    for anime in recs_list:
        anime['image_url'] = get_image_url(anime['name'])
    return recs_list

def get_genre_anime_logic(genre):
    filtered_df = anime_df[anime_df['genre'].str.contains(genre, case=False, na=False)]
    output_df = filtered_df.sort_values('members', ascending=False).head(5) # Top 5
    anime_list = output_df[['name', 'genre']].to_dict(orient='records')
    for anime in anime_list:
        anime['image_url'] = get_image_url(anime['name'])
    return anime_list

# --- Flask Web Server ---
app = Flask(__name__)
CORS(app)

# --- API Endpoints ---

@app.route('/api/anime', methods=['GET'])
def get_all_anime():
    genre = request.args.get('genre', None)
    if genre:
        filtered_df = anime_df[anime_df['genre'].str.contains(genre, case=False, na=False)]
    else:
        filtered_df = anime_df
    output_df = filtered_df.sort_values('members', ascending=False).head(100)
    anime_list = output_df[['name', 'genre']].to_dict(orient='records')
    for anime in anime_list:
        anime['image_url'] = get_image_url(anime['name'])
    return jsonify(anime_list)

@app.route('/api/genres', methods=['GET'])
def get_genres():
    return jsonify(all_genres)

@app.route('/api/random', methods=['GET'])
def get_random_anime():
    random_anime = anime_df.sample(n=1).to_dict(orient='records')[0]
    random_anime['image_url'] = get_image_url(random_anime['name'])
    return jsonify(random_anime)

@app.route('/api/search', methods=['GET'])
def search_anime():
    query = request.args.get('q', '').strip()
    if not query: return jsonify([])
    search_results = anime_df[anime_df['name'].str.contains(query, case=False, na=False)]
    output_results = search_results.sort_values('members', ascending=False).head(50)
    anime_list = output_results[['name', 'genre']].to_dict(orient='records')
    for anime in anime_list:
        anime['image_url'] = get_image_url(anime['name'])
    return jsonify(anime_list)

@app.route('/api/recommend', methods=['GET'])
def get_recommendations_endpoint():
    title = request.args.get('title', '')
    if not title: return jsonify({"error": "Title parameter is required."}), 400
    recommendations = get_recommendations_logic(title)
    if not recommendations: return jsonify({"error": f"Title '{title}' not found."}), 404
    return jsonify(recommendations)

@app.route('/api/chatbot', methods=['POST'])
def handle_chat():
    message = request.json.get('message', '').lower().strip()
    
    # Intent 1: Recommendation Request
    rec_patterns = [r'like\s(.+)', r'similar to\s(.+)', r'recommendations for\s(.+)']
    for pattern in rec_patterns:
        match = re.search(pattern, message)
        if match:
            anime_title = match.group(1).strip()
            recommendations = get_recommendations_logic(anime_title)
            if recommendations:
                return jsonify({
                    'reply': f"Here are some anime similar to '{anime_title.title()}':",
                    'anime_list': recommendations
                })
            else:
                return jsonify({'reply': f"Sorry, I couldn't find '{anime_title.title()}' in my database."})

    # Intent 2: Genre Request
    matched_genre = next((genre for genre in all_genres if genre.lower() in message), None)
    if matched_genre:
        anime_list = get_genre_anime_logic(matched_genre)
        return jsonify({
            'reply': f"Here are some popular anime in the '{matched_genre}' genre:",
            'anime_list': anime_list
        })
        
    # Fallback response
    return jsonify({
        'reply': "Sorry, I don't understand. You can ask me for 'anime like Naruto' or 'show me some action anime'."
    })

if __name__ == '__main__':
    if load_data_and_build_model():
        app.run(debug=True, port=5000)

