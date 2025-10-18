import { useState } from "react";

/**
 * StarRating
 * - value: number (1..5)
 * - onChange: fn(newValue) when user picks a star
 * - readOnly: boolean (no interactivity if true)
 * - size: px size of star (default 22)
 */
export default function StarRating({ value = 0, onChange, readOnly = false, size = 22 }) {
  const [hover, setHover] = useState(0);
  const stars = [1, 2, 3, 4, 5];

  function choose(v) {
    if (readOnly || !onChange) return;
    onChange(v);
  }

  function handleKey(e) {
    if (readOnly || !onChange) return;
    if (e.key === "ArrowRight" || e.key === "ArrowUp") onChange(Math.min(5, (value || 0) + 1));
    if (e.key === "ArrowLeft" || e.key === "ArrowDown") onChange(Math.max(1, (value || 1) - 1));
    if (e.key === "Home") onChange(1);
    if (e.key === "End") onChange(5);
  }

  return (
    <div
      role={readOnly ? undefined : "slider"}
      aria-label="Rating"
      aria-valuemin={1}
      aria-valuemax={5}
      aria-valuenow={value || 0}
      tabIndex={readOnly ? -1 : 0}
      onKeyDown={handleKey}
      style={{ display: "inline-flex", gap: 4, cursor: readOnly ? "default" : "pointer" }}
    >
      {stars.map((s) => {
        const active = (hover || value) >= s;
        return (
          <svg
            key={s}
            onMouseEnter={() => !readOnly && setHover(s)}
            onMouseLeave={() => !readOnly && setHover(0)}
            onClick={() => choose(s)}
            width={size}
            height={size}
            viewBox="0 0 24 24"
            style={{ transition: "transform .08s ease-in-out", transform: active ? "scale(1.05)" : "scale(1.0)" }}
            aria-hidden="true"
          >
            <path
              d="M12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.62L12 2 9.19 8.62 2 9.24l5.46 4.73L5.82 21z"
              fill={active ? "#ffd54f" : "none"}
              stroke={active ? "#ffd54f" : "#555"}
              strokeWidth="1.2"
            />
          </svg>
        );
      })}
    </div>
  );
}
