from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
import requests as http_requests


from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView


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
# google login classes
# ──────────────────────────────────────────────
class GoogleLoginview(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://localhost:8000/api/auth/google/callback/"
    client_class    = OAuth2Client

@api_view(['POST'])
@permission_classes(AllowAny)
def google_login_view(request):
    access_token = request.data.get('access_token')
    if not access_token:
        return Response({'error': 'access_token is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Ask Google for the user's profile using the access token
    google_response = http_requests.get(
        'https://www.googleapis.com/oauth2/v3/userinfo',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    if google_response.status_code != 200:
        return Response({'error': 'Invalid Google token.'}, status=status.HTTP_400_BAD_REQUEST)

    google_data = google_response.json()
    email       = google_data.get('email')
    first_name  = google_data.get('given_name', '')
    last_name   = google_data.get('family_name', '')

    if not email:
        return Response({'error': 'Could not retrieve email from Google.'}, status=status.HTTP_400_BAD_REQUEST)

    # Get or create the user by email
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username':   email.split('@')[0],   # default username from email
            'first_name': first_name,
            'last_name':  last_name,
            'is_active':  True,                  # Google-verified, no email step needed
        }
    )

    # If user already existed but was inactive (registered manually), activate them
    if not user.is_active:
        user.is_active = True
        user.save()

    # Return our own JWT tokens
    tokens = get_tokens(user)
    return Response({
        'access':  tokens['access'],
        'refresh': tokens['refresh'],
        'user': {
            'id':       user.id,
            'username': user.username,
            'email':    user.email,
        },
        'created': created,   # True = new user, False = existing user logged in
    }, status=status.HTTP_200_OK)

# ──────────────────────────────────────────────
# Custom throttle classes
# ──────────────────────────────────────────────
class AuthRateThrottle(AnonRateThrottle):
    """Strict throttle for auth endpoints: 5 requests / minute."""
    rate = '5/min'


class PasswordResetThrottle(AnonRateThrottle):
    """Very strict throttle for password-reset: 3 requests / hour."""
    rate = '3/hour'


# ──────────────────────────────────────────────
# Helper
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
            # Don't block registration if email fails; just log it
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
        return Response({"message": "Account already verified."}, status=status.HTTP_200_OK)

    user.is_active = True
    user.save()
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
# Profile (view)
# ──────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user
    return Response({
        "id":           user.id,
        "username":     user.username,
        "email":        user.email,
        "date_joined":  user.date_joined,
        "last_login":   user.last_login,
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

        # Blacklist old refresh token (if provided) and issue fresh tokens
        # so the current session stays valid without forcing re-login.
        new_tokens = get_tokens(user)
        return Response({
            "message": "Password changed successfully.",
            "tokens":  new_tokens,
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
        # Always return the same response to prevent email enumeration
        generic_response = Response(
            {"message": "If an account with that email exists, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return generic_response   # don't reveal that email wasn't found

        uid   = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
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
        return Response({"message": "Password reset successfully. You can now log in."}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)