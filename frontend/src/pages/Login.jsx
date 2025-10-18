import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { setUser } = useAuth();

  async function handleSubmit(e) {
    e.preventDefault();
    try {
      const r = await api.post("/token/", { username, password });
      localStorage.setItem("access", r.data.access);
      localStorage.setItem("refresh", r.data.refresh);
      
      const me = await api.get("/me/");
      setUser(me.data);
      navigate("/");
    } catch {
      setError("Invalid username or password.");
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "60px auto" }}>
      <h3>Login</h3>
      {error && <div style={{ color: "tomato", marginBottom: 8 }}>{error}</div>}
      <form onSubmit={handleSubmit}>
        <input value={username} onChange={e=>setUsername(e.target.value)} placeholder="Username" required style={{ width:"100%", marginBottom:8 }} />
        <input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password" required style={{ width:"100%", marginBottom:8 }} />
        <button type="submit" style={{ width:"100%" }}>Login</button>
      </form>
    </div>
  );
}
