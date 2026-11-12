// The schema has no image column, so every film gets a printed typographic poster.
// Everything is derived from the movie id, so a film looks the same on every page.

const INKS = [
  { bg: "#f2a007", fg: "#1f1c3b" }, // saffron / indigo
  { bg: "#d8432c", fg: "#fbebd3" }, // vermilion / cream
  { bg: "#0f6e6e", fg: "#f7c4b8" }, // teal / blush
  { bg: "#2b2a6b", fg: "#f5c542" }, // indigo / mustard
  { bg: "#2f7d3b", fg: "#f3f0d7" }, // leaf / ivory
  { bg: "#e86a92", fg: "#3b0f1e" }, // rani pink / maroon
  { bg: "#2945c9", fg: "#f4e9d8" }, // ultramarine / paper
  { bg: "#5b2a5e", fg: "#ffb98a" }, // plum / peach
];

const MOTIFS = ["sun", "bands", "split", "rings"];

export function inkFor(id) {
  return INKS[(id * 5) % INKS.length];
}

// Size the title so its longest word fills the poster width (container query units).
function titleSize(title) {
  const words = title.toUpperCase().split(/\s+/);
  const longest = Math.max(...words.map((w) => w.length));
  const byWidth = 150 / Math.max(longest, 3);
  const byLines = words.length > 3 ? 22 : 36;
  return Math.min(byWidth, byLines);
}

export default function Poster({ movie, size = "md" }) {
  const { movie_id, title, release_yr, age_rating, language_name } = movie;
  const ink = inkFor(movie_id);
  // Offset the motif every full cycle of inks so two films never share both colour and motif
  // until 32 films apart.
  const motif = MOTIFS[(movie_id * 3 + 1 + Math.floor(movie_id / INKS.length)) % MOTIFS.length];

  return (
    <div
      className={`poster poster-${size} motif-${motif}`}
      style={{ "--p-bg": ink.bg, "--p-fg": ink.fg }}
      aria-hidden="true"
    >
      <div className="poster-motif" />
      {/* Padding lives on this inner box: a container can't size its own padding in cqw. */}
      <div className="poster-inner">
        {size !== "xs" && (
          <div className="poster-top">
            <span>{language_name}</span>
            {age_rating && <span className="cert">{age_rating}</span>}
          </div>
        )}
        <div className="poster-title" style={{ fontSize: `${titleSize(title)}cqw` }}>
          {title}
        </div>
        {size !== "xs" && release_yr && <div className="poster-year">{release_yr}</div>}
      </div>
    </div>
  );
}
