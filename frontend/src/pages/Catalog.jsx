import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api.js";
import MovieCard from "../components/MovieCard.jsx";
import Pagination from "../components/Pagination.jsx";
import { plural, SORTS } from "../utils.js";

const PAGE_SIZE = 12;

export default function Catalog() {
  const [params, setParams] = useSearchParams();
  const q = params.get("q") || "";
  const genre = params.get("genre") || "";
  const language = params.get("language") || "";
  const platform = params.get("platform") || "";
  const year = params.get("year") || "";
  const minRating = params.get("min_rating") || "";
  const sort = params.get("sort") || "title_asc";
  const page = Number(params.get("page")) || 1;

  const [search, setSearch] = useState(q);
  const [yearInput, setYearInput] = useState(year);
  const [lookups, setLookups] = useState({ genres: [], languages: [], platforms: [] });
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  function update(changes) {
    const next = new URLSearchParams(params);
    Object.entries(changes).forEach(([key, value]) => {
      if (value === "" || value === null || value === undefined) next.delete(key);
      else next.set(key, value);
    });
    setParams(next);
  }

  // Keep the search box in sync when filters are cleared, and debounce typing.
  useEffect(() => setSearch(q), [q]);
  useEffect(() => {
    if (search === q) return undefined;
    const t = setTimeout(() => update({ q: search.trim(), page: "" }), 350);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  // Year: only send a complete 4-digit year (the backend accepts 1888 to 2100).
  useEffect(() => setYearInput(year), [year]);
  useEffect(() => {
    if (yearInput === year) return undefined;
    if (yearInput !== "" && !/^\d{4}$/.test(yearInput)) return undefined;
    const t = setTimeout(() => update({ year: yearInput, page: "" }), 350);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [yearInput]);

  useEffect(() => {
    Promise.all([api.genres(), api.languages(), api.platforms()])
      .then(([genres, languages, platforms]) => setLookups({ genres, languages, platforms }))
      .catch(() => {
        /* filters stay empty; the movie request below reports the real error */
      });
  }, []);

  const queryKey = params.toString();
  useEffect(() => {
    let alive = true;
    setError("");
    api
      .movies({
        search: q,
        genre_id: genre,
        language_id: language,
        platform_id: platform,
        year,
        min_rating: minRating,
        sort,
        page,
        page_size: PAGE_SIZE,
      })
      .then((res) => alive && setData(res))
      .catch((e) => alive && setError(e.message));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queryKey, reloadKey]);

  const filtered = q || genre || language || platform || year || minRating;

  return (
    <>
      <section className="finder" aria-label="Find a film">
        <label className="finder-search">
          <span className="visually-hidden">Search films by title or description</span>
          <input
            type="search"
            placeholder="Search films"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>

        <div className="finder-row">
          <div className="segmented" role="radiogroup" aria-label="Language">
            {[{ language_id: "", language_name: "All" }, ...lookups.languages].map((l) => (
              <label key={l.language_id || "all"} className={String(l.language_id) === language ? "on" : ""}>
                <input
                  type="radio"
                  name="language"
                  className="visually-hidden"
                  checked={String(l.language_id) === language}
                  onChange={() => update({ language: l.language_id, page: "" })}
                />
                {l.language_name}
              </label>
            ))}
          </div>

          <div className="finder-selects">
            <label className="inline-field">
              <span>Genre</span>
              <select className="select" value={genre} onChange={(e) => update({ genre: e.target.value, page: "" })}>
                <option value="">Any</option>
                {lookups.genres.map((g) => (
                  <option key={g.genre_id} value={g.genre_id}>
                    {g.genre_name}
                  </option>
                ))}
              </select>
            </label>
            <label className="inline-field">
              <span>On</span>
              <select
                className="select"
                value={platform}
                onChange={(e) => update({ platform: e.target.value, page: "" })}
              >
                <option value="">Any platform</option>
                {lookups.platforms.map((p) => (
                  <option key={p.streaming_platform_id} value={p.streaming_platform_id}>
                    {p.streaming_platform_name}
                  </option>
                ))}
              </select>
            </label>
            <label className="inline-field">
              <span>Rated</span>
              <select
                className="select"
                value={minRating}
                onChange={(e) => update({ min_rating: e.target.value, page: "" })}
              >
                <option value="">Any rating</option>
                <option value="4">4★ and up</option>
                <option value="3">3★ and up</option>
                <option value="2">2★ and up</option>
              </select>
            </label>
            <label className="inline-field">
              <span>Year</span>
              <input
                className="input year-input"
                inputMode="numeric"
                maxLength={4}
                placeholder="Any"
                value={yearInput}
                onChange={(e) => setYearInput(e.target.value.replace(/\D/g, ""))}
              />
            </label>
            <label className="inline-field">
              <span>Sort</span>
              <select className="select" value={sort} onChange={(e) => update({ sort: e.target.value, page: "" })}>
                {SORTS.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
      </section>

      {error && (
        <div className="notice error" role="alert">
          <p>{error}</p>
          <button type="button" className="btn btn-line" onClick={() => setReloadKey((k) => k + 1)}>
            Try again
          </button>
        </div>
      )}

      {!error && data === null && <p className="notice">Loading films…</p>}

      {!error && data && (
        <>
          <div className="count-line">
            <p>{plural(data.total, "film")}</p>
            {filtered && (
              <button type="button" className="btn btn-text" onClick={() => setParams(new URLSearchParams())}>
                Clear filters
              </button>
            )}
          </div>

          {data.items.length === 0 ? (
            <p className="notice">No films match. Try another word or remove a filter.</p>
          ) : (
            <div className="wall">
              {data.items.map((m) => (
                <MovieCard key={m.movie_id} movie={m} />
              ))}
            </div>
          )}

          <Pagination
            page={data.page}
            pageSize={data.page_size}
            total={data.total}
            onChange={(p) => {
              update({ page: p === 1 ? "" : p });
              window.scrollTo({ top: 0 });
            }}
          />
        </>
      )}
    </>
  );
}
