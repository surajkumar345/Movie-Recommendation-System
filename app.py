import streamlit as st
import pickle
import pandas as pd
import requests
import os
import gdown

file_id = "1bVtmYxUBJdbm1Mj7mdBpwR71aXkJ80f4"
url = f"https://drive.google.com/uc?id={file_id}"

if not os.path.exists("similarity.pkl"):
    gdown.download(url, "similarity.pkl", quiet=False)

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# ------------------ LOAD DATA ------------------
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)

similarity = pickle.load(open('similarity.pkl', 'rb'))

# ------------------ FETCH POSTER FUNCTION ------------------
        def fetch_movie_details(movie_id):
    api_key = "3d815c36541b7f27658d61cc3c3dd6c2"
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    
    data = requests.get(url).json()

    poster_path = data.get('poster_path')
    rating = data.get('vote_average')
    genres = [genre['name'] for genre in data.get('genres', [])]

    poster_url = (
        "https://image.tmdb.org/t/p/w500/" + poster_path
        if poster_path
        else "https://via.placeholder.com/300x450?text=No+Image"
    )

    return poster_url, rating, ", ".join(genres)

# ------------------ RECOMMEND FUNCTION ------------------
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]

    movies_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:11]   # 🔥 10 movies

    recommended_movies = []

    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        title = movies.iloc[i[0]].title
        poster, rating, genres = fetch_movie_details(movie_id)

        recommended_movies.append({
            "title": title,
            "poster": poster,
            "rating": rating,
            "genres": genres
        })

    return recommended_movies

# ------------------ CUSTOM CSS ------------------
st.markdown("""
<style>

body {
    background-color: #0E1117;
}

.main-title {
    text-align: center;
    font-size: 48px;
    font-weight: bold;
    background: -webkit-linear-gradient(45deg, #ff4b2b, #ff416c);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 30px;
}

.movie-card {
    background-color: #1e1e1e;
    padding: 12px;
    border-radius: 15px;
    text-align: center;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.movie-card:hover {
    transform: scale(1.07);
    box-shadow: 0px 0px 15px rgba(255, 65, 108, 0.6);
}

.movie-title {
    font-weight: bold;
    margin-top: 8px;
}

.movie-rating {
    color: gold;
    font-size: 14px;
}

.movie-genre {
    font-size: 12px;
    color: #bbb;
}

</style>
""", unsafe_allow_html=True)

# ------------------ GRADIENT TITLE ------------------
st.markdown("<div class='main-title'>🎬 Movie Recommendation System</div>", unsafe_allow_html=True)

st.write("")

# ------------------ SIDEBAR ------------------
st.sidebar.title("About")
st.sidebar.info("This Movie Recommendation System uses Content-Based Filtering with Cosine Similarity.")

# ------------------ SEARCH BAR ------------------
st.markdown("### 🔎 Search Movie")

search_query = st.text_input(
    "",
    placeholder="Type movie name here...",
    key="search_input"
)

selected_movie = None

if search_query:
    filtered_movies = movies[
        movies['title'].str.contains(search_query, case=False, na=False)
    ]

    if not filtered_movies.empty:
        selected_movie = st.selectbox(
            "Select from results",
            filtered_movies['title'].values,
            key="filtered_movie_select"
        )
    else:
        st.warning("No movie found 😢")

st.write("")
#----------------- BUTTOM FNCTION ------------------
if selected_movie and st.button("✨ Show Recommendations", key="recommend_button"):
    with st.spinner("Finding best movies for you... 🎬"):

        recommended_movies = recommend(selected_movie)

        st.markdown("## 🎥 Recommended For You")

        cols = st.columns(5)

        for idx, movie in enumerate(recommended_movies):
            col = cols[idx % 5]

            with col:
                st.markdown(
                    f"""
                    <div class="movie-card">
                        <img src="{movie['poster']}" width="100%">
                        <div class="movie-title">{movie['title']}</div>
                        <div class="movie-rating">⭐ {movie['rating']}</div>
                        <div class="movie-genre">{movie['genres']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
