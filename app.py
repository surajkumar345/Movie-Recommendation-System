import streamlit as st
import pickle
import pandas as pd
import requests
import os
import gdown

st.set_page_config(page_title="Movie Recommender", layout="wide")

# ---- Download similarity file if not present ----
file_id = "1bVtmYxUBJdbm1Mj7mdBpwR71aXkJ80f4"
url = f"https://drive.google.com/uc?id={file_id}"

if not os.path.exists("similarity.pkl"):
    gdown.download(url, "similarity.pkl", quiet=False)

# ---- Load files ----
movies = pickle.load(open('model.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

def fetch_poster(movie_id):
    api_key = "3d815c36541b7f27658d61cc3c3dd6c2"
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    data = requests.get(url).json()
    poster_path = data['poster_path']
    return "https://image.tmdb.org/t/p/w500/" + poster_path

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)),
                         reverse=True,
                         key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_posters = []

    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_posters.append(fetch_poster(movie_id))

    return recommended_movies, recommended_posters


st.markdown("<h1 style='text-align: center;'>🎬 Movie Recommendation System</h1>", unsafe_allow_html=True)

selected_movie_name = st.selectbox(
    "Select a movie",
    movies['title'].values)

if st.button('Recommend'):
    names, posters = recommend(selected_movie_name)

    st.write("## 🎥 Recommended Movies")

    cols = st.columns(5)

    for col, name, poster in zip(cols, names, posters):
        with col:
            st.image(poster)
            st.markdown(f"<p style='text-align: center;'>{name}</p>", unsafe_allow_html=True)
