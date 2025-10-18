// smartshop-ui/src/pages/ProductDetail.jsx
import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import {
  api,
  createInteraction,
  genDescription,
  summarizeReviews,
  createReview,
  listReviews,
} from "../api";
import StarRating from "../shared/StarRating";
import { useAuth } from "../auth/AuthContext";
import { addToCart } from "../api";

export default function ProductDetail() {
  const { id } = useParams();
  const [search] = useSearchParams();
  const { user } = useAuth();

  // derive the effective user once: prefer logged-in user; else ?user=; else 1
  const urlUserId = Number(search.get("user") || 0);
  const userId = user?.id || urlUserId || 1;

  // product + generated content
  const [p, setP] = useState(null);
  const [aiDesc, setAiDesc] = useState("");
  const [revSummary, setRevSummary] = useState("");

  // reviews state
  const [reviews, setReviews] = useState([]);
  const [myRating, setMyRating] = useState(5);
  const [myText, setMyText] = useState("");

  // load product and log a view
  useEffect(() => {
    api.get(`/products/${id}/`).then((r) => {
      setP(r.data);
      setAiDesc(r.data.generated?.ai_description || "");
      setRevSummary(r.data.generated?.reviews_summary || "");
      createInteraction({ product_id: r.data.id, type: "view" });
    });
  }, [id, userId]);

  // load reviews
  useEffect(() => {
    listReviews(id).then((r) => setReviews(r.data || []));
  }, [id]);

  async function handleGenDesc() {
    const r = await genDescription(id);
    setAiDesc(r.data?.ai_description || "");
  }

  async function handleSummReviews() {
    const r = await summarizeReviews(id);
    setRevSummary(r.data?.reviews_summary || "");
  }

  async function submitReview() {
  const text = (myText || "").trim();
  if (!text) return;

  // Optional: guard if not logged in (prevents 401s)
  if (!user) {
    alert("Please log in to submit a review.");
    return;
  }

  await createReview({ product: Number(id), rating: myRating, text }); // ⬅️ no 'user'
  setMyText("");
  const r = await listReviews(id);
  setReviews(r.data || []);
}


  if (!p) return <p>Loading...</p>;

  return (
    <div>
      <h3>{p.name}</h3>
      {(p.image || p.image_url) && (
        <img
          src={p.image || p.image_url}
          alt={p.name}
          style={{ width: 420, borderRadius: 10 }}
        />
      )}

      <p style={{ maxWidth: 580 }}>{p.description}</p>
      <div><strong>Category:</strong> {p.category}</div>
      <div><strong>Price:</strong> ${Number(p.price).toFixed(2)}</div>
      <div><strong>Tags:</strong> {p.tags}</div>

      <hr />

      <button onClick={() => addToCart(p.id, 1).then(()=>alert("Added to cart"))}>
        Add to Cart
      </button>
      <button
        style={{ marginLeft: 8 }}
        onClick={() => createInteraction({ product_id: p.id, type: "purchase", rating: 5 })}
      >
        Purchase (logs interaction)
      </button>

      <hr />

      <h4>AI Description</h4>
      <p style={{ maxWidth: 680, whiteSpace: "pre-wrap" }}>{aiDesc || "No AI description yet."}</p>
      <button onClick={handleGenDesc}>Generate / Refresh Description</button>

      <hr />

      <h4>Review Highlights</h4>
      <p style={{ maxWidth: 680, whiteSpace: "pre-wrap" }}>{revSummary || "No summary yet."}</p>
      <button onClick={handleSummReviews}>Summarize Reviews</button>

      <hr />

      <h4>Customer Reviews</h4>
      {reviews.length ? (
        reviews.map((rv) => (
          <div key={rv.id} style={{ marginBottom: 10 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <strong>{rv.user_name}</strong>
              <StarRating value={rv.rating} readOnly size={18} />
              <span style={{ opacity: 0.6, fontSize: 12 }}>{rv.rating} / 5</span>
            </div>
            <div>{rv.text}</div>
          </div>
        ))
      ) : (
        <p>No reviews yet.</p>
      )}

      <div style={{ marginTop: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <label>Rating:</label>
          <StarRating value={myRating} onChange={setMyRating} />
          <span style={{ opacity: 0.7, fontSize: 12 }}>{myRating} / 5</span>
        </div>
        <textarea
          rows={3}
          value={myText}
          onChange={(e) => setMyText(e.target.value)}
          placeholder="Write a short review…"
          style={{ width: 420, marginTop: 8, display: "block" }}
        />
        <button onClick={submitReview} style={{ marginTop: 8 }}>
          Submit review
        </button>
      </div>
    </div>
  );
}
