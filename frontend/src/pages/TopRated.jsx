import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import Poster from "../components/Poster.jsx";
import { fmtRating, fmtRuntime, plural } from "../utils.js";

export default function TopRated() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    api
      .topRated({ limit: 10, min_reviews: 1 })
      .then((res) => alive && setItems(res))
      .catch((e) => alive && setError(e.message));
    return () => {
      alive = false;
    };
  }, []);

  return (
    <>
      <header className="page-head">
        <h1>Top rated</h1>
        <p className="muted">The ten best-reviewed films. Ties are broken by number of reviews.</p>
      </header>

      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      {!error && items === null && <p className="notice">Loading the rankings…</p>}
      {items && items.length === 0 && <p className="notice">No film has a review yet, so there is nothing to rank.</p>}

      {items && items.length > 0 && (
        <ol className="chart">
          {items.map((m) => (
            <li key={m.movie_id}>
              <span className="chart-rank">{m.rank}</span>
              <Link to={`/movies/${m.movie_id}`} className="chart-film">
                <Poster movie={m} size="xs" />
                <span className="chart-text">
                  <span className="chart-title">{m.title}</span>
                  <span className="muted">
                    {[m.release_yr, m.language_name, fmtRuntime(m.duration)].filter(Boolean).join(", ")}
                  </span>
                </span>
              </Link>
              <span className="chart-score">
                <span className="chart-number">{fmtRating(m.average_rating)}</span>
                <span className="muted">{plural(m.review_count, "review")}</span>
              </span>
            </li>
          ))}
        </ol>
      )}
    </>
  );
}
