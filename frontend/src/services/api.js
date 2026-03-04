import axios from "axios";
import { ensureCsrfCookie, getCsrfToken } from "./csrf";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api/auth";

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

let authSessionEnded = false;

api.interceptors.request.use(async (config) => {
  const method = (config.method || "get").toLowerCase();
  const unsafeMethod = ["post", "put", "patch", "delete"].includes(method);

  if (unsafeMethod) {
    if (!getCsrfToken()) {
      await ensureCsrfCookie(API_BASE_URL);
    }
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      config.headers["X-CSRFToken"] = csrfToken;
    }
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const requestUrl = String(originalRequest?.url || "");
    const isAuthFlowEndpoint =
      requestUrl.includes("/logout/") || requestUrl.includes("/token/refresh/");

    if (
      error.response?.status === 401 &&
      !originalRequest?._retry &&
      !isAuthFlowEndpoint &&
      !authSessionEnded
    ) {
      originalRequest._retry = true;

      try {
        await axios.post(
          `${API_BASE_URL}/token/refresh/`,
          {},
          { withCredentials: true },
        );
        authSessionEnded = false;
        return api(originalRequest);
      } catch (refreshError) {
        authSessionEnded = true;
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);

export const authAPI = {
  register: async (data) => {
    authSessionEnded = false;
    const response = await api.post("/register/", data);
    return response.data;
  },

  login: async (data) => {
    authSessionEnded = false;
    const response = await api.post("/login/", data);
    return response.data;
  },

  logout: async () => {
    authSessionEnded = true;
    await api.post("/logout/", {});
  },

  getProfile: async () => {
    const response = await api.get("/profile/");
    return response.data;
  },

  updateProfile: async (data) => {
    const response = await api.put("/profile/update/", data);
    return response.data;
  },

  changePassword: async (data) => {
    const response = await api.post("/change-password/", data);
    return response.data;
  },

  resetPasswordEmail: async (email) => {
    const response = await api.post("/reset-password/", { email });
    return response.data;
  },

  resetPasswordConfirm: async (uidb64, token, new_password, new_password2) => {
    const response = await api.post(
      `/reset-password-confirm/${uidb64}/${token}/`,
      {
        new_password,
        new_password2,
      },
    );
    return response.data;
  },
};
