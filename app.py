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

# ================= DOWNLOAD FILE =================
if not os.path.exists("similarity.pkl"):
    gdown.download(
        "https://drive.google.com/uc?id=1bVtmYxUBJdbm1Mj7mdBpwR71aXkJ80f4",
        "similarity.pkl",
        quiet=False
    )

# ================= API KEY =================
try:
    api_key = st.secrets["TMDB_API_KEY"]
except:
    st.error("TMDB API Key not found.")
    st.stop()

# ================= LOAD MODEL =================
movies = pickle.load(open("model.pkl","rb"))
similarity = pickle.load(open("similarity.pkl","rb"))

# ================= MOOD MAP =================
MOOD_MAP = {
    "😊 Happy":"35,10751",
    "😢 Sad":"18,10749",
    "🔥 Action":"28,12",
    "❤️ Romantic":"10749",
    "😱 Thriller":"53,27",
    "🧠 Mind Bending":"878,9648"
}

# ================= CSS =================
st.markdown("""
<style>
body{
background-color:#141414;
}

.section-title{
font-size:26px;
font-weight:700;
margin-top:20px;
}

img{
border-radius:10px;
transition:0.3s;
}

img:hover{
transform:scale(1.08);
}
</style>
""",unsafe_allow_html=True)

# ================= FUNCTIONS =================

def fetch_trailer(movie_id):
    url=f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={api_key}"
    data=requests.get(url).json()

    for v in data.get("results",[]):
        if v["type"]=="Trailer" and v["site"]=="YouTube":
            return v["key"]
    return None


def fetch_movie_details(movie_id):
    url=f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}"
    data=requests.get(url).json()

    poster=data.get("poster_path")
    poster=f"https://image.tmdb.org/t/p/w500{poster}" if poster else None

    return poster,data.get("vote_average"),data.get("overview")


def fetch_trending():
    url=f"https://api.themoviedb.org/3/trending/movie/week?api_key={api_key}"
    data=requests.get(url).json()

    movies_list=[]

    for m in data["results"][:10]:

        poster=f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m["poster_path"] else None
        trailer=fetch_trailer(m["id"])

        movies_list.append({
            "id":m["id"],
            "title":m["title"],
            "poster":poster,
            "rating":m["vote_average"],
            "trailer":trailer
        })

    return movies_list


def fetch_popular():
    url=f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}"
    data=requests.get(url).json()

    movies_list=[]

    for m in data["results"][:10]:

        poster=f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m["poster_path"] else None
        trailer=fetch_trailer(m["id"])

        movies_list.append({
            "id":m["id"],
            "title":m["title"],
            "poster":poster,
            "rating":m["vote_average"],
            "trailer":trailer
        })

    return movies_list


def fetch_movies_by_genre(genre_id):
    url=f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&with_genres={genre_id}"
    data=requests.get(url).json()

    movies_list=[]

    for m in data["results"][:10]:

        poster=f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m["poster_path"] else None
        trailer=fetch_trailer(m["id"])

        movies_list.append({
            "id":m["id"],
            "title":m["title"],
            "poster":poster,
            "rating":m["vote_average"],
            "trailer":trailer
        })

    return movies_list


def fetch_movies_by_mood(genre_id):

    url=f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&with_genres={genre_id}&sort_by=popularity.desc"

    data=requests.get(url).json()

    movies_list=[]

    for m in data["results"][:10]:

        poster=f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m["poster_path"] else None
        trailer=fetch_trailer(m["id"])

        movies_list.append({
            "id":m["id"],
            "title":m["title"],
            "poster":poster,
            "rating":m["vote_average"],
            "trailer":trailer
        })

    return movies_list


def recommend(movie):

    index=movies[movies["title"]==movie].index[0]

    distances=similarity[index]

    movie_list=sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x:x[1]
    )[1:11]

    rec=[]

    for i in movie_list:

        movie_id=movies.iloc[i[0]].movie_id
        title=movies.iloc[i[0]].title

        poster,rating,overview=fetch_movie_details(movie_id)
        trailer=fetch_trailer(movie_id)

        rec.append({
            "title":title,
            "poster":poster,
            "rating":rating,
            "overview":overview,
            "trailer":trailer
        })

    return rec


def show_movie_row(title,movies_list):

    st.subheader(title)

    cols=st.columns(5)

    for idx,m in enumerate(movies_list):

        with cols[idx%5]:

            if m["poster"]:
                st.image(m["poster"])

            st.markdown(f"**{m['title']}**")
            st.caption(f"⭐ {m['rating']}")

            if m["trailer"]:
                with st.expander("▶ Trailer"):
                    st.video(f"https://www.youtube.com/watch?v={m['trailer']}")

# ================= SIDEBAR =================

menu=st.sidebar.radio(
"Navigation",
["🏠 Home","🔎 Search","🔥 Trending","⭐ Popular","🎭 Genre","😊 Mood"]
)

# ================= HOME =================

if menu=="🏠 Home":

    st.title("🎬 Movie Recommendation System")

    trending=fetch_trending()
    show_movie_row("🔥 Trending Now",trending)

    popular=fetch_popular()
    show_movie_row("⭐ Popular Movies",popular)

# ================= TRENDING =================

elif menu=="🔥 Trending":

    trending=fetch_trending()
    show_movie_row("🔥 Trending Movies",trending)

# ================= POPULAR =================

elif menu=="⭐ Popular":

    popular=fetch_popular()
    show_movie_row("⭐ Popular Movies",popular)

# ================= GENRE =================

elif menu=="🎭 Genre":

    url=f"https://api.themoviedb.org/3/genre/movie/list?api_key={api_key}"
    genres=requests.get(url).json()["genres"]

    names=[g["name"] for g in genres]

    gname=st.selectbox("Select Genre",names)

    gid=None
    for g in genres:
        if g["name"]==gname:
            gid=g["id"]

    movies_list=fetch_movies_by_genre(gid)

    show_movie_row(f"🎭 {gname} Movies",movies_list)

# ================= MOOD =================

elif menu=="😊 Mood":

    mood=st.selectbox("How are you feeling?",list(MOOD_MAP.keys()))

    movies_list=fetch_movies_by_mood(MOOD_MAP[mood])

    show_movie_row(f"✨ Movies for {mood}",movies_list)

# ================= SEARCH =================

elif menu=="🔎 Search":

    st.header("Search Movies")

    query=st.text_input("Type movie name")

    if query:

        url=f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={query}"

        data=requests.get(url).json()

        results=data.get("results",[])[:8]

        titles=[m["title"] for m in results]

        if titles:

            selected=st.selectbox("Suggestions",titles)

            if st.button("Recommend"):

                recs=recommend(selected)

                show_movie_row("🎬 Recommended Movies",recs)
