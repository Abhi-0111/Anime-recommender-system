import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, request, jsonify
from flask_cors import CORS
import os


DATASET_PATH = 'anime.csv'

def load_and_preprocess_data(path):
    """Loads and preprocesses the anime dataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found at {path}. Please download it and place it in the correct directory.")
    
        df = pd.read_csv(path)
    
   
    df = df[['name', 'genre', 'type', 'episodes', 'rating', 'members']].copy()
    df.dropna(subset=['name', 'genre'], inplace=True)
    
    
    df['anime_id'] = range(len(df))
    df.set_index('anime_id', inplace=True)
    
   
    df['features'] = df['genre'] + ' ' + df['type']
    df['features'] = df['features'].fillna('')
    
    return df

def create_recommendation_engine(df):
    """Creates the TF-IDF vectorizer and cosine similarity matrix."""

    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['features'])
    
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    indices = pd.Series(df.index, index=df['name']).drop_duplicates()

    cleaned_indices = pd.Series(df.index, index=df['name'].str.lower().str.strip()).drop_duplicates()
    
    return cosine_sim, indices, cleaned_indices


app = Flask(__name__)
CORS(app)

try:
    anime_df = load_and_preprocess_data(DATASET_PATH)
    cosine_sim_matrix, anime_indices, cleaned_anime_indices = create_recommendation_engine(anime_df)
    print("✅ Recommender system loaded successfully.")
except FileNotFoundError as e:
    print(f"❌ ERROR: {e}")
    print("Please make sure the 'anime.csv' file is in the same directory and run the script again.")
    anime_df = None # Set to None to handle errors gracefully in routes

@app.route('/api/anime', methods=['GET'])
def get_all_anime():
    """
    Endpoint to get a list of anime.
    Can be filtered by genre using a query parameter.
    e.g., /api/anime?genre=Action
    """
    if anime_df is None:
        return jsonify({"error": "Dataset not loaded. Check server logs."}), 500
    
    genre_filter = request.args.get('genre', None)

    if genre_filter:
        filtered_anime = anime_df[anime_df['genre'].str.contains(genre_filter, case=False, na=False)]
        output_anime = filtered_anime.sort_values('members', ascending=False).head(50)
    else:
        output_anime = anime_df.sort_values('members', ascending=False).head(50)
        
    result = output_anime[['name', 'genre']].to_dict(orient='records')
    return jsonify(result)


@app.route('/api/genres', methods=['GET'])
def get_all_genres():
    """Endpoint to get a list of all unique genres."""
    if anime_df is None:
        return jsonify({"error": "Dataset not loaded. Check server logs."}), 500
    
    all_genres = anime_df['genre'].dropna().str.split(', ').explode().str.strip().unique()
    sorted_genres = sorted([genre for genre in all_genres if genre]) # Filter out empty strings
    return jsonify(sorted_genres)


@app.route('/api/random', methods=['GET'])
def get_random_anime():
    """Endpoint to get a single random anime."""
    if anime_df is None:
        return jsonify({"error": "Dataset not loaded. Check server logs."}), 500
    
    random_anime = anime_df.sample(1)
    result = random_anime[['name', 'genre', 'rating']].to_dict(orient='records')[0]
    return jsonify(result)


@app.route('/api/recommend', methods=['GET'])
def recommend_anime():
    """Endpoint to get recommendations for a given anime."""
    if anime_df is None:
        return jsonify({"error": "Dataset not loaded. Check server logs."}), 500

    title = request.args.get('title', '')
    
    print(f"--- Received request for title: '{title}'")

    cleaned_title = title.lower().strip()
    if not cleaned_title or cleaned_title not in cleaned_anime_indices:
        print(f"--- ERROR: Cleaned title '{cleaned_title}' not found in indices.")
        return jsonify({"error": f"Anime title '{title}' not found."}), 404

    idx = cleaned_anime_indices[cleaned_title]

    sim_scores = list(enumerate(cosine_sim_matrix[idx]))

    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    sim_scores = sim_scores[1:11]

    anime_indices_result = [i[0] for i in sim_scores]

    recommended_anime = anime_df.iloc[anime_indices_result][['name', 'genre', 'rating']]
    return jsonify(recommended_anime.to_dict(orient='records'))

@app.route('/api/search', methods=['GET'])
def search_anime():
    """Endpoint to search for anime by name."""
    if anime_df is None:
        return jsonify({"error": "Dataset not loaded. Check server logs."}), 500

    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([]) # Return empty list if query is empty

    search_results = anime_df[anime_df['name'].str.contains(query, case=False, na=False)]
    
    output_results = search_results.sort_values('members', ascending=False).head(50)
    
    return jsonify(output_results[['name', 'genre']].to_dict(orient='records'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)

