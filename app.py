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
import streamlit as st
import pickle
import pandas as pd
import requests

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
def fetch_poster(movie_id):
    api_key = "3d815c36541b7f27658d61cc3c3dd6c2"   # 👈 Yahan apni API key daalo
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    data = requests.get(url)
    data = data.json()
    poster_path = data.get('poster_path')

    if poster_path:
        return "https://image.tmdb.org/t/p/w500/" + poster_path
    else:
        return "https://via.placeholder.com/300x450?text=No+Image"

# ------------------ RECOMMEND FUNCTION ------------------
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

# ------------------ TITLE ------------------
st.markdown("<h1 style='text-align: center;'>🎬 Movie Recommendation System</h1>", unsafe_allow_html=True)

st.write("")

# ------------------ SIDEBAR ------------------
st.sidebar.title("About")
st.sidebar.info("This Movie Recommendation System uses Content-Based Filtering with Cosine Similarity.")

# ------------------ SELECT BOX ------------------
selected_movie = st.selectbox(
    "Select a movie",
    movies['title'].values
)

# ------------------ RECOMMEND BUTTON ------------------
if st.button("Recommend"):
    with st.spinner("Finding best movies for you... 🎬"):
        names, posters = recommend(selected_movie)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.image(posters[0])
        st.caption(names[0])

    with col2:
        st.image(posters[1])
        st.caption(names[1])

    with col3:
        st.image(posters[2])
        st.caption(names[2])

    with col4:
        st.image(posters[3])
        st.caption(names[3])

    with col5:
        st.image(posters[4])
        st.caption(names[4])
