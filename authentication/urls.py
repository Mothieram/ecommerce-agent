from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    register_view,
    resend_verification_email_view,
    verify_email_view,
    login_view,
    logout_view,
    profile_view,
    user_update_view,
    change_password_view,
    reset_password_email_view,
    reset_password_confirm_view,
    google_login_view,
)

urlpatterns = [
    # Auth
    path('register/',                                  register_view,                    name='register'),
    path('resend-verification/',                       resend_verification_email_view,   name='resend_verification'),
    path('verify-email/<uidb64>/<token>/',             verify_email_view,                name='verify_email'),
    path('login/',                                     login_view,                       name='login'),
    path('logout/',                                    logout_view,                      name='logout'),
    path('token/refresh/',                             TokenRefreshView.as_view(),       name='token_refresh'),
    path('google/',                                    google_login_view,                name='google_login'),

    # Profile
    path('profile/',                                   profile_view,                     name='profile'),
    path('update-profile/',                            user_update_view,                 name='user_update'),

    # Password
    path('change-password/',                           change_password_view,             name='change_password'),
    path('reset-password/',                            reset_password_email_view,        name='reset_password'),
    path('reset-password-confirm/<uidb64>/<token>/',   reset_password_confirm_view,      name='reset_password_confirm'),
]