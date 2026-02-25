import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { Login } from "./components/Login";
import { Register } from "./components/Register";
import { Profile } from "./components/Profile";
import { VerifyEmail } from "./components/VerifyEmail";
import { ResetPassword } from "./components/ResetPassword";
import { ResendVerification } from "./components/ResendVerification";
import { PrivateRoute } from "./components/PrivateRoute";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/resend-verification" element={<ResendVerification />} />
          <Route
            path="/reset-password-confirm/:uidb64/:token"
            element={<ResetPassword />}
          />
          <Route
            path="/verify-email/:uidb64/:token"
            element={<VerifyEmail />}
          />
          <Route
            path="/profile"
            element={
              <PrivateRoute>
                <Profile />
              </PrivateRoute>
            }
          />
          <Route path="/" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
