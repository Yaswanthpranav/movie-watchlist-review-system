import { useEffect, useState } from "react";

// Two-step destructive button: the first click arms it, the second confirms.
// Avoids browser confirm() dialogs.
export default function ConfirmButton({ children, confirmLabel, onConfirm, disabled, className = "" }) {
  const [armed, setArmed] = useState(false);

  useEffect(() => {
    if (!armed) return undefined;
    const t = setTimeout(() => setArmed(false), 4000);
    return () => clearTimeout(t);
  }, [armed]);

  return (
    <button
      type="button"
      className={`btn btn-text danger ${armed ? "armed" : ""} ${className}`}
      disabled={disabled}
      onClick={() => {
        if (armed) {
          setArmed(false);
          onConfirm();
        } else setArmed(true);
      }}
    >
      {armed ? confirmLabel : children}
    </button>
  );
}
