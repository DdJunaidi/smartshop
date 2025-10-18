import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { searchProducts } from "../api";

/**
 * Shows products for a natural-language query.
 */
export default function SearchResults() {
  const [params] = useSearchParams();
  const q = params.get("q") || "";
  const [items, setItems] = useState([]);

  useEffect(() => {
    if (!q) return;
    searchProducts(q).then(res => setItems(res.data.results || []));
  }, [q]);

  return (
    <div>
      <h3>Results for: “{q}”</h3>
      {!items.length && <p>No results found.</p>}

      <div className="grid">
        {items.map(p => (
          <div key={p.id} className="card">
            {p.image_url && <img src={p.image_url} alt={p.name} />}
            <h4 style={{ margin: "10px 0 4px" }}>
              <Link to={`/products/${p.id}`}>{p.name}</Link>
            </h4>
            <div style={{ fontSize: 13, opacity: 0.8 }}>
              {p.category} — ${Number(p.price).toFixed(2)}
            </div>
            {p.generated?.ai_description && (
              <p style={{ fontSize: 13, opacity: 0.9, marginTop: 8 }}>
                {p.generated.ai_description.slice(0, 120)}…
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
