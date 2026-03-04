"""Password management flows: change, reset email, reset confirm."""

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..serializers import ChangePasswordSerializer, ResetPasswordEmailSerializer, ResetPasswordConfirmSerializer
from .throttles import PasswordResetThrottle
from .utils import get_tokens, set_auth_cookies, blacklist_all_user_tokens

User = get_user_model()


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data.get('old_password', "")
            # Google-created users may not have a usable local password yet.
            if user.has_usable_password():
                if not old_password or not user.check_password(old_password):
                    return Response(
                        {"error": "Old password is incorrect."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            tokens = get_tokens(user)
            response = Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
            set_auth_cookies(response, tokens)
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes   = [PasswordResetThrottle]

    def post(self, request):
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
                    message=(
                        f"Hi {user.username},\n\n"
                        f"Reset your password here:\n\n{reset_link}\n\n"
                        "This link expires in 24 hours. If you didn't request this, ignore this email."
                    ),
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


class ResetPasswordConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        if serializer.is_valid():
            try:
                uid  = force_str(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid)
            except (User.DoesNotExist, ValueError):
                return Response({"error": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

            if not default_token_generator.check_token(user, token):
                return Response(
                    {"error": "Reset link is invalid or has expired."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(serializer.validated_data['new_password'])
            user.save()

            # Blacklist all existing tokens so old sessions can't be reused
            blacklist_all_user_tokens(user)

            return Response(
                {"message": "Password reset successfully. You can now log in."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
