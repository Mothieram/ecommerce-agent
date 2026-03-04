from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate JWT from Authorization header or HttpOnly cookie."""

    def enforce_csrf(self, request):
        check = CSRFCheck(lambda _: None)
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise exceptions.PermissionDenied(f"CSRF Failed: {reason}")

    def authenticate(self, request):
        header = self.get_header(request)
        raw_token = self.get_raw_token(header) if header is not None else None
        from_cookie = False

        if raw_token is None:
            raw_token = request.COOKIES.get(settings.JWT_AUTH_COOKIE)
            from_cookie = raw_token is not None

        if raw_token is None:
            return None

        if from_cookie:
            try:
                validated_token = self.get_validated_token(raw_token)
                user = self.get_user(validated_token)
            except Exception:
                return None
            self.enforce_csrf(request)
            return user, validated_token

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
