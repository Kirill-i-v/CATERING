from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import serializers


User = get_user_model()


class TokenObtainResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "password",
        ]

    def validate(self, attrs: dict) -> dict:
        """Change the password for its hash to make token validation available"""

        attrs["password"] = make_password(attrs["password"])
        return attrs


class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "phone_number", "first_name", "last_name", "role"]


class UserActivationSerializer(serializers.Serializer):
    key = serializers.UUIDField()
    