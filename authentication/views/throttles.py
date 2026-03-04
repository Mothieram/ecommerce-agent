"""Rate limit classes used by auth endpoints."""

from rest_framework.throttling import AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    rate = '5/min'


class PasswordResetThrottle(AnonRateThrottle):
    rate = '3/hour'
