import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { useToast } from "../toast.jsx";
import StatusSelect from "./StatusSelect.jsx";

export default function AddToWatchlist({ movieId }) {
  const { user } = useAuth();
  const toast = useToast();
  const location = useLocation();
  const [lists, setLists] = useState(null);
  const [listId, setListId] = useState("");
  const [status, setStatus] = useState("PLANNED");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return undefined;
    let alive = true;
    api
      .watchlists()
      .then((data) => {
        if (!alive) return;
        setLists(data);
        if (data.length) setListId(String(data[0].watchlist_id));
      })
      .catch((e) => alive && setError(e.message));
    return () => {
      alive = false;
    };
  }, [user]);

  if (!user) {
    return (
      <p className="save-box muted">
        <Link to="/login" state={{ from: location.pathname }}>
          Log in
        </Link>{" "}
        to save this film to a watchlist.
      </p>
    );
  }

  async function handleAdd(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.addToWatchlist(Number(listId), movieId, status);
      const name = lists.find((l) => String(l.watchlist_id) === listId)?.watchlist_name;
      toast(`Saved to ${name}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (lists && lists.length === 0) {
    return (
      <p className="save-box muted">
        You have no watchlists yet. <Link to="/watchlists">Make one</Link> to start saving films.
      </p>
    );
  }

  return (
    <form className="save-box" onSubmit={handleAdd}>
      <div className="save-row">
        <label className="inline-field">
          <span>Save to</span>
          <select
            className="select"
            value={listId}
            disabled={!lists}
            onChange={(e) => setListId(e.target.value)}
          >
            {(lists ?? []).map((l) => (
              <option key={l.watchlist_id} value={l.watchlist_id}>
                {l.watchlist_name}
              </option>
            ))}
          </select>
        </label>
        <label className="inline-field">
          <span>as</span>
          <StatusSelect value={status} onChange={setStatus} />
        </label>
        <button className="btn btn-ink" disabled={busy || !lists}>
          {busy ? "Saving…" : "Save"}
        </button>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
