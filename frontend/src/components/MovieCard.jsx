import { Link } from "react-router-dom";
import { fmtRating, fmtRuntime } from "../utils.js";
import Poster from "./Poster.jsx";

export default function MovieCard({ movie }) {
  const { movie_id, title, release_yr, duration, genres, average_rating, review_count } = movie;

  return (
    <Link to={`/movies/${movie_id}`} className="film">
      <Poster movie={movie} />
      <div className="film-caption">
        <div className="film-line">
          <h3 className="film-title">{title}</h3>
          {review_count > 0 && (
            <span className="film-score" aria-label={`Rated ${fmtRating(average_rating)} out of 5`}>
              <span className="star" aria-hidden="true">★</span>
              {fmtRating(average_rating)}
            </span>
          )}
        </div>
        <p className="film-meta">
          {[release_yr, fmtRuntime(duration), genres.map((g) => g.genre_name).join(" / ")].filter(Boolean).join(", ")}
        </p>
      </div>
    </Link>
  );
}
