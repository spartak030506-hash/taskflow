from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from ..models import User


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "avatar",
        ]
        read_only_fields = fields


class UserDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "avatar",
            "phone",
            "bio",
            "is_verified",
            "date_joined",
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Email пользователя (используется для входа)")
    password = serializers.CharField(
        write_only=True, min_length=8, help_text="Пароль (минимум 8 символов)"
    )
    first_name = serializers.CharField(max_length=150, help_text="Имя")
    last_name = serializers.CharField(max_length=150, help_text="Фамилия")

    def validate_email(self, value):
        return value.lower()

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value


class UserUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False, help_text="Имя")
    last_name = serializers.CharField(max_length=150, required=False, help_text="Фамилия")
    phone = serializers.CharField(
        max_length=20, required=False, allow_blank=True, help_text="Номер телефона"
    )
    bio = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Биография (максимум 500 символов)",
    )
    avatar = serializers.ImageField(
        required=False, allow_null=True, help_text="Аватар пользователя"
    )


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, help_text="Текущий пароль")
    new_password = serializers.CharField(
        write_only=True, min_length=8, help_text="Новый пароль (минимум 8 символов)"
    )

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value


class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Email для восстановления пароля")

    def validate_email(self, value):
        return value.lower()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(help_text="Токен восстановления пароля из email")
    new_password = serializers.CharField(
        write_only=True, min_length=8, help_text="Новый пароль (минимум 8 символов)"
    )

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField(help_text="Токен верификации email из письма")
