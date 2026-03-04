import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { UserPlus, AlertCircle, CheckCircle, Eye, EyeOff } from "lucide-react";
import { useGoogleLogin } from "@react-oauth/google";

export const Register = () => {
  const navigate = useNavigate();
  const { register, googleLogin } = useAuth();

  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    password2: "",
  });

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showPassword2, setShowPassword2] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (formData.password !== formData.password2) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      await register(formData);
      setSuccess(
        "Account created! Please check your email to verify your account before logging in.",
      );
      setFormData({ username: "", email: "", password: "", password2: "" });
    } catch (err) {
      setError(
        err.username?.[0] ||
          err.email?.[0] ||
          err.non_field_errors?.[0] ||
          err.message ||
          "Registration failed. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleRegister = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setError("");
      setGoogleLoading(true);
      try {
        const data = await googleLogin(tokenResponse.access_token, "register");
        if (data.requires_password_setup) {
          navigate("/set-password");
        } else {
          navigate("/profile");
        }
      } catch (err) {
        setError(
          err.error ||
          err.non_field_errors?.[0] ||
          err.message ||
          "Google sign-up failed. Please try again.",
        );
      } finally {
        setGoogleLoading(false);
      }
    },
    onError: () =>
      setError("Google sign-up was cancelled or failed. Please try again."),
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-gray-100 flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="flex justify-center mb-6">
          <div className="bg-green-100 p-3 rounded-full">
            <UserPlus className="w-8 h-8 text-green-600" />
          </div>
        </div>

        <h2 className="text-3xl font-bold text-center text-gray-800 mb-2">
          Create Account
        </h2>
        <p className="text-center text-gray-600 mb-8">Sign up to get started</p>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
            <AlertCircle className="w-5 h-5 text-red-600 mr-3 flex-shrink-0 mt-0.5" />
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start">
            <CheckCircle className="w-5 h-5 text-green-600 mr-3 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-green-800 text-sm">{success}</p>
              <Link
                to="/login"
                className="text-green-700 font-semibold underline text-sm mt-1 inline-block"
              >
                Go to Login
              </Link>
            </div>
          </div>
        )}

        {/* ── Google Button ─────────────────────────────── */}
        <button
          type="button"
          onClick={() => handleGoogleRegister()}
          disabled={googleLoading || loading}
          className="w-full flex items-center justify-center gap-3 border border-gray-300 rounded-lg py-3 px-4 mb-6 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {googleLoading ? (
            <svg
              className="w-5 h-5 animate-spin text-gray-500"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v8z"
              />
            </svg>
          ) : (
            <svg className="w-5 h-5" viewBox="0 0 48 48">
              <path
                fill="#4285F4"
                d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v8.5h12.7c-.6 3-2.3 5.5-4.8 7.2v6h7.8c4.6-4.2 7.3-10.5 7.3-17.2z"
              />
              <path
                fill="#34A853"
                d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.8-6c-2.1 1.4-4.8 2.3-8.1 2.3-6.2 0-11.5-4.2-13.4-9.9H2.6v6.2C6.5 42.6 14.7 48 24 48z"
              />
              <path
                fill="#FBBC05"
                d="M10.6 28.6A14.8 14.8 0 0 1 9.8 24c0-1.6.3-3.1.8-4.6v-6.2H2.6A23.9 23.9 0 0 0 0 24c0 3.9.9 7.5 2.6 10.8l8-6.2z"
              />
              <path
                fill="#EA4335"
                d="M24 9.5c3.5 0 6.6 1.2 9 3.6l6.8-6.8C35.9 2.1 30.5 0 24 0 14.7 0 6.5 5.4 2.6 13.2l8 6.2C12.5 13.7 17.8 9.5 24 9.5z"
              />
            </svg>
          )}
          <span className="text-gray-700 font-medium">
            {googleLoading ? "Signing up..." : "Continue with Google"}
          </span>
        </button>

        {/* ── Divider ───────────────────────────────────── */}
        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="bg-white px-3 text-gray-500">
              or sign up with email
            </span>
          </div>
        </div>

        {/* ── Standard form ─────────────────────────────── */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label
              htmlFor="username"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              required
              value={formData.username}
              onChange={(e) =>
                setFormData({ ...formData, username: e.target.value })
              }
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
              placeholder="Choose a username"
            />
          </div>

          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={formData.email}
              onChange={(e) =>
                setFormData({ ...formData, email: e.target.value })
              }
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
              placeholder="your@email.com"
            />
          </div>

          {/* ── Password ──────────────────────────────────── */}
          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                required
                minLength={8}
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all pr-12"
                placeholder="Min. 8 characters"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                {showPassword ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          {/* ── Confirm Password ──────────────────────────── */}
          <div>
            <label
              htmlFor="password2"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Confirm Password
            </label>
            <div className="relative">
              <input
                id="password2"
                type={showPassword2 ? "text" : "password"}
                required
                minLength={8}
                value={formData.password2}
                onChange={(e) =>
                  setFormData({ ...formData, password2: e.target.value })
                }
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all pr-12"
                placeholder="Confirm your password"
              />
              <button
                type="button"
                onClick={() => setShowPassword2(!showPassword2)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                {showPassword2 ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || googleLoading}
            className="w-full bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <p className="mt-8 text-center text-gray-600">
          Already have an account?{" "}
          <Link
            to="/login"
            className="text-green-600 hover:text-green-700 font-semibold transition-colors"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
};
