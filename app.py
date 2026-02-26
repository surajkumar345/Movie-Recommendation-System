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

#==============  COUSTOM ===========================
st.markdown(
    """
<style>

/* ----------- GLOBAL ----------- */
body {
    background: linear-gradient(180deg, #0e1117, #000000);
    color: white;
    font-family: 'Segoe UI', sans-serif;
}

/* ----------- MOVIE CARD ----------- */
.movie-card {
    background: rgba(28, 31, 38, 0.75);
    backdrop-filter: blur(10px);
    border-radius: 14px;
    padding: 10px;
    transition: 0.35s ease-in-out;
    box-shadow: 0 10px 25px rgba(0,0,0,0.6);
    position: relative;
    overflow: hidden;
}

.movie-card:hover {
    transform: translateY(-8px) scale(1.03);
}

/* ----------- POSTER ----------- */
.movie-card img {
    width: 100%;
    border-radius: 10px;
}

/* ----------- TITLE ----------- */
.movie-title {
    margin-top: 8px;
    font-size: 15px;
    font-weight: 600;
}

/* ----------- RATING ----------- */
.movie-rating {
    color: gold;
    font-size: 14px;
}

/* ----------- TRAILER OVERLAY ----------- */
.trailer-btn {
    position: absolute;
    top: 40%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0,0,0,0.7);
    color: white;
    padding: 12px 18px;
    border-radius: 50px;
    font-size: 16px;
    opacity: 0;
    transition: 0.3s;
    cursor: pointer;
}

.movie-card:hover .trailer-btn {
    opacity: 1;
}

.slider-container {
    display: flex;
    overflow-x: auto;
    gap: 16px;
    padding: 10px 0;
}

.slider-container::-webkit-scrollbar {
    height: 6px;
}

.slider-container::-webkit-scrollbar-thumb {
    background: #444;
    border-radius: 10px;
}

.movie-card {
    min-width: 160px;
    background-color: #1c1f26;
    border-radius: 12px;
    padding: 8px;
    transition: transform 0.3s;
}

.movie-card:hover {
    transform: scale(1.08);
}

.movie-card img {
    border-radius: 10px;
}

.movie-title {
    font-size: 14px;
    font-weight: 600;
    margin-top: 6px;
    color: white;
    text-align: center;
}

</style>
""",
unsafe_allow_html=True 
)
#=========== MOOD CHOICE ==================
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

#------fetch movie by mood-------------------
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

#----------- Autocomplete search--------------
def autocomplete_movies(query):
    if len(query) < 2:
        return []

    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={query}"
    data = requests.get(url).json()

    suggestions = []

    for movie in data.get("results", [])[:8]:
        suggestions.append({
            "id": movie["id"],
            "title": movie["title"]
        })

    return suggestions
#========= WHY RECOMMEND =====================
def recommendation_reason(similarity):
    if similarity >= 85:
        return "🔥 Very strong match based on genre, storyline, and themes."
    elif similarity >= 70:
        return "✅ Recommended due to similar genre and plot structure."
    elif similarity >= 55:
        return "🎯 Suggested because of overlapping keywords and movie style."
    else:
        return "📌 Recommended based on general viewing patterns."

#============== OTT MOVIE CARD ==========================
def ott_movie_card(movie, key_prefix):
    st.markdown(
        f"""
        <div class="movie-card">
            <img src="{movie['poster']}"/>
            <div class="trailer-btn">▶ Trailer</div>
            <div class="movie-title">{movie['title']}</div>
            <div class="movie-rating">⭐ {round(movie['rating'],1)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if movie.get("trailer"):
        with st.expander("▶ Watch Trailer"):
            st.video(f"https://www.youtube.com/watch?v={movie['trailer']}")

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

        recommended.append({
            "title": title,
            "poster": poster,
            "rating": rating,
            "overview": overview,
            "similarity": similarity_score,
            "reason": recommendation_reason(similarity_score),
            "trailer": trailer,
        })

    return recommended

# ================ SEARCH SECTION WITH MODAL ============ #
st.header("🔎 Search Movies")

query = st.text_input(
    "Search",
    placeholder="Type movie name...",
)
# ---------- SHOW SUGGESTIONS ----------
results = []    #initialize 
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
                   
    else:
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


genres = fetch_genres()
genre_map = {g["name"]: g["id"] for g in genres}

selected_genre = st.selectbox("Choose Genre", genre_map.keys())

genre_movies = fetch_movies_by_genre(genre_map[selected_genre])

# ---------- SLIDER ----------
genre_html = "<div class='slider-container'>"

for movie in genre_movies:
    poster = (
        movie["poster"]
        if movie["poster"]
        else "https://via.placeholder.com/300x450?text=No+Image"
    )

    genre_html += f"""
    <div class="movie-card">
        <img src="{poster}" width="150">
        <div class="movie-title">{movie['title']}</div>
    </div>
    """

genre_html += "</div>"
st.markdown(genre_html, unsafe_allow_html=True)

# ---------- TRAILER ----------
selected_genre_movie = st.selectbox(
    "🎬 Watch Genre Trailer",
    [m["title"] for m in genre_movies],
    key="genre_select"
)

for movie in genre_movies:
    if movie["title"] == selected_genre_movie and movie["trailer"]:
        with st.expander("▶ Play Trailer"):
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

# ---------- OTT SLIDER ----------
slider_html = "<div class='slider-container'>"

for movie in popular_movies:
    poster = (
        f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
        if movie.get("poster_path")
        else "https://via.placeholder.com/300x450?text=No+Image"
    )

    slider_html += f"""
    <div class="movie-card">
        <img src="{poster}" width="150">
        <div class="movie-title">{movie['title']}</div>
    </div>
    """

slider_html += "</div>"
st.markdown(slider_html, unsafe_allow_html=True)

# ---------- TRAILER USING EXPANDER ----------
st.subheader("🎬 Watch Trailer")

selected_movie = st.selectbox(
    "Select a popular movie",
    [movie["title"] for movie in popular_movies],
    key="popular_select"
)

for movie in popular_movies:
    if movie["title"] == selected_movie:
        trailer_key = fetch_trailer(movie["id"])

        if trailer_key:
            with st.expander("▶ Play Trailer"):
                st.video(f"https://www.youtube.com/watch?v={trailer_key}")
        else:
            st.info("Trailer not available")
#================= MOOD SECTION ============================               
st.header("🎭 Pick Your Mood")

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

    cols = st.columns(5)

    for idx, movie in enumerate(mood_movies):
        with cols[idx % 5]:

            if movie["poster"]:
                ott_movie_card(movie, "popular")

            ott_movie_card (f"**{movie['title']}**")
            st.caption(f"⭐ {movie['rating']}")

            if movie["trailer"]:
                with st.expander("▶ Watch Trailer"):
                    st.video(f"https://www.youtube.com/watch?v={movie['trailer']}")
