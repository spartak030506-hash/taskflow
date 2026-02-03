from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    UserViewSet,
    RegisterView,
    VerifyEmailView,
    ResendVerificationView,
    RequestPasswordResetView,
    ResetPasswordView,
)

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),

    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/verify-email/', VerifyEmailView.as_view(), name='auth-verify-email'),
    path('auth/resend-verification/', ResendVerificationView.as_view(), name='auth-resend-verification'),

    path('auth/token/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    path('auth/password-reset/', RequestPasswordResetView.as_view(), name='auth-password-reset'),
    path('auth/password-reset/confirm/', ResetPasswordView.as_view(), name='auth-password-reset-confirm'),
]
