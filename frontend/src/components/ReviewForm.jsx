import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { useToast } from "../toast.jsx";
import ConfirmButton from "./ConfirmButton.jsx";
import { StarInput } from "./Stars.jsx";

// Creates a review, or edits/deletes the signed-in user's existing one
// (the backend allows one review per user per movie).
export default function ReviewForm({ movie, existing, onChanged }) {
  const { user } = useAuth();
  const toast = useToast();
  const location = useLocation();
  const [rating, setRating] = useState(existing ? Math.round(existing.rating) : 0);
  const [text, setText] = useState(existing?.review_text ?? "");
  const [platformId, setPlatformId] = useState(existing?.platform_id ? String(existing.platform_id) : "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  if (!user) {
    return (
      <p className="review-form muted">
        <Link to="/login" state={{ from: location.pathname }}>
          Log in
        </Link>{" "}
        to rate and review this film.
      </p>
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (rating < 1) {
      setError("Pick a rating from 1 to 5 stars.");
      return;
    }
    const body = {
      rating,
      review_text: text.trim() || null,
      platform_id: platformId ? Number(platformId) : null,
    };
    setBusy(true);
    try {
      if (existing) await api.updateReview(existing.review_id, body);
      else await api.createReview(movie.movie_id, body);
      toast(existing ? "Review updated" : "Review posted");
      await onChanged();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    setError("");
    setBusy(true);
    try {
      await api.deleteReview(existing.review_id);
      toast("Review deleted");
      await onChanged();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <form className="review-form" onSubmit={handleSubmit}>
      <h3>{existing ? "Edit your review" : "Write a review"}</h3>
      <StarInput value={rating} onChange={setRating} />
      <label className="field">
        <span>What did you think? (optional)</span>
        <textarea rows={4} maxLength={5000} value={text} onChange={(e) => setText(e.target.value)} />
      </label>
      {movie.platforms.length > 0 && (
        <label className="field">
          <span>Watched on (optional)</span>
          <select className="select" value={platformId} onChange={(e) => setPlatformId(e.target.value)}>
            <option value="">Not saying</option>
            {movie.platforms.map((p) => (
              <option key={p.streaming_platform_id} value={p.streaming_platform_id}>
                {p.streaming_platform_name}
              </option>
            ))}
          </select>
        </label>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="actions">
        <button className="btn btn-ink" disabled={busy}>
          {busy ? "Saving…" : existing ? "Save changes" : "Post review"}
        </button>
        {existing && (
          <ConfirmButton confirmLabel="Click again to delete" onConfirm={handleDelete} disabled={busy}>
            Delete review
          </ConfirmButton>
        )}
      </div>
    </form>
  );
}
