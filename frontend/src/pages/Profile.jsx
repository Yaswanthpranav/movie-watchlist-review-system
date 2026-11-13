import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import Shelves from "../components/Shelves.jsx";
import { fmtDate, STATUSES } from "../utils.js";

// The signed-in user's profile. The backend keeps watchlists private,
// so this shows the current user only (GET /auth/me + GET /watchlists).
export default function Profile() {
  const [me, setMe] = useState(null);
  const [lists, setLists] = useState(null);
  const [details, setDetails] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    Promise.all([api.me(), api.watchlists()])
      .then(async ([user, summaries]) => {
        if (!alive) return;
        setMe(user);
        setLists(summaries);
        // Each list's items give the posters and the status counts.
        const full = await Promise.all(
          summaries.map((l) => (l.item_count > 0 ? api.watchlist(l.watchlist_id) : { ...l, items: [] }))
        );
        if (alive) setDetails(full);
      })
      .catch((e) => alive && setError(e.message));
    return () => {
      alive = false;
    };
  }, []);

  if (error) {
    return (
      <p className="notice error" role="alert">
        {error}
      </p>
    );
  }
  if (!me || !lists) return <p className="notice">Loading your profile…</p>;

  const allItems = details.flatMap((d) => d.items);
  const distinctFilms = new Set(allItems.map((i) => i.movie_id)).size;
  const byStatus = Object.fromEntries(
    STATUSES.map((s) => [s.value, new Set(allItems.filter((i) => i.status === s.value).map((i) => i.movie_id)).size])
  );
  const previews = Object.fromEntries(details.map((d) => [d.watchlist_id, d.items.map((i) => i.movie)]));

  const stats = [
    { label: "Watchlists", value: lists.length },
    { label: "Films saved", value: distinctFilms },
    ...STATUSES.map((s) => ({ label: s.label, value: byStatus[s.value] })),
  ];

  return (
    <>
      <header className="profile-head">
        <span className="profile-avatar" aria-hidden="true">
          {me.username.slice(0, 1).toUpperCase()}
        </span>
        <div>
          <h1>{me.username}</h1>
          <p className="muted">
            {me.email}
            {me.create_date && `, member since ${fmtDate(me.create_date)}`}
          </p>
        </div>
      </header>

      <dl className="stat-strip">
        {stats.map((s) => (
          <div key={s.label}>
            <dd>{s.value}</dd>
            <dt>{s.label}</dt>
          </div>
        ))}
      </dl>

      <section aria-labelledby="profile-lists">
        <div className="section-head">
          <h2 id="profile-lists">Your watchlists</h2>
          <Link to="/watchlists" className="btn btn-line">
            New watchlist
          </Link>
        </div>
        {lists.length === 0 ? (
          <p className="notice">
            You haven't made a watchlist yet. <Link to="/watchlists">Make your first one</Link>.
          </p>
        ) : (
          <Shelves lists={lists} previews={previews} />
        )}
      </section>
    </>
  );
}
