"""Google OAuth login/signup bridge."""

from django.contrib.auth import get_user_model
from django.utils import timezone

import requests as http_requests

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .utils import get_tokens, set_auth_cookies

User = get_user_model()


class GoogleLoginView(APIView):
    """
    Receives the Google access_token from the frontend (@react-oauth/google).
    Verifies it with Google, creates/fetches the Django user,
    and sets our JWT cookies.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get('access_token')
        intent = (request.data.get('intent') or 'login').strip().lower()

        if not access_token:
            return Response({'error': 'access_token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate Google access token and fetch profile payload.
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

        if intent == "register" and User.objects.filter(email=email).exists():
            return Response(
                {"error": "An account with this email already exists. Please sign in."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Username acts as display name; uniqueness is intentionally not required.
        username = email.split('@')[0]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username':   username,
                'first_name': first_name,
                'last_name':  last_name,
                'is_active':  True,
            }
        )

        update_fields = []

        # Keep OAuth-only users passwordless until they explicitly set app password.
        if created and not user.password:
            user.set_unusable_password()
            update_fields.append("password")

        # Activate existing unverified users who sign in via Google
        if not user.is_active:
            user.is_active = True
            update_fields.append("is_active")

        # Always update last_login (bypassed since we don't use authenticate()).
        user.last_login = timezone.now()
        update_fields.append("last_login")
        user.save(update_fields=update_fields)

        tokens = get_tokens(user)
        response = Response({
            'user': {
                'id':         user.id,
                'username':   user.username,
                'email':      user.email,
                'first_name': user.first_name,
                'last_name':  user.last_name,
                'has_usable_password': user.has_usable_password(),
            },
            'created': created,
            'requires_password_setup': not user.has_usable_password(),
        }, status=status.HTTP_200_OK)
        set_auth_cookies(response, tokens)
        return response
