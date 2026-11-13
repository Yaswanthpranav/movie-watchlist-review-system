import { Link } from "react-router-dom";
import { fmtDate, plural } from "../utils.js";
import Poster from "./Poster.jsx";

// One row per watchlist: a strip of its first posters, then name, size and notes.
// `previews` maps watchlist_id to that list's movies (fetched by the page).
export default function Shelves({ lists, previews }) {
  return (
    <ul className="shelves">
      {lists.map((l) => {
        const films = previews[l.watchlist_id] ?? [];
        return (
          <li key={l.watchlist_id}>
            <Link to={`/watchlists/${l.watchlist_id}`} className="shelf">
              <div className="shelf-posters" aria-hidden="true">
                {films.slice(0, 5).map((m) => (
                  <Poster key={m.movie_id} movie={m} size="xs" />
                ))}
                {films.length === 0 && <span className="poster-slot">Empty</span>}
              </div>
              <div className="shelf-text">
                <h2>{l.watchlist_name}</h2>
                <p className="muted">
                  {plural(l.item_count, "film")}, started {fmtDate(l.create_date)}
                </p>
                {l.notes && <p className="shelf-notes">{l.notes}</p>}
              </div>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
