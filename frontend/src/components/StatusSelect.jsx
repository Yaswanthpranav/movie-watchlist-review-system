import { STATUSES } from "../utils.js";

export default function StatusSelect({ value, onChange, disabled, label = "Status", id }) {
  return (
    <select
      id={id}
      className="select select-sm"
      aria-label={label}
      value={value}
      disabled={disabled}
      onChange={(e) => onChange(e.target.value)}
    >
      {STATUSES.map((s) => (
        <option key={s.value} value={s.value}>
          {s.label}
        </option>
      ))}
    </select>
  );
}
