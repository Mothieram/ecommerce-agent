from django.urls import path
from .views import (
    RegisterView,
    ResendVerificationEmailView,
    VerifyEmailView,
    LoginView,
    LogoutView,
    ProfileView,
    UserUpdateView,
    ChangePasswordView,
    ResetPasswordEmailView,
    ResetPasswordConfirmView,
    GoogleLoginView,
)

urlpatterns = [
    path('register/',                    RegisterView.as_view(),                name='register'),
    path('resend-verification/',         ResendVerificationEmailView.as_view(), name='resend-verification'),
    path('verify-email/<str:uidb64>/<str:token>/', VerifyEmailView.as_view(),   name='verify-email'),
    path('login/',                       LoginView.as_view(),                   name='login'),
    path('logout/',                      LogoutView.as_view(),                  name='logout'),
    path('profile/',                     ProfileView.as_view(),                 name='profile'),
    path('profile/update/',              UserUpdateView.as_view(),              name='user-update'),
    path('change-password/',             ChangePasswordView.as_view(),          name='change-password'),
    path('reset-password/',              ResetPasswordEmailView.as_view(),      name='reset-password'),
    path('reset-password-confirm/<str:uidb64>/<str:token>/', ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
    path('google/',                      GoogleLoginView.as_view(),             name='google-login'),
]