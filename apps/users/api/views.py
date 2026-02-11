from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api_docs import (
    action_endpoint_schema,
    list_endpoint_schema,
    retrieve_endpoint_schema,
    update_endpoint_schema,
)

from .. import selectors, services
from ..models import User
from .permissions import IsOwner
from .serializers import (
    ChangePasswordSerializer,
    RegisterSerializer,
    RequestPasswordResetSerializer,
    ResetPasswordSerializer,
    UserDetailSerializer,
    UserListSerializer,
    UserUpdateSerializer,
    VerifyEmailSerializer,
)


class UserViewSet(viewsets.GenericViewSet):
    """
    ViewSet для управления пользователями.

    Доступ:
    - list: только администраторы
    - retrieve, partial_update: владелец профиля
    - me: текущий пользователь
    """

    queryset = User.objects.all()
    serializer_class = UserDetailSerializer

    def get_permissions(self):
        if self.action == "list":
            return [IsAdminUser()]
        if self.action in ["retrieve", "partial_update"]:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return UserListSerializer
        if self.action == "partial_update":
            return UserUpdateSerializer
        if self.action == "change_password":
            return ChangePasswordSerializer
        return UserDetailSerializer

    def get_queryset(self):
        return selectors.filter_active()

    @list_endpoint_schema(
        summary="Список пользователей",
        description="Возвращает пагинированный список активных пользователей. Доступно только администраторам.",
        tags=["users"],
    )
    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @retrieve_endpoint_schema(
        summary="Детали пользователя",
        description="Возвращает подробную информацию о пользователе. Доступно только владельцу профиля.",
        tags=["users"],
    )
    def retrieve(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @update_endpoint_schema(
        summary="Обновить профиль",
        description="Обновляет профиль пользователя (имя, фамилия, телефон, биография).",
        tags=["users"],
        request_examples=[
            OpenApiExample(
                name="UpdateProfileExample",
                value={
                    "first_name": "Иван",
                    "last_name": "Иванов",
                    "phone": "+79001234567",
                },
                request_only=True,
            ),
        ],
    )
    def partial_update(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = services.update_profile(user=user, **serializer.validated_data)
        return Response(UserDetailSerializer(user).data)

    @action_endpoint_schema(
        summary="Текущий пользователь",
        description="Возвращает информацию о текущем авторизованном пользователе.",
        tags=["users"],
        method="GET",
    )
    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="Изменить пароль",
        description="Изменяет пароль текущего пользователя. Требуется старый пароль для подтверждения.",
        tags=["users"],
        request=ChangePasswordSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"description": "Неверный старый пароль"},
        },
        examples=[
            OpenApiExample(
                name="ChangePasswordRequest",
                value={"old_password": "oldpass123", "new_password": "newpass123"},
                request_only=True,
            ),
        ],
    )
    @action(detail=False, methods=["post"], url_path="me/change-password")
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.change_password(
            user=request.user,
            old_password=serializer.validated_data["old_password"],
            new_password=serializer.validated_data["new_password"],
        )
        return Response({"detail": "Пароль успешно изменён"})


class RegisterView(APIView):
    """Регистрация нового пользователя."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Регистрация пользователя",
        description="Создаёт нового пользователя и отправляет письмо для подтверждения email.",
        tags=["auth"],
        request=RegisterSerializer,
        responses={
            201: UserDetailSerializer,
            400: {"description": "Ошибка валидации"},
            409: {"description": "Email уже зарегистрирован"},
        },
        examples=[
            OpenApiExample(
                name="RegisterRequest",
                value={
                    "email": "user@example.com",
                    "password": "securepass123",
                    "first_name": "Иван",
                    "last_name": "Иванов",
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = services.register_user(**serializer.validated_data)
        return Response(
            UserDetailSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    """Подтверждение email через токен."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Подтверждение email",
        description="Подтверждает email пользователя через токен из письма.",
        tags=["auth"],
        request=VerifyEmailSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"description": "Неверный или истёкший токен"},
        },
        examples=[
            OpenApiExample(
                name="VerifyEmailRequest",
                value={"token": "abc123xyz"},
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.verify_email(token=serializer.validated_data["token"])
        return Response({"detail": "Email успешно подтверждён"})


class ResendVerificationView(APIView):
    """Повторная отправка письма с подтверждением email."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Повторная отправка подтверждения",
        description="Отправляет новое письмо с токеном для подтверждения email.",
        tags=["auth"],
        request=None,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
    def post(self, request):
        services.resend_verification_email(user=request.user)
        return Response({"detail": "Письмо с подтверждением отправлено"})


class RequestPasswordResetView(APIView):
    """Запрос на восстановление пароля."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Запрос восстановления пароля",
        description="Отправляет письмо с токеном для восстановления пароля.",
        tags=["auth"],
        request=RequestPasswordResetSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
        examples=[
            OpenApiExample(
                name="RequestPasswordResetRequest",
                value={"email": "user@example.com"},
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.request_password_reset(email=serializer.validated_data["email"])
        return Response({"detail": "Если пользователь с таким email существует, письмо отправлено"})


class ResetPasswordView(APIView):
    """Сброс пароля через токен."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Сброс пароля",
        description="Устанавливает новый пароль используя токен из письма.",
        tags=["auth"],
        request=ResetPasswordSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"description": "Неверный или истёкший токен"},
        },
        examples=[
            OpenApiExample(
                name="ResetPasswordRequest",
                value={"token": "abc123xyz", "new_password": "newsecure123"},
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.reset_password(
            token=serializer.validated_data["token"],
            new_password=serializer.validated_data["new_password"],
        )
        return Response({"detail": "Пароль успешно сброшен"})
