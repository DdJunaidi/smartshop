// frontend/src/pages/Home.jsx
import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth/AuthContext";
import RecommendedProducts from "../shared/RecommendedProducts";
import SearchBar from "../shared/SearchBar";

export default function Home() {
  const { user } = useAuth();           // set by Login → /api/token + /api/me
  const [recs, setRecs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  async function loadRecs() {
    setLoading(true);
    setErrorMsg("");
    try {
      if (user) {
        // 1) fast path (no LLM): instant UI
        const fast = await api.get("/recommendations/me/?fast=1");
        setRecs(Array.isArray(fast.data) ? fast.data : []);

        // 2) quiet upgrade to LLM-ranked results when ready
        api.get("/recommendations/me/")
          .then(r => Array.isArray(r.data) && setRecs(r.data))
          .catch(() => {/* ignore upgrade failure */});
      } else {
        // not logged in → clear recs
        setRecs([]);
      }
    } catch (e) {
      setErrorMsg("Could not load recommendations.");
      setRecs([]);
    } finally {
      setLoading(false);
    }
  }

  // Re-load when login state changes
  useEffect(() => { loadRecs(); }, [user?.id]);

  return (
    <div>
      <h3>Home</h3>

      {/* Smart search with suggestions */}
      <SearchBar />

      <p style={{ marginTop: 12 }}>
        {user ? (
          <>Hi <strong>{user.first_name || user.username}</strong>! Here are your personalized picks.</>
        ) : (
          <>Please <strong>Login</strong> to see personalized recommendations.</>
        )}
      </p>

      {user && (
        <>
          {loading && <p>Loading recommendations…</p>}
          {!!errorMsg && <p style={{ color: "tomato" }}>{errorMsg}</p>}
          {(!loading && !errorMsg) && (
            recs.length ? (
              <RecommendedProducts items={recs} />
            ) : (
              <p>No recommendations yet.</p>
            )
          )}
        </>
      )}
    </div>
  );
}
