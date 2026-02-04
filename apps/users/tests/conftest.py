import pytest
from datetime import timedelta
from django.utils import timezone

from .factories import UserFactory, EmailVerificationTokenFactory, PasswordResetTokenFactory


@pytest.fixture
def unverified_user(db):
    return UserFactory(is_verified=False)


@pytest.fixture
def verified_user(db):
    return UserFactory(is_verified=True)


@pytest.fixture
def admin_user(db):
    return UserFactory(is_verified=True, is_staff=True, is_superuser=True)


@pytest.fixture
def user_with_verification_token(db):
    user = UserFactory(is_verified=False)
    token = EmailVerificationTokenFactory(user=user)
    return user, token


@pytest.fixture
def user_with_expired_verification_token(db):
    user = UserFactory(is_verified=False)
    token = EmailVerificationTokenFactory(
        user=user,
        expires_at=timezone.now() - timedelta(hours=1)
    )
    return user, token


@pytest.fixture
def user_with_password_reset_token(db):
    user = UserFactory(is_verified=True)
    token = PasswordResetTokenFactory(user=user)
    return user, token


@pytest.fixture
def user_with_expired_password_reset_token(db):
    user = UserFactory(is_verified=True)
    token = PasswordResetTokenFactory(
        user=user,
        expires_at=timezone.now() - timedelta(hours=1)
    )
    return user, token


@pytest.fixture
def user_with_used_password_reset_token(db):
    user = UserFactory(is_verified=True)
    token = PasswordResetTokenFactory(user=user, is_used=True)
    return user, token
