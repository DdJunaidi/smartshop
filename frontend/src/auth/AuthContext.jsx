import { createContext, useContext, useEffect, useState } from "react";
import { api, getMe } from "../api";

const AuthCtx = createContext({ user: null, loading: true, setUser: () => {} });

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // if we have a token, try to resolve the current user
    const token = localStorage.getItem("access");
    if (!token) { setLoading(false); return; }
    getMe().then(r => setUser(r.data)).catch(() => setUser(null)).finally(() => setLoading(false));
  }, []);

  return <AuthCtx.Provider value={{ user, loading, setUser }}>{children}</AuthCtx.Provider>;
}
export function useAuth() { return useContext(AuthCtx); }
