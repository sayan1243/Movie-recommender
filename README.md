# Movie Recommender System

A content-based movie recommender with a FastAPI backend and a responsive web
interface. It compares each movie's overview, genres, keywords, cast, and
director to find five similar films.

## Run on Windows

1. Install Python 3.10 or newer (Python 3.12 is recommended).
2. Open PowerShell in this folder and create/activate a virtual environment:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run the commands below using
   `.venv\Scripts\python.exe` instead of `python`.

3. Install dependencies and build the local model:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   python build_model.py
   ```

   The model builder downloads the TMDB 5000 movie metadata and credits into
   `data\`, then creates the recommendation model in `model\`. These generated
   files are local and are excluded from version control.

4. Start the FastAPI server:

   ```powershell
   python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
   ```

   Open http://127.0.0.1:8000 in your browser. Interactive API documentation
   is available at http://127.0.0.1:8000/docs.

The API provides movie search at `/api/movies?q=...`, recommendations at
`/api/movies/{movie_id}/recommendations`, and service status at `/api/health`.
The web interface is served by FastAPI from the `web\` folder.

## Deploy to Render

The included `render.yaml` defines a free Render web service. In Render:

1. Sign in at https://dashboard.render.com/ and connect your GitHub account.
2. Select **New > Blueprint** and choose the `sayan1243/Movie-recommender`
   repository.
3. Review the service configuration and click **Apply**. Render builds the
   recommendation model from the dataset during deployment, then starts the
   FastAPI server.
4. Open the `onrender.com` URL shown on the service page after the deploy
   finishes.

The free instance may take a little time to wake after inactivity. The model
and dataset are recreated on each deployment; they are intentionally not
committed to Git.

The original notebook is a Kaggle notebook and expects Kaggle's
`/kaggle/input/` directory. It is not required to run the local app.
