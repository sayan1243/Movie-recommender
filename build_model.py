import ast
import pickle
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
MODEL_DIR = PROJECT_DIR / "model"
MOVIES_CSV = DATA_DIR / "tmdb_5000_movies.csv"
CREDITS_ZIP = DATA_DIR / "tmdb_5000_credits.csv.zip"
MODEL_PATH = MODEL_DIR / "recommender.pkl"

DATA_BASE_URL = (
    "https://raw.githubusercontent.com/"
    "Hamza-Tahirr/Movie-Recommender-System-With-Streamlit/"
    "1ae18812c142157abb2c5fea7d94960163752dd0/"
)


def download_file(url, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Movie-Recommender-setup/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            destination.write_bytes(response.read())
    except (OSError, urllib.error.URLError) as error:
        raise RuntimeError(
            f"Could not download {destination.name} from {url}. "
            "Check your internet connection or download the TMDB 5000 dataset "
            "files manually into the data folder."
        ) from error


def ensure_dataset():
    if not MOVIES_CSV.is_file():
        print("Downloading movie metadata...")
        download_file(DATA_BASE_URL + "tmdb_5000_movies.csv", MOVIES_CSV)
    if not CREDITS_ZIP.is_file():
        print("Downloading movie credits...")
        download_file(DATA_BASE_URL + "tmdb_5000_credits.csv.zip", CREDITS_ZIP)

    if not zipfile.is_zipfile(CREDITS_ZIP):
        raise RuntimeError(
            f"{CREDITS_ZIP} is not a valid ZIP archive. Delete it and rerun this script."
        )


def parse_items(value):
    if not isinstance(value, str):
        return []
    try:
        items = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return []
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def names(value, limit=None):
    result = [item.get("name", "") for item in parse_items(value)]
    result = [name.replace(" ", "") for name in result if isinstance(name, str)]
    return result if limit is None else result[:limit]


def director_names(value):
    return [
        item.get("name", "").replace(" ", "")
        for item in parse_items(value)
        if item.get("job") == "Director" and isinstance(item.get("name"), str)
    ]


def build_model():
    ensure_dataset()
    movies = pd.read_csv(MOVIES_CSV)
    with zipfile.ZipFile(CREDITS_ZIP) as archive:
        credit_files = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(credit_files) != 1:
            raise RuntimeError("Expected exactly one credits CSV inside the downloaded ZIP.")
        with archive.open(credit_files[0]) as credits_file:
            credits = pd.read_csv(credits_file)

    required_movie_columns = {"id", "title", "overview", "genres", "keywords"}
    required_credit_columns = {"movie_id", "title", "cast", "crew"}
    if not required_movie_columns.issubset(movies.columns):
        raise RuntimeError("The movie metadata CSV is missing required columns.")
    if not required_credit_columns.issubset(credits.columns):
        raise RuntimeError("The credits CSV is missing required columns.")

    merged = movies.merge(credits, on="title", how="inner")
    merged = merged.dropna(subset=["overview", "title"])
    merged = merged.drop_duplicates(subset=["title"]).reset_index(drop=True)
    tags = []
    for row in merged.itertuples(index=False):
        overview = row.overview.split()
        genre_names = names(row.genres)
        keyword_names = names(row.keywords)
        cast_names = names(row.cast, limit=3)
        crew_names = director_names(row.crew)
        tags.append(
            " ".join(overview + genre_names + keyword_names + cast_names + crew_names)
        )

    movie_list = merged[["movie_id", "title"]].copy()
    vectorizer = CountVectorizer(max_features=5000, stop_words="english")
    vectors = vectorizer.fit_transform(tags)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with MODEL_PATH.open("wb") as model_file:
        pickle.dump({"movies": movie_list, "vectors": vectors}, model_file)
    print(f"Built model for {len(movie_list):,} movies at {MODEL_PATH}")


if __name__ == "__main__":
    build_model()
