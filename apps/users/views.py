from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from . import selectors, services
from .models import User
from .permissions import IsOwner
from .serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
    RequestPasswordResetSerializer,
    ResetPasswordSerializer,
    VerifyEmailSerializer,
)


class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [IsAdminUser()]
        if self.action in ['retrieve', 'partial_update']:
            return [IsAuthenticated(), IsOwner()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        if self.action == 'partial_update':
            return UserUpdateSerializer
        if self.action == 'change_password':
            return ChangePasswordSerializer
        return UserDetailSerializer

    def get_queryset(self):
        return selectors.filter_active()

    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = services.update_profile(user=user, **serializer.validated_data)
        return Response(UserDetailSerializer(user).data)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='me/change-password')
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.change_password(
            user=request.user,
            old_password=serializer.validated_data['old_password'],
            new_password=serializer.validated_data['new_password'],
        )
        return Response({'detail': 'Пароль успешно изменён'})


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = services.register_user(**serializer.validated_data)
        return Response(
            UserDetailSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.verify_email(token=serializer.validated_data['token'])
        return Response({'detail': 'Email успешно подтверждён'})


class ResendVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        services.resend_verification_email(user=request.user)
        return Response({'detail': 'Письмо с подтверждением отправлено'})


class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.request_password_reset(email=serializer.validated_data['email'])
        return Response({
            'detail': 'Если пользователь с таким email существует, письмо отправлено'
        })


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.reset_password(
            token=serializer.validated_data['token'],
            new_password=serializer.validated_data['new_password'],
        )
        return Response({'detail': 'Пароль успешно сброшен'})
