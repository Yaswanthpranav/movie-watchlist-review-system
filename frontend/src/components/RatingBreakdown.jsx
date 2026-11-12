import { fmtRating, plural } from "../utils.js";
import { Stars } from "./Stars.jsx";

// Average comes from the backend (SQL AVG); the 5-to-1 distribution is counted from the review list.
export default function RatingBreakdown({ average, count, reviews }) {
  const buckets = [5, 4, 3, 2, 1].map((n) => ({
    n,
    count: reviews.filter((r) => Math.round(r.rating) === n).length,
  }));
  const max = Math.max(1, ...buckets.map((b) => b.count));

  return (
    <div className="breakdown">
      <div className="breakdown-score">
        <span className="big-number">{fmtRating(average)}</span>
        <div>
          <Stars value={average ?? 0} />
          <p>{count ? plural(count, "review") : "No reviews yet"}</p>
        </div>
      </div>
      <dl className="bars">
        {buckets.map((b) => (
          <div key={b.n} className="bar-row">
            <dt>{b.n}★</dt>
            <dd>
              <span className="bar">
                <span style={{ width: `${(b.count / max) * 100}%` }} />
              </span>
              <span className="bar-count">{b.count}</span>
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
