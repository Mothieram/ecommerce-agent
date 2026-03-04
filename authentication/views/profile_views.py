"""Profile read/update endpoints for authenticated users."""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..serializers import UserUpdateSerializer


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id":          user.id,
            "username":    user.username,
            "email":       user.email,
            "first_name":  user.first_name,
            "last_name":   user.last_name,
            "date_joined": user.date_joined,
            "last_login":  user.last_login,
            "has_usable_password": user.has_usable_password(),
        }, status=status.HTTP_200_OK)


class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def _update(self, request, partial):
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=partial,
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Profile updated successfully.",
                "user":    serializer.data,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        return self._update(request, partial=False)

    def patch(self, request):
        return self._update(request, partial=True)
