# Movie Recommender System

A content-based movie recommender built with Streamlit and the TMDB 5000 movie
dataset. It compares each movie's overview, genres, keywords, cast, and director
to find five similar movies.

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

4. Start the app:

   ```powershell
   python -m streamlit run app.py --server.address 127.0.0.1
   ```

   Streamlit prints a local URL (normally http://localhost:8501); open it in
   your browser.

The original notebook is a Kaggle notebook and expects Kaggle's
`/kaggle/input/` directory. It is not required to run the local app.
