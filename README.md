# ANIME RECOMMENDER SYSTEM
A full-stack web application that provides personalized anime recommendations based on a content-based filtering machine learning model. The backend is powered by Python, Flask, and Scikit-learn, while the interactive frontend is built with pure HTML, Tailwind CSS, and JavaScript.

This project uses the "Anime Recommendations Database" from Kaggle to train the model and fetches live cover art from the Jikan API.

(Replace the placeholder above with a screenshot of your running application!)

✨ Features

Content-Based Recommendations: Get suggestions for similar anime based on genre and type using a TF-IDF and Cosine Similarity model.

Dynamic Search: Instantly search for any anime in the dataset by name.

Filter by Genre: Browse the most popular anime within a specific genre.

Random Suggestions: Discover a new anime with the click of a button.

Live Cover Art: Fetches and displays up-to-date anime posters from the Jikan API.

Interactive UI: A sleek, modern, and responsive user interface built for a great user experience.

🛠️ Tech Stack

Backend

Python: Core programming language.

Flask: A lightweight web server framework to create the API.

Pandas: For data loading, cleaning, and manipulation.

Scikit-learn: For building the TF-IDF vectorizer and Cosine Similarity matrix.

Requests: To fetch data from the external Jikan API.

Frontend

HTML5: For the structure of the web page.

Tailwind CSS: For utility-first styling and a responsive design.

JavaScript (ES6+): For DOM manipulation and handling all frontend logic, including API calls to the backend.

🚀 Setup and Installation

Follow these steps to get the project up and running on your local machine.

1. Prerequisites

Python 3.8+ and pip installed. (Make sure Python is added to your system's PATH).

Git for cloning the repository.

2. Clone the Repository

Open your terminal or command prompt and clone this repository:

git clone [https://github.com/your-username/anime-recommender-system.git](https://github.com/Abhi-0111/anime-recommender-system.git)
cd anime-recommender-system


3. Backend Setup

a. Create a Virtual Environment (Recommended)
It's best practice to create a virtual environment to keep project dependencies isolated.

# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS / Linux
python3 -m venv venv
source venv/bin/activate


b. Install Python Dependencies
Install all the necessary libraries for the backend server:

pip install pandas scikit-learn Flask Flask-Cors requests


c. Download the Dataset

Download the anime.csv file from the Anime Recommendations Database on Kaggle.

Place the anime.csv file in the root directory of the project (the same folder as recommender.py).

4. Running the Application

a. Start the Backend Server
With your virtual environment still active, run the Flask server:

python recommender.py


If successful, you will see output like this, indicating the server is running:

✅ Recommender system loaded successfully.
 * Running on [http://127.0.0.1:5000](http://127.0.0.1:5000)


Keep this terminal window open!

b. Launch the Frontend

Navigate to the project folder in your file explorer.

Open the index.html file directly in your favorite web browser (like Chrome, Firefox, or Edge).

The application should now be fully functional!

🔬 How It Works

This project uses a Content-Based Filtering approach. Here's a quick overview of the recommendation logic:

Data Preprocessing: The anime.csv data is loaded into a Pandas DataFrame. The genres and anime types are combined into a single "features" string for each anime.

TF-IDF Vectorization: The text "features" are converted into a numerical matrix using Term Frequency-Inverse Document Frequency (TF-IDF). This process gives more importance to genres that are unique and descriptive for a particular anime.

Cosine Similarity: A Cosine Similarity matrix is computed from the TF-IDF matrix. This matrix contains a similarity score (from 0 to 1) between every pair of anime in the dataset.

Serving Recommendations: When a user requests recommendations for an anime, the backend finds that anime in the similarity matrix and returns the top 10 anime with the highest scores.

📝 API Endpoints

The Flask backend provides the following API endpoints:

Method

Endpoint

Description

GET

/api/anime

Get a list of the top 100 most popular anime.

GET

/api/anime?genre=<g>

Get top anime filtered by a specific genre.

GET

/api/genres

Get a list of all unique genres.

GET

/api/search?q=<query>

Search for anime by name.

GET

/api/random

Get a single random anime from the dataset.

GET

/api/recommend?title=<t>

Get the top 10 recommendations for a given anime.
