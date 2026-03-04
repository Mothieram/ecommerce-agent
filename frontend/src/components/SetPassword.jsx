import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Lock, AlertCircle, CheckCircle } from "lucide-react";
import { authAPI } from "../services/api";
import { useAuth } from "../contexts/AuthContext";

export const SetPassword = () => {
  const navigate = useNavigate();
  const { fetchProfile, user } = useAuth();
  const [formData, setFormData] = useState({
    new_password: "",
    new_password2: "",
  });
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user?.has_usable_password) {
      navigate("/profile");
    }
  }, [user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage(null);
    if (formData.new_password !== formData.new_password2) {
      setMessage({ type: "error", text: "Passwords do not match." });
      return;
    }

    setLoading(true);
    try {
      await authAPI.changePassword({
        old_password: "",
        new_password: formData.new_password,
        new_password2: formData.new_password2,
      });
      await fetchProfile();
      setMessage({ type: "success", text: "Password set successfully. Redirecting..." });
      setTimeout(() => navigate("/profile"), 1000);
    } catch (err) {
      setMessage({
        type: "error",
        text: err.response?.data?.error || "Failed to set password.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="flex justify-center mb-6">
          <div className="bg-blue-100 p-3 rounded-full">
            <Lock className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <h2 className="text-3xl font-bold text-center text-gray-800 mb-2">
          Set Password
        </h2>
        <p className="text-center text-gray-600 mb-8">
          Set a password to enable email and password login.
        </p>

        {message && (
          <div
            className={`mb-6 p-4 rounded-lg flex items-start ${
              message.type === "success"
                ? "bg-green-50 border border-green-200"
                : "bg-red-50 border border-red-200"
            }`}
          >
            {message.type === "success" ? (
              <CheckCircle className="w-5 h-5 text-green-600 mr-3 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-600 mr-3 flex-shrink-0 mt-0.5" />
            )}
            <p
              className={
                message.type === "success" ? "text-green-800 text-sm" : "text-red-800 text-sm"
              }
            >
              {message.text}
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              New Password
            </label>
            <input
              type="password"
              minLength={8}
              required
              value={formData.new_password}
              onChange={(e) =>
                setFormData({ ...formData, new_password: e.target.value })
              }
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confirm Password
            </label>
            <input
              type="password"
              minLength={8}
              required
              value={formData.new_password2}
              onChange={(e) =>
                setFormData({ ...formData, new_password2: e.target.value })
              }
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Saving..." : "Set Password"}
          </button>
        </form>
      </div>
    </div>
  );
};
