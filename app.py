import streamlit as st
import pickle
import pandas as pd
import requests

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# ================= API SECURITY =================
try:
    api_key = st.secrets["TMDB_API_KEY"]
except:
    st.error("TMDB API Key not found. Check secrets.toml")
    st.stop()

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

        recommended.append({
            "title": title,
            "poster": poster,
            "rating": rating,
            "overview": overview,
            "similarity": similarity_score
        })

    return recommended


def fetch_popular_movies():
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}"
    data = requests.get(url).json()

    movies_list = []

    for movie in data["results"][:20]:
        movies_list.append({
            "title": movie["title"],
            "poster": "https://image.tmdb.org/t/p/w500/" + movie["poster_path"],
            "rating": movie["vote_average"]
        })

    return movies_list


def fetch_genres():
    url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={api_key}"
    data = requests.get(url).json()
    return {g["name"]: g["id"] for g in data["genres"]}


def fetch_movies_by_genre(genre_id):
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&with_genres={genre_id}"
    data = requests.get(url).json()

    movies_list = []

    for movie in data["results"][:15]:
        movies_list.append({
            "title": movie["title"],
            "poster": "https://image.tmdb.org/t/p/w500/" + movie["poster_path"],
            "rating": movie["vote_average"]
        })

    return movies_list


# ================= SIDEBAR =================
st.sidebar.title("🎭 Filter By Genre")
genres = fetch_genres()
selected_genre = st.sidebar.selectbox("Select Genre", ["None"] + list(genres.keys()))

# ================= SEARCH SECTION =================
st.title("🎬 Movie Recommendation System")

selected_movie = st.text_input(
    "Search Movie",
    placeholder="Type movie name exactly..."
)

if st.button("🎯 Recommend"):
    if selected_movie in movies["title"].values:

        recommended_movies = recommend(selected_movie)

        st.subheader("Top 10 Recommendations")

        cols = st.columns(5)

        for idx, movie in enumerate(recommended_movies):
            with cols[idx % 5]:
                st.image(movie["poster"])
                st.markdown(f"**{movie['title']}**")
                st.caption(f"⭐ Rating: {movie['rating']}")
                st.progress(movie["similarity"] / 100)
                st.caption(f"{movie['similarity']}% Match")
                st.write(movie["overview"][:120] + "...")

    else:
        st.warning("Movie not found in dataset.")

# ================= POPULAR MOVIES =================
st.subheader("🔥 Popular Movies")

popular_movies = fetch_popular_movies()
cols = st.columns(5)

for idx, movie in enumerate(popular_movies):
    with cols[idx % 5]:
        st.image(movie["poster"])
        st.markdown(f"**{movie['title']}**")
        st.caption(f"⭐ {movie['rating']}")

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