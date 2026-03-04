"""Email verification and resend flows."""

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .throttles import AuthRateThrottle
from .utils import get_tokens, set_auth_cookies, send_verification_email

User = get_user_model()


class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes   = [AuthRateThrottle]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Keep response generic for unknown emails to prevent enumeration.
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


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid  = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError):
            return Response({"error": "Invalid verification link."}, status=status.HTTP_400_BAD_REQUEST)

        # Skip token re-check when already active: old links can become invalid after last_login changes.
        if user.is_active:
            return Response({"message": "Account already verified. You can log in."}, status=status.HTTP_200_OK)

        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": "Verification link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active  = True
        user.last_login = timezone.now()
        user.save(update_fields=['is_active', 'last_login'])

        tokens = get_tokens(user)
        response = Response(
            {"message": "Email verified successfully. You can now log in."},
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(response, tokens)
        return response
