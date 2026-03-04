"""Authentication entrypoints: csrf, register, login, logout, refresh."""

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from ..serializers import RegisterSerializer, LoginSerializer
from .throttles import AuthRateThrottle
from .utils import get_tokens, set_auth_cookies, clear_auth_cookies, _cookie_kwargs, send_verification_email


class CsrfCookieView(APIView):
    permission_classes = [AllowAny]

    # Sets csrftoken cookie used by frontend for unsafe HTTP methods.
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({"message": "CSRF cookie set."}, status=status.HTTP_200_OK)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes   = [AuthRateThrottle]

    def post(self, request):
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


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes   = [AuthRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = get_tokens(user)
            response = Response({
                "message": "Login successful.",
                "user": {
                    "id":         user.id,
                    "username":   user.username,
                    "email":      user.email,
                    "last_login": user.last_login,
                    "has_usable_password": user.has_usable_password(),
                },
            }, status=status.HTTP_200_OK)
            set_auth_cookies(response, tokens)
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Strict cookie-based logout: refresh token is read only from HttpOnly cookie.
        refresh_token = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass

        response = Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        clear_auth_cookies(response)
        return response


class TokenRefreshCookieView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Refresh token is read from HttpOnly cookie, not request body.
        refresh_token = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if not refresh_token:
            return Response({"error": "Refresh token missing."}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        if not serializer.is_valid():
            response = Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
            clear_auth_cookies(response)
            return response

        response = Response({"message": "Token refreshed."}, status=status.HTTP_200_OK)
        response.set_cookie(
            settings.JWT_AUTH_COOKIE,
            serializer.validated_data["access"],
            max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
            **_cookie_kwargs(),
        )
        if "refresh" in serializer.validated_data:
            response.set_cookie(
                settings.JWT_AUTH_REFRESH_COOKIE,
                serializer.validated_data["refresh"],
                max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
                **_cookie_kwargs(),
            )
        return response

