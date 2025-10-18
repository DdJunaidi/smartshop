// frontend/src/shared/RecommendedProducts.jsx
// Reusable component that displays recommendations and the "reason" from Gemini.
// Each card shows image, name, price, reason, and a link to the detail page.

import { Link } from "react-router-dom";
import { createInteraction, api } from "../api";
import { useAuth } from "../auth/AuthContext";

// ---- relative media URLs coming from DRF ----
const API_BASE =
  (api?.defaults?.baseURL || "http://127.0.0.1:8000/api").replace(/\/api\/?$/, "");

function resolveImg(p) {
  const img = p.image || p.image_url || "";
  if (!img) return "https://picsum.photos/seed/fallback/400/260";
  // If DRF returns a relative path (e.g. "/media/products/x.jpg"), prefix with host
  if (img.startsWith("/")) return `${API_BASE}${img}`;
  return img; // already absolute URL
}

export default function RecommendedProducts({ items = [], userId = 1 }) {
  const { user } = useAuth();
  const effectiveUserId = user?.id || userId; // use logged-in user if available

  async function handleAction(productId, type) {
    try {
      await createInteraction({
        product_id: productId,
        type,
        rating: type === "purchase" ? 5 : null,
      });
      // optional toast/alert here
    } catch (e) {
      console.error("Failed to log interaction:", e);
      alert("Failed to log interaction");
    }
  }

  if (!items.length) return <p>No recommendations yet.</p>;

  return (
    <div
      style={{
        display: "grid",
        gap: 16,
        gridTemplateColumns: "repeat(auto-fill, minmax(260px,1fr))",
      }}
    >
      {items.map((p) => (
        <div
          key={p.id}
          style={{ border: "1px solid #333", borderRadius: 12, padding: 12 }}
          className="card"
        >
          <img
            src={resolveImg(p)}
            alt={p.name}
            style={{ width: "100%", height: 140, objectFit: "cover", borderRadius: 8 }}
            onError={(e) => {
              e.currentTarget.src = "https://picsum.photos/seed/fallback2/400/260";
            }}
          />

          <h4 style={{ margin: "12px 0 6px" }}>{p.name}</h4>
          <div style={{ fontSize: 13, opacity: 0.6 }}>
            {p.category} • ${Number(p.price).toFixed(2)}
          </div>

          <div className="badge-why" style={{ marginTop: 8 }}>
            <strong>Why:</strong> {p.reason || "No reason"}{" "}
            <span style={{ opacity: 0.6 }}>
              (score {Number(p.score ?? 0).toFixed(2)})
            </span>
          </div>

          <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
            <button onClick={() => handleAction(p.id, "cart")}>Add to cart</button>
            <button onClick={() => handleAction(p.id, "purchase")}>Purchase</button>
            {/* carry the user into the detail page */}
            <Link to={`/products/${p.id}`}>View details</Link>
          </div>
        </div>
      ))}
    </div>
  );
}
