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

def fetch_trailer(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={api_key}"
    data = requests.get(url).json()

    for video in data.get("results", []):
        if video["type"] == "Trailer" and video["site"] == "YouTube":
            return video["key"]
    return None


def fetch_popular_movies():
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}"
    data = requests.get(url).json()

    movies_list = []

    for movie in data["results"][:20]:

        trailer = fetch_trailer(movie["id"])

        movies_list.append({
            "id": movie["id"],
            "title": movie["title"],
            "poster": "https://image.tmdb.org/t/p/w500/" + movie["poster_path"],
            "rating": movie["vote_average"],
            "trailer": trailer
        })

    return movies_list

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


def fetch_genres():
    url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={api_key}"
    data = requests.get(url).json()
    return {g["name"]: g["id"] for g in data["genres"]}

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

# ================= SIDEBAR =================
st.sidebar.title("🎭 Filter By Genre")
genres = fetch_genres()
selected_genre = st.sidebar.selectbox("Select Genre", ["None"] + list(genres.keys()))

# ================= SEARCH SECTION =================
st.title("🎬 Movie Recommendation System")

selected_movie = st.text_input("Search Movie")

if st.button("🎯 Recommend"):

    if selected_movie.strip() == "":
        st.warning("Please type a movie name.")
        st.stop()

    matched_movies = movies[movies["title"].str.lower().str.contains(selected_movie.lower())]

    if not matched_movies.empty:

        movie_name = matched_movies.iloc[0]["title"]
        recommended_movies = recommend(movie_name)

        st.subheader(f"Top Recommendations for {movie_name}")

        cols = st.columns(5)

        for idx, movie in enumerate(recommended_movies):

            with cols[idx % 5]:

                # 🎬 OTT CARD START
                st.markdown('<div class="movie-card">', unsafe_allow_html=True)

                st.image(movie["poster"])

                st.markdown(
                    f'<div class="movie-title">{movie["title"]}</div>',
                    unsafe_allow_html=True
                )

                st.caption(f"⭐ Rating: {movie['rating']}")
                st.progress(movie["similarity"] / 100)
                st.caption(f"{movie['similarity']}% Match")

                # 🎥 TRAILER BUTTON
                if movie["trailer"]:
                    if st.button("▶ Trailer", key=f"rec_trailer_{idx}"):
                        st.video(f"https://www.youtube.com/watch?v={movie['trailer']}")

                st.markdown('</div>', unsafe_allow_html=True)
                # 🎬 OTT CARD END

    else:
        st.warning("No matching movie found.")
        
# ================= GENRE SECTION =================
if selected_genre != "None":
    st.subheader(f"🎬 {selected_genre} Movies")

    genre_movies = fetch_movies_by_genre(genres[selected_genre])
    cols = st.columns(5)

for idx, movie in enumerate(genre_movies):
    with cols[idx % 5]:

        st.image(movie["poster"])
        st.markdown(f"**{movie['title']}**")
        st.caption(f"⭐ {movie['rating']}")

        if movie["trailer"]:
            if st.button("▶ Trailer", key=f"genre_trailer_{idx}"):
                st.video(f"https://www.youtube.com/watch?v={movie['trailer']}")

            

 # ================= POPULAR MOVIES =================
st.subheader("🔥 Popular Movies")
popular_movies = fetch_popular_movies()

cols = st.columns(5)

for idx, movie in enumerate(popular_movies):
    with cols[idx % 5]:

        st.image(movie["poster"])
        st.markdown(f"**{movie['title']}**")
        st.caption(f"⭐ {movie['rating']}")

        if movie["trailer"]:
            if st.button("▶ Trailer", key=f"pop_trailer_{idx}"):
                st.video(f"https://www.youtube.com/watch?v={movie['trailer']}")
