import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import AddToWatchlist from "../components/AddToWatchlist.jsx";
import Poster from "../components/Poster.jsx";
import RatingBreakdown from "../components/RatingBreakdown.jsx";
import ReviewForm from "../components/ReviewForm.jsx";
import ReviewList from "../components/ReviewList.jsx";
import { fmtRuntime } from "../utils.js";

export default function MovieDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [movie, setMovie] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [error, setError] = useState("");

  // Reload both so the average and the list never disagree.
  const load = useCallback(async () => {
    const [m, r] = await Promise.all([api.movie(id), api.movieReviews(id)]);
    setMovie(m);
    setReviews(r);
  }, [id]);

  useEffect(() => {
    let alive = true;
    setMovie(null);
    setError("");
    load().catch((e) => alive && setError(e.message));
    return () => {
      alive = false;
    };
  }, [load]);

  if (error) {
    return (
      <div className="notice error" role="alert">
        <p>{error}</p>
        <Link to="/" className="btn btn-line">
          Back to films
        </Link>
      </div>
    );
  }
  if (!movie) return <p className="notice">Loading film…</p>;

  const myReview = user ? reviews.find((r) => r.user_id === user.user_id) : undefined;
  const posterMovie = { ...movie, language_name: movie.language.language_name };

  return (
    <article className="film-page">
      <div className="film-hero">
        <Poster movie={posterMovie} size="lg" />

        <div className="film-info">
          <h1>{movie.title}</h1>
          <p className="facts">
            {[movie.release_yr, movie.language.language_name, fmtRuntime(movie.duration)].filter(Boolean).join(", ")}
            {movie.age_rating && <span className="cert-inline">{movie.age_rating}</span>}
          </p>

          {movie.genres.length > 0 && (
            <p className="genres">{movie.genres.map((g) => g.genre_name).join(" / ")}</p>
          )}

          {movie.description && <p className="synopsis">{movie.description}</p>}

          <div className="where">
            <h2>Where to watch</h2>
            {movie.platforms.length > 0 ? (
              <ul className="platforms">
                {movie.platforms.map((p) => (
                  <li key={p.streaming_platform_id}>{p.streaming_platform_name}</li>
                ))}
              </ul>
            ) : (
              <p className="muted">Not listed on any platform yet.</p>
            )}
          </div>

          <AddToWatchlist movieId={movie.movie_id} />
        </div>
      </div>

      <section className="reviews" aria-labelledby="reviews-heading">
        <h2 id="reviews-heading">Reviews</h2>
        <div className="reviews-grid">
          <div className="reviews-side">
            <RatingBreakdown average={movie.average_rating} count={movie.review_count} reviews={reviews} />
            {/* key resets the fields whenever the user's own review changes */}
            <ReviewForm
              key={myReview ? `${myReview.review_id}-${myReview.reviewed_on}` : "new"}
              movie={movie}
              existing={myReview}
              onChanged={load}
            />
          </div>
          <ReviewList reviews={reviews} currentUserId={user?.user_id} />
        </div>
      </section>
    </article>
  );
}
