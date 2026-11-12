// Read-only stars. Accepts decimals (averages) and fills them proportionally.
export function Stars({ value = 0 }) {
  const clamped = Math.max(0, Math.min(5, Number(value) || 0));
  return (
    <span className="stars" role="img" aria-label={`${clamped} out of 5 stars`}>
      <span className="stars-bg" aria-hidden="true">
        ★★★★★
      </span>
      <span className="stars-fg" aria-hidden="true" style={{ width: `${(clamped / 5) * 100}%` }}>
        ★★★★★
      </span>
    </span>
  );
}

const WORDS = ["", "Didn't like it", "It was okay", "Liked it", "Really liked it", "Loved it"];

// 1-5 picker for the review form, built on native radio inputs for keyboard support.
export function StarInput({ value, onChange }) {
  return (
    <fieldset className="star-input">
      <legend>Your rating</legend>
      <div className="star-row">
        {[1, 2, 3, 4, 5].map((n) => (
          <label key={n} className={n <= value ? "on" : ""}>
            <input
              type="radio"
              name="rating"
              value={n}
              checked={value === n}
              onChange={() => onChange(n)}
              className="visually-hidden"
            />
            <span aria-hidden="true">★</span>
            <span className="visually-hidden">{n} out of 5</span>
          </label>
        ))}
        <span className="star-word">{WORDS[value] || "Pick 1 to 5"}</span>
      </div>
    </fieldset>
  );
}
