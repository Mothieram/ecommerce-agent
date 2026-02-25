from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

import requests as http_requests

from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    LogoutSerializer,
    ChangePasswordSerializer,
    UserUpdateSerializer,
    ResetPasswordEmailSerializer,
    ResetPasswordConfirmSerializer,
)


# ──────────────────────────────────────────────
# Throttle classes
# ──────────────────────────────────────────────
class AuthRateThrottle(AnonRateThrottle):
    rate = '5/min'

class PasswordResetThrottle(AnonRateThrottle):
    rate = '3/hour'


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }


def send_verification_email(user, request):
    uid   = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link  = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"
    send_mail(
        subject="Verify your email address",
        message=f"Hi {user.username},\n\nPlease verify your email:\n\n{link}\n\nThis link expires in 24 hours.",
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


# ──────────────────────────────────────────────
# Register
# ──────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        try:
            send_verification_email(user, request)
        except Exception:
            pass
        return Response({
            "message": "Registration successful. Please check your email to verify your account.",
            "user": {
                "id":       user.id,
                "username": user.username,
                "email":    user.email,
            },
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Resend Verification Email
# ──────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def resend_verification_email_view(request):
    email = request.data.get('email')
    if not email:
        return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Always return generic response to prevent email enumeration
    generic_response = Response(
        {"message": "If that email exists and is unverified, a new verification link has been sent."},
        status=status.HTTP_200_OK,
    )
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return generic_response

    if user.is_active:
        return Response({"message": "Account is already verified. You can log in."}, status=status.HTTP_200_OK)

    try:
        send_verification_email(user, request)
    except Exception:
        return Response(
            {"error": "Failed to send email. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return generic_response


# ──────────────────────────────────────────────
# Email Verification
# ──────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email_view(request, uidb64, token):
    try:
        uid  = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError):
        return Response({"error": "Invalid verification link."}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({"error": "Verification link is invalid or has expired."}, status=status.HTTP_400_BAD_REQUEST)

    if user.is_active:
        return Response({"message": "Account already verified. You can log in."}, status=status.HTTP_200_OK)

    user.is_active  = True
    user.last_login = timezone.now()
    user.save(update_fields=['is_active', 'last_login'])

    return Response({
        "message": "Email verified successfully. You can now log in.",
        "tokens":  get_tokens(user),
    }, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        return Response({
            "message": "Login successful.",
            "user": {
                "id":         user.id,
                "username":   user.username,
                "email":      user.email,
                "last_login": user.last_login,
            },
            "tokens": get_tokens(user),
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Logout
# ──────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    serializer = LogoutSerializer(data=request.data)
    if serializer.is_valid():
        try:
            token = RefreshToken(serializer.validated_data['refresh'])
            token.blacklist()
            return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({"error": "Token is invalid or already expired."}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Profile
# ──────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user
    return Response({
        "id":          user.id,
        "username":    user.username,
        "email":       user.email,
        "first_name":  user.first_name,
        "last_name":   user.last_name,
        "date_joined": user.date_joined,
        "last_login":  user.last_login,
    }, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────
# Update Profile
# ──────────────────────────────────────────────
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_update_view(request):
    serializer = UserUpdateSerializer(
        request.user,
        data=request.data,
        partial=request.method == 'PATCH',
    )
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Profile updated successfully.",
            "user":    serializer.data,
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Change Password
# ──────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    serializer = ChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"error": "Old password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({
            "message": "Password changed successfully.",
            "tokens":  get_tokens(user),
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Password Reset — send email
# ──────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetThrottle])
def reset_password_email_view(request):
    serializer = ResetPasswordEmailSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        generic_response = Response(
            {"message": "If an account with that email exists, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return generic_response

        uid        = urlsafe_base64_encode(force_bytes(user.pk))
        token      = default_token_generator.make_token(user)
        reset_link = f"{settings.FRONTEND_URL}/reset-password-confirm/{uid}/{token}/"

        try:
            send_mail(
                subject="Reset your password",
                message=f"Hi {user.username},\n\nReset your password here:\n\n{reset_link}\n\nThis link expires in 24 hours. If you didn't request this, ignore this email.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception:
            return Response(
                {"error": "Failed to send email. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return generic_response
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Password Reset — confirm
# ──────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_confirm_view(request, uidb64, token):
    serializer = ResetPasswordConfirmSerializer(data=request.data)
    if serializer.is_valid():
        try:
            uid  = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError):
            return Response({"error": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Reset link is invalid or has expired."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # Blacklist all existing tokens so old sessions can't be reused
        blacklist_all_user_tokens(user)

        return Response({"message": "Password reset successfully. You can now log in."}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Google OAuth
# ──────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def google_login_view(request):
    """
    Receives the Google access_token from the frontend (@react-oauth/google).
    Verifies it with Google, creates/fetches the Django user,
    and returns our own JWT tokens.
    """
    access_token = request.data.get('access_token')
    if not access_token:
        return Response({'error': 'access_token is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Verify token with Google and fetch user info
    google_response = http_requests.get(
        'https://www.googleapis.com/oauth2/v3/userinfo',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    if google_response.status_code != 200:
        return Response({'error': 'Invalid or expired Google token.'}, status=status.HTTP_400_BAD_REQUEST)

    google_data = google_response.json()
    email       = google_data.get('email')
    first_name  = google_data.get('given_name', '')
    last_name   = google_data.get('family_name', '')

    if not email:
        return Response({'error': 'Could not retrieve email from Google.'}, status=status.HTTP_400_BAD_REQUEST)

    # Build a unique username from the email prefix
    base_username = email.split('@')[0]
    username      = base_username
    counter       = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    # Get or create user
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username':   username,
            'first_name': first_name,
            'last_name':  last_name,
            'is_active':  True,
        }
    )

    # Activate existing unverified users who sign in via Google
    if not user.is_active:
        user.is_active = True

    # Always update last_login (bypassed since we don't use authenticate())
    user.last_login = timezone.now()
    user.save(update_fields=['is_active', 'last_login'])

    tokens = get_tokens(user)
    return Response({
        'access':  tokens['access'],
        'refresh': tokens['refresh'],
        'user': {
            'id':         user.id,
            'username':   user.username,
            'email':      user.email,
            'first_name': user.first_name,
            'last_name':  user.last_name,
        },
        'created': created,
    }, status=status.HTTP_200_OK)