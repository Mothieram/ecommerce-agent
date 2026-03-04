from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


# ──────────────────────────────────────────────
# Register
# ──────────────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['username', 'email', 'password', 'password2']

    def validate_email(self, value):
        """Ensure the email is not already registered."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        user.is_active = False   # require email verification before login
        user.save()
        return user


# ──────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password          = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data['email']
        password          = data['password']
        try:
            user_by_email = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials.")

        if not user_by_email.has_usable_password():
            raise serializers.ValidationError(
                "This account uses Google sign-in. Please sign in with Google and set a password first."
            )

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")

        if not user.is_active:
            raise serializers.ValidationError(
                "Account is not verified. Please check your email."
            )

        data['user'] = user
        return data


# ──────────────────────────────────────────────
# Logout
# ──────────────────────────────────────────────
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


# ──────────────────────────────────────────────
# Change Password
# ──────────────────────────────────────────────
class ChangePasswordSerializer(serializers.Serializer):
    old_password  = serializers.CharField(write_only=True, required=False, allow_blank=True)
    new_password  = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError("New passwords do not match.")
        if data.get('old_password') and data['old_password'] == data['new_password']:
            raise serializers.ValidationError(
                "New password must be different from the old password."
            )
        return data


# ──────────────────────────────────────────────
# Update Profile
# ──────────────────────────────────────────────
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['username', 'email']

    def validate_email(self, value):
        """Prevent a user from taking another user's email."""
        user = self.instance
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value


# ──────────────────────────────────────────────
# Password Reset
# ──────────────────────────────────────────────
class ResetPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordConfirmSerializer(serializers.Serializer):
    new_password  = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
