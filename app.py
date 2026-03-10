import streamlit as st
import pickle
import pandas as pd
import requests
import os
import gdown
# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# ================== DOWNLOAD FILES ==================
if not os.path.exists("similarity.pkl"):
    gdown.download(
        "https://drive.google.com/uc?id=1bVtmYxUBJdbm1Mj7mdBpwR71aXkJ80f4",
        "similarity.pkl",
        quiet=False
    )

# ================= API SECURITY. =================
try:
    api_key = st.secrets["TMDB_API_KEY"]
except:
    st.error("TMDB API Key not found. Check secrets.toml")
    st.stop()

#========== MOOD MAP =============================
MOOD_MAP = {
    "😊 Happy": {
        "genres": "35,10751",
        "keywords": "fun,feel good"
    },
    "😢 Sad": {
        "genres": "18,10749",
        "keywords": "emotional"
    },
    "🔥 Action": {
        "genres": "28,12",
        "keywords": "fight,war"
    },
    "❤️ Romantic": {
        "genres": "10749",
        "keywords": "love"
    },
    "😱 Thriller": {
        "genres": "53,27",
        "keywords": "suspense"
    },
    "🧠 Mind-Bending": {
        "genres": "878,9648",
        "keywords": "mystery,twist"
    }
}
#============== CSS COUSTOM ===========================
st.markdown("""
<style>

body {
    background-color: #0e1117;
}

.movie-card {
    background-color: #1c1f26;
    padding: 12px;
    border-radius: 12px;
    transition: 0.3s;
    text-align: center;
}

.movie-card:hover {
    transform: scale(1.05);
}

.movie-title {
    font-size: 15px;
    font-weight: 600;
    color: white;
    margin-top: 8px;
}

</style>
""", unsafe_allow_html=True)

# ================= LOAD DATA =================
movies = pickle.load(open("model.pkl", "rb"))
similarity = pickle.load(open("similarity.pkl", "rb"))

# ================= FUNCTIONS =================
def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    data = requests.get(url).json()

    poster_path = data.get("poster_path")
    rating = data.get("vote_average")
    overview = data.get("overview", "No description available.")

    poster = (
        "https://image.tmdb.org/t/p/w500/" + poster_path
        if poster_path
        else "https://via.placeholder.com/300x450?text=No+Image"
    )

    return poster, rating, overview
#========= DISPLAY MOVIE =========================
def display_movie(movie):
    if movie.get("poster_path"):
        st.image(
            f"https://image.tmdb.org/t/p/w500{movie['poster_path']}",
            use_column_width=True
        )

    st.write(f"### {movie['title']}")
    st.write(f"⭐ Rating: {movie['vote_average']}")

    trailer_url = fetch_trailer(movie["id"])

    if trailer_url:
        with st.expander("▶ Watch Trailer"):
            st.video(f"https://www.youtube.com/watch?v={trailer_url}")

# Fetch Trailer
def fetch_trailer(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={api_key}"
    data = requests.get(url).json()

    for video in data.get("results", []):
        if video["type"] == "Trailer" and video["site"] == "YouTube":
            return video["key"]
    return None

# Fetch Genres
def fetch_genres():
    url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={api_key}"
    data = requests.get(url).json()
    return data["genres"]

def fetch_movies_by_genre(genre_id):
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&with_genres={genre_id}"
    data = requests.get(url).json()

    movies_list = []

    for movie in data["results"][:15]:

        trailer = fetch_trailer(movie["id"])

        movies_list.append({
            "id": movie["id"],
            "title": movie["title"],
            "poster": "https://image.tmdb.org/t/p/w500/" + movie["poster_path"],
            "rating": movie["vote_average"],
            "trailer": trailer
        })

    return movies_list

#-------- fetch movie by mood -------------------
def fetch_movies_by_mood(genre_ids, keywords):
    url = (
        f"https://api.themoviedb.org/3/discover/movie?"
        f"api_key={api_key}"
        f"&with_genres={genre_ids}"
        f"&sort_by=popularity.desc"
    )

    data = requests.get(url).json()

    movies = []

    for movie in data.get("results", [])[:10]:
        trailer = fetch_trailer(movie["id"])
        poster = (
            f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
            if movie.get("poster_path") else None
        )

        movies.append({
            "id": movie["id"],
            "title": movie["title"],
            "poster": poster,
            "rating": movie["vote_average"],
            "trailer": trailer
        })

    return movies
#============= RECOMMENDATION FUNCTION ===================
def recommend(movie):

    index = movies[movies["title"] == movie].index[0]
    distances = similarity[index]

    movie_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:11]

    recommended = []

    for i in movie_list:
        movie_id = movies.iloc[i[0]].movie_id
        title = movies.iloc[i[0]].title
        similarity_score = round(i[1] * 100, 2)

        poster, rating, overview = fetch_movie_details(movie_id)
        trailer = fetch_trailer(movie_id)

def get_recommendation_reason(similarity_score):

    if similarity_score > 0.75:
        return "Very strong similarity in genre, keywords and storyline."

    elif similarity_score > 0.60:
        return "Similar genre and plot style."

    elif similarity_score > 0.45:
        return "Some common themes and movie structure."

    else:
        return "General recommendation based on movie similarity."
        
        recommended.append({
            "title": title,
            "poster": poster,
            "rating": rating,
            "overview": overview,
            "similarity": similarity_score,
            "trailer": trailer,
            "reason": get_recommendation_reason(similarity_score),
        })
        
    return recommended
# ---------------- SESSION STATE ----------------
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []

# ================ SEARCH SECTION WITH MODAL ============
st.header("🔎 Search Movies")

query = st.text_input(
    "Search",
    placeholder="Type movie name...",
)

# ---------- AUTOCOMPLETE FUNCTION ----------
def autocomplete_movies(query):
    if len(query) < 2:
        return []

    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={query}"
    data = requests.get(url).json()

    return data.get("results", [])[:8]

results = autocomplete_movies(query)

# ---------- SHOW SUGGESTIONS ----------
if results:
    movie_titles = [movie["title"] for movie in results]

    selected_title = st.selectbox(
        "Suggestions",
        movie_titles,
        label_visibility="collapsed"
    )

    selected_movie = None
    for movie in results:
        if movie["title"] == selected_title:
            selected_movie = movie
            break

    if selected_movie:
        poster = (
            f"https://image.tmdb.org/t/p/w500{selected_movie['poster_path']}"
            if selected_movie.get("poster_path") else None
        )

        st.markdown("## 🎬 Movie Details")

        col1, col2 = st.columns([1, 2])

        with col1:
            if poster:
                st.image(poster)

        with col2:
            st.markdown(f"### {selected_movie['title']}")
            st.write(f"⭐ Rating: {selected_movie['vote_average']}")
            st.write(selected_movie.get("overview", "No overview available."))

            trailer = fetch_trailer(selected_movie["id"])

            if trailer:
                with st.expander("▶ Watch Trailer"):
                    st.video(f"https://www.youtube.com/watch?v={trailer}")
 # ---------- RECOMMEND BUTTON ----------
        if st.button("🎯 Recommend Similar Movies"):

            st.session_state.recommendations = recommend(selected_movie["title"])


# ---------------- DISPLAY RECOMMENDATIONS ----------------
recommendations = st.session_state.recommendations

if recommendations:

    st.subheader("🎬 Recommended Movies")

    cols = st.columns(5)

    for idx, movie in enumerate(recommendations):

        with cols[idx % 5]:

            if movie["poster"]:
                st.image(movie["poster"])

            st.markdown(f"**{movie['title']}**")
            st.caption(f"⭐ {movie['rating']}")
            st.caption(f"🤖 {movie['reason']}")

            if movie["trailer"]:
                with st.expander("▶ Watch Trailer"):
                    st.video(
                        f"https://www.youtube.com/watch?v={movie['trailer']}"
                    )      
                
elif query:
    st.warning("No movies found 😔")
# =============== GENRE SECTION WITH MODAL =============== #

st.header("🎭 Browse by Genre")

# Fetch Genres
def fetch_genres():
    url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={api_key}"
    data = requests.get(url).json()
    return data["genres"]

# Fetch Movies by Genre
def fetch_movies_by_genre(genre_id):
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&with_genres={genre_id}"
    data = requests.get(url).json()

    movies = []

    for movie in data["results"][:10]:

        poster = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie["poster_path"] else None
        trailer = fetch_trailer(movie["id"])

        movies.append({
            "id": movie["id"],
            "title": movie["title"],
            "poster": poster,
            "rating": movie["vote_average"],
            "trailer": trailer
        })

    return movies


# Get Genre List
genres = fetch_genres()
genre_names = [genre["name"] for genre in genres]

selected_genre_name = st.selectbox("Select Genre", genre_names)

# Find selected genre ID
selected_genre_id = None
for genre in genres:
    if genre["name"] == selected_genre_name:
        selected_genre_id = genre["id"]
        break


# Show Movies
if selected_genre_id:

    genre_movies = fetch_movies_by_genre(selected_genre_id)

    cols = st.columns(5)

    for idx, movie in enumerate(genre_movies):

        with cols[idx % 5]:

            if movie["poster"]:
                st.image(movie["poster"])

            st.markdown(f"**{movie['title']}**")
            st.caption(f"⭐ {movie['rating']}")

            if movie["trailer"]:
                with st.expander("▶ Watch Trailer"):
                    st.video(f"https://www.youtube.com/watch?v={movie['trailer']}")
# =============== POPULAR MOVIES SECTION WITH MODAL ================ #

st.header("🔥 Popular Movies")

# Fetch Trailer
def fetch_trailer(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={api_key}"
    data = requests.get(url).json()

    for video in data.get("results", []):
        if video["type"] == "Trailer" and video["site"] == "YouTube":
            return video["key"]
    return None


# Fetch Popular Movies
def fetch_popular_movies():
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}"
    data = requests.get(url).json()

    movies = []

    for movie in data["results"][:10]:

        poster = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie["poster_path"] else None
        trailer = fetch_trailer(movie["id"])

        movies.append({
            "id": movie["id"],
            "title": movie["title"],
            "poster": poster,
            "rating": movie["vote_average"],
            "trailer": trailer
        })

    return movies


popular_movies = fetch_popular_movies()

cols = st.columns(5)

for idx, movie in enumerate(popular_movies):

    with cols[idx % 5]:

        if movie["poster"]:
            st.image(movie["poster"])

        st.markdown(f"**{movie['title']}**")
        st.caption(f"⭐ {movie['rating']}")

        if movie["trailer"]:
            with st.expander("▶ Watch Trailer"):
                st.video(f"https://www.youtube.com/watch?v={movie['trailer']}")

#==================== MOOD SECTION ===================
st.header("🎭 Pick Movies Based on Your Mood")

selected_mood = st.selectbox(
    "How are you feeling today?",
    list(MOOD_MAP.keys())
)

if selected_mood:

    mood_data = MOOD_MAP[selected_mood]

    mood_movies = fetch_movies_by_mood(
        mood_data["genres"],
        mood_data["keywords"]
    )

    st.subheader(f"✨ Movies for {selected_mood}")

    cols = st.columns(5)

    for idx, movie in enumerate(mood_movies):

        with cols[idx % 5]:

            if movie["poster"]:
                st.image(movie["poster"])

            st.markdown(f"**{movie['title']}**")
            st.caption(f"⭐ {movie['rating']}")

            if movie["trailer"]:
                with st.expander("▶ Watch Trailer"):
                    st.video(
                        f"https://www.youtube.com/watch?v={movie['trailer']}"
                    )

  









