# Re-export all views so existing urls.py imports remain unchanged.
# e.g.:  from .views import RegisterView, LoginView  (still works)

from .auth_views import (
    CsrfCookieView,
    RegisterView,
    LoginView,
    LogoutView,
    TokenRefreshCookieView,
)
from .email_views import (
    ResendVerificationEmailView,
    VerifyEmailView,
)
from .profile_views import (
    ProfileView,
    UserUpdateView,
)
from .password_views import (
    ChangePasswordView,
    ResetPasswordEmailView,
    ResetPasswordConfirmView,
)
from .oauth_views import GoogleLoginView

__all__ = [
    "CsrfCookieView",
    "RegisterView",
    "LoginView",
    "LogoutView",
    "TokenRefreshCookieView",
    "ResendVerificationEmailView",
    "VerifyEmailView",
    "ProfileView",
    "UserUpdateView",
    "ChangePasswordView",
    "ResetPasswordEmailView",
    "ResetPasswordConfirmView",
    "GoogleLoginView",
]
