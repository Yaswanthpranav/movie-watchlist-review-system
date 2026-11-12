// Every call to the FastAPI backend lives in this file.
// Endpoints and field names mirror backend/app/routers/* and backend/app/schemas.py.

const BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
const TOKEN_KEY = "cinetrack_token";

export const getToken = () => {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
};

export const setToken = (token) => {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable: the session just won't survive a reload */
  }
};

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

let onUnauthorized = null;
export const setUnauthorizedHandler = (fn) => {
  onUnauthorized = fn;
};

// FastAPI returns { detail: "text" } for HTTPException and
// { detail: [{ loc, msg }] } for request validation (422) errors.
function messageFrom(body, status) {
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e) => {
        const field = Array.isArray(e.loc) ? e.loc.slice(1).join(".") : "";
        return field ? `${field}: ${e.msg}` : e.msg;
      })
      .join(" ");
  }
  return `Request failed (${status}).`;
}

async function request(path, { method = "GET", body, params, auth = true } = {}) {
  const url = new URL(BASE + path);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
    });
  }

  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const token = auth ? getToken() : null;
  if (token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, `Can't reach the server at ${BASE}. Check that the backend is running.`);
  }

  if (res.status === 204) return null;

  let data = null;
  try {
    data = await res.json();
  } catch {
    /* non-JSON error body */
  }

  if (!res.ok) {
    if (res.status === 401 && token && onUnauthorized) onUnauthorized();
    throw new ApiError(res.status, messageFrom(data, res.status));
  }
  return data;
}

export const api = {
  // Auth
  login: (identifier, password) =>
    request("/auth/login", {
      method: "POST",
      auth: false,
      body: identifier.includes("@") ? { email: identifier, password } : { username: identifier, password },
    }),
  register: ({ username, email, password }) =>
    request("/auth/register", { method: "POST", auth: false, body: { username, email, password } }),
  me: () => request("/auth/me"),

  // Lookups
  genres: () => request("/genres"),
  languages: () => request("/languages"),
  platforms: () => request("/platforms"),

  // Movies
  movies: (params) => request("/movies", { params }),
  topRated: (params) => request("/movies/top-rated", { params }),
  movie: (id) => request(`/movies/${id}`),
  movieReviews: (id) => request(`/movies/${id}/reviews`),
  createReview: (movieId, body) => request(`/movies/${movieId}/reviews`, { method: "POST", body }),

  // Reviews
  updateReview: (reviewId, body) => request(`/reviews/${reviewId}`, { method: "PUT", body }),
  deleteReview: (reviewId) => request(`/reviews/${reviewId}`, { method: "DELETE" }),

  // Watchlists
  watchlists: () => request("/watchlists"),
  watchlist: (id) => request(`/watchlists/${id}`),
  createWatchlist: (body) => request("/watchlists", { method: "POST", body }),
  // One transaction on the backend: the list and all its films are saved together, or nothing is.
  createWatchlistWithItems: (body) => request("/watchlists/with-items", { method: "POST", body }),
  deleteWatchlist: (id) => request(`/watchlists/${id}`, { method: "DELETE" }),
  addToWatchlist: (watchlistId, movieId, status = "PLANNED") =>
    request(`/watchlists/${watchlistId}/items`, { method: "POST", body: { movie_id: movieId, status } }),
  setItemStatus: (watchlistId, movieId, status) =>
    request(`/watchlists/${watchlistId}/items/${movieId}`, { method: "PATCH", body: { status } }),
  removeFromWatchlist: (watchlistId, movieId) =>
    request(`/watchlists/${watchlistId}/items/${movieId}`, { method: "DELETE" }),
};
