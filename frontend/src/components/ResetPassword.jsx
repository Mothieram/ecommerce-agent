import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { authAPI } from '../services/api';
import { KeyRound, AlertCircle, CheckCircle, ArrowLeft } from 'lucide-react';

export const ResetPassword = () => {
  const { uidb64, token } = useParams();
  const [email, setEmail] = useState('');
  const [passwords, setPasswords] = useState({ new_password: '', new_password2: '' });
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(false);

  const isConfirmPage = uidb64 && token;

  const handleRequestReset = async (e) => {
    e.preventDefault();
    setMessage(null);
    setLoading(true);

    try {
      const response = await authAPI.resetPasswordEmail(email);
      setMessage({ type: 'success', text: response.message });
      setEmail('');
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Failed to send reset email' });
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmReset = async (e) => {
    e.preventDefault();
    setMessage(null);

    if (passwords.new_password !== passwords.new_password2) {
      setMessage({ type: 'error', text: 'Passwords do not match' });
      return;
    }

    setLoading(true);

    try {
      const response = await authAPI.resetPasswordConfirm(
        uidb64,
        token,
        passwords.new_password,
        passwords.new_password2
      );
      setMessage({ type: 'success', text: response.message });
      setPasswords({ new_password: '', new_password2: '' });
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.error || 'Failed to reset password' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 to-gray-100 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="flex justify-center mb-6">
          <div className="bg-teal-100 p-3 rounded-full">
            <KeyRound className="w-8 h-8 text-teal-600" />
          </div>
        </div>

        <h2 className="text-3xl font-bold text-center text-gray-800 mb-2">
          {isConfirmPage ? 'Set New Password' : 'Reset Password'}
        </h2>
        <p className="text-center text-gray-600 mb-8">
          {isConfirmPage
            ? 'Enter your new password below'
            : 'Enter your email to receive a password reset link'}
        </p>

        {message && (
          <div
            className={`mb-6 p-4 rounded-lg flex items-start ${
              message.type === 'success'
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}
          >
            {message.type === 'success' ? (
              <CheckCircle className="w-5 h-5 text-green-600 mr-3 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-600 mr-3 flex-shrink-0 mt-0.5" />
            )}
            <p className={message.type === 'success' ? 'text-green-800' : 'text-red-800'}>{message.text}</p>
          </div>
        )}

        {isConfirmPage ? (
          <form onSubmit={handleConfirmReset} className="space-y-6">
            <div>
              <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 mb-2">
                New Password
              </label>
              <input
                id="new_password"
                type="password"
                required
                minLength={8}
                value={passwords.new_password}
                onChange={(e) => setPasswords({ ...passwords, new_password: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                placeholder="Min. 8 characters"
              />
            </div>

            <div>
              <label htmlFor="new_password2" className="block text-sm font-medium text-gray-700 mb-2">
                Confirm New Password
              </label>
              <input
                id="new_password2"
                type="password"
                required
                minLength={8}
                value={passwords.new_password2}
                onChange={(e) => setPasswords({ ...passwords, new_password2: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                placeholder="Confirm your new password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-teal-600 text-white py-3 rounded-lg font-semibold hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Resetting...' : 'Reset Password'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleRequestReset} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                placeholder="your@email.com"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-teal-600 text-white py-3 rounded-lg font-semibold hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Sending...' : 'Send Reset Link'}
            </button>
          </form>
        )}

        <Link
          to="/login"
          className="flex items-center justify-center gap-2 mt-8 text-gray-600 hover:text-gray-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="font-medium">Back to Login</span>
        </Link>
      </div>
    </div>
  );
};