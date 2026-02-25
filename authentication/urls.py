from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    register_view,
    verify_email_view,
    login_view,
    logout_view,
    profile_view,
    user_update_view,
    change_password_view,
    reset_password_email_view,
    reset_password_confirm_view,
    GoogleLoginview
)
from allauth.socialaccount.providers.google.views import oauth2_callback

urlpatterns = [
    # Auth
    path('register/',register_view,name='register'),
    path('verify-email/<uidb64>/<token>/',verify_email_view,name='verify_email'),
    path('login/',login_view,name='login'),
    path('logout/',logout_view,name='logout'),
    path('token/refresh/',TokenRefreshView.as_view(),name='token_refresh'),
    path('auth/google',GoogleLoginview.as_view,name = 'google_login'),
    path('auth/google/callback/',oauth2_callback,name='google_callback'),

    # Profile
    path('profile/',profile_view,name='profile'),
    path('update-profile/', user_update_view,name='user_update'),

    # Password
    path('change-password/',change_password_view,name='change_password'),
    path('reset-password/',reset_password_email_view,name='reset_password'),
    path('reset-password-confirm/<uidb64>/<token>/',reset_password_confirm_view,  name='reset_password_confirm'),
]