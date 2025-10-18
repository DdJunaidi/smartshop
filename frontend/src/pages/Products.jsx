// smartshop-ui/src/pages/Products.jsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export default function Products() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    api.get("/products/").then((r) => setItems(r.data));
  }, []);

  return (
    <div>
      <h3>All Products</h3>

      {!items.length && <p>Loading…</p>}

      <div
        className="grid"
        style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 16 }}
      >
        {items.map((p) => (
          <div key={p.id} className="card" style={{ border: "1px solid #222", borderRadius: 12, padding: 12, background: "#111315" }}>
            <img
              src={p.image || p.image_url || "https://picsum.photos/seed/fallback/400/260"}
              alt={p.name}
              style={{ width: "100%", height: 140, objectFit: "cover", borderRadius: 8 }}
              onError={(e) => { e.currentTarget.src = "https://picsum.photos/seed/fallback2/400/260"; }}
            />

            <h4 style={{ margin: "10px 0 4px" }}>
              <Link to={`/products/${p.id}`}>{p.name}</Link>
            </h4>
            <div style={{ fontSize: 13, opacity: 0.8 }}>
              {p.category} — ${Number(p.price).toFixed(2)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
