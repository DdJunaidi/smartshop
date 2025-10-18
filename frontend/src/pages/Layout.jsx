// src/pages/Layout.jsx
import { useEffect } from "react";
import { Outlet, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { getMe, logout as apiLogout } from "../api";
import ChatbotWidget from "../shared/ChatbotWidget";

export default function Layout() {
  const { user, loading, setUser } = useAuth();
  const nav = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("access");
    if (!token || user) return;
    (async () => {
      try {
        const r = await getMe();
        setUser(r.data);
      } catch {
        apiLogout();
        setUser(null);
      }
    })();
  }, [user, setUser]);

  function doLogout() {
    apiLogout();
    setUser(null);
    nav("/login");
  }

  return (
    <div style={{ maxWidth: 960, margin: "0 auto", padding: 16 }}>
      <header style={{ display: "flex", gap: 16, alignItems: "center" }}>
        <h2 style={{ marginRight: 16 }}>SmartShop</h2>
        <nav style={{ display: "flex", gap: 12 }}>
          <Link to="/">Home</Link>
          <Link to="/products">Products</Link>
          <Link to="/cart">Cart</Link>
        </nav>

        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          {loading ? (
            <span>Loading…</span>
          ) : user ? (
            <>
              <span>
                Hello, <strong>{user.first_name || user.username}</strong>
              </span>
              <button onClick={doLogout}>Logout</button>
            </>
          ) : (
            <Link to="/login">Login</Link>
          )}
        </div>
      </header>
      <hr />
      <Outlet />
      <ChatbotWidget /> {/* floating widget */}
    </div>
  );
}
