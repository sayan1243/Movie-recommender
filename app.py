import pickle
from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sklearn.metrics.pairwise import cosine_similarity


PROJECT_DIR = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_DIR / "model" / "recommender.pkl"
WEB_DIR = PROJECT_DIR / "web"


class MovieResponse(BaseModel):
    id: int
    title: str


class RecommendationResponse(MovieResponse):
    similarity: float = Field(ge=0, le=1)


class RecommendationsResponse(BaseModel):
    selected_movie: MovieResponse
    recommendations: list[RecommendationResponse]


class MovieRecommender:
    def __init__(self, movies: pd.DataFrame, vectors):
        required_columns = {"movie_id", "title"}
        if not required_columns.issubset(movies.columns):
            raise RuntimeError("The recommendation model is missing movie IDs or titles.")
        if len(movies) != vectors.shape[0]:
            raise RuntimeError("Movie metadata and recommendation vectors do not align.")

        self.movies = movies.reset_index(drop=True)
        if self.movies["movie_id"].duplicated().any():
            raise RuntimeError("The recommendation model contains duplicate movie IDs.")
        self.vectors = vectors
        self.id_to_index = {
            int(movie_id): index
            for index, movie_id in enumerate(self.movies["movie_id"])
        }
        self.normalized_titles = self.movies["title"].astype(str).str.casefold()

    def search(self, query: str, limit: int) -> list[MovieResponse]:
        normalized_query = query.strip().casefold()
        matches = self.normalized_titles.str.contains(
            normalized_query, regex=False, na=False
        )
        indices = self.movies.index[matches].tolist()
        indices.sort(
            key=lambda index: (
                0 if self.normalized_titles.iloc[index] == normalized_query else 1,
                0 if self.normalized_titles.iloc[index].startswith(normalized_query) else 1,
                self.normalized_titles.iloc[index],
            )
        )
        return [
            MovieResponse(
                id=int(self.movies.iloc[index]["movie_id"]),
                title=str(self.movies.iloc[index]["title"]),
            )
            for index in indices[:limit]
        ]

    def recommend(self, movie_id: int, limit: int) -> RecommendationsResponse:
        movie_index = self.id_to_index.get(movie_id)
        if movie_index is None:
            raise HTTPException(status_code=404, detail="Movie not found.")

        scores = cosine_similarity(
            self.vectors[movie_index], self.vectors
        ).ravel()
        ranked_indices = sorted(
            (index for index in range(len(scores)) if index != movie_index),
            key=lambda index: (-float(scores[index]), index),
        )[:limit]

        selected = self.movies.iloc[movie_index]
        return RecommendationsResponse(
            selected_movie=MovieResponse(
                id=int(selected["movie_id"]), title=str(selected["title"])
            ),
            recommendations=[
                RecommendationResponse(
                    id=int(self.movies.iloc[index]["movie_id"]),
                    title=str(self.movies.iloc[index]["title"]),
                    similarity=max(0.0, min(1.0, float(scores[index]))),
                )
                for index in ranked_indices
            ],
        )


@asynccontextmanager
async def lifespan(application: FastAPI):
    if not MODEL_PATH.is_file():
        raise RuntimeError(
            f"Recommendation model not found at {MODEL_PATH}. "
            "Run `python build_model.py` before starting the server."
        )

    with MODEL_PATH.open("rb") as model_file:
        model = pickle.load(model_file)
    application.state.recommender = MovieRecommender(
        movies=model["movies"], vectors=model["vectors"]
    )
    yield


app = FastAPI(
    title="Movie Recommender",
    description="Search movies and discover similar titles.",
    version="1.0.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/health")
def health(request: Request):
    recommender: MovieRecommender = request.app.state.recommender
    return {"status": "ok", "movie_count": len(recommender.movies)}


@app.get("/api/movies", response_model=list[MovieResponse])
def search_movies(
    request: Request,
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=8, ge=1, le=20),
):
    recommender: MovieRecommender = request.app.state.recommender
    return recommender.search(q, limit)


@app.get(
    "/api/movies/{movie_id}/recommendations",
    response_model=RecommendationsResponse,
)
def get_recommendations(
    movie_id: int,
    request: Request,
    limit: int = Query(default=5, ge=1, le=10),
):
    recommender: MovieRecommender = request.app.state.recommender
    return recommender.recommend(movie_id, limit)
