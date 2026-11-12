# CineTrack frontend

React + Vite single-page app for the CineTrack FastAPI backend in `../backend`. Plain CSS, no UI library. The Archivo font is bundled through npm, so it works offline.

## Run it

1. Start the backend (see `backend/.env.example` for the Supabase settings it needs):
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload        # http://localhost:8000
   ```
2. Start the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev                          # http://localhost:5173
   ```

The backend only allows CORS from `http://localhost:5173` and `http://127.0.0.1:5173`, so the dev server port is fixed.
To point at a backend somewhere else, copy `.env.example` to `.env` and change `VITE_API_URL`.

## Pages

| Route | Page | Needs login |
|---|---|---|
| `/` | Browse: search, language, genre, platform, minimum rating, year, sort, pagination (filters live in the URL) | No |
| `/movies/:id` | Details, streaming platforms, rating summary, reviews, review form, add to watchlist | Only to review or save |
| `/top-rated` | Ranking from `GET /movies/top-rated` | No |
| `/login`, `/register` | Account forms (register logs you in) | No |
| `/watchlists` | Your watchlists; create one empty or with starting films (`POST /watchlists/with-items`, a single transaction) | Yes |
| `/watchlists/:id` | Movies in a list, change status, remove, filter by status | Yes |

## How it is organised

- `src/api.js`: every backend call, the JWT header, and error-message handling. Change an endpoint here only.
- `src/auth.jsx`: login state. The token is stored in `localStorage` and restored with `GET /auth/me`. A 401 on any signed-in request logs the user out.
- `src/pages/`: one file per route. `src/components/`: shared pieces (`MovieCard`, `ReviewForm`, `AddToWatchlist`, `Stars`, ...).

## Backend behaviour the UI relies on

- One review per user per movie: the review form switches to edit/delete mode if you already reviewed it.
- Watchlist statuses are `PLANNED`, `WATCHING`, `COMPLETED`.
- The same movie can't be added twice to one list, and watchlist names are unique per user. The backend's 409 message is shown as-is.
- The schema has no poster or image column, so `Poster.jsx` prints a typographic poster for each film. Its colours and motif come from the movie id, so a film looks the same on every page.
