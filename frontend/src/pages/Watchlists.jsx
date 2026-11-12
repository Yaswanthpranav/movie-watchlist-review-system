import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import Poster from "../components/Poster.jsx";
import { useToast } from "../toast.jsx";
import { fmtDate, plural } from "../utils.js";

export default function Watchlists() {
  const toast = useToast();
  const [lists, setLists] = useState(null);
  const [previews, setPreviews] = useState({});
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const [formError, setFormError] = useState("");
  const [busy, setBusy] = useState(false);
  const [picked, setPicked] = useState([]);
  const [pickQuery, setPickQuery] = useState("");
  const [pickResults, setPickResults] = useState([]);

  // Film finder for "start with films".
  useEffect(() => {
    const term = pickQuery.trim();
    if (!term) {
      setPickResults([]);
      return undefined;
    }
    let alive = true;
    const t = setTimeout(() => {
      api
        .movies({ search: term, page_size: 6 })
        .then((res) => alive && setPickResults(res.items))
        .catch(() => alive && setPickResults([]));
    }, 250);
    return () => {
      alive = false;
      clearTimeout(t);
    };
  }, [pickQuery]);

  function togglePick(movie) {
    setPicked((prev) =>
      prev.some((m) => m.movie_id === movie.movie_id)
        ? prev.filter((m) => m.movie_id !== movie.movie_id)
        : prev.length >= 50
        ? prev
        : [...prev, movie]
    );
  }

  useEffect(() => {
    let alive = true;
    api
      .watchlists()
      .then(async (res) => {
        if (!alive) return;
        setLists(res);
        // The summary endpoint has no items, so fetch each list once to show its posters.
        const details = await Promise.all(
          res.filter((l) => l.item_count > 0).map((l) => api.watchlist(l.watchlist_id).catch(() => null))
        );
        if (!alive) return;
        const map = {};
        details.filter(Boolean).forEach((d) => {
          map[d.watchlist_id] = d.items.map((i) => i.movie);
        });
        setPreviews(map);
      })
      .catch((e) => alive && setError(e.message));
    return () => {
      alive = false;
    };
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    setFormError("");
    if (!name.trim()) {
      setFormError("Give the watchlist a name.");
      return;
    }
    setBusy(true);
    try {
      const body = { watchlist_name: name.trim(), notes: notes.trim() || null };
      let created;
      if (picked.length > 0) {
        // Atomic: if any film fails (e.g. a duplicate), the backend rolls the whole list back.
        const detail = await api.createWatchlistWithItems({
          ...body,
          items: picked.map((m) => ({ movie_id: m.movie_id, status: "PLANNED" })),
        });
        created = { ...detail, item_count: detail.items.length };
        setPreviews((prev) => ({ ...prev, [detail.watchlist_id]: detail.items.map((i) => i.movie) }));
      } else {
        created = await api.createWatchlist(body);
      }
      setLists((prev) => [created, ...(prev ?? [])]);
      setName("");
      setNotes("");
      setPicked([]);
      setPickQuery("");
      toast(
        picked.length ? `Created ${created.watchlist_name} with ${plural(picked.length, "film")}` : `Created ${created.watchlist_name}`
      );
    } catch (err) {
      setFormError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <header className="page-head">
        <h1>Watchlists</h1>
      </header>

      <div className="lists-layout">
        <section aria-label="Your watchlists">
          {error && (
            <p className="notice error" role="alert">
              {error}
            </p>
          )}
          {!error && lists === null && <p className="notice">Loading your watchlists…</p>}
          {lists && lists.length === 0 && (
            <p className="notice">No watchlists yet. Name your first one to start saving films.</p>
          )}
          {lists && lists.length > 0 && (
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
          )}
        </section>

        <form className="new-list" onSubmit={handleCreate}>
          <h2>New watchlist</h2>
          <label className="field">
            <span>Name</span>
            <input
              className="input"
              maxLength={150}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Weekend picks"
            />
          </label>
          <label className="field">
            <span>Notes (optional)</span>
            <textarea rows={3} maxLength={2000} value={notes} onChange={(e) => setNotes(e.target.value)} />
          </label>

          <div className="field">
            <label htmlFor="pick-search">Start with films (optional)</label>
            <input
              id="pick-search"
              className="input"
              type="search"
              placeholder="Find a film to add"
              value={pickQuery}
              onChange={(e) => setPickQuery(e.target.value)}
            />
            {pickResults.length > 0 && (
              <ul className="pick-results">
                {pickResults.map((m) => {
                  const on = picked.some((p) => p.movie_id === m.movie_id);
                  return (
                    <li key={m.movie_id}>
                      <button type="button" className={on ? "pick on" : "pick"} aria-pressed={on} onClick={() => togglePick(m)}>
                        <span>{m.title}</span>
                        <span className="muted">{on ? "Added" : m.release_yr}</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
            {picked.length > 0 && (
              <ul className="picked" aria-label="Films to start with">
                {picked.map((m) => (
                  <li key={m.movie_id}>
                    {m.title}
                    <button type="button" aria-label={`Remove ${m.title}`} onClick={() => togglePick(m)}>
                      ×
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          {formError && (
            <p className="error" role="alert">
              {formError}
            </p>
          )}
          <button className="btn btn-ink" disabled={busy}>
            {busy ? "Creating…" : picked.length ? `Create with ${plural(picked.length, "film")}` : "Create watchlist"}
          </button>
        </form>
      </div>
    </>
  );
}
