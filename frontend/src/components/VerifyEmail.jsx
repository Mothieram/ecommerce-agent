import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { CheckCircle, AlertCircle, Loader } from "lucide-react";

const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/auth`
  : "http://localhost:8000/api/auth";

export const VerifyEmail = () => {
  const { uidb64, token } = useParams();
  const [status, setStatus] = useState("loading"); // loading | success | error
  const [message, setMessage] = useState("");

  useEffect(() => {
    const verify = async () => {
      try {
        const res = await fetch(`${BASE_URL}/verify-email/${uidb64}/${token}/`, {
          credentials: "include",
        });
        const data = await res.json();
        if (res.ok) {
          setStatus("success");
          setMessage(data.message);
        } else {
          setStatus("error");
          setMessage(data.error || "Verification failed.");
        }
      } catch {
        setStatus("error");
        setMessage("Something went wrong. Please try again.");
      }
    };

    verify();
  }, [uidb64, token]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-10 text-center">
        {status === "loading" && (
          <>
            <div className="flex justify-center mb-6">
              <div className="bg-blue-100 p-4 rounded-full">
                <Loader className="w-10 h-10 text-blue-600 animate-spin" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              Verifying your email...
            </h2>
            <p className="text-gray-500">Please wait a moment.</p>
          </>
        )}

        {status === "success" && (
          <>
            <div className="flex justify-center mb-6">
              <div className="bg-green-100 p-4 rounded-full">
                <CheckCircle className="w-10 h-10 text-green-600" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              Email Verified!
            </h2>
            <p className="text-gray-600 mb-8">{message}</p>
            <Link
              to="/login"
              className="inline-block w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Go to Login
            </Link>
          </>
        )}

        {status === "error" && (
          <>
            <div className="flex justify-center mb-6">
              <div className="bg-red-100 p-4 rounded-full">
                <AlertCircle className="w-10 h-10 text-red-600" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              Verification Failed
            </h2>
            <p className="text-gray-600 mb-8">{message}</p>
            <div className="space-y-3">
              <Link
                to="/login"
                className="inline-block w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              >
                Go to Login
              </Link>
              <p className="text-sm text-gray-500">
                Link expired?{" "}
                <Link
                  to="/resend-verification"
                  className="text-blue-600 hover:underline font-medium"
                >
                  Resend verification email
                </Link>
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
