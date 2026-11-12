import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api.js";
import ConfirmButton from "../components/ConfirmButton.jsx";
import Poster from "../components/Poster.jsx";
import StatusSelect from "../components/StatusSelect.jsx";
import { useToast } from "../toast.jsx";
import { fmtDate, fmtRuntime, plural, STATUSES } from "../utils.js";

const EMPTY = {
  PLANNED: "Nothing planned.",
  WATCHING: "Nothing in progress.",
  COMPLETED: "Nothing finished yet.",
};

export default function WatchlistDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [list, setList] = useState(null);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [pendingId, setPendingId] = useState(null);

  useEffect(() => {
    let alive = true;
    setList(null);
    setError("");
    api
      .watchlist(id)
      .then((res) => alive && setList(res))
      .catch((e) => alive && setError(e.message));
    return () => {
      alive = false;
    };
  }, [id]);

  async function changeStatus(item, status) {
    setActionError("");
    setPendingId(item.movie_id);
    try {
      const updated = await api.setItemStatus(list.watchlist_id, item.movie_id, status);
      setList((prev) => ({
        ...prev,
        items: prev.items.map((i) => (i.movie_id === item.movie_id ? { ...i, status: updated.status } : i)),
      }));
      toast(`${item.movie.title} moved to ${STATUSES.find((s) => s.value === updated.status).label}`);
    } catch (err) {
      setActionError(err.message);
    } finally {
      setPendingId(null);
    }
  }

  async function removeItem(item) {
    setActionError("");
    setPendingId(item.movie_id);
    try {
      await api.removeFromWatchlist(list.watchlist_id, item.movie_id);
      setList((prev) => ({ ...prev, items: prev.items.filter((i) => i.movie_id !== item.movie_id) }));
      toast(`Removed ${item.movie.title}`);
    } catch (err) {
      setActionError(err.message);
    } finally {
      setPendingId(null);
    }
  }

  async function deleteList() {
    try {
      await api.deleteWatchlist(list.watchlist_id);
      toast(`Deleted ${list.watchlist_name}`);
      navigate("/watchlists");
    } catch (err) {
      setActionError(err.message);
    }
  }

  if (error) {
    return (
      <div className="notice error" role="alert">
        <p>{error}</p>
        <Link to="/watchlists" className="btn btn-line">
          Back to watchlists
        </Link>
      </div>
    );
  }
  if (!list) return <p className="notice">Loading watchlist…</p>;

  return (
    <>
      <header className="page-head list-head">
        <div>
          <Link to="/watchlists" className="crumb">
            Watchlists
          </Link>
          <h1>{list.watchlist_name}</h1>
          <p className="muted">
            {plural(list.items.length, "film")}, started {fmtDate(list.create_date)}
          </p>
          {list.notes && <p className="list-notes">{list.notes}</p>}
        </div>
        <ConfirmButton confirmLabel="Click again to delete this list" onConfirm={deleteList}>
          Delete watchlist
        </ConfirmButton>
      </header>

      {actionError && (
        <p className="error" role="alert">
          {actionError}
        </p>
      )}

      {list.items.length === 0 ? (
        <p className="notice">
          This list is empty. <Link to="/">Find a film</Link> and save it here.
        </p>
      ) : (
        <div className="board">
          {STATUSES.map((s) => {
            const items = list.items.filter((i) => i.status === s.value);
            return (
              <section key={s.value} className="column" aria-labelledby={`col-${s.value}`}>
                <h2 id={`col-${s.value}`}>
                  {s.label} <span className="muted">{items.length}</span>
                </h2>
                {items.length === 0 ? (
                  <p className="column-empty">{EMPTY[s.value]}</p>
                ) : (
                  <ul>
                    {items.map((item) => (
                      <li key={item.watchlist_item_id} className="slip">
                        <Poster movie={item.movie} size="xs" />
                        <div className="slip-body">
                          <Link to={`/movies/${item.movie_id}`} className="slip-title">
                            {item.movie.title}
                          </Link>
                          <span className="muted">
                            {[item.movie.release_yr, item.movie.language_name, fmtRuntime(item.movie.duration)]
                              .filter(Boolean)
                              .join(", ")}
                          </span>
                          <div className="slip-actions">
                            <StatusSelect
                              label={`Move ${item.movie.title}`}
                              value={item.status}
                              disabled={pendingId === item.movie_id}
                              onChange={(st) => changeStatus(item, st)}
                            />
                            <button
                              type="button"
                              className="btn btn-text"
                              disabled={pendingId === item.movie_id}
                              onClick={() => removeItem(item)}
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            );
          })}
        </div>
      )}
    </>
  );
}
