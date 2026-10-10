import pickle
from pathlib import Path

import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity


PROJECT_DIR = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_DIR / "model" / "recommender.pkl"


@st.cache_resource
def load_model():
    with MODEL_PATH.open("rb") as model_file:
        return pickle.load(model_file)


def recommend(movie_title, movies, vectors):
    movie_index = movies.index[movies["title"] == movie_title][0]
    scores = cosine_similarity(vectors[movie_index], vectors).ravel()
    ranked_indices = scores.argsort()[::-1]
    return movies.iloc[ranked_indices[1:6]]


st.title("Movie Recommender System")

if not MODEL_PATH.is_file():
    st.error(
        "The recommendation model has not been built yet. "
        "Run `python build_model.py` from the project folder, then reload this page."
    )
    st.stop()

model = load_model()
movies = model["movies"]
vectors = model["vectors"]

selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movies["title"].tolist(),
)

if st.button("Show Recommendation"):
    st.session_state["recommended_movie"] = selected_movie

if "recommended_movie" in st.session_state:
    recommendations = recommend(st.session_state["recommended_movie"], movies, vectors)
    columns = st.columns(len(recommendations))

    for column, (_, movie) in zip(columns, recommendations.iterrows()):
        with column:
            st.text(movie["title"])
