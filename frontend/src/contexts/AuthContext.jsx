// src/contexts/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext(null);
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // ── helpers ──────────────────────────────────────────────────────────────
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
      const res = await fetch(`${BASE_URL}/auth/profile/`, {
        headers: authHeaders(),
      });
      const data = await res.json();
      if (res.ok) setUser(data);
      else clearTokens();
    } catch {
      clearTokens();
    } finally {
      setLoading(false);
    }
  };

  // ── standard login ────────────────────────────────────────────────────────
  const login = async (credentials) => {
    const res = await fetch(`${BASE_URL}/auth/login/`, {
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
    const res = await fetch(`${BASE_URL}/auth/register/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw data;
    return data; // no auto-login: user must verify email first
  };

  // ── Google OAuth ──────────────────────────────────────────────────────────
  // Receives the Google access_token from useGoogleLogin,
  // sends it to our Django backend which verifies it with Google,
  // creates/fetches the user, and returns our own JWT tokens.
  const googleLogin = async (googleAccessToken) => {
    const res = await fetch(`${BASE_URL}/auth/google/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ access_token: googleAccessToken }),
    });
    const data = await res.json();
    if (!res.ok) throw data;
    saveTokens({ access: data.access, refresh: data.refresh });
    // fetch full profile after saving tokens
    await fetchProfile();
    return data;
  };

  // ── logout ────────────────────────────────────────────────────────────────
  const logout = async () => {
    try {
      await fetch(`${BASE_URL}/auth/logout/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          refresh: localStorage.getItem("refresh_token"),
        }),
      });
    } catch {
      // even if it fails, clear local state
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
