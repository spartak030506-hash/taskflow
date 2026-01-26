from django.db.models import QuerySet

from core.exceptions import NotFoundError

from .models import User, EmailVerificationToken, PasswordResetToken


def get_by_id(user_id: int) -> User:
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise NotFoundError('Пользователь не найден')


def get_by_email(email: str) -> User:
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        raise NotFoundError('Пользователь не найден')


def filter_active() -> QuerySet[User]:
    return User.objects.filter(is_active=True)


def exists_email(email: str) -> bool:
    return User.objects.filter(email=email).exists()


def get_verification_token(token: str) -> EmailVerificationToken:
    try:
        return EmailVerificationToken.objects.select_related('user').get(token=token)
    except EmailVerificationToken.DoesNotExist:
        raise NotFoundError('Токен верификации не найден')


def get_password_reset_token(token: str) -> PasswordResetToken:
    try:
        return PasswordResetToken.objects.select_related('user').get(token=token)
    except PasswordResetToken.DoesNotExist:
        raise NotFoundError('Токен сброса пароля не найден')
