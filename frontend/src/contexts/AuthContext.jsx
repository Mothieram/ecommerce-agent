import { createContext, useContext, useState, useEffect } from "react";
import { ensureCsrfCookie, getCsrfToken } from "../services/csrf";

const AuthContext = createContext(null);

const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/auth`
  : "http://localhost:8000/api/auth";

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      await ensureCsrfCookie(BASE_URL);
      await fetchProfile();
    };
    initAuth();
  }, []);

  const fetchProfile = async () => {
    try {
      let res = await fetch(`${BASE_URL}/profile/`, {
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });

      if (res.status === 401) {
        const csrfToken = getCsrfToken();
        const refreshRes = await fetch(`${BASE_URL}/token/refresh/`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
          },
          body: JSON.stringify({}),
        });

        if (refreshRes.ok) {
          res = await fetch(`${BASE_URL}/profile/`, {
            credentials: "include",
            headers: { "Content-Type": "application/json" },
          });
        }
      }

      const data = await res.json();
      if (res.ok) {
        setUser(data);
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials) => {
    await ensureCsrfCookie(BASE_URL);
    const csrfToken = getCsrfToken();
    const res = await fetch(`${BASE_URL}/login/`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
      },
      body: JSON.stringify(credentials),
    });
    const data = await res.json();
    if (!res.ok) throw data;
    setUser(data.user);
    return data;
  };

  const register = async (payload) => {
    await ensureCsrfCookie(BASE_URL);
    const csrfToken = getCsrfToken();
    const res = await fetch(`${BASE_URL}/register/`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
      },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw data;
    return data;
  };

  const googleLogin = async (googleAccessToken, intent = "login") => {
    await ensureCsrfCookie(BASE_URL);
    const csrfToken = getCsrfToken();
    const res = await fetch(`${BASE_URL}/google/`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
      },
      body: JSON.stringify({ access_token: googleAccessToken, intent }),
    });
    const data = await res.json();
    if (!res.ok) throw data;
    await fetchProfile();
    return data;
  };

  const logout = async () => {
    try {
      await ensureCsrfCookie(BASE_URL);
      const csrfToken = getCsrfToken();
      await fetch(`${BASE_URL}/logout/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
        },
        body: JSON.stringify({}),
      });
    } catch {
      // Keep local state cleanup even if API call fails.
    } finally {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
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
