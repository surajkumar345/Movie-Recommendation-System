import streamlit as st
import pickle
import pandas as pd
import requests
import os
import gdown

file_id = "1CReMVOK7gdNfru5Dnyu4tsjiOYf493Ej"
url = f"https://drive.google.com/uc?id={file_id}"

if not os.path.exists("similarity.pkl"):
    gdown.download(url, "similarity.pkl", quiet=False)

st.set_page_config(page_title="Movie Recommender",layout="wide")

# API KEY from secrets
api_key = st.secrets["TMDB_API_KEY"]

# load data
movie_dict = pickle.load(open("movie_dict.pkl","rb"))
movies = pd.DataFrame(movie_dict)

similarity = pickle.load(open("similarity.pkl","rb"))

# --------------------------------------------------
# Fetch Movie Details
# --------------------------------------------------

def fetch_movie(movie_id):

    url=f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}"
    data=requests.get(url).json()

    poster="https://image.tmdb.org/t/p/w500"+str(data.get("poster_path"))

    return {
        "title":data.get("title"),
        "poster":poster,
        "rating":data.get("vote_average"),
        "overview":data.get("overview"),
        "movie_id":movie_id
    }

# --------------------------------------------------
# Fetch Trailer
# --------------------------------------------------

def fetch_trailer(movie_id):

    url=f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={api_key}"
    data=requests.get(url).json()

    for v in data["results"]:
        if v["type"]=="Trailer":
            return v["key"]

    return None

# --------------------------------------------------
# Movie Recommendation
# --------------------------------------------------

def recommend(movie):

    if movie not in movies["title"].values:
        return None

    index=movies[movies["title"]==movie].index[0]

    distances=similarity[index]

    movies_list=sorted(list(enumerate(distances)),
                       reverse=True,
                       key=lambda x:x[1])[1:11]

    recommended=[]

    for i in movies_list:

        movie_id=movies.iloc[i[0]].movie_id
        recommended.append(fetch_movie(movie_id))

    return recommended

# --------------------------------------------------
# Trending Movies
# --------------------------------------------------

def fetch_trending():

    url=f"https://api.themoviedb.org/3/trending/movie/week?api_key={api_key}"
    data=requests.get(url).json()

    movies_list=[]

    for m in data["results"][:10]:

        poster="https://image.tmdb.org/t/p/w500"+str(m["poster_path"])

        movies_list.append({
            "title":m["title"],
            "poster":poster,
            "rating":m["vote_average"],
            "movie_id":m["id"]
        })

    return movies_list

# --------------------------------------------------
# Popular Movies
# --------------------------------------------------

def fetch_popular():

    url=f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}"
    data=requests.get(url).json()

    movies_list=[]

    for m in data["results"][:10]:

        poster="https://image.tmdb.org/t/p/w500"+str(m["poster_path"])

        movies_list.append({
            "title":m["title"],
            "poster":poster,
            "rating":m["vote_average"],
            "movie_id":m["id"]
        })

    return movies_list

# --------------------------------------------------
# Mood Movies
# --------------------------------------------------

mood_dict={
    "Happy":[35,10751],
    "Romantic":[10749],
    "Thriller":[53],
    "Action":[28],
    "Sad":[18]
}

def fetch_mood_movies(mood):

    genres=mood_dict[mood]

    url=f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&with_genres={genres[0]}"
    data=requests.get(url).json()

    movies_list=[]

    for m in data["results"][:10]:

        poster="https://image.tmdb.org/t/p/w500"+str(m["poster_path"])

        movies_list.append({
            "title":m["title"],
            "poster":poster,
            "rating":m["vote_average"],
            "movie_id":m["id"]
        })

    return movies_list

# --------------------------------------------------
# Actor Movies
# --------------------------------------------------

def get_actor_id(actor):

    url=f"https://api.themoviedb.org/3/search/person?api_key={api_key}&query={actor}"
    data=requests.get(url).json()

    if data["results"]:
        return data["results"][0]["id"]

    return None

def fetch_actor_movies(actor_id):

    url=f"https://api.themoviedb.org/3/person/{actor_id}/movie_credits?api_key={api_key}"
    data=requests.get(url).json()

    movies=data.get("cast",[])

    movies=sorted(movies,
                  key=lambda x:x.get("vote_average",0),
                  reverse=True)

    movies_list=[]

    for m in movies[:10]:

        if m.get("poster_path"):

            poster="https://image.tmdb.org/t/p/w500"+m["poster_path"]

            movies_list.append({
                "title":m["title"],
                "poster":poster,
                "rating":m["vote_average"],
                "movie_id":m["id"]
            })

    return movies_list

# --------------------------------------------------
# Display Movie Row
# --------------------------------------------------

def show_movie_row(title,movies):

    st.subheader(title)

    cols=st.columns(5)

    for i,m in enumerate(movies):

        with cols[i%5]:

            st.image(m["poster"])

            st.caption(m["title"])

            st.write("⭐",m["rating"])

            trailer=fetch_trailer(m["movie_id"])

            if trailer:
                st.video(f"https://www.youtube.com/watch?v={trailer}")

# --------------------------------------------------
# Sidebar
# --------------------------------------------------

menu=st.sidebar.radio(
"Navigation",
[
"🏠 Home",
"🎯 Recommend",
"🔥 Trending",
"⭐ Popular",
"😊 Mood Movies",
"🎭 Actor Movies"
]
)

# --------------------------------------------------
# Home
# --------------------------------------------------

if menu=="🏠 Home":

    st.title("🎬 Netflix Style Movie Recommender")

    show_banner()

    show_movie_row("🔥 Trending",fetch_trending())

    show_movie_row("⭐ Popular",fetch_popular())

# --------------------------------------------------
# Recommendation
# --------------------------------------------------
elif menu == "🎯 Recommend":

    st.title("🎯 Movie Recommendation")

    # Empty input box
    movie_name = st.text_input("Enter movie name and press Enter")

    if movie_name:

        # Check movie in dataset
        matched_movies = movies[movies["title"].str.lower() == movie_name.lower()]

        if matched_movies.empty:

            st.error("Movie not found")

        else:

            movie_title = matched_movies.iloc[0]["title"]

            recs = recommend(movie_title)

            if recs:

                show_movie_row("Recommended Movies", recs)

            else:

                st.error("No recommendations found")

# --------------------------------------------------
# Trending
# --------------------------------------------------

elif menu=="🔥 Trending":

    st.title("Trending Movies")

    show_movie_row("Trending",fetch_trending())

# --------------------------------------------------
# Popular
# --------------------------------------------------

elif menu=="⭐ Popular":

    st.title("Popular Movies")

    show_movie_row("Popular",fetch_popular())

# --------------------------------------------------
# Mood
# --------------------------------------------------

elif menu=="😊 Mood Movies":

    st.title("Mood Based Movies")

    mood=st.selectbox("Select mood",list(mood_dict.keys()))

    if st.button("Get Movies"):

        show_movie_row("Movies for your mood",fetch_mood_movies(mood))

# --------------------------------------------------
# Actor
# --------------------------------------------------

elif menu=="🎭 Actor Movies":

    st.title("Actor Top Movies")

    actor=st.text_input("Enter actor name")

    if st.button("Search"):

        actor_id=get_actor_id(actor)

        if actor_id:

            show_movie_row("Top Movies",fetch_actor_movies(actor_id))

        else:

            st.error("Actor not found")





