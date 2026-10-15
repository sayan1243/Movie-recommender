const searchForm = document.querySelector("#search-form");
const searchInput = document.querySelector("#movie-query");
const suggestions = document.querySelector("#movie-suggestions");
const searchHint = document.querySelector("#search-hint");
const recommendButton = document.querySelector("#recommend-button");
const libraryCount = document.querySelector("#library-count");
const resultsSection = document.querySelector("#results");
const resultsTitle = document.querySelector("#results-title span");
const recommendationList = document.querySelector("#recommendation-list");
const errorMessage = document.querySelector("#error-message");
const changeMovieButton = document.querySelector("#change-movie");

let selectedMovie = null;
let searchTimer = null;
let searchController = null;

function setHint(message) {
  searchHint.textContent = message;
}

function hideSuggestions() {
  suggestions.replaceChildren();
  suggestions.hidden = true;
  searchInput.setAttribute("aria-expanded", "false");
}

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
}

function clearError() {
  errorMessage.textContent = "";
  errorMessage.hidden = true;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail || "Something went wrong. Please try again.");
  }
  return response.json();
}

function chooseMovie(movie) {
  selectedMovie = movie;
  searchInput.value = movie.title;
  recommendButton.disabled = false;
  setHint("Selected. Ready to find films with a similar feel.");
  hideSuggestions();
  clearError();
}

function renderSuggestions(movies) {
  suggestions.replaceChildren();

  if (!movies.length) {
    const empty = document.createElement("div");
    empty.className = "suggestion-empty";
    empty.textContent = "No matching titles. Try another search.";
    suggestions.append(empty);
  } else {
    movies.forEach((movie, index) => {
      const option = document.createElement("button");
      option.className = "suggestion-option";
      option.type = "button";
      option.role = "option";
      option.setAttribute("aria-selected", "false");

      const number = document.createElement("span");
      number.className = "suggestion-number";
      number.textContent = String(index + 1).padStart(2, "0");

      const title = document.createElement("span");
      title.className = "suggestion-title";
      title.textContent = movie.title;

      option.append(number, title);
      option.addEventListener("click", () => chooseMovie(movie));
      suggestions.append(option);
    });
  }

  suggestions.hidden = false;
  searchInput.setAttribute("aria-expanded", "true");
}

async function searchMovies(query) {
  if (searchController) {
    searchController.abort();
  }
  searchController = new AbortController();
  setHint("Searching the film library…");

  try {
    const movies = await fetchJson(
      `/api/movies?q=${encodeURIComponent(query)}&limit=8`,
      { signal: searchController.signal },
    );
    renderSuggestions(movies);
    setHint(
      movies.length
        ? `${movies.length} ${movies.length === 1 ? "title" : "titles"} found. Choose one to continue.`
        : "No titles found. Try a different spelling.",
    );
  } catch (error) {
    if (error.name !== "AbortError") {
      hideSuggestions();
      setHint("Movie search is temporarily unavailable.");
      showError(error.message);
    }
  }
}

function renderRecommendations(data) {
  resultsTitle.textContent = data.selected_movie.title;
  recommendationList.replaceChildren();

  data.recommendations.forEach((movie, index) => {
    const card = document.createElement("article");
    card.className = "recommendation-card";
    card.style.animationDelay = `${index * 55}ms`;

    const number = document.createElement("span");
    number.className = "recommendation-number";
    number.textContent = String(index + 1).padStart(2, "0");

    const title = document.createElement("h3");
    title.className = "recommendation-title";
    title.textContent = movie.title;

    const track = document.createElement("div");
    track.className = "match-track";
    track.setAttribute("role", "meter");
    track.setAttribute("aria-label", "Content similarity");
    track.setAttribute("aria-valuemin", "0");
    track.setAttribute("aria-valuemax", "100");
    const fill = document.createElement("span");
    const percentage = Math.max(0, Math.min(100, Math.round(movie.similarity * 100)));
    fill.style.width = `${percentage}%`;
    track.setAttribute("aria-valuenow", String(percentage));
    track.append(fill);

    const match = document.createElement("span");
    match.className = "match-label";
    match.textContent = `${percentage}% match`;

    card.append(number, title, track, match);
    recommendationList.append(card);
  });

  resultsSection.hidden = false;
  resultsSection.setAttribute("aria-busy", "false");
  resultsSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

searchInput.addEventListener("input", () => {
  const query = searchInput.value.trim();
  selectedMovie = null;
  recommendButton.disabled = true;
  resultsSection.hidden = true;
  clearError();
  hideSuggestions();
  window.clearTimeout(searchTimer);

  if (searchController) {
    searchController.abort();
  }

  if (query.length < 2) {
    hideSuggestions();
    setHint("Type at least 2 characters to search the film library.");
    return;
  }

  searchTimer = window.setTimeout(() => searchMovies(query), 220);
});

searchInput.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    hideSuggestions();
  }
  if (event.key === "ArrowDown" && !suggestions.hidden) {
    event.preventDefault();
    suggestions.querySelector("button")?.focus();
  }
});

suggestions.addEventListener("keydown", (event) => {
  const options = [...suggestions.querySelectorAll("button")];
  const current = options.indexOf(document.activeElement);
  if (event.key === "ArrowDown") {
    event.preventDefault();
    options[Math.min(current + 1, options.length - 1)]?.focus();
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    if (current <= 0) {
      searchInput.focus();
    } else {
      options[current - 1]?.focus();
    }
  } else if (event.key === "Escape") {
    hideSuggestions();
    searchInput.focus();
  }
});

document.addEventListener("click", (event) => {
  if (!event.target.closest(".search-field-wrap")) {
    hideSuggestions();
  }
});

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  if (!selectedMovie) {
    setHint("Choose a title from the search suggestions first.");
    searchInput.focus();
    return;
  }

  hideSuggestions();
  recommendButton.disabled = true;
  recommendButton.querySelector("span").textContent = "Finding your films…";
  resultsSection.hidden = false;
  resultsSection.setAttribute("aria-busy", "true");
  recommendationList.replaceChildren();
  const loading = document.createElement("p");
  loading.className = "suggestion-empty";
  loading.textContent = "Looking for stories with a similar feel…";
  recommendationList.append(loading);

  try {
    const data = await fetchJson(
      `/api/movies/${selectedMovie.id}/recommendations?limit=5`,
    );
    renderRecommendations(data);
  } catch (error) {
    resultsSection.hidden = true;
    showError(error.message);
  } finally {
    recommendButton.disabled = false;
    recommendButton.querySelector("span").textContent = "Find similar films";
  }
});

changeMovieButton.addEventListener("click", () => {
  resultsSection.hidden = true;
  selectedMovie = null;
  recommendButton.disabled = true;
  setHint("Search for a title and choose it from the suggestions.");
  searchInput.focus();
  searchInput.select();
});

async function loadLibraryStatus() {
  try {
    const health = await fetchJson("/api/health");
    libraryCount.replaceChildren();
    const dot = document.createElement("span");
    dot.className = "count-dot";
    const label = document.createElement("span");
    label.textContent = `${health.movie_count.toLocaleString()} FILMS IN THE LIBRARY`;
    libraryCount.append(dot, label);
    setHint(`Start typing to search ${health.movie_count.toLocaleString()} films.`);
  } catch {
    libraryCount.textContent = "FILM LIBRARY OFFLINE";
    libraryCount.style.color = "#a44c37";
    setHint("The movie library could not be reached.");
    showError("The recommendation service is unavailable. Please refresh or try again shortly.");
  }
}

loadLibraryStatus();
