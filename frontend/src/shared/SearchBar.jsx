import { useEffect, useState } from "react";
import { suggest } from "../api";
import { useNavigate } from "react-router-dom";

/**
 * Minimal search bar with LLM autocomplete suggestions.
 * Props:
 *  - initial: optional initial text
 */
export default function SearchBar({ initial = "" }) {
  const [q, setQ] = useState(initial);
  const [sugs, setSugs] = useState([]);
  const [open, setOpen] = useState(false);
  const nav = useNavigate();

  useEffect(() => {
    const id = setTimeout(() => {
      if (q.length >= 2) {
        suggest(q).then(r => setSugs(r.data || [])).catch(() => setSugs([]));
        setOpen(true);
      } else {
        setSugs([]);
        setOpen(false);
      }
    }, 200); // debounce
    return () => clearTimeout(id);
  }, [q]);

  function submit(val) {
    const query = val ?? q;
    if (!query) return;
    nav(`/search?q=${encodeURIComponent(query)}`);
    setOpen(false);
  }

  return (
    <div style={{ position: "relative", maxWidth: 520 }}>
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
        placeholder="Search for 'wireless headphones under $200'..."
        style={{ width: "100%", padding: 10, borderRadius: 8 }}
      />
      <button onClick={() => submit()} style={{ marginTop: 8 }}>Search</button>

      {open && sugs.length > 0 && (
        <div style={{
          position: "absolute", top: 46, left: 0, right: 0,
          background: "#111315", border: "1px solid #333", borderRadius: 8, zIndex: 50
        }}>
          {sugs.map((s, i) => (
            <div
              key={i}
              onMouseDown={() => submit(s)}
              style={{ padding: 8, cursor: "pointer", borderBottom: "1px solid #222" }}
            >
              {s}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
