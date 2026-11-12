export const STATUSES = [
  { value: "PLANNED", label: "Planned" },
  { value: "WATCHING", label: "Watching" },
  { value: "COMPLETED", label: "Completed" },
];

export const statusLabel = (value) => STATUSES.find((s) => s.value === value)?.label ?? value;

export const fmtDate = (iso) =>
  new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });

export const fmtRuntime = (minutes) => {
  if (!minutes) return "";
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h ? `${h}h ${String(m).padStart(2, "0")}m` : `${m}m`;
};

export const fmtRating = (value) => (value == null ? "–" : Number(value).toFixed(1));

export const plural = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;

export const SORTS = [
  { value: "title_asc", label: "Title, A to Z" },
  { value: "title_desc", label: "Title, Z to A" },
  { value: "year_desc", label: "Newest first" },
  { value: "year_asc", label: "Oldest first" },
  { value: "rating_desc", label: "Highest rated" },
  { value: "rating_asc", label: "Lowest rated" },
  { value: "reviews_desc", label: "Most reviewed" },
];
