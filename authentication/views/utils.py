"""Shared helpers for auth views: cookies, tokens, email sending, token blacklisting."""

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

User = get_user_model()


def get_tokens(user):
    # Generate a fresh refresh/access pair for the given user.
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }


def _cookie_kwargs():
    kwargs = {
        "httponly": True,
        "secure":   settings.JWT_COOKIE_SECURE,
        "samesite": settings.JWT_COOKIE_SAMESITE,
        "path":     "/",
    }
    if settings.JWT_COOKIE_DOMAIN:
        kwargs["domain"] = settings.JWT_COOKIE_DOMAIN
    return kwargs


def set_auth_cookies(response, tokens):
    access_max_age  = int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
    refresh_max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())
    kwargs = _cookie_kwargs()

    response.set_cookie(
        settings.JWT_AUTH_COOKIE,
        tokens["access"],
        max_age=access_max_age,
        **kwargs,
    )
    response.set_cookie(
        settings.JWT_AUTH_REFRESH_COOKIE,
        tokens["refresh"],
        max_age=refresh_max_age,
        **kwargs,
    )


def clear_auth_cookies(response):
    # Mirror cookie attributes used in set_cookie so deletion always matches.
    response.delete_cookie(
        settings.JWT_AUTH_COOKIE,
        path="/",
        domain=settings.JWT_COOKIE_DOMAIN,
        samesite=settings.JWT_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        settings.JWT_AUTH_REFRESH_COOKIE,
        path="/",
        domain=settings.JWT_COOKIE_DOMAIN,
        samesite=settings.JWT_COOKIE_SAMESITE,
    )


def send_verification_email(user, request):
    uid   = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link  = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"
    send_mail(
        subject="Verify your email address",
        message=(
            f"Hi {user.username},\n\n"
            f"Please verify your email:\n\n{link}\n\n"
            "This link expires in 24 hours."
        ),
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False,
    )


def blacklist_all_user_tokens(user):
    """Blacklist all active refresh tokens for a user (used after password reset)."""
    for token in OutstandingToken.objects.filter(user=user, expires_at__gt=timezone.now()):
        try:
            RefreshToken(token.token).blacklist()
        except TokenError:
            pass
