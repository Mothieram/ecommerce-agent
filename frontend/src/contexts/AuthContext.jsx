// src/contexts/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext(null);

const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/auth`
  : "http://localhost:8000/api/auth";

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // ── helpers ───────────────────────────────────────────────────────────────
  const saveTokens = ({ access, refresh }) => {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
  };

  const clearTokens = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  };

  const authHeaders = () => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
  });

  // ── load user on mount ────────────────────────────────────────────────────
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) fetchProfile();
    else setLoading(false);
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await fetch(`${BASE_URL}/profile/`, {
        headers: authHeaders(),
      });
      const data = await res.json();
      if (res.ok) setUser(data);
      else {
        clearTokens();
        setUser(null);
      }
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  // ── standard login ────────────────────────────────────────────────────────
  const login = async (credentials) => {
    const res = await fetch(`${BASE_URL}/login/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
    });
    const data = await res.json();
    if (!res.ok) throw data;
    saveTokens(data.tokens);
    setUser(data.user);
    return data;
  };

  // ── standard register ─────────────────────────────────────────────────────
  const register = async (payload) => {
    const res = await fetch(`${BASE_URL}/register/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw data;
    return data; // no auto-login: user must verify email first
  };

  // ── Google OAuth ──────────────────────────────────────────────────────────
  const googleLogin = async (googleAccessToken) => {
    const res = await fetch(`${BASE_URL}/google/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ access_token: googleAccessToken }),
    });
    const data = await res.json();
    if (!res.ok) throw data;
    saveTokens({ access: data.access, refresh: data.refresh });
    await fetchProfile();
    return data;
  };

  // ── logout ────────────────────────────────────────────────────────────────
  const logout = async () => {
    try {
      await fetch(`${BASE_URL}/logout/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          refresh: localStorage.getItem("refresh_token"),
        }),
      });
    } catch {
      // clear local state even if request fails
    } finally {
      clearTokens();
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user, // ← used by PrivateRoute and Login
        login,
        register,
        googleLogin,
        logout,
        fetchProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
};
