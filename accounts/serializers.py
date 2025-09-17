from rest_framework import serializers
from .models import User
from django.contrib.auth.hashers import make_password
import re


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "full_name",
            "email",
            "password",
            "is_admin",
            "storage_path",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_username(self, value):
        if not re.match(r"^[A-Za-z][A-Za-z0-9]{3,19}$", value):
            raise serializers.ValidationError(
                "Логин: латиница, 4–20 символов, первая буква"
            )
        return value

    def create(self, validated_data):
        if "password" in validated_data:
            validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.password = make_password(password)
        return super().update(instance, validated_data)
