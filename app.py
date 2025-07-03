import streamlit as st
import pickle
import pandas as pd
import requests
import random
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --------------------------
# API Keys
# --------------------------
TMDB_API_KEY = "0e5ecf7bbd38a940928dc50b335a9a91"
YOUTUBE_API_KEY = "AIzaSyCb0k0V6tY1D4zP9nAh_fw1L73ncyfNDZ4"

# --------------------------
# Fetch poster, overview, rating
# --------------------------
def fetch_movie_data(movie_id):
    response = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    )
    data = response.json()
    poster_url = (
        "https://image.tmdb.org/t/p/w500/" + data["poster_path"]
        if data.get("poster_path")
        else "https://via.placeholder.com/500x750.png?text=No+Image"
    )
    overview = data.get("overview", "No description available.")
    rating = data.get("vote_average", "N/A")
    return poster_url, overview, rating

# --------------------------
# Fetch trailer URL
# --------------------------
def fetch_trailer_url(movie_title):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        q=f"{movie_title} trailer",
        part="snippet",
        maxResults=1,
        type="video"
    )
    response = request.execute()
    if response["items"]:
        video_id = response["items"][0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={video_id}"
    else:
        return None

# --------------------------
# Recommend function
# --------------------------
def recommend(movie, genre_filter=None):
    movie_index = movies[movies["title"] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:30]

    recommended_titles = []
    recommended_posters = []
    recommended_overviews = []
    recommended_ratings = []
    recommended_trailers = []

    for i in movies_list:
        movie_data = movies.iloc[i[0]]
        if genre_filter and genre_filter != "All":
            if genre_filter not in movie_data["genre_list"]:
                continue

        movie_id = movie_data.id
        poster, overview, rating = fetch_movie_data(movie_id)

        # Safely try to fetch trailer
        try:
            trailer_url = fetch_trailer_url(movie_data.title)
        except HttpError:
            trailer_url = None
        except Exception:
            trailer_url = None

        recommended_titles.append(movie_data.title)
        recommended_posters.append(poster)
        recommended_overviews.append(overview)
        recommended_ratings.append(rating)
        recommended_trailers.append(trailer_url)

        if len(recommended_titles) == 10:
            break

    return (
        recommended_titles,
        recommended_posters,
        recommended_overviews,
        recommended_ratings,
        recommended_trailers,
    )

# --------------------------
# Load data
# --------------------------
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

# --------------------------
# Extract genres
# --------------------------
def extract_genres_from_tags(tags):
    genre_keywords = [
        "Action", "Adventure", "Comedy", "Crime", "Drama", "Fantasy",
        "History", "Horror", "Mystery", "Romance", "Science Fiction",
        "Thriller", "Western", "Animation", "Family", "War"
    ]
    tag_words = set(tags.lower().split())
    return [g for g in genre_keywords if g.lower() in tag_words]

movies["genre_list"] = movies["tags"].apply(extract_genres_from_tags)
all_genres = sorted(set(genre for sub in movies["genre_list"] for genre in sub))

# --------------------------
# Streamlit UI
# --------------------------
st.title('🎬 Movie Buddy')
st.caption('- Movie recommender system - By Vivek ')

selected_movie = st.selectbox(
    "Choose a movie you like:",
    movies['title'].values
)

selected_genre = st.selectbox(
    "Filter by Genre:",
    ["All"] + all_genres
)

# Session state
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = {}

# Buttons
col1, col2, col3 = st.columns([1,1,1])

with col1:
    if st.button('🎯 Recommend'):
        rec = recommend(selected_movie, genre_filter=selected_genre)
        st.session_state.recommendations = {
            'titles': rec[0],
            'posters': rec[1],
            'overviews': rec[2],
            'ratings': rec[3],
            'trailers': rec[4],
        }

with col2:
    if st.button(' 🎲 Surprise Me!'):
        if selected_genre == "All":
            filtered = movies
        else:
            filtered = movies[movies["genre_list"].apply(lambda x: selected_genre in x)]
        rand_movie = random.choice(filtered['title'].values)
        st.success(f"✨ Surprise! Recommending movies like: {rand_movie}")
        rec = recommend(rand_movie, genre_filter=selected_genre)
        st.session_state.recommendations = {
            'titles': rec[0],
            'posters': rec[1],
            'overviews': rec[2],
            'ratings': rec[3],
            'trailers': rec[4],
        }

with col3:
    if st.button('🔄 Reset'):
        st.session_state.recommendations = {}
        st.rerun()

# Display recommendations

if rec and rec['titles']:
    for row_start in range(0, len(rec['titles']), 3):
        cols = st.columns(3)
        for i in range(3):
            idx = row_start + i
            if idx < len(rec['titles']):
                with cols[i]:
                    st.image(rec['posters'][idx])
                    st.markdown(f"**{rec['titles'][idx]}**")
                    st.caption(f"⭐ Rating: {rec['ratings'][idx]}")
                    st.write(rec['overviews'][idx])
                    if rec['trailers'][idx]:
                        st.markdown(
                            f"[▶️ Watch Trailer]({rec['trailers'][idx]})"
                        )
                    else:
                        st.caption("🎞️ Trailer unavailable.")

                        






    

    



