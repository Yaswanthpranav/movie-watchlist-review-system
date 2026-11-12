import { fmtDate } from "../utils.js";
import { Stars } from "./Stars.jsx";

export default function ReviewList({ reviews, currentUserId }) {
  if (reviews.length === 0) {
    return <p className="muted">Nobody has reviewed this film yet.</p>;
  }
  return (
    <ol className="review-list">
      {reviews.map((r) => (
        <li key={r.review_id} className={r.user_id === currentUserId ? "review mine" : "review"}>
          <div className="review-by">
            <span className="avatar" aria-hidden="true">
              {r.username.slice(0, 1).toUpperCase()}
            </span>
            <strong>{r.user_id === currentUserId ? `${r.username} (you)` : r.username}</strong>
            <Stars value={r.rating} />
          </div>
          {r.review_text && <p className="review-text">{r.review_text}</p>}
          <p className="review-when">
            {fmtDate(r.reviewed_on)}
            {r.platform_name && `, watched on ${r.platform_name}`}
          </p>
        </li>
      ))}
    </ol>
  );
}
