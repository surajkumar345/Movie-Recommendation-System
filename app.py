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
            "trailer": trailer,
        })

    return recommended

# ================ SEARCH SECTION WITH MODAL ============ #

st.header("🔎 Search Movies")

search_query = st.text_input("Type movie name...")

def search_movies(query):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={query}"
    data = requests.get(url).json()

    movies = []

    for movie in data.get("results", [])[:10]:

        poster = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie["poster_path"] else None
        trailer = fetch_trailer(movie["id"])

        movies.append({
            "id": movie["id"],
            "title": movie["title"],
            "poster": poster,
            "rating": movie["vote_average"],
            "overview": movie["overview"],
            "trailer": trailer
        })

    return movies


if search_query:

    search_results = search_movies(search_query)

    if search_results:

        cols = st.columns(5)

        for idx, movie in enumerate(search_results):

            with cols[idx % 5]:

                if movie["poster"]:
                    st.image(movie["poster"])

                st.markdown(f"**{movie['title']}**")
                st.caption(f"⭐ {movie['rating']}")

               if movie["trailer"]:
                   with st.expander("▶ Watch Trailer"):
                       st.video(f"https://www.youtube.com/watch?v={movie['trailer']}")
                    
                   
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