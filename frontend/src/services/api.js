import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/auth";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/token/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem("access_token", access);

          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);

export const authAPI = {
  register: async (data) => {
    const response = await api.post("/register/", data);
    return response.data;
  },

  login: async (data) => {
    const response = await api.post("/login/", data);
    return response.data;
  },

  logout: async (refreshToken) => {
    await api.post("/logout/", { refresh: refreshToken });
  },

  getProfile: async () => {
    const response = await api.get("/profile/");
    return response.data;
  },

  updateProfile: async (data) => {
    const response = await api.put("/update-profile/", data);
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
